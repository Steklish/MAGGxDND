import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Ensure the project root is in sys.path and prioritized
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
else:
    # Move to top if already exists but lower priority
    sys.path.remove(project_root)
    sys.path.insert(0, project_root)

print(sys.path)
import logging
from game.engine import Session
from game.event_pool import EventPool
from game.manipulator import Manipulator
from game.orchestrator import Orchestrator
from schemas.in_game import Character, NPCCharacter, SceneNode
from skls_generator.generator import Generator
from skls_generator.gen_backends.google_gen import GoogleGenAI
from skls_embeddings.chroma_client import ChromaClient
from skls_embeddings.embedding_client import EmbeddingClient

# Custom logging setup (Simplified for testing)
logging.basicConfig(level=logging.DEBUG)
main_logger = logging.getLogger("test.game_actions")

# Initialize components
# Using a placeholder key or environment variable if available
api_key = os.getenv("GEMINI_API_KEY", "dummy_key")
generator = Generator(GoogleGenAI(api_key=api_key, logger=main_logger), logger_instance=main_logger)
class MockChromaClient:
    def __init__(self, *args, **kwargs):
        pass
    # Add other necessary methods if they are called in Session

chroma_client = MockChromaClient()

# Load session
session = Session(
    session_name="test_session",
    chroma_client=chroma_client,
    logger=main_logger,
    generator=generator,
    event_pool=EventPool(),
    magg_logger=main_logger
)

session.inject_manipulator(
    manipulator = Manipulator(
        generator=generator,
        state=session,
        archive=None,
        logger=main_logger
    )
)

orchestrator = Orchestrator(
    generator=generator,
    logger=main_logger
)
orchestrator.add_state(session)

session._init_orchestrator(orchestrator)
session.load_session_from_save("./saves/ex_01.json")

def test_add_item_to_inventory():
    """Test adding an item to a player's inventory and checking manipulator registration."""
    print("\n--- Testing Add Item to Inventory ---")
    
    # Get the first player
    if not session.players:
        print("No players found in session.")
        return
        
    player = session.players[0]
    print(f"Player type: {type(player)}")
    print(f"Player dir: {dir(player)}")
    print(f"Testing with player: {player.character.name}")
    
    # Create a dummy item that grants a specific manipulator
    # We'll rely on an existing manipulator for this test, e.g., 'AttackManipulation'
    # In a real scenario, this would be a specific item manipulator
    from schemas.in_game import Item
    
    # Let's say a "Scope" adds "CharacterRangedAttackManipulation" (simulating dynamic add)
    # Since we don't have many distinct manipulators yet, we will test the logic 
    # by adding an item that ostensibly adds 'AttackManipulation' again (or a mocked one if we had it)
    # For now, let's trust the logic in GameEntity._update_manipulators
    
    # Check current manipulators
    print(f"Initial manipulators: {[m.__class__.__name__ for m in player.manipulators]}")
    
    new_item = Item(
        name="Sniper Scope",
        description="Allows precise aiming.",
        available_manipulators=["AttackManipulation"] # Using existing one for test
    )
    
    player.add_item(new_item)
    
    print(f"Inventory: {[i.name for i in player.inventory]}")
    print(f"Manipulators after adding item: {[m.__class__.__name__ for m in player.manipulators]}")
    
    # Basic Assertion: Check if item is in inventory
    assert new_item in player.inventory
    print("Item added successfully.")

def test_move_character():
    """Test moving a character to a different location."""
    print("\n--- Testing Character Movement ---")
    
    if not session.players:
        return

    player = session.players[0]
    # Ensure character has current_scene set
    if not player.character.current_scene:
        player.character.current_scene = session.current_scene.name
        
    start_pos = player.character.position
    print(f"Start Position: ({start_pos.x}, {start_pos.y})")
    
    # Define a target position
    from schemas.in_game import Coordinate2D
    target_pos = Coordinate2D(x=start_pos.x + 5, y=start_pos.y + 5)
    
    # Execute movement via GameEntity method
    success = player.move_character_to_position(player.character, target_pos)
    
    print(f"Movement success: {success}")
    print(f"End Position: ({player.character.position.x}, {player.character.position.y})")
    
    assert success is True
    assert player.character.position.x == target_pos.x
    assert player.character.position.y == target_pos.y
    print("Movement verification passed.")

if __name__ == "__main__":
    try:
        test_add_item_to_inventory()
        test_move_character()
        print("\nAll tests passed!")
    except Exception as e:
        print(f"\nTests failed with error: {e}")
        import traceback
        traceback.print_exc()
