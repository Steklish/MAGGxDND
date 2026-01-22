from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from schemas.in_game import Character

class EventTypes(Enum):
    LOCATION_CHANGE = "LOCATION_CHANGE"
    LOCATION_MUTATION = "LOCATION_MUTATION"
    LOCATION_STATUS_CHANGE = "LOCATION_STATUS_CHANGE"
    SCENE_UPDATE = "SCENE_UPDATE"

    OBJECT_TRANSFER="OBJECT_TRANSFER"
    ITEM_TRANSFER = "ITEM_TRANSFER" # for moving from inventory to scene, scene to inventory, scene to scene
    ITEM_STATUS_CHANGE = "ITEM_STATUS_CHANGE"
    ITEM_MOVEMENT = "ITEM_MOVEMENT"
    ITEM_MUTATION = "ITEM_MUTATION"
    ITEM_INTERACTION = "ITEM_INTERACTION"
    ITEM_PICKUP = "ITEM_PICKUP"
    ITEM_DROP = "ITEM_DROP"
    CONTAINER_ACCESS = "CONTAINER_ACCESS"
    CONTAINER_TRANSFER = "CONTAINER_TRANSFER"

    CHARACTER_STATUS_CHANGE = "CHARACTER_STATUS_CHANGE"
    CHARACTER_DEATH = "CHARACTER_DEATH"
    CHARACTER_STATS_UPDATE = "CHARACTER_STATS_UPDATE"
    CHARACTER_MOVEMENT = "CHARACTER_MOVEMENT"
    CHARACTER_TRANSFER = "CHARACTER_TRANSFER" # this was just removed
    
    NPC_ACTION = "NPC_ACTION"
    LOG="LOG"
    

class Event(BaseModel):
    """An event that triggers orchestration logic."""
    event_type: EventTypes = Field(..., description="Type of the event.")
    event_initiator: Optional[str] = Field(..., description="Who or what initiated the event.")
    event_subject: Optional[str] = Field(..., description="The subject involved in the event.")
    event_target: Optional[str] = Field(description="Target object or character involved.")
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
    source: str = Field(..., description="Source of the transfer: 'scene', 'inventory', or 'container'")
    target: str = Field(..., description="Target of the transfer: 'inventory', 'scene', or 'container'")
    object_name: str = Field(..., description="Name of the object being transferred")
    quantity: int = Field(1, ge=1, description="Number of objects to transfer")
    target_container: Optional[str] = Field(None, description="Name of the target container if target is 'container'")

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
    
class Message(BaseModel):
    sender_name : str
    text : str
    
class CharacterToUserBinding(BaseModel):
    username : str = Field(description="Username")
    character_name : str = Field(description="Undercontrolled character name")
    
class UserInterationType(Enum):
    CHARACTER_ACTION = "CHARACTER_ACTION"
    META_COMMENT = "META_COMMENT"
    DM_INTERACTION = "DM_INTERACTION"
    
class UserInteractionProcessing(BaseModel):
    interaction_type : UserInterationType
    user_request_saturated : str = Field(description="Enhanecd user's request with all the details available and necessary")
    
class CombatRulesCheck(BaseModel):
    is_rule_violation : bool = Field(description="Whether the action violates combat rules")
    violation_details : Optional[str] = Field(None, description="Details of the rule violation, if any")
    
class StoryRulesCheck(BaseModel):
    is_rule_violation : bool = Field(description="Whether the action violates story rules")
    violation_details : Optional[str] = Field(None, description="Details of the rule violation, if any")