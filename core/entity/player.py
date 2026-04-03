from logging import Logger
from typing import TYPE_CHECKING

from core.game.event_pool import SubscriberQueue
from core.interface.delivery import Delivery
from core.schemas.orchestration import Event, Message, OrchestrationVerdictType, UserInterationType
if TYPE_CHECKING:
    from core.game.engine import Session
from core.entity.orchestrator import Orchestrator
from core.schemas.in_game import Character, GameModes
from core.entity.game_entity import GameEntity


MAX_LEN = 1000

class Player(GameEntity):
    def __init__(self, character: Character,
                 event_queuee : SubscriberQueue,
                 logger: Logger,
                 orchestrator: Orchestrator,
                 ) -> None:
        super().__init__(character, event_queuee, logger)
        self.orchestrator = orchestrator
        self.character : Character
        # string used for context if character clarifications or rules checks 
        # were interrupted by another player (used for run_story) 
        # should be cleaned after action is complete
        self._input_cache : str = "" 
        
    @property
    def input_cache(self) -> str:
        return self._input_cache

    @input_cache.setter
    def input_cache(self, value: str) -> None:
        # assign new value
        buf = value

        # if too long, drop whole lines from the left at '\n'
        if len(buf) > MAX_LEN:
            # keep only last MAX_LEN chars as a starting point
            buf = buf[-MAX_LEN:]

            # try to drop a partial leading line, if any
            first_newline = buf.find("\n")
            if first_newline != -1:
                # drop everything up to and including that newline
                buf = buf[first_newline + 1 :]

        self._input_cache = buf

        
    def run_story(self, ):
        """A method that runs character in story mode. If an input doesn't result to an accepable action it releases the game loop instead of blockig it like self.run()"""
        
        
        request = self.session.delivery.player_request(self.character)

        if request.strip() == "":
            # Skip turn - return empty list of events
            return

        new_message = Message(
            sender_name=self.character.name,
            text=request)
        self.session.new_message(new_message)

        user_interaction = self.orchestrator.request(
            username=self.character.name,
            request_text=request,
            message_cahce=self._input_cache
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
                executed_events.extend(self.session.manipulator.execute_events(events))
                self._input_cache = ""
                for e in executed_events:
                    self.event_queue.publish_to_others(e)
                return
            elif verdict.verdict_type == OrchestrationVerdictType.CLAIRIFICATION_NEEDED:
                # Unclear action - need clarification from user
                # Send clarification request to game master
                clarification_response = self.session.game_master.clarify_user_request(
                    correction_question=verdict.details if verdict.details else "Action needs clarification"
                )
                self.session.delivery.master_message(
                    text=clarification_response,
                    tag="Clarification"
                )
                
                self._input_cache += f"""{self.character.name} sent: {request} \n master's clarification request: {clarification_response}\n"""
                return 
            
            elif verdict.verdict_type == OrchestrationVerdictType.ILLEGAL_PLAYER_ACTION:
                # Illegal action - request a new one
                illegal_response = self.session.game_master.illegal_action_comment(
                    prompt=request,
                    name=self.character.name,
                    reasoning=verdict.details if verdict.details else "Action is not allowed"
                )
                self.session.delivery.master_message(
                    text=illegal_response,
                    tag="Illegal"
                )
                self._input_cache += f"""{self.character.name} sent: {request} \n master's illegal comment on the previous request: {illegal_response}\n"""
                return 
            
        elif user_interaction.interaction_type == UserInterationType.META_COMMENT:
            # Meta comment - this is a direct question/query to the game master
            # Process it and continue the loop to get an actual action
            meta_response = self.session.game_master.comment_on_meta_request(request)
            self.session.delivery.master_message(
                    text=meta_response,
                    tag="Meta"
                )
            self._input_cache += f"""{self.character.name} sent: {request} \n master's meta comment: {meta_response}\n"""
            return 
    
    def run(self):
        """Player's turn. Returns a list of events based on player action.
        Handles three possible outcomes: legal action, unclear action needing clarification,
        and illegal action requiring a new one."""
        self.session.delivery.draw_ascii_scene(self.session)
        # just in case it stores really old cache not usefull after the combat ends
        self._input_cache = "" 
        while True:
            self.logger.debug(f"Waiting for player input for {self.character.name}")

            request = self.session.delivery.player_request(self.character)

            if request.strip() == "":
                # Skip turn - return empty list of events
                return

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
                    executed_events.extend(self.session.manipulator.execute_events(events))
                    break

                elif verdict.verdict_type == OrchestrationVerdictType.CLAIRIFICATION_NEEDED:
                    # Unclear action - need clarification from user
                    # Send clarification request to game master
                    clarification_response = self.session.game_master.clarify_user_request(
                        correction_question=verdict.details if verdict.details else "Action needs clarification"
                    )
                    self.session.delivery.master_message(
                        text=clarification_response,
                        tag="Clarification"
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
                        text=illegal_response,
                        tag="Illegal"
                    )
                    # Continue the loop to get a new action
                    continue
            elif user_interaction.interaction_type == UserInterationType.META_COMMENT:
                # Meta comment - this is a direct question/query to the game master
                # Process it and continue the loop to get an actual action
                meta_response = self.session.game_master.comment_on_meta_request(request)
                self.session.delivery.master_message(
                        text=meta_response,
                        tag="Meta"
                    )
                # Continue the loop to get a real action from the player
                continue
            
        for e in executed_events:
            self.event_queue.publish_to_others(e)