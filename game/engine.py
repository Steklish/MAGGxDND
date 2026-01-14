from typing import List
from schemas.in_game import Character, SceneNode
from skls_embeddings import ChromaClient
from logging import Logger
from schemas.orchestration import Event

class Session:
    def __init__(self, 
                 session_name, 
                 chroma_client : ChromaClient, 
                 logger : Logger
                 ) -> None:
        self.session_name = session_name
        self.chroma_client = chroma_client
        self.logger = logger
        self.collection_name = f"game_session_{session_name}"
        self.chroma_client.get_or_create_collection(self.collection_name)
    
    def load_session_from_save(self):
        pass
    
    def init_new_session(self, 
                         player_characters : List[Character], 
                         npcs : List[Character], 
                         scene : SceneNode 
                         ):
        '''
        Initialize a new game session with player characters and NPCs.
        '''
        self.player_characters = player_characters
        self.npcs = npcs
        self.current_scene = scene
        self.logger.info(f"Initialized session '{self.session_name}' with {len(player_characters)} PCs and {len(npcs)} NPCs.")
        
    def external_action(self)  -> List[Event]:
        """Perform an external action within the game session. (players moves)"""
        return []
    
    def external_privileged_action(self):
        """Perform a privileged external action within the game session. (DM moves)"""
        return []
    
    def sort_npcs_by_initiative(self):
        """Sort NPCs based on their initiative scores."""
        self.npcs.sort(key=lambda npc: npc.initiative_bonus, reverse=True)
        self.logger.debug("Sorted NPCs by initiative.")
        