"""
Game Engine Integration Module
Connects the FastAPI server with the MAGGxDND game engine
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Optional, Any

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from game.event_pool import EventPool
from game.engine import Session
from game.manipulator import Manipulator
from entity.orchestrator import Orchestrator
from entity.player import Player
from entity.npc import NPC
from schemas.in_game import Character, NPCCharacter, SceneNode, GameModes
from skls_embeddings.chroma_client import ChromaClient
from skls_embeddings.embedding_client import EmbeddingClient
from skls_generator.generator import Generator
from skls_generator.gen_backends.google_gen import GoogleGenAI

from server.main import GameDelivery

logger = logging.getLogger("game_integration")


class GameSessionManager:
    """
    Manages game sessions and their lifecycle.
    Creates and maintains Session objects with GameDelivery.
    """
    
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.event_pools: Dict[str, EventPool] = {}
        self.deliveries: Dict[str, GameDelivery] = {}
        self.logger = logging.getLogger("session_manager")
        
    def create_session(
        self,
        session_id: str,
        session_name: str,
        game_mode: str = "STORY",
        gemini_api_key: Optional[str] = None
    ) -> Session:
        """
        Create a new game session with GameDelivery.
        
        Args:
            session_id: Unique session identifier
            session_name: Human-readable session name
            game_mode: "STORY" or "COMBAT"
            gemini_api_key: API key for Google Gemini
            
        Returns:
            Session object
        """
        self.logger.info(f"Creating session: {session_name} (ID: {session_id})")
        
        # Create event pool
        event_pool = EventPool()
        self.event_pools[session_id] = event_pool
        
        # Create delivery
        delivery_queue = event_pool.subscribe(f"delivery_{session_id}")
        delivery = GameDelivery(delivery_queue, self.logger)
        self.deliveries[session_id] = delivery
        
        # Setup game engine components
        chroma_client = ChromaClient(
            EmbeddingClient(os.getenv("LLAMACPP_EMBED_BASE", "localhost:12345")),
            path="./chroma_db/data.db",
            logger_instance=self.logger
        )
        
        generator = Generator(
            GoogleGenAI(
                api_key=gemini_api_key or os.getenv("GEMINI_API_KEY", "NO_KEY"),
                logger=self.logger,
                model_name="gemini-2.0-flash"
            ),
            logger_instance=self.logger
        )
        
        # Create session
        session = Session(
            session_name=session_name,
            chroma_client=chroma_client,
            logger=self.logger.getChild("session"),
            generator=generator,
            event_pool=event_pool,
            delivery=delivery
        )
        
        # Set game mode
        if game_mode.upper() == "COMBAT":
            session.game_mode = GameModes.COMBAT
        else:
            session.game_mode = GameModes.STORY
            
        # Inject manipulator
        manipulator = Manipulator(
            generator=generator,
            session=session,
            archive=None,
            logger=self.logger.getChild("manipulator")
        )
        session.inject_manipulator(manipulator)
        
        # Create and set orchestrator
        orchestrator = Orchestrator(
            generator=generator,
            logger=self.logger.getChild("orchestrator")
        )
        orchestrator.add_state(session)
        session._init_orchestrator(orchestrator)
        
        # Store session
        self.sessions[session_id] = session
        
        self.logger.info(f"Session created successfully: {session_id}")
        
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        return self.sessions.get(session_id)
    
    def get_delivery(self, session_id: str) -> Optional[GameDelivery]:
        """Get delivery instance for session."""
        return self.deliveries.get(session_id)
    
    def delete_session(self, session_id: str):
        """Delete a session and cleanup resources."""
        if session_id in self.sessions:
            self.logger.info(f"Deleting session: {session_id}")
            del self.sessions[session_id]
            
        if session_id in self.event_pools:
            del self.event_pools[session_id]
            
        if session_id in self.deliveries:
            del self.deliveries[session_id]
    
    async def start_game_loop(self, session_id: str, background_tasks=None):
        """
        Start the game loop for a session.
        
        Args:
            session_id: Session to start
            background_tasks: FastAPI BackgroundTasks (optional)
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        self.logger.info(f"Starting game loop for session: {session_id}")
        
        # Run game loop in background
        asyncio.create_task(self._run_game_loop(session))
    
    async def _run_game_loop(self, session: Session):
        """Run the game loop."""
        try:
            await session.game_loop()
        except Exception as e:
            self.logger.error(f"Game loop error: {e}", exc_info=True)


# Global session manager instance
session_manager = GameSessionManager()


def get_session_manager() -> GameSessionManager:
    """Get the global session manager instance."""
    return session_manager
