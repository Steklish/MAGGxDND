import logging
import uuid
import threading
import sys
from typing import Dict

import os

# Get the directory of the current file (e.g., D:\...\MAGGxDND\server)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (the project root, e.g., D:\...\MAGGxDND)
project_root = os.path.dirname(current_dir)
# Add the project root to the Python path
sys.path.append(project_root)

from game.engine import Session
from delivery.game_delivery import GameDelivery
from websocket.manager import ConnectionManager
from game.event_pool import EventPool
from schemas.in_game import Character, SceneNode
# We will need these later
# from magg.magg import MAGG
# from magg.generator import Generator

logger = logging.getLogger("server.session_manager")

# In-memory storage for active sessions
# In a production environment, this might be handled by a separate service or database.
sessions: Dict[str, Session] = {}
event_pools: Dict[str, EventPool] = {}

def create_new_session(
    session_name: str,
    manager: ConnectionManager,
    player_characters: List[Character],
    initial_scene: SceneNode,
) -> Session:
    """
    Creates a new game session, initializes its components,
    and starts its game loop in a background thread.
    """
    session_id = str(uuid.uuid4())
    logger.info(f"Creating new session '{session_name}' with ID: {session_id}")

    # 1. Create a dedicated EventPool for this session
    event_pool = EventPool()
    event_pools[session_id] = event_pool

    # 2. Create the GameDelivery instance for this session
    # Each session needs its own delivery mechanism to talk to its players
    delivery_logger = logging.getLogger(f"server.delivery.{session_id}")
    delivery = GameDelivery(
        event_queue=event_pool.subscribe(f"delivery-{session_id}"),
        logger=delivery_logger,
        manager=manager
    )

    # 3. Create the core Session object from the game engine
    session_logger = logging.getLogger(f"game.engine.{session_id}")
    
    # TODO: Initialize the Generator and MAGG properly
    # generator = Generator(logger=session_logger)
    # chroma_client = None # Placeholder
    
    session = Session(
        session_name=session_id, # Use UUID as the internal name
        # chroma_client=chroma_client,
        logger=session_logger,
        # generator=generator,
        event_pool=event_pool,
        delivery=delivery,
    )
    
    # 4. Store the session
    sessions[session_id] = session

    session.init_new_session(
        scene=initial_scene,
        player_characters=player_characters,
        # logger instances for player/npc can be created here if needed
    )

    # 6. Start the game loop in a separate thread
    # This is CRITICAL. The game_loop is a blocking while(True) loop.
    # Running it directly would block the entire server.
    loop_thread = threading.Thread(
        target=session.game_loop,
        name=f"game-loop-{session_id}",
        daemon=True  # Allows the main program to exit even if threads are running
    )
    loop_thread.start()
    logger.info(f"Game loop started for session {session_id} in a background thread.")

    return session

def get_session(session_id: str) -> Session | None:
    """Retrieves an active session by its ID."""
    return sessions.get(session_id)

def end_session(session_id: str) -> bool:
    """Ends a session and cleans up resources."""
    session = sessions.get(session_id)
    if not session:
        return False
    
    # The game loop will exit on the next iteration because is_running is False
    session.is_running = False
    
    del sessions[session_id]
    if session_id in event_pools:
        del event_pools[session_id]
        
    logger.info(f"Session {session_id} has been terminated.")
    return True
