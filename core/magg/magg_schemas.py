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

    
class PlotDevelopmentAction(str, Enum):
    CREATE_NEW_CHAPTER = "CREATE_NEW_CHAPTER"
    UPDATE_CURRENT_GOALS = "UPDATE_CURRENT_GOALS"
    ESCALATE_TO_NEXT_CHAPTER = "ESCALATE_TO_NEXT_CHAPTER"
    MAINTAIN_CURRENT_CHAPTER = "MAINTAIN_CURRENT_CHAPTER"
    FAIL_CURRENT_CHAPTER = "FAIL_CURRENT_CHAPTER"


class PlotFollowingIntervention(BaseModel):
    requires_intervention: bool = Field(
        description="True if the plot or player actions require intervention to guide the story."
    )
    
    action: PlotDevelopmentAction = Field(
        description="The action to take regarding chapter progression and goals."
    )
    
    visual_description: str = Field(
        description="Narrative description of the plot development for the players."
    )
    
    # Fields for updating current chapter goals
    updated_tasks: Optional[dict[str, bool]] = Field(
        default=None,
        description="Updated tasks for the current chapter (key: task description, value: completion status)"
    )
    
    # Fields for creating a new chapter
    new_chapter_name: Optional[str] = Field(
        default=None,
        description="Name of the new chapter if creating one"
    )
    
    new_chapter_description: Optional[str] = Field(
        default=None,
        description="Description of the new chapter if creating one"
    )
    
    new_chapter_tasks: Optional[dict[str, bool]] = Field(
        default=None,
        description="Tasks for the new chapter if creating one"
    )
    
    new_chapter_fail_conditions: Optional[list[str]] = Field(
        default=None,
        description="Fail conditions for the new chapter if creating one"
    )
    
    # Additional world intervention properties (reuse from WorldIntervention)
    removed_entity_names: list[str] = Field(
        default=[],
        description="Names of any NPCs or Objects that are no longer present in the scene due to plot development."
    )

    new_objects: list[str] = Field(
        default=[],
        description="Names of new items or prop objects appearing in the scene due to plot development."
    )

    new_npcs: list[NewNPC] = Field(
        default=[],
        description="A list of new characters entering the scene due to plot development, including their names and descriptions."
    )