from logging import Logger
from typing import TYPE_CHECKING

from schemas.orchestration import Event, Message, OrchestrationVerdictType, UserInterationType
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
            f"{self.character.position.y})): \033[0m"
        )
        return input(prompt)
        
    def run(self) -> list[Event]:
        """Player's turn. Returns a list of events based on player action.
        Handles three possible outcomes: legal action, unclear action needing clarification,
        and illegal action requiring a new one."""

        while True:
            self.logger.debug(f"Waiting for player input for {self.character.name}")

            request = self.request_terminal_input()

            if request.strip() == "":
                # Skip turn - return empty list of events
                return []

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
                    verdict = self.orchestrator.character_action_combat(
                        character=self,
                        request_text=request,
                        processed_interaction=user_interaction
                    )
                else:
                    verdict = self.orchestrator.character_action_story(
                        character=self,
                        request_text=request,
                        processed_interaction=user_interaction
                    )

                # Handle the three possible outcomes
                if verdict.verdict_type == OrchestrationVerdictType.ALLOWED_PLAYER_ACTION:
                    # Legal action - proceed to generate events
                    return self.session.manipulator.external_action(verdict.details if verdict.details else request)
                elif verdict.verdict_type == OrchestrationVerdictType.CLAIRIFICATION_NEEDED:
                    # Unclear action - need clarification from user
                    # Send clarification request to game master
                    clarification_response = self.session.game_master.clarify_user_request(
                        correction_question=verdict.details if verdict.details else "Action needs clarification"
                    )
                    print(f"\033[31mDM Clarification: {clarification_response}\033[0m")
                    # Continue the loop to get a new action
                    continue
                elif verdict.verdict_type == OrchestrationVerdictType.ILLEGAL_PLAYER_ACTION:
                    # Illegal action - request a new one
                    illegal_response = self.session.game_master.illegal_action_comment(
                        prompt=request,
                        name=self.character.name,
                        reasoning=verdict.details if verdict.details else "Action is not allowed"
                    )
                    print(f"\033[31mDM Illegal Action: {illegal_response}\033[0m")
                    # Continue the loop to get a new action
                    continue
            elif user_interaction.interaction_type == UserInterationType.META_COMMENT:
                # Meta comment - this is a direct question/query to the game master
                # Process it and continue the loop to get an actual action
                meta_response = self.session.game_master.comment_on_meta_request(request)
                print(f"\033[31mDM Meta Response: {meta_response}\033[0m")
                # Continue the loop to get a real action from the player
                continue

            # Default case - return empty list
            return []