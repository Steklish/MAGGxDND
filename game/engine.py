import math
from typing import TYPE_CHECKING, List, Optional, Dict, Set
import uuid
from entity.round_determinator import RoundDeterminator
from game.event_pool import EventPool
from interface.delivery import Delivery
from magg.magg import Magg
from utils.naming_utils import find_fuzzy_matches
if TYPE_CHECKING:
    from game.manipulator import Manipulator
    from entity.orchestrator import Orchestrator

from entity.npc import NPC
from entity.player import Player
from schemas.in_game import Character, GameModes, NPCCharacter, SceneNode, Coordinate2D, UnifiedObject
from skls_embeddings import ChromaClient
from skls_generator import Generator
from logging import Logger
from schemas.orchestration import Message
import json

MAX_MESSAGES_STORED = 20
ROUND_DURATION = 10 # used for status efects ticks

class Session:
    def __init__(self,
                 session_name,
                 chroma_client : ChromaClient,
                 logger : Logger,
                 generator : Generator,
                 event_pool : EventPool,
                 delivery : Delivery,
                 magg_logger : Logger
                 ) -> None:
        self.session_name = session_name
        self.delivery = delivery
        self.generator = generator
        self.chroma_client = chroma_client
        self.logger = logger.getChild("session")
        self.event_pool = event_pool
        self.collection_name = f"game_session_{session_name}"
        self.players : List[Player] = []
        self.npcs : List[NPC] = []
        self.current_scene : SceneNode = None # type: ignore
        self.game_mode : GameModes = GameModes.STORY
        self.messages : List[Message] = []
        self._game_master = None  # Will be initialized later to avoid circular import
        self._init_mage(magg_logger)  # Initialize game master after avoiding circular import
        self.turn_queue : list[tuple[Player | NPC | RoundDeterminator, float, float]] = []
        # Turn-based system attributes
        self.turn_time = 0.0  # Global time tracker
        self.turn_distance = 10
        # Spatial system attributes
        self.spatial_enabled = True  # Flag to enable/disable spatial features

        # Location graph attributes
        self.location_graph: Dict[str, Set[str]] = {}  # Graph of connected locations
        self.all_locations: Dict[str, SceneNode] = {}  # Store all visited/known locations
        self.current_location_name: Optional[str] = None  # Track current location name
        self._orchestrator : 'Orchestrator | None'  # Will be set later
        
        self._initialize_round_determinator()


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
            event_queuee=self.event_pool.subscribe(npc_character.name),
            logger=logger_to_use,
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
            event_queuee=self.event_pool.subscribe(character.name),
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
            scene_info += f"\nScene center: ({self.current_scene.center_position.x}, {self.current_scene.center_position.y})"
            scene_info += f"\nScene dimensions: {self.current_scene.dimensions.x}x{self.current_scene.dimensions.y} {self.current_scene.scale_unit}"

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

        # Add spatial positions of characters
        characters_spatial_info = "\n\n#### SPATIAL POSITIONS OF CHARACTERS"
        for player in self.players:
            char = player.character
            characters_spatial_info += f"\n- {char.name}: ({char.position.x}, {char.position.y})"

        for npc in self.npcs:
            npc_char = npc.character
            if npc_char.current_scene == self.current_location_name:  # Only show NPCs in current scene
                characters_spatial_info += f"\n- {npc_char.name}: ({npc_char.position.x}, {npc_char.position.y})"

        # Add spatial positions of objects in the current scene
        objects_spatial_info = "\n\n#### SPATIAL POSITIONS OF OBJECTS IN CURRENT SCENE"
        if self.current_scene:
            for obj in self.current_scene.objects:
                if obj.position:
                    objects_spatial_info += f"\n- {obj.name}: ({obj.position.x}, {obj.position.y})"
                else:
                    objects_spatial_info += f"\n- {obj.name}: Position not specified"

        # 3. Construct the Context String
        context_str = f"""
### CURRENT SESSION STATE:

#### 1. CURRENT SCENE
{scene_info}

#### 2. PLAYER CHARACTERS (PCs)
{[c.character.short_summary for c in self.players]}

#### 3. NON-PLAYER CHARACTERS (NPCs)
{[n.character.short_summary if n.character.current_scene == self.current_location_name else None for n in self.npcs]}

{characters_spatial_info}
{objects_spatial_info}
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


    def find_object_by_name(self, name : str):
        def extractor(o : UnifiedObject):
            return o.name
        res = find_fuzzy_matches(
            items=self.get_all_objects_in_session(),
            extractor=extractor,
            target=name
        )
        if res != []:
            return res[0]
        else:
            return None

    def find_entity_by_name(self, name: str) -> Player | NPC | None:
        """Find an entity (Player or NPC) by name."""
        char = self.npcs + self.players

        def extractor(c : Player | NPC):
            return c.character.name
        
        res = find_fuzzy_matches(
            items=char,
            extractor=extractor,
            target=name
        )
        
        if res != []:
            return res[0]
        else:
            return None 

        


    def calculate_distance_2d(self, pos1: Coordinate2D, pos2: Coordinate2D) -> float:
        """Calculate Euclidean distance between two 2D coordinates."""
        dx = pos2.x - pos1.x
        dy = pos2.y - pos1.y
        return math.sqrt(dx*dx + dy*dy)

    def is_within_scene_bounds(self, position: Coordinate2D, scene: SceneNode) -> bool:
        """Check if a position is within the bounds of a scene."""
        if not self.spatial_enabled:
            return True  # If spatial system disabled, always within bounds

        half_x = scene.dimensions.x / 2
        half_y = scene.dimensions.y / 2

        min_x = scene.center_position.x - half_x
        max_x = scene.center_position.x + half_x
        min_y = scene.center_position.y - half_y
        max_y = scene.center_position.y + half_y

        return (min_x <= position.x <= max_x and
                min_y <= position.y <= max_y)

    def move_character_to_position(self, character: Character, new_position: Coordinate2D,
                                  scene: SceneNode) -> bool:
        """Move a character to a new position if it's within scene bounds."""
        if not self.spatial_enabled:
            character.position = new_position
            return True

        if self.is_within_scene_bounds(new_position, scene):
            old_position = character.position
            character.position = new_position
            self.logger.info(f"Moved {character.name} from ({old_position.x}, {old_position.y}) "
                           f"to ({new_position.x}, {new_position.y})")
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


    def _add_round_determinator_to_turn_queue(self):
        time_added = self.turn_time 
        next_move_time = self.turn_time + time_added / ROUND_DURATION
        self.turn_queue.append((self.round_determinator, time_added, next_move_time))
            
        
        
    def _add_character_to_turn_queue(self, char : NPC | Player | RoundDeterminator):
        if isinstance(char, RoundDeterminator):
            self._add_round_determinator_to_turn_queue()
        elif isinstance(char, (NPC, Player)):
            if char.character.is_alive:
                time_added = self.turn_time
                # Prevent division by zero if initiative_bonus is 0
                if char.character.initiative_bonus == 0:
                    next_move_time = self.turn_time + time_added  # Default to same turn time
                else:
                    next_move_time = self.turn_time + time_added / char.character.initiative_bonus
                self.turn_queue.append((char, time_added, next_move_time))
        
    def _add_all_characters_to_turn_queue(self):
        """Add a character to the turn queue with their calculated next turn time."""
        for o in self.npcs + self.players:
            # Only add characters that are alive and in the current scene (for NPCs)
            if isinstance(o, Player):
                # For players, just check if alive
                if o.character.is_alive:
                    self._add_character_to_turn_queue(o)
            elif isinstance(o, NPC):
                # For NPCs, check if alive and in current scene
                if o.character.is_alive and o.character.current_scene == self.current_location_name:
                    self._add_character_to_turn_queue(o)
        
        
    def _initialize_turn_queue(self):
        """Initialize the turn queue with all characters (both PCs and NPCs)."""
        self.turn_queue = []
        self.turn_time = 0.0
        self._add_all_characters_to_turn_queue()
        self._add_round_determinator_to_turn_queue()
        self.logger.debug(f"Initialized turn queue with {len(self.players)} PCs and {len(self.npcs)} NPCs")

    def _get_next_character_turn(self) -> Player | NPC | RoundDeterminator:
        def time_sort(a):
            return a[2]

        # Check if turn queue is empty and initialize if needed
        if not self.turn_queue:
            self._initialize_turn_queue()
            if not self.turn_queue:  # If still empty, there are no valid characters
                raise RuntimeError("No characters available for turns. All characters may be dead or inactive.")

        self.turn_queue.sort(key=time_sort)
        next_char, time_added, next_turn = self.turn_queue[0]
        self.turn_time = float(next_turn)
        self.turn_queue.pop(0)

        self._add_character_to_turn_queue(next_char)
        return next_char

    def get_all_characters_in_current_location(self) -> List[Player | NPC]:
        """Get all characters (both players and NPCs in current location)."""
        all_characters = []
        for player in self.players:
            all_characters.append(player.character)
        for npc in self.npcs:
            if npc.character.current_scene == self.current_scene.name:
                all_characters.append(npc.character)
        return all_characters



    def get_all_active_characters(self) -> list[Character |NPCCharacter]:
        return [c.character for c in self.get_all_active_entities()]
    
    def get_all_active_entities(self) -> list[Player | NPC]:
        all_characters = []
        for player in self.players:
            if player.character.current_hp > 0 and player.character.is_alive: # type: ignore
                all_characters.append(player)
        for npc in self.npcs:
            if npc.character.current_scene == self.current_scene.name and npc.character.current_hp > 0 and npc.character.is_alive:
                all_characters.append(npc)
        return all_characters
        

    def _get_all_characters(self):
        """Get all characters (both players and NPCs) in the session."""
        all_characters = []
        for player in self.players:
            all_characters.append(player.character)
        for npc in self.npcs:
            all_characters.append(npc.character)
        return all_characters

    def draw_ascii_scene(self):
        """Draw an ASCII representation of the current scene with characters and objects."""
        if not self.current_scene:
            print("\n[No current scene loaded]")
            return

        print("\n" + "="*60)
        print(f"📍 {self.current_scene.name.upper()}")
        print("="*60)
        self._print_turn_queue()

        # Get scene dimensions and center
        center_x, center_y = (self.current_scene.center_position.x,
                              self.current_scene.center_position.y)
        width = self.current_scene.dimensions.x
        height = self.current_scene.dimensions.y

        # Calculate boundaries
        min_x = center_x - width/2
        max_x = center_x + width/2
        min_y = center_y - height/2
        max_y = center_y + height/2

        print(f"📏 Scene: {width}x{height} {self.current_scene.scale_unit} | Center: ({center_x}, {center_y})")
        print(f"💬 {self.current_scene.description}")

        # Create a 2D grid representation
        # We'll use a simple grid where each cell represents a 1-unit area
        grid_size = 20  # Fixed grid size for visualization
        grid = [['.' for _ in range(grid_size)] for _ in range(grid_size)]

        # Calculate scaling factors to map scene coordinates to grid positions
        x_scale = grid_size / width if width > 0 else 1
        y_scale = grid_size / height if height > 0 else 1

        # Place characters on the grid
        for player in self.players:
            char = player.character
            if hasattr(char, 'position'):
                # Map position to grid coordinates
                grid_x = int((char.position.x - min_x) * x_scale)
                grid_y = int((char.position.y - min_y) * y_scale)

                # Keep within bounds
                grid_x = max(0, min(grid_size - 1, grid_x))
                grid_y = max(0, min(grid_size - 1, grid_y))

                # Use first letter of name or 'P' for player
                symbol = char.name[0].upper() if char.name else 'P'
                grid[grid_y][grid_x] = f'\033[34m{symbol}\033[0m'  # Blue for players

        # Place NPCs on the grid
        for npc in self.npcs:
            npc_char = npc.character
            if npc_char.current_scene == self.current_location_name:  # Only show NPCs in current scene
                if hasattr(npc_char, 'position'):
                    # Map position to grid coordinates
                    grid_x = int((npc_char.position.x - min_x) * x_scale)
                    grid_y = int((npc_char.position.y - min_y) * y_scale)

                    # Keep within bounds
                    grid_x = max(0, min(grid_size - 1, grid_x))
                    grid_y = max(0, min(grid_size - 1, grid_y))

                    # Use first letter of name or 'N' for NPC
                    symbol = npc_char.name[0].upper() if npc_char.name else 'N'
                    grid[grid_y][grid_x] = f'\033[31m{symbol}\033[0m'  # Red for NPCs

        # Place objects on the grid
        for obj in self.current_scene.objects:
            if hasattr(obj, 'position') and obj.position:
                # Map position to grid coordinates
                grid_x = int((obj.position.x - min_x) * x_scale)
                grid_y = int((obj.position.y - min_y) * y_scale)

                # Keep within bounds
                grid_x = max(0, min(grid_size - 1, grid_x))
                grid_y = max(0, min(grid_size - 1, grid_y))

                # Use first letter of object name or 'O' for object
                symbol = obj.name[0].upper() if obj.name else 'O'
                grid[grid_y][grid_x] = f'\033[33m{symbol}\033[0m'  # Yellow for objects

        # Print the grid
        print("\n🗺️  SCENE MAP:")
        for row in grid:
            print(' '.join(row))

        # Print legend
        print("\n📋 LEGEND:")
        print(f"  \033[34mP\033[0m - Players ({', '.join([p.character.name for p in self.players])})")
        print(f"  \033[31mN\033[0m - NPCs ({', '.join([n.character.name for n in self.npcs if n.character.current_scene == self.current_location_name])})")
        print(f"  \033[33mO\033[0m - Objects ({', '.join([o.name for o in self.current_scene.objects])})")
        print(f"  \033[32m.\033[0m - Empty space")

        # Print character statuses
        print("\n👤 CHARACTER STATUS:")
        for player in self.players:
            char = player.character
            status = f"  🧍 {char.name}: HP {char.current_hp}/{char.max_hp}, Pos ({char.position.x}, {char.position.y})"
            if char.active_conditions and char.active_conditions.strip():
                # active_conditions is a string with newlines, split by newline to get individual conditions
                conditions = [cond.strip() for cond in char.active_conditions.split('\n') if cond.strip()]
                if conditions:
                    status += f" ⚠️  {', '.join(conditions)}"
            print(status)

        for npc in self.npcs:
            npc_char = npc.character
            if npc_char.current_scene == self.current_location_name:
                status = f"  👹 {npc_char.name}: HP {npc_char.current_hp}/{npc_char.max_hp}, Pos ({npc_char.position.x}, {npc_char.position.y})"
                if npc_char.active_conditions and npc_char.active_conditions.strip():
                    # active_conditions is a string with newlines, split by newline to get individual conditions
                    conditions = [cond.strip() for cond in npc_char.active_conditions.split('\n') if cond.strip()]
                    if conditions:
                        status += f" ⚠️  {', '.join(conditions)}"
                print(status)

        print("="*60)

    def _print_turn_queue(self):
        """Print a beautiful and informative representation of the turn queue."""
        if not self.turn_queue:
            print("🕐 Turn Queue: Empty")
            return

        print("🕐 TURN QUEUE:")
        print("┌─────────────────────────────────────────────────────────┐")

        # Sort the queue by turn time to show the order
        sorted_queue = sorted(self.turn_queue, key=lambda x: x[2])

        for i, (char, time_added, next_turn) in enumerate(sorted_queue):
            # Determine character name and type
            if hasattr(char, 'character'):
                name = char.character.name # type: ignore
                char_type = "👤" if hasattr(char, '_init_player') or 'Player' in str(type(char)) else "👹"
            else:
                name = "Round Determinator"
                char_type = "🔄"

            # Format the turn time
            turn_time_str = f"{next_turn:.2f}"

            # Determine if this is the next to act
            is_next = i == 0

            # Create the entry with appropriate highlighting
            if is_next:
                print(f"│ 🎯 NEXT: {char_type} {name:<20} │ Turn: {turn_time_str:>6} │")
            else:
                print(f"│        {char_type} {name:<20} │ Turn: {turn_time_str:>6} │")

        print("└─────────────────────────────────────────────────────────┘")
        print(f"⏱️  Global Time: {self.turn_time:.2f}")
        
    def _initialize_round_determinator(self):
        """Initialize the round determinator separately."""
        # Create the round determinator
        self.round_determinator = RoundDeterminator(ROUND_DURATION, self.event_pool.subscribe("round determinator"))
        self.round_determinator.inject_state(self)
        self.logger.debug(f"Initialized round determinator with round duration {ROUND_DURATION}")

    def get_all_objects_in_session(self):
        """
        Returns a list of all objects in the session including:
        - Objects in the current scene
        - Objects in containers (any recursion depth)
        - Objects in character inventories (both players and NPCs)
        """
        all_objects = []

        # Add objects from the current scene
        if self.current_scene:
            for obj in self.current_scene.objects:
                all_objects.append(obj)
                # Recursively add objects from containers
                all_objects.extend(self._get_all_objects_in_container(obj))

        # Add objects from player inventories
        for player in self.players:
            for obj in player.character.inventory:
                all_objects.append(obj)
                # Recursively add objects from containers in inventory
                all_objects.extend(self._get_all_objects_in_container(obj))

        # Add objects from NPC inventories
        for npc in self.npcs:
            for obj in npc.character.inventory:
                all_objects.append(obj)
                # Recursively add objects from containers in inventory
                all_objects.extend(self._get_all_objects_in_container(obj))

        return all_objects

    def find_object_and_location(self, object_name: str):
        """
        Find an object and return both the object and its location information.
        Returns a tuple: (object, location_type, owner, container) where:
        - object: The UnifiedObject instance
        - location_type: 'scene', 'player_inventory', 'npc_inventory', or 'container'
        - owner: The player/npc if in inventory, None otherwise
        - container: The container object if inside a container, None otherwise
        """
        # Search in scene objects
        for obj in self.current_scene.objects if self.current_scene else []:
            if obj.name.lower() == object_name.lower():
                return obj, 'scene', None, None
            # Check if it's in a container in the scene
            container_obj, container = self._find_in_container(obj, object_name)
            if container_obj:
                return container_obj, 'container', None, container

        # Search in player inventories
        for player in self.players:
            for obj in player.character.inventory:
                if obj.name.lower() == object_name.lower():
                    return obj, 'player_inventory', player, None
                # Check if it's in a container in the inventory
                container_obj, container = self._find_in_container(obj, object_name)
                if container_obj:
                    return container_obj, 'container', player, container

        # Search in NPC inventories
        for npc in self.npcs:
            for obj in npc.character.inventory:
                if obj.name.lower() == object_name.lower():
                    return obj, 'npc_inventory', npc, None
                # Check if it's in a container in the inventory
                container_obj, container = self._find_in_container(obj, object_name)
                if container_obj:
                    return container_obj, 'container', npc, container

        return None, None, None, None

    def _find_in_container(self, container_obj, target_name: str):
        """
        Recursively search for an object inside a container.
        Returns (found_object, parent_container) or (None, None).
        """
        if container_obj.contained_objects:
            for obj in container_obj.contained_objects:
                if obj.name.lower() == target_name.lower():
                    return obj, container_obj
                # Recursively search nested containers
                nested_obj, nested_container = self._find_in_container(obj, target_name)
                if nested_obj:
                    return nested_obj, nested_container
        return None, None

    def transfer_object(self, obj: 'UnifiedObject', from_location: str, to_location: str,
                       quantity: int = 1, target_owner = None, target_container = None):
        """
        Transfer an object from one location to another.
        """
        # Adjust quantity if needed
        if obj.quantity < quantity:
            self.logger.warning(f"Not enough quantity of {obj.name} to transfer. Available: {obj.quantity}, Requested: {quantity}")
            return False

        # Handle partial quantity transfer by creating a new object
        obj_to_transfer = obj
        original_quantity = obj.quantity

        if quantity < obj.quantity:
            # Create a new object with the transferred quantity
            obj_to_transfer = obj.copy(update={"quantity": quantity})
            # Reduce the quantity of the original object
            obj.quantity -= quantity
        else:
            # Transfer the entire object - remove it from its current location
            removal_success = self._remove_object_from_location(obj, from_location, quantity)
            if not removal_success:
                return False

        # Add the object to target location
        addition_success = self._add_object_to_location(obj_to_transfer, to_location, quantity, target_owner, target_container)
        if not addition_success:
            # If adding failed, restore the original object's state
            if quantity < original_quantity:
                obj.quantity += quantity
            elif quantity == original_quantity:
                # If we removed the whole object, try to add it back to its original location
                self._add_object_to_location(obj, from_location, quantity, target_owner, target_container)
            return False

        return True

    def _remove_object_from_location(self, obj: 'UnifiedObject', location_type: str, quantity: int):
        """
        Remove an object from its current location.
        """
        if quantity >= obj.quantity:
            # Remove the entire object
            if location_type == 'scene':
                if self.current_scene and obj in self.current_scene.objects:
                    self.current_scene.objects.remove(obj)
                    return True
            elif location_type == 'player_inventory':
                for player in self.players:
                    if obj in player.character.inventory:
                        player.character.inventory.remove(obj)
                        return True
            elif location_type == 'npc_inventory':
                for npc in self.npcs:
                    if obj in npc.character.inventory:
                        npc.character.inventory.remove(obj)
                        return True
            elif location_type == 'container':
                # Find the container that holds this object and remove it
                for container in self._get_all_containers():
                    if container.contained_objects and obj in container.contained_objects:
                        container.contained_objects.remove(obj)
                        return True
        else:
            # Reduce the quantity and create a new object with the transferred quantity
            obj.quantity -= quantity
            # We need to return the new object that will be transferred
            # This is tricky because we're modifying the original object in place
            # For now, we'll just return True and handle the new object creation elsewhere
            return True

        return False

    def _add_object_to_location(self, obj: 'UnifiedObject', location_type: str, quantity: int,
                               target_owner = None, target_container = None):
        """
        Add an object to a location.
        """
        if location_type == 'scene':
            if self.current_scene:
                self.current_scene.objects.append(obj)
                return True
        elif location_type in ['player_inventory', 'npc_inventory']:
            if target_owner:
                target_owner.character.inventory.append(obj)
                return True
            else:
                # If no specific owner, add to the first player's inventory as default
                if self.players:
                    self.players[0].character.inventory.append(obj)
                    return True
        elif location_type == 'container':
            if target_container:
                if target_container.contained_objects is None:
                    target_container.contained_objects = []
                target_container.contained_objects.append(obj)
                return True

        return False

    def _get_all_containers(self):
        """
        Get all containers in the session (in scene, player inventories, and NPC inventories).
        """
        containers = []

        # Add containers from scene
        if self.current_scene:
            for obj in self.current_scene.objects:
                if obj.obj_type and obj.obj_type.value == "Container":
                    containers.append(obj)
                    # Add nested containers too
                    containers.extend(self._get_nested_containers(obj))

        # Add containers from player inventories
        for player in self.players:
            for obj in player.character.inventory:
                if obj.obj_type and obj.obj_type.value == "Container":
                    containers.append(obj)
                    # Add nested containers too
                    containers.extend(self._get_nested_containers(obj))

        # Add containers from NPC inventories
        for npc in self.npcs:
            for obj in npc.character.inventory:
                if obj.obj_type and obj.obj_type.value == "Container":
                    containers.append(obj)
                    # Add nested containers too
                    containers.extend(self._get_nested_containers(obj))

        return containers

    def _get_nested_containers(self, container_obj):
        """
        Recursively get all nested containers within a container.
        """
        nested_containers = []
        if container_obj.contained_objects:
            for obj in container_obj.contained_objects:
                if obj.obj_type and obj.obj_type.value == "Container":
                    nested_containers.append(obj)
                    # Recursively get deeper nested containers
                    nested_containers.extend(self._get_nested_containers(obj))
        return nested_containers

    def _get_all_objects_in_container(self, obj):
        """
        Recursively get all objects in a container and its nested containers.
        """
        all_nested_objects = []

        # If the object is a container, get its contents
        if obj.contained_objects:
            for nested_obj in obj.contained_objects:
                all_nested_objects.append(nested_obj)
                # Recursively get objects in nested containers
                all_nested_objects.extend(self._get_all_objects_in_container(nested_obj))

        return all_nested_objects
    
    def new_message(self, message: Message):
        """Add a new message to the session's message history."""
        self.messages.append(message)
        # Keep only the last MAX_MESSAGES_STORED messages
        if len(self.messages) > MAX_MESSAGES_STORED:
            self.messages = self.messages[-MAX_MESSAGES_STORED:]
    
    def game_loop(self):
        self._initialize_turn_queue()
        while 1:
            self.logger.debug(f"Turn at turn_time {self.turn_time} starter."    )
            try:
                char = self._get_next_character_turn()
                char.run()
                self.logger.debug(f"Launcing DM comment for {len(self.event_pool.get_events())} events")
                if len(self.event_pool.get_events()) > 0:
                    comment = self.game_master.comment()
                    self.delivery.master_message(
                        text=comment
                    )
                else: self.logger.debug("No events provided on the end of turn.")
            except KeyboardInterrupt as e:
                self.logger.info("Game loop was stopped by user")
                break
    
    def get_messages_formatted(self) -> str:
        """Get all messages formatted as a single string."""
        formatted_messages = ""
        for msg in self.messages:
            formatted_messages += f"{msg.sender_name}: {msg.text}\n"
        return formatted_messages