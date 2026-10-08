from typing import TYPE_CHECKING, List, Optional
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from core.game.engine import Session
from core.game.manipulators.base_manipulation import BaseManipulation
from core.schemas.orchestration import Event, EventTypes


class LocationTransitionBreakdown(BaseModel):
    """Breakdown of a location/scene transition action."""
    destination_name: str = Field(..., description="Target name of the destination room, area, or location")
    description: Optional[str] = Field(None, description="Atmospheric or visual description of the destination")
    transition_successful: bool = Field(True, description="Whether the transition is possible based on environment and barriers")
    transition_narrative: str = Field(..., description="Vivid description of the party traveling to or entering the new location")


class LocationManipulator(BaseManipulation):
    event_types_binded = [
        EventTypes.LOCATION_CHANGE,
        EventTypes.CHARACTER_TRANSFER,
    ]

    def __init__(self, state: 'Session'):
        super().__init__(state)
        self.logger.info("LocationManipulator initialized")

    def manipulate(self, event: Event) -> List[Event]:
        """
        Process a location transition event and apply the results to the game state.
        """
        self.logger.info(f"Processing location transition event: {event.description}")

        destination_hint = event.event_subject or ""

        task = self.generator.generate_one_shot(
            pydantic_model=LocationTransitionBreakdown,
            prompt=f"""
# Role:
You are an action classifier determining scene transition and movement between locations.

## Rules:
1. Identify the intended destination name (room, dungeon wing, outdoor area, portal, etc.).
2. If the user refers to an existing exit or door, name the destination appropriately.
3. If this is traveling to an already known connected location, use that exact name.
4. If traveling to an unvisited or new area, choose an evocative, thematic name.
5. Determine if the transition is successful.
6. Provide an artistic description of the party traveling or entering.

## Scene context:
{self.session.get_session_context()}

## Event subject / hint:
{destination_hint}

## Event description:
{event.description}
"""
        )

        if not task.transition_successful:
            return [Event(
                event_type=EventTypes.ACTION_RESULT,
                description=f"{task.transition_narrative} (Transition blocked)"
            )]

        dest_name = task.destination_name.strip()
        if not dest_name:
            dest_name = destination_hint or "Adjacent Area"

        # Execute session transition
        self.session.transition_to_location(dest_name, description=task.description)

        return [Event(
            event_type=EventTypes.ACTION_RESULT,
            description=task.transition_narrative
        )]
