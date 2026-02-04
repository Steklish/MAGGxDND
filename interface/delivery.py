from abc import ABC, abstractmethod
from schemas.in_game import Character


class Delivery(ABC):
    """A class that is responsible for interaction with the system. Now handling the cli."""
    
    @abstractmethod
    def master_message(self, text : str, tag : str | None = None):
        pass    
    
    @abstractmethod
    def player_request(self, character : Character) -> str:
        pass