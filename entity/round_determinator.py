from typing import TYPE_CHECKING
from schemas.orchestration import Event, EventTypes
from schemas.in_game import Character, GameModes

if TYPE_CHECKING:
    from logging import Logger
    from game.engine import Session

class RoundDeterminator:
    """Special object that analyzes game state and determines if mode changes are needed."""
    
    def __init__(self, round_duration : int) -> None:
        self._logger : 'Logger | None' = None
        self._session: 'Session | None' = None
        self.round_duration = round_duration

    @property
    def session(self) -> "Session":
        if self._session is None:
            raise ValueError("Session not injected to RoundDeterminator!")
        return self._session

    @property
    def logger(self) -> "Logger":
        if self._logger is None:
            raise ValueError("Session not injected to RoundDeterminator! (logging is not available)")
        return self._logger


    def inject_state(self, state: 'Session') -> None:
        self._session = state
        self._logger = state.logger.getChild("RounDeterminator")

    def run(self)  -> list[Event]:
        """Analyze game state and determine if mode changes are needed."""
        
        self._cleanup_expired_conditions()
        self._analyze_game_state()
        return []        

    def _cleanup_expired_conditions(self):
        """Check all characters and remove expired conditions."""
       
    def _analyze_game_state(self):
        """Analyze the current game state to determine the appropriate game mode."""
        