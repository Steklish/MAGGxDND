"""
Character Profile to In-Game Character Converter

Converts saved CharacterProfile database models to in-game Character objects
that can be used during active game sessions.
"""
import json
import logging
from typing import Optional, Dict, Any

from core.schemas.in_game import (
    Character,
    CharacterClass,
    AbilityScores,
    Coordinate2D,
    Condition,
    SpellAbility,
    UnifiedObject,
    ObjectType
)
from backend.src.models.character_profile import CharacterProfile

logger = logging.getLogger(__name__)


def profile_to_character(
    profile: CharacterProfile,
    position: Optional[Coordinate2D] = None
) -> Character:
    """
    Convert a CharacterProfile to an in-game Character object.

    Args:
        profile: The saved character profile from database
        position: Optional 2D position for the character (defaults to 0,0)

    Returns:
        Character object ready for use in a game session
    """
    # Parse character_data if it exists, otherwise use defaults
    character_data = profile.character_data or {}

    # Extract ability scores
    stats = character_data.get('stats', {})
    ability_scores = AbilityScores(
        strength=stats.get('strength', 10),
        dexterity=stats.get('dexterity', 10),
        constitution=stats.get('constitution', 10),
        intelligence=stats.get('intelligence', 10),
        wisdom=stats.get('wisdom', 10),
        charisma=stats.get('charisma', 10)
    )

    # Parse personality traits
    personality_traits = []
    if profile.personality_traits:
        if isinstance(profile.personality_traits, str):
            try:
                personality_traits = json.loads(profile.personality_traits)
                if isinstance(personality_traits, dict):
                    # Convert dict to list of formatted strings
                    traits_list = []
                    for key, value in personality_traits.items():
                        if value:
                            traits_list.append(f"{key}: {value}")
                    personality_traits = traits_list
                elif not isinstance(personality_traits, list):
                    personality_traits = [str(personality_traits)]
            except (json.JSONDecodeError, TypeError):
                personality_traits = [profile.personality_traits]
        elif isinstance(profile.personality_traits, list):
            personality_traits = profile.personality_traits

    # Parse inventory from character_data
    inventory_data = character_data.get('inventory', [])
    inventory = []
    for item in inventory_data:
        if isinstance(item, str):
            # Create simple UnifiedObject from item name
            inventory.append(UnifiedObject(
                id=f"item_{item.lower().replace(' ', '_')}",
                name=item,
                description=f"A {item.lower()}",
                obj_type=ObjectType.OTHER,
                quantity=1
            ))
        elif isinstance(item, dict):
            # Convert dict to UnifiedObject
            try:
                inventory.append(UnifiedObject(**item))
            except Exception as e:
                logger.warning(f"Failed to parse inventory item: {e}")

    # Parse abilities/spells from character_data
    abilities_data = character_data.get('abilities', [])
    if isinstance(abilities_data, list):
        abilities = []
        for ability in abilities_data:
            if isinstance(ability, str):
                abilities.append(ability)
            elif isinstance(ability, dict):
                try:
                    abilities.append(SpellAbility(**ability))
                except Exception as e:
                    logger.warning(f"Failed to parse ability: {e}")
                    abilities.append(ability.get('name', 'Unknown'))
    else:
        abilities = abilities_data if isinstance(abilities_data, list) else []

    # Parse conditions from character_data
    conditions_data = character_data.get('conditions', [])
    conditions = []
    for condition in conditions_data:
        if isinstance(condition, dict):
            try:
                conditions.append(Condition(**condition))
            except Exception as e:
                logger.warning(f"Failed to parse condition: {e}")

    # Map character class string to enum
    char_class = CharacterClass.FIGHTER  # default
    class_name = profile.char_class.lower() if profile.char_class else ''
    class_mapping = {
        'barbarian': CharacterClass.BARBARIAN,
        'bard': CharacterClass.BARD,
        'cleric': CharacterClass.CLERIC,
        'druid': CharacterClass.DRUID,
        'fighter': CharacterClass.FIGHTER,
        'monk': CharacterClass.MONK,
        'paladin': CharacterClass.PALADIN,
        'ranger': CharacterClass.RANGER,
        'rogue': CharacterClass.ROGUE,
        'sorcerer': CharacterClass.SORCERER,
        'warlock': CharacterClass.WARLOCK,
        'wizard': CharacterClass.WIZARD,
    }
    if class_name in class_mapping:
        char_class = class_mapping[class_name]

    # Build character object
    character = Character(
        name=profile.name,
        race=profile.race,
        char_class=char_class,
        level=profile.level,
        backstory_summary=profile.backstory_summary or f"A {profile.race} {profile.char_class} seeking adventure",
        personality_traits=personality_traits,
        max_hp=profile.max_hp,
        current_hp=profile.max_hp,  # Start at full HP
        temp_hp=0,
        armor_class=profile.armor_class,
        speed=profile.speed,
        ability_scores=ability_scores,
        inventory=inventory,
        conditions=conditions,
        position=position or Coordinate2D(x=0, y=0),
        abilities=abilities
    )

    logger.info(f"Converted profile '{profile.name}' (ID: {profile.id}) to Character object")
    return character


def characters_from_profiles(
    profiles: list[CharacterProfile],
    positions: Optional[list[Coordinate2D]] = None
) -> list[Character]:
    """
    Convert multiple CharacterProfiles to Character objects.

    Args:
        profiles: List of character profiles
        positions: Optional list of positions (one per character)

    Returns:
        List of Character objects
    """
    characters = []
    for i, profile in enumerate(profiles):
        position = None
        if positions and i < len(positions):
            position = positions[i]
        characters.append(profile_to_character(profile, position))
    return characters
