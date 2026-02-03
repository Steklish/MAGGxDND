from logging import Logger
from typing import TYPE_CHECKING, List

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from game.engine import Session
from game.manipulators.base_manipulation import BaseManipulation
from schemas.orchestration import Event, EventTypes
from schemas.in_game import Coordinate2D


class MovementBreakdown(BaseModel):
    """Breakdown of a movement action."""
    character_name: str = Field(..., description="Name of the character moving")
    target_position: Coordinate2D = Field(..., description="Target position to move to")
    movement_description: str = Field(..., description="Description of the movement action")
    movement_successful: bool = Field(True, description="Whether the movement was successful")


class MovementManipulator(BaseManipulation):
    event_types_binded = [
        EventTypes.CHARACTER_MOVEMENT,
        EventTypes.CHARACTER_POSITION_UPDATE
    ]

    def __init__(self, state: 'Session'):
        super().__init__(state)
        self.logger.info("MovementManipulator initialized")

    def manipulate(self, event: Event) -> List[Event]:
        """
        Process a movement event and apply the results to the game state.
        """
        self.logger.info(f"Processing movement event: {event.description}")
        character = None
        if event.event_initiator:
            character = self.session.find_entity_by_name(event.event_initiator)
        if character is None:
            raise ValueError(f"Cannot find the character {event.event_initiator}")

        task = self.generator.generate_one_shot(
            pydantic_model=MovementBreakdown,
            prompt=f"""
# Role:
You are an action classifier and you need to determine exact information of a movement action described in artistic form and bind it to its context data.

## Rules:
1. Identify the character that is moving and their target position.
2. Determine if the movement is possible based on scene context, character stats, environment, and terrain.
3. Calculate the distance of the movement based on the starting and ending positions.
4. Provide the movement speed based on the character's stats and the environment.
5. Provide an artistic description of the movement using the environment.

## Scene context:
{self.session.get_session_context()}

## Moving character:
{character.character.short_summary}
"""
        )

        if not task.movement_successful:
            return [Event(
                event_type=EventTypes.ACTION_RESULT,
                description=task.movement_description + f"(movement failed)"
            )]

        # Update character's position
        character.character.position = task.target_position
        
        # Calculate if the movement is within scene bounds
        if self.session.spatial_enabled:
            if not self.session.is_within_scene_bounds(task.target_position, self.session.current_scene):
                self.logger.warning(f"Character {character.character.name} moved outside scene bounds")
                # Optionally, we could return a failure event instead
                # For now, we'll allow the move but log the warning

        events = []
        events.append(Event(
            event_type=EventTypes.ACTION_RESULT,
            description=f"{task.movement_description}"
        ))
        
        self.logger.info(f"🚶Character {character.character.name} moved to position ({task.target_position.x}, {task.target_position.y})")
        return events