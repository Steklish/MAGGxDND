"""
Character Profile Repository

Handles CRUD operations for user's saved character profiles.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.src.models.character_profile import CharacterProfile


class CharacterProfileRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: int,
        name: str,
        race: str,
        char_class: str,
        character_data: Optional[Dict[str, Any]] = None,
        backstory_summary: Optional[str] = None,
        personality_traits: Optional[list] = None,
        appearance_description: Optional[str] = None,
        background: Optional[str] = None,
        alignment: Optional[str] = None,
        max_hp: int = 10,
        armor_class: int = 10,
        speed: int = 30,
        is_favorite: bool = False
    ) -> CharacterProfile:
        """Create a new character profile."""
        profile = CharacterProfile(
            user_id=user_id,
            name=name,
            race=race,
            char_class=char_class,
            character_data=character_data,
            backstory_summary=backstory_summary,
            personality_traits=personality_traits,
            appearance_description=appearance_description,
            background=background,
            alignment=alignment,
            max_hp=max_hp,
            armor_class=armor_class,
            speed=speed,
            is_favorite=is_favorite
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def get_by_id(self, profile_id: int, user_id: int) -> Optional[CharacterProfile]:
        """Get character profile by ID, ensuring it belongs to the user."""
        return self.db.query(CharacterProfile).filter(
            CharacterProfile.id == profile_id,
            CharacterProfile.user_id == user_id
        ).first()

    def get_by_user(self, user_id: int, skip: int = 0, limit: int = 50) -> List[CharacterProfile]:
        """Get all character profiles for a user."""
        return (
            self.db.query(CharacterProfile)
            .filter(CharacterProfile.user_id == user_id)
            .order_by(CharacterProfile.is_favorite.desc(), CharacterProfile.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update(
        self,
        profile_id: int,
        user_id: int,
        **kwargs
    ) -> Optional[CharacterProfile]:
        """Update a character profile."""
        profile = self.get_by_id(profile_id, user_id)
        if not profile:
            return None

        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        profile.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def delete(self, profile_id: int, user_id: int) -> bool:
        """Delete a character profile."""
        profile = self.get_by_id(profile_id, user_id)
        if not profile:
            return False

        self.db.delete(profile)
        self.db.commit()
        return True
