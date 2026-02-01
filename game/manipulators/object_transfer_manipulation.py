from game.manipulators.base_manipulation import BaseManipulation
from skls_generator.generator import Generator
from schemas.orchestration import Event, EventTypes, TransferEventBreakDown
from typing import  List, Tuple
from logging import Logger
from game.engine import Session
from schemas.in_game import UnifiedObject
import copy
from utils.spatial_utils import calculate_spatial_distances


class ObjectTransferManipulation(BaseManipulation):
    """Handles transferring objects between scene objects and player inventories."""

    task_rules = f"""
    1. Use object names exactly as provided in the scene or inventory
    2. Determine the direction of transfer:
        2.1 From scene to inventory: Take/Grab/Pick up from scene
        2.2 From inventory to scene: Drop/Put/Place from inventory
        2.3 From container to inventory: Take/Remove from container
        2.4 From inventory to container: Add/Put/Store in container
        2.5 From container to container: Move/Transfer between containers
    3. Handle quantity properly - if quantity > 1, only transfer the specified amount
    4. Validate that containers respect capacity limits when adding objects
    5. When moving from container to inventory, remove from the container's contained_objects
    6. When moving from inventory to scene/container, remove from the character's inventory
    7. Use exact object names as they appear in the scene context
    8. For container operations, specify both the object name and target container name
    """

    event_types_binded = [EventTypes.OBJECT_TRANSFER,
                         EventTypes.ITEM_PICKUP,
                         EventTypes.ITEM_DROP,
                         EventTypes.CONTAINER_ACCESS,
                         EventTypes.CONTAINER_TRANSFER,
                         EventTypes.ITEM_TRANSFER]

    def __init__(self, generator: Generator, state: Session, archive, logger: Logger) -> None:
        super().__init__(generator, state, archive, logger)

    def manipulate(self, event: Event) -> List[Event]:
        """Process the object transfer event."""
        # Get the scene context to help the LLM understand object names

        # Calculate spatial distances if relevant
        spatial_info = calculate_spatial_distances(self.state, event)

        # Create a prompt for the LLM to generate a transfer command
        prompt = f"""
        Create a specific authoritative transfer command from the event {event}

        Spatial Information (if applicable):
        {spatial_info}

        Follow the following rules {self.task_rules}.

        Scene Context:
        {self.state.get_session_context()}

        SPECIAL CASES TO HANDLE:
        - If the event describes searching a character's body, the items should come from that character's inventory, not from the scene.
        - If the event describes looting a corpse, the items should come from that character's inventory.
        - Pay close attention to the event description to determine the correct source of items.
        """

        self.logger.debug(f"Processing transfer event: {event.event_type.value} - {event.description}")
        self.logger.debug(f"Event context: {event.event_initiator} -> {event.event_subject} -> {event.event_target}")

        transfer_command = self.generator.generate_one_shot(
            pydantic_model=TransferEventBreakDown,
            prompt=prompt
        )

        source = transfer_command.source
        target = transfer_command.target
        object_name = transfer_command.object_name
        quantity = transfer_command.quantity
        target_container_name = transfer_command.target_container

        self.logger.info(f"Generated transfer command: {source} -> {target} | {quantity}x '{object_name}' | Container: {target_container_name}")

        # Determine transfer direction and execute
        if source == "scene" and target == "inventory":
            self.logger.debug(f"Executing scene->inventory transfer: {quantity}x '{object_name}'")
            # Check if the object is actually in any location (special case for searching bodies)
            target_character_name = event.event_initiator or event.event_target
            if target_character_name and ("search" in event.description.lower() or "loot" in event.description.lower() or "body" in event.description.lower()):
                # This is likely a case where the LLM misidentified the source
                # Try to find the object in any possible location
                found_in_any_location = self._try_transfer_from_any_location(event, object_name, quantity, target_character_name)
                if not found_in_any_location:
                    # Fall back to scene if not found in any location
                    self._transfer_from_scene_to_inventory(object_name, quantity)
            else:
                # Even if not a search action, try to find the object in any location to be robust
                found_in_any_location = self._try_transfer_from_any_location(event, object_name, quantity, target_character_name or "")
                if not found_in_any_location:
                    self._transfer_from_scene_to_inventory(object_name, quantity)
        elif source == "inventory" and target == "scene":
            self.logger.debug(f"Executing inventory->scene transfer: {quantity}x '{object_name}'")
            # Try to find the object in any location to be robust
            target_character_name = event.event_initiator or event.event_target
            found_in_any_location = self._try_transfer_from_any_location(event, object_name, quantity, target_character_name or "")
            if not found_in_any_location:
                self._transfer_from_inventory_to_scene(object_name, quantity)
        elif source == "container" and target == "inventory":
            self.logger.debug(f"Executing container->inventory transfer: {quantity}x '{object_name}'")
            # Try to find the object in any location to be robust
            target_character_name = event.event_initiator or event.event_target
            found_in_any_location = self._try_transfer_from_any_location(event, object_name, quantity, target_character_name or "")
            if not found_in_any_location:
                self._transfer_from_container_to_inventory(object_name, quantity)
        elif source == "inventory" and target == "container":
            self.logger.debug(f"Executing inventory->container transfer: {quantity}x '{object_name}' to container '{target_container_name}'")
            # Try to find the object in any location to be robust
            found_in_any_location = self._try_transfer_from_any_location(event, object_name, quantity, event.event_initiator or "")
            if not found_in_any_location:
                self._transfer_from_inventory_to_container(object_name, quantity, target_container_name)
        elif source == "container" and target == "container":
            self.logger.debug(f"Executing container->container transfer: {quantity}x '{object_name}' to container '{target_container_name}'")
            # Try to find the object in any location to be robust
            found_in_any_location = self._try_transfer_from_any_location(event, object_name, quantity, event.event_initiator or "")
            if not found_in_any_location:
                self._transfer_from_container_to_container(object_name, quantity, target_container_name)
        # NEW: Handle inventory-to-inventory transfers (between different characters)
        elif source == "inventory" and target == "inventory":
            self.logger.debug(f"Executing inventory->inventory transfer: {quantity}x '{object_name}'")
            # Try to find the object in any location to be robust
            target_char_name = event.event_target or ""
            found_in_any_location = self._try_transfer_from_any_location(event, object_name, quantity, target_char_name)
            if not found_in_any_location:
                initiator_name = event.event_initiator or ""
                target_name = event.event_target or ""
                self._transfer_between_inventories(initiator_name, object_name, target_name, quantity)
        else:
            self.logger.error(f"Unsupported transfer direction: {source} to {target}")
            raise ValueError(f"Unsupported transfer direction: {source} to {target}")

        # Create action result event
        action_result = Event(
            event_type=EventTypes.ACTION_RESULT,
            event_initiator=event.event_initiator,
            event_subject=object_name,
            event_target=f"{source} -> {target}",
            description=f"Transferred {quantity}x '{object_name}' from {source} to {target}"
        )

        return [action_result]


    def _transfer_from_scene_to_inventory(self, object_name: str, quantity: int):
        """Transfer an object from the scene to the player's inventory."""
        scene_objects = self.state.current_scene.objects
        # Get the first player character (assuming single player for now)
        if not self.state.players:
            raise ValueError("No player characters available")
        player_character = self.state.players[0].character

        # Find the object in the scene
        obj = self._find_object_in_list(object_name, scene_objects)
        if not obj:
            raise ValueError(f"Object '{object_name}' not found in scene")

        # Check if we're dealing with a container's contained object
        container = None
        actual_obj = obj
        if hasattr(obj, 'contained_objects') and obj.contained_objects:
            # If the object itself is a container, look for the contained object
            contained_obj = self._find_object_in_list(object_name, obj.contained_objects)
            if contained_obj:
                container = obj
                actual_obj = contained_obj

        # Log the transfer details
        self.logger.debug(f"Transferring {quantity}x '{actual_obj.name}' from scene to {player_character.name}'s inventory")
        self.logger.debug(f"Before transfer - Object quantity: {actual_obj.quantity}, Player inventory count: {len(player_character.inventory)}")

        # Handle quantity transfer
        if actual_obj.quantity > quantity:
            # Create a new object with the transferred quantity
            transferred_obj = copy.deepcopy(actual_obj)
            transferred_obj.quantity = quantity
            actual_obj.quantity -= quantity

            # Add to player inventory
            player_character.inventory.append(transferred_obj)
            self.logger.debug(f"Partial transfer: reduced scene object quantity to {actual_obj.quantity}, added {transferred_obj.quantity} to inventory")
        else:
            # Transfer the entire object
            if container:
                # Remove from container's contained_objects
                if container.contained_objects: container.contained_objects.remove(actual_obj) # type: ignore
                self.logger.debug(f"Removed '{actual_obj.name}' from container '{container.name}'")
            else:
                # Remove from scene objects
                scene_objects.remove(actual_obj)
                self.logger.debug(f"Removed '{actual_obj.name}' from scene objects")

            # Add to player inventory
            player_character.inventory.append(actual_obj)
            self.logger.debug(f"Full transfer: moved entire object to inventory")

        self.logger.info(f"Transferred {quantity}x '{actual_obj.name}' from scene to inventory")
        self.logger.debug(f"After transfer - Player inventory count: {len(player_character.inventory)}")

    def _transfer_from_inventory_to_scene(self, object_name: str, quantity: int):
        """Transfer an object from the player's inventory to the scene."""
        scene_objects = self.state.current_scene.objects
        # Get the first player character (assuming single player for now)
        if not self.state.players:
            raise ValueError("No player characters available")
        player_character = self.state.players[0].character

        # Find the object in the player's inventory
        obj = self._find_object_in_list(object_name, player_character.inventory)
        if not obj:
            raise ValueError(f"Object '{object_name}' not found in player inventory")

        # Log the transfer details
        self.logger.debug(f"Transferring {quantity}x '{obj.name}' from {player_character.name}'s inventory to scene")
        self.logger.debug(f"Before transfer - Object quantity: {obj.quantity}, Player inventory count: {len(player_character.inventory)}")

        # Handle quantity transfer
        if obj.quantity > quantity:
            # Create a new object with the transferred quantity
            transferred_obj = copy.deepcopy(obj)
            transferred_obj.quantity = quantity
            obj.quantity -= quantity

            # Add to scene objects
            scene_objects.append(transferred_obj)
            self.logger.debug(f"Partial transfer: reduced inventory object quantity to {obj.quantity}, added {transferred_obj.quantity} to scene")
        else:
            # Transfer the entire object
            player_character.inventory.remove(obj)

            # Add to scene objects
            scene_objects.append(obj)
            self.logger.debug(f"Full transfer: moved entire object to scene")

        self.logger.info(f"Transferred {quantity}x '{obj.name}' from inventory to scene")
        self.logger.debug(f"After transfer - Player inventory count: {len(player_character.inventory)}, Scene objects count: {len(scene_objects)}")

    def _transfer_from_container_to_inventory(self, object_name: str, quantity: int):
        """Transfer an object from a container in the scene to the player's inventory."""
        scene_objects = self.state.current_scene.objects
        # Get the first player character (assuming single player for now)
        if not self.state.players:
            raise ValueError("No player characters available")
        player_character = self.state.players[0].character

        # Find the object in any container in the scene
        container, obj = self._find_object_in_containers(object_name, scene_objects)
        if not obj:
            raise ValueError(f"Object '{object_name}' not found in any container in the scene")

        # Log the transfer details
        self.logger.debug(f"Transferring {quantity}x '{obj.name}' from container '{container.name}' to {player_character.name}'s inventory")
        self.logger.debug(f"Before transfer - Object quantity: {obj.quantity}, Player inventory count: {len(player_character.inventory)}")

        # Handle quantity transfer
        if obj.quantity > quantity:
            # Create a new object with the transferred quantity
            transferred_obj = copy.deepcopy(obj)
            transferred_obj.quantity = quantity
            obj.quantity -= quantity

            # Add to player inventory
            player_character.inventory.append(transferred_obj)
            self.logger.debug(f"Partial transfer: reduced container object quantity to {obj.quantity}, added {transferred_obj.quantity} to inventory")
        else:
            # Transfer the entire object
            if container.contained_objects: container.contained_objects.remove(obj) # type: ignore

            # Add to player inventory
            player_character.inventory.append(obj)
            self.logger.debug(f"Full transfer: moved entire object from container to inventory")

        self.logger.info(f"Transferred {quantity}x '{obj.name}' from container '{container.name}' to inventory")
        self.logger.debug(f"After transfer - Player inventory count: {len(player_character.inventory)}, Container objects count: {len(container.contained_objects) if container.contained_objects else 0}")

    def _transfer_from_inventory_to_container(self, object_name: str, quantity: int, target_container_name: str):
        """Transfer an object from the player's inventory to a container in the scene."""
        scene_objects = self.state.current_scene.objects
        # Get the first player character (assuming single player for now)
        if not self.state.players:
            raise ValueError("No player characters available")
        player_character = self.state.players[0].character

        # Find the object in the player's inventory
        obj = self._find_object_in_list(object_name, player_character.inventory)
        if not obj:
            raise ValueError(f"Object '{object_name}' not found in player inventory")

        if not target_container_name:
            raise ValueError("Target container name not specified for inventory to container transfer")

        # Find the target container
        target_container = self._find_object_in_list(target_container_name, scene_objects)
        if not target_container:
            raise ValueError(f"Target container '{target_container_name}' not found in scene")

        # Check if target is actually a container
        if not hasattr(target_container, 'contained_objects'):
            raise ValueError(f"Target '{target_container_name}' is not a container")

        # Check capacity if container has capacity limit
        if hasattr(target_container, 'capacity') and target_container.capacity is not None:
            current_count = len(target_container.contained_objects) # type: ignore
            if current_count >= target_container.capacity:
                raise ValueError(f"Container '{target_container.name}' is at capacity ({target_container.capacity})")

        # Handle quantity transfer
        if obj.quantity > quantity:
            # Create a new object with the transferred quantity
            transferred_obj = copy.deepcopy(obj)
            transferred_obj.quantity = quantity
            obj.quantity -= quantity

            # Add to container's contained_objects
            target_container.contained_objects.append(transferred_obj) # type: ignore
        else:
            # Transfer the entire object
            player_character.inventory.remove(obj)

            # Add to container's contained_objects
            target_container.contained_objects.append(obj) # type: ignore

        self.logger.info(f"Transferred {quantity}x '{obj.name}' from inventory to container '{target_container.name}'")

    def _transfer_from_container_to_container(self, object_name: str, quantity: int, target_container_name: str):
        """Transfer an object from one container to another container in the scene."""
        scene_objects = self.state.current_scene.objects

        # Find the object in any container in the scene
        source_container, obj = self._find_object_in_containers(object_name, scene_objects)
        if not obj:
            raise ValueError(f"Object '{object_name}' not found in any container in the scene")

        if not target_container_name:
            raise ValueError("Target container name not specified for container to container transfer")

        # Find the target container
        target_container = self._find_object_in_list(target_container_name, scene_objects)
        if not target_container:
            raise ValueError(f"Target container '{target_container_name}' not found in scene")

        # Check if target is actually a container
        if not hasattr(target_container, 'contained_objects'):
            raise ValueError(f"Target '{target_container_name}' is not a container")

        # Check capacity if container has capacity limit
        if hasattr(target_container, 'capacity') and target_container.capacity is not None:
            current_count = len(target_container.contained_objects) # type: ignore
            if current_count >= target_container.capacity:
                raise ValueError(f"Container '{target_container.name}' is at capacity ({target_container.capacity})")

        # Handle quantity transfer
        if obj.quantity > quantity:
            # Create a new object with the transferred quantity
            transferred_obj = copy.deepcopy(obj)
            transferred_obj.quantity = quantity
            obj.quantity -= quantity

            # Add to target container's contained_objects
            
            if target_container.contained_objects: target_container.contained_objects.append(transferred_obj)
        else:
            # Transfer the entire object
            if source_container.contained_objects: source_container.contained_objects.remove(obj)

            # Add to target container's contained_objects
            if target_container.contained_objects: target_container.contained_objects.append(obj)

        self.logger.info(f"Transferred {quantity}x '{obj.name}' from container '{source_container.name}' to container '{target_container.name}'")

    def _find_object_in_list(self, name: str, objects: List[UnifiedObject]) -> UnifiedObject:
        """Find an object by name in a list of objects, including nested containers."""
        for obj in objects:
            if obj.name.lower() == name.lower():
                return obj
            # Also check in contained objects recursively
            if hasattr(obj, 'contained_objects') and obj.contained_objects:
                found = self._find_object_in_list(name, obj.contained_objects)
                if found:
                    return found
        return None # type: ignore

    def _find_object_in_containers(self, name: str, scene_objects: List[UnifiedObject]) -> Tuple[UnifiedObject, UnifiedObject]:
        """Find an object by name in any container within the scene objects."""
        for container in scene_objects:
            if hasattr(container, 'contained_objects') and container.contained_objects:
                for contained_obj in container.contained_objects:
                    if contained_obj.name.lower() == name.lower():
                        return container, contained_obj
                    # Recursively check nested containers
                    nested_container, nested_obj = self._find_nested_object_in_containers(name, container.contained_objects)
                    if nested_obj:
                        return nested_container, nested_obj
        return None, None # type: ignore # type: ignore

    def _find_nested_object_in_containers(self, name: str, objects: List[UnifiedObject]) -> Tuple[UnifiedObject, UnifiedObject]:
        """Helper method to find an object in nested containers."""
        for container in objects:
            if hasattr(container, 'contained_objects') and container.contained_objects:
                for contained_obj in container.contained_objects:
                    if contained_obj.name.lower() == name.lower():
                        return container, contained_obj
                    # Recursively check deeper nested containers
                    nested_container, nested_obj = self._find_nested_object_in_containers(name, container.contained_objects)
                    if nested_obj:
                        return nested_container, nested_obj
        return None, None # type: ignore

    def _transfer_between_inventories(self, initiator_name: str, object_name: str, target_character_name: str, quantity: int):
        """Transfer an object from one character's inventory to another character's inventory."""
        # Find the source character (initiator) and target character
        source_character = None
        target_character = None

        # Find source character (the one initiating the transfer)
        for player in self.state.players:
            if player.character.name.lower() in initiator_name.lower() or initiator_name.lower() in player.character.name.lower():
                source_character = player.character
                break
        if not source_character:
            for npc in self.state.npcs:
                if npc.character.name.lower() in initiator_name.lower() or initiator_name.lower() in npc.character.name.lower():
                    source_character = npc.character
                    break

        # Find target character (the one receiving the transfer)
        for player in self.state.players:
            if player.character.name.lower() in target_character_name.lower() or target_character_name.lower() in player.character.name.lower():
                target_character = player.character
                break
        if not target_character:
            for npc in self.state.npcs:
                if npc.character.name.lower() in target_character_name.lower() or target_character_name.lower() in npc.character.name.lower():
                    target_character = npc.character
                    break

        if not source_character:
            raise ValueError(f"Source character '{initiator_name}' not found")
        if not target_character:
            raise ValueError(f"Target character '{target_character_name}' not found")

        # Find the object in the source character's inventory
        obj = self._find_object_in_list(object_name, source_character.inventory)
        if not obj:
            raise ValueError(f"Object '{object_name}' not found in {source_character.name}'s inventory")

        # Log the transfer details
        self.logger.debug(f"Transferring {quantity}x '{obj.name}' from {source_character.name}'s inventory to {target_character.name}'s inventory")
        self.logger.debug(f"Before transfer - Source inventory count: {len(source_character.inventory)}, Target inventory count: {len(target_character.inventory)}")

        # Handle quantity transfer
        if obj.quantity > quantity:
            # Create a new object with the transferred quantity
            transferred_obj = copy.deepcopy(obj)
            transferred_obj.quantity = quantity
            obj.quantity -= quantity

            # Add to target character's inventory
            target_character.inventory.append(transferred_obj)
            self.logger.debug(f"Partial transfer: reduced source object quantity to {obj.quantity}, added {transferred_obj.quantity} to target inventory")
        else:
            # Transfer the entire object
            source_character.inventory.remove(obj)

            # Add to target character's inventory
            target_character.inventory.append(obj)
            self.logger.debug(f"Full transfer: moved entire object to target inventory")

        self.logger.info(f"Transferred {quantity}x '{obj.name}' from {source_character.name}'s inventory to {target_character.name}'s inventory")
        self.logger.debug(f"After transfer - Source inventory count: {len(source_character.inventory)}, Target inventory count: {len(target_character.inventory)}")

    def _try_transfer_from_any_location(self, event: Event, object_name: str, quantity: int, target_character_name: str) -> bool:
        """Try to transfer an object from any possible location (inventories, scene, containers).

        Returns True if the object was found and transferred, False otherwise.
        """
        # Look for the object in all possible locations
        all_characters = self.state.get_all_characters()

        # First, check all character inventories
        for character in all_characters:
            # Skip the target character (the one receiving the item)
            if character.name.lower() in target_character_name.lower() or target_character_name.lower() in character.name.lower():
                continue

            # Look for the object in this character's inventory
            obj, container = self._find_object_in_character_inventory(character, object_name)
            if obj:
                # Found the object in this character's inventory (possibly in a container)
                return self._perform_transfer_from_character_to_target(character, obj, container, quantity, target_character_name)

        # Next, check the scene objects
        scene_obj, container = self._find_object_in_scene(object_name)
        if scene_obj:
            # Found the object in the scene (possibly in a container)
            return self._perform_transfer_from_scene_to_target(scene_obj, container, quantity, target_character_name)

        # Object not found anywhere
        self.logger.warning(f"Object '{object_name}' not found in any location for transfer")
        return False

    def _find_object_in_character_inventory(self, character, object_name: str):
        """Find an object in a character's inventory, including nested containers."""
        # First, check the main inventory
        obj = self._find_object_in_list(object_name, character.inventory)
        if obj:
            return obj, None  # Found directly in inventory

        # Then, check nested containers in the inventory
        for item in character.inventory:
            if hasattr(item, 'contained_objects') and item.contained_objects:
                nested_obj = self._find_object_in_list(object_name, item.contained_objects)
                if nested_obj:
                    return nested_obj, item  # Found in a container within inventory

        return None, None

    def _find_object_in_scene(self, object_name: str):
        """Find an object in the scene, including nested containers."""
        # First, check the main scene objects
        obj = self._find_object_in_list(object_name, self.state.current_scene.objects)
        if obj:
            return obj, None  # Found directly in scene

        # Then, check nested containers in the scene
        for scene_obj in self.state.current_scene.objects:
            if hasattr(scene_obj, 'contained_objects') and scene_obj.contained_objects:
                nested_obj = self._find_object_in_list(object_name, scene_obj.contained_objects)
                if nested_obj:
                    return nested_obj, scene_obj  # Found in a container in scene

        return None, None

    def _perform_transfer_from_character_to_target(self, source_character, obj, container, quantity: int, target_character_name: str) -> bool:
        """Perform transfer from a character's inventory (or container within inventory) to target character."""
        # Find the target character
        target_character = None
        for player in self.state.players:
            if player.character.name.lower() in target_character_name.lower() or target_character_name.lower() in player.character.name.lower():
                target_character = player.character
                break
        if not target_character:
            for npc in self.state.npcs:
                if npc.character.name.lower() in target_character_name.lower() or target_character_name.lower() in npc.character.name.lower():
                    target_character = npc.character
                    break

        if not target_character:
            self.logger.error(f"Target character '{target_character_name}' not found")
            return False

        # Log the transfer details
        location_desc = f"in {container.name}" if container else "directly"
        self.logger.debug(f"Transferring {quantity}x '{obj.name}' from {source_character.name}'s inventory ({location_desc}) to {target_character.name}'s inventory")
        self.logger.debug(f"Before transfer - Source inventory count: {len(source_character.inventory)}, Target inventory count: {len(target_character.inventory)}")

        # Handle quantity transfer
        if obj.quantity > quantity:
            # Create a new object with the transferred quantity
            transferred_obj = copy.deepcopy(obj)
            transferred_obj.quantity = quantity
            obj.quantity -= quantity

            # Add to target character's inventory
            target_character.inventory.append(transferred_obj)
            self.logger.debug(f"Partial transfer: reduced source object quantity to {obj.quantity}, added {transferred_obj.quantity} to target inventory")
        else:
            # Transfer the entire object
            if container:
                # Remove from container within inventory
                container.contained_objects.remove(obj)
            else:
                # Remove from main inventory
                source_character.inventory.remove(obj)

            # Add to target character's inventory
            target_character.inventory.append(obj)
            self.logger.debug(f"Full transfer: moved entire object to target inventory")

        self.logger.info(f"Transferred {quantity}x '{obj.name}' from {source_character.name}'s inventory to {target_character.name}'s inventory")
        self.logger.debug(f"After transfer - Source inventory count: {len(source_character.inventory)}, Target inventory count: {len(target_character.inventory)}")
        return True

    def _perform_transfer_from_scene_to_target(self, scene_obj, container, quantity: int, target_character_name: str) -> bool:
        """Perform transfer from scene (or container within scene) to target character."""
        # Find the target character
        target_character = None
        for player in self.state.players:
            if player.character.name.lower() in target_character_name.lower() or target_character_name.lower() in player.character.name.lower():
                target_character = player.character
                break
        if not target_character:
            for npc in self.state.npcs:
                if npc.character.name.lower() in target_character_name.lower() or target_character_name.lower() in npc.character.name.lower():
                    target_character = npc.character
                    break

        if not target_character:
            self.logger.error(f"Target character '{target_character_name}' not found")
            return False

        # Log the transfer details
        location_desc = f"in {container.name}" if container else "directly"
        self.logger.debug(f"Transferring {quantity}x '{scene_obj.name}' from scene ({location_desc}) to {target_character.name}'s inventory")
        self.logger.debug(f"Before transfer - Scene objects count: {len(self.state.current_scene.objects)}, Target inventory count: {len(target_character.inventory)}")

        # Handle quantity transfer
        if scene_obj.quantity > quantity:
            # Create a new object with the transferred quantity
            transferred_obj = copy.deepcopy(scene_obj)
            transferred_obj.quantity = quantity
            scene_obj.quantity -= quantity

            # Add to target character's inventory
            target_character.inventory.append(transferred_obj)
            self.logger.debug(f"Partial transfer: reduced scene object quantity to {scene_obj.quantity}, added {transferred_obj.quantity} to target inventory")
        else:
            # Transfer the entire object
            if container:
                # Remove from container within scene
                container.contained_objects.remove(scene_obj)
            else:
                # Remove from main scene objects
                self.state.current_scene.objects.remove(scene_obj)

            # Add to target character's inventory
            target_character.inventory.append(scene_obj)
            self.logger.debug(f"Full transfer: moved entire object to target inventory")

        self.logger.info(f"Transferred {quantity}x '{scene_obj.name}' from scene to {target_character.name}'s inventory")
        self.logger.debug(f"After transfer - Scene objects count: {len(self.state.current_scene.objects)}, Target inventory count: {len(target_character.inventory)}")
        return True