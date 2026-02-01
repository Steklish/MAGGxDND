from logging import Logger
from typing import List
from game.engine import Session
from game.event_pool import SubscriberQueue
from skls_generator.generator import Generator
from schemas.orchestration import Event, EventList
from game.manipulators.base_manipulation import Archive, BaseManipulation
from game.manipulators.object_transfer_manipulation import ObjectTransferManipulation
from game.manipulators.scene_manipulation import SceneManipulation
from game.manipulators.character_mutation_manipulation import CharacterMutationManipulation
from game.manipulators.character_movement_manipulation import CharacterMovementManipulation
from game.manipulators.scene_object_movement_manipulation import SceneObjectMovementManipulation
from game.manipulators.character_transfer_manipulation import CharacterTransferManipulation
from game.manipulators.npc_transfer_manipulation import NPCTransferManipulation
from game.manipulators.scene_object_mutation_manipulation import SceneObjectMutationManipulation



class Manipulator:
    def __init__(self, generator : Generator, state : Session, archive : Archive | None, logger : Logger) -> None:
        self.generator = generator
        self.manipulations : List[BaseManipulation] = []
        self.state = state
        self.archive = archive
        self.logger = logger
        self.init_manipulations()
        self.logger.info("Manipulator initialized")
        
    
    def external_action(self, prompt: str = "", actor : str | None = None) -> List[Event]:
        """Perform a privileged external action within the game session. (DM moves)"""

        rules = f"""
        1. Determine which objects involved into the request.
        2. Be the most specific (if there is a certain object in the scene you should set event type to item-based not the entire scene)
        3. Choose the appropriate event type based on the action being performed:
        4. There are special types of requests from user when in battle. If an attack requested you Must generate an event that includes damage calculation based on character and item stats.
        5. Do not generate ACTION_RESULT events.

        EVENT TYPE RESPONSIBILITIES:
        - LOCATION_CHANGE: Moving characters between locations/scenes
        - LOCATION_MUTATION: Changing properties of a location itself
        - LOCATION_STATUS_CHANGE: Updating the status of a location (e.g., peaceful to dangerous)
        - SCENE_UPDATE: Updating scene description or properties
        - OBJECT_TRANSFER: Moving objects between containers/scene/inventory
        - ITEM_TRANSFER: Moving items between inventories, scenes, or containers
        - ITEM_STATUS_CHANGE: Changing status of an item (e.g., locked/unlocked, open/closed)
        - ITEM_MUTATION: Changing properties of an item (e.g., durability, condition)
        - ITEM_INTERACTION: Interacting with an item (e.g., opening a chest, using a key)
        - ITEM_PICKUP: Picking up an item from the scene
        - ITEM_DROP: Dropping an item into the scene
        - CONTAINER_ACCESS: Opening/closing/accessing containers
        - CONTAINER_TRANSFER: Moving items between containers
        - CHARACTER_STATUS_CHANGE: Changing character status (e.g., poisoned, stunned)
        - CHARACTER_DEATH: Character death events
        - CHARACTER_MOVEMENT: Character movement within a scene
        - CHARACTER_TRANSFER: Moving characters between locations (for players)
        - NPC_TRANSFER: Moving NPCs between locations (for NPCs)
        """

        prompt_text = f"""
        You need to generate authoritative events based on the situation and a request e.g. "The dragon gets 1d8+2 damage. (based on items properties)" or "character 1 hits character 2 with a sword and dealing 1d6+3 damage"

        # EVENT TYPE RESPONSIBILITIES:
        {rules}

        # prompt
        {f"## actor: {actor}\nrequest: " if actor else ""}
        {prompt}
        # scene:
        {self.state.get_session_context()}
        
        # Last messages history (meta game) - for references:
        {self.state.get_messages_formatted()}
        """
        events = self.generator.generate_one_shot(
            pydantic_model=EventList,
            prompt=prompt_text
        )
        self.logger.debug(f"Events generated {events.event_list}")
        return events.event_list
        
    def manage(self, event : Event):
        for manipulator in self.manipulations:
            if event.event_type in manipulator.event_types_binded:
                result_events = manipulator.execute(event)
                # Process any result events returned by the manipulator
                if result_events:
                    for result_event in result_events:
                        # Add result events to the event pool for other systems to process
                        self.state.event_pool.add_event(result_event)
                break
        else:
            if event.event_type != "ACTION_RESULT":
                raise ValueError(f"No manipulator for this event type found. Event type is {event.event_type.value}")
            else:
                self.logger.warning(f"Ignored ACTION_RESULT event: {event}")
    
    def init_manipulations(self):
        self.manipulations.append(CharacterMutationManipulation(self.generator, self.state, self.archive, self.logger))
        self.manipulations.append(CharacterMovementManipulation(self.generator, self.state, self.archive, self.logger))
        self.manipulations.append(SceneObjectMovementManipulation(self.generator, self.state, self.archive, self.logger))
        self.manipulations.append(SceneManipulation(self.generator, self.state, self.archive, self.logger))
        self.manipulations.append(SceneObjectMutationManipulation(self.generator, self.state, self.archive, self.logger))
        self.manipulations.append(ObjectTransferManipulation(self.generator, self.state, self.archive, self.logger))
        self.manipulations.append(CharacterTransferManipulation(self.generator, self.state, self.archive, self.logger))
        self.manipulations.append(NPCTransferManipulation(self.generator, self.state, self.archive, self.logger))

        for manipulation in self.manipulations:
            self.logger.info(f"Initialized manipulation: {manipulation.__class__.__name__}")