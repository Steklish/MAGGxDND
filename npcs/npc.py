from logging import Logger
from typing import TYPE_CHECKING
from game.event_pool import SubscriberQueue
from npcs.schemas import NPCActDecision
from schemas.in_game import NPCCharacter
from schemas.orchestration import Event, EventTypes, Message
from skls_generator.generator import Generator
if TYPE_CHECKING:
    from game.engine import Session
from game.game_entity import GameEntity
from game.manipulators.attack_manipulation import AttackManipulation
from game.manipulators.character_movement_manipulation import CharacterMovementManipulation

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
        with open("prompts/npc.md", "r") as f:
            npc_instruction = f.read()
    except FileNotFoundError:
        # Default instruction if file not found
        npc_instruction = """
        You are an NPC in a role-playing game. React to events happening around you based on your personality and objectives.
        """

    def __init__(self, character : NPCCharacter,
                 event_queuee : SubscriberQueue,
                 logger : Logger,
                 generator : Generator,
                 session: 'Session',
                 ) -> None:
        super().__init__(session=session)
        self.character = character
        self.event_queue = event_queuee
        self._npc_logger = logger  # Store the logger separately to avoid conflict with GameEntity's logger property
        self._npc_generator = generator  # Store the generator separately to avoid conflict with GameEntity's generator property
        self._running = False

        # Initialize default manipulators
        self.attack_manipulator = AttackManipulation(generator=self._npc_generator, logger=logger, session=self.session)
        self.movement_manipulator = CharacterMovementManipulation(generator=self._npc_generator, logger=logger, session=self.session)
        self.manipulators = [self.attack_manipulator, self.movement_manipulator]

        # Update manipulators based on inventory/spells
        self._update_manipulators()
       
    
    def run(self) -> list[Event]:
        """Process events and decide on an action."""

        events = self.event_queue.get_all()
        self.event_queue.clear()
        description = self._handle_events(events, self.session.get_session_context())
        self._npc_logger.debug(f"NPC {self.character.name} processed {len(events)} events.")

        # Return empty list if no action is decided
        if description is None:
            return []

        # Generate intent events from description using global manipulator as event generator
        intent_events = self.session.manipulator.external_action(description, actor=self.character.name)

        # Process intent events using entity manipulators
        results = []
        for event in intent_events:
            event_results = self.manage_event(event)
            if event_results:
                results.extend(event_results)
            else:
                # If entity doesn't have a manipulator for this event, it might be a global event
                # but intent was generated for this actor. We should probably keep the intent event.
                results.append(event)

        return results

    def _handle_events(self, events: list[Event], context : str) -> str | None:
        """Process a list of events and decide on an action."""

        # Enhance context with spatial information
        spatial_context = self._get_spatial_context(events)

        # Update NPC's current scene if needed based on context
        self._update_current_scene(context)

        decision = self._npc_generator.generate_one_shot(
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

            ## Here are the recent events in the game:
            {', '.join([str(e.dict()) for e in events])}
            Based on these events, decide if you need to act and what to do if you need to react in some way.

            If decided to act you must describe you action as specific as possible.
            """
            )

        if decision.will_act:
            self._npc_logger.info(f"NPC {self.character.name} decided to act: {decision.action_description}")
            # saving and trimming the NPC memory
            self.character.memory += str(decision.action_description)
            self.character.memory = self.character.memory[-MEMORY_LENGTH_LIMIT:]

            # add NPC action to global chat histori in order for Game Master to see exact intent of the NPC
            if decision.action_description:
                new_message = Message(
                    sender_name=self.character.name + "[NPC action request]",
                    text=decision.action_description)
                self.session.new_message(new_message)
            return decision.action_description
        else:
            self._npc_logger.debug(f"NPC {self.character.name} decided not to act.")
            return None

    def _update_current_scene(self, context: str):
        """
        Update the NPC's current scene based on the game context.
        # Extract scene information from context if available """
        
        # This is a simple implementation - in a real system, you might parse the context more thoroughly
        if "Location:" in context:
            # Extract the location name from the context
            import re
            location_match = re.search(r"Location:\s*([^\n]+)", context)
            if location_match:
                location_name = location_match.group(1).strip()
                if location_name != "Unknown":
                    self.character.current_scene = location_name

    def _get_spatial_context(self, events: list[Event]) -> str:
        """Generate spatial context from recent events."""
        spatial_events = [e for e in events if e.event_type in [
            EventTypes.CHARACTER_POSITION_UPDATE,
            EventTypes.CHARACTER_MOVEMENT
        ]]

        if not spatial_events:
            return "No recent spatial movements detected."

        context = "Recent spatial movements:\n"
        for event in spatial_events:
            # Since spatial coordinates are no longer in events, we'll just note the movement
            # The actual positions are maintained by the objects themselves
            context += f"- {event.event_subject} moved to location '{event.event_target}'\n"

        return context

    def _calculate_distance_3d(self, pos1, pos2) -> float:
        """Calculate Euclidean distance between two 3D coordinates."""
        dx = pos2.x - pos1.x
        dy = pos2.y - pos1.y
        dz = pos2.z - pos1.z
        return (dx**2 + dy**2 + dz**2)**0.5