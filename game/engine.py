import heapq
import time
import threading
import math
from typing import TYPE_CHECKING, List, Optional, Union, Dict, Set
import uuid
from game.event_pool import EventPool
from magg.magg import Magg
if TYPE_CHECKING:
    from game.manipulator import Manipulator
    from game.orchestrator import Orchestrator

from npcs.npc import NPC
from player.player import Player
from schemas.in_game import Character, GameModes, NPCCharacter, SceneNode, Coordinate3D
from skls_embeddings import ChromaClient
from skls_generator import Generator
from logging import Logger
from schemas.orchestration import CharacterToUserBinding, Event, EventList, Message, EventTypes, OrchestrationVerdictType
from schemas.orchestration import SpatialMovementCommand, SpatialTeleportCommand, DistanceCalculationRequest
import json
from schemas.save_game import SaveGameData

MAX_MESSAGES_STORED = 20

class Session:
    def __init__(self,
                 session_name,
                 chroma_client : ChromaClient,
                 logger : Logger,
                 generator : Generator,
                 event_pool : EventPool,
                 magg_logger : Logger
                 ) -> None:
        self.session_name = session_name
        self.generator = generator
        self.chroma_client = chroma_client
        self.logger = logger
        self.event_pool = event_pool
        self.collection_name = f"game_session_{session_name}"
        self.players : List[Player] = []
        self.npcs : List[NPC] = []
        self.current_scene : SceneNode = None # type: ignore
        self.game_mode : GameModes = GameModes.STORY
        self.character_bindings : List[CharacterToUserBinding] = []
        self.messages : List[Message] = []
        self.tick_time_seconds = 0.1  # Time between each game tick
        self._game_master = None  # Will be initialized later to avoid circular import
        # Game loop attributes
        self._game_loop_running = False
        self._game_loop_thread = None
        self._init_mage(magg_logger)  # Initialize game master after avoiding circular import
        # Turn-based system attributes
        self.turn_queue = []  # Priority queue (min-heap) for turn order
        self.next_turn_time = 0.0  # Global time tracker
        self.turn_distance = 100.0  # Distance for turn calculation (constant)

        # Spatial system attributes
        self.spatial_enabled = True  # Flag to enable/disable spatial features

        # Location graph attributes
        self.location_graph: Dict[str, Set[str]] = {}  # Graph of connected locations
        self.all_locations: Dict[str, SceneNode] = {}  # Store all visited/known locations
        self.current_location_name: Optional[str] = None  # Track current location name
        self._orchestrator : 'Orchestrator | None'  # Will be set later


    @property
    def game_master(self) -> 'Magg':
        if self._game_master is None:
            raise ValueError("Mage not initialized!")
        return self._game_master


    @property
    def orchestrator(self) -> 'Orchestrator':
        if self._orchestrator is None:
            raise ValueError("Orchestrator not initialized!")
        return self._orchestrator
        
    def _init_orchestrator(self, orchestrator : 'Orchestrator'):
        self._orchestrator = orchestrator


    def _init_mage(self, magg_logger=None):
        """Initialize the game master (MAGG) after avoiding circular import issues."""
        if self._game_master is None:
            # Use provided MAGG logger if available, otherwise use session logger
            logger_to_use = magg_logger if magg_logger else self.logger
            self._game_master = Magg(
                generator=self.generator,
                archive=None,
                logger=logger_to_use,
                event_queue=self.event_pool.subscribe("magg")
            )
            self.game_master.inject_state(self)
        
    def inject_manipulator(self, manipulator : 'Manipulator'):
        self.manipulator = manipulator

    
    def _init_npc(self, npc_character : NPCCharacter, npc_logger=None):
        """Initialize an NPC in the session."""
        # Use provided NPC logger if available, otherwise use session logger
        logger_to_use = npc_logger if npc_logger else self.logger
        new_NPC = NPC(
            character=npc_character,
            event_queuee=self.event_pool.subscribe(uuid.uuid4().hex),
            logger=logger_to_use,
            generator=self.generator
        )
        new_NPC.inject_state(self)
        logger_to_use.debug(f"Initialized NPC: {npc_character.name}")
        return new_NPC

    def _init_player(self, character: Character, orchestrator: 'Orchestrator', player_logger=None):
        """Initialize a Player in the session."""
        # Use provided Player logger if available, otherwise use session logger
        logger_to_use = player_logger if player_logger else self.logger
        new_player = Player(
            character=character,
            logger=logger_to_use,
            orchestrator=orchestrator
        )
        new_player.inject_state(self)
        logger_to_use.debug(f"Initialized Player: {character.name}")
        return new_player
    
    def save_session(self, filename: str):
        """Saves session data to a JSON file."""
        # Prepare data for serialization
        save_dict = {
            "game_mode": self.game_mode.value,
            "player_characters": [char.character.dict() for char in self.players],
            "npcs": [npc.character.dict() for npc in self.npcs],
            "current_scene": self.current_scene.dict(),
            # Location graph data - convert sets to lists for JSON
            "location_graph": {k: list(v) for k, v in self.location_graph.items()},
            "all_locations": {name: scene.dict() for name, scene in self.all_locations.items()},
            "current_location_name": self.current_location_name,
            "messages": [msg.dict() for msg in self.messages]
        }

        with open(filename, 'w') as f:
            json.dump(save_dict, f, indent=4)
        self.logger.info(f"Session saved to {filename}")

    def get_session_context(self) -> str:
        """
        Generates a text representation of the current session state
        optimized for LLM consumption.
        """
        # 1. Format Scene Info
        scene_info = ""
        if self.current_scene:
            # Assuming SceneNode has 'name' and 'description' attributes
            scene_info = f"Location: {getattr(self.current_scene, 'name', 'Unknown')}\n"
            scene_info += f"Description: {getattr(self.current_scene, 'description', 'No description available.')}"
            scene_info += f"Game mode: {self.game_mode.value}"
            # Add spatial information
            scene_info += f"\nScene center: ({self.current_scene.center_position.x}, {self.current_scene.center_position.y}, {self.current_scene.center_position.z})"
            scene_info += f"\nScene dimensions: {self.current_scene.dimensions.x}x{self.current_scene.dimensions.y}x{self.current_scene.dimensions.z} {self.current_scene.scale_unit}"

            # Add location graph information
            if self.current_location_name:
                connected_locs = self.get_connected_locations(self.current_location_name)
                if connected_locs:
                    scene_info += f"\nConnected locations: {', '.join(connected_locs)}"
                else:
                    scene_info += f"\nConnected locations: None"
        else:
            scene_info += "\nNo current scene loaded."

        # Add all known locations to the context
        all_locations = self.get_all_locations()
        if all_locations:
            scene_info += f"\nAll known locations: {', '.join(all_locations)}"

        # 3. Construct the Context String
        context_str = f"""
### CURRENT SESSION STATE:

#### 1. CURRENT SCENE
{scene_info}

#### 2. PLAYER CHARACTERS (PCs)
{[c.character.short_summary for c in self.players]}

#### 3. NON-PLAYER CHARACTERS (NPCs)
{[n.character.short_summary if n.character.current_scene == self.current_location_name else None for n in self.npcs]}
"""
        return context_str.strip()
    
    def init_new_session(self,
                         scene : SceneNode,
                         player_characters : List[Character] = [],
                         npcs : List[NPCCharacter] = [],
                         npc_logger=None,
                         player_logger=None
                         ):
        '''
        Initialize a new game session with player characters and NPCs.
        '''
        self.players = []
        for character in player_characters:
            player = self._init_player(character, self.orchestrator, player_logger)
            self.players.append(player)

        self.npcs = []
        for n in npcs:
            npc = self._init_npc(n, npc_logger)
            # Assign NPC to current scene if not already assigned
            if not npc.character.current_scene:
                npc.character.current_scene = scene.name
            self.npcs.append(npc)

        # Set the current scene and add to location graph
        self.current_scene = scene
        self.add_location_to_graph(scene.name, scene)

        self.logger.info(f"Initialized session '{self.session_name}' with {len(player_characters)} PCs")
        """Perform an external action within the game session. (players moves)"""
        return []

    def execute_events(self, event_list : list[Event]):
        """Process an event through the session's manipulator."""
        for event in event_list:
            self.manipulator.manage(event)

        


    def calculate_distance_3d(self, pos1: Coordinate3D, pos2: Coordinate3D) -> float:
        """Calculate Euclidean distance between two 3D coordinates."""
        dx = pos2.x - pos1.x
        dy = pos2.y - pos1.y
        dz = pos2.z - pos1.z
        return math.sqrt(dx*dx + dy*dy + dz*dz)

    def is_within_scene_bounds(self, position: Coordinate3D, scene: SceneNode) -> bool:
        """Check if a position is within the bounds of a scene."""
        if not self.spatial_enabled:
            return True  # If spatial system disabled, always within bounds

        half_x = scene.dimensions.x / 2
        half_y = scene.dimensions.y / 2
        half_z = scene.dimensions.z / 2

        min_x = scene.center_position.x - half_x
        max_x = scene.center_position.x + half_x
        min_y = scene.center_position.y - half_y
        max_y = scene.center_position.y + half_y
        min_z = scene.center_position.z - half_z
        max_z = scene.center_position.z + half_z

        return (min_x <= position.x <= max_x and
                min_y <= position.y <= max_y and
                min_z <= position.z <= max_z)

    def move_character_to_position(self, character: Character, new_position: Coordinate3D,
                                  scene: SceneNode) -> bool:
        """Move a character to a new position if it's within scene bounds."""
        if not self.spatial_enabled:
            character.position = new_position
            return True

        if self.is_within_scene_bounds(new_position, scene):
            old_position = character.position
            character.position = new_position
            self.logger.info(f"Moved {character.name} from ({old_position.x}, {old_position.y}, {old_position.z}) "
                           f"to ({new_position.x}, {new_position.y}, {new_position.z})")
            return True
        else:
            self.logger.warning(f"Attempted to move {character.name} outside scene bounds")
            return False

    def add_location_to_graph(self, location_name: str, scene_node: SceneNode):
        """Add a location to the location graph."""
        if location_name not in self.all_locations:
            self.all_locations[location_name] = scene_node
            self.location_graph[location_name] = set()
            self.logger.info(f"Added location '{location_name}' to location graph")

        # If this is the first location or we're initializing, set as current
        if self.current_location_name is None:
            self.current_location_name = location_name

    def connect_locations(self, location1: str, location2: str):
        """Connect two locations in the location graph."""
        # Ensure both locations exist in the graph
        if location1 not in self.location_graph:
            self.location_graph[location1] = set()
        if location2 not in self.location_graph:
            self.location_graph[location2] = set()

        # Add bidirectional connection
        self.location_graph[location1].add(location2)
        self.location_graph[location2].add(location1)
        self.logger.info(f"Connected locations '{location1}' and '{location2}'")

    def get_connected_locations(self, location_name: str) -> Set[str]:
        """Get all locations connected to the given location."""
        return self.location_graph.get(location_name, set())

    def get_all_locations(self) -> List[str]:
        """Get a list of all known locations."""
        return list(self.all_locations.keys())

    def change_current_location(self, new_location_name: str) -> bool:
        """Change the current location to the specified location."""
        if new_location_name in self.all_locations:
            old_location = self.current_location_name
            self.current_location_name = new_location_name
            self.current_scene = self.all_locations[new_location_name]
            self.logger.info(f"Changed location from '{old_location}' to '{new_location_name}'")
            return True
        else:
            self.logger.warning(f"Location '{new_location_name}' not found in location graph")
            return False

    def get_location_path(self, start_location: str, end_location: str) -> List[str]:
        """Find the shortest path between two locations using BFS."""
        if start_location not in self.location_graph or end_location not in self.location_graph:
            return []

        if start_location == end_location:
            return [start_location]

        # BFS to find shortest path
        queue = [(start_location, [start_location])]
        visited = {start_location}

        while queue:
            current_location, path = queue.pop(0)

            for neighbor in self.location_graph[current_location]:
                if neighbor == end_location:
                    return path + [neighbor]

                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return []  # No path found

    def _external_action(self, prompt: str = "", actor : str | None = None) -> List[Event]:
        """Perform a privileged external action within the game session. (DM moves)"""

        rules = f"""
        1. Determine which objects involved into the request.
        2. Be the most specific (if there is a certain object in the scene you should set event type to item-based not the entire scene)
        3. Always include spatial commands if the action involves movement or position changes.
        4. Choose the appropriate event type based on the action being performed:
        5. There are special types of requests from user when in battle. If an attack requested you Must generate an event that includes damage calculation based on character and item stats.
        6. Do not generate ACTION_RESULT events.

        EVENT TYPE RESPONSIBILITIES:
        - LOCATION_CHANGE: Moving characters between locations/scenes
        - LOCATION_MUTATION: Changing properties of a location itself
        - LOCATION_STATUS_CHANGE: Updating the status of a location (e.g., peaceful to dangerous)
        - SCENE_UPDATE: Updating scene description or properties
        - OBJECT_TRANSFER: Moving objects between containers/scene/inventory
        - ITEM_TRANSFER: Moving items between inventories, scenes, or containers
        - ITEM_STATUS_CHANGE: Changing status of an item (e.g., locked/unlocked, open/closed)
        - ITEM_MUTATION: Changing properties of an item (e.g., durability, condition)
        - ITEM_INTERACTION: Interacting with an item (e.g., opening a chest, using a key)
        - ITEM_PICKUP: Picking up an item from the scene
        - ITEM_DROP: Dropping an item into the scene
        - CONTAINER_ACCESS: Opening/closing/accessing containers
        - CONTAINER_TRANSFER: Moving items between containers
        - CHARACTER_STATUS_CHANGE: Changing character status (e.g., poisoned, stunned)
        - CHARACTER_DEATH: Character death events
        - CHARACTER_STATS_UPDATE: Updating character statistics (HP, attributes, etc.)
        - CHARACTER_MOVEMENT: Character movement within a scene
        - CHARACTER_TRANSFER: Moving characters between locations (for players)
        - NPC_TRANSFER: Moving NPCs between locations (for NPCs)
        - CHARACTER_POSITION_UPDATE: Updating character positions in 3D space
        - CHARACTER_TELEPORT: Instant character position changes
        - CHARACTER_PATHFINDING: Pathfinding and navigation events
        - DISTANCE_CALCULATION: Distance calculation requests
        """

        prompt_text = f"""
        You need to generate authoritative events based on the situation and a request e.g. "The dragon gets 1d8+2 damage. (based on items properties)" or "character 1 hits character 2 with a sword and dealing 1d6+3 damage"

        # EVENT TYPE RESPONSIBILITIES:
        {rules}

        # prompt
        {f"## actor: {actor}\nrequest: " if actor else ""}
        {prompt}
        # scene:
        {self.get_session_context()}
        
        # Last messages history (meta game) - for references:
        {self.get_messages_formatted()}
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

            player_characters = [Character(**char_data) for char_data in save_data["player_characters"]]

            # Initialize Player objects for each character
            self.players = []
            for character in player_characters:
                player = self._init_player(character, self.orchestrator)
                self.players.append(player)

            # Load NPCs
            self.npcs = []
            for npc_data in save_data["npcs"]:
                npc_character = NPCCharacter(**npc_data)
                npc = self._init_npc(npc_character)
                # Ensure NPC is assigned to the current scene if not already assigned
                if not npc.character.current_scene:
                    npc.character.current_scene = self.current_scene.name
                self.npcs.append(npc)
            for message_data in save_data.get("messages", []):
                message = Message(**message_data)
                self.messages.append(message)
            self.game_mode = GameModes(save_data["game_mode"])
            # Restore location graph data
            # Convert lists back to sets
            self.location_graph = {
                k: set(v) for k, v in save_data["location_graph"].items()
            }
            self.all_locations = {}
            for name, scene_dict in save_data["all_locations"].items():
                self.all_locations[name] = SceneNode(**scene_dict)
            self.current_location_name = save_data["current_location_name"]

            # Set the current scene
            self.current_scene = SceneNode(**save_data["current_scene"])

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

    def get_next_character_turn(self) -> tuple[Player | NPC, bool, float]:
        """Get the next character whose turn it is, based on initiative.

        Returns:
            tuple: (character_object, is_npc_boolean, next_turn_time)
        """
        if not self.turn_queue:
            self.initialize_turn_queue()
            if not self.turn_queue:
                raise ValueError("Turn queue is empty after initialization.")

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


    def start_game_loop_simple(self):
        if not self.game_master:
            raise ValueError("Game master (MAGG) is not initialized.")
        self.initialize_turn_queue()
        start_description = self.game_master.get_simple_description()
        print(f"\033[31mDM {self.game_mode.value}: {start_description}\033[0m\n")
        while True:
            try:
                character, is_npc, time = self.get_next_character_turn()
                
                decision = character.run()
                self.logger.debug(f"Character {character.character.name} decision {decision.verdict_type.value}")
                if decision.verdict_type == OrchestrationVerdictType.NPC_ACTION:
                    assert decision.details is not None
                    events = self._external_action(prompt=decision.details, actor=character.character.name)
                    self.logger.debug(f"Generated events after NPC decision: {events}")
                    self.execute_events(events)
                    
                elif decision.verdict_type == OrchestrationVerdictType.ILLEGAL_PLAYER_ACTION:
                    assert decision.details is not None
                    narrative = self.game_master.illegal_action_comment(
                        prompt=decision.original_request,
                        name=character.character.name,
                        reasoning=decision.details
                    )
                    self.logger.info(f"Generated narrative after ILLEGAL PLAYER decision: {decision.details}")
                        
                elif decision.verdict_type == OrchestrationVerdictType.ALLOWED_PLAYER_ACTION:
                    events = self._external_action(prompt=decision.details if decision.details else "Not provided", actor=character.character.name)
                    self.logger.debug(f"Generated events after PLAYER decision: {events}")
                    self.execute_events(events)
                    narrative = self.game_master.comment()
                else:
                    self.logger.info(f"{character.character.name} chose to skip their turn.")
                    self.logger.debug(decision)
                
                print(f"\033[31mDM Comment: {narrative}\033[0m")
            except KeyboardInterrupt:
                self.logger.info("Game loop interrupted by user.")
                break
    
    def new_message(self, message: Message):
        """Add a new message to the session's message history."""
        self.messages.append(message)
        # Keep only the last MAX_MESSAGES_STORED messages
        if len(self.messages) > MAX_MESSAGES_STORED:
            self.messages = self.messages[-MAX_MESSAGES_STORED:]
            
    def get_messages_formatted(self) -> str:
        """Get all messages formatted as a single string."""
        formatted_messages = ""
        for msg in self.messages:
            formatted_messages += f"{msg.sender_name}: {msg.text}\n"
        return formatted_messages