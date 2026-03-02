from sqlalchemy.orm import Session
from typing import List, Optional
import json

from server.src.models.character import CharacterModel
from server.src.schema.character import CharacterCreate, CharacterUpdate


def create_character(db: Session, character: CharacterCreate) -> CharacterModel:
    """Create a new character."""
    db_character = CharacterModel(
        user_id=character.user_id,
        name=character.name,
        race=character.race,
        char_class=character.char_class,
        level=character.level,
        backstory_summary=character.backstory_summary,
        personality_traits=character.personality_traits,
        max_hp=character.max_hp,
        current_hp=character.current_hp,
        armor_class=character.armor_class,
        speed=character.speed,
        stats=json.dumps(character.stats),
        abilities=json.dumps(character.abilities),
        inventory=json.dumps(character.inventory),
        position_x=0.0,
        position_y=0.0,
    )
    
    # Calculate bonuses
    db_character.proficiency_bonus = calculate_proficiency_bonus(character.level)
    db_character.initiative_bonus = calculate_initiative_bonus(character.stats.get("dexterity", 10))
    db_character.short_summary = f"{character.name} the {character.race} {character.char_class} (Lvl {character.level})"
    
    db.add(db_character)
    db.commit()
    db.refresh(db_character)
    return db_character


def get_character(db: Session, character_id: int) -> Optional[CharacterModel]:
    """Get a character by ID."""
    return db.query(CharacterModel).filter(CharacterModel.id == character_id).first()


def get_characters_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[CharacterModel]:
    """Get all characters for a user."""
    return db.query(CharacterModel).filter(CharacterModel.user_id == user_id).offset(skip).limit(limit).all()


def update_character(db: Session, character_id: int, character: CharacterUpdate) -> Optional[CharacterModel]:
    """Update a character."""
    db_character = get_character(db, character_id)
    if not db_character:
        return None
    
    update_data = character.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if field in ["stats", "abilities", "inventory", "active_conditions", "resources"]:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
        setattr(db_character, field, value)
    
    # Recalculate bonuses if needed
    if "level" in update_data:
        db_character.proficiency_bonus = calculate_proficiency_bonus(db_character.level)
    
    if "stats" in update_data:
        stats = json.loads(db_character.stats) if isinstance(db_character.stats, str) else db_character.stats
        dex = stats.get("dexterity", 10)
        db_character.initiative_bonus = calculate_initiative_bonus(dex)
    
    db_character.short_summary = f"{db_character.name} the {db_character.race} {db_character.char_class} (Lvl {db_character.level})"
    
    db.commit()
    db.refresh(db_character)
    return db_character


def delete_character(db: Session, character_id: int) -> bool:
    """Delete a character."""
    db_character = get_character(db, character_id)
    if not db_character:
        return False
    
    db.delete(db_character)
    db.commit()
    return True


def calculate_proficiency_bonus(level: int) -> int:
    """Calculate proficiency bonus based on level."""
    return 2 + (level - 1) // 4


def calculate_initiative_bonus(dexterity: int) -> int:
    """Calculate initiative bonus from dexterity."""
    return (dexterity - 10) // 2
