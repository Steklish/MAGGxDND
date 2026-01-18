import unittest
import json
import sys
sys.path.append('D:\\Duty\\MAGGxDND')
from game.engine import Session
from game.manipulator import Manipulator
from schemas.in_game import Character, SceneNode, Item
#from skls_core.generator import Generator
#from skls_core.google_gen_ai import GoogleGenAI
from skls_embeddings import ChromaClient
from unittest.mock import MagicMock


class TestObjectTransfer(unittest.TestCase):
    def setUp(self):
        # Initialize necessary components for testing
        self.logger = MagicMock()
        #self.generator = Generator(GoogleGenAI(api_key = "test"), logger_instance=self.logger) # Replace None with actual generator if needed
        self.generator = MagicMock()
        self.chroma_client = MagicMock()#ChromaClient(None, logger_instance=self.logger) # Replace None with actual embedding client if needed
        self.session = Session("test_session", self.chroma_client, self.logger)
        self.archive = None #Not used, so left as None
        self.manipulator = Manipulator(self.generator, self.session, self.archive, self.logger)

        # Create a sample scene and characters for testing
        self.scene = SceneNode(name="test_scene", description="A test scene", objects=[])
        self.player = Character(name="test_player", description="A test player", inventory=[], char_class = "Fighter", max_hp = 10, current_hp = 10, abilities = {})
        self.session.init_new_session([self.player], [], self.scene)

    def test_object_transfer_from_scene_to_inventory(self):
        # Create a sample object
        item = Item(name="test_item", description="A test item")
        self.scene.objects.append(item)

        # Define the transfer details
        transfer_details = {
            "object": "test_item",
            "source": "scene",
            "destination": "test_player"
        }
        transfer_details_json = json.dumps(transfer_details)

        # Execute the object transfer manipulation
        self.manipulator.execute_manipulation("ObjectTransferManipulation", transfer_details_json)

        # Assert that the object is now in the player's inventory
        self.assertIn(item, self.player.inventory)

        # Assert that the object is no longer in the scene
        self.assertNotIn(item, self.scene.objects)

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
