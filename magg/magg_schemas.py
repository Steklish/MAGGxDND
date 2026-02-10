from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, computed_field

class SimpleComment(BaseModel):
    comment: str = Field(
        ...,
        description="A concise comment about the game events from the perspective of a DND game master."
    )
    
class SimpleDescription(BaseModel):
    description: str = Field(
        ...,
        description="A vivid description of the current scene in the DND game."
    )
    
class DecisionType(str, Enum):
    FORCEFULLY_START_COMBAT = "FORCEFULLY_START_COMBAT"
    FORCEFULLY_START_STORY = "FORCEFULLY_START_STORY"
    CONTINUE_CURRENT_MODE = "CONTINUE_CURRENT_MODE"

class GameStateDecision(BaseModel):
    mode_change: DecisionType = Field(
        ...,
        description="A decision on whether to change the game mode or continue the current mode.")
    
    
class NewNPC(BaseModel):
    name: str = Field(description="The name of the character.")
    description: str = Field(description="Brief visual appearance and current mood/intent.")

class WorldIntervention(BaseModel):
    requires_intervention: bool = Field(
        description="True if the plot or player actions dictate a change in the environment assets."
    )
    
    visual_description: str = Field(
        description="Narrative description of the change for the game (may be object stats change or characters mutations)."
    )
    
    # Using 'set' indicates unique items, but 'list' is safer for LLM generation
    removed_entity_names: list[str] = Field(
        default=[],
        description="Names of any NPCs or Objects that are no longer present in the scene."
    )
    
    new_objects: list[str] = Field(
        default=[],
        description="Names of new items or prop objects appearing in the scene."
    )
    
    new_npcs: list[NewNPC] = Field(
        default=[],
        description="A list of new characters entering the scene, including their names and descriptions."
    )