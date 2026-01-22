from typing import List
import uuid
from game.event_pool import EventPool
from npcs.npc import NPC
from schemas.in_game import Character, GameModes, NPCCharacter, SceneNode
from skls_embeddings import ChromaClient
from skls_generator import Generator
from logging import Logger
from schemas.orchestration import CharacterToUserBinding, Event, EventList, Message
import json
from schemas.save_game import SaveGameData

class Session:
    def __init__(self, 
                 session_name, 
                 chroma_client : ChromaClient, 
                 logger : Logger,
                 generator : Generator, 
                 event_pool : EventPool,
                 ) -> None:
        self.session_name = session_name
        self.generator = generator
        self.chroma_client = chroma_client
        self.logger = logger
        self.event_pool = event_pool
        self.collection_name = f"game_session_{session_name}"
        self.player_characters : List[Character] = []
        self.npcs : List[NPC] = []
        self.current_scene : SceneNode = None # type: ignore
        self.game_mode : GameModes = GameModes.STORY
        self.character_bindings : List[CharacterToUserBinding] = []
        self.messages : List[Message] = []
        
    
    def _init_npc(self, npc_character : NPCCharacter):
        """Initialize an NPC in the session."""
        new_NPC = NPC(
            character=npc_character,
            event_queuee=self.event_pool.subscribe(uuid.uuid4().hex),
            logger=self.logger,
            generator=self.generator
        )
        # Start continuous processing for the NPC
        new_NPC.start_continuous_processing()
        self.logger.debug(f"Initialized NPC: {npc_character.name}")
        return new_NPC
    
    def save_session(self, filename: str):
        """Saves session data to a JSON file."""
        save_data = SaveGameData(
            player_characters=self.player_characters,
            npcs=[n.character for n in self.npcs],
            current_scene=self.current_scene
        ).dict()
        with open(filename, 'w') as f:
            json.dump(save_data, f, indent=4)
        self.logger.info(f"Session saved to {filename}")

    def get_session_context(self, include_json_details: bool = False) -> str:
        """
        Generates a text representation of the current session state 
        optimized for LLM consumption.
        """
        # 1. Format Scene Info
        scene_info = "Unknown"
        if self.current_scene:
            # Assuming SceneNode has 'name' and 'description' attributes
            scene_info = f"Location: {getattr(self.current_scene, 'name', 'Unknown')}\n"
            scene_info += f"Description: {getattr(self.current_scene, 'description', 'No description available.')}"
            scene_info += f"Game mode: {self.game_mode.value}"

        # 2. Format Characters (Helper function)
        def format_char_list(chars: List[Character] | List[NPCCharacter]) -> str:
            if not chars:
                return "None"
            
            summary = ""
            for char in chars:
                # We assume Character is a Pydantic model
                # We extract key fields to save tokens, rather than dumping the whole JSON
                char_data = char.dict() if hasattr(char, 'dict') else char.__dict__
                
                name = char_data.get('name', 'Unnamed')
                race = char_data.get('race', 'Unknown Race')
                c_class = char_data.get('class_name', 'Unknown Class')
                hp = f"{char_data.get('current_hp', '?')}/{char_data.get('max_hp', '?')}"
                status = char_data.get('status_effects', [])
                
                summary += f"- {name} ({race} {c_class}) | HP: {hp} | Status: {status}\n"
                
                # If specifically requested, dump the full raw data for the LLM (uses more tokens)
                if include_json_details:
                    summary += f"  > Raw Data: {json.dumps(char_data)}\n"
            return summary

        # 3. Construct the Context String
        context_str = f"""
### CURRENT SESSION STATE: {self.session_name}

#### 1. CURRENT SCENE
{scene_info}

#### 2. PLAYER CHARACTERS (PCs)
{format_char_list(self.player_characters)}

#### 3. NON-PLAYER CHARACTERS (NPCs)
{format_char_list([n.character for n in self.npcs])}
"""
        return context_str.strip()
    
    def init_new_session(self,
                         scene : SceneNode,
                         player_characters : List[Character] = [],
                         ):
        '''
        Initialize a new game session with player characters and NPCs.
        '''
        self.player_characters = player_characters
        self.npcs = []
        self.current_scene = scene
        self.logger.info(f"Initialized session '{self.session_name}' with {len(player_characters)} PCs")
        """Perform an external action within the game session. (players moves)"""
        return []

    def external_privileged_action(self, prompt: str = ""):
        """Perform a privileged external action within the game session. (DM moves)"""
        
        rules = f"""
        1. Determine which objects involved into the request.
        2. Be the most specific (if there is a certain object in the scene you should set event type to item-based not the entire scene)
        """
        prompt_text = f"""
        You need to generate authoritative events based on the situation and a request e g "The dragon gets 1d8+2 damage. (based on items properties)" or "character 1 hits character 2 with a sword"
        # rules:
        {rules}
        # prompt 
        {prompt}
        # scene:
        {self.get_session_context()}
        """
        events = self.generator.generate_one_shot(
            pydantic_model=EventList,
            prompt=prompt_text
        )
        return events.event_list

    def sort_npcs_by_initiative(self):
        """Sort NPCs based on their initiative scores."""
        self.npcs.sort(key=lambda npc: npc.character.initiative_bonus, reverse=True)
        self.logger.debug("Sorted NPCs by initiative.")

    def load_session_from_save(self, filename: str):
        """Loads session data from a JSON file."""
        try:
            with open(filename, 'r') as f:
                save_data = json.load(f)
            loaded_data = SaveGameData(**save_data)
            self.player_characters = loaded_data.player_characters
            
            npcs = []
            for n in loaded_data.npcs:
                npc = self._init_npc(n)
                npcs.append(npc)
            self.npcs = npcs
            self.current_scene = loaded_data.current_scene
            self.logger.info(f"Session loaded from {filename}")
        except FileNotFoundError:
            self.logger.error(f"Save file not found: {filename}")
        except Exception as e:
            self.logger.error(f"Error loading session: {e}")


