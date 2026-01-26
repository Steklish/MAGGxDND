from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, computed_field

class SimpleComment(BaseModel):
    comment: str = Field(
        ...,
        description="A concise comment about the game events from the perspective of a DND game master."
    )