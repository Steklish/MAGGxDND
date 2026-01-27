"""
Session builder for creating test sessions with predefined or custom configurations.
"""

from typing import List
from game.engine import Session
from game.event_pool import EventPool
from game.orchestrator import Orchestrator
from schemas.in_game import Character, NPCCharacter, SceneNode, Coordinate3D
from skls_generator.generator import Generator
from skls_generator.gen_backends.google_gen import GoogleGenAI
from skls_core.logging import get_skls_logger
from skls_embeddings.chroma_client import ChromaClient
from skls_embeddings.embedding_client import EmbeddingClient
import os


class SessionBuilder:
    """A builder class for creating test sessions with predefined or custom configurations."""
    
    def __init__(self):
        self.session_name = "test_session"
        self.chroma_client = None
        self.logger = get_skls_logger(__name__)
        self.logger.setLevel("DEBUG")
        self.generator = None
        self.event_pool = EventPool()
        self.player_characters = []
        self.npcs = []
        self.scene = None
        self.api_key = os.getenv("GEMINI_API_KEY")

        # Initialize generator if API key is available
        if self.api_key:
            try:
                embedding_client = EmbeddingClient()
                self.chroma_client = ChromaClient(embedding_client, self.logger) # type: ignore
                self.generator = Generator(GoogleGenAI(self.api_key), logger_instance=self.logger)
            except Exception as e:
                self.logger.warning(f"Could not initialize ChromaDB: {e}. Using mock generator.")
                self.generator = self._create_mock_generator()
        else:
            # Create a mock generator for testing without API key
            self.generator = self._create_mock_generator()
    
    def _create_mock_generator(self):
        """Create a mock generator for testing without API key."""
        from schemas.orchestration import EventList
        from schemas.in_game import SceneNode, Coordinate3D

        class MockGenerator:
            def generate_one_shot(self, pydantic_model, prompt):
                # For testing purposes, return appropriate mock objects based on the model
                if "EventList" in str(pydantic_model):
                    return EventList(event_list=[])
                elif "SceneNode" in str(pydantic_model):
                    return SceneNode(
                        name="Mock Scene",
                        description="A scene generated for testing purposes.",
                        center_position=Coordinate3D(x=0.0, y=0.0, z=0.0),
                        dimensions=Coordinate3D(x=10.0, y=10.0, z=10.0),
                        scale_unit="feet"
                    )
                elif "CharacterTransferDecision" in str(pydantic_model):
                    from schemas.orchestration import CharacterTransferDecision
                    return CharacterTransferDecision(
                        will_transfer=False,
                        transfer_breakdowns=[],
                        new_location_description="",
                        connection_reason=""
                    )
                elif "NPCTransferDecision" in str(pydantic_model):
                    from schemas.orchestration import NPCTransferDecision
                    return NPCTransferDecision(
                        will_transfer=False,
                        transfer_breakdowns=[],
                        new_location_description="",
                        connection_reason=""
                    )
                else:
                    # Return None for other types
                    return None
        return MockGenerator()
    
    def with_name(self, name: str):
        """Set the session name."""
        self.session_name = name
        return self
    
    def with_chroma_client(self, chroma_client):
        """Set the chroma client."""
        self.chroma_client = chroma_client
        return self
    
    def with_logger(self, logger):
        """Set the logger."""
        self.logger = logger
        return self
    
    def with_generator(self, generator):
        """Set the generator."""
        self.generator = generator
        return self
    
    def with_event_pool(self, event_pool: EventPool):
        """Set the event pool."""
        self.event_pool = event_pool
        return self
    
    def with_characters(self, characters: List[Character]):
        """Set the player characters."""
        self.player_characters = characters
        return self
    
    def with_npcs(self, npcs: List[NPCCharacter]):
        """Set the NPCs."""
        self.npcs = npcs
        return self
    
    def with_scene(self, scene: SceneNode):
        """Set the scene."""
        self.scene = scene
        return self
    
    def add_character(self, character: Character):
        """Add a single player character."""
        self.player_characters.append(character)
        return self
    
    def add_npc(self, npc: NPCCharacter):
        """Add a single NPC."""
        self.npcs.append(npc)
        return self
    
    def build(self) -> Session:
        """Build and return the session."""
        if not self.generator:
            raise ValueError("Generator is required to build a session")
        
        session = Session(
            session_name=self.session_name,
            chroma_client=self.chroma_client if self.chroma_client is not None else None, # type: ignore
            logger=self.logger,
            generator=self.generator,  # type: ignore
            event_pool=self.event_pool
        )
        
        # Initialize orchestrator
        orchestrator = Orchestrator(
            generator=self.generator, # type: ignore
            logger=self.logger
        )
        orchestrator.add_state(session)
        session._init_orchestrator(orchestrator)
        
        # Initialize the session if scene and characters are provided
        if self.scene and (self.player_characters or self.npcs):
            session.init_new_session(
                scene=self.scene,
                player_characters=self.player_characters,
                npcs=self.npcs
            )
        
        return session
    
    @classmethod
    def create_combat_scenario(cls, num_players: int = 2, num_enemies: int = 3):
        """Create a pre-configured combat scenario."""
        from test_framework.character_library import get_test_hero, get_test_wizard
        from test_framework.npc_library import get_bandit_npc
        
        builder = cls()
        builder.with_name("combat_test_session")
        
        # Add player characters
        for i in range(num_players):
            if i % 2 == 0:
                char = get_test_hero()
                char.name = f"Hero_{i+1}"
            else:
                char = get_test_wizard()
                char.name = f"Wizard_{i+1}"
            builder.add_character(char)
        
        # Add enemy NPCs
        for i in range(num_enemies):
            npc = get_bandit_npc()
            npc.name = f"Bandit_{i+1}"
            builder.add_npc(npc)
        
        # Create a combat scene
        scene = SceneNode(
            name="Forest Clearing",
            description="A small clearing in the forest where a battle is about to unfold.",
            center_position=Coordinate3D(x=0.0, y=0.0, z=0.0),
            dimensions=Coordinate3D(x=20.0, y=20.0, z=10.0),
            scale_unit="feet"
        )
        builder.with_scene(scene)
        
        return builder
    
    @classmethod
    def create_social_scenario(cls, num_players: int = 1, num_npcs: int = 2):
        """Create a pre-configured social scenario."""
        from test_framework.character_library import get_test_hero
        from test_framework.npc_library import get_merchant_npc, get_friendly_villager_npc
        
        builder = cls()
        builder.with_name("social_test_session")
        
        # Add player character
        for i in range(num_players):
            char = get_test_hero()
            char.name = f"Player_{i+1}"
            builder.add_character(char)
        
        # Add NPCs
        if num_npcs > 0:
            npc = get_merchant_npc()
            npc.name = "Merchant_Tom"
            builder.add_npc(npc)
        
        if num_npcs > 1:
            npc = get_friendly_villager_npc()
            npc.name = "Villager_Mary"
            builder.add_npc(npc)
        
        # Create a social scene
        scene = SceneNode(
            name="Village Square",
            description="A bustling village square with shops and people going about their daily business.",
            center_position=Coordinate3D(x=0.0, y=0.0, z=0.0),
            dimensions=Coordinate3D(x=30.0, y=30.0, z=10.0),
            scale_unit="feet"
        )
        builder.with_scene(scene)
        
        return builder
    
    @classmethod
    def create_exploration_scenario(cls, num_players: int = 1):
        """Create a pre-configured exploration scenario."""
        from test_framework.character_library import get_test_hero, get_test_wizard, get_test_rogue
        from test_framework.npc_library import get_wise_old_man_npc
        
        builder = cls()
        builder.with_name("exploration_test_session")
        
        # Add diverse player characters
        builder.add_character(get_test_hero())
        builder.add_character(get_test_wizard())
        builder.add_character(get_test_rogue())
        
        # Add a quest-giving NPC
        npc = get_wise_old_man_npc()
        npc.name = "Elder_Thaddeus"
        builder.add_npc(npc)
        
        # Create an exploration scene
        scene = SceneNode(
            name="Ancient Ruins",
            description="Ancient stone ruins covered in moss and mystery. Strange symbols are carved into the walls.",
            center_position=Coordinate3D(x=0.0, y=0.0, z=0.0),
            dimensions=Coordinate3D(x=50.0, y=50.0, z=20.0),
            scale_unit="feet"
        )
        builder.with_scene(scene)
        
        return builder


def create_basic_test_session():
    """Create a basic test session with default characters and scene."""
    from test_framework.character_library import get_test_hero
    from test_framework.npc_library import get_guard_npc
    
    scene = SceneNode(
        name="Test Chamber",
        description="A simple chamber for testing game mechanics.",
        center_position=Coordinate3D(x=0.0, y=0.0, z=0.0),
        dimensions=Coordinate3D(x=10.0, y=10.0, z=10.0),
        scale_unit="feet"
    )
    
    builder = SessionBuilder()
    builder.with_name("basic_test_session")
    builder.add_character(get_test_hero())
    builder.add_npc(get_guard_npc())
    builder.with_scene(scene)
    
    return builder.build()