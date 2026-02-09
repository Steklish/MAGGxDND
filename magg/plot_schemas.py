from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, computed_field

    
class ChapterStatus(str, Enum):
    COMING = "COMING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    DISCARDED = "DISCARDED"

class Chapter(BaseModel):
    name : str = Field(description="A chapter name (must be short and unique)")
    description : str = Field(description="Text description of events planned.")
    tasks : dict[str, bool] = Field(description="List of tasks to be accomplished in this chapter. (with completeion status)")
    fail_conditions : list[str] = Field(description="A lit of conditions that instantly fail chapter progress")
    status : ChapterStatus = Field(description="Chapter status.")
    
class Plot(BaseModel):
    world_description : str = Field(description="A brief description of the world. INcule only the details that differ the current wprl from an average dnd fantasy environment.")
    chapters : List[Chapter] = Field(description="A list of chapters that are expected to happen in the story.")
    status : ChapterStatus = Field(description="Chapter status describing how to handle a capter.")
    # current_chapter : Chapter = Field(description="A pointer to the current chapter")
    @computed_field
    @property
    def current_chapter(self) -> Chapter | None:
        for c in self.chapters:
            if c.status == ChapterStatus.COMING:
                return c
        return None