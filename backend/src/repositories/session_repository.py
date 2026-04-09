"""
Session Repository - Database access layer for game sessions.

Provides CRUD operations for GameSession model with ownership validation.
Sessions store complete game state as JSON in session_data field.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import select, update, delete

from backend.src.models.session import (
    GameSession,
    GameModeEnum,
    SessionStatusEnum
)


class SessionRepository:
    """
    Repository for database operations on game sessions.

    All operations respect session ownership - only the owner
    has full control over their sessions.
    """

    def __init__(self, db: DBSession):
        self.db = db

    # === CREATE ===

    def create_session(
        self,
        session_uuid: str,
        session_name: str,
        owner_id: int,
        game_mode: str = "STORY",
        session_data: Optional[Dict[str, Any]] = None
    ) -> GameSession:
        """
        Create a new game session.

        Args:
            session_uuid: Unique UUID for the session
            session_name: Name of the session
            owner_id: ID of the user who owns (created) this session
            game_mode: Game mode (STORY, COMBAT, SANDBOX)
            session_data: Complete session data as JSON (optional)

        Returns:
            Created GameSession object
        """
        db_session = GameSession(
            session_uuid=session_uuid,
            session_name=session_name,
            owner_id=owner_id,
            game_mode=GameModeEnum(game_mode),
            session_data=session_data or {},
            status=SessionStatusEnum.CREATED,
            is_active=True
        )

        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)

        return db_session

    # === READ ===

    def get_session_by_id(self, session_id: int) -> Optional[GameSession]:
        """Get session by database ID."""
        return self.db.get(GameSession, session_id)

    def get_session_by_uuid(self, session_uuid: str) -> Optional[GameSession]:
        """Get session by UUID."""
        result = self.db.execute(
            select(GameSession).where(GameSession.session_uuid == session_uuid)
        )
        return result.scalar_one_or_none()

    def get_owner_sessions(
        self,
        owner_id: int,
        active_only: bool = True
    ) -> List[GameSession]:
        """
        Get all sessions owned by a user.

        Args:
            owner_id: ID of the owner
            active_only: If True, only return active sessions

        Returns:
            List of GameSession objects
        """
        query = select(GameSession).where(GameSession.owner_id == owner_id)

        if active_only:
            query = query.where(GameSession.is_active == True)

        query = query.order_by(GameSession.created_at.desc())

        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_all_active_sessions(self) -> List[GameSession]:
        """Get all active sessions (for admin purposes)."""
        result = self.db.execute(
            select(GameSession)
            .where(GameSession.is_active == True)
            .order_by(GameSession.created_at.desc())
        )
        return list(result.scalars().all())

    def get_public_sessions(
        self,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[GameSession]:
        """
        Get all public sessions (for browsing).
        
        Args:
            search: Optional search term (matches session name or description)
            skip: Number of results to skip (pagination)
            limit: Maximum number of results
            
        Returns:
            List of public GameSession objects
        """
        query = select(GameSession).where(
            GameSession.is_active == True,
            GameSession.is_public == True
        )
        
        # Add search filter if provided
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (GameSession.session_name.ilike(search_pattern)) |
                (GameSession.description.ilike(search_pattern))
            )
        
        query = query.order_by(GameSession.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = self.db.execute(query)
        return list(result.scalars().all())

    # === UPDATE ===

    def update_session(
        self,
        session_uuid: str,
        updates: Dict[str, Any],
        owner_id: Optional[int] = None
    ) -> bool:
        """
        Update session fields including session_data.

        Args:
            session_uuid: UUID of the session
            updates: Dictionary of fields to update (can include session_data)
            owner_id: Optional owner ID for ownership validation

        Returns:
            True if updated, False if not found or not owner
        """
        session = self.get_session_by_uuid(session_uuid)

        if not session:
            return False

        if owner_id is not None and session.owner_id != owner_id:
            return False  # Not the owner

        # Update fields
        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)

        session.updated_at = datetime.now()
        session.last_active_at = datetime.now()

        self.db.commit()
        return True

    def update_session_data(
        self,
        session_uuid: str,
        session_data: Dict[str, Any],
        owner_id: Optional[int] = None
    ) -> bool:
        """
        Update complete session data.

        Args:
            session_uuid: UUID of the session
            session_data: Complete session data as JSON
            owner_id: Optional owner ID for ownership validation

        Returns:
            True if updated, False if not found or not owner
        """
        session = self.get_session_by_uuid(session_uuid)

        if not session:
            return False

        if owner_id is not None and session.owner_id != owner_id:
            return False

        session.session_data = session_data
        session.updated_at = datetime.now()
        session.last_active_at = datetime.now()

        self.db.commit()
        return True

    def update_session_status(
        self,
        session_uuid: str,
        status: str,
        owner_id: Optional[int] = None
    ) -> bool:
        """
        Update session status.

        Args:
            session_uuid: UUID of the session
            status: New status value
            owner_id: Optional owner ID for ownership validation

        Returns:
            True if updated, False if not found or not owner
        """
        session = self.get_session_by_uuid(session_uuid)

        if not session:
            return False

        if owner_id is not None and session.owner_id != owner_id:
            return False  # Not the owner

        session.status = SessionStatusEnum(status)
        session.updated_at = datetime.now()

        if status == SessionStatusEnum.RUNNING:
            session.last_active_at = datetime.now()

        self.db.commit()
        return True

    def update_session_scene(
        self,
        session_uuid: str,
        scene_name: str,
        owner_id: Optional[int] = None
    ) -> bool:
        """
        Update current scene name in session_data.

        Args:
            session_uuid: UUID of the session
            scene_name: Name of the current scene
            owner_id: Optional owner ID for ownership validation

        Returns:
            True if updated, False if not found or not owner
        """
        session = self.get_session_by_uuid(session_uuid)

        if not session:
            return False

        if owner_id is not None and session.owner_id != owner_id:
            return False

        # Store scene name in session_data
        session_data = session.session_data or {}
        session_data["current_scene_name"] = scene_name
        session.session_data = session_data
        session.updated_at = datetime.now()
        session.last_active_at = datetime.now()

        self.db.commit()
        return True

    def update_session_activity(
        self,
        session_uuid: str
    ) -> bool:
        """Update last active timestamp."""
        session = self.get_session_by_uuid(session_uuid)

        if not session:
            return False

        session.last_active_at = datetime.now()
        self.db.commit()
        return True

    def deactivate_session(
        self,
        session_uuid: str,
        owner_id: Optional[int] = None
    ) -> bool:
        """
        Deactivate a session (soft delete).

        Args:
            session_uuid: UUID of the session
            owner_id: Optional owner ID for validation
        """
        session = self.get_session_by_uuid(session_uuid)

        if not session:
            return False

        if owner_id is not None and session.owner_id != owner_id:
            return False

        session.is_active = False
        session.status = SessionStatusEnum.ARCHIVED
        session.updated_at = datetime.now()

        self.db.commit()
        return True

    # === DELETE ===

    def delete_session(
        self,
        session_uuid: str,
        owner_id: Optional[int] = None
    ) -> bool:
        """
        Delete a session (hard delete).

        Args:
            session_uuid: UUID of the session
            owner_id: Optional owner ID for validation

        Returns:
            True if deleted, False if not found or not owner
        """
        session = self.get_session_by_uuid(session_uuid)

        if not session:
            return False

        if owner_id is not None and session.owner_id != owner_id:
            return False

        self.db.delete(session)
        self.db.commit()
        return True

    # === PARTICIPANT MANAGEMENT (stored in session_data JSON) ===

    def add_participant(
        self,
        session_uuid: str,
        player_uuid: str,
        player_name: str,
        user_id: Optional[int] = None,
        character_id: Optional[int] = None,
        character_name: Optional[str] = None,
        role: str = "player",
        owner_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Add a participant to session_data JSON.

        Args:
            session_uuid: UUID of the session
            player_uuid: Unique UUID for the player
            player_name: Display name of the player
            user_id: Optional user ID (for registered users)
            character_id: Optional character ID (deprecated, stored in session_data)
            character_name: Optional character name
            role: Player role (owner, player, observer)
            owner_id: Optional owner ID for ownership validation

        Returns:
            Created participant dict or None if session not found
        """
        session = self.get_session_by_uuid(session_uuid)

        if not session:
            return None

        if owner_id is not None and session.owner_id != owner_id:
            return None

        # Get or initialize participants list in session_data
        session_data = session.session_data or {}
        participants = session_data.get("participants", [])

        # Check if already a participant
        existing = next((p for p in participants if p.get("player_uuid") == player_uuid), None)

        if existing:
            # Re-activate existing participation
            existing["is_connected"] = True
            existing["last_active_at"] = datetime.now().isoformat()
        else:
            participant = {
                "player_uuid": player_uuid,
                "player_name": player_name,
                "user_id": user_id,
                "character_name": character_name,
                "role": role,
                "is_connected": True,
                "joined_at": datetime.now().isoformat(),
                "last_active_at": datetime.now().isoformat()
            }
            participants.append(participant)

        session_data["participants"] = participants
        session.session_data = session_data
        session.updated_at = datetime.now()
        session.last_active_at = datetime.now()

        self.db.commit()
        
        # Return the participant we just added/updated
        return next((p for p in participants if p.get("player_uuid") == player_uuid), None)

    def remove_participant(
        self,
        session_uuid: str,
        player_uuid: str,
        owner_id: Optional[int] = None
    ) -> bool:
        """Remove a participant from session_data JSON."""
        session = self.get_session_by_uuid(session_uuid)

        if not session:
            return False

        if owner_id is not None and session.owner_id != owner_id:
            return False

        session_data = session.session_data or {}
        participants = session_data.get("participants", [])

        # Filter out the participant
        original_count = len(participants)
        participants = [p for p in participants if p.get("player_uuid") != player_uuid]

        if len(participants) == original_count:
            return False  # Participant not found

        session_data["participants"] = participants
        session.session_data = session_data
        session.updated_at = datetime.now()

        self.db.commit()
        return True

    def update_participant_connection(
        self,
        session_uuid: str,
        player_uuid: str,
        is_connected: bool,
        owner_id: Optional[int] = None
    ) -> bool:
        """Update participant connection status in session_data JSON."""
        session = self.get_session_by_uuid(session_uuid)

        if not session:
            return False

        if owner_id is not None and session.owner_id != owner_id:
            return False

        session_data = session.session_data or {}
        participants = session_data.get("participants", [])

        participant = next((p for p in participants if p.get("player_uuid") == player_uuid), None)

        if not participant:
            return False

        participant["is_connected"] = is_connected
        if is_connected:
            participant["last_active_at"] = datetime.now().isoformat()

        session_data["participants"] = participants
        session.session_data = session_data
        session.updated_at = datetime.now()

        self.db.commit()
        return True

    def get_session_participants(
        self,
        session_uuid: str
    ) -> List[Dict[str, Any]]:
        """Get all participants from session_data JSON."""
        session = self.get_session_by_uuid(session_uuid)

        if not session:
            return []

        session_data = session.session_data or {}
        return session_data.get("participants", [])


# Convenience function for creating repository with dependency injection
def get_repository(db: DBSession) -> SessionRepository:
    """Get session repository instance."""
    return SessionRepository(db)

