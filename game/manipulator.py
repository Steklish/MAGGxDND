from logging import Logger
from typing import List
from game.engine import Session
from skls_generator.generator import Generator
from schemas.orchestration import Event
from game.base_manipulation import Archive, BaseManipulation
from game.object_transfer_manipulation import ObjectTransferManipulation
from game.scene_manipulation import SceneManipulation
from game.character_mutation_manipulation import CharacterMutationManipulation
from game.character_transfer_manipulation import CharacterTransferManipulation



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
                manipulator.execute(event)
                break
        else:
            raise ValueError(f"No manipulator for this event type found. Event type is {event.event_type.value}")
    
    def init_manipulations(self):
        self.manipulations.append(CharacterMutationManipulation(self.generator, self.state, self.archive, self.logger))
        
        for manipulation in self.manipulations:
            self.logger.info(f"Initialized manipulation: {manipulation.__class__.__name__}")