from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from schemas.in_game import Character

class EventTypes(Enum):
    LOCATION_CHANGE = "LOCATION_CHANGE"
    LOCATION_MUTATION = "LOCATION_MUTATION"
    LOCATION_STATUS_CHANGE = "LOCATION_STATUS_CHANGE"
    SCENE_UPDATE = "SCENE_UPDATE"
    
    ITEM_TRANSFER = "ITEM_TRANSFER" # for moving from inventory to scene, scene to inventory, scene to scene
    ITEM_STATUS_CHANGE = "ITEM_STATUS_CHANGE"
    ITEM_MOVEMENT = "ITEM_MOVEMENT"
    ITEM_MUTATION = "ITEM_MUTATION"
    ITEM_INTERACTION = "ITEM_INTERACTION"
    
    CHARACTER_STATUS_CHANGE = "CHARACTER_STATUS_CHANGE"
    CHARACTER_DEATH = "CHARACTER_DEATH"
    CHARACTER_STATS_UPDATE = "CHARACTER_STATS_UPDATE"
    CHARACTER_MOVEMENT = "CHARACTER_MOVEMENT"
    CHARACTER_TRANSFER = "CHARACTER_TRANSFER" # this was just removed
    


class Event(BaseModel):
    """An event that triggers orchestration logic."""
    event_type: EventTypes = Field(..., description="Type of the event.")
    event_initiator: Optional[str] = Field(..., description="Who or what initiated the event.")
    event_subject: Optional[str] = Field(..., description="The subject involved in the event.")
    description: str = Field(..., description="Detailed description of the event.")

class EventList(BaseModel):
    event_list : List[Event] = Field(description="list of events from a prompt")

class GenericManipulationCommand(BaseModel):
    description: str = Field(..., description="A description of the manipulation command.")
    details: str = Field(..., description="The details of the manipulation command in JSON format.")

class CharacterManipulationBrakdown(BaseModel):
    character_name: str = Field(..., description="The name of the character to be manipulated.")
    target : str  = Field(..., description="The attribute to be changed (e.g., current_hp, strength, inventory).")
    attribute: List[str] = Field(description="text attributes involved")
    value: str = Field(..., description="Numeric values involved.")
    operation: str = Field(..., description="The operation to be performed (add/subtract/append/remove/replace only).")
    
class TransferEventBreakDown(BaseModel):
    pass

class SceneManipulationCommand(BaseModel):
    target : str  = Field(..., description="The attribute to be changed (e.g., lighting, temperature, objects).")
    attribute: List[str] = Field(description="text attributes involved")
    value: str = Field(..., description="Numeric values involved.")
    operation: str = Field(..., description="The operation to be performed (add/subtract/append/remove/replace only).")

class SceneObjectManipulationCommand(BaseModel):
    object_name: str = Field(..., description="The name of the scene object to be manipulated.")
    target : str  = Field(..., description="The attribute to be changed (e.g., state, description, is_locked).")
    attribute: List[str] = Field(description="text attributes involved")
    value: str = Field(..., description="Values involved (numeric for quantities, string for states).")
    operation: str = Field(..., description="The operation to be performed (add/subtract/append/remove/replace only).")