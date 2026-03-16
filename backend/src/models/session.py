"""
GameSession database model for persistent session storage.
"""
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
import enum

from sqlalchemy import (
    Integer, String, ForeignKey, DateTime, Boolean, Enum, Text, JSON, func
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from backend.src.database.base import Base


class GameModeEnum(str, enum.Enum):
    """Game mode enumeration."""
    STORY = "STORY"
    COMBAT = "COMBAT"
    SANDBOX = "SANDBOX"


class SessionStatusEnum(str, enum.Enum):
    """Session status enumeration."""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class GameSession(Base):
    """
    Database model for game sessions.
    
    Each session is owned by a user (the creator) who has full control.
    """
    __tablename__ = "game_sessions"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Session identification
    session_uuid: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    session_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Owner relationship (creator has full control)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    owner: Mapped["User"] = relationship("User", back_populates="sessions")
    
    # Session configuration
    game_mode: Mapped[str] = mapped_column(
        Enum(GameModeEnum),
        default=GameModeEnum.STORY,
        nullable=False
    )
    max_players: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    guide: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # AI plot hint
    
    # Session state
    status: Mapped[str] = mapped_column(
        Enum(SessionStatusEnum),
        default=SessionStatusEnum.CREATED,
        nullable=False,
        index=True
    )
    current_scene_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # AI configuration
    gemini_model: Mapped[str] = mapped_column(String(100), default="gemini-2.0-flash")
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    last_active_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    # Players participating in this session
    participants: Mapped[List["SessionParticipant"]] = relationship(
        "SessionParticipant",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    
    # Save states (serialized session data)
    saves: Mapped[List["SessionSave"]] = relationship(
        "SessionSave",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    
    # Characters associated with this session
    session_characters: Mapped[List["SessionCharacter"]] = relationship(
        "SessionCharacter",
        back_populates="session",
        cascade="all, delete-orphan"
    )


class SessionParticipant(Base):
    """
    Database model for session participants (players).
    
    Links users to sessions they are participating in.
    """
    __tablename__ = "session_participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("game_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Player info (for guest players without accounts)
    player_name: Mapped[str] = mapped_column(String(100), nullable=False)
    player_uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    
    # Character info
    character_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("characters.id", ondelete="SET NULL"),
        nullable=True
    )
    character_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Session state
    role: Mapped[str] = mapped_column(String(50), default="player", nullable=False)  # 'owner', 'player', 'observer'
    is_connected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Timestamps
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    session: Mapped["GameSession"] = relationship("GameSession", back_populates="participants")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="session_participations")
    character: Mapped[Optional["CharacterModel"]] = relationship("CharacterModel", backref="session_participations")


class SessionSave(Base):
    """
    Database model for session save states.
    
    Stores serialized session data for persistence and recovery.
    """
    __tablename__ = "session_saves"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Foreign key
    session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("game_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Save metadata
    save_name: Mapped[str] = mapped_column(String(100), nullable=False)
    save_type: Mapped[str] = mapped_column(String(50), default="auto", nullable=False)  # 'auto', 'manual', 'checkpoint'
    
    # Serialized session data
    session_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Metadata
    game_state_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    turn_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    in_game_time: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    # Relationships
    session: Mapped["GameSession"] = relationship("GameSession", back_populates="saves")


class SessionCharacter(Base):
    """
    Database model for characters in a session.
    
    Links characters to specific sessions.
    """
    __tablename__ = "session_characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("game_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    character_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Character role in session
    character_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'player', 'npc'
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timestamps
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    session: Mapped["GameSession"] = relationship("GameSession", back_populates="session_characters")
    character: Mapped["CharacterModel"] = relationship("CharacterModel", backref="session_assignments")


# Import for type hints (avoid circular imports)
if TYPE_CHECKING:
    from backend.src.models.user import User
    from backend.src.models.character import CharacterModel
