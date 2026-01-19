import json
import os
from game.engine import Session
from schemas.in_game import Character, SceneNode
from skls_generator.generator import Generator
from skls_generator.gen_backends.google_gen import GoogleGenAI
from skls_core.logging import get_skls_logger
from skls_embeddings.chroma_client import ChromaClient
from skls_embeddings.embedding_client import EmbeddingClient

logger = get_skls_logger(__name__)
generator = Generator(GoogleGenAI(os.getenv("GEMINI_API_KEY")), logger_instance=logger)
chroma_client = ChromaClient(EmbeddingClient(), logger_instance=logger)

session = Session(
    session_name="example_session",
    chroma_client=chroma_client,
    logger=logger
)

# scene = generator.generate_one_shot(
#     pydantic_model=SceneNode,
#     prompt="A dark and eerie forest clearing at night, with twisted trees and a faint mist."
# )

# ch1 = generator.generate_one_shot(
#     pydantic_model=Character,
#     prompt="A brave knight in shining armor, wielding a longsword and shield."
# )
# print(json.dumps(scene.dict(), indent=2))

# session.init_new_session(
#     scene=scene,
#     player_characters=[ch1]
# )

# session.save_session("example_save.json")

session.load_session_from_save("example_save.json")
session.external_privileged_action("Sir Reginald gets 1d4 damage")