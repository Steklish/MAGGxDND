from game.manipulators.base_manipulation import BaseManipulation
from schemas.orchestration import Event, EventTypes, SceneManipulationCommand
from skls_generator.generator import Generator
from logging import Logger
from game.engine import Session
from schemas.in_game import SceneNode


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
                          EventTypes.LOCATION_MUTATION]

    def __init__(self, generator : Generator, state : Session, archive, logger : Logger) -> None:
        super().__init__(generator, state, archive, logger)

    def manipulate(self, event: Event):
        # Get the current scene
        current_scene = self.state.current_scene

        task_prompt = f"create a specific authoritative task from the event {event} \n\n Follow the following rules {self.task_rules}.\n\n # object schema for attribute matches: \n {SceneNode.schema()} # current scene:\n{self.state.current_scene.dict()}"

        task = self.generator.generate_one_shot(
            pydantic_model=SceneManipulationCommand,
            prompt=task_prompt
        )

        self.logger.debug(f"Scene manipulation task generated: {task}")
        self._apply_change(current_scene, task)

    def _apply_change(self, scene: SceneNode, task: SceneManipulationCommand):
        """Applies changes to the scene description field."""

        # Since we're only dealing with the description field, we can directly handle it
        if task.target.lower() != 'description':
            raise ValueError(f"SceneManipulation only supports 'description' field, got: {task.target}")

        if task.operation in ["replace", "set"]:
            old_description = scene.description
            scene.description = task.value
            self.logger.debug(f"📝 Scene description changed: '{old_description}' -> '{scene.description}'")
        else:
            raise ValueError(f"SceneManipulation only supports 'replace' or 'set' operations, got: {task.operation}")