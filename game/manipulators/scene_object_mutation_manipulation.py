from game.manipulators.base_manipulation import BaseManipulation
from utils.dice_utils import roll
from skls_generator.generator import Generator
from schemas.orchestration import Event, EventTypes, SceneObjectManipulationCommand
from thefuzz import process
from typing import Any, List, Tuple
from logging import Logger
from game.engine import Session
from schemas.in_game import UnifiedObject
from utils.spatial_utils import calculate_spatial_distances


class SceneObjectMutationManipulation(BaseManipulation):
    """Handles scene object-related manipulations, such as state changes or property updates."""
    # the llm prompt
    task_rules = f"""
    1. Use object names, field names, other values exactly as provided
    2. Use one of the following types of operations add/subtract/append/remove/replace
        2.1 add/subtract should be applied to numeric values add/subtract is acceptable
        2.2 the rest should be applied to text/states values
        2.3 append adds a value (multiple values) to the list, remove removes them, replace replaces the entire list with a new one
        2.4 Numeric value should follow dnd dice notation or a constant number (e g 10d4+1 where 10d4 means addition of 10 times rolled dice with 4 planes and + 1 constantly on top of that)
        2.5 for non-numeric values use attribute field
    3. If the target is an object attribute you MUST use it exactly as it spelled in reference objects.
    4. For nested objects, use dot notation (e.g., 'container.contained_objects.object_name.field_name')
    """

    event_types_binded = [EventTypes.ITEM_STATUS_CHANGE,
                         EventTypes.ITEM_MUTATION,
                         EventTypes.ITEM_INTERACTION]

    def __init__(self, generator : Generator, state : Session, archive, logger : Logger) -> None:
        super().__init__(generator, state, archive, logger)

    def manipulate(self, event) -> List[Event]:
        # Get all scene objects in the current scene
        scene_objects = self.state.current_scene.objects
        all_object_names = self._get_all_object_names(scene_objects)

        # Calculate spatial distances if relevant
        spatial_info = calculate_spatial_distances(self.state, event)

        task_prompt = f"""Create a specific authoritative task from the event {event}

        Spatial Information (if applicable):
        {spatial_info}

        Follow the following rules {self.task_rules}.

        # object schema for attribute matches:
        {UnifiedObject.schema()}"""

        task = self.generator.generate_one_shot(
            pydantic_model=SceneObjectManipulationCommand,
            prompt=task_prompt
        )

        # Check if the task.object_name contains dot notation for nested objects
        if '.' in task.object_name:
            # Handle nested object path (e.g., "chest.contained_objects.sword.damage_dice")
            target = self._find_nested_object_by_path(task.object_name, scene_objects)
        else:
            # Find the target object using fuzzy matching
            target = None
            best = process.extractOne(task.object_name, all_object_names)
            if best:
                best = best[0]
            else:
                raise ValueError(f"No scene object found with name similar to: {task.object_name}")

            # Find the actual object in the scene (including nested objects)
            target = self._find_object_by_name(best, scene_objects)

        if not target:
            raise ValueError(f"No scene object found with name: {task.object_name}")

        # Store before state for action result
        parent_obj, field_name = self._resolve_attribute_path(target, task.target)
        original_value = getattr(parent_obj, field_name)

        self._apply_change(target, task)

        # Get the new value after applying the change
        new_value = getattr(parent_obj, field_name)

        # Create action result event
        action_result = Event(
            event_type=EventTypes.ACTION_RESULT,
            event_initiator=event.event_initiator,
            event_subject=target.name,
            event_target=task.target,
            description=f"Applied {task.operation} operation to object '{target.name}' attribute '{task.target}': {original_value} -> {new_value}"
        )

        return [action_result]

    def _get_all_object_names(self, objects, prefix=""):
        """Recursively collect all object names including nested objects."""
        names = []
        for obj in objects:
            # Add the current object name
            obj_name = f"{prefix}{obj.name}" if prefix else obj.name
            names.append(obj_name)

            # Add names of contained objects recursively
            if hasattr(obj, 'contained_objects') and obj.contained_objects:
                nested_prefix = f"{obj.name}.contained_objects." if prefix else f"{obj.name}.contained_objects."
                names.extend(self._get_all_object_names(obj.contained_objects, nested_prefix))
        return names

    def _find_object_by_name(self, name, objects):
        """Recursively find an object by name including nested objects."""
        # Handle the case where name might be a full path like "chest.contained_objects.sword"
        if '.' in name:
            # Extract just the object name from the path (last part after the last dot)
            obj_name = name.split('.')[-1]
        else:
            obj_name = name

        for obj in objects:
            if obj.name == obj_name:
                return obj
            # Search in contained objects recursively
            if hasattr(obj, 'contained_objects') and obj.contained_objects:
                found = self._find_object_by_name(name, obj.contained_objects)
                if found:
                    return found
        return None

    def _find_nested_object_by_path(self, path, objects):
        """Find an object using dot notation path (e.g., 'container.contained_objects.nested_obj')."""
        path_parts = path.split('.')

        # Find the top-level object first
        top_level_name = path_parts[0]
        target_obj = self._find_object_by_name(top_level_name, objects)

        if not target_obj:
            return None

        # Navigate through the path to find the nested object
        current_obj = target_obj

        # Process the remaining path parts
        for i in range(1, len(path_parts)):
            part = path_parts[i]

            # If this is the last part and it's an attribute name, return the current object
            # (we'll handle the attribute separately in _resolve_attribute_path)
            if i == len(path_parts) - 1:
                # Check if this is an attribute of the current object
                if hasattr(current_obj, part):
                    return current_obj  # Return the object that has this attribute
                else:
                    # If it's not an attribute, it might be a nested object name within contained_objects
                    if hasattr(current_obj, 'contained_objects') and current_obj.contained_objects:
                        nested_obj = self._find_object_by_name(part, current_obj.contained_objects)
                        if nested_obj:
                            return nested_obj
                    return None

            # If this is not the last part, navigate deeper
            if hasattr(current_obj, part):
                current_obj = getattr(current_obj, part)
            elif part == 'contained_objects':
                # Special handling for contained_objects
                if hasattr(current_obj, 'contained_objects'):
                    # The next part should be an object name within contained_objects
                    if i + 1 < len(path_parts):
                        next_part = path_parts[i + 1]
                        nested_obj = self._find_object_by_name(next_part, current_obj.contained_objects)
                        if nested_obj:
                            current_obj = nested_obj
                            i += 1  # Skip the next part since we handled it
                        else:
                            return None
                else:
                    return None
            else:
                return None

        return current_obj

    def _apply_change(self, obj: UnifiedObject, task: SceneObjectManipulationCommand):
        """Dispatches logic based on the attribute type (Numeric vs List/State)."""

        # Map common AI terms to Pydantic fields
        # Returns (parent_object, field_name)
        parent_obj, field_name = self._resolve_attribute_path(obj, task.target)

        # Retrieve the current value to determine how to handle it
        current_val = getattr(parent_obj, field_name)

        self.logger.debug(f"Applying object change to {obj.name}: {task.operation} {field_name} with value {task.value} (current: {current_val})")

        # --- BRANCH A: Numeric Operations (quantity, etc.) ---
        if isinstance(current_val, int):
            self._handle_numeric_op(parent_obj, field_name, current_val, task)

        # --- BRANCH B: List Operations (tags, content, etc.) ---
        elif isinstance(current_val, list):
            self._handle_list_op(parent_obj, field_name, current_val, task)

        # --- BRANCH C: String/Boolean Operations (state, description, is_locked, etc.) ---
        elif isinstance(current_val, str):
            if task.operation == "replace" or task.operation == "set":
                old_val = getattr(parent_obj, field_name)
                setattr(parent_obj, field_name, task.value)
                self.logger.debug(f"Set {obj.name}.{field_name} to '{task.value}' (was '{old_val}')")
        elif isinstance(current_val, bool):
            if task.operation == "replace" or task.operation == "set":
                # Convert the value to boolean
                if isinstance(task.value, str):
                    new_val = task.value.lower() in ['true', '1', 'yes', 'on']
                else:
                    new_val = bool(task.value)
                old_val = getattr(parent_obj, field_name)
                setattr(parent_obj, field_name, new_val)
                self.logger.debug(f"Set {obj.name}.{field_name} to {new_val} (was {old_val})")
        elif isinstance(current_val, list) and field_name == "contained_objects":
            # Handle operations on contained_objects list
            self._handle_contained_objects_op(parent_obj, field_name, current_val, task)

    def _handle_contained_objects_op(self, obj: UnifiedObject, field: str, current_list: list, task: SceneObjectManipulationCommand):
        """Handles operations on the contained_objects list."""
        if task.operation == "append" or task.operation == "add":
            # Need to create a new UnifiedObject from the task value
            # For now, we'll just note this as a limitation since we can't create objects from string values
            self.logger.warning(f"Cannot add new objects to contained_objects from string value: {task.value}. This requires object creation from schema.")
        elif task.operation == "remove" or task.operation == "delete":
            # Remove object by name if it exists in the list
            obj_to_remove = None
            for contained_obj in current_list:
                if contained_obj.name == str(task.value):
                    obj_to_remove = contained_obj
                    break
            if obj_to_remove:
                current_list.remove(obj_to_remove)
                self.logger.info(f"➖ Removed '{obj_to_remove.name}' from contained_objects.")
            else:
                self.logger.warning(f"Object '{task.value}' not found in contained_objects to remove.")
        elif task.operation == "replace":
            # Replace the entire contained_objects list
            if str(task.value).lower() in ["none", "clear", "empty"]:
                setattr(obj, field, [])
            else:
                self.logger.warning(f"Replacing contained_objects with string value '{task.value}' is not supported. This requires a list of UnifiedObject instances.")

    def _handle_numeric_op(self, obj: Any, field: str, current_val: int, task: SceneObjectManipulationCommand):
        """Handles dice parsing and math."""
        # Parse the value (handle '1d4+2' or '10')
        change_amount = roll(task.value)
        self.logger.debug(f"Dice Roll: {change_amount}")
        self.logger.debug(f"Task: {task}")
        new_val = int(current_val)

        if task.operation in ["add", "heal", "buff"]:
            new_val += change_amount
        elif task.operation in ["subtract", "sub", "damage", "debuff"]:
            new_val -= change_amount
        elif task.operation in ["set", "replace"]:
            new_val = change_amount
        else:
            raise ValueError(f"Unknown operation: {task.operation}")

        setattr(obj, field, int(new_val))
        self.logger.info(f"🔢 {field} changed: {current_val} -> {new_val} (Operation: {task.operation} {task.value})")

    def _handle_list_op(self, obj: Any, field: str, current_list: list, task: SceneObjectManipulationCommand):
        """Handles list operations (e.g., adding/removing tags from scene objects)."""

        clean_value = str(task.value)

        if task.operation in ["append", "add"]:
            if clean_value not in current_list:
                current_list.append(clean_value)
                self.logger.info(f"➕ Added '{clean_value}' to {field}.")

        elif task.operation in ["remove", "subtract", "delete"]:
            if clean_value in current_list:
                current_list.remove(clean_value)
                self.logger.info(f"➖ Removed '{clean_value}' from {field}.")

        elif task.operation == "replace":
            # Replaces the whole list
            if clean_value.lower() in ["none", "clear", "empty"]:
                setattr(obj, field, [])
            else:
                setattr(obj, field, [clean_value])

    def _resolve_attribute_path(self, obj: UnifiedObject, attr_name: str) -> Tuple[Any, str]:
        """
        Translates attribute names to the appropriate object and field.
        Handles both simple attribute names and dot notation for nested attributes.
        """
        # If attr_name contains dot notation, we need to navigate to the nested attribute
        if '.' in attr_name:
            path_parts = attr_name.split('.')
            current_obj = obj

            # Navigate through all parts except the last one (which is the actual attribute)
            for part in path_parts[:-1]:
                if hasattr(current_obj, part):
                    current_obj = getattr(current_obj, part)
                else:
                    raise ValueError(f"Attribute path invalid: {attr_name} - '{part}' not found in {current_obj}")

            # The last part is the actual attribute we want to modify
            final_attr = path_parts[-1]
            if hasattr(current_obj, final_attr):
                return current_obj, final_attr
            else:
                raise ValueError(f"Final attribute not found: {final_attr} in {current_obj}")

        # Handle simple attribute names as before
        attr = attr_name.lower()

        # Common mappings for UnifiedObject attributes
        if attr in ["state", "status"]:
            return obj, "state"
        elif attr in ["description", "desc"]:
            return obj, "description"
        elif attr in ["locked", "is_locked"]:
            return obj, "is_locked"
        elif attr in ["hidden", "is_hidden"]:
            return obj, "is_hidden"
        elif attr in ["content", "contents", "items"]:
            return obj, "content"
        elif attr in ["tags", "tag"]:
            return obj, "tags"
        elif attr in ["quantity", "amount", "count"]:
            return obj, "quantity"
        elif attr in ["type", "obj_type"]:
            return obj, "obj_type"
        elif attr in ["capacity"]:
            return obj, "capacity"
        elif attr in ["contained_objects", "nested_objects", "inner_objects"]:
            return obj, "contained_objects"
        elif attr in ["item_description", "item_desc"]:
            return obj, "item_description"
        elif attr in ["id", "identifier"]:
            return obj, "id"
        elif attr in ["damage_dice", "dice"]:
            return obj, "damage_dice"
        elif attr in ["damage_type", "damage"]:
            return obj, "damage_type"
        elif attr in ["equipped", "is_equipped"]:
            return obj, "is_equipped"

        # Fallback: Try to find the attribute directly on the UnifiedObject
        if hasattr(obj, attr):
            return obj, attr

        raise ValueError(f"Unknown attribute: {attr_name}")