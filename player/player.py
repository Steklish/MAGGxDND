from logging import Logger
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from game.engine import Session
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
        kwarg.setdefault("state", None)
        state = kwarg["state"]
        if not state:
            self.logger.warning("Player run called without state")
            raise ValueError("State is required for player run")
        else:
            state : 'Session' = state
        
        self.logger.debug(f"Waiting for player input for {self.character.name}")
        request = input(
            f"\033[35mPlayer {self.character.name}, enter your action "
            f"(current position: ({self.character.position.x}, "
            f"{self.character.position.y}, {self.character.position.z})): \033[0m"
        )
        state.game_master.memory += f"\nPlayer {self.character.name} action input: {request}\n" # type: ignore
        
        if request.strip() == "":
            return None
        return request

        