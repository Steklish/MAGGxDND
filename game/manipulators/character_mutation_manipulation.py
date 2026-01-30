from game.manipulators.base_manipulation import BaseManipulation
from utils.dice_utils import roll
from skls_generator.generator import Generator
from schemas.orchestration import Event, EventTypes, Character, CharacterManipulationBrakdown
from thefuzz import process
from typing import Any, List, Tuple
from logging import Logger
from game.engine import Session
from utils.spatial_utils import calculate_spatial_distances


class CharacterMutationManipulation(BaseManipulation):
    """Handles character-related manipulations, such as status effects or inventory changes."""
    # the llm prompt
    task_rules = f"""
    1. Use charater names, field names, other values exactly as provided
    2. Use one of the following tyles of operations add/subtract/append/remove/replace
        2.1 add/subtract should be applied to numeric values add/subtract is acceptable
        2.2 the rest should be applied to text/states values
        2.3 append adds a value (multiple values) to the list, remove removes them, replace replaces the entire list with a new one
        2.4 Numeric value should follow dnd dice notation or a constatnt number (e g 10d4+1 where 10d4 means addition of 10 times rolled dice with 4 planes and + 1 constatly on top of that)
        2.5 for non-numeric values use attribute field
    3. If the target is an object attibute you MUST use its exactly as it spelled in reference objects.
    4. If inventory or spells or other objects involved you may need to yse their stats to choose numeric values.
    """

    event_types_binded = [EventTypes.CHARACTER_STATS_UPDATE,
                                   EventTypes.CHARACTER_STATUS_CHANGE,
                                   EventTypes.CHARACTER_DEATH]

    def __init__(self, generator : Generator, state : Session, archive, logger : Logger) -> None:
        super().__init__(generator, state, archive, logger)

    def manipulate(self, event) -> List[Event]:
        objects = self.get_related_objects(event)
        objects_text = ""
        for o in objects:
            objects_text += '\n'
            objects_text += str(o.__str__ if o else None)

        # Calculate spatial distances between mentioned objects if spatial system is enabled
        spatial_info = calculate_spatial_distances(self.state, event)

        task_prompt = f"""Create a specific authoritative task from the event {event}

        Spatial Information (if applicable):
        {spatial_info}

        Follow the following rules {self.task_rules}.

        # object schema for attribute matches:
        {Character.schema()}"""

        task = self.generator.generate_one_shot(
            pydantic_model=CharacterManipulationBrakdown,
            prompt=task_prompt
        )

        names = [c.name for c in self._get_all_caracters()]
        target = None
        best = process.extractOne(task.character_name, names)
        if best:
            best = best[0]
        else:
            raise ValueError("No target found")

        for c in self._get_all_caracters():
            if c.name == best:
                target = c
                break
        if not target:
            raise ValueError("No target found")

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
            description=f"From request {event.description}:\n Applied {task.operation} operation to {target.name}'s {task.target}: {original_value} -> {new_value}",
            start_position=event.start_position,
            end_position=event.end_position,
            distance=event.distance
        )

        return [action_result]

    def _apply_change(self, char: Character, task: CharacterManipulationBrakdown):
        """Dispatches logic based on the attribute type (Numeric vs List/State)."""

        # Map common AI terms to Pydantic fields and handle nested "abilities"
        # Returns (parent_object, field_name)
        parent_obj, field_name = self._resolve_attribute_path(char, task.target)

        # Retrieve the current value to determine how to handle it
        current_val = getattr(parent_obj, field_name)

        self.logger.debug(f"Applying change to {char.name}: {task.operation} {field_name} with value {task.value} (current: {current_val})")

        # --- BRANCH A: Numeric Operations (HP, Str, Speed) ---
        if isinstance(current_val, int):
            self._handle_numeric_op(parent_obj, field_name, current_val, task)

        # --- BRANCH B: List Operations (Active Conditions, Personality) ---
        elif isinstance(current_val, list):
            self._handle_list_op(parent_obj, field_name, current_val, task)

        # --- BRANCH C: String/Enum Operations (Race, Class Name) ---
        elif isinstance(current_val, str):
             if task.operation == "replace" or task.operation == "set":
                 setattr(parent_obj, field_name, task.value)
                 self.logger.info(f"Set {char.name}.{field_name} to '{task.value}' (was '{current_val}')")

    def _handle_numeric_op(self, obj: Any, field: str, current_val: int, task: CharacterManipulationBrakdown):
        """Handles dice parsing and math."""
        # Parse the value (handle '1d4+2' or '10')
        change_amount = roll(task.value)
        self.logger.debug(f"Dice Roll: {change_amount}")
        self.logger.debug(f"Task: {task}")
        new_val = int(current_val)

        if task.operation in ["add", "heal", "buff"]:
            new_val += change_amount
            self.logger.debug(f"Adding {change_amount} to {field} (was {current_val}, now {new_val})")
        elif task.operation in ["subtract", "sub", "damage", "debuff"]:
            new_val -= change_amount
            self.logger.debug(f"Subtracting {change_amount} from {field} (was {current_val}, now {new_val})")
        elif task.operation in ["set", "replace"]:
            new_val = change_amount
            self.logger.debug(f"Setting {field} to {change_amount} (was {current_val}, now {new_val})")
        else:
            raise ValueError(f"Unknown operation: {task.operation}")


        # Logical clamps (HP cannot go below 0)
        if field == "current_hp":
            new_val = max(0, new_val)
            # You might also want to clamp to max_hp here if you have access to it
            if hasattr(obj, "max_hp"):
                new_val = min(new_val, obj.max_hp)

        setattr(obj, field, int(new_val))
        self.logger.info(f"🔢 {field} changed: {current_val} -> {new_val} (Operation: {task.operation} {task.value})")

    def _handle_list_op(self, obj: Any, field: str, current_list: list, task: CharacterManipulationBrakdown):
        """Handles States/Conditions (e.g., ['Prone'] -> ['Prone', 'Poisoned'])."""


        clean_value = task.value.title() # "poisoned" -> "Poisoned"

        self.logger.debug(f"Handling list operation on {field}: {task.operation} '{clean_value}', current list: {current_list}")

        if task.operation in ["append", "add"]:
            if clean_value not in current_list:
                current_list.append(clean_value)
                self.logger.info(f"➕ Added status '{clean_value}' to {field}. New list: {current_list}")
            else:
                self.logger.debug(f"'{clean_value}' already exists in {field}, skipping add operation.")

        elif task.operation in ["remove", "subtract", "delete"]:
            if clean_value in current_list:
                current_list.remove(clean_value)
                self.logger.info(f"➖ Removed status '{clean_value}' from {field}. New list: {current_list}")
            else:
                self.logger.debug(f"'{clean_value}' not found in {field}, skipping remove operation.")

        elif task.operation == "replace":
            # Replaces the whole list (e.g. clear all conditions)
            if clean_value.lower() in ["none", "clear", "empty"]:
                old_list = current_list.copy()
                setattr(obj, field, [])
                self.logger.info(f"🔄 Cleared all values from {field}. Old list: {old_list}, new list: {getattr(obj, field)}")
            else:
                old_list = current_list.copy()
                setattr(obj, field, [clean_value])
                self.logger.info(f"🔄 Replaced {field}. Old list: {old_list}, new list: {getattr(obj, field)}")

    def _resolve_attribute_path(self, char: Character, attr_name: str) -> Tuple[Any, str]:
        """
        Translates 'strength' -> (char.abilities, 'strength')
        Translates 'hp' -> (char, 'current_hp')
        """
        attr = attr_name.lower()

        # 1. Shortcuts for Core Stats
        ability_map = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
        for ability in ability_map:
            # Matches "strength" or "str"
            if attr == ability or (len(attr) == 3 and ability.startswith(attr)):
                return char.abilities, ability

        # 2. Shortcuts for Vitals
        if attr in ["hp", "health", "life"]:
            return char, "current_hp"
        if attr in ["max_hp", "total_health"]:
            return char, "max_hp"
        if attr in ["ac", "armor"]:
            return char, "armor_class"

        # 3. Shortcuts for States
        if attr in ["condition", "conditions", "status", "effect"]:
            return char, "active_conditions"

        # 4. Fallback: Try to find the attribute directly on the Character object
        if hasattr(char, attr):
            return char, attr

        # 5. Fallback: Try to find it on abilities (if the AI guessed the full name correctly)
        if hasattr(char.abilities, attr):
            return char.abilities, attr

        raise ValueError(f"Unknown attribute: {attr_name}")