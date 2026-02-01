from typing import List
from game.manipulators.base_manipulation import BaseManipulation
from skls_generator.generator import Generator
from schemas.orchestration import CharacterTransferBreakdown, CharacterTransferDecision, Event, EventTypes
from logging import Logger
from game.engine import Session
from schemas.in_game import SceneNode


class CharacterTransferManipulation(BaseManipulation):
    """Handles moving characters between scenes or creating characters."""

    task_rules = f"""
    1. Analyze the event to determine if characters are trying to leave the current scene
    2. Check if the intended destination is already connected in the location graph
    3. If it's a connected location, transfer the character there
    4. If it's a new direction/location, generate a new location and connect it
    5. Only transfer player characters (not NPCs)
    6. Consider the scene context and character positions when making decisions
    7. If multiple players are involved, handle all of them appropriately
    """

    event_types_binded = [EventTypes.CHARACTER_TRANSFER,
                         EventTypes.LOCATION_CHANGE]

    def __init__(self, generator : Generator, state : Session, archive, logger : Logger) -> None:
        super().__init__(generator, state, archive, logger)

    def manipulate(self, event: Event) -> List[Event]:
        # Get spatial distances if available
        from utils.spatial_utils import calculate_spatial_distances
        spatial_info = calculate_spatial_distances(self.state, event)

        # Create a prompt for the LLM to decide on character transfers
        prompt = f"""
        Analyze the following event and decide if any characters should be transferred to a different location:

        Event: {event}

        Spatial Information (if applicable):
        {spatial_info}
        Follow these rules:
        {self.task_rules}

        Scene Context:
        {self.state.get_session_context()}

        Generate a decision on character transfers.
        """

        decision = self.generator.generate_one_shot(
            pydantic_model=CharacterTransferDecision,
            prompt=prompt
        )

        results = []
        if decision.will_transfer:
            for breakdown in decision.transfer_breakdowns:
                self._execute_transfer(breakdown, decision)

                # Create action result event for each transfer
                action_result = Event(
                    event_type=EventTypes.ACTION_RESULT,
                    event_initiator=event.event_initiator,
                    event_subject=breakdown.character_name,
                    event_target=breakdown.target_location,
                    description=f"Transferred character '{breakdown.character_name}' to location '{breakdown.target_location}'"
                )
                results.append(action_result)

        return results if results else []

    def _execute_transfer(self, breakdown: CharacterTransferBreakdown, decision: CharacterTransferDecision):
        """Execute the character transfer based on the breakdown."""
        self.logger.debug(f"Executing character transfer: {breakdown.character_name} -> {breakdown.target_location} (is_new: {breakdown.is_new_location})")

        # Find the character by name (first check player characters, then NPCs)
        target_character = None
        character_source = "player"  # Track if this is a player or NPC

        # First, check player characters
        for char in self.state.players:
            if char.character.name.lower() == breakdown.character_name.lower():
                target_character = char.character
                character_source = "player"
                break

        # If not found in players, check NPCs
        if not target_character:
            for npc_obj in self.state.npcs:
                if npc_obj.character.name.lower() == breakdown.character_name.lower():
                    target_character = npc_obj.character
                    character_source = "npc"
                    break

        if not target_character:
            self.logger.warning(f"Character '{breakdown.character_name}' not found in player characters or NPCs")
            return

        self.logger.debug(f"Found character {target_character.name} for transfer")

        if breakdown.is_new_location:
            # Create a new location and connect it
            new_scene = self._generate_new_location(breakdown.target_location, decision.new_location_description, breakdown.exit_direction)
            self.state.add_location_to_graph(breakdown.target_location, new_scene)
            self.state.connect_locations(self.state.current_scene.name, breakdown.target_location)
            self.logger.info(f"Created new location '{breakdown.target_location}' and connected it to '{self.state.current_scene.name}'")
        else:
            # Check if the target location exists in the graph
            if breakdown.target_location not in self.state.all_locations:
                self.logger.warning(f"Target location '{breakdown.target_location}' not found in location graph")
                return

            # Check if the locations are connected
            connected_locs = self.state.get_connected_locations(self.state.current_scene.name)
            if breakdown.target_location not in connected_locs:
                self.state.connect_locations(self.state.current_scene.name, breakdown.target_location)
                self.logger.info(f"Connected '{self.state.current_scene.name}' to '{breakdown.target_location}'")

        # Change the current location for the session
        success = self.state.change_current_location(breakdown.target_location)
        if success:
            self.logger.info(f"Transferred character '{target_character.name}' to '{breakdown.target_location}'")
            self.logger.debug(f"Character {target_character.name} successfully transferred from {self.state.current_scene.name} to {breakdown.target_location}")
        else:
            self.logger.warning(f"Failed to transfer character '{target_character.name}' to '{breakdown.target_location}'")

    def _generate_new_location(self, location_name: str, description_hint: str, exit_direction: str) -> SceneNode:
        """Generate a new location using the LLM."""
        # Create a prompt to generate the new location
        prompt = f"""
        Generate a detailed scene description for a new location called '{location_name}'.

        Description hint: {description_hint or 'Provide a generic description based on the location name.'}

        Exit direction from the previous location: {exit_direction}

        The location should be appropriate for a fantasy RPG setting and fit well with the current game context.

        Current scene context: {self.state.current_scene.description}

        Generate a complete SceneNode with appropriate:
        - Name: {location_name}
        - Description: Detailed description of the location
        - Center position: Appropriate position based on the exit direction from the previous location
        - Dimensions: Appropriate dimensions for the location type
        - Scale unit: Same as the current scene
        """

        # Generate the new scene using the LLM
        new_scene = self.generator.generate_one_shot(
            pydantic_model=SceneNode,
            prompt=prompt
        )

        return new_scene