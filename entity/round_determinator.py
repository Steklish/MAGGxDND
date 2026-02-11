from typing import TYPE_CHECKING, List
from entity.npc import NPC
from entity.player import Player
from entity.schemas import GameModeActions, RoundDeterminationDecision
from game.event_pool import SubscriberQueue
from schemas.orchestration import Event, EventTypes
from schemas.in_game import Character, Condition, GameModes
from utils.threads import run_in_parallel_args, run_list_in_parallel

if TYPE_CHECKING:
    from logging import Logger
    from game.engine import Session

class RoundDeterminator:
    """Special object that analyzes game state and determines if mode changes are needed."""
    
    def __init__(self, 
                 round_duration : int,
                 event_queue : SubscriberQueue) -> None:
        self._logger : 'Logger | None' = None
        self._session: 'Session | None' = None
        self.round_duration = round_duration
        self.event_queue = event_queue

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

    def _events_to_string(self, events : List[Event]) -> str:
        events_str = ""
        for i, e in enumerate(events):
            events_str += f"Event {i+1}: {str(e.dict())}\n"
        return events_str


    def inject_state(self, state: 'Session') -> None:
        self._session = state
        self._logger = state.logger.getChild("RounDeterminator")
    
    def run(self):
        """Analyze game state and determine if mode changes are needed."""
        events = self.event_queue.get_all() 
        self.event_queue.clear()
        self.logger.debug(f"Running round determinator at game time {self.session.turn_time} for [{len(events)}] events")
        
        run_list_in_parallel(
            funcs=[
                self.all_characters_conditions_exec,
                self.get_game_mode_and_expred_conditions_decision
            ],
            args_list=[
                (),
                (events,)
            ]
        )
        
    
    def get_game_mode_and_expred_conditions_decision(self, events : list[Event]):
        prompt = f"""
## ROLE
You are a game classificator. You need to update game mode and active characters conditions.
<game_state>
{self.session.get_session_context()}
</game_state>

### INPUT DATA
<current_events>
{self._events_to_string(events)}
</current_events>

<in game messages>
{self.session.get_messages_formatted()}
</in game messages>

the game master is marked as "Mage".

Update game mode if there is an indicator. Dont end battles too early and but start them immediately as any agression was brought up. It is more likely to start battle when early signs of agression is being shown.
        """
        decision = self.session.generator.generate_one_shot(
            pydantic_model=RoundDeterminationDecision,
            prompt=prompt
        )
        self.logger.debug("Processing decision")
        if decision.suggested_game_mode_action == GameModeActions.CHANGE_TO_COMBAT:
            self.session.game_mode = GameModes.COMBAT
            self.logger.info("Game mode changed to COMBAT")
            self.event_queue.publish_to_others(
                event=Event(
                    event_type=EventTypes.ACTION_RESULT,
                    description="Game mod changed to COMBAT"
                )
            )
        elif decision.suggested_game_mode_action == GameModeActions.CHANGE_TO_STORY:
            self.session.game_mode = GameModes.STORY
            self.logger.info("Game mode changed to STORY")
            self.event_queue.publish_to_others(
                event=Event(
                    event_type=EventTypes.ACTION_RESULT,
                    description="Game mod changed to STORY"
                )
            )
            
        for char in decision.expired_conditions.keys():
            c = self.session.find_entity_by_name(char)
            if c:
                c.remove_condition_by_name(decision.expired_conditions[char])
            else:
                self.logger.debug(f"Could not find entity {char} to remove expired condition {decision.expired_conditions[char]}")
        
    
    def _execute_condition(self, character : Player | NPC, condition : Condition):
        self.logger.debug(f"Executing condition {condition.name} for {character.character.name}")
        self.session.manipulator._external_action_as_an_entity(
            prompt=condition.periodic_effect_description,
            actor=character
        )

    def _conditions_for_character(self, character : Player | NPC):
        args = [(character, c) for c in character.character.active_conditions_list]
        run_in_parallel_args(
            func=self._execute_condition,
            arg_lists=args
        )
        
    def all_characters_conditions_exec(self):
        """Executing al character conditions in parallel for all characters which are currently active"""
        self.logger.debug(f"Checking character conditions in parallel for [{len(self.session.get_all_active_entities())}] entities")
        run_in_parallel_args(
            func=self._conditions_for_character,
            arg_lists=[(c,) for c in self.session.get_all_active_entities()]
        )