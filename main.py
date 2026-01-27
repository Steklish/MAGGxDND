import json
import os
from game.engine import Session
from game.event_pool import EventPool
from game.manipulator import Manipulator
from game.orchestrator import Orchestrator
from schemas.in_game import Character, NPCCharacter, SceneNode
from skls_core import SKLSLoggerConfig
from skls_generator.generator import Generator
from skls_generator.gen_backends.google_gen import GoogleGenAI
from skls_core.logging import get_skls_logger
from skls_embeddings.chroma_client import ChromaClient
from skls_embeddings.embedding_client import EmbeddingClient


os.makedirs('log', exist_ok=True)
logger = get_skls_logger(__name__)
logger.setLevel("DEBUG")
SKLSLoggerConfig.setup_logging(log_file='./log/application.log')

generator = Generator(GoogleGenAI(os.getenv("GEMINI_API_KEY")), logger_instance=logger)
chroma_client = ChromaClient(EmbeddingClient(), logger_instance=logger)


# -- INIT SESSION AND MANIPULATOR --

session = Session(
    session_name="example_session",
    chroma_client=chroma_client,
    logger=logger,
    generator=generator,
    event_pool=EventPool()
)

session.inject_manipulator(
    manipulator = Manipulator(
        generator=generator,
        state=session,
        archive=None,
        logger=logger
    )
)

orchestrator = Orchestrator(
    generator=generator,
    logger=logger
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
    npcs=[npc1]
)
# session.save_session("./saves/ex_01.json")
# session.load_session_from_save("./saves/ex_01.json")
session.start_game_loop_simple()
# print(json.dumps(session.player_characters[0].dict(), indent=2))