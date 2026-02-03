from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from schemas.in_game import Character

from schemas.in_game import Coordinate2D

from enum import Enum

class EventTypes(str, Enum):
    """
    Event types with built-in descriptions.
    Usage: 
        EventTypes.LOCATION_CHANGE.value -> "LOCATION_CHANGE"
        EventTypes.LOCATION_CHANGE.description -> "Moving characters between locations/scenes"
    """

    description : str
    
    def __new__(cls, value, description):
        # Create the string instance using the value
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.description = description
        return obj

    # Location Events - Non-entity specific
    LOCATION_CHANGE = "LOCATION_CHANGE", "Moving characters between locations/scenes"
    LOCATION_MUTATION = "LOCATION_MUTATION", "Changing properties of a location itself"
    LOCATION_STATUS_CHANGE = "LOCATION_STATUS_CHANGE", "Updating the status of a location (e.g., peaceful to dangerous)"
    # Object/Item Events - Non-entity specific
    OBJECT_TRANSFER = "OBJECT_TRANSFER", "Moving objects between containers/scene/inventory"
    ITEM_TRANSFER = "ITEM_TRANSFER", "Moving items between inventories, scenes, or containers"
    ITEM_MOVEMENT = "ITEM_MOVEMENT", "Moving items within a scene"
    ITEM_MUTATION = "ITEM_MUTATION", "Changing properties of an item (e.g., durability, condition)"
    ITEM_INTERACTION = "ITEM_INTERACTION", "Interacting with an item (e.g., opening a chest, using a key)"
    ITEM_PICKUP = "ITEM_PICKUP", "Picking up an item from the scene"
    ITEM_DROP = "ITEM_DROP", "Dropping an item into the scene"
    CONTAINER_ACCESS = "CONTAINER_ACCESS", "Opening/closing/accessing containers"
    CONTAINER_TRANSFER = "CONTAINER_TRANSFER", "Moving items between containers"

    # Character Events - Entity specific
    CHARACTER_STATUS_CHANGE = "CHARACTER_STATUS_CHANGE", "Changing character status (e.g., poisoned, stunned)"
    CHARACTER_DEATH = "CHARACTER_DEATH", "Character death events"
    CHARACTER_STATS_UPDATE = "CHARACTER_STATS_UPDATE", "Updating character statistics"
    CHARACTER_MOVEMENT = "CHARACTER_MOVEMENT", "Character movement within a scene"
    CHARACTER_TRANSFER = "CHARACTER_TRANSFER", "Moving characters between locations (for players)"

    # Spatial Events - Entity specific
    CHARACTER_POSITION_UPDATE = "CHARACTER_POSITION_UPDATE", "Updating character position in space"
    
    # Action Result Events - Non-entity specific
    ACTION_RESULT = "ACTION_RESULT", "Result of an action taken in the game"

    CHARACTER_MELEE_ATTACK = "CHARACTER_MELEE_ATTACK", "Melee attack by a character"
    CHARACTER_RANGED_ATTACK = "CHARACTER_RANGED_ATTACK", "Ranged attack by a character"

    @classmethod
    def get_event_descriptions(cls):
        """Returns a dictionary of event types and their descriptions."""
        return {event: event.description for event in cls}
    
    
class Event(BaseModel):
    """An event that triggers orchestration logic."""
    event_type: EventTypes = Field(..., description="Type of the event.")
    event_initiator: Optional[str] = Field(default=None, description="Who or what initiated the event.")
    event_subject: Optional[str] = Field(default=None, description="The subject involved in the event.")
    event_target: Optional[str] = Field(default=None, description="Target object or character involved.")
    description: str = Field(..., description="Detailed description of the event.")
    
class EventList(BaseModel):
    event_list : List[Event] = Field(description="list of events from a prompt")

class Message(BaseModel):
    sender_name : str
    text : str
    
class UserInterationType(Enum):
    CHARACTER_ACTION = "CHARACTER_ACTION"
    META_COMMENT = "META_COMMENT"
    
class UserInteractionProcessing(BaseModel):
    interaction_type : UserInterationType
    user_request_saturated : str = Field(description="Enhanecd user's request with all the details available and necessary")
    
    
class RulesCheck(BaseModel):
    is_rule_violation : bool = Field(description="Whether the action violates rules")
    violation_details : Optional[str] = Field(None, description="Details of the rule violation, if any")
    
class OrchestrationVerdictType(Enum):
    ALLOWED_PLAYER_ACTION = "ALLOWED_PLAYER_ACTION"
    CLAIRIFICATION_NEEDED = "CLAIRIFICATION_NEEDED"
    ILLEGAL_PLAYER_ACTION = "ILLEGAL_PLAYER_ACTION"
    META_REQUEST = "META_REQUEST"
    NPC_ACTION = "NPC_ACTION"
    SKIPPED = "SKIPPED"
    
class OrchestrationVerdict(BaseModel):
    original_request : Optional[str] = Field(default=None, description="Original request text from the player or NPC")
    verdict_type : OrchestrationVerdictType = Field(default=OrchestrationVerdictType.SKIPPED)
    details : Optional[str] = Field(default=None, description="Additional details about the verdict")
    
class ClarityCheck(BaseModel):
    needs_clarification: bool = Field(description="Whether the action needs clarification")
    clarification_needed: str = Field(description="What clarification is needed")

class RuleViolationObject(BaseModel):
    details : str