import io
import json
import os
import sys
import logging
import subprocess
from logging.handlers import RotatingFileHandler
from game.engine import Session
from game.event_pool import EventPool
from game.manipulator import Manipulator
from game.orchestrator import Orchestrator
from schemas.in_game import Character, NPCCharacter, SceneNode
from skls_generator.generator import Generator
from skls_generator.gen_backends.google_gen import GoogleGenAI

# Mock ChromaClient to avoid ChromaDB issues
class MockChromaClient:
    def __init__(self, embedding_client, logger_instance=None):
        self.embedding_client = embedding_client
        self.logger_instance = logger_instance
        self.collections = {}

    def get_collection(self, name):
        if name not in self.collections:
            self.collections[name] = MockCollection(name)
        return self.collections[name]

    def list_collections(self):
        return list(self.collections.keys())

    def delete_collection(self, name):
        if name in self.collections:
            del self.collections[name]

class MockCollection:
    def __init__(self, name):
        self.name = name
        self.data = []

    def add(self, documents=None, embeddings=None, metadatas=None, ids=None):
        # Mock implementation
        pass

    def query(self, query_embeddings=None, n_results=10, where=None):
        # Mock implementation returning empty results
        return {"documents": [], "metadatas": [], "distances": [], "ids": []}

    def peek(self):
        return {"count": len(self.data)}

    def count(self):
        return len(self.data)

# Mock EmbeddingClient
class MockEmbeddingClient:
    def embed_query(self, text):
        # Return a mock embedding (simple hash-based vector)
        return [hash(text + str(i)) % 1000 / 1000.0 for i in range(1536)]  # Typical embedding size

    def embed_documents(self, texts):
        return [self.embed_query(text) for text in texts]

# Set console code page to UTF-8 on Windows to handle Unicode characters properly
if os.name == 'nt':  # Windows
    subprocess.run(['chcp', '65001'], shell=True)

# Force stdout to use UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8') # type: ignore


# Custom logging setup to handle Unicode characters
def setup_unicode_logging(log_file_path: str = './log/application.log'):
    """Setup logging with Unicode support."""
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                 datefmt='%Y-%m-%d %H:%M:%S')

    # 1. File Handler (Keep this, it was correct)
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Avoid adding duplicate handlers if function is called twice
    if not root_logger.handlers:
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)


os.makedirs('log', exist_ok=True)
setup_unicode_logging('./log/application.log')

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)


# Create specific named loggers for different components while preserving global configuration
main_logger = logging.getLogger("game.main")
engine_logger = logging.getLogger("game.engine")
manipulator_logger = logging.getLogger("game.manipulator")
orchestrator_logger = logging.getLogger("game.orchestrator")
magg_logger = logging.getLogger("magg.core")
npc_logger = logging.getLogger("npc.core")
player_logger = logging.getLogger("player.core")

# Set log levels for different components
main_logger.setLevel(logging.WARNING)
engine_logger.setLevel(logging.DEBUG)
manipulator_logger.setLevel(logging.DEBUG)
orchestrator_logger.setLevel(logging.DEBUG)
magg_logger.setLevel(logging.INFO)
npc_logger.setLevel(logging.INFO)
player_logger.setLevel(logging.INFO)

print("Starting the game...")

generator = Generator(GoogleGenAI(api_key=os.getenv("GEMINI_API_KEY"), logger=main_logger), logger_instance=main_logger)
chroma_client = MockChromaClient(MockEmbeddingClient(), logger_instance=main_logger)


# -- INIT SESSION AND MANIPULATOR --

session = Session(
    session_name="example_session",
    chroma_client=chroma_client,
    logger=engine_logger,
    generator=generator,
    event_pool=EventPool(),
    magg_logger=magg_logger
)

session.inject_manipulator(
    manipulator = Manipulator(
        generator=generator,
        state=session,
        archive=None,
        logger=manipulator_logger
    )
)

orchestrator = Orchestrator(
    generator=generator,
    logger=orchestrator_logger
)
orchestrator.add_state(session)


session._init_orchestrator(orchestrator)

# -- LOAD OR INIT GAME STATE --

import os

save_file_path = "./saves/ex_01.json"

if os.path.exists(save_file_path):
    try:
        session.load_session_from_save(save_file_path)
        # Check if loading was successful by verifying we have players or NPCs
        if len(session.players) == 0 and len(session.npcs) == 0:
            print("Save file loaded but no characters found. Creating a new game session...")
            raise ValueError("No characters in save file")
        # Initialize the turn queue after successful loading
        session._initialize_turn_queue()
    except Exception as e:
        print(f"Failed to load save file: {e}. Creating a new game session...")

        # Generate a scene, character, and NPC for the new game
        scene = generator.generate_one_shot(
            pydantic_model=SceneNode,
            prompt="A dark and eerie forest clearing at night, with twisted trees and a faint mist."
        )

        ch1 = generator.generate_one_shot(
            pydantic_model=Character,
            prompt="A wizard named Ogorek. has some random spells"
        )

        npc1 = generator.generate_one_shot(
            pydantic_model=NPCCharacter,
            prompt="An evil ork warrior with an axe."
        )

        npc1.current_scene = scene.name
        session.init_new_session(
            scene=scene,
            player_characters=[ch1],
            npcs=[npc1],
            npc_logger=npc_logger,
            player_logger=player_logger
        )

        # Save the newly created session
        session.save_session(save_file_path)

        # Initialize the turn queue with all characters
        session._initialize_turn_queue()
else:
    print("Save file not found. Creating a new game session...")

    # Generate a scene, character, and NPC for the new game
    scene = generator.generate_one_shot(
        pydantic_model=SceneNode,
        prompt="A dark and eerie forest clearing at night, with twisted trees and a faint mist."
    )

    ch1 = generator.generate_one_shot(
        pydantic_model=Character,
        prompt="A wizard named Ogorek. has some random spells"
    )

    npc1 = generator.generate_one_shot(
        pydantic_model=NPCCharacter,
        prompt="An evil ork warrior with an axe."
    )

    npc1.current_scene = scene.name
    session.init_new_session(
        scene=scene,
        player_characters=[ch1],
        npcs=[npc1],
        npc_logger=npc_logger,
        player_logger=player_logger
    )

    # Save the newly created session
    session.save_session(save_file_path)

    # Initialize the turn queue with all characters
    session._initialize_turn_queue()

session.start_game_loop_simple()
print(session.get_session_context())