import asyncio
import math
from typing import TYPE_CHECKING, List, Optional, Dict, Set
import uuid
from core.entity.round_determinator import RoundDeterminator
from core.game.event_pool import EventPool
from core.interface.delivery import Delivery
from core.magg.magg import Magg
from core.magg.plot_schemas import ChapterStatus, Plot
from core.utils.naming_utils import find_fuzzy_matches
if TYPE_CHECKING:
    from core.game.manipulator import Manipulator
    from core.entity.orchestrator import Orchestrator

from core.entity.npc import NPC
from core.entity.player import Player
from core.schemas.in_game import Character, GameModes, NPCCharacter, SceneNode, Coordinate2D, UnifiedObject
from skls_embeddings import ChromaClient
from skls_generator import Generator
from logging import Logger
from core.schemas.orchestration import Message
import json

MAX_MESSAGES_STORED = 20
ROUND_DURATION = 10 # used for round based actions

class Session:
    def __init__(self,
                 session_name,
                 chroma_client : ChromaClient,
                 logger : Logger,
                 generator : Generator,
                 event_pool : EventPool,
                 delivery : Delivery,
                 language: str = "ru",
                 ) -> None:
        self.session_name = session_name
        self.language = language or "ru"
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
        self._init_mage(logger.getChild("magg"))  # Initialize game master after avoiding circular import
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
        self._plot : "Plot | None" = None

    def set_language(self, language: str) -> None:
        """Update session language ('ru' or 'en') and synchronize game master, plot, and characters."""
        if language in ("ru", "en"):
            self.language = language
            self.logger.info(f"Session language updated to '{language}'")
            try:
                from core.magg.plot_schemas import generate_default_plot
                self._plot = generate_default_plot(self.session_name, language=self.language)
            except Exception as e:
                self.logger.warning(f"Error regenerating plot for language {language}: {e}")

            if self.delivery:
                announcement = (
                    "🌐 **ЯЗЫК ИГРЫ ИЗМЕНЕН:** Ведущий (DM), сюжет и персонажи теперь ведут повествование на **русском языке**."
                    if language == "ru"
                    else "🌐 **GAME LANGUAGE UPDATED:** Game Master (DM), plot, and characters are now narrating in **English**."
                )
                self.delivery.master_message(text=announcement, tag="system_info")
                self.delivery.session_updated(self)

    @property
    def game_master(self) -> 'Magg':
        if self._game_master is None:
            raise ValueError("Mage is not initialized!")
        return self._game_master

    @property
    def plot(self) -> 'Plot':
        if self._plot is None:
            from core.magg.plot_schemas import generate_default_plot
            self._plot = generate_default_plot(self.session_name, language=self.language)
        return self._plot

    @property
    def orchestrator(self) -> 'Orchestrator':
        if self._orchestrator is None:
            raise ValueError("Orchestrator not initialized!")
        return self._orchestrator
        
    def _init_orchestrator(self, orchestrator : 'Orchestrator'):
        self._orchestrator = orchestrator

    def _init_plot(self, guide : str = "") -> None:
        """Initialize plot using AI if available, falling back to thematic procedural plot."""
        import os
        from core.magg.plot_schemas import Plot, ChapterStatus, generate_default_plot
        prompt = None
        prompt_paths = [
            "docs/prompts/plot_generation.md",
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs", "prompts", "plot_generation.md")
        ]
        for p in prompt_paths:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        prompt = f.read()
                    break
                except Exception:
                    pass

        if self.generator and prompt:
            try:
                lang_rule = "Respond strictly in RUSSIAN." if self.language == "ru" else "Respond strictly in ENGLISH."
                full_prompt = f"{prompt}\n\n### Language Directive\n{lang_rule}\n\n### Mature content\nViolence is acceptable in this story.\n\n### Guide\nUse those ideas to create a story:\n{guide or self.session_name}\n"
                self._plot = self.generator.generate_one_shot(
                    pydantic_model=Plot,
                    prompt=full_prompt
                )
                if self._plot and self._plot.chapters:
                    for chapter in self._plot.chapters:
                        if not chapter.status:
                            chapter.status = ChapterStatus.COMING
                    self.logger.info("Plot initialized via AI generator.")
                    return
            except Exception as e:
                self.logger.warning(f"AI plot generation failed: {e}. Falling back to procedural plot.")

        self._plot = generate_default_plot(guide or self.session_name, language=self.language)
        self.logger.info("Plot initialized via procedural generator fallback.")
        
         
        
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
        logger_to_use = npc_logger if npc_logger else self.logger
        new_NPC = NPC(
            character=npc_character,
            event_queuee=self.event_pool.subscribe(npc_character.name),
            logger=logger_to_use,
        )
        new_NPC.inject_state(self)
        self.npcs.append(new_NPC)  # Add to session's NPC list
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
    
    def get_session_state(self):
        """"Serializes session to a json object."""
        # Prepare data for serialization
        save_dict = {
            "session_name": self.session_name,
            "language": getattr(self, "language", "ru"),
            "game_mode": self.game_mode.value,
            "player_characters": [char.character.dict() for char in self.players],
            "players": [char.character.dict() for char in self.players],
            "npcs": [npc.character.dict() for npc in self.npcs],
            "current_scene": self.current_scene.dict() if self.current_scene else None,
            # Location graph data - convert sets to lists for JSON
            "location_graph": {k: list(v) for k, v in self.location_graph.items()},
            "all_locations": {name: scene.dict() for name, scene in self.all_locations.items()},
            "current_location_name": self.current_location_name,
            "messages": [msg.dict() for msg in self.messages],
            # Turn-based system attributes
            "turn_time": self.turn_time,
            "turn_distance": self.turn_distance,
            # Spatial system attributes
            "spatial_enabled": self.spatial_enabled,
            # Plot information
            "plot": self.plot.model_dump(mode='json') if hasattr(self.plot, 'model_dump') else self.plot.dict(),
            "current_chapter": self.plot.current_chapter.model_dump(mode='json') if self.plot and self.plot.current_chapter else None,
            # Turn queue (serialize as structured objects matching frontend schema)
            "turn_queue": [
                {
                    "character": entity.character.name if hasattr(entity, 'character') else "Round Determinator",
                    "character_type": "player" if isinstance(entity, Player) else ("npc" if isinstance(entity, NPC) else "round_determinator"),
                    "time_added": time_added,
                    "next_turn": next_turn
                }
                for entity, time_added, next_turn in self.turn_queue
                if hasattr(entity, 'character')
            ]
        }
        return save_dict
    
    def save_session(self, filename: str):
        """Saves session data to a JSON file."""
        save_dict = self.get_session_state()

        with open(filename, 'w', encoding="utf-8") as f:
            json.dump(save_dict, f, indent=4)
        self.logger.info(f"Session saved to {filename}")

    def _serialize_character_identifier(self, entity):
        """Serialize a character identifier for storage."""
        if isinstance(entity, (Player, NPC)):
            return {"type": "character", "name": entity.character.name}
        elif isinstance(entity, RoundDeterminator):
            return {"type": "round_determinator"}
        else:
            return {"type": "unknown", "repr": str(entity)}

    def get_session_context(self) -> str:
        """
        Generates a comprehensive text representation of the current session state
        optimized for LLM consumption, providing full world omniscience to the Dungeon Master (MAGG):
        - Overarching Plot, Current Chapter, and Active Objectives
        - World Map & Location Graph (all visited locations & connections)
        - Current Scene (description, interactive objects, spatial positions)
        - Characters in Current Scene (players & NPCs present)
        - Characters in Other Locations (off-screen NPCs & players pinned elsewhere)
        - Proximity and Visibility Relationships
        """
        # 1. Format Plot & Objectives
        plot_info = "No active plot."
        if self.plot:
            current_ch = self.plot.current_chapter
            chapter_status_str = f"Chapter: {current_ch.name} (Status: {current_ch.status.value if hasattr(current_ch.status, 'value') else current_ch.status})\nDescription: {current_ch.description}\n" if current_ch else "No active chapter."
            tasks_str = ""
            if current_ch and current_ch.tasks:
                tasks_str = "Tasks / Objectives:\n" + "\n".join([f"  [{'x' if done else ' '}] {task}" for task, done in current_ch.tasks.items()])
            upcoming_chapters = [c.name for c in self.plot.chapters if c != current_ch]
            plot_info = f"Campaign Plot: {getattr(self.plot, 'theme', self.session_name)}\n{chapter_status_str}{tasks_str}\nUpcoming Chapters: {', '.join(upcoming_chapters) if upcoming_chapters else 'None'}"

        # 2. Format Location Graph Info
        scene_info = ""
        if self.current_scene:
            scene_info = f"Current Location: {getattr(self.current_scene, 'name', 'Unknown')}\n"
            scene_info += f"Description: {getattr(self.current_scene, 'description', 'No description available.')}\n"
            scene_info += f"Game mode: {self.game_mode.value}"
            if self.current_location_name:
                connected_locs = self.get_connected_locations(self.current_location_name)
                scene_info += f"\nDirectly connected locations: {', '.join(connected_locs) if connected_locs else 'None'}"
        else:
            scene_info = "No current scene loaded."

        # All visited locations in graph
        all_locs = self.get_all_locations()
        location_graph_summary = f"All Visited Locations ({len(all_locs)}): {', '.join(all_locs)}\n"
        graph_edges = []
        for loc, neighbors in self.location_graph.items():
            if neighbors:
                graph_edges.append(f"  {loc} <-> {', '.join(neighbors)}")
        if graph_edges:
            location_graph_summary += "World Connection Topology:\n" + "\n".join(graph_edges)

        # 3. Entities in Current Scene
        current_players = [p.character.short_summary for p in self.players]
        current_npcs = [n.character.short_summary for n in self.npcs if n.character.current_scene == self.current_location_name]

        # 4. Entities in Other Visited Locations across the Realm (DM Omniscience)
        other_npcs_by_loc = {}
        for n in self.npcs:
            npc_loc = n.character.current_scene or "Unknown / Wandering"
            if npc_loc != self.current_location_name:
                if npc_loc not in other_npcs_by_loc:
                    other_npcs_by_loc[npc_loc] = []
                status = "ALIVE" if n.character.is_alive else "DEAD"
                other_npcs_by_loc[npc_loc].append(f"{n.character.name} ({n.character.char_class.value if hasattr(n.character.char_class, 'value') else n.character.char_class}, {status})")

        offscreen_info = "None"
        if other_npcs_by_loc:
            offscreen_lines = []
            for loc, n_list in other_npcs_by_loc.items():
                offscreen_lines.append(f"- Location '{loc}': {', '.join(n_list)}")
            offscreen_info = "\n".join(offscreen_lines)

        # Spatial positions in current scene
        characters_spatial_info = "\n\n#### SPATIAL POSITIONS OF CHARACTERS IN CURRENT SCENE"
        for player in self.players:
            char = player.character
            characters_spatial_info += f"\n- {char.name}: ({char.position.x}, {char.position.y})"

        for npc in self.npcs:
            npc_char = npc.character
            if npc_char.current_scene == self.current_location_name:
                characters_spatial_info += f"\n- {npc_char.name}: ({npc_char.position.x}, {npc_char.position.y})"

        # Spatial positions of objects in current scene
        objects_spatial_info = "\n\n#### OBJECTS IN CURRENT SCENE"
        if self.current_scene and getattr(self.current_scene, 'objects', None):
            for obj in self.current_scene.objects:
                pos_str = f"({obj.position.x}, {obj.position.y})" if getattr(obj, 'position', None) else "Position not specified"
                state_str = f", State: {obj.state}" if getattr(obj, 'state', None) else ""
                objects_spatial_info += f"\n- {obj.name} [{getattr(obj, 'obj_type', 'Prop')}]: {pos_str}{state_str} - {getattr(obj, 'description', '')}"
        else:
            objects_spatial_info += "\nNo interactive objects in this scene."

        visibility_info = self._get_visibility_info()

        context_str = f"""
### CURRENT SESSION STATE:

#### 1. CAMPAIGN PLOT & ACTIVE QUESTS
{plot_info}

#### 2. CURRENT SCENE
{scene_info}

#### 3. WORLD MAP & VISITED LOCATION GRAPH
{location_graph_summary}

#### 4. PLAYER CHARACTERS (PCs in Current Scene)
{current_players}

#### 5. NON-PLAYER CHARACTERS (NPCs in Current Scene)
{current_npcs if current_npcs else 'None present'}

#### 6. CHARACTERS IN OTHER VISITED LOCATIONS (WORLD OVERVIEW)
{offscreen_info}

{characters_spatial_info}
{objects_spatial_info}
{visibility_info}
"""
        return context_str.strip()

    def _get_visibility_info(self, max_distance: float = 10.0) -> str:
        """
        Generates information about who sees who and what objects based on spatial proximity.
        
        Args:
            max_distance: Maximum distance at which characters can see each other and objects
            
        Returns:
            A formatted string describing visibility relationships
        """
        visibility_info = "\n\n#### VISIBILITY INFORMATION (WHO SEES WHO AND WHAT)"
        
        # Get all characters in the current scene
        all_characters = []
        for player in self.players:
            all_characters.append(('player', player.character))
        for npc in self.npcs:
            if npc.character.current_scene == self.current_location_name:
                all_characters.append(('npc', npc.character))
        
        # For each character, determine what they can see
        for char_type, character in all_characters:
            visible_entities = []
            visible_objects = []
            
            # Check which other characters this character can see
            for other_char_type, other_character in all_characters:
                if character.name != other_character.name:  # Don't include self
                    distance = self.calculate_distance_2d(character.position, other_character.position)
                    if distance <= max_distance:
                        visible_entities.append(f"{other_character.name} ({other_char_type.upper()}) at distance {distance:.2f}")
            
            # Check which objects this character can see
            if self.current_scene:
                for obj in self.current_scene.objects:
                    if obj.position:
                        distance = self.calculate_distance_2d(character.position, obj.position)
                        if distance <= max_distance:
                            visible_objects.append(f"{obj.name} at distance {distance:.2f}")
            
            # Format the visibility info for this character
            visibility_info += f"\n\n{character.name} ({char_type.upper()}) sees:"
            if visible_entities:
                visibility_info += f"\n  Characters: {', '.join(visible_entities)}"
            else:
                visibility_info += f"\n  Characters: None nearby"
                
            if visible_objects:
                visibility_info += f"\n  Objects: {', '.join(visible_objects)}"
            else:
                visibility_info += f"\n  Objects: None nearby"
        
        return visibility_info
    
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

    
    def find_player_by_name(self, name: str) -> Player | NPC | None:
        """Find an player by name."""

        def extractor(c : Player | NPC):
            return c.character.name
        
        res = find_fuzzy_matches(
            items=self.players,
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

    def is_within_scene_bounds(self, position: Coordinate2D, scene: Optional[SceneNode]) -> bool:
        """Check if a position is within the bounds of a scene."""
        if not self.spatial_enabled or scene is None or not hasattr(scene, 'dimensions') or not scene.dimensions:
            return True  # If spatial system disabled or scene missing, allow movement

        half_x = scene.dimensions.x / 2
        half_y = scene.dimensions.y / 2

        min_x = scene.center_position.x - half_x
        max_x = scene.center_position.x + half_x
        min_y = scene.center_position.y - half_y
        max_y = scene.center_position.y + half_y

        return (min_x <= position.x <= max_x and
                min_y <= position.y <= max_y)

    def move_character_to_position(self, character: Character, new_position: Coordinate2D,
                                  scene: Optional[SceneNode]) -> bool:
        """Move a character to a new position if it's within scene bounds."""
        if not self.spatial_enabled or scene is None:
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

    def transition_to_location(self, new_location_name: str, description: Optional[str] = None) -> SceneNode:
        """
        Transition party to a location.
        If the location already exists in visited locations (all_locations), load it.
        If it has never occurred before, generate a brand new SceneNode with thematic objects and battlemap,
        connect it in the location graph, generate thematic NPCs pinned to the location, and update the graph.
        """
        old_location = self.current_location_name
        is_new_location = new_location_name not in self.all_locations

        if is_new_location:
            from backend.src.api.routers.session_router import procedural_gen, ensure_scene_battlemap
            self.logger.info(f"Generating new undiscovered location: '{new_location_name}'")
            scene_prompt = f"{new_location_name}. {description or ''}".strip()
            new_scene = procedural_gen.generate_scene(scene_prompt, language=getattr(self, "language", "ru"))
            new_scene.name = new_location_name
            if description:
                new_scene.description = description
            ensure_scene_battlemap(new_scene)

            # Add to graph
            self.add_location_to_graph(new_location_name, new_scene)
            if old_location:
                self.connect_locations(old_location, new_location_name)

            # Generate 1-2 thematic NPCs pinned to this newly discovered location
            try:
                npc_prompts = [
                    f"A local resident or guardian encountered at {new_location_name}",
                ]
                for prompt in npc_prompts:
                    new_npc = procedural_gen.generate_npc(prompt=prompt, language=getattr(self, "language", "ru"))
                    new_npc.current_scene = new_location_name
                    self._init_npc(new_npc)
                    self.logger.info(f"Generated location-pinned NPC: '{new_npc.name}' at '{new_location_name}'")
            except Exception as e:
                self.logger.warning(f"Could not generate NPCs for new location: {e}")
        else:
            self.logger.info(f"Loading existing visited location: '{new_location_name}'")
            if old_location and old_location != new_location_name:
                self.connect_locations(old_location, new_location_name)

        # Set as current
        self.current_location_name = new_location_name
        self.current_scene = self.all_locations[new_location_name]

        # Update all player character tokens to the new scene
        for player in self.players:
            if hasattr(player, 'character'):
                player.character.current_scene = new_location_name

        # Emit LOCATION_CHANGE event
        from core.schemas.orchestration import Event, EventTypes
        event_desc = f"Party traveled from '{old_location or 'Beginning'}' to '{new_location_name}'."
        loc_event = Event(
            event_type=EventTypes.LOCATION_CHANGE,
            event_initiator="Game Master",
            event_subject=new_location_name,
            description=event_desc
        )
        self.event_pool.add_event(loc_event)

        # Broadcast narrative update
        if self.delivery:
            if getattr(self, "language", "ru") == "ru":
                status_text = "исследовала новую область" if is_new_location else "вернулась в"
                broadcast_text = f"🗺️ **Отряд {status_text}: {new_location_name}!**\n\n*{self.current_scene.description}*"
            else:
                status_text = "discovered a new realm" if is_new_location else "returned to"
                broadcast_text = f"🗺️ **The party has {status_text}: {new_location_name}!**\n\n*{self.current_scene.description}*"

            self.delivery.master_message(
                text=broadcast_text,
                tag="location_change"
            )
            self.delivery.session_updated(self)

        # If in combat when changing locations, disengage and return to story mode
        if self.game_mode == GameModes.COMBAT:
            self.exit_combat(reason=f"Party transitioned to {new_location_name}")
        else:
            self._initialize_turn_queue()

        return self.current_scene

    def enter_combat(self, reason: Optional[str] = None) -> None:
        """
        Transition session from STORY mode to COMBAT mode.
        Initializes tactical turn queue, rolls initiative, and alerts players.
        """
        if self.game_mode == GameModes.COMBAT:
            return
        self.logger.info(f"⚔️ Transitioning to COMBAT mode. Reason: {reason or 'Hostilities initiated'}")
        self.game_mode = GameModes.COMBAT
        self._initialize_turn_queue()

        # Emit system event for history
        from core.schemas.orchestration import Event, EventTypes
        combat_event = Event(
            event_type=EventTypes.LOCATION_STATUS_CHANGE,
            event_initiator="Game Master",
            event_subject="COMBAT",
            description=f"⚔️ Combat begins: {reason or 'Hostilities have erupted.'}"
        )
        self.event_pool.add_event(combat_event)

        if self.delivery:
            if getattr(self, "language", "ru") == "ru":
                banner = (
                    "⚔️ **НАЧАЛО БОЯ!**\n\n"
                    "Обстановка накалилась до предела! Отряд переходит в пошаговый тактический бой. "
                    "Инициатива брошена — очередность действий определяется боевой шкалой."
                )
            else:
                banner = (
                    "⚔️ **COMBAT INITIATED!**\n\n"
                    "Tensions have broken into open battle! The session has entered turn-based tactical combat. "
                    "Initiative has been rolled and tactical turn order is now active."
                )
            self.delivery.master_message(text=banner, tag="combat_start")
            self.delivery.session_updated(self)

    def exit_combat(self, reason: Optional[str] = None) -> None:
        """
        Transition session from COMBAT mode back to STORY mode.
        Concludes combat, restores narrative exploration, and alerts players.
        """
        if self.game_mode == GameModes.STORY:
            return
        self.logger.info(f"🕊️ Transitioning to STORY mode. Reason: {reason or 'Combat concluded'}")
        self.game_mode = GameModes.STORY

        from core.schemas.orchestration import Event, EventTypes
        combat_end_event = Event(
            event_type=EventTypes.LOCATION_STATUS_CHANGE,
            event_initiator="Game Master",
            event_subject="STORY",
            description=f"🕊️ Combat concluded: {reason or 'All threats neutralized.'}"
        )
        self.event_pool.add_event(combat_end_event)

        if self.delivery:
            if getattr(self, "language", "ru") == "ru":
                banner = (
                    "🕊️ **БОЙ ЗАВЕРШЁН!**\n\n"
                    "Пыль сражения оседает, оружие опущено. Все враги повержены или бой утих. "
                    "Отряд возвращается в режим свободного сюжетного исследования."
                )
            else:
                banner = (
                    "🕊️ **COMBAT CONCLUDED!**\n\n"
                    "The dust settles and blades find their sheaths. All adversaries have been vanquished or fled. "
                    "Returning to open narrative exploration mode."
                )
            self.delivery.master_message(text=banner, tag="combat_end")
            self.delivery.session_updated(self)

    def set_game_mode(self, mode: GameModes | str, reason: Optional[str] = None) -> None:
        """Explicitly switch the session game mode between STORY and COMBAT."""
        mode_str = mode.value if hasattr(mode, 'value') else str(mode)
        if mode_str.upper() == "COMBAT":
            self.enter_combat(reason=reason or "Game mode switched to COMBAT")
        else:
            self.exit_combat(reason=reason or "Game mode switched to STORY")

    def _should_enter_combat(self) -> bool:
        """
        Check if any recent events or scene conditions warrant transitioning to COMBAT.
        Triggers when attacks or damage occur and there are living NPCs in the scene.
        """
        if self.game_mode == GameModes.COMBAT:
            return False

        living_scene_npcs = [
            n for n in self.npcs
            if getattr(n.character, 'is_alive', True)
            and getattr(n.character, 'current_hp', 1) > 0
            and getattr(n.character, 'current_scene', None) == self.current_location_name
        ]
        if not living_scene_npcs:
            return False

        from core.schemas.orchestration import EventTypes
        combat_event_types = {
            EventTypes.CHARACTER_MELEE_ATTACK,
            EventTypes.CHARACTER_RANGED_ATTACK,
        }
        recent_events = self.event_pool.get_events()[-10:] if hasattr(self.event_pool, 'get_events') else []
        for e in recent_events:
            etype = getattr(e, 'event_type', None)
            if etype in combat_event_types:
                return True
            desc = (getattr(e, 'description', '') or '').lower()
            if any(term in desc for term in ["takes damage", "attacks", "наносит урон", "атакует", "удар", "damage from"]):
                return True

        return False

    def _should_exit_combat(self) -> bool:
        """
        Check if combat should conclude because all hostile/adversary NPCs in the scene
        are dead or have fled.
        """
        if self.game_mode != GameModes.COMBAT:
            return False

        living_scene_npcs = [
            n for n in self.npcs
            if getattr(n.character, 'is_alive', True)
            and getattr(n.character, 'current_hp', 1) > 0
            and getattr(n.character, 'current_scene', None) == self.current_location_name
        ]
        return not living_scene_npcs

    def change_current_location(self, new_location_name: str, description: Optional[str] = None) -> bool:
        """Change the current location to the specified location, creating it if unvisited."""
        self.transition_to_location(new_location_name, description)
        return True

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

    
    def restore_session_from_serialized(self, save_data, dependencies=None):
        self.session_name = save_data["session_name"]
        self.language = save_data.get("language", "ru")
        self.collection_name = f"game_session_{self.session_name}"
        
        # Restore game mode
        self.game_mode = GameModes(save_data["game_mode"])
        
        # Restore spatial settings
        self.spatial_enabled = save_data.get("spatial_enabled", True)
        
        # Restore turn-based settings
        self.turn_time = save_data.get("turn_time", 0.0)
        self.turn_distance = save_data.get("turn_distance", 10)
        
        # Restore plot if available
        plot_data = save_data.get("plot")
        if plot_data:
            from core.magg.plot_schemas import Plot
            self._plot = Plot(**plot_data) # type: ignore
        else:
            self._plot = None

        # Set up dependencies if provided
        if dependencies:
            if 'orchestrator' in dependencies:
                self._orchestrator = dependencies['orchestrator']
            if 'event_pool' in dependencies:
                self.event_pool = dependencies['event_pool']
            if 'generator' in dependencies:
                self.generator = dependencies['generator']
            if 'chroma_client' in dependencies:
                self.chroma_client = dependencies['chroma_client']
            if 'logger' in dependencies:
                self.logger = dependencies['logger'].getChild("session")
            if 'delivery' in dependencies:
                self.delivery = dependencies['delivery']

        # Initialize Player objects for each character
        self.players = []
        raw_char_data = save_data.get("player_characters") or save_data.get("players") or []
        player_characters = [Character(**char_data) if isinstance(char_data, dict) else char_data for char_data in raw_char_data]
        for character in player_characters:
            # Need to ensure orchestrator is available
            if hasattr(self, '_orchestrator') and self._orchestrator is not None:
                player = self._init_player(character, self.orchestrator)
                self.players.append(player)
            else:
                raise ValueError("Orchestrator not available for initializing players during load")

        # Set the current scene first so NPCs can reference it
        if save_data.get("current_scene"):
            self.current_scene = SceneNode(**save_data["current_scene"])
        else:
            self.current_scene = None

        # Load NPCs
        self.npcs = []
        for npc_data in save_data.get("npcs", []):
            npc_character = NPCCharacter(**npc_data)
            npc = self._init_npc(npc_character)
            # Ensure NPC is assigned to the current scene if not already assigned
            if not npc.character.current_scene and self.current_scene:
                npc.character.current_scene = self.current_scene.name
            # Note: self._init_npc already appends to self.npcs
            
        # Load messages
        self.messages = []
        for message_data in save_data.get("messages", []):
            message = Message(**message_data)
            self.messages.append(message)
            
        # Restore location graph data
        # Convert lists back to sets
        self.location_graph = {
            k: set(v) for k, v in save_data.get("location_graph", {}).items()
        }
        self.all_locations = {}
        for name, scene_dict in save_data.get("all_locations", {}).items():
            self.all_locations[name] = SceneNode(**scene_dict)
        self.current_location_name = save_data.get("current_location_name")
        
        # Initialize round determinator after dependencies are set
        self._initialize_round_determinator()
        
        # Restore turn queue
        self.turn_queue = []
        for entity_data, time_added, next_turn in save_data.get("turn_queue", []):
            entity = self._deserialize_character_identifier(entity_data)
            if entity:
                self.turn_queue.append((entity, time_added, next_turn))

        # Re-initialize game master after loading
        from logging import Logger
        if hasattr(self, 'logger'):
            self._init_mage(self.logger)  # Reinitialize game master        

        return True        

    def load_session_from_save(self, filename: str, dependencies=None):
        """Loads session data from a JSON file.
        
        Args:
            filename: Path to the save file
            dependencies: Dictionary containing dependencies that need to be injected
                         (orchestrator, event_pool, generator, chroma_client, logger, delivery)
        """
        try:
            with open(filename, 'r', encoding="utf-8") as f:
                save_data = json.load(f)
            self.restore_session_from_serialized(save_data, dependencies)
            # Restore basic properties

            self.logger.info(f"Session loaded from {filename}")
        except FileNotFoundError:
            self.logger.error(f"Save file not found: {filename}")
        except Exception as e:
            self.logger.error(f"Error loading session: {e}")

    def _deserialize_character_identifier(self, entity_data):
        """Deserialize a character identifier from storage."""
        entity_type = entity_data["type"]
        
        if entity_type == "character":
            # Find the character by name in players or NPCs
            for player in self.players:
                if player.character.name == entity_data["name"]:
                    return player
            for npc in self.npcs:
                if npc.character.name == entity_data["name"]:
                    return npc
        elif entity_type == "round_determinator":
            # Return the round determinator instance
            # Make sure it's initialized
            if not hasattr(self, 'round_determinator') or self.round_determinator is None:
                self._initialize_round_determinator()
            return self.round_determinator
            
        return None


    def _add_round_determinator_to_turn_queue(self):
        time_added = self.turn_time 
        next_move_time = self.turn_time + max(1.0, float(ROUND_DURATION))
        self.turn_queue.append((self.round_determinator, time_added, next_move_time))
            
    def _add_character_to_turn_queue(self, char : NPC | Player | RoundDeterminator):
        if isinstance(char, RoundDeterminator):
            self._add_round_determinator_to_turn_queue()
        elif isinstance(char, (NPC, Player)):
            if char.character.is_alive:
                time_added = self.turn_time
                # Initiative determines slight offset within the round (higher initiative acts faster)
                init_val = max(0.0, float(getattr(char.character, 'initiative_bonus', 0) or 0))
                init_offset = max(1.0, float(ROUND_DURATION) - min(init_val, float(ROUND_DURATION) - 1.0))
                next_move_time = self.turn_time + init_offset
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

    def get_current_turn_character_name(self) -> Optional[str]:
        """Returns the character name whose turn it is in COMBAT mode."""
        mode_str = self.game_mode.value if hasattr(self.game_mode, 'value') else str(self.game_mode)
        if mode_str.upper() != "COMBAT" or not self.turn_queue:
            return None
        sorted_q = sorted(self.turn_queue, key=lambda a: a[2] if len(a) > 2 else 0)
        for entry in sorted_q:
            ent = entry[0]
            if hasattr(ent, 'character') and getattr(ent.character, 'is_alive', True):
                return ent.character.name
        return None

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


    def _print_turn_queue(self):
        """Print a beautiful and informative representation of the turn queue."""
        if not self.turn_queue:
            self.logger.debug("🕐 Turn Queue: Empty")
            return

        queue_log = ["🕐 TURN QUEUE:"]
        queue_log.append("┌─────────────────────────────────────────────────────────┐")

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
                queue_log.append(f"│ 🎯 NEXT: {char_type} {name:<20} │ Turn: {turn_time_str:>6} │")
            else:
                queue_log.append(f"│        {char_type} {name:<20} │ Turn: {turn_time_str:>6} │")

        queue_log.append("└─────────────────────────────────────────────────────────┘")
        queue_log.append(f"⏱️  Global Time: {self.turn_time:.2f}")
        
        self.logger.debug("\n".join(queue_log))
        
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
    
    def advance_plot_if_applicable(self, character=None) -> list:
        """
        Evaluate recent player actions and events against current chapter tasks.
        Advances tasks, triggers chapter completions, and broadcasts fanfare updates.
        """
        from core.magg.plot_schemas import ChapterStatus, generate_default_plot
        from core.schemas.orchestration import Event, EventTypes

        if self._plot is None:
            self._plot = generate_default_plot(self.session_name)

        current_chapter = self._plot.current_chapter
        if not current_chapter or not current_chapter.tasks:
            return []

        # Collect recent text from player actions and game messages
        recent_texts = []
        if character and getattr(character, '_input_cache', None):
            recent_texts.append(character._input_cache)
        if hasattr(self, 'messages') and self.messages:
            for m in self.messages[-5:]:
                if getattr(m, 'sender_name', '') != 'GM':
                    recent_texts.append(m.text)

        recent_corpus = " ".join(recent_texts).lower()
        if not recent_corpus.strip():
            return []

        advanced_events = []
        completed_any_task = False

        # Keyword dictionaries for intelligent intent matching
        intent_map = {
            "investigate": ["look", "search", "examine", "inspect", "check", "clue", "wall", "stone", "sarcophag", "secret", "trap", "door", "stair", "room", "chamber", "floor", "find", "explore", "scan", "sense", "peer", "survey"],
            "combat": ["attack", "fight", "strike", "kill", "guard", "skeleton", "undead", "enemy", "blade", "sword", "spell", "cast", "smite", "shoot", "hit", "damage", "defeat", "slay", "destroy", "subdue", "neutralize", "evade"],
            "puzzle": ["open", "gate", "door", "breach", "unseal", "lever", "key", "keystone", "rune", "inscript", "altar", "chest", "passage", "unlock", "enter", "portal", "decipher", "read", "interact", "pull", "push", "touch"],
        }

        for task_desc, is_done in list(current_chapter.tasks.items()):
            if is_done:
                continue

            t_lower = task_desc.lower()
            task_tokens = [w for w in t_lower.split() if len(w) > 3 and w not in ["with", "from", "that", "this", "into", "their", "have", "been", "where", "about", "leading", "needed", "order"]]

            # Check direct token hits
            direct_hits = sum(1 for tok in task_tokens if tok in recent_corpus)
            
            # Check intent category hits
            category_hit = False
            for cat, keywords in intent_map.items():
                task_matches_cat = any(kw in t_lower for kw in keywords)
                corpus_matches_cat = any(kw in recent_corpus for kw in keywords)
                if task_matches_cat and corpus_matches_cat:
                    category_hit = True
                    break

            if direct_hits >= 2 or (direct_hits >= 1 and category_hit):
                current_chapter.tasks[task_desc] = True
                completed_any_task = True
                self.logger.info(f"🏆 [QUEST] Task completed: '{task_desc}' in chapter '{current_chapter.name}'")

                # Master message fanfare
                if self.delivery:
                    self.delivery.master_message(
                        text=f"🏆 **Objective Completed:** *{task_desc}*",
                        tag="quest_update"
                    )

                event = Event(
                    event_type=EventTypes.SYSTEM,
                    event_initiator="Quest Master",
                    description=f"Objective Completed: {task_desc}"
                )
                self.event_pool.add_event(event)
                advanced_events.append(event)

        # Check if all tasks in chapter are completed
        if completed_any_task:
            all_done = all(status for status in current_chapter.tasks.values())
            if all_done:
                current_chapter.status = ChapterStatus.COMPLETED
                self.logger.info(f"🌟 [QUEST] Chapter completed: '{current_chapter.name}'")
                next_chapter = self._plot.current_chapter
                if next_chapter:
                    if self.delivery:
                        self.delivery.master_message(
                            text=f"🌟 **CHAPTER COMPLETED:** *{current_chapter.name}*!\n\n📜 **New Chapter Unlocked:** **{next_chapter.name}**\n*{next_chapter.description}*",
                            tag="chapter_advance"
                        )
                    self.event_pool.add_event(Event(
                        event_type=EventTypes.SYSTEM,
                        event_initiator="Quest Master",
                        description=f"Chapter Complete: {current_chapter.name}. Next chapter: {next_chapter.name}"
                    ))
                else:
                    if self.delivery:
                        self.delivery.master_message(
                            text=f"👑 **CAMPAIGN TRIUMPH:** All chapters conquered! You have triumphed over the perils of the realm!",
                            tag="campaign_complete"
                        )

        return advanced_events

    async def game_loop(self):
        self._initialize_turn_queue()
        while 1:
            self.logger.debug(f"Turn at turn_time {self.turn_time} starter.")
            try:
                # ── STORY mode: only process when player queues input ──────
                if self.game_mode == GameModes.STORY:
                    if self.delivery.has_requests():
                        self.logger.debug("[STORY] Player input available, processing...")
                        char_acting = self.delivery.choose_player(self)
                        handled_directly = char_acting.run_story()
                        self.logger.debug(f"[STORY] run_story() returned (handled_directly={handled_directly}), pool now has {self.event_pool.get_event_count()} events")

                        # NPCs in current location process event queue
                        for npc in self.npcs:
                            if (
                                npc.character.is_alive
                                and npc.character.current_scene == self.current_location_name
                                and npc.event_queue.size() > 0
                            ):
                                self.logger.debug(f"[STORY] Processing NPC {npc.character.name} in current location")
                                npc.run()

                        # Process events generated by the player action & NPC reactions (ONE round only)
                        # ONLY if the turn was not already handled directly (e.g. meta comment or clarification)
                        if not handled_directly:
                            magg_queue_size = self.game_master.event_queue.size()
                            if magg_queue_size > 0:
                                self.logger.debug(f"DM post-processing: {magg_queue_size} events for MAGG")
                                comment = await self.game_master.handle_events()
                                if comment:
                                    self.delivery.master_message(text=comment)
                        else:
                            # Clear old unhandled events so they don't fire unexpectedly later
                            self.game_master.event_queue.clear()

                        # Advance plot tasks & chapters based on player deeds
                        try:
                            self.advance_plot_if_applicable(char_acting)
                        except Exception as plot_err:
                            self.logger.warning(f"Error checking plot advancement: {plot_err}")

                        # Check if combat was initiated during this story turn
                        if self._should_enter_combat():
                            self.enter_combat(reason="Hostilities erupted in the scene.")

                        # Broadcast updated session state to frontend
                        self.delivery.session_updated(self)

                    # Idle until player provides new input — do NOT cycle turns
                    await asyncio.sleep(0.5)
                    continue

                # ── COMBAT mode: full turn-based cycle ─────────────────────
                # Check if all adversaries defeated before next turn
                if self._should_exit_combat():
                    self.exit_combat(reason="All hostile threats defeated.")
                    await asyncio.sleep(0.5)
                    continue

                char = self._get_next_character_turn()

                if isinstance(char, NPC):
                    if char.character.is_alive and char.character.current_scene == self.current_location_name:
                        char.run()
                    else:
                        self.logger.debug(f"Skipping NPC {char.character.name} not in current scene ({char.character.current_scene})")

                elif isinstance(char, Player):
                    if char.is_ai_controlled:
                        char.run()
                    else:
                        # Check if this player has queued input ready
                        has_input = self.delivery.has_request_from_player(char.character.name)
                        if not has_input:
                            # Notify frontend whose turn it is
                            if hasattr(self.delivery, '_broadcast_to_session'):
                                asyncio.create_task(self.delivery._broadcast_to_session({
                                    "type": "TURN_UPDATE",
                                    "active_player_name": char.character.name,
                                    "turn_queue": [
                                        {"character": c.character.name, "next_turn": nt}
                                        for c, _, nt in self.turn_queue if hasattr(c, 'character')
                                    ]
                                }))
                            # Wait for player input without discarding their turn
                            await asyncio.sleep(0.5)
                            self.turn_queue.insert(0, (char, self.turn_time, self.turn_time))
                            continue
                        char.run()

                elif isinstance(char, RoundDeterminator):
                    char.run()

                else:
                    raise ValueError(f"Unexpected object type {char.__class__.__name__}")

                # ── DM post-processing ──────────────────────────────────────
                magg_queue_size = self.game_master.event_queue.size()
                if magg_queue_size > 0:
                    self.logger.debug(f"DM post-processing: {magg_queue_size} events for MAGG")
                    comment = await self.game_master.handle_events()
                    if comment:
                        self.delivery.master_message(text=comment)

                # Check if combat concluded after turn resolution
                if self._should_exit_combat():
                    self.exit_combat(reason="All hostile threats defeated.")

                # Advance plot tasks & chapters in combat
                try:
                    self.advance_plot_if_applicable(char if isinstance(char, Player) else None)
                except Exception as plot_err:
                    self.logger.warning(f"Error checking plot advancement: {plot_err}")

                # Broadcast updated session state after each turn
                self.delivery.session_updated(self)

            except asyncio.CancelledError:
                self.logger.info("Game loop cancelled")
                break
            except KeyboardInterrupt:
                self.logger.info("Game loop was stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in game loop iteration: {e}", exc_info=True)
                if self.delivery:
                    try:
                        is_ru = getattr(self, "language", "ru") == "ru"
                        err_msg = (
                            "⚠️ *Эфир связи дрожит от магических помех (ошибка модели ИИ). Состояние игры стабилизировано.*"
                            if is_ru else
                            "⚠️ *The astral conduit fluctuates (AI service error). Game state has been stabilized.*"
                        )
                        self.delivery.master_message(text=err_msg, tag="error")
                        self.delivery.session_updated(self)
                    except Exception as b_err:
                        self.logger.debug(f"Could not broadcast loop error state: {b_err}")
                await asyncio.sleep(1.0)
    
    def get_messages_formatted(self) -> str:
        """Get all messages formatted as a single string."""
        formatted_messages = ""
        for msg in self.messages:
            formatted_messages += f"{msg.sender_name}: {msg.text}\n"
        return formatted_messages