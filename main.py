import json
import os
from game.engine import Session
from game.event_pool import EventPool
from game.manipulator import Manipulator
from schemas.in_game import Character, SceneNode
from skls_generator.generator import Generator
from skls_generator.gen_backends.google_gen import GoogleGenAI
from skls_core.logging import get_skls_logger
from skls_embeddings.chroma_client import ChromaClient
from skls_embeddings.embedding_client import EmbeddingClient


logger = get_skls_logger(__name__)
logger.setLevel("DEBUG")
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
manipulator = Manipulator(
    generator=generator,
    state=session,
    archive=None,
    logger=logger
)

# -- LOAD OR INIT GAME STATE --

# scene = generator.generate_one_shot(
#     pydantic_model=SceneNode,
#     prompt="A dark and eerie forest clearing at night, with twisted trees and a faint mist."
# )

ch1 = generator.generate_one_shot(
    pydantic_model=Character,
    prompt="A wizard named Ogorek."
)
# print(json.dumps(scene.dict(), indent=2))

# session.init_new_session(
#     scene=scene,
#     player_characters=[ch1]
# )
# session.save_session("./saves/example_save_02.json")
session.load_session_from_save("./saves/example_save_02.json")
events = session.external_privileged_action("Reginald gives his sword to Ogorek")
print(events)
for e in events:
    manipulator.manage(e)

# print(json.dumps(session.player_characters[0].dict(), indent=2))