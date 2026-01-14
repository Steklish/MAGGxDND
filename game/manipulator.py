from logging import Logger
from game.engine import Session
from skls_generator.generator import Generator
import json

class Archive:
    """Manages storage and retrieval of unused game objects. For consistency."""
    def __init__(self, directory: str = "/data"):
        self.directory =  directory # Base directory for data files where currently unused object stored in a file
        
    def store(self, object):
        """Stores objects that are no longer in the current scene for future use."""
        with open(f"{self.directory}/archive.json", "r") as file:
            archive = json.load(file)
            
        archive.append(object)
        with open(f"{self.directory}/archive.json", "w") as file:
            json.dump(archive, file)
    
    def retrieve(self, object_type: str):
        """Retrieves stored all objects by type for the manipulator to decide what to do with an LLM."""
        with open(f"{self.directory}/archive.json", "r") as file:
            archive = json.load(file)
        return [obj for obj in archive if obj['type'] == object_type]


class BaseManipulation:
    def __init__(self, generator : Generator, state : Session, archive : Archive, logger : Logger) -> None:
        self.generator = generator
        self.archive = archive
        self.state = state
        self.logger = logger
        
    def execute(self, prompt: str):
        """Executes the manipulation based on the provided prompt. (Wrapper)"""
        self.logger.debug(f"Executing manipulation {self.__class__.__name__} with prompt: {prompt[0:10]}...")
        self.manipulate(prompt)
    
    def manipulate(self, prompt: str):
        """Core manipulation logic to be implemented by subclasses."""
        raise NotImplementedError("This method should be overridden by subclasses.")


class ObjectTransferManipulation(BaseManipulation):
    """Handles moving objects between scenes or inventories."""
    pass    

class SceneManipulation(BaseManipulation):
    """Handles changes to the scene, such as adding or removing objects."""
    pass
    
class CharacterMutationManipulation(BaseManipulation):
    """Handles character-related manipulations, such as status effects or inventory changes."""
    pass

class CharacterTransferManipulation(BaseManipulation):
    """Handles moving characters between scenes or creating characters."""
    pass



class Manipulator:
    def __init__(self, generator : Generator, state : Session, archive : Archive,logger : Logger) -> None:
        self.generator = generator
        self.manipulations = []
        self.state = state
        self.archive = archive
        self.logger = logger
        self.init_manipulations()
        
    def execute_manipulation(self, manipulation_type: str, prompt: str):
        for manipulation in self.manipulations:
            if manipulation.__class__.__name__ == manipulation_type:
                return manipulation.execute(prompt)
        
    def init_manipulations(self):
        self.manipulations.append(SceneManipulation(self.generator, self.state, self.archive, self.logger))
        
        for manipulation in self.manipulations:
            self.logger.info(f"Initialized manipulation: {manipulation.__class__.__name__}")