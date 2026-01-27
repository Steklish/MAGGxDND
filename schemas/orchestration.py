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
    CHARACTER_TRANSFER = "CHARACTER_TRANSFER"

    # NPC Specific Events
    NPC_TRANSFER = "NPC_TRANSFER"

    # Spatial Events
    CHARACTER_POSITION_UPDATE = "CHARACTER_POSITION_UPDATE"
    CHARACTER_TELEPORT = "CHARACTER_TELEPORT"
    CHARACTER_PATHFINDING = "CHARACTER_PATHFINDING"
    # DISTANCE_CALCULATION = "DISTANCE_CALCULATION"

    # Action Result Events
    ACTION_RESULT = "ACTION_RESULT"

    # NPC_ACTION = "NPC_ACTION"
    # LOG="LOG"
    

from schemas.in_game import Coordinate3D

class Event(BaseModel):
    """An event that triggers orchestration logic."""
    event_type: EventTypes = Field(..., description="Type of the event.")
    event_initiator: Optional[str] = Field(..., description="Who or what initiated the event.")
    event_subject: Optional[str] = Field(..., description="The subject involved in the event.")
    event_target: Optional[str] = Field(description="Target object or character involved.")
    description: str = Field(..., description="Detailed description of the event.")

    # Spatial information (for spatial events)
    start_position: Optional[Coordinate3D] = Field(None, description="Starting position for movement events")
    end_position: Optional[Coordinate3D] = Field(None, description="Ending position for movement events")
    distance: Optional[float] = Field(None, description="Distance of movement for movement events")
    
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

class CharacterTransferBreakdown(BaseModel):
    """Breakdown of a character transfer action."""
    character_name: str = Field(..., description="Name of the character to transfer")
    target_location: str = Field(..., description="Name of the target location to transfer to")
    is_new_location: bool = Field(False, description="Whether the target location is a new location that needs to be generated")
    exit_direction: str = Field(description="Direction the character is exiting (e.g., north, south, east, west, up, down)")


class CharacterTransferDecision(BaseModel):
    """LLM decision on character transfer."""
    will_transfer: bool = Field(..., description="Whether the character will transfer to another location")
    transfer_breakdowns: List[CharacterTransferBreakdown] = Field(default_factory=list, description="List of transfer breakdowns for each character")
    new_location_description: str = Field(description="Description of the new location if is_new_location is True")
    connection_reason: Optional[str] = Field(None, description="Reason for connecting the new location to the current one")


class NPCTransferBreakdown(BaseModel):
    """Breakdown of an NPC transfer action."""
    npc_name: str = Field(..., description="Name of the NPC to transfer")
    target_location: str = Field(..., description="Name of the target location to transfer to")
    is_new_location: bool = Field(False, description="Whether the target location is a new location that needs to be generated")
    exit_direction: str = Field(description="Direction the NPC is exiting (e.g., north, south, east, west, up, down)")


class NPCTransferDecision(BaseModel):
    """LLM decision on NPC transfer."""
    will_transfer: bool = Field(..., description="Whether the NPC will transfer to another location")
    transfer_breakdowns: List[NPCTransferBreakdown] = Field(default_factory=list, description="List of transfer breakdowns for each NPC")
    new_location_description: str = Field(description="Description of the new location if is_new_location is True")
    connection_reason: Optional[str] = Field(None, description="Reason for connecting the new location to the current one")


class SpatialMovementCommand(BaseModel):
    """Command for character movement in 3D space."""
    character_name: str = Field(..., description="Name of the character to move")
    target_position: Coordinate3D = Field(..., description="Destination coordinates")
    movement_speed: Optional[float] = Field(None, description="Speed of movement (overrides character's default speed)")
    path_description: Optional[str] = Field(None, description="Description of the path taken")


class SpatialTeleportCommand(BaseModel):
    """Command for instant character teleportation."""
    character_name: str = Field(..., description="Name of the character to teleport")
    destination_position: Coordinate3D = Field(..., description="Destination coordinates")
    reason: Optional[str] = Field(None, description="Reason for teleportation")

class DistanceCalculationRequest(BaseModel):
    """Request to calculate distance between two points."""
    point_a: Coordinate3D = Field(..., description="First point")
    point_b: Coordinate3D = Field(..., description="Second point")
    unit: str = Field("feet", description="Unit of measurement")
    
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