from logging import Logger
from typing import List
from game.engine import Session
from game.event_pool import SubscriberQueue
from skls_generator.generator import Generator
from schemas.orchestration import Event
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