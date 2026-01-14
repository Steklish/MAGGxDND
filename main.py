import os
from game.engine import Session
from magg.magg import Magg
from skls_generator.generator import Generator
from skls_generator.gen_backends.google_gen import GoogleGenAI
from skls_core.logging import get_skls_logger
from skls_embeddings.chroma_client import ChromaClient
from skls_embeddings.embedding_client import EmbeddingClient

logger = get_skls_logger(__name__)
generator = Generator(GoogleGenAI(os.getenv("GEMINI_API_KEY")), logger_instance=logger)
chroma_client = ChromaClient(EmbeddingClient(), logger_instance=logger)

session = Session()

magg = Magg(
    instructions_filename="./agents/DM_personality.md",
    chroma_client=chroma_client,
    generator=generator,
    game_state=session
    )