from logging import Logger
from game.orchestrator import Orchestrator
from schemas.in_game import Character


class Player:
    def __init__(self, character: Character,
                 logger: Logger,
                 orchestrator: Orchestrator,
                 ) -> None:
        self.character = character
        self.logger = logger
        self.orchestrator = orchestrator

    def run(self, *arg, **kwarg) -> str | None:
        """Player's turn. Returns the player's action decision or none if a player skips their turn."""
        # In a real implementation, this would get input from the actual player
        # For now, returning None to indicate the player is waiting for input
        self.logger.debug(f"Waiting for player input for {self.character.name}")
        requestt = input(f"Player {self.character.name}, enter your action: ")
        return requestt
        # This would typically wait for user input through an interface
        # For now, we return None to indicate no action taken
        return None
        