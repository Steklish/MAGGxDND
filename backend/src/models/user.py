from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List, Optional

from backend.src.database.base import Base

class AccessGroup(Base):
    __tablename__ = "access_groups"

    # The type hint `Mapped[int]` is for the Python instance attribute.
    # `mapped_column()` defines the database column behavior.
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    # Relationship to User (One-to-Many)
    # The type hint `Mapped[List["User"]]` tells the type checker this is a list of User objects.
    users: Mapped[List["User"]] = relationship(back_populates="group")


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("access_groups.id"), nullable=True)

    # Relationship to AccessGroup (Many-to-One)
    # The type hint `Mapped[Optional["AccessGroup"]]` indicates this can be an AccessGroup or None.
    group: Mapped[Optional["AccessGroup"]] = relationship(back_populates="users")
    
    # Relationship to Characters (One-to-Many)
    characters: Mapped[List["CharacterModel"]] = relationship("CharacterModel", back_populates="user", cascade="all, delete-orphan")
    
    # Relationships to Compendium will be added later when compendium is fully implemented
    # compendium_entries: Mapped[List["CompendiumEntry"]] = relationship("CompendiumEntry", back_populates="creator")
    # compendium_ratings: Mapped[List["CompendiumRating"]] = relationship("CompendiumRating", back_populates="user")
    # compendium_comments: Mapped[List["CompendiumComment"]] = relationship("CompendiumComment", back_populates="user")
    # homebrew_content: Mapped[List["UserHomebrew"]] = relationship("UserHomebrew", back_populates="user")