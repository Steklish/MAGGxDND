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
from game.manipulators.character_transfer_manipulation import CharacterTransferManipulation
from game.manipulators.scene_object_mutation_manipulation import SceneObjectMutationManipulation


class Magg:
    def __init__(self, generator : Generator, 
                 archive : Archive | None, 
                 logger : Logger,
                 event_queue : SubscriberQueue) -> None:
        self.generator = generator
        self.archive = archive
        self.logger = logger
        self.event_queue = event_queue
        self.logger.debug("Magg initialized")
        
    