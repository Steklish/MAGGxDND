from game.manipulators.base_manipulation import BaseManipulation
from skls_generator.generator import Generator
from schemas.orchestration import Event, EventTypes, SpatialMovementCommand
from thefuzz import process
from typing import List
from logging import Logger
from game.engine import Session
from schemas.in_game import Coordinate3D, UnifiedObject


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
        super().__init__(generator, state, archive, logger)

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

        # Create prompt for spatial movement command
        
        current_object_position = f"Current object position: ({target_object.position.x if hasattr(target_object, 'position') else 0}, {target_object.position.y if hasattr(target_object, 'position') else 0}, {target_object.position.z if hasattr(target_object, 'position') else 0})" # type: ignore
        prompt = f"""
        Process the following object movement event and generate appropriate spatial coordinates:

        Event: {event}
        
        Spatial Information (if applicable):
        {spatial_info}

        {current_object_position}
        
        Scene context:
        - Scene center: ({self.state.current_scene.center_position.x}, {self.state.current_scene.center_position.y}, {self.state.current_scene.center_position.z})
        - Scene dimensions: {self.state.current_scene.dimensions.x} x {self.state.current_scene.dimensions.y} x {self.state.current_scene.dimensions.z} {self.state.current_scene.scale_unit}
        - Scene scale unit: {self.state.current_scene.scale_unit}

        Following these rules:
        {self.task_rules}

        Generate appropriate destination coordinates for the object movement.
        """

        # Ensure the object has a position field
        if not target_object.position:
            target_object.position = Coordinate3D(x=0, y=0, z=0)

        # Generate the movement command
        movement_cmd = self.generator.generate_one_shot(
            pydantic_model=SpatialMovementCommand,
            prompt=prompt
        )

        # Calculate the distance between current and target positions
        current_pos = target_object.position
        target_pos = movement_cmd.target_position
        distance = self._calculate_distance_3d(current_pos, target_pos)

        # Update object position if it's within scene bounds
        if self._is_position_within_scene_bounds(target_pos):
            old_position = target_object.position
            target_object.position = target_pos
            
            # Create action result event
            action_result = Event(
                event_type=EventTypes.ACTION_RESULT,
                event_initiator=event.event_initiator,
                event_subject=target_object.name,
                event_target=f"moved to ({target_pos.x}, {target_pos.y}, {target_pos.z})",
                description=f"Object {target_object.name} moved from ({old_position.x}, {old_position.y}, {old_position.z}) "
                           f"to ({target_pos.x}, {target_pos.y}, {target_pos.z}). Distance: {distance:.2f} {self.state.current_scene.scale_unit}",
                start_position=old_position,
                end_position=target_pos,
                distance=distance
            )

            self.logger.debug(f"Object {target_object.name} moved to ({target_pos.x}, {target_pos.y}, {target_pos.z})")
            return [action_result]
        else:
            self.logger.warning(f"Failed to move object {target_object.name} to invalid position")
            return []

    def _is_position_within_scene_bounds(self, position: Coordinate3D) -> bool:
        """Check if a position is within the current scene bounds."""
        scene = self.state.current_scene
        half_x = scene.dimensions.x / 2
        half_y = scene.dimensions.y / 2
        half_z = scene.dimensions.z / 2

        min_x = scene.center_position.x - half_x
        max_x = scene.center_position.x + half_x
        min_y = scene.center_position.y - half_y
        max_y = scene.center_position.y + half_y
        min_z = scene.center_position.z - half_z
        max_z = scene.center_position.z + half_z

        return (min_x <= position.x <= max_x and
                min_y <= position.y <= max_y and
                min_z <= position.z <= max_z)

    def _calculate_distance_3d(self, pos1: Coordinate3D, pos2: Coordinate3D) -> float:
        """Calculate Euclidean distance between two 3D coordinates."""
        dx = pos2.x - pos1.x
        dy = pos2.y - pos1.y
        dz = pos2.z - pos1.z
        return (dx**2 + dy**2 + dz**2)**0.5