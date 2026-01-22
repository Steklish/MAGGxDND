from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, computed_field

    
class ChapterStatus(str, Enum):
    COMING = "COMING"
    PAST = "PAST"
    FAILED = "FAILED"
    
class Chapter(BaseModel):
    description : str = Field(description="Text description of events planned.")
    core_idea : str = Field(description="COre game master's plan behind this chapter")
    status : ChapterStatus = Field(description="Chapter status.")
    
class Campaign(BaseModel):
    chapters : List[Chapter] = Field(description="list of chapters")
    goal : str = Field(description="Text description of the goal and idea behind the game")
    mood : str = Field(description="Campaign mood description.")
    world_buildigng_rules : List[str] = Field(description="Optional custom rules for better game experience")