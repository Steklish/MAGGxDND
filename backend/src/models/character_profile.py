"""
User Character Profile Model

Stores user's pre-created characters in the database for reuse across sessions.
Characters are saved as complete JSON blobs for flexibility.
"""
from sqlalchemy import Integer, String, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from backend.src.database.base import Base


class CharacterProfile(Base):
    """
    A user's saved character template that can be reused across sessions.
    Stores the complete character data as JSON for maximum flexibility.
    """
    __tablename__ = "character_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    
    # Character identity
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    race: Mapped[str] = mapped_column(String(50), nullable=False, default="Human")
    char_class: Mapped[str] = mapped_column(String(50), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1)
    
    # Character data stored as JSON (full D&D character sheet)
    character_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Descriptive fields
    backstory_summary: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    personality_traits: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    appearance_description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    background: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    alignment: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Computed stats (cached for quick access without parsing JSON)
    max_hp: Mapped[int] = mapped_column(Integer, default=10)
    armor_class: Mapped[int] = mapped_column(Integer, default=10)
    speed: Mapped[int] = mapped_column(Integer, default=30)
    
    # Metadata
    is_favorite: Mapped[bool] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="character_profiles")


# Add relationship to User model
from backend.src.models.user import User
User.character_profiles = relationship("CharacterProfile", back_populates="user", cascade="all, delete-orphan")
