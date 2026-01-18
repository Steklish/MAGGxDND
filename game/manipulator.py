from logging import Logger
from game.engine import Session
from skls_generator.generator import Generator
import json
from schemas.orchestration import Event, GenericManipulationCommand, Character
from typing import Optional

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
    def manipulate(self, prompt: str):
        """Handles the logic for moving objects between scenes or inventories."""
        self.logger.info(f"ObjectTransferManipulation executing with prompt: {prompt}")
        # Parse the prompt to identify the object, source, and destination.
        try:
            transfer_details = json.loads(prompt)
            object_name = transfer_details['object']
            source = transfer_details['source']
            destination = transfer_details['destination']
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Invalid prompt format: {e}")
            return []

        # Get objects from source
        if source == "scene":
            objects = self.state.current_scene.objects
        else:
            character = next((c for c in self.state.player_characters + self.state.npcs if c.name == source), None)
            if not character:
                self.logger.error(f"Source character {source} not found.")
                return []
            objects = character.inventory

        # Find object to transfer
        obj_to_transfer = next((obj for obj in objects if obj.name == object_name), None)
        if not obj_to_transfer:
            self.logger.error(f"Object {object_name} not found in {source}.")
            return []
        
        # Remove object from source
        objects.remove(obj_to_transfer)

        # Add object to destination
        if destination == "scene":
            self.state.current_scene.objects.append(obj_to_transfer)
        else:
            character = next((c for c in self.state.player_characters + self.state.npcs if c.name == destination), None)
            if not character:
                self.logger.error(f"Destination character {destination} not found.")
                return []
            character.inventory.append(obj_to_transfer)

        # Create event
        event = Event(
            event_type="ITEM_TRANSFER",
            event_initiator="system",
            event_subject=object_name,
            description=f"Object {object_name} transferred from {source} to {destination}."
        )

        return [event]    

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
        self.manipulations.append(ObjectTransferManipulation(self.generator, self.state, self.archive, self.logger))
        
        for manipulation in self.manipulations:
            self.logger.info(f"Initialized manipulation: {manipulation.__class__.__name__}")