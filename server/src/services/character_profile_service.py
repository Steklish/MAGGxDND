from sqlalchemy.orm import Session
from typing import Optional
import json
from datetime import datetime

from server.src.models.character_profile import CharacterProfile
from server.src.schema.character_profile import CharacterProfileCreate, CharacterProfileUpdate


def get_by_character_id(db: Session, character_id: int) -> Optional[CharacterProfile]:
    """Get profile by character ID."""
    return db.query(CharacterProfile).filter(CharacterProfile.character_id == character_id).first()


def create_profile(db: Session, profile: CharacterProfileCreate) -> CharacterProfile:
    """Create a new character profile."""
    db_profile = CharacterProfile(
        character_id=profile.character_id,
        alignment=profile.alignment,
        deity=profile.deity,
        homeland=profile.homeland,
        background=profile.background,
        appearance_description=profile.appearance_description,
        hit_dice=profile.hit_dice,
        proficiency_bonus=profile.proficiency_bonus,
        inspiration=profile.inspiration,
        passive_wisdom=profile.passive_wisdom,
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile


def update_profile(db: Session, profile_id: int, profile: CharacterProfileUpdate) -> Optional[CharacterProfile]:
    """Update a character profile."""
    db_profile = db.query(CharacterProfile).filter(CharacterProfile.id == profile_id).first()
    if not db_profile:
        return None
    
    update_data = profile.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if field in ["saving_throws", "skills", "attacks", "spell_slots", "equipment", "features_traits"]:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
        setattr(db_profile, field, value)
    
    db_profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_profile)
    return db_profile


def update_by_character_id(db: Session, character_id: int, profile: CharacterProfileUpdate) -> Optional[CharacterProfile]:
    """Update character profile by character ID."""
    db_profile = get_by_character_id(db, character_id)
    if not db_profile:
        # Create if doesn't exist
        create_data = CharacterProfileCreate(character_id=character_id)
        db_profile = create_profile(db, create_data)
    
    update_data = profile.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if field in ["saving_throws", "skills", "attacks", "spell_slots", "equipment", "features_traits"]:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
        setattr(db_profile, field, value)
    
    db_profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_profile)
    return db_profile
