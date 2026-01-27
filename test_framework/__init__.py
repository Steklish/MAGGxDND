"""
Main test framework module for the game.
"""

from test_framework.character_library import *
from test_framework.npc_library import *
from test_framework.session_builder import *
from test_framework.scenario_library import *
from test_framework.validation_tools import *

# Import all necessary components for easy access
__all__ = [
    # Character library
    'get_test_hero',
    'get_test_wizard', 
    'get_test_rogue',
    'get_test_cleric',
    'get_custom_character',
    
    # NPC library
    'get_guard_npc',
    'get_merchant_npc',
    'get_bandit_npc',
    'get_wise_old_man_npc',
    'get_friendly_villager_npc',
    'get_custom_npc',
    
    # Session builder
    'SessionBuilder',
    'create_basic_test_session',
    
    # Scenario library
    'create_combat_scenario',
    'create_social_scenario',
    'create_exploration_scenario',
    'create_empty_scenario',
    'create_complex_scenario',
    'get_test_combat_session',
    'get_test_social_session',
    'get_test_exploration_session',
    'get_test_complex_session',
    
    # Validation tools
    'validate_session_structure',
    'validate_character_attributes',
    'validate_npc_attributes',
    'validate_scene_attributes',
    'validate_session_characters',
    'validate_session_npcs',
    'validate_session_scene',
    'validate_complete_session',
    'print_validation_report'
]


def run_sample_test():
    """Run a sample test to demonstrate the framework."""
    print("Running Sample Test with Test Framework...")
    
    # Create a basic test session
    session = create_basic_test_session()
    
    print(f"Created session: {session.session_name}")
    print(f"Characters: {len(session.player_characters)}")
    print(f"NPCs: {len(session.npcs)}")
    print(f"Scene: {session.current_scene.name if session.current_scene else 'None'}")
    
    # Validate the session
    validation_report = validate_complete_session(session)
    print("\nValidation Report:")
    print_validation_report(validation_report)
    
    return session


if __name__ == "__main__":
    run_sample_test()