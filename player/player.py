from logging import Logger
from typing import TYPE_CHECKING

from schemas.orchestration import Message, OrchestrationVerdict, OrchestrationVerdictType, UserInterationType
if TYPE_CHECKING:
    from game.engine import Session
from game.orchestrator import Orchestrator
from schemas.in_game import Character, GameModes


class Player:
    def __init__(self, character: Character,
                 logger: Logger,
                 orchestrator: Orchestrator,
                 ) -> None:
        self.character = character
        self.logger = logger
        self.orchestrator = orchestrator
        self._session: 'Session | None' = None
        
    
    @property
    def session(self) -> "Session":
        if self._session is None:
            raise ValueError("Session not injected to a Player!")
        return self._session
    
        
    def inject_state(self, state : 'Session') -> None:
        self._session = state
       
    def request_terminal_input(self) -> str:
        # Prepare the prompt with proper encoding handling
        prompt = (
            f"\033[35mPlayer {self.character.name}, enter your action "
            f"(current position: ({self.character.position.x}, "
            f"{self.character.position.y}, {self.character.position.z})): \033[0m"
        )
        return input(prompt)
        
    def run(self) -> OrchestrationVerdict:
        """Player's turn. Returns the player's action decision or none if a player skips their turn. (Mostly for combat mode.)"""
       
        self.logger.debug(f"Waiting for player input for {self.character.name}")

        

        request = self.request_terminal_input()
        
        if request.strip() == "":
            return OrchestrationVerdict()

        new_message = Message(
            sender_name=self.character.name,
            text=request)
        self.session.new_message(new_message)
        
        user_interaction = self.orchestrator.request(
            username=self.character.name,
            request_text=request
        )
        
        if user_interaction.interaction_type == UserInterationType.CHARACTER_ACTION:
            if self.session.game_mode == GameModes.COMBAT:
                return self.orchestrator.character_action_combat(
                    character=self,
                    request_text=request,
                    processed_interaction=user_interaction
                )
            else:
                return self.orchestrator.character_action_story(
                    character=self,
                    request_text=request,
                    processed_interaction=user_interaction
                )
        elif user_interaction.interaction_type == UserInterationType.META_COMMENT:
            return OrchestrationVerdict(
                verdict_type=OrchestrationVerdictType.META_REQUEST,
                details=request
            )

        return OrchestrationVerdict()