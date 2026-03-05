"""
Session management REST API endpoints
"""

import asyncio
import logging
import os
import sys
import uuid
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from game.event_pool import EventPool
from schemas.in_game import GameModes

logger = logging.getLogger("game_server.sessions")

router = APIRouter()

# In-memory session storage
sessions_db: Dict[str, dict] = {}
active_game_loops: Dict[str, asyncio.Task] = {}


# Request/Response models
class SessionCreateRequest(BaseModel):
    session_name: str
    game_mode: str = "STORY"
    max_players: int = 6
    description: Optional[str] = None
    guide: Optional[str] = None
    scene_prompt: Optional[str] = None
    character_prompts: Optional[List[str]] = None
    npc_prompts: Optional[List[str]] = None


class SessionResponse(BaseModel):
    session_id: str
    session_name: str
    game_mode: str
    player_count: int
    max_players: int
    status: str
    description: Optional[str] = None


class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]
    total: int


class PlayerJoinRequest(BaseModel):
    player_name: str
    character_name: Optional[str] = None


class PlayerResponse(BaseModel):
    player_id: str
    player_name: str
    character_name: Optional[str] = None
    connected: bool = False


class SessionStartRequest(BaseModel):
    scene_prompt: str
    character_prompts: List[str] = []
    npc_prompts: List[str] = []


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions():
    """Get list of all active sessions."""
    logger.info("Listing all sessions")
    
    session_list = []
    for session_id, session_data in sessions_db.items():
        session_list.append(SessionResponse(
            session_id=session_id,
            session_name=session_data.get("session_name", "Unknown"),
            game_mode=session_data.get("game_mode", "STORY"),
            player_count=len(session_data.get("players", [])),
            max_players=session_data.get("max_players", 6),
            status=session_data.get("status", "created"),
            description=session_data.get("description")
        ))
    
    return SessionListResponse(
        sessions=session_list,
        total=len(session_list)
    )


@router.post("/sessions", response_model=SessionResponse)
async def create_session(request: SessionCreateRequest):
    """Create a new game session."""
    logger.info(f"Creating new session: {request.session_name}")
    
    session_id = str(uuid.uuid4())
    
    # Store session data
    sessions_db[session_id] = {
        "session_id": session_id,
        "session_name": request.session_name,
        "game_mode": request.game_mode,
        "max_players": request.max_players,
        "description": request.description,
        "guide": request.guide,
        "scene_prompt": request.scene_prompt,
        "character_prompts": request.character_prompts or [],
        "npc_prompts": request.npc_prompts or [],
        "players": [],
        "status": "created",
        "created_at": asyncio.get_event_loop().time()
    }
    
    logger.info(f"Session created: {session_id}")
    
    return SessionResponse(
        session_id=session_id,
        session_name=request.session_name,
        game_mode=request.game_mode,
        player_count=0,
        max_players=request.max_players,
        status="created",
        description=request.description
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get session info by ID."""
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data = sessions_db[session_id]
    
    return SessionResponse(
        session_id=session_id,
        session_name=session_data["session_name"],
        game_mode=session_data["game_mode"],
        player_count=len(session_data["players"]),
        max_players=session_data["max_players"],
        status=session_data["status"],
        description=session_data.get("description")
    )


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Cancel game loop if running
    if session_id in active_game_loops:
        active_game_loops[session_id].cancel()
        del active_game_loops[session_id]
    
    # Delete session
    del sessions_db[session_id]
    
    logger.info(f"Session deleted: {session_id}")
    return {"status": "deleted", "session_id": session_id}


@router.post("/sessions/{session_id}/players", response_model=PlayerResponse)
async def join_session(session_id: str, request: PlayerJoinRequest):
    """Join a session as a player."""
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data = sessions_db[session_id]
    
    # Check if session is full
    if len(session_data["players"]) >= session_data["max_players"]:
        raise HTTPException(status_code=400, detail="Session is full")
    
    # Generate player ID
    player_id = str(uuid.uuid4())
    
    # Add player to session
    player_data = {
        "player_id": player_id,
        "player_name": request.player_name,
        "character_name": request.character_name,
        "connected": False
    }
    
    session_data["players"].append(player_data)
    
    logger.info(f"Player {request.player_name} joined session {session_id}")
    
    return PlayerResponse(
        player_id=player_id,
        player_name=request.player_name,
        character_name=request.character_name,
        connected=False
    )


@router.delete("/sessions/{session_id}/players/{player_id}")
async def leave_session(session_id: str, player_id: str):
    """Leave a session."""
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data = sessions_db[session_id]
    
    # Remove player
    session_data["players"] = [
        p for p in session_data["players"] if p["player_id"] != player_id
    ]
    
    logger.info(f"Player {player_id} left session {session_id}")
    return {"status": "left", "session_id": session_id, "player_id": player_id}


@router.get("/sessions/{session_id}/players", response_model=List[PlayerResponse])
async def get_session_players(session_id: str):
    """Get all players in a session."""
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data = sessions_db[session_id]
    
    return [
        PlayerResponse(
            player_id=p["player_id"],
            player_name=p["player_name"],
            character_name=p.get("character_name"),
            connected=p.get("connected", False)
        )
        for p in session_data["players"]
    ]


@router.post("/sessions/{session_id}/start")
async def start_session(
    session_id: str,
    request: SessionStartRequest,
    background_tasks: BackgroundTasks
):
    """Start a game session (initialize game engine)."""
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data = sessions_db[session_id]
    
    # Check if already running
    if session_data.get("status") == "running":
        raise HTTPException(status_code=400, detail="Session already running")
    
    logger.info(f"Starting session: {session_id}")
    
    # Update session data
    session_data["scene_prompt"] = request.scene_prompt
    session_data["character_prompts"] = request.character_prompts
    session_data["npc_prompts"] = request.npc_prompts
    session_data["status"] = "running"
    
    # TODO: Initialize game engine here
    # This would create the Session object and start the game loop
    # For now, we'll just mark it as running
    
    logger.info(f"Session started: {session_id}")
    
    return {
        "status": "started",
        "session_id": session_id,
        "message": "Session initialization in progress"
    }


@router.get("/sessions/{session_id}/info")
async def get_session_info(session_id: str):
    """Get detailed session info including connected players."""
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data = sessions_db[session_id]
    
    return {
        **session_data,
        "players": [
            {
                "player_id": p["player_id"],
                "player_name": p["player_name"],
                "character_name": p.get("character_name"),
                "connected": p.get("connected", False)
            }
            for p in session_data["players"]
        ]
    }
