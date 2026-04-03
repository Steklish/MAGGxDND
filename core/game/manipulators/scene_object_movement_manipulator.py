from typing import TYPE_CHECKING, List

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from core.game.engine import Session
from core.game.manipulators.base_manipulation import BaseManipulation
from core.schemas.orchestration import Event, EventTypes
from core.schemas.in_game import Coordinate2D, UnifiedObject


class SceneObjectMovementBreakdown(BaseModel):
    """Breakdown of a scene object movement action."""
    object_name: str = Field(..., description="Name of the object being moved")
    target_position: Coordinate2D = Field(..., description="Target position to move the object to")
    movement_distance: float = Field(..., description="Distance of the movement in units")
    movement_description: str = Field(..., description="Description of the movement action")
    movement_successful: bool = Field(True, description="Whether the movement was successful")
    movement_reason: str = Field(..., description="Reason why the object was moved")


class SceneObjectMovementManipulator(BaseManipulation):
    event_types_binded = [
        EventTypes.ITEM_MOVEMENT,
        EventTypes.OBJECT_TRANSFER
    ]

    def __init__(self, state: 'Session'):
        super().__init__(state)
        self.logger.info("SceneObjectMovementManipulator initialized")

    def manipulate(self, event: Event) -> List[Event]:
        """
        Process a scene object movement event and apply the results to the game state.
        """
        self.logger.info(f"Processing scene object movement event: {event.description}")
        
        task = self.generator.generate_one_shot(
            pydantic_model=SceneObjectMovementBreakdown,
            prompt=f"""
# Role:
You are an action classifier and you need to determine exact information of a scene object movement action described in artistic form and bind it to its context data.

## Rules:
1. Identify the object that is being moved and its target position.
2. Determine if the movement is possible based on scene context, object properties, environment, and terrain.
3. Calculate the distance of the movement based on the starting and ending positions.
4. Provide the reason for the movement (e.g., pushed by character, moved by mechanism, etc.).
5. Provide an artistic description of the movement using the environment.

## Scene context:
{self.session.get_session_context()}

## Movement event:
{event.description}
"""
        )

        if not task.movement_successful:
            return [Event(
                event_type=EventTypes.ACTION_RESULT,
                description=task.movement_description + f"(object movement failed)"
            )]

        # Find the object in the current scene
        target_object = None
        for obj in self.session.current_scene.objects:
            if obj.name.lower() == task.object_name.lower():
                target_object = obj
                break
        
        if target_object is None:
            self.logger.warning(f"Can't find scene object {task.object_name} (skipped)")
            return [Event(
                event_type=EventTypes.ACTION_RESULT,
                description=f"(object movement failed) (can't find object {task.object_name})"
            )]

        # Update object's position
        target_object.position = task.target_position

        # Calculate if the movement is within scene bounds
        if self.session.spatial_enabled:
            if not self.session.is_within_scene_bounds(task.target_position, self.session.current_scene):
                self.logger.warning(f"Object {target_object.name} moved outside scene bounds")
                # Optionally, we could return a failure event instead
                # For now, we'll allow the move but log the warning

        events = []
        events.append(Event(
            event_type=EventTypes.ACTION_RESULT,
            description=f"{task.movement_description} (moved {task.movement_distance:.2f} units because {task.movement_reason})"
        ))
        
        self.logger.info(f"📦Object {target_object.name} moved to position ({task.target_position.x}, {task.target_position.y})")
        return events