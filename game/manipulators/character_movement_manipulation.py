from game.manipulators.base_manipulation import BaseManipulation
from skls_generator.generator import Generator
from schemas.orchestration import Event, EventTypes, SpatialMovementBreakdown
from thefuzz import process
from typing import List, TYPE_CHECKING
from logging import Logger
from schemas.in_game import Coordinate2D, Character

if TYPE_CHECKING:
    from game.engine import Session

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

    def __init__(self, generator: Generator, logger: Logger, session: 'Session') -> None:
        super().__init__(generator, logger)
        self.state = session

    def manipulate(self, character: Character, event: Event) -> List[Event]:
        # Get spatial distances if available
        from utils.spatial_utils import calculate_spatial_distances
        spatial_info = calculate_spatial_distances(self.state, event)

        # Determine the character to move (it's the character itself)
        target_character = character

        # Create prompt for spatial movement breakdown
        prompt = f"""
        Process the following movement event and generate a detailed spatial movement breakdown:

        Event: {event}

        Spatial Information (if applicable):
        {spatial_info}

        Current character position: ({target_character.position.x}, {target_character.position.y})

        Scene context:
        - Scene center: ({self.state.current_scene.center_position.x}, {self.state.current_scene.center_position.y})
        - Scene dimensions: {self.state.current_scene.dimensions.x} x {self.state.current_scene.dimensions.y} {self.state.current_scene.scale_unit}
        - Scene scale unit: {self.state.current_scene.scale_unit}

        Available characters in scene: {[char.name for char in self.state.get_all_characters()]}

        Following these rules:
        {self.task_rules}

        Generate an appropriate spatial movement breakdown based on the movement described in the event.
        """

        movement_breakdown = self.generator.generate_one_shot(
            pydantic_model=SpatialMovementBreakdown,
            prompt=prompt
        )

        # Calculate the target position based on the movement breakdown
        target_pos = self._calculate_target_position(target_character, movement_breakdown)

        # Calculate the distance between current and target positions
        distance = self._calculate_distance_3d(target_character.position, target_pos)

        # Update character position if it's within scene bounds
        if self.state.move_character_to_position(character, target_pos):
            # Create action result event
            action_result = Event(
                event_type=EventTypes.ACTION_RESULT,
                event_initiator=event.event_initiator,
                event_subject=target_character.name,
                event_target=f"moved to ({target_pos.x}, {target_pos.y})",
                description=f"Character {target_character.name} moved from ({target_character.position.x}, {target_character.position.y}) "
                           f"to ({target_pos.x}, {target_pos.y}). Distance: {distance:.2f} {self.state.current_scene.scale_unit}"
            )

            self.logger.info(f"Character {target_character.name} moved to ({target_pos.x}, {target_pos.y})")
            return [action_result]
        else:
            self.logger.warning(f"Failed to move character {target_character.name} to invalid position")
            return []

    def _calculate_target_position(self, character: Character, breakdown: 'SpatialMovementBreakdown') -> Coordinate2D:
        """Calculate the target position based on the movement breakdown."""
        current_pos = character.position

        if breakdown.movement_type == "directional":
            # Apply directional movement
            if breakdown.direction_vector and breakdown.distance:
                # Normalize the direction vector and multiply by distance
                dir_vec = breakdown.direction_vector
                # Simple normalization (in a real implementation, you'd want proper vector normalization)
                length = (dir_vec.x**2 + dir_vec.y**2)**0.5
                if length > 0:
                    normalized_dir = Coordinate2D(
                        x=dir_vec.x / length,
                        y=dir_vec.y / length
                    )
                    target_pos = Coordinate2D(
                        x=current_pos.x + normalized_dir.x * breakdown.distance,
                        y=current_pos.y + normalized_dir.y * breakdown.distance
                    )
                else:
                    target_pos = current_pos  # No movement if direction vector is zero
            else:
                target_pos = current_pos  # Default to no movement if incomplete data

        elif breakdown.movement_type == "relative_to_target":
            # Move relative to a target character/object
            if breakdown.target_reference:
                # First, try to find the target in characters
                all_characters = self.state.get_all_characters()
                target_obj = None
                for char in all_characters:
                    if breakdown.target_reference.lower() in char.name.lower():
                        target_obj = char
                        break

                # If not found in characters, try to find in scene objects
                if not target_obj:
                    for obj in self.state.current_scene.objects:
                        if breakdown.target_reference.lower() in obj.name.lower():
                            target_obj = obj
                            break

                if target_obj and hasattr(target_obj, 'position'):
                    # Calculate position relative to the target
                    if breakdown.target_offset:
                        target_pos = Coordinate2D(
                            x=target_obj.position.x + breakdown.target_offset.x, # type: ignore
                            y=target_obj.position.y + breakdown.target_offset.y # type: ignore
                        )
                    else:
                        # Default to moving to the target's position
                        target_pos = target_obj.position
                else:
                    # If target not found, default to current position
                    target_pos = current_pos
            else:
                target_pos = current_pos  # Default to no movement if no target specified

        elif breakdown.movement_type == "specific_coordinates":
            # Use specific coordinates if provided
            if breakdown.specific_coordinates:
                target_pos = breakdown.specific_coordinates
            else:
                target_pos = current_pos  # Default to no movement if no coordinates provided

        else:
            # Default fallback - no movement
            target_pos = current_pos

        return target_pos # type: ignore

    def _calculate_distance_3d(self, pos1: Coordinate2D, pos2: Coordinate2D) -> float:
        """Calculate Euclidean distance between two 2D coordinates."""
        dx = pos2.x - pos1.x
        dy = pos2.y - pos1.y
        return (dx**2 + dy**2)**0.5