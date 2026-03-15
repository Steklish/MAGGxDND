"""
AI Game Service - Bridge between FastAPI server and Core Game Engine

This service handles all AI-related operations for the game engine:
- AI generation for scenes, characters, NPCs
- Plot generation and management
- Action processing with AI interpretation
- Event generation based on player actions

Core Integration:
- Uses core.game.engine.Session for game state
- Uses core.magg.magg.Magg for AI dungeon master logic
- Uses skls_generator for AI content generation
"""
import os
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from core.game.engine import Session
from core.game.event_pool import EventPool
from core.schemas.in_game import Character, NPCCharacter, SceneNode, GameModes
from core.schemas.orchestration import Event, EventTypes, Message
from core.entity.player import Player
from core.entity.npc import NPC

try:
    from skls_generator.generator import Generator
    from skls_generator.gen_backends.google_gen import GoogleGenAI
    from skls_embeddings.chroma_client import ChromaClient
    from skls_embeddings.embedding_client import EmbeddingClient
    SKLS_AVAILABLE = True
except ImportError:
    SKLS_AVAILABLE = False
    Generator = None  # type: ignore
    GoogleGenAI = None  # type: ignore
    ChromaClient = None  # type: ignore
    EmbeddingClient = None  # type: ignore

logger = logging.getLogger(__name__)


class AIGameService:
    """
    Service for handling AI operations in game sessions.
    
    This service acts as a bridge between the FastAPI server
    and the core game engine, ensuring proper AI integration.
    """

    def __init__(self):
        if not SKLS_AVAILABLE:
            logger.warning("SKLS dependencies not available. AI features disabled.")
        
        self._generators: Dict[str, Generator] = {}
        self._chroma_clients: Dict[str, ChromaClient] = {}

    def create_generator(
        self,
        session_id: str,
        gemini_api_key: str,
        gemini_model: str = "gemini-2.0-flash",
        logger_instance: Optional[logging.Logger] = None
    ) -> Generator:
        """
        Create AI generator for a session.
        
        Args:
            session_id: Unique session identifier
            gemini_api_key: Google Gemini API key
            gemini_model: Model name to use
            logger_instance: Optional logger instance
            
        Returns:
            Configured Generator instance
        """
        if not SKLS_AVAILABLE:
            raise ImportError("SKLS dependencies not installed")
        
        if session_id in self._generators:
            return self._generators[session_id]
        
        log = logger_instance or logger
        
        # Create Google GenAI backend
        google_genai = GoogleGenAI(
            api_key=gemini_api_key,
            logger=log,
            model_name=gemini_model
        )
        
        # Create Generator
        generator = Generator(
            google_genai,
            logger_instance=log
        )
        
        self._generators[session_id] = generator
        log.info(f"AI Generator created for session {session_id} using {gemini_model}")
        
        return generator

    def create_chroma_client(
        self,
        session_id: str,
        embed_base: str = "localhost:12345",
        chroma_path: str = "./chroma_db/data.db",
        logger_instance: Optional[logging.Logger] = None
    ) -> ChromaClient:
        """
        Create ChromaDB client for vector storage.
        
        Args:
            session_id: Unique session identifier
            embed_base: Embedding service endpoint
            chroma_path: Path to ChromaDB database
            logger_instance: Optional logger instance
            
        Returns:
            Configured ChromaClient instance
        """
        if not SKLS_AVAILABLE:
            raise ImportError("SKLS dependencies not installed")
        
        if session_id in self._chroma_clients:
            return self._chroma_clients[session_id]
        
        log = logger_instance or logger
        
        # Create embedding client
        embedding_client = EmbeddingClient(embed_base)
        
        # Create ChromaClient
        chroma_client = ChromaClient(
            embedding_client,
            path=chroma_path,
            logger_instance=log
        )
        
        self._chroma_clients[session_id] = chroma_client
        log.info(f"ChromaClient created for session {session_id}")
        
        return chroma_client

    async def generate_scene(
        self,
        generator: Generator,
        prompt: str,
        session: Optional[Session] = None
    ) -> SceneNode:
        """
        Generate a scene using AI.
        
        Args:
            generator: AI Generator instance
            prompt: Scene description prompt
            session: Optional session for context
            
        Returns:
            Generated SceneNode
        """
        try:
            logger.info(f"Generating scene with prompt: {prompt[:100]}...")
            
            scene = generator.generate_one_shot(
                pydantic_model=SceneNode,
                prompt=prompt
            )
            
            logger.info(f"Scene generated: {scene.name}")
            return scene
            
        except Exception as e:
            logger.error(f"Failed to generate scene: {e}", exc_info=True)
            raise

    async def generate_character(
        self,
        generator: Generator,
        prompt: str,
        session: Optional[Session] = None
    ) -> Character:
        """
        Generate a player character using AI.
        
        Args:
            generator: AI Generator instance
            prompt: Character description prompt
            session: Optional session for context
            
        Returns:
            Generated Character
        """
        try:
            logger.info(f"Generating character with prompt: {prompt[:100]}...")
            
            character = generator.generate_one_shot(
                pydantic_model=Character,
                prompt=prompt
            )
            
            logger.info(f"Character generated: {character.name}")
            return character
            
        except Exception as e:
            logger.error(f"Failed to generate character: {e}", exc_info=True)
            raise

    async def generate_npc(
        self,
        generator: Generator,
        prompt: str,
        session: Optional[Session] = None
    ) -> NPCCharacter:
        """
        Generate an NPC using AI.
        
        Args:
            generator: AI Generator instance
            prompt: NPC description prompt
            session: Optional session for context
            
        Returns:
            Generated NPCCharacter
        """
        try:
            logger.info(f"Generating NPC with prompt: {prompt[:100]}...")
            
            npc = generator.generate_one_shot(
                pydantic_model=NPCCharacter,
                prompt=prompt
            )
            
            logger.info(f"NPC generated: {npc.name}")
            return npc
            
        except Exception as e:
            logger.error(f"Failed to generate NPC: {e}", exc_info=True)
            raise

    async def process_player_action(
        self,
        session: Session,
        player_id: str,
        action_text: str,
        character_name: str
    ) -> Tuple[bool, str, List[Event]]:
        """
        Process a player action through the game engine.
        
        This is the main entry point for handling player actions.
        It routes the action through the core engine's manipulator
        and returns the results.
        
        Args:
            session: Game session
            player_id: ID of the player
            action_text: Text description of the action
            character_name: Name of the character performing action
            
        Returns:
            Tuple of (success, result_message, generated_events)
        """
        try:
            logger.info(f"Processing player action: {action_text[:100]}...")
            
            # Get the player from session
            player = None
            for p in session.players:
                if p.character.name == character_name or str(p.id) == player_id:
                    player = p
                    break
            
            if not player:
                return False, "Player not found", []
            
            # Use session's manipulator to process action
            # This integrates with the core engine's action processing
            manipulator = session.manipulator
            
            # Create action event
            action_event = Event(
                event_type=EventTypes.PLAYER_ACTION,
                data={
                    "action": action_text,
                    "character": character_name,
                    "player_id": player_id
                },
                source=character_name
            )
            
            # Publish to event pool
            session.event_pool.publish(action_event)
            
            # Process through manipulator
            # The manipulator will use AI to interpret and resolve the action
            result = await manipulator.process_action(
                player=player,
                action_text=action_text
            )
            
            # Get generated events
            generated_events = []
            
            logger.info(f"Action processed successfully: {result}")
            
            return True, result, generated_events
            
        except Exception as e:
            logger.error(f"Failed to process player action: {e}", exc_info=True)
            return False, str(e), []

    def cleanup_session(self, session_id: str):
        """
        Cleanup AI resources for a session.
        
        Args:
            session_id: Session to cleanup
        """
        if session_id in self._generators:
            del self._generators[session_id]
            logger.info(f"Generator cleaned up for session {session_id}")
        
        if session_id in self._chroma_clients:
            del self._chroma_clients[session_id]
            logger.info(f"ChromaClient cleaned up for session {session_id}")


# Global service instance
ai_game_service = AIGameService()
