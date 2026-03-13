"""
Compendium Models - D&D Beyond Style Encyclopedia
Contains spells, items, monsters, rules, etc.
"""
from sqlalchemy import Integer, String, ForeignKey, Text, Boolean, JSON, Float
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List, Optional, Dict, Any

from backend.src.database.base import Base


class CompendiumCategory(Base):
    """Main categories for compendium entries"""
    __tablename__ = "compendium_categories"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    icon: Mapped[str] = mapped_column(String, default="📚")
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("compendium_categories.id"), nullable=True)
    
    # Self-referential relationship for subcategories
    subcategories: Mapped[List["CompendiumCategory"]] = relationship(
        remote_side="CompendiumCategory.id",
        back_populates="parent"
    )
    parent: Mapped[Optional["CompendiumCategory"]] = relationship(
        remote_side="CompendiumCategory.id",
        back_populates="subcategories"
    )
    
    # Entries in this category
    entries: Mapped[List["CompendiumEntry"]] = relationship(back_populates="category")


class CompendiumEntry(Base):
    """Individual compendium entries (spells, items, monsters, etc.)"""
    __tablename__ = "compendium_entries"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("compendium_categories.id"), nullable=False)
    
    # Basic info
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String, nullable=False)  # spell, item, monster, rule, etc.
    
    # Content
    description: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)  # Full HTML/Markdown content
    
    # Metadata (stored as JSON for flexibility)
    metadata: Mapped[str] = mapped_column(JSON, default={})
    
    # Example metadata structures:
    # For spells:
    # {
    #     "level": 3,
    #     "school": "Fire",
    #     "casting_time": "1 action",
    #     "range": "120 feet",
    #     "components": ["V", "S", "M"],
    #     "duration": "Instantaneous",
    #     "damage": "8d6",
    #     "damage_type": "fire"
    # }
    #
    # For items:
    # {
    #     "rarity": "rare",
    #     "type": "weapon",
    #     "cost": "500 gp",
    #     "weight": "3 lbs",
    #     "properties": ["magical", "+1"]
    # }
    #
    # For monsters:
    # {
    #     "challenge_rating": 5,
    #     "type": "dragon",
    #     "alignment": "chaotic evil",
    #     "armor_class": 18,
    #     "hit_points": 150,
    #     "speed": "40 ft., fly 80 ft.",
    #     "stats": {
    #         "strength": 23,
    #         "dexterity": 10,
    #         "constitution": 21,
    #         "intelligence": 14,
    #         "wisdom": 11,
    #         "charisma": 19
    #     }
    # }
    
    # Search optimization
    search_tags: Mapped[str] = mapped_column(Text, default="")  # Comma-separated tags
    search_vector: Mapped[str] = mapped_column(Text, default="")  # Full-text search vector
    
    # Organization
    source: Mapped[str] = mapped_column(String, default="SRD")  # Source book
    page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Access control
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    is_homebrew: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # Relationships
    category: Mapped["CompendiumCategory"] = relationship(back_populates="entries")
    creator: Mapped[Optional["User"]] = relationship(back_populates="compendium_entries")
    
    # Ratings and reviews
    ratings: Mapped[List["CompendiumRating"]] = relationship(back_populates="entry", cascade="all, delete-orphan")
    comments: Mapped[List["CompendiumComment"]] = relationship(back_populates="entry", cascade="all, delete-orphan")


class CompendiumRating(Base):
    """User ratings for compendium entries"""
    __tablename__ = "compendium_ratings"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("compendium_entries.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    rating: Mapped[int] = mapped_column(Integer)  # 1-5 stars
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(String)  # ISO timestamp
    
    # Relationships
    entry: Mapped["CompendiumEntry"] = relationship(back_populates="ratings")
    user: Mapped["User"] = relationship(back_populates="compendium_ratings")


class CompendiumComment(Base):
    """User comments for compendium entries"""
    __tablename__ = "compendium_comments"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("compendium_entries.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("compendium_comments.id"), nullable=True)
    
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)
    
    # Relationships
    entry: Mapped["CompendiumEntry"] = relationship(back_populates="comments")
    user: Mapped["User"] = relationship(back_populates="compendium_comments")
    replies: Mapped[List["CompendiumComment"]] = relationship(
        remote_side="CompendiumComment.id",
        back_populates="parent"
    )
    parent: Mapped[Optional["CompendiumComment"]] = relationship(
        remote_side="CompendiumComment.id",
        back_populates="replies"
    )


class UserHomebrew(Base):
    """User-created homebrew content"""
    __tablename__ = "user_homebrew"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # Basic info
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)  # subclass, race, spell, item, etc.
    description: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    
    # Metadata
    metadata: Mapped[str] = mapped_column(JSON, default={})
    
    # Publishing
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Versioning
    version: Mapped[str] = mapped_column(String, default="1.0.0")
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user_homebrew.id"), nullable=True)
    
    # Statistics
    views: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    downloads: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="homebrew_content")


# Update User model to include relationships
# (This would be added to the existing User model in backend/src/models/user.py)
# Add these to the User class:
# compendium_entries: Mapped[List["CompendiumEntry"]] = relationship(back_populates="creator")
# compendium_ratings: Mapped[List["CompendiumRating"]] = relationship(back_populates="user")
# compendium_comments: Mapped[List["CompendiumComment"]] = relationship(back_populates="user")
# homebrew_content: Mapped[List["UserHomebrew"]] = relationship(back_populates="user")
