from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class NPCActDecision(BaseModel):
    """Represents a decision made by an NPC to react or not."""
    will_act: bool = Field(..., description="Whether the NPC decides to act.")
    action_description: Optional[str] = Field(None, description="Description of the action if acting.")
    

class GameModeActions(str, Enum):
    KEEP_GAME_MODE = "KEEP_GAME_MODE"
    CHANGE_TO_COMBAT = "CHANGE_TO_COMBAT"
    CHANGE_TO_STORY = "CHANGE_TO_STORY"
        
    
class RoundDeterminationDecision(BaseModel):
    suggested_game_mode_action : GameModeActions = Field(description="Action for current game state.")
    expired_conditions : dict[str, str] = Field(description="A list of strings of conditions that should be removed due to some events along with character names. use format {character_name : \"name_value\"} (char name as a key and condition name for value)")
    # dm_intervention : Optional[str] = Field(None, description="An optional parameter if due to plot or any other reason the game master has to intervent current situations and change something in the scene.")