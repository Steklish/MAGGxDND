import heapq
import time
import threading
from typing import TYPE_CHECKING, List, Optional, Union
import uuid
from game.event_pool import EventPool

if TYPE_CHECKING:
    from game.manipulator import Manipulator
    from magg.magg import Magg  # Moved to TYPE_CHECKING to avoid runtime import
    from game.orchestrator import Orchestrator
    
from npcs.npc import NPC
from player.player import Player
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
        self.players : List[Player] = []
        self.npcs : List[NPC] = []
        self.current_scene : SceneNode = None # type: ignore
        self.game_mode : GameModes = GameModes.STORY
        self.character_bindings : List[CharacterToUserBinding] = []
        self.messages : List[Message] = []
        self.tick_time_seconds = 0.1  # Time between each game tick
        self.game_master = None  # Will be initialized later to avoid circular import
        # Game loop attributes
        self._game_loop_running = False
        self._game_loop_thread = None

        # Turn-based system attributes
        self.turn_queue = []  # Priority queue (min-heap) for turn order
        self.next_turn_time = 0.0  # Global time tracker
        self.turn_distance = 100.0  # Distance for turn calculation (constant)

    def _init_orchestrator(self, orchestrator : 'Orchestrator'):
        self.orchestrator = orchestrator

    def _initialize_game_master(self):
        """Initialize the game master (MAGG) after avoiding circular import issues."""
        if self.game_master is None:
            from magg.magg import Magg
            self.game_master = Magg(
                generator=self.generator,
                archive=None,
                logger=self.logger,
                event_queue=self.event_pool.subscribe("magg")
            )
        
    def inject_manipulator(self, manipulator : 'Manipulator'):
        self.manipulator = manipulator

    
    def _init_npc(self, npc_character : NPCCharacter):
        """Initialize an NPC in the session."""
        new_NPC = NPC(
            character=npc_character,
            event_queuee=self.event_pool.subscribe(uuid.uuid4().hex),
            logger=self.logger,
            generator=self.generator
        )
        self.logger.debug(f"Initialized NPC: {npc_character.name}")
        return new_NPC

    def _init_player(self, character: Character, orchestrator: 'Orchestrator'):
        """Initialize a Player in the session."""
        new_player = Player(
            character=character,
            logger=self.logger,
            orchestrator=orchestrator
        )
        self.logger.debug(f"Initialized Player: {character.name}")
        return new_player
    
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
                         npcs : List[NPCCharacter] = []
                         ):
        '''
        Initialize a new game session with player characters and NPCs.
        '''
        self.player_characters = player_characters
        # Initialize Player objects for each character
        self.players = []
        for character in player_characters:
            player = self._init_player(character, self.orchestrator)
            self.players.append(player)
    
        self.npcs = []
        for n in npcs:
            npc = self._init_npc(n)
            self.npcs.append(npc)
        self.current_scene = scene
        self._initialize_game_master()  # Initialize game master after avoiding circular import
        self.initialize_turn_queue()  # Initialize the turn queue for the new session
        self.logger.info(f"Initialized session '{self.session_name}' with {len(player_characters)} PCs")
        """Perform an external action within the game session. (players moves)"""
        return []

    def execute_events(self, event_list : list[Event]):
        """Process an event through the session's manipulator."""
        for event in event_list:
            self.manipulator.manage(event)

    def process_characters_in_order_once(self):
        """Process all characters (NPCs and Players) in initiative order once, used in story mode."""
        # Sort NPCs by initiative
        self._sort_npcs_by_initiative()

        # Process NPCs
        for npc in self.npcs:
            decision = npc.run(self.get_session_context())
            if decision:
                events = self._external_action(decision, actor=npc.character.name)
                self.execute_events(events)

        # Process Players (though they typically wait for user input)
        for player in self.players:
            decision = player.run()
            if decision:
                events = self._external_action(decision, actor=player.character.name)
                self.execute_events(events)
        


    def _external_action(self, prompt: str = "", actor : str | None = None) -> List[Event]:
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
        {f"## actor: {actor}\nrequest: " if actor else ""}
        {prompt}
        # scene:
        {self.get_session_context()}
        """
        events = self.generator.generate_one_shot(
            pydantic_model=EventList,
            prompt=prompt_text
        )
        return events.event_list

    def _sort_npcs_by_initiative(self):
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

            # Initialize Player objects for each character
            self.players = []
            for character in loaded_data.player_characters:
                player = self._init_player(character, self.orchestrator)
                self.players.append(player)

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

    def _calculate_next_turn_time(self, initiative: int) -> float:
        """Calculate the next turn time for a character based on their initiative.

        The formula is: current_time + (distance / speed)
        Where speed is the initiative value.
        Higher initiative means faster turn arrival.
        """
        if initiative <= 0:
            initiative = 1  # Prevent division by zero

        time_to_next_turn = self.turn_distance / initiative
        return self.next_turn_time + time_to_next_turn

    def _add_character_to_turn_queue(self, character: Union[Character, NPCCharacter], obj: Union[Character, NPC, Player], is_npc: bool):
        """Add a character to the turn queue with their calculated next turn time."""
        initiative = character.initiative_bonus
        next_turn_time = self._calculate_next_turn_time(initiative)

        # Push to heap: (next_turn_time, is_npc, character_id, character_object)
        heapq.heappush(self.turn_queue, (next_turn_time, is_npc, character.name, obj))

    def initialize_turn_queue(self):
        """Initialize the turn queue with all characters (both PCs and NPCs)."""
        self.turn_queue = []
        self.next_turn_time = 0.0

        # Add player characters to the turn queue
        for i, player in enumerate(self.players):
            self._add_character_to_turn_queue(player.character, player, False)

        # Add NPCs to the turn queue
        for npc in self.npcs:
            self._add_character_to_turn_queue(npc.character, npc, True)

        self.logger.debug(f"Initialized turn queue with {len(self.players)} PCs and {len(self.npcs)} NPCs")

    def get_next_character_turn(self) -> tuple:
        """Get the next character whose turn it is, based on initiative.

        Returns:
            tuple: (character_object, is_npc_boolean, next_turn_time)
        """
        if not self.turn_queue:
            self.initialize_turn_queue()
            if not self.turn_queue:
                return None, False, 0.0

        # Pop the character with the earliest next turn time
        next_turn_time, is_npc, character_name, character_obj = heapq.heappop(self.turn_queue)

        # Update global time to this character's turn time
        self.next_turn_time = next_turn_time

        # Calculate and add this character back to the queue for their next turn
        # Both NPCs and Players store their character in the .character attribute
        initiative = character_obj.character.initiative_bonus
        next_next_turn_time = self._calculate_next_turn_time(initiative)
        heapq.heappush(self.turn_queue, (next_next_turn_time, is_npc, character_name, character_obj))

        return character_obj, is_npc, next_turn_time

    def process_next_character_turn(self):
        """Process the next character's turn in the turn queue."""
        if self.game_mode != GameModes.COMBAT:
            # In story mode, just process all characters in initiative order once
            self.process_characters_in_order_once()
            return

        character_obj, is_npc, turn_time = self.get_next_character_turn()

        if character_obj is None:
            return

        if is_npc:
            # Process NPC turn
            decision = character_obj.run(self.get_session_context())
            if decision:
                events = self._external_action(decision, actor=character_obj.character.name)
                self.execute_events(events)
        else:
            # Process Player turn
            decision = character_obj.run(self.get_session_context())
            if decision:
                # Player decisions would typically be processed differently
                # For now, we'll treat them similarly to NPC actions
                events = self._external_action(decision, actor=character_obj.character.name)
                self.execute_events(events)
            else:
                # For player characters, we might want to notify that it's their turn
                # This could trigger UI updates or notifications to players
                self.logger.debug(f"It's {character_obj.character.name}'s turn (PC)")
                # In a real implementation, this would wait for player input
                # For now, we'll just log it

    def start_game_loop_simple(self):
        while True:
            try:
                self.initialize_turn_queue()
                character : Player | NPC
                character, is_npc, time = self.get_next_character_turn()
                if character:
                    self.logger.info(f"Next turn: {character.character.name} (NPC: {is_npc}) at time {time}")
                decision = character.run(context=self.get_session_context())
                if decision:
                    events = self._external_action(decision, actor=character.character.name)
                    self.execute_events(events)
            except KeyboardInterrupt:
                self.logger.info("Game loop interrupted by user.")
                break