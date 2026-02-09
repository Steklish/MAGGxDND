from logging import Logger
from typing import List
from entity.npc import NPC
from entity.player import Player
from game.engine import Session
from skls_generator.generator import Generator
from schemas.orchestration import Event, EventList, EventTypes
from game.manipulators.base_manipulation import Archive, BaseManipulation
from game.manipulators.melee_attack_manipulation import MeleeAttackBreakdown, MeleeAttackManipulator
from game.manipulators.ranged_attack_manipulation import RangedAttackManipulator
from game.manipulators.movement_manipulator import MovementManipulator
from game.manipulators.scene_object_movement_manipulator import SceneObjectMovementManipulator
from game.manipulators.object_transfer_manipulator import ObjectTransferManipulator
from game.manipulators.item_interaction_manipulator import ItemInteractionManipulator
from utils.threads import run_in_parallel_args


class Manipulator:
    def __init__(self, generator : Generator, state : Session, archive : Archive | None, logger : Logger, entity_specific: bool = False) -> None:
        self.generator = generator
        self.manipulations : List[BaseManipulation] = []
        self.session = state
        self.archive = archive
        self.logger = logger
        self.entity_specific = entity_specific
        self.logger.info(f"Manipulator initialized (entity_specific={entity_specific})")

        # Initialize manipulations
        self._init_manipulations()

    def _init_manipulations(self):
        """Initialize all available manipulations."""
        # Add melee attack manipulator
        self.manipulations.append(MeleeAttackManipulator(self.session))

        # Add ranged attack manipulator
        self.manipulations.append(RangedAttackManipulator(self.session))

        # Add movement manipulator
        self.manipulations.append(MovementManipulator(self.session))

        # Add scene object movement manipulator
        self.manipulations.append(SceneObjectMovementManipulator(self.session))

        # Add object transfer manipulator
        self.manipulations.append(ObjectTransferManipulator(self.session))

        # Add item interaction manipulator
        self.manipulations.append(ItemInteractionManipulator(self.session))

        self.logger.info(f"Initialized {len(self.manipulations)} manipulations")
        
    
    def _external_action_as_a_supervisor(self, prompt):
        """Perform a privileged external action within the game session. (DM moves)"""
    
    def _external_action_as_an_entity(self, prompt: str, actor : NPC | Player) -> List[Event]:
        """Perform a non-privileged external action within the game session. (Entity moves)"""

        rules = f"""
        1. Determine which objects involved into the request.
        2. Be the most specific (if there is a certain object in the scene you should set event type to item-based not the entire scene)
        3. Choose the appropriate event type based on the action being performed:
        4. There are special types of requests from user when in battle. If an attack requested you Must generate an event that includes damage calculation based on character and item stats.
        5. Do not generate ACTION_RESULT events.
        """
        prompt_text = f"""
        You need to generate authoritative events based on the situation and a request e.g. "The dragon gets 1d8+2 damage. (based on items properties)" or "character 1 hits character 2 with a sword and dealing 1d6+3 damage"

        # AVAILABLE EVENT TYPES:
        {"\n".join(self.get_event_types())}

        # prompt
        {f"## actor: {actor}\nrequest: " if actor else ""}
        {prompt}
        # scene:
        {self.session.get_session_context()}

        # Last messages history (meta game) - for references:
        {self.session.get_messages_formatted()}

        # Rules:
        {rules}
        """
        events = self.generator.generate_one_shot(
            pydantic_model=EventList,
            prompt=prompt_text
        )
        
        # Add the system notification event to the list of events to be returned
        # This allows the calling entity to publish all events properly to other entities
        system_event = Event(
            event_type=EventTypes.SYSTEM,
            description=f"Character {actor.character.name} required action {prompt}"
        )
        
        # Return both the generated events and the system notification
        return events.event_list + [system_event]

    def execute_events(self, events: list[Event]) -> List[Event]:
        """Executes a list of events in parallel"""
        self.logger.debug(f"Executing [{len(events)}] in parallel")
        res = run_in_parallel_args(
            func=self._execute_event,
            arg_lists=[(e,) for e in events]
        )
        events_produced = []
        for r in res:
            events_produced += r
        return events_produced
            
        

    def _execute_event(self, event: Event) -> List[Event]:
        """
        Execute an event through the appropriate manipulator based on event type.
        """
        
        # Find the appropriate manipulator for this event type
        for manipulator in self.manipulations:
            if manipulator.can_handle_event_type(event.event_type):
                return manipulator.execute(event, self.manipulations)

        # If no specific manipulator is found, return an empty list
        self.logger.warning(f"No manipulator found for event type: {event.event_type}")
        return []
    
    def init_manipulators(self):
        self.manipulations.append(MeleeAttackManipulator(self.session))
        
    def get_event_types(self) -> list[str]:
        res = []
        for m in self.manipulations:
            for e in m.event_types_binded:
                res += [f"Allowed event type {e._value_}. Description [{e.description}]"]
        return res
             