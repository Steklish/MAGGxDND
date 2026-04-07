from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List, Optional

from backend.src.database.base import Base
from backend.src.models.session import GameSession

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

    # Relationship to Game Sessions (One-to-Many) - sessions owned by this user
    sessions: Mapped[List["GameSession"]] = relationship(
        "GameSession",
        back_populates="owner",
        foreign_keys="GameSession.owner_id"
    )