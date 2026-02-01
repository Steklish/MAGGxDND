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
    CHARACTER_PATHFINDING = "CHARACTER_PATHFINDING"
    # DISTANCE_CALCULATION = "DISTANCE_CALCULATION"

    # Action Result Events
    ACTION_RESULT = "ACTION_RESULT"

    # NPC_ACTION = "NPC_ACTION"
    # LOG="LOG"
    

from schemas.in_game import Coordinate2D

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
    target_position: Coordinate2D = Field(..., description="Destination coordinates")
    movement_speed: Optional[float] = Field(None, description="Speed of movement (overrides character's default speed)")
    path_description: Optional[str] = Field(None, description="Description of the path taken")


class SpatialTeleportCommand(BaseModel):
    """Command for instant character teleportation."""
    character_name: str = Field(..., description="Name of the character to teleport")
    destination_position: Coordinate2D = Field(..., description="Destination coordinates")
    reason: Optional[str] = Field(None, description="Reason for teleportation")

class DistanceCalculationRequest(BaseModel):
    """Request to calculate distance between two points."""
    point_a: Coordinate2D = Field(..., description="First point")
    point_b: Coordinate2D = Field(..., description="Second point")
    unit: str = Field("feet", description="Unit of measurement")

class SpatialMovementBreakdown(BaseModel):
    """Breakdown of a spatial movement action."""
    character_name: str = Field(..., description="Name of the character to move")
    movement_type: str = Field(..., description="Type of movement: 'directional', 'relative_to_target', 'specific_coordinates'")
    direction_vector: Optional[Coordinate2D] = Field(None, description="Direction vector for movement (for directional movement)")
    distance: Optional[float] = Field(None, description="Distance to move in the specified direction")
    target_reference: Optional[str] = Field(None, description="Reference to a target character/object for relative movement")
    target_offset: Optional[Coordinate2D] = Field(None, description="Offset from the target position")
    specific_coordinates: Optional[Coordinate2D] = Field(None, description="Specific coordinates to move to")
    movement_description: str = Field(..., description="Description of the movement action")
    
class Message(BaseModel):
    sender_name : str
    text : str
    
class CharacterToUserBinding(BaseModel):
    username : str = Field(description="Username")
    character_name : str = Field(description="Undercontrolled character name")
    
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