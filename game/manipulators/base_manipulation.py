from abc import ABC, abstractmethod
from logging import Logger
from typing import TYPE_CHECKING, Any, List
if TYPE_CHECKING:
    from game.engine import Session
import json
from schemas.orchestration import Event, EventTypes


class Archive:
    """Manages storage and retrieval of unused game objects. For consistency."""
    def __init__(self, directory: str = "/data"):
        self.directory =  directory # Base directory for data files where currently unused object stored in a file

    def store(self, object):
        """Stores objects that are no longer in the current scene for future use."""
        with open(f"{self.directory}/archive.json", "r", encoding="utf-8") as file:
            archive = json.load(file)

        archive.append(object)
        with open(f"{self.directory}/archive.json", "w", encoding="utf-8") as file:
            json.dump(archive, file)

    def retrieve(self, object_type: str):
        """Retrieves stored all objects by type for the manipulator to decide what to do with an LLM."""
        with open(f"{self.directory}/archive.json", "r", encoding="utf-8") as file:
            archive = json.load(file)
        return [obj for obj in archive if obj['type'] == object_type]


class BaseManipulation(ABC):
    event_types_binded : list[EventTypes] = []
    def __init__(self, state : 'Session') -> None:
        self.session = state
        self.generator = self.session.generator
        self.logger = self.session.logger.getChild(self.__class__.__name__)

    def _get_all_caracters(self):
        return [n.character for n in self.session.players] + [n.character for n in self.session.npcs]
        
    def get_related_objects(self, event : Event) -> List[Any]:
        names = [c.name for c in self._get_all_caracters()]
        selected_objects = []
        for name in names:
            if name == event.event_initiator or name == event.event_subject:
                selected_objects.append(name)
        return selected_objects


    def execute(self, event: Event, manipulators_list):
        """Executes the manipulation based on the provided prompt. (Wrapper)"""
        self.logger.debug(f"Executing manipulation {self.__class__.__name__}")
        result = self.manipulate(event)
        self.session.delivery.session_updated(self.session)
        return result if result is not None else []

    @abstractmethod
    def manipulate(self, event: Event) -> List[Event]:
        """Core manipulation logic to be implemented by subclasses."""
        raise NotImplementedError("This method should be overridden by subclasses.")

    def can_handle_event_type(self, event_type):
        """Check if this manipulation can handle the given event type."""
        return event_type in self.event_types_binded

    def get_event_type_descriptions_for_prompt(self):
        """Returns a string with descriptions of all supported event types for this manipulation, formatted for LLM prompts."""
        descriptions = []
        for event_type in self.event_types_binded:
            desc = event_type.description if hasattr(event_type, 'description') else str(event_type)
            descriptions.append(f"- {event_type.value}: {desc}")
        return "\n".join(descriptions)