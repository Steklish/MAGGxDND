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
        self._actor_thread = None
        self._processing_interval = (5 - self.character.initiative_bonus) / 2   # seconds between checking for events

    def start_continuous_processing(self):
        """Start continuous event processing in a separate thread."""
        if not self._running:
            self._running = True
            self._actor_thread = threading.Thread(target=self._continuous_process_events, daemon=True)
            self._actor_thread.start()
            self.logger.info(f"Started continuous processing for NPC: {self.character.name}")

    def stop_continuous_processing(self):
        """Stop continuous event processing."""
        self._running = False
        if self._actor_thread:
            self._actor_thread.join(timeout=1.0)  # Wait up to 1 second for thread to finish
            self.logger.info(f"Stopped continuous processing for NPC: {self.character.name}")

    def _continuous_process_events(self):
        """Continuously process events from the queue."""
        while self._running:
            try:
                # Check if there are events to process
                if not self.event_queue.empty():
                    # Get all events from the queue
                    events = self.event_queue.get_all()
                    if events:
                        # Process the events
                        self.handle_events(events)

                # Sleep for the processing interval to prevent busy-waiting
                time.sleep(self._processing_interval)

            except Exception as e:
                self.logger.error(f"Error in continuous event processing for {self.character.name}: {e}")
                # Brief pause before continuing to avoid rapid error loops
                time.sleep(0.5)
        
    def _filter_relevant_events(self, events: list[Event]) -> list[Event]:
        """Filter events to only those relevant to this NPC."""
        relevant_events = []
        for event in events:
            if event.event_type in self.events_binded_to_npc:
                relevant_events.append(event)
        return relevant_events
    
    def handle_events(self, events: list[Event]):
        """Process a list of events and decide on an action."""

        decision = self.generator.generate_one_shot(
            pydantic_model=NPCActDecision,
            prompt=f"""
            ## You are an NPC named {self.character.name}.
            ## here are your state:
            {self.character.dict()}

            ## Here are the recent events in the game:
            {', '.join([str(e.dict()) for e in self._filter_relevant_events(events)])}
            Based on these events, decide if you need to act and what to do if you need to react in some way.
            """)

        if decision.will_act:
            self.logger.info(f"NPC {self.character.name} decided to act: {decision.action_description}")
            # Here you would generate a new event based on the action description
            # For simplicity, we will just log it
            if decision.action_description:
                new_event = Event(
                    event_type=EventTypes.NPC_ACTION,
                    event_initiator=self.character.name,
                    event_subject=None,
                    event_target=None,
                    description=decision.action_description
                )
            else:
                raise ValueError("NPC decided to act but no action description provided.")

            # saving and trimming the NPC memory
            self.character.memory += str(decision.action_description)
            self.character.memory = self.character.memory[-MEMORY_LENGTH_LIMIT:]

            self.event_queue.publish_to_others(new_event)