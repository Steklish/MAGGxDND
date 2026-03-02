from sqlalchemy import Integer, String, ForeignKey, Text, Boolean, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from typing import List, Optional

from server.src.database.base import Base


class CharacterProfile(Base):
    """Extended character profile with D&D specific details."""
    __tablename__ = "character_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), index=True)
    
    # Visual Appearance
    portrait_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    background_image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    appearance_description: Mapped[Optional[str]] = mapped_column(Text, default="")
    
    # D&D Core Details
    alignment: Mapped[str] = mapped_column(String, default="True Neutral")
    deity: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    homeland: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    background: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Combat Stats
    hit_dice: Mapped[str] = mapped_column(String, default="1d10")
    proficiency_bonus: Mapped[int] = mapped_column(Integer, default=2)
    inspiration: Mapped[bool] = mapped_column(Boolean, default=False)
    passive_wisdom: Mapped[int] = mapped_column(Integer, default=10)
    
    # Saving Throws (stored as JSON)
    saving_throws: Mapped[str] = mapped_column(Text, default='{"str": 0, "dex": 0, "con": 0, "int": 0, "wis": 0, "cha": 0}')
    
    # Skills (stored as JSON)
    skills: Mapped[str] = mapped_column(Text, default='{"acrobatics": 0, "animal_handling": 0, "arcana": 0, "athletics": 0, "deception": 0, "history": 0, "insight": 0, "intimidation": 0, "investigation": 0, "medicine": 0, "nature": 0, "perception": 0, "performance": 0, "persuasion": 0, "religion": 0, "sleight_of_hand": 0, "stealth": 0, "survival": 0}')
    
    # Attacks & Spellcasting
    attacks: Mapped[str] = mapped_column(Text, default="[]")
    spell_slots: Mapped[str] = mapped_column(Text, default='{"lvl1": 0, "lvl2": 0, "lvl3": 0, "lvl4": 0, "lvl5": 0, "lvl6": 0, "lvl7": 0, "lvl8": 0, "lvl9": 0}')
    
    # Equipment & Features
    equipment: Mapped[str] = mapped_column(Text, default="[]")
    features_traits: Mapped[str] = mapped_column(Text, default="[]")
    
    # Notes & Journals
    notes: Mapped[Optional[str]] = mapped_column(Text, default="")
    journal: Mapped[Optional[str]] = mapped_column(Text, default="")
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    character = relationship("CharacterModel", back_populates="profile")


# Update CharacterModel to include profile relationship
# This will be done in the character model file
