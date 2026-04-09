from typing import TYPE_CHECKING, List
from core.entity.npc import NPC
from core.entity.player import Player
from core.entity.schemas import GameModeActions, RoundDeterminationDecision
from core.game.event_pool import SubscriberQueue
from core.schemas.orchestration import Event, EventTypes
from core.schemas.in_game import Character, Condition, GameModes
from core.utils.threads import run_in_parallel_args, run_list_in_parallel

if TYPE_CHECKING:
    from logging import Logger
    from core.game.engine import Session

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
        """Analyze game state and determine if mode changes are needed. Only runs if there are events."""
        events = self.event_queue.get_all()
        self.event_queue.clear()

        if not events:
            self.logger.debug(f"Round determinator: no events, skipping")
            # Still check character conditions — they may need periodic execution
            self.all_characters_conditions_exec()
            return

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
You are a game mode classifier. Your task is to determine if the game should switch between STORY mode and COMBAT mode based on events and game state.

## CRITICAL COMBAT TRIGGER RULES
**IMMEDIATELY switch to COMBAT mode when ANY of the following occurs:**
1. **Any attack is made** - melee attack, ranged attack, bite, claw, weapon strike, etc.
2. **Any damage is dealt** - HP loss, injury, wound, bleeding, etc.
3. **Any hostile spell is cast** - fireball, magic missile, curse, or any spell targeting an enemy
4. **Any character initiates hostile action** - charging, lunging, drawing weapon with intent to harm
5. **NPC shows clear aggression** - attacking, threatening with immediate violence, initiating combat

**DO NOT end COMBAT mode prematurely:**
- Keep COMBAT mode active until ALL hostile entities are defeated/fled
- Do not switch to STORY mode just because there's a pause in action
- Only end combat when there is clearly no more threat

**Stay in STORY mode when:**
- Characters are talking, exploring, or interacting peacefully
- No hostile actions have occurred
- All characters are cooperating

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

The game master is marked as "Mage".

## DECISION INSTRUCTIONS
Analyze the events above. If you see ANY attack, damage, or hostile action - IMMEDIATELY set suggested_game_mode_action to "CHANGE_TO_COMBAT".

Remember: It is better to start combat TOO EARLY than TOO LATE. Any sign of aggression = COMBAT MODE.
        """
        decision = self.session.generator.generate_one_shot(
            pydantic_model=RoundDeterminationDecision,
            prompt=prompt
        )
        self.logger.debug("Processing decision")
        if decision.suggested_game_mode_action == GameModeActions.CHANGE_TO_COMBAT:
            if self.session.game_mode != GameModes.COMBAT:
                self.session.game_mode = GameModes.COMBAT
                self.logger.info("Game mode changed to COMBAT")
                self.event_queue.publish_to_others(
                    event=Event(
                        event_type=EventTypes.ACTION_RESULT,
                        description="Game mod changed to COMBAT"
                    )
                )
            else:
                self.logger.debug("Game mode already COMBAT, no change needed")
        elif decision.suggested_game_mode_action == GameModeActions.CHANGE_TO_STORY:
            if self.session.game_mode != GameModes.STORY:
                self.session.game_mode = GameModes.STORY
                self.logger.info("Game mode changed to STORY")
                self.event_queue.publish_to_others(
                    event=Event(
                        event_type=EventTypes.ACTION_RESULT,
                        description="Game mod changed to STORY"
                    )
                )
            else:
                self.logger.debug("Game mode already STORY, no change needed")
        elif decision.suggested_game_mode_action == GameModeActions.KEEP_GAME_MODE:
            self.logger.debug("Game mode remains unchanged")
            
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