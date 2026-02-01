from game.manipulators.base_manipulation import BaseManipulation
from skls_generator.generator import Generator
from schemas.orchestration import Event, EventTypes, NPCTransferDecision, NPCTransferBreakdown
from thefuzz import process
from typing import List
from logging import Logger
from game.engine import Session
from schemas.in_game import SceneNode


class NPCTransferManipulation(BaseManipulation):
    """Handles moving NPCs between scenes independently from player characters."""

    task_rules = f"""
    1. Analyze the event to determine if NPCs are trying to leave the current scene
    2. Check if the intended destination is already connected in the location graph
    3. If it's a connected location, transfer only the specific NPC there (not player characters)
    4. If it's a new direction/location, generate a new location and connect it
    5. Only transfer the specific NPC mentioned (not the entire party)
    6. Consider the scene context and NPC motivations when making decisions
    7. NPCs can move independently of player characters
    """

    event_types_binded = [EventTypes.NPC_TRANSFER]

    def __init__(self, generator : Generator, state : Session, archive, logger : Logger) -> None:
        super().__init__(generator, state, archive, logger)

    def manipulate(self, event: Event) -> List[Event]:
        # Get spatial distances if available
        from utils.spatial_utils import calculate_spatial_distances
        spatial_info = calculate_spatial_distances(self.state, event)

        self.logger.debug(f"Processing NPC transfer event: {event.event_type.value} - {event.description}")
        self.logger.debug(f"Event context: {event.event_initiator} -> {event.event_subject} -> {event.event_target}")

        # Create a prompt for the LLM to decide on NPC transfers
        prompt = f"""
        Analyze the following event and decide if any NPCs should be transferred to a different location:

        Event: {event}

        Spatial Information (if applicable):
        {spatial_info}

        Follow these rules:
        {self.task_rules}

        Scene Context:
        {self.state.get_session_context()}

        Generate a decision on NPC transfers.
        """

        decision = self.generator.generate_one_shot(
            pydantic_model=NPCTransferDecision,
            prompt=prompt
        )

        self.logger.debug(f"NPC transfer decision: will_transfer={decision.will_transfer}, {len(decision.transfer_breakdowns)} breakdowns")

        results = []
        if decision.will_transfer:
            for breakdown in decision.transfer_breakdowns:
                self.logger.debug(f"Processing NPC transfer breakdown: {breakdown.npc_name} -> {breakdown.target_location}")
                self._execute_transfer(breakdown, decision)

                # Create action result event for each NPC transfer
                action_result = Event(
                    event_type=EventTypes.ACTION_RESULT,
                    event_initiator=event.event_initiator,
                    event_subject=breakdown.npc_name,
                    event_target=breakdown.target_location,
                    description=f"Transferred NPC '{breakdown.npc_name}' to location '{breakdown.target_location}'"
                )
                results.append(action_result)

        return results if results else []

    def _execute_transfer(self, breakdown: NPCTransferBreakdown, decision: NPCTransferDecision):
        """Execute the NPC transfer based on the breakdown."""
        self.logger.debug(f"Executing NPC transfer: {breakdown.npc_name} -> {breakdown.target_location} (is_new: {breakdown.is_new_location})")

        # Find the NPC by name
        target_npc = None
        for npc in self.state.npcs:
            if npc.character.name.lower() == breakdown.npc_name.lower():
                target_npc = npc
                break

        if not target_npc:
            self.logger.warning(f"NPC '{breakdown.npc_name}' not found in NPCs")
            return

        self.logger.debug(f"Found NPC {target_npc.character.name} for transfer")

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

        # Update the NPC's current scene to reflect their new location
        old_scene = target_npc.character.current_scene
        target_npc.character.current_scene = breakdown.target_location

        # Move only the specific NPC to the new location (don't change the session's current location)
        # For now, we'll just log that the NPC has moved - in a real implementation,
        # we might want to track NPC locations separately
        self.logger.info(f"NPC '{target_npc.character.name}' moved to '{breakdown.target_location}' independently")
        self.logger.debug(f"NPC {target_npc.character.name} transferred from scene '{old_scene}' to '{breakdown.target_location}'")

    def _generate_new_location(self, location_name: str, description_hint: str, exit_direction: str) -> SceneNode:
        """Generate a new location using the LLM."""
        # Create a prompt to generate the new location
        prompt = f"""
        Generate a detailed scene description for a new location called '{location_name}'.
        
        Description hint: {description_hint or 'Provide a generic description based on the location name.'}
        
        Exit direction from the previous location: {exit_direction or 'unknown'}
        
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