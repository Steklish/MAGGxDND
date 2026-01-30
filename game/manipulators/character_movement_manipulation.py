from game.manipulators.base_manipulation import BaseManipulation
from skls_generator.generator import Generator
from schemas.orchestration import Event, EventTypes, SpatialMovementCommand
from thefuzz import process
from typing import List
from logging import Logger
from game.engine import Session
from schemas.in_game import Coordinate3D


class CharacterMovementManipulation(BaseManipulation):
    """Handles character movement within a single scene in 3D space."""
    
    task_rules = """
    1. Interpret movement commands to determine destination coordinates
    2. Calculate appropriate movement path based on scene dimensions and character position
    3. Generate new coordinates that represent realistic movement within the scene
    4. Respect scene boundaries when calculating new positions
    5. Consider the distance between current and target positions for movement feasibility
    """

    event_types_binded = [
        EventTypes.CHARACTER_MOVEMENT,
        EventTypes.CHARACTER_POSITION_UPDATE,
        EventTypes.CHARACTER_PATHFINDING
    ]

    def __init__(self, generator: Generator, state: Session, archive, logger: Logger) -> None:
        super().__init__(generator, state, archive, logger)

    def manipulate(self, event: Event) -> List[Event]:
        # Get spatial distances if available
        from utils.spatial_utils import calculate_spatial_distances
        spatial_info = calculate_spatial_distances(self.state, event)

        # Determine the character to move
        names = [c.name for c in self._get_all_caracters()]
        
        # Find the character based on event information
        target_name = event.event_subject or event.event_initiator or event.event_target
        if not target_name:
            self.logger.warning("No target character specified in event")
            return []
            
        best_match = process.extractOne(target_name, names)
        if not best_match:
            self.logger.warning(f"No character found matching '{target_name}'")
            return []
            
        target_name = best_match[0]
        target_character = None
        
        for char in self._get_all_caracters():
            if char.name == target_name:
                target_character = char
                break
                
        if not target_character:
            self.logger.warning(f"Character '{target_name}' not found")
            return []

        # Create prompt for spatial movement command
        prompt = f"""
        Process the following movement event and generate appropriate spatial coordinates:

        Event: {event}
        
        Spatial Information (if applicable):
        {spatial_info}

        Current character position: ({target_character.position.x}, {target_character.position.y}, {target_character.position.z})

        Scene context:
        - Scene center: ({self.state.current_scene.center_position.x}, {self.state.current_scene.center_position.y}, {self.state.current_scene.center_position.z})
        - Scene dimensions: {self.state.current_scene.dimensions.x} x {self.state.current_scene.dimensions.y} x {self.state.current_scene.dimensions.z} {self.state.current_scene.scale_unit}
        - Scene scale unit: {self.state.current_scene.scale_unit}

        Following these rules:
        {self.task_rules}

        Generate appropriate destination coordinates for the character movement.
        """

        movement_cmd = self.generator.generate_one_shot(
            pydantic_model=SpatialMovementCommand,
            prompt=prompt
        )

        # Calculate the distance between current and target positions
        current_pos = target_character.position
        target_pos = movement_cmd.target_position
        distance = self._calculate_distance_3d(current_pos, target_pos)

        # Update character position if it's within scene bounds
        if self.state.move_character_to_position(target_character, target_pos, self.state.current_scene):
            # Create action result event
            action_result = Event(
                event_type=EventTypes.ACTION_RESULT,
                event_initiator=event.event_initiator,
                event_subject=target_character.name,
                event_target=f"moved to ({target_pos.x}, {target_pos.y}, {target_pos.z})",
                description=f"Character {target_character.name} moved from ({current_pos.x}, {current_pos.y}, {current_pos.z}) "
                           f"to ({target_pos.x}, {target_pos.y}, {target_pos.z}). Distance: {distance:.2f} {self.state.current_scene.scale_unit}",
                start_position=current_pos,
                end_position=target_pos,
                distance=distance
            )

            self.logger.info(f"Character {target_character.name} moved to ({target_pos.x}, {target_pos.y}, {target_pos.z})")
            return [action_result]
        else:
            self.logger.warning(f"Failed to move character {target_character.name} to invalid position")
            return []

    def _calculate_distance_3d(self, pos1: Coordinate3D, pos2: Coordinate3D) -> float:
        """Calculate Euclidean distance between two 3D coordinates."""
        dx = pos2.x - pos1.x
        dy = pos2.y - pos1.y
        dz = pos2.z - pos1.z
        return (dx**2 + dy**2 + dz**2)**0.5