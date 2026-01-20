from logging import Logger
from typing import Any, List, Tuple
from game.engine import Session
from game.utils import roll, roll_dice
from skls_generator.generator import Generator
import json
from schemas.orchestration import Event, EventTypes, GenericManipulationCommand, Character, CharacterManipulationBrakdown
from thefuzz import process

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
    event_types_binded = []
    def __init__(self, generator : Generator, state : Session, archive : Archive | None, logger : Logger) -> None:
        self.generator = generator
        self.archive = archive
        self.state = state
        self.logger = logger
        
    def get_related_objects(self, event : Event) -> List[Character]:
        character_pool = self.state.player_characters + self.state.npcs
        names = [c.name for c in character_pool]
        selected_objects = []
        for name in names:
            if name == event.event_initiator or name == event.event_subject:
                selected_objects.append(name)
        return selected_objects
        
        
    def execute(self, event: Event):
        """Executes the manipulation based on the provided prompt. (Wrapper)"""
        self.logger.debug(f"Executing manipulation {self.__class__.__name__}")
        self.manipulate(event)
    
    def manipulate(self, event: Event):
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
    # the llm prompt
    task_rules = f"""
    1. Use charater names, field names, other values exactly as provided
    2. Use one of the following tyles of operations add/subtract/append/remove/replace
        2.1 add/subtract should be applied to numeric values add/subtract is acceptable
        2.2 the rest should be applied to text/states values
        2.3 append adds a value (multiple values) to the list, remove removes them, replace replaces the entire list with a new one 
        2.4 Numeric value should follow dnd dice notation or a constatnt number (e g 10d4+1 where 10d4 means addition of 10 times rolled dice with 4 planes and + 1 constatly on top of that)
        2.5 for non-numeric values use attribute field
    3. If the target is an object attibute you MUST use its exactly as it spelled in reference objects.
    """
    
    event_types_binded = [EventTypes.CHARACTER_STATS_UPDATE, 
                                   EventTypes.CHARACTER_STATUS_CHANGE]
        
    def manipulate(self, event: Event):
        objects = self.get_related_objects(event)
        objects_text = ""
        for o in objects:
            objects_text += '\n'
            objects_text += str(o.__str__ if o else None)
        task_prompt = f"create a specific authoritive task from the event {event} \n\n Follow the following rules {self.task_rules}.\n\n # object schema for attribute matches: \n {Character.schema()}"
        # self.logger.debug(f"Task prompt: {task_prompt}")
        task = self.generator.generate_one_shot(
            pydantic_model=CharacterManipulationBrakdown,
            prompt=task_prompt
        )
        
        character_pool = self.state.player_characters + self.state.npcs
        names = [c.name for c in character_pool]
        target = None
        best = process.extractOne(task.character_name, names)
        if best:
            best = best[0]
        else:
            raise ValueError("No target found")
        # self.logger.debug(f"Task generated {best} / total > {names} / {character_pool}" )
        self.logger.debug(f"breakdown object here {task}")
        
        for c in character_pool:
            if c.name == best:
                target = c
                break
        if not target:
            raise ValueError("No target found")
        self._apply_change(target, task)
        
    def _apply_change(self, char: Character, task: CharacterManipulationBrakdown):
        """Dispatches logic based on the attribute type (Numeric vs List/State)."""
        
        # Map common AI terms to Pydantic fields and handle nested "abilities"
        # Returns (parent_object, field_name)
        parent_obj, field_name = self._resolve_attribute_path(char, task.target)

        # Retrieve the current value to determine how to handle it
        current_val = getattr(parent_obj, field_name)

        # --- BRANCH A: Numeric Operations (HP, Str, Speed) ---
        if isinstance(current_val, int):
            self._handle_numeric_op(parent_obj, field_name, current_val, task)
        
        # --- BRANCH B: List Operations (Active Conditions, Personality) ---
        elif isinstance(current_val, list):
            self._handle_list_op(parent_obj, field_name, current_val, task)

        # --- BRANCH C: String/Enum Operations (Race, Class Name) ---
        elif isinstance(current_val, str):
             if task.operation == "replace" or task.operation == "set":
                 setattr(parent_obj, field_name, task.value)

    def _handle_numeric_op(self, obj: Any, field: str, current_val: int, task: CharacterManipulationBrakdown):
        """Handles dice parsing and math."""
        # Parse the value (handle '1d4+2' or '10')
        change_amount = roll(task.value)
        self.logger.debug(f"Dice Roll: {change_amount}")
        self.logger.debug(f"Task: {task}")
        new_val = int(current_val)
        
        if task.operation in ["add", "heal", "buff"]:
            new_val += change_amount
        elif task.operation in ["subtract", "sub", "damage", "debuff"]:
            new_val -= change_amount
        elif task.operation in ["set", "replace"]:
            new_val = change_amount
        else:
            raise ValueError(f"Unknown operation: {task.operation}")


        # Logical clamps (HP cannot go below 0)
        if field == "current_hp":
            new_val = max(0, new_val)
            # You might also want to clamp to max_hp here if you have access to it
            if hasattr(obj, "max_hp"):
                new_val = min(new_val, obj.max_hp)

        setattr(obj, field, int(new_val))
        self.logger.debug(f"🔢 {field} changed: {current_val} -> {new_val} (Operation: {task.operation} {task.value})")

    def _handle_list_op(self, obj: Any, field: str, current_list: list, task: CharacterManipulationBrakdown):
        """Handles States/Conditions (e.g., ['Prone'] -> ['Prone', 'Poisoned'])."""
        

        clean_value = task.value.title() # "poisoned" -> "Poisoned"

        if task.operation in ["append", "add"]:
            if clean_value not in current_list:
                current_list.append(clean_value)
                self.logger.debug(f"➕ Added status '{clean_value}' to {field}.")
        
        elif task.operation in ["remove", "subtract", "delete"]:
            if clean_value in current_list:
                current_list.remove(clean_value)
                self.logger.debug(f"➖ Removed status '{clean_value}' from {field}.")
        
        elif task.operation == "replace":
            # Replaces the whole list (e.g. clear all conditions)
            if clean_value.lower() in ["none", "clear", "empty"]:
                setattr(obj, field, [])
            else:
                setattr(obj, field, [clean_value])

    def _resolve_attribute_path(self, char: Character, attr_name: str) -> Tuple[Any, str]:
        """
        Translates 'strength' -> (char.abilities, 'strength')
        Translates 'hp' -> (char, 'current_hp')
        """
        attr = attr_name.lower()
        
        # 1. Shortcuts for Core Stats
        ability_map = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
        for ability in ability_map:
            # Matches "strength" or "str"
            if attr == ability or (len(attr) == 3 and ability.startswith(attr)):
                return char.abilities, ability

        # 2. Shortcuts for Vitals
        if attr in ["hp", "health", "life"]:
            return char, "current_hp"
        if attr in ["max_hp", "total_health"]:
            return char, "max_hp"
        if attr in ["ac", "armor"]:
            return char, "armor_class"
        
        # 3. Shortcuts for States
        if attr in ["condition", "conditions", "status", "effect"]:
            return char, "active_conditions"
        
        # 4. Fallback: Try to find the attribute directly on the Character object
        if hasattr(char, attr):
            return char, attr
            
        # 5. Fallback: Try to find it on abilities (if the AI guessed the full name correctly)
        if hasattr(char.abilities, attr):
            return char.abilities, attr

        raise ValueError(f"Unknown attribute: {attr_name}")

        

class CharacterTransferManipulation(BaseManipulation):
    """Handles moving characters between scenes or creating characters."""
    pass



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