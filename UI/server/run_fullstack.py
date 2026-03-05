"""
MAGGxDND Full Stack Runner
Запускает сервер + игровой движок + game loop в одном процессе
"""

import asyncio
import logging
import os
import sys
import uuid
from typing import Optional

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from logging.handlers import RotatingFileHandler

# Setup logging
os.makedirs('log', exist_ok=True)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                             datefmt='%Y-%m-%d %H:%M:%S')

file_handler = RotatingFileHandler(
    './log/fullstack_runner.log',
    maxBytes=10*1024*1024,
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

logger = logging.getLogger("runner")


class FullStackRunner:
    """
    Runs the complete MAGGxDND stack:
    - FastAPI server
    - Game engine Session
    - Game loop
    - WebSocket connections
    """
    
    def __init__(self):
        self.session = None
        self.server = None
        self.running = False
        self.logger = logging.getLogger("fullstack_runner")
        
    async def initialize_game(self, 
                              session_name: str = "Test Session",
                              game_mode: str = "STORY",
                              scene_prompt: str = "A cozy tavern with warm fire",
                              character_prompts: list = None,
                              npc_prompts: list = None,
                              gemini_api_key: Optional[str] = None):
        """
        Initialize a complete game session.
        
        Args:
            session_name: Name for the session
            game_mode: "STORY" or "COMBAT"
            scene_prompt: Prompt for initial scene generation
            character_prompts: List of prompts for player characters
            npc_prompts: List of prompts for NPCs
            gemini_api_key: Google Gemini API key
        """
        self.logger.info("=" * 60)
        self.logger.info("Initializing MAGGxDND Full Stack")
        self.logger.info("=" * 60)
        
        try:
            # Import game engine components
            from game.engine import Session
            from game.manipulator import Manipulator
            from entity.orchestrator import Orchestrator
            from game.event_pool import EventPool
            from skls_embeddings.chroma_client import ChromaClient
            from skls_embeddings.embedding_client import EmbeddingClient
            from skls_generator.generator import Generator
            from skls_generator.gen_backends.google_gen import GoogleGenAI
            
            # Import our GameDelivery
            from server.main import GameDelivery
            
            # Create event pool
            event_pool = EventPool()
            self.logger.info("✓ EventPool created")
            
            # Create delivery
            delivery_queue = event_pool.subscribe("delivery")
            delivery = GameDelivery(delivery_queue, self.logger)
            self.logger.info("✓ GameDelivery created")
            
            # Setup components
            chroma_client = ChromaClient(
                EmbeddingClient(os.getenv("LLAMACPP_EMBED_BASE", "localhost:12345")),
                path="./chroma_db/data.db",
                logger_instance=self.logger
            )
            self.logger.info("✓ ChromaClient initialized")
            
            generator = Generator(
                GoogleGenAI(
                    api_key=gemini_api_key or os.getenv("GEMINI_API_KEY", "NO_KEY"),
                    logger=self.logger,
                    model_name="gemini-2.0-flash"
                ),
                logger_instance=self.logger
            )
            self.logger.info("✓ Generator initialized")
            
            # Create session
            session_id = str(uuid.uuid4())
            session = Session(
                session_name=session_name,
                chroma_client=chroma_client,
                logger=self.logger.getChild("session"),
                generator=generator,
                event_pool=event_pool,
                delivery=delivery
            )
            self.logger.info(f"✓ Session created: {session_name}")
            
            # Set game mode
            from schemas.in_game import GameModes
            if game_mode.upper() == "COMBAT":
                session.game_mode = GameModes.COMBAT
            else:
                session.game_mode = GameModes.STORY
            self.logger.info(f"✓ Game mode: {game_mode}")
            
            # Inject manipulator
            manipulator = Manipulator(
                generator=generator,
                session=session,
                archive=None,
                logger=self.logger.getChild("manipulator")
            )
            session.inject_manipulator(manipulator)
            self.logger.info("✓ Manipulator injected")
            
            # Create and set orchestrator
            orchestrator = Orchestrator(
                generator=generator,
                logger=self.logger.getChild("orchestrator")
            )
            orchestrator.add_state(session)
            session._init_orchestrator(orchestrator)
            self.logger.info("✓ Orchestrator initialized")
            
            # Generate initial scene
            self.logger.info(f"Generating scene: {scene_prompt}")
            from schemas.in_game import SceneNode
            scene = generator.generate_one_shot(
                pydantic_model=SceneNode,
                prompt=scene_prompt
            )
            session.current_scene = scene
            session.current_location_name = scene.name
            self.logger.info(f"✓ Scene generated: {scene.name}")
            
            # Generate player characters if prompts provided
            character_prompts = character_prompts or []
            if character_prompts:
                from schemas.in_game import Character
                from entity.player import Player
                
                for i, prompt in enumerate(character_prompts):
                    self.logger.info(f"Generating character {i+1}: {prompt}")
                    char = generator.generate_one_shot(
                        pydantic_model=Character,
                        prompt=prompt
                    )
                    
                    # Create player
                    player_queue = event_pool.subscribe(f"player_{char.name}")
                    player = Player(
                        character=char,
                        event_queuee=player_queue,
                        logger=self.logger.getChild("player"),
                        orchestrator=orchestrator
                    )
                    session.players.append(player)
                    self.logger.info(f"✓ Character created: {char.name}")
            
            # Generate NPCs if prompts provided
            npc_prompts = npc_prompts or []
            if npc_prompts:
                from schemas.in_game import NPCCharacter
                from entity.npc import NPC
                
                for i, prompt in enumerate(npc_prompts):
                    self.logger.info(f"Generating NPC {i+1}: {prompt}")
                    npc_char = generator.generate_one_shot(
                        pydantic_model=NPCCharacter,
                        prompt=prompt
                    )
                    npc_char.current_scene = scene.name
                    
                    # Create NPC
                    npc_queue = event_pool.subscribe(f"npc_{npc_char.name}")
                    npc = NPC(
                        character=npc_char,
                        event_queuee=npc_queue,
                        logger=self.logger.getChild("npc")
                    )
                    session.npcs.append(npc)
                    self.logger.info(f"✓ NPC created: {npc_char.name}")
            
            self.session = session
            self.logger.info("=" * 60)
            self.logger.info("✓ Game initialization complete!")
            self.logger.info(f"  Session: {session_name}")
            self.logger.info(f"  Players: {len(session.players)}")
            self.logger.info(f"  NPCs: {len(session.npcs)}")
            self.logger.info(f"  Scene: {scene.name}")
            self.logger.info("=" * 60)
            
            return session_id
            
        except Exception as e:
            self.logger.error(f"Failed to initialize game: {e}", exc_info=True)
            raise
    
    async def run_game_loop(self):
        """Run the game loop."""
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        self.logger.info("Starting game loop...")
        self.running = True
        
        try:
            await self.session.game_loop()
        except Exception as e:
            self.logger.error(f"Game loop error: {e}", exc_info=True)
            self.running = False
            raise
    
    async def run_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the FastAPI server."""
        import uvicorn
        
        self.logger.info(f"Starting FastAPI server on {host}:{port}")
        
        config = uvicorn.Config(
            "server.main:app",
            host=host,
            port=port,
            log_level="info",
            reload=False
        )
        
        self.server = uvicorn.Server(config)
        
        try:
            await self.server.serve()
        except Exception as e:
            self.logger.error(f"Server error: {e}", exc_info=True)
            raise
    
    async def run(self, 
                  start_server: bool = True,
                  start_game: bool = True,
                  **game_kwargs):
        """
        Run everything together.
        
        Args:
            start_server: Start FastAPI server
            start_game: Start game loop
            **game_kwargs: Arguments for initialize_game()
        """
        tasks = []
        
        # Initialize game if requested
        if start_game:
            await self.initialize_game(**game_kwargs)
        
        # Create tasks
        if start_game and self.session:
            tasks.append(asyncio.create_task(self.run_game_loop()))
            self.logger.info("✓ Game loop task created")
        
        if start_server:
            # Need to run server in a way that doesn't block
            tasks.append(asyncio.create_task(self.run_server()))
            self.logger.info("✓ Server task created")
        
        # Wait for all tasks
        if tasks:
            self.logger.info("All systems started!")
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            self.logger.info("Nothing to run!")


async def main():
    """Main entry point."""
    runner = FullStackRunner()
    
    # Get API key from environment or use default
    gemini_api_key = os.getenv("GEMINI_API_KEY", "NO_KEY")
    
    # Initialize and run
    await runner.initialize_game(
        session_name="Demo Adventure",
        game_mode="STORY",
        scene_prompt="A medieval tavern called 'The Laughing Dragon' with a warm fireplace, wooden tables, and a friendly bartender",
        character_prompts=[
            "A human wizard named Gandor with a long beard and blue robes, knows fireball and magic missile spells",
            "A dwarf fighter named Thorin with an axe and shield, brave and loyal"
        ],
        npc_prompts=[
            "A mysterious hooded figure sitting in the corner of the tavern"
        ],
        gemini_api_key=gemini_api_key
    )
    
    # Run server and game loop concurrently
    await runner.run(
        start_server=True,
        start_game=True
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
