from logging import Logger
from typing import TYPE_CHECKING
from game.event_pool import SubscriberQueue
from entity.schemas import NPCActDecision
from schemas.in_game import NPCCharacter
from schemas.orchestration import Event, EventTypes, Message
from skls_generator.generator import Generator
from entity.game_entity import GameEntity

MEMORY_LENGTH_LIMIT = 2000  # characters


class NPC(GameEntity):
    """The idea is that the NPC class creature is intependent actor
    (independent from game master/ narrator) but the narrator
    will describe its actions.
    It listens to the events and decides if to act or not.

    If an NPC acts after an event, it will generate a new event.

    Multiple events can be processed at a time.
    """
    try:
        with open("prompts/npc.md", "r", encoding="utf-8") as f:
            npc_instruction = f.read()
    except FileNotFoundError:
        # Default instruction if file not found
        npc_instruction = """
        You are an NPC in a role-playing game. React to events happening around you based on your personality and objectives.
        """

    def __init__(self, character : NPCCharacter,
                 event_queuee : SubscriberQueue,
                 logger : Logger
                 ) -> None:
        super().__init__(character, event_queuee, logger)
        self.character : NPCCharacter
        self._running = False
       
    
    def run(self):
        """Process events and decide on an action."""

        events = self.event_queue.get_all()
        self.event_queue.clear()
        action_description = self._handle_events(events, self.session.get_session_context())
        self.logger.debug(f"NPC {self.character.name} processed {len(events)} events.")

        # If the NPC decided to act, generate events based on the action
        if action_description:
            # Generate events from the action description
            generated_events = self.session.manipulator._external_action_as_an_entity(action_description, self)

            # Execute each event through the appropriate manipulator
            executed_events = []
                
            for e in self.session.manipulator.execute_events(generated_events):
                self.event_queue.publish_to_others(e)

            

    def _handle_events(self, events: list[Event], context : str) -> str | None:
        """Process a list of events and decide on an action."""

        # Enhance context with spatial information
        spatial_context = self._get_spatial_context(events)

        decision = self.session.generator.generate_one_shot(
            pydantic_model=NPCActDecision,
            prompt=f"""
            ##  Scene context:
            {context}
            ## You are an NPC named {self.character.name} in this scene.
            ## Your current position: ({self.character.position.x}, {self.character.position.y})
            ## Your current scene: {self.character.current_scene or 'Unknown'}
            
            ## Current scene state:
            {self.session.get_session_context()}
            
            ## here are your state:
            {self.character.dict()}

            ## Spatial context:
            {spatial_context}
            
            {self.get_seen_entities_context()}

            ## Here are the recent events in the game:
            {', '.join([str(e.dict()) for e in events])}
            Based on these events, decide if you need to act and what to do if you need to react in some way.
            
            If decided to act you must describe you action as specific as possible.
            """)

        if decision.will_act:
            self.logger.info(f"NPC {self.character.name} decided to act: {decision.action_description}")
            # saving and trimming the NPC memory
            self.character.memory += str(decision.action_description) + decision.reasoning if decision.reasoning else ""
            self.character.memory = self.character.memory[-MEMORY_LENGTH_LIMIT:]
            
            # add NPC action to global chat histori in order for Game Master to see exact intent of the NPC
            if decision.action_description:
                new_message = Message(
                    sender_name=self.character.name + "[NPC action request]",
                    text=decision.action_description)
                self.session.new_message(new_message)
            return decision.action_description
        else:
            self.logger.debug(f"NPC {self.character.name} decided not to act.")
            return None
