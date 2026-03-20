from fastapi import APIRouter, HTTPException, Depends
from models.api import (
    CreateSessionRequest,
    CreateSessionResponse,
    SessionStateResponse
)
import session_manager
from main import manager

router = APIRouter(
    prefix="/api/sessions",
    tags=["sessions"],
)

@router.post("", response_model=CreateSessionResponse)
async def create_session(
    request: CreateSessionRequest,
):
    """
    Creates a new game session and starts its game loop.
    """
    session = session_manager.create_new_session(
        session_name=request.session_name,
        manager=manager,
        player_characters=request.player_characters,
        initial_scene=request.initial_scene,
    )
    return CreateSessionResponse(session_id=session.session_name)

@router.get("/{session_id}", response_model=SessionStateResponse)
async def get_session_state(session_id: str):
    """
    Retrieves the current state of a game session.
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionStateResponse(
        session_id=session_id,
        session_name=session.session_name_proper, # Assuming this property exists
        game_mode=session.game_mode.value,
        is_running=session.is_running,
        players=[p.character.name for p in session.players]
    )

@router.delete("/{session_id}", status_code=204)
async def delete_session(session_id: str):
    """

    Ends a game session and cleans up its resources.
    """
    success = session_manager.end_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session ended successfully."}
