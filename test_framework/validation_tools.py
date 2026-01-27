"""
Validation tools for testing game sessions.
"""

from game.engine import Session
from schemas.in_game import Character, NPCCharacter, SceneNode
from typing import List, Dict, Any


def validate_session_structure(session: Session) -> Dict[str, Any]:
    """Validate the basic structure of a session."""
    result = {
        'session_name_valid': session.session_name is not None and len(session.session_name) > 0,
        'has_characters': len(session.player_characters) > 0,
        'has_npcs': len(session.npcs) > 0,
        'has_scene': session.current_scene is not None,
        'character_count': len(session.player_characters),
        'npc_count': len(session.npcs),
        'turn_queue_initialized': len(session.turn_queue) > 0 if hasattr(session, 'turn_queue') else False
    }
    
    return result


def validate_character_attributes(character: Character) -> Dict[str, Any]:
    """Validate the attributes of a character."""
    result = {
        'name_valid': character.name is not None and len(character.name) > 0,
        'hp_valid': character.current_hp <= character.max_hp and character.current_hp >= 0,
        'abilities_valid': (
            1 <= character.abilities.strength <= 30 and
            1 <= character.abilities.dexterity <= 30 and
            1 <= character.abilities.constitution <= 30 and
            1 <= character.abilities.intelligence <= 30 and
            1 <= character.abilities.wisdom <= 30 and
            1 <= character.abilities.charisma <= 30
        ),
        'level_valid': character.level >= 1,
        'position_valid': hasattr(character, 'position'),
        'has_position': character.position is not None
    }
    
    return result


def validate_npc_attributes(npc) -> Dict[str, Any]:
    """Validate the attributes of an NPC."""
    # The npc parameter is likely an NPC object from npcs.npc module, not NPCCharacter
    # Access the actual NPCCharacter through the character attribute
    npc_character = npc.character if hasattr(npc, 'character') else npc

    result = {
        'name_valid': npc_character.name is not None and len(npc_character.name) > 0,
        'hp_valid': npc_character.current_hp <= npc_character.max_hp and npc_character.current_hp >= 0,
        'abilities_valid': (
            1 <= npc_character.abilities.strength <= 30 and
            1 <= npc_character.abilities.dexterity <= 30 and
            1 <= npc_character.abilities.constitution <= 30 and
            1 <= npc_character.abilities.intelligence <= 30 and
            1 <= npc_character.abilities.wisdom <= 30 and
            1 <= npc_character.abilities.charisma <= 30
        ),
        'level_valid': npc_character.level >= 1,
        'position_valid': hasattr(npc_character, 'position'),
        'has_position': npc_character.position is not None,
        'has_motivation': npc_character.motivation is not None,
        'has_memory': npc_character.memory is not None,
        'has_current_scene': hasattr(npc_character, 'current_scene') and npc_character.current_scene is not None
    }

    return result


def validate_scene_attributes(scene: SceneNode) -> Dict[str, Any]:
    """Validate the attributes of a scene."""
    result = {
        'name_valid': scene.name is not None and len(scene.name) > 0,
        'description_valid': scene.description is not None and len(scene.description) > 0,
        'position_valid': hasattr(scene, 'center_position'),
        'dimensions_valid': hasattr(scene, 'dimensions'),
        'has_center_position': scene.center_position is not None,
        'has_dimensions': scene.dimensions is not None
    }
    
    return result


def validate_session_characters(session: Session) -> Dict[str, Any]:
    """Validate all characters in a session."""
    results = {
        'total_characters': len(session.player_characters),
        'valid_characters': 0,
        'invalid_characters': [],
        'character_details': []
    }
    
    for i, character in enumerate(session.player_characters):
        validation = validate_character_attributes(character)
        results['character_details'].append({
            'index': i,
            'name': character.name,
            'validation': validation
        })
        
        if all(validation.values()):
            results['valid_characters'] += 1
        else:
            results['invalid_characters'].append(i)
    
    return results


def validate_session_npcs(session: Session) -> Dict[str, Any]:
    """Validate all NPCs in a session."""
    results = {
        'total_npcs': len(session.npcs),
        'valid_npcs': 0,
        'invalid_npcs': [],
        'npc_details': []
    }
    
    for i, npc in enumerate(session.npcs):
        validation = validate_npc_attributes(npc)
        results['npc_details'].append({
            'index': i,
            'name': npc.character.name,
            'validation': validation
        })
        
        if all(validation.values()):
            results['valid_npcs'] += 1
        else:
            results['invalid_npcs'].append(i)
    
    return results


def validate_session_scene(session: Session) -> Dict[str, Any]:
    """Validate the scene in a session."""
    if not session.current_scene:
        return {'error': 'No scene in session'}
    
    validation = validate_scene_attributes(session.current_scene)
    return {
        'scene_validation': validation,
        'is_valid': all(validation.values())
    }


def validate_complete_session(session: Session) -> Dict[str, Any]:
    """Complete validation of a session."""
    session_validation = validate_session_structure(session)
    character_validation = validate_session_characters(session)
    npc_validation = validate_session_npcs(session)
    scene_validation = validate_session_scene(session)
    
    overall_valid = (
        session_validation['session_name_valid'] and
        session_validation['has_characters'] and
        session_validation['has_scene'] and
        character_validation['valid_characters'] == character_validation['total_characters'] and
        npc_validation['valid_npcs'] == npc_validation['total_npcs'] and
        scene_validation.get('is_valid', False)
    )
    
    return {
        'session_structure': session_validation,
        'character_validation': character_validation,
        'npc_validation': npc_validation,
        'scene_validation': scene_validation,
        'overall_valid': overall_valid
    }


def print_validation_report(report: Dict[str, Any], indent: int = 0):
    """Print a formatted validation report."""
    spaces = "  " * indent
    
    for key, value in report.items():
        if isinstance(value, dict):
            print(f"{spaces}{key}:")
            print_validation_report(value, indent + 1)
        elif isinstance(value, list):
            print(f"{spaces}{key}: {len(value)} items")
            if value and isinstance(value[0], dict) and 'validation' in value[0]:
                for item in value[:3]:  # Show first 3 items
                    print(f"{spaces}  - {item.get('name', 'Unknown')} (index {item.get('index', 'N/A')})")
                    print_validation_report(item['validation'], indent + 2)
        else:
            status = "✓" if value is True else "✗" if value is False else ""
            print(f"{spaces}{key}: {value} {status}")