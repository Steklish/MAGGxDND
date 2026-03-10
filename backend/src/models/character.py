from sqlalchemy import Integer, String, ForeignKey, Text, Float, Boolean, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List, Optional
import json

from backend.src.database.base import Base


class CharacterModel(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    # Basic Info
    name: Mapped[str] = mapped_column(String, nullable=False)
    race: Mapped[str] = mapped_column(String, default="Human")
    char_class: Mapped[str] = mapped_column(String, default="Fighter")
    level: Mapped[int] = mapped_column(Integer, default=1)
    backstory_summary: Mapped[str] = mapped_column(Text, default="")
    personality_traits: Mapped[str] = mapped_column(String, default="")  # Stored as JSON array
    
    # Vitals
    max_hp: Mapped[int] = mapped_column(Integer, default=30)
    current_hp: Mapped[int] = mapped_column(Integer, default=30)
    temp_hp: Mapped[int] = mapped_column(Integer, default=0)
    armor_class: Mapped[int] = mapped_column(Integer, default=12)
    speed: Mapped[int] = mapped_column(Integer, default=30)
    
    # Stats (stored as JSON)
    stats: Mapped[str] = mapped_column(Text, default='{"strength": 15, "dexterity": 12, "constitution": 14, "intelligence": 10, "wisdom": 10, "charisma": 10}')
    
    # Inventory (stored as JSON)
    inventory: Mapped[str] = mapped_column(Text, default="[]")
    
    # Abilities (stored as JSON)
    abilities: Mapped[str] = mapped_column(Text, default="[]")
    
    # Conditions
    active_conditions: Mapped[str] = mapped_column(Text, default="[]")
    
    # Resources (stored as JSON)
    resources: Mapped[str] = mapped_column(Text, default="{}")
    
    # Position
    position_x: Mapped[float] = mapped_column(Float, default=0.0)
    position_y: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Computed
    proficiency_bonus: Mapped[int] = mapped_column(Integer, default=2)
    is_alive: Mapped[bool] = mapped_column(Boolean, default=True)
    initiative_bonus: Mapped[int] = mapped_column(Integer, default=0)
    short_summary: Mapped[str] = mapped_column(String, default="")
    
    # Relationships
    user = relationship("User", back_populates="characters")
    profile = relationship("CharacterProfile", back_populates="character", uselist=False, cascade="all, delete-orphan")
