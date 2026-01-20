from game.manipulators.base_manipulation import BaseManipulation
from schemas.orchestration import Event
from skls_generator.generator import Generator
from logging import Logger
from game.engine import Session


class ObjectTransferManipulation(BaseManipulation):
    """Handles moving objects between scenes or inventories."""
    
    def __init__(self, generator : Generator, state : Session, archive, logger : Logger) -> None:
        super().__init__(generator, state, archive, logger)

    def manipulate(self, event: Event):
        # TODO: Implement the specific logic for object transfer manipulation
        pass