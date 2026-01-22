from logging import Logger
from typing import List
from game.engine import Session
from skls_generator.generator import Generator
from schemas.orchestration import Event
from game.manipulators.base_manipulation import Archive, BaseManipulation
from game.manipulators.object_transfer_manipulation import ObjectTransferManipulation
from game.manipulators.scene_manipulation import SceneManipulation
from game.manipulators.character_mutation_manipulation import CharacterMutationManipulation
from game.manipulators.character_transfer_manipulation import CharacterTransferManipulation
from game.manipulators.scene_object_mutation_manipulation import SceneObjectMutationManipulation


class Magg:
    def __init__(self, generator : Generator, state : Session, archive : Archive | None, logger : Logger) -> None:
        self.generator = generator
        self.manipulations : List[BaseManipulation] = []
        self.state = state
        self.archive = archive
        self.logger = logger
        
        self.logger.debug("Magg initialized")
        
    