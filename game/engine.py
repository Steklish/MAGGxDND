from typing import List
from schemas.in_game import Character, SceneNode
from skls_embeddings import ChromaClient
from skls_generator import Generator
from logging import Logger
from schemas.orchestration import Event, EventList
import json
from schemas.save_game import SaveGameData

class Session:
    def __init__(self, 
                 session_name, 
                 chroma_client : ChromaClient, 
                 logger : Logger,
                 generator : Generator
                 ) -> None:
        self.session_name = session_name
        self.generator = generator
        self.chroma_client = chroma_client
        self.logger = logger
        self.collection_name = f"game_session_{session_name}"
        self.player_characters : List[Character] = []
        self.npcs : List[Character] = []
        self.current_scene : SceneNode = None # type: ignore
    
    def save_session(self, filename: str):
        """Saves session data to a JSON file."""
        save_data = SaveGameData(
            player_characters=self.player_characters,
            npcs=self.npcs,
            current_scene=self.current_scene
        ).dict()
        with open(filename, 'w') as f:
            json.dump(save_data, f, indent=4)
        self.logger.info(f"Session saved to {filename}")

    def init_new_session(self,
                         scene : SceneNode,
                         player_characters : List[Character] = [],
                         npcs : List[Character] = []
                         ):
        '''
        Initialize a new game session with player characters and NPCs.
        '''
        self.player_characters = player_characters
        self.npcs = npcs
        self.current_scene = scene
        self.logger.info(f"Initialized session '{self.session_name}' with {len(player_characters)} PCs and {len(npcs)} NPCs.")
        """Perform an external action within the game session. (players moves)"""
        return []

    def external_privileged_action(self, prompt: str = ""):
        """Perform a privileged external action within the game session. (DM moves)"""
        
        prompt = f"""
        YOu need to generate authoritative events e g "The dragon gets 1d8+2 damage." or "character 1 hits character 2 with a sword"
        """
        events = self.generator.generate_one_shot(
            pydantic_model=EventList,
            prompt=prompt
        )
        return events.event_list

    def sort_npcs_by_initiative(self):
        """Sort NPCs based on their initiative scores."""
        self.npcs.sort(key=lambda npc: npc.initiative_bonus, reverse=True)
        self.logger.debug("Sorted NPCs by initiative.")

    def load_session_from_save(self, filename: str):
        """Loads session data from a JSON file."""
        try:
            with open(filename, 'r') as f:
                save_data = json.load(f)
            loaded_data = SaveGameData(**save_data)
            self.player_characters = loaded_data.player_characters
            self.npcs = loaded_data.npcs
            self.current_scene = loaded_data.current_scene
            self.logger.info(f"Session loaded from {filename}")
        except FileNotFoundError:
            self.logger.error(f"Save file not found: {filename}")
        except Exception as e:
            self.logger.error(f"Error loading session: {e}")


