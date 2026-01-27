from typing import List
from game.manipulators.base_manipulation import BaseManipulation
from schemas.orchestration import Event, EventTypes, SceneManipulationCommand
from skls_generator.generator import Generator
from logging import Logger
from game.engine import Session
from schemas.in_game import SceneNode
from utils.spatial_utils import calculate_spatial_distances


class SceneManipulation(BaseManipulation):
    """Handles changes to the scene, specifically the description field."""
    # the llm prompt
    task_rules = f"""
    1. Use scene names, field names, other values exactly as provided
    2. Use one of the following types of operations replace/set
        2.1 replace/set will update the entire description field with the new value
    3. Target should always be 'description' for scene manipulations
    4. For minor updates do not loose previous details
    """

    event_types_binded = [EventTypes.SCENE_UPDATE,
                          EventTypes.LOCATION_STATUS_CHANGE,
                          EventTypes.LOCATION_MUTATION,
                          EventTypes.CHARACTER_MOVEMENT,
                          EventTypes.CHARACTER_POSITION_UPDATE,
                          EventTypes.CHARACTER_TELEPORT,
                          EventTypes.CHARACTER_PATHFINDING]

    def __init__(self, generator : Generator, state : Session, archive, logger : Logger) -> None:
        super().__init__(generator, state, archive, logger)

    def manipulate(self, event: Event) -> List[Event]:
        # Get the current scene
        current_scene = self.state.current_scene

        # Store before state for action result
        original_description = current_scene.description

        # Calculate spatial distances if relevant
        spatial_info = calculate_spatial_distances(self.state, event)

        task_prompt = f"""Create a specific authoritative task from the event {event}

        Spatial Information (if applicable):
        {spatial_info}

        Follow the following rules {self.task_rules}.

        # object schema for attribute matches:
        {SceneNode.schema()}

        # current scene:
        {self.state.current_scene.dict()}"""

        task = self.generator.generate_one_shot(
            pydantic_model=SceneManipulationCommand,
            prompt=task_prompt
        )

        self.logger.debug(f"Scene manipulation task generated: {task}")
        self._apply_change(current_scene, task)

        # Create action result event
        action_result = Event(
            event_type=EventTypes.ACTION_RESULT,
            event_initiator=event.event_initiator,
            event_subject=current_scene.name,
            event_target="description",
            description=f"Updated scene description from '{original_description}' to '{current_scene.description}'",
            start_position=event.start_position,
            end_position=event.end_position,
            distance=event.distance
        )

        return [action_result]

    def _apply_change(self, scene: SceneNode, task: SceneManipulationCommand):
        """Applies changes to the scene description field."""

        self.logger.debug(f"Applying scene change: {task.operation} {task.target} with value '{task.value}' (current: '{getattr(scene, task.target, 'N/A')}')")

        # Since we're only dealing with the description field, we can directly handle it
        if task.target.lower() != 'description':
            raise ValueError(f"SceneManipulation only supports 'description' field, got: {task.target}")

        if task.operation in ["replace", "set"]:
            old_description = scene.description
            scene.description = task.value
            self.logger.debug(f"📝 Scene description changed: '{old_description}' -> '{scene.description}'")
        else:
            raise ValueError(f"SceneManipulation only supports 'replace' or 'set' operations, got: {task.operation}")