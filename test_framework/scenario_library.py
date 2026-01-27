"""
Library of common test scenarios for the game.
"""

from typing import List
from game.engine import Session
from schemas.in_game import Character, NPCCharacter, SceneNode, Coordinate3D
from test_framework.session_builder import SessionBuilder


def create_combat_scenario(players: List[Character], enemies: List[NPCCharacter], 
                         scene_name: str = "Combat Arena", 
                         description: str = "A battlefield for testing combat mechanics.") -> Session:
    """Create a combat scenario with players and enemies."""
    scene = SceneNode(
        name=scene_name,
        description=description,
        center_position=Coordinate3D(x=0.0, y=0.0, z=0.0),
        dimensions=Coordinate3D(x=20.0, y=20.0, z=10.0),
        scale_unit="feet"
    )
    
    builder = SessionBuilder()
    for player in players:
        builder.add_character(player)
    for enemy in enemies:
        builder.add_npc(enemy)
    builder.with_scene(scene)
    builder.with_name("combat_scenario")
    
    return builder.build()


def create_social_scenario(players: List[Character], npcs: List[NPCCharacter], 
                         scene_name: str = "Tavern", 
                         description: str = "A tavern for testing social interactions.") -> Session:
    """Create a social scenario with players and NPCs."""
    scene = SceneNode(
        name=scene_name,
        description=description,
        center_position=Coordinate3D(x=0.0, y=0.0, z=0.0),
        dimensions=Coordinate3D(x=15.0, y=15.0, z=10.0),
        scale_unit="feet"
    )
    
    builder = SessionBuilder()
    for player in players:
        builder.add_character(player)
    for npc in npcs:
        builder.add_npc(npc)
    builder.with_scene(scene)
    builder.with_name("social_scenario")

    return builder.build()


def create_exploration_scenario(players: List[Character], npcs: List[NPCCharacter], 
                              scene_name: str = "Mysterious Cave", 
                              description: str = "A mysterious cave for testing exploration mechanics.") -> Session:
    """Create an exploration scenario with players and NPCs."""
    scene = SceneNode(
        name=scene_name,
        description=description,
        center_position=Coordinate3D(x=0.0, y=0.0, z=0.0),
        dimensions=Coordinate3D(x=30.0, y=30.0, z=15.0),
        scale_unit="feet"
    )
    
    builder = SessionBuilder()
    for player in players:
        builder.add_character(player)
    for npc in npcs:
        builder.add_npc(npc)
    builder.with_scene(scene)
    builder.with_name("exploration_scenario")

    return builder.build()


def create_empty_scenario(scene_name: str = "Empty Room", 
                        description: str = "An empty room for testing basic mechanics.") -> Session:
    """Create an empty scenario with just a scene."""
    scene = SceneNode(
        name=scene_name,
        description=description,
        center_position=Coordinate3D(x=0.0, y=0.0, z=0.0),
        dimensions=Coordinate3D(x=10.0, y=10.0, z=10.0),
        scale_unit="feet"
    )
    
    builder = SessionBuilder()
    builder.with_scene(scene)
    builder.with_name("empty_scenario")
    
    return builder.build()


def create_complex_scenario(
    players: List[Character], 
    friendly_npcs: List[NPCCharacter], 
    enemy_npcs: List[NPCCharacter],
    scene_name: str = "Complex Dungeon",
    description: str = "A complex dungeon with multiple factions."
) -> Session:
    """Create a complex scenario with players, friendly NPCs, and enemy NPCs."""
    scene = SceneNode(
        name=scene_name,
        description=description,
        center_position=Coordinate3D(x=0.0, y=0.0, z=0.0),
        dimensions=Coordinate3D(x=40.0, y=40.0, z=20.0),
        scale_unit="feet"
    )
    
    builder = SessionBuilder()
    for player in players:
        builder.add_character(player)
    for npc in friendly_npcs:
        builder.add_npc(npc)
    for enemy in enemy_npcs:
        builder.add_npc(enemy)
    builder.with_scene(scene)
    builder.with_name("complex_scenario")
    
    return builder.build()


# Predefined scenario constructors
def get_test_combat_session():
    """Get a pre-built combat test session."""
    from test_framework.character_library import get_test_hero, get_test_wizard
    from test_framework.npc_library import get_bandit_npc
    
    players = [get_test_hero(), get_test_wizard()]
    enemies = [get_bandit_npc()]
    
    return create_combat_scenario(players, enemies, 
                                "Forest Battle Ground", 
                                "A clearing in the forest where heroes meet bandits.")


def get_test_social_session():
    """Get a pre-built social test session."""
    from test_framework.character_library import get_test_hero
    from test_framework.npc_library import get_merchant_npc, get_friendly_villager_npc
    
    players = [get_test_hero()]
    npcs = [get_merchant_npc(), get_friendly_villager_npc()]
    
    return create_social_scenario(players, npcs, 
                                "Village Market", 
                                "A busy market square with merchants and villagers.")


def get_test_exploration_session():
    """Get a pre-built exploration test session."""
    from test_framework.character_library import get_test_hero, get_test_rogue
    from test_framework.npc_library import get_wise_old_man_npc
    
    players = [get_test_hero(), get_test_rogue()]
    npcs = [get_wise_old_man_npc()]
    
    return create_exploration_scenario(players, npcs, 
                                     "Ancient Temple", 
                                     "An ancient temple filled with mysteries and puzzles.")


def get_test_complex_session():
    """Get a pre-built complex test session."""
    from test_framework.character_library import get_test_hero, get_test_wizard
    from test_framework.npc_library import get_guard_npc, get_bandit_npc
    
    players = [get_test_hero(), get_test_wizard()]
    friendly_npcs = [get_guard_npc()]
    enemy_npcs = [get_bandit_npc()]
    
    return create_complex_scenario(players, friendly_npcs, enemy_npcs,
                                 "Town Under Siege",
                                 "A town being attacked where heroes must defend alongside guards against bandits.")