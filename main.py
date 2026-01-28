import json
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from game.engine import Session
from game.event_pool import EventPool
from game.manipulator import Manipulator
from game.orchestrator import Orchestrator
from schemas.in_game import Character, NPCCharacter, SceneNode
from skls_generator.generator import Generator
from skls_generator.gen_backends.google_gen import GoogleGenAI
from skls_embeddings.chroma_client import ChromaClient
from skls_embeddings.embedding_client import EmbeddingClient


# Custom logging setup to handle Unicode characters
def setup_unicode_logging(log_file_path: str = './log/application.log'):
    """Setup logging with Unicode support."""
    # Create log directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                 datefmt='%Y-%m-%d %H:%M:%S')

    # Create file handler with UTF-8 encoding
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'  # Explicitly set UTF-8 encoding
    )
    file_handler.setFormatter(formatter)

    # Create console handler with proper encoding for Windows
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


os.makedirs('log', exist_ok=True)
setup_unicode_logging('./log/application.log')

# Create specific named loggers for different components while preserving global configuration
main_logger = logging.getLogger("game.main")
engine_logger = logging.getLogger("game.engine")
manipulator_logger = logging.getLogger("game.manipulator")
orchestrator_logger = logging.getLogger("game.orchestrator")
magg_logger = logging.getLogger("magg.core")
npc_logger = logging.getLogger("npc.core")
player_logger = logging.getLogger("player.core")

# Set log levels for different components
main_logger.setLevel("DEBUG")
engine_logger.setLevel("DEBUG")
manipulator_logger.setLevel("DEBUG")
orchestrator_logger.setLevel("DEBUG")
magg_logger.setLevel("DEBUG")
npc_logger.setLevel("DEBUG")
player_logger.setLevel("DEBUG")

generator = Generator(GoogleGenAI(api_key=os.getenv("GEMINI_API_KEY"), logger=main_logger), logger_instance=main_logger)
chroma_client = ChromaClient(EmbeddingClient(), logger_instance=main_logger)


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

scene = generator.generate_one_shot(
    pydantic_model=SceneNode,
    prompt="A dark and eerie forest clearing at night, with twisted trees and a faint mist."
)

ch1 = generator.generate_one_shot(
    pydantic_model=Character,
    prompt="A wizard named Ogorek."
)

npc1 = generator.generate_one_shot(
    pydantic_model=NPCCharacter,
    prompt="An evil ork warrior."
)
# print(json.dumps(scene.dict(), indent=2))

npc1.current_scene = scene.name
session.init_new_session(
    scene=scene,
    player_characters=[ch1],
    npcs=[npc1],
    npc_logger=npc_logger,
    player_logger=player_logger
)
# session.save_session("./saves/ex_01.json")
# session.load_session_from_save("./saves/ex_01.json")
session.start_game_loop_simple()
print(session.get_session_context())