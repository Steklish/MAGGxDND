from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import Dict, Any, List, Optional
import json
import logging

logger = logging.getLogger(__name__)

from backend.src.auth.dependencies import get_current_user_from_cookie
from backend.src.config import settings
from backend.src.database.session import get_db
from backend.src.schema import Token
from backend.src.utils import security
from backend.src.services import auth_service
from backend.src.game.session_manager import session_manager
from backend.src.models.session import GameSession

router = APIRouter(prefix="/test", tags=["Dev"])


# ===================================================================
# DEVELOPER ENDPOINTS - Access all sessions and their data
# ===================================================================

@router.get("/info", summary="Вывод информации о пользователе. Использует cookies для получения данных")
def login_for_access_token(db: Session = Depends(get_db), user = Depends(get_current_user_from_cookie)):
    try:
        return {
            "data" : user.__dict__
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/sessions", summary="Get all sessions (database + active in-memory)")
async def get_all_sessions(db: Session = Depends(get_db)):
    """
    Get a list of all sessions from the database and active in-memory sessions.
    
    Returns both persisted database sessions and currently running sessions.
    """
    try:
        # Get all database sessions
        db_sessions = db.query(GameSession).filter(
            GameSession.is_active == True
        ).order_by(GameSession.created_at.desc()).all()
        
        # Get active in-memory sessions
        active_sessions = session_manager.get_all_sessions()
        
        # Build response with both types
        database_sessions = []
        for db_sess in db_sessions:
            session_data = db_sess.session_data or {}
            is_running = db_sess.session_uuid in active_sessions
            
            database_sessions.append({
                "session_id": db_sess.session_uuid,
                "session_name": db_sess.session_name,
                "owner_id": db_sess.owner_id,
                "game_mode": db_sess.game_mode.value,
                "status": db_sess.status.value,
                "created_at": db_sess.created_at.isoformat() if db_sess.created_at else None,
                "updated_at": db_sess.updated_at.isoformat() if db_sess.updated_at else None,
                "last_active_at": db_sess.last_active_at.isoformat() if db_sess.last_active_at else None,
                "is_running": is_running,
                "source": "database",
                "participants_count": len(session_data.get("participants", [])),
                "session_data_preview": {
                    k: v for k, v in session_data.items() 
                    if k in ["max_players", "description", "guide"]
                }
            })
        
        # Add in-memory sessions that aren't in database (shouldn't happen but just in case)
        memory_sessions = []
        for session_id, session in active_sessions.items():
            # Check if already in database list
            if not any(s["session_id"] == session_id for s in database_sessions):
                session_info = session_manager.get_session_info(session_id)
                if session_info:
                    memory_sessions.append({
                        "session_id": session_id,
                        "session_name": session_info["session_name"],
                        "player_count": session_info["player_count"],
                        "event_count": session_info["event_count"],
                        "game_mode": session_info["game_mode"],
                        "player_ids": list(session_manager.get_all_session_websockets(session_id).keys()),
                        "is_running": True,
                        "source": "memory",
                    })
        
        return {
            "total_database_sessions": len(database_sessions),
            "total_memory_sessions": len(memory_sessions),
            "database_sessions": database_sessions,
            "memory_sessions": memory_sessions
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/sessions/{session_id}", summary="Get detailed session data")
async def get_session_detail(session_id: str, db: Session = Depends(get_db)):
    """
    Get comprehensive data for a specific session.
    
    Tries in-memory session first, then falls back to database.
    Includes full session state, players, NPCs, scene, messages, and more.
    """
    try:
        # Try to get from SessionManager first (running session)
        session = session_manager.get_session(session_id)
        
        if session:
            # It's a running session in memory
            ws_connections = session_manager.get_all_session_websockets(session_id)
            
            return {
                "session_id": session_id,
                "session_name": session.session_name,
                "game_mode": session.game_mode.value,
                "source": "memory",
                "is_running": True,
                "session_state": session.get_session_state(),
                "websocket_connections": {
                    player_id: "connected" 
                    for player_id in ws_connections.keys()
                },
                "active_player_count": len(ws_connections),
                "event_pool_size": session.event_pool.get_event_count(),
                "message_count": len(session.messages),
                "npc_count": len(session.npcs),
                "player_count": len(session.players),
                "current_location": session.current_location_name,
            }
        else:
            # Try database
            db_session = db.query(GameSession).filter(
                GameSession.session_uuid == session_id
            ).first()
            
            if not db_session:
                raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
            
            session_data = db_session.session_data or {}
            
            return {
                "session_id": session_id,
                "session_name": db_session.session_name,
                "owner_id": db_session.owner_id,
                "game_mode": db_session.game_mode.value,
                "status": db_session.status.value,
                "source": "database",
                "is_running": False,
                "created_at": db_session.created_at.isoformat() if db_session.created_at else None,
                "updated_at": db_session.updated_at.isoformat() if db_session.updated_at else None,
                "last_active_at": db_session.last_active_at.isoformat() if db_session.last_active_at else None,
                "session_data": session_data,
            }
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}


@router.get("/sessions/{session_id}/players", summary="Get all players in a session")
async def get_session_players(session_id: str):
    """
    Get detailed information about all players in a session.
    
    Includes character data, positions, stats, and connection status.
    """
    try:
        session = session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        ws_connections = session_manager.get_all_session_websockets(session_id)
        
        players_data = []
        for player in session.players:
            player_info = {
                "player_id": player.player_id if hasattr(player, 'player_id') else None,
                "character_name": player.name if hasattr(player, 'name') else "Unknown",
                "connected": player.player_id in ws_connections if hasattr(player, 'player_id') else False,
                "character_data": player.dict() if hasattr(player, 'dict') else str(player),
            }
            players_data.append(player_info)
        
        return {
            "session_id": session_id,
            "total_players": len(players_data),
            "connected_players": sum(1 for p in players_data if p["connected"]),
            "players": players_data
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}


@router.get("/sessions/{session_id}/npcs", summary="Get all NPCs in a session")
async def get_session_npcs(session_id: str):
    """
    Get all NPCs in a session with their current state.
    """
    try:
        session = session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        npcs_data = []
        for npc in session.npcs:
            npc_info = {
                "npc_name": npc.name if hasattr(npc, 'name') else "Unknown",
                "current_scene": npc.current_scene if hasattr(npc, 'current_scene') else None,
                "npc_data": npc.dict() if hasattr(npc, 'dict') else str(npc),
            }
            npcs_data.append(npc_info)
        
        return {
            "session_id": session_id,
            "total_npcs": len(npcs_data),
            "npcs": npcs_data
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}


@router.get("/sessions/{session_id}/scene", summary="Get current scene data")
async def get_session_scene(session_id: str):
    """
    Get the current scene data for a session.
    """
    try:
        session = session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        scene_data = None
        if session.current_scene:
            scene_data = session.current_scene.dict() if hasattr(session.current_scene, 'dict') else str(session.current_scene)
        
        return {
            "session_id": session_id,
            "current_location": session.current_location_name,
            "scene": scene_data,
            "all_locations_count": len(session.all_locations) if session.all_locations else 0,
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}


@router.get("/sessions/{session_id}/messages", summary="Get session message history")
async def get_session_messages(session_id: str):
    """
    Get the message history for a session.
    """
    try:
        session = session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        messages_data = []
        for msg in session.messages[-100:]:  # Last 100 messages
            msg_data = msg.dict() if hasattr(msg, 'dict') else str(msg)
            messages_data.append(msg_data)
        
        return {
            "session_id": session_id,
            "total_messages": len(session.messages),
            "messages_returned": len(messages_data),
            "messages": messages_data
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}


@router.get("/sessions/{session_id}/turn-queue", summary="Get turn queue state")
async def get_session_turn_queue(session_id: str):
    """
    Get the current turn queue for combat sessions.
    """
    try:
        session = session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        turn_queue_data = None
        if session.turn_queue:
            turn_queue_data = session.turn_queue.get_queue_state() if hasattr(session.turn_queue, 'get_queue_state') else str(session.turn_queue)
        
        return {
            "session_id": session_id,
            "game_mode": session.game_mode.value,
            "turn_queue": turn_queue_data
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}


@router.get("/sessions/{session_id}/full-state", summary="Get complete session state as JSON")
async def get_session_full_state(session_id: str):
    """
    Get the complete serializable state of a session.
    
    This returns everything that would be saved to the database.
    """
    try:
        session = session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        session_state = session.get_session_state()
        
        return {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "session_state": session_state
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}


@router.get("/sessions/{session_id}/event-pool", summary="Get event pool statistics")
async def get_session_event_pool(session_id: str):
    """
    Get event pool statistics and recent events.
    """
    try:
        session = session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        event_pool = session.event_pool
        
        return {
            "session_id": session_id,
            "event_count": event_pool.get_event_count(),
            "subscriber_count": len(event_pool.subscribers) if hasattr(event_pool, 'subscribers') else 0,
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}


@router.get("/summary", summary="Get summary of all sessions")
async def get_sessions_summary(db: Session = Depends(get_db)):
    """
    Get a comprehensive summary of all sessions.
    
    Includes both database sessions and active in-memory sessions.
    """
    try:
        # Get database sessions
        db_sessions = db.query(GameSession).filter(
            GameSession.is_active == True
        ).all()
        
        # Get in-memory sessions
        active_sessions = session_manager.get_all_sessions()
        
        summary = {
            "total_database_sessions": len(db_sessions),
            "total_active_memory_sessions": len(active_sessions),
            "total_players_connected": 0,
            "total_events_in_pools": 0,
            "total_messages": 0,
            "database_sessions": [],
            "memory_sessions": []
        }
        
        # Database sessions summary
        for db_sess in db_sessions:
            session_data = db_sess.session_data or {}
            is_running = db_sess.session_uuid in active_sessions
            
            db_summary = {
                "session_id": db_sess.session_uuid,
                "session_name": db_sess.session_name,
                "game_mode": db_sess.game_mode.value,
                "status": db_sess.status.value,
                "is_running": is_running,
                "participants_count": len(session_data.get("participants", [])),
                "created_at": db_sess.created_at.isoformat() if db_sess.created_at else None,
            }
            summary["database_sessions"].append(db_summary)
        
        # Memory sessions summary
        for session_id, session in active_sessions.items():
            ws_connections = session_manager.get_all_session_websockets(session_id)
            session_summary = {
                "session_id": session_id,
                "session_name": session.session_name,
                "game_mode": session.game_mode.value,
                "players_connected": len(ws_connections),
                "total_players": len(session.players),
                "total_npcs": len(session.npcs),
                "event_pool_size": session.event_pool.get_event_count(),
                "message_count": len(session.messages),
                "current_location": session.current_location_name,
            }
            summary["memory_sessions"].append(session_summary)
            summary["total_players_connected"] += len(ws_connections)
            summary["total_events_in_pools"] += session.event_pool.get_event_count()
            summary["total_messages"] += len(session.messages)
        
        return summary
    except Exception as e:
        return {"error": str(e)}