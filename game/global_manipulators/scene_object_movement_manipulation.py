from game.manipulators.base_manipulation import BaseManipulation
from skls_generator.generator import Generator
from schemas.orchestration import Event, EventTypes, SpatialMovementBreakdown
from thefuzz import process
from typing import List
from logging import Logger
from game.engine import Session
from schemas.in_game import Coordinate2D


class SceneObjectMovementManipulation(BaseManipulation):
    """Handles movement of objects within a single scene in 3D space."""
    
    task_rules = """
    1. Interpret object movement commands to determine destination coordinates
    2. Calculate appropriate movement path based on scene dimensions and object position
    3. Generate new coordinates that represent realistic movement within the scene
    4. Respect scene boundaries when calculating new positions
    5. Consider the distance between current and target positions for movement feasibility
    6. Only move objects that are present in the current scene
    """

    event_types_binded = [
        EventTypes.ITEM_MOVEMENT,
        EventTypes.OBJECT_TRANSFER  # Also handle object movement as part of transfer
    ]

    def __init__(self, generator: Generator, state: Session, archive, logger: Logger) -> None:
        super().__init__(generator, logger)
        self.state = state
        self.archive = archive

    def manipulate(self, event: Event) -> List[Event]:
        # Get spatial distances if available
        from utils.spatial_utils import calculate_spatial_distances
        spatial_info = calculate_spatial_distances(self.state, event)

        # Find the object to move based on event information
        target_object_name = event.event_subject or event.event_target
        if not target_object_name:
            self.logger.warning("No target object specified in event")
            return []

        # Look for the object in the current scene
        scene_objects = self.state.current_scene.objects
        object_names = [obj.name for obj in scene_objects]

        best_match = process.extractOne(target_object_name, object_names)
        if not best_match:
            self.logger.warning(f"No object found matching '{target_object_name}' in current scene")
            return []

        target_object_name = best_match[0]
        target_object = None

        for obj in scene_objects:
            if obj.name == target_object_name:
                target_object = obj
                break

        if not target_object:
            self.logger.warning(f"Object '{target_object_name}' not found in current scene")
            return []

        # Ensure the object has a position field
        if not target_object.position:
            target_object.position = Coordinate2D(x=0, y=0)

        # Create prompt for spatial movement breakdown
        prompt = f"""
        Process the following object movement event and generate a detailed spatial movement breakdown:

        Event: {event}

        Spatial Information (if applicable):
        {spatial_info}

        Current object position: ({target_object.position.x}, {target_object.position.y})

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
        target_pos = self._calculate_target_position(target_object, movement_breakdown)

        # Calculate the distance between current and target positions
        distance = self._calculate_distance_3d(target_object.position, target_pos)

        # Update object position if it's within scene bounds
        if self._is_position_within_scene_bounds(target_pos):
            old_position = target_object.position
            target_object.position = target_pos

            # Create action result event
            action_result = Event(
                event_type=EventTypes.ACTION_RESULT,
                event_initiator=event.event_initiator,
                event_subject=target_object.name,
                event_target=f"moved to ({target_pos.x}, {target_pos.y})",
                description=f"Object {target_object.name} moved from ({old_position.x}, {old_position.y}) "
                           f"to ({target_pos.x}, {target_pos.y}). Distance: {distance:.2f} {self.state.current_scene.scale_unit}"
            )

            self.logger.info(f"Object {target_object.name} moved to ({target_pos.x}, {target_pos.y})")
            return [action_result]
        else:
            self.logger.warning(f"Failed to move object {target_object.name} to invalid position")
            return []

    def _calculate_target_position(self, obj, breakdown: 'SpatialMovementBreakdown') -> Coordinate2D:
        """Calculate the target position based on the movement breakdown."""
        current_pos = obj.position

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
                    for scene_obj in self.state.current_scene.objects:
                        if breakdown.target_reference.lower() in scene_obj.name.lower():
                            target_obj = scene_obj
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

    def _is_position_within_scene_bounds(self, position: Coordinate2D) -> bool:
        """Check if a position is within the current scene bounds."""
        scene = self.state.current_scene
        half_x = scene.dimensions.x / 2
        half_y = scene.dimensions.y / 2

        min_x = scene.center_position.x - half_x
        max_x = scene.center_position.x + half_x
        min_y = scene.center_position.y - half_y
        max_y = scene.center_position.y + half_y

        return (min_x <= position.x <= max_x and
                min_y <= position.y <= max_y)

    def _calculate_distance_3d(self, pos1: Coordinate2D, pos2: Coordinate2D) -> float:
        """Calculate Euclidean distance between two 2D coordinates."""
        dx = pos2.x - pos1.x
        dy = pos2.y - pos1.y
        return (dx**2 + dy**2)**0.5