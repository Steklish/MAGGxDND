import sys
from pydantic import BaseModel, Field
from typing import Literal, List

sys.path.append(r"D:\Lectures\SDLC\MAGGxDND")
from schemas.in_game import Character, SceneNode

# Based on the REST API Specification in server_requirements.md

class CreateSessionRequest(BaseModel):
    """Request model for creating a new session."""
    session_name: str = Field(..., description="The name of the campaign or session.")
    player_characters: List[Character] = Field(..., description="A list of player characters to start the session with.")
    initial_scene: SceneNode = Field(..., description="The scene where the session will begin.")
    game_mode: Literal["STORY", "COMBAT"] = Field(
        "STORY", description="The initial game mode."
    )
    spatial_enabled: bool = Field(
        True, description="Whether the spatial system (grid) is enabled."
    )

class CreateSessionResponse(BaseModel):
    """Response model after creating a session."""
    session_id: str = Field(..., description="The unique identifier for the created session.")
    status: str = Field("created", description="The status of the operation.")

class SessionStateResponse(BaseModel):
    """Response model for getting the state of a session."""
    session_id: str
    session_name: str
    game_mode: str
    is_running: bool
    players: list[str] # List of player names

# We can add more models here for joining sessions, adding characters, etc.
# For example:

class JoinSessionRequest(BaseModel):
    player_name: str
    # The full character schema can be imported or redefined here
    # For now, we'll keep it simple
    character_data: dict 
