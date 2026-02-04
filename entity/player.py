from logging import Logger
from typing import TYPE_CHECKING

from game.event_pool import SubscriberQueue
from interface.delivery import Delivery
from schemas.orchestration import Event, Message, OrchestrationVerdictType, UserInterationType
if TYPE_CHECKING:
    from game.engine import Session
from entity.orchestrator import Orchestrator
from schemas.in_game import Character, GameModes
from entity.game_entity import GameEntity


class Player(GameEntity):
    def __init__(self, character: Character,
                 event_queuee : SubscriberQueue,
                 logger: Logger,
                 orchestrator: Orchestrator,
                 ) -> None:
        super().__init__(character, event_queuee, logger)
        self.orchestrator = orchestrator
        self.character : Character
       
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
        self.session.draw_ascii_scene()
        while True:
            self.logger.debug(f"Waiting for player input for {self.character.name}")

            request = self.session.delivery.player_request(self.character)

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
            executed_events = []
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
                if verdict.verdict_type == OrchestrationVerdictType.ALLOWED_PLAYER_ACTION:
                    events = self.session.manipulator._external_action_as_an_entity(verdict.details if verdict.details else request, self)
                    for event in events:
                        executed_events.extend(self.session.manipulator.execute_event(event))

                elif verdict.verdict_type == OrchestrationVerdictType.CLAIRIFICATION_NEEDED:
                    # Unclear action - need clarification from user
                    # Send clarification request to game master
                    clarification_response = self.session.game_master.clarify_user_request(
                        correction_question=verdict.details if verdict.details else "Action needs clarification"
                    )
                    self.session.delivery.master_message(
                        text=clarification_response,
                        tag="Clarfication"
                    )
                    # Continue the loop to get a new action
                    continue
                elif verdict.verdict_type == OrchestrationVerdictType.ILLEGAL_PLAYER_ACTION:
                    # Illegal action - request a new one
                    illegal_response = self.session.game_master.illegal_action_comment(
                        prompt=request,
                        name=self.character.name,
                        reasoning=verdict.details if verdict.details else "Action is not allowed"
                    )
                    self.session.delivery.master_message(
                        text=clarification_response,
                        tag="Illeal"
                    )
                    # Continue the loop to get a new action
                    continue
            elif user_interaction.interaction_type == UserInterationType.META_COMMENT:
                # Meta comment - this is a direct question/query to the game master
                # Process it and continue the loop to get an actual action
                meta_response = self.session.game_master.comment_on_meta_request(request)
                self.session.delivery.master_message(
                        text=clarification_response,
                        tag="Meta"
                    )
                # Continue the loop to get a real action from the player
                continue
            for e in executed_events:
                self.event_queue.publish_to_others(e)