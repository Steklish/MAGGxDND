import threading
import time
from logging import Logger
from game.event_pool import EventPool, SubscriberQueue
from npcs.schemas import NPCActDecision
from schemas.in_game import Character, NPCCharacter
from schemas.orchestration import Event, EventTypes
from skls_generator.generator import Generator

MEMORY_LENGTH_LIMIT = 2000  # characters


class NPC:
    """The idea is that the NPC class creature is intependent actor 
    (independent from game master/ narrator) but the narrator 
    will describe its actions. 
    It listens to the events and decides if to act or not.
    
    If an NPC acts after an event, it will generate a new event.
    
    Multiple events can be processed at a time.
    """
    try:
        with open("prompts/npc.md", "r") as f:
            npc_instruction = f.read()
    except FileNotFoundError:
        # Default instruction if file not found
        npc_instruction = """
        You are an NPC in a role-playing game. React to events happening around you based on your personality and objectives.
        """
        
    events_binded_to_npc = [
        EventTypes.LOCATION_CHANGE,
        EventTypes.LOCATION_MUTATION,
        EventTypes.LOCATION_STATUS_CHANGE,
        EventTypes.SCENE_UPDATE,
        EventTypes.OBJECT_TRANSFER,
        EventTypes.ITEM_TRANSFER,
        # EventTypes.ITEM_STATUS_CHANGE,
        EventTypes.ITEM_MOVEMENT,
        # EventTypes.ITEM_MUTATION,
        EventTypes.ITEM_INTERACTION,
        EventTypes.ITEM_PICKUP,
        EventTypes.ITEM_DROP,
        # EventTypes.CONTAINER_ACCESS,
        EventTypes.CONTAINER_TRANSFER,
        EventTypes.CHARACTER_STATUS_CHANGE,
        EventTypes.CHARACTER_DEATH,
        EventTypes.CHARACTER_STATS_UPDATE,
        EventTypes.CHARACTER_MOVEMENT,
        EventTypes.CHARACTER_TRANSFER,
        EventTypes.NPC_ACTION
        ]
        
    def __init__(self, character : NPCCharacter,
                 event_queuee : SubscriberQueue,
                 logger : Logger,
                 generator : Generator
                 ) -> None:
        self.character = character
        self.event_queue = event_queuee
        self.logger = logger
        self.generator = generator
        self._running = False
 
    def _filter_relevant_events(self, events: list[Event]) -> list[Event]:
        """Filter events to only those relevant to this NPC."""
        relevant_events = []
        for event in events:
            if event.event_type in self.events_binded_to_npc:
                relevant_events.append(event)
        return relevant_events
    
    def run(self, context : str) -> str | None:
        events = self.event_queue.get_all()
        self.event_queue.clear()
        decision = self._handle_events(events, context)
        self.logger.debug(f"NPC {self.character.name} processed {len(events)} events.")
        return decision
    
    def _handle_events(self, events: list[Event], context : str) -> str | None:
        """Process a list of events and decide on an action."""

        decision = self.generator.generate_one_shot(
            pydantic_model=NPCActDecision,
            prompt=f"""
            ##  Scene context:
            {context}
            ## You are an NPC named {self.character.name} in this scene.
            ## here are your state:
            {self.character.dict()}

            ## Here are the recent events in the game:
            {', '.join([str(e.dict()) for e in self._filter_relevant_events(events)])}
            Based on these events, decide if you need to act and what to do if you need to react in some way.
            """)

        if decision.will_act:
            self.logger.info(f"NPC {self.character.name} decided to act: {decision.action_description}")
            # saving and trimming the NPC memory
            self.character.memory += str(decision.action_description)
            self.character.memory = self.character.memory[-MEMORY_LENGTH_LIMIT:]
            return decision.action_description
        else:
            self.logger.debug(f"NPC {self.character.name} decided not to act.")
            return None