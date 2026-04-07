"""
GameSession database model for persistent session storage.

Stores only:
- User credentials (ownership)
- Complete session data as a JSON object
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
import enum

from sqlalchemy import (
    Integer, String, ForeignKey, DateTime, Boolean, Enum, JSON, func
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
    
    Stores only:
    - Session ownership (owner_id)
    - Complete session data as JSON (players, NPCs, scenes, game state, etc.)
    
    Each session is owned by a user (the creator) who has full control.
    """
    __tablename__ = "game_sessions"
    __table_args__ = {'extend_existing': True}

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
    status: Mapped[str] = mapped_column(
        Enum(SessionStatusEnum),
        default=SessionStatusEnum.CREATED,
        nullable=False,
        index=True
    )

    # Complete session data (stores everything as JSON)
    session_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

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


# Import for type hints (avoid circular imports)
if TYPE_CHECKING:
    from backend.src.models.user import User
