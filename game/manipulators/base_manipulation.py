from logging import Logger
from typing import TYPE_CHECKING, Any, List
if TYPE_CHECKING:
    from game.engine import Session
import json
from schemas.orchestration import Event


class Archive:
    """Manages storage and retrieval of unused game objects. For consistency."""
    def __init__(self, directory: str = "/data"):
        self.directory =  directory # Base directory for data files where currently unused object stored in a file

    def store(self, object):
        """Stores objects that are no longer in the current scene for future use."""
        with open(f"{self.directory}/archive.json", "r") as file:
            archive = json.load(file)

        archive.append(object)
        with open(f"{self.directory}/archive.json", "w") as file:
            json.dump(archive, file)

    def retrieve(self, object_type: str):
        """Retrieves stored all objects by type for the manipulator to decide what to do with an LLM."""
        with open(f"{self.directory}/archive.json", "r") as file:
            archive = json.load(file)
        return [obj for obj in archive if obj['type'] == object_type]


class BaseManipulation:
    event_types_binded = []
    def __init__(self, generator, state : 'Session', archive, logger : Logger) -> None:
        self.generator = generator
        self.archive = archive
        self.state = state
        self.logger = logger

    def get_related_objects(self, event : Event) -> List[Any]:
        character_pool = self.state.player_characters + [n.character for n in self.state.npcs]
        names = [c.name for c in character_pool]
        selected_objects = []
        for name in names:
            if name == event.event_initiator or name == event.event_subject:
                selected_objects.append(name)
        return selected_objects


    def execute(self, event: Event):
        """Executes the manipulation based on the provided prompt. (Wrapper)"""
        self.logger.debug(f"Executing manipulation {self.__class__.__name__}")
        result = self.manipulate(event)
        return result if result is not None else []

    def manipulate(self, event: Event) -> List[Event]:
        """Core manipulation logic to be implemented by subclasses."""
        raise NotImplementedError("This method should be overridden by subclasses.")