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
    