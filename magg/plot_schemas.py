from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, computed_field

    
class ChapterStatus(str, Enum):
    COMING = "COMING"
    PAST = "PAST"
    FAILED = "FAILED"
    DISCARDED = "DISCARDED"

    
class Chapter(BaseModel):
    description : str = Field(description="Text description of events planned.")
    tasks : dict[str, bool] = Field(description="List of tasks to be accomplished in this chapter. (with completeion status)")
    status : ChapterStatus = Field(description="Chapter status.")
    