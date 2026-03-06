"""
MAGGxDND Game Server with Full Game Engine Integration
This server integrates the FastAPI backend with the actual game engine
"""

import asyncio
import logging
import os
import sys
import uuid
from typing import Dict, Optional, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from game.event_pool import EventPool, SubscriberQueue
from interface.delivery import Delivery, Request
from schemas.in_game import Character, NPCCharacter, SceneNode, GameModes, Coordinate2D
from schemas.orchestration import Event

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("game_server_engine")


# Import GameDelivery and WebSocketHandler from main.py
from server.main import GameDelivery, WebSocketHandler


# Global state
active_sessions: Dict[str, dict] = {}
event_pools: Dict[str, EventPool] = {}
game_deliveries: Dict[str, GameDelivery] = {}
session_managers: Dict[str, any] = {}  # Will hold Session objects


# Request models
class SessionInitRequest(BaseModel):
    session_name: str
    game_mode: str = "STORY"
    scene_prompt: str = "A dark dungeon corridor"
    character_prompts: List[str] = []
    npc_prompts: List[str] = []
    gemini_api_key: Optional[str] = None


# Create FastAPI app
app = FastAPI(
    title="MAGGxDND Game Server (With Engine)",
    description="WebSocket & REST API with full game engine integration",
    version="0.2.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize server on startup."""
    logger.info("MAGGxDND Game Server (with Engine) starting...")


@app.websocket("/ws/{session_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, player_id: str):
    """WebSocket endpoint for real-time game communication."""
    logger.info(f"New WebSocket connection: session={session_id}, player={player_id}")
    
    # Get or create event pool for this session
    if session_id not in event_pools:
        event_pools[session_id] = EventPool()
        logger.info(f"Created new EventPool for session: {session_id}")
    
    event_pool = event_pools[session_id]
    
    # Subscribe player to events
    subscriber_queue = event_pool.subscribe(player_id)
    
    # Create or get delivery instance
    if session_id not in game_deliveries:
        delivery = GameDelivery(subscriber_queue, logger)
        game_deliveries[session_id] = delivery
        active_sessions[session_id] = {
            "delivery": delivery,
            "players": {},
            "session_object": None
        }
    else:
        delivery = game_deliveries[session_id]
    
    # Create WebSocket handler
    handler = WebSocketHandler(
        websocket=websocket,
        session_id=session_id,
        player_id=player_id,
        delivery=delivery,
        event_queue=subscriber_queue,
        logger_instance=logger
    )
    
    # Connect and handle
    await handler.connect()
    
    # Keep connection alive
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        await handler.disconnect()
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await handler.disconnect()


@app.post("/api/v1/sessions/start_real_game", response_model=dict)
async def start_real_game(request: SessionInitRequest, background_tasks: BackgroundTasks):
    """
    Start a REAL game session with the actual game engine running.
    This creates characters, NPCs, scene, and starts the game loop.
    """
    logger.info(f"Starting REAL game session: {request.session_name}")
    
    try:
        # Import game engine components
        from game.engine import Session
        from game.manipulator import Manipulator
        from entity.orchestrator import Orchestrator
        from entity.player import Player
        from entity.npc import NPC
        from skls_embeddings.chroma_client import ChromaClient
        from skls_embeddings.embedding_client import EmbeddingClient
        from skls_generator.generator import Generator
        from skls_generator.gen_backends.google_gen import GoogleGenAI
        from schemas.in_game import GameModes, SceneNode, Character, NPCCharacter
        
        session_id = str(uuid.uuid4())
        
        # Create event pool
        event_pool = EventPool()
        event_pools[session_id] = event_pool
        logger.info(f"[{session_id}] EventPool created")
        
        # Create delivery
        delivery_queue = event_pool.subscribe(f"delivery_{session_id}")
        delivery = GameDelivery(delivery_queue, logger)
        game_deliveries[session_id] = delivery
        logger.info(f"[{session_id}] GameDelivery created")
        
        # Setup components
        chroma_client = ChromaClient(
            EmbeddingClient(os.getenv("LLAMACPP_EMBED_BASE", "localhost:12345")),
            path="./chroma_db/data.db",
            logger_instance=logger
        )
        
        generator = Generator(
            GoogleGenAI(
                api_key=request.gemini_api_key or os.getenv("GEMINI_API_KEY", "NO_KEY"),
                logger=logger,
                model_name="gemini-2.0-flash"
            ),
            logger_instance=logger
        )
        
        # Create session
        session = Session(
            session_name=request.session_name,
            chroma_client=chroma_client,
            logger=logger.getChild("session"),
            generator=generator,
            event_pool=event_pool,
            delivery=delivery
        )
        
        # Set game mode
        if request.game_mode.upper() == "COMBAT":
            session.game_mode = GameModes.COMBAT
        else:
            session.game_mode = GameModes.STORY
        
        # Inject manipulator
        manipulator = Manipulator(
            generator=generator,
            session=session,
            archive=None,
            logger=logger.getChild("manipulator")
        )
        session.inject_manipulator(manipulator)
        
        # Create and set orchestrator
        orchestrator = Orchestrator(
            generator=generator,
            logger=logger.getChild("orchestrator")
        )
        orchestrator.add_state(session)
        session._init_orchestrator(orchestrator)
        
        # Generate scene
        logger.info(f"[{session_id}] Generating scene...")
        scene = generator.generate_one_shot(
            pydantic_model=SceneNode,
            prompt=request.scene_prompt or "A medieval tavern"
        )
        session.current_scene = scene
        session.current_location_name = scene.name
        logger.info(f"[{session_id}] Scene: {scene.name}")
        
        # Generate player characters
        character_prompts = request.character_prompts or [
            "A human wizard named Gandor with fireball spell",
            "A dwarf fighter named Thorin with an axe"
        ]
        
        for prompt in character_prompts:
            try:
                char = generator.generate_one_shot(
                    pydantic_model=Character,
                    prompt=prompt
                )
                
                player_queue = event_pool.subscribe(f"player_{char.name}")
                player = Player(
                    character=char,
                    event_queuee=player_queue,
                    logger=logger.getChild("player"),
                    orchestrator=orchestrator
                )
                session.players.append(player)
                logger.info(f"[{session_id}] Player: {char.name}")
            except Exception as e:
                logger.error(f"Failed to create character: {e}")
        
        # Generate NPCs
        npc_prompts = request.npc_prompts or [
            "A mysterious hooded stranger"
        ]
        
        for prompt in npc_prompts:
            try:
                npc_char = generator.generate_one_shot(
                    pydantic_model=NPCCharacter,
                    prompt=prompt
                )
                npc_char.current_scene = scene.name
                
                npc_queue = event_pool.subscribe(f"npc_{npc_char.name}")
                npc = NPC(
                    character=npc_char,
                    event_queuee=npc_queue,
                    logger=logger.getChild("npc")
                )
                session.npcs.append(npc)
                logger.info(f"[{session_id}] NPC: {npc_char.name}")
            except Exception as e:
                logger.error(f"Failed to create NPC: {e}")
        
        # Store session
        active_sessions[session_id] = {
            "delivery": delivery,
            "players": {p.character.name: p for p in session.players},
            "session_object": session
        }
        session_managers[session_id] = session
        game_deliveries[session_id] = delivery
        event_pools[session_id] = event_pool
        
        logger.info(f"[{session_id}] Session stored in active_sessions")
        
        # Start game loop in background
        background_tasks.add_task(run_game_loop, session_id)
        
        logger.info(f"[{session_id}] REAL GAME STARTED!")
        
        return {
            "status": "running",
            "session_id": session_id,
            "session_name": request.session_name,
            "game_mode": request.game_mode,
            "scene": scene.name,
            "players": [p.character.name for p in session.players],
            "npcs": [n.character.name for n in session.npcs],
            "message": "Real game session started with AI!"
        }
        
    except Exception as e:
        logger.error(f"Failed to start real game: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start game: {str(e)}")


@app.get("/api/v1/sessions/{session_id}/game_info")
async def get_game_info(session_id: str):
    """Get detailed game session info including players, NPCs, and scene."""
    session = session_managers.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        session_data = active_sessions.get(session_id, {})
        session_obj = session_data.get("session_object")

        players_data = []
        for player_name, player_obj in session_data.get("players", {}).items():
            if hasattr(player_obj, 'character'):
                char = player_obj.character
                # Get stats if available
                stats = getattr(char, 'stats', None)
                players_data.append({
                    "name": char.name if hasattr(char, 'name') else str(char),
                    "race": getattr(char, 'race', 'Human'),
                    "char_class": getattr(char, 'char_class', 'Fighter'),
                    "level": getattr(char, 'level', 1),
                    "current_hp": getattr(char, 'current_hp', 10),
                    "max_hp": getattr(char, 'max_hp', 10),
                    "armor_class": getattr(char, 'armor_class', 10),
                    "speed": getattr(char, 'speed', 30),
                    "proficiency_bonus": getattr(char, 'proficiency_bonus', 2),
                    "initiative_bonus": getattr(char, 'initiative_bonus', 0),
                    "is_alive": getattr(char, 'is_alive', True),
                    "stats": {
                        "strength": getattr(stats, 'strength', 10) if stats else 10,
                        "dexterity": getattr(stats, 'dexterity', 10) if stats else 10,
                        "constitution": getattr(stats, 'constitution', 10) if stats else 10,
                        "intelligence": getattr(stats, 'intelligence', 10) if stats else 10,
                        "wisdom": getattr(stats, 'wisdom', 10) if stats else 10,
                        "charisma": getattr(stats, 'charisma', 10) if stats else 10,
                    } if stats else {
                        "strength": 10, "dexterity": 10, "constitution": 10,
                        "intelligence": 10, "wisdom": 10, "charisma": 10,
                    },
                })

        npcs_data = []
        if session_obj and hasattr(session_obj, 'npcs'):
            for npc in session_obj.npcs:
                if hasattr(npc, 'character'):
                    char = npc.character
                    stats = getattr(char, 'stats', None)
                    npcs_data.append({
                        "name": getattr(char, 'name', 'Unknown'),
                        "race": getattr(char, 'race', 'Human'),
                        "char_class": getattr(char, 'char_class', 'Commoner'),
                        "alignment": getattr(char, 'alignment', 'Neutral'),
                        "current_hp": getattr(char, 'current_hp', 10),
                        "max_hp": getattr(char, 'max_hp', 10),
                        "armor_class": getattr(char, 'armor_class', 10),
                        "speed": getattr(char, 'speed', 30),
                        "proficiency_bonus": getattr(char, 'proficiency_bonus', 2),
                        "initiative_bonus": getattr(char, 'initiative_bonus', 0),
                        "is_alive": getattr(char, 'is_alive', True),
                        "stats": {
                            "strength": getattr(stats, 'strength', 10) if stats else 10,
                            "dexterity": getattr(stats, 'dexterity', 10) if stats else 10,
                            "constitution": getattr(stats, 'constitution', 10) if stats else 10,
                            "intelligence": getattr(stats, 'intelligence', 10) if stats else 10,
                            "wisdom": getattr(stats, 'wisdom', 10) if stats else 10,
                            "charisma": getattr(stats, 'charisma', 10) if stats else 10,
                        } if stats else {
                            "strength": 10, "dexterity": 10, "constitution": 10,
                            "intelligence": 10, "wisdom": 10, "charisma": 10,
                        },
                    })

        scene_data = None
        if session_obj and hasattr(session_obj, 'current_scene'):
            scene = session_obj.current_scene
            if scene:
                scene_data = {
                    "name": getattr(scene, 'name', 'Unknown'),
                    "description": getattr(scene, 'description', ''),
                }

        return {
            "session_id": session_id,
            "session_name": session.session_name,
            "game_mode": session.game_mode.value if hasattr(session.game_mode, 'value') else str(session.game_mode),
            "status": "running",
            "players": players_data,
            "npcs": npcs_data,
            "scene": scene_data,
        }

    except Exception as e:
        logger.error(f"Failed to get game info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get game info: {str(e)}")


async def run_game_loop(session_id: str):
    """Run the game loop for a session."""
    session = session_managers.get(session_id)
    if not session:
        logger.error(f"Session not found: {session_id}")
        return
    
    try:
        logger.info(f"Starting game loop for session: {session_id}")
        await session.game_loop()
    except Exception as e:
        logger.error(f"Game loop error for session {session_id}: {e}", exc_info=True)


@app.post("/api/v1/sessions/{session_id}/add_player_character")
async def add_player_character(
    session_id: str,
    character_data: dict,
    background_tasks: BackgroundTasks
):
    """Add a player character to an active session."""
    session = session_managers.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        # Create Character object
        character = Character(**character_data)
        
        # Import Player class
        from entity.player import Player
        
        # Get player's event queue
        player_id = character.name
        event_queue = event_pools[session_id].subscribe(player_id)
        
        # Create player
        player = Player(
            character=character,
            event_queuee=event_queue,
            logger=logger.getChild("player"),
            orchestrator=session.orchestrator
        )
        
        # Add to session
        session.players.append(player)
        
        logger.info(f"Added player character: {character.name} to session {session_id}")
        
        return {
            "status": "success",
            "player_id": player_id,
            "character_name": character.name
        }
        
    except Exception as e:
        logger.error(f"Failed to add player character: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to add character: {str(e)}")


@app.post("/api/v1/sessions/{session_id}/add_npc")
async def add_npc(
    session_id: str,
    character_data: dict,
    background_tasks: BackgroundTasks
):
    """Add an NPC to an active session."""
    session = session_managers.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        # Create NPCCharacter object
        character = NPCCharacter(**character_data)
        
        # Import NPC class
        from entity.npc import NPC
        
        # Get NPC's event queue
        event_queue = event_pools[session_id].subscribe(f"npc_{character.name}")
        
        # Create NPC
        npc = NPC(
            character=character,
            event_queuee=event_queue,
            logger=logger.getChild("npc")
        )
        
        # Add to session
        session.npcs.append(npc)
        
        logger.info(f"Added NPC: {character.name} to session {session_id}")
        
        return {
            "status": "success",
            "npc_name": character.name
        }
        
    except Exception as e:
        logger.error(f"Failed to add NPC: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to add NPC: {str(e)}")


# Include original routes for compatibility
from server.routes import sessions, characters, auth

app.include_router(sessions.router, prefix="/api/v1", tags=["Sessions"])
app.include_router(characters.router, prefix="/api/v1", tags=["Characters"])
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
