from typing import Optional
from pydantic import BaseModel, Field


class NPCActDecision(BaseModel):
    """Represents a decision made by an NPC to react or not."""
    will_act: bool = Field(..., description="Whether the NPC decides to act.")
    action_description: Optional[str] = Field(None, description="Description of the action if acting.")
    