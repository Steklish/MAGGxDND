"""
Session Repository - Database access layer for game sessions.

Provides CRUD operations for GameSession model with ownership validation.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import select, update, delete

from backend.src.models.session import (
    GameSession,
    SessionParticipant,
    SessionSave,
    SessionCharacter,
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
        max_players: int = 5,
        description: Optional[str] = None,
        guide: Optional[str] = None,
        gemini_model: str = "gemini-2.0-flash"
    ) -> GameSession:
        """
        Create a new game session.
        
        Args:
            session_uuid: Unique UUID for the session
            session_name: Name of the session
            owner_id: ID of the user who owns (created) this session
            game_mode: Game mode (STORY, COMBAT, SANDBOX)
            max_players: Maximum number of players
            description: Session description
            guide: AI plot hint
            gemini_model: AI model to use
            
        Returns:
            Created GameSession object
        """
        db_session = GameSession(
            session_uuid=session_uuid,
            session_name=session_name,
            owner_id=owner_id,
            game_mode=GameModeEnum(game_mode),
            max_players=max_players,
            description=description,
            guide=guide,
            gemini_model=gemini_model,
            status=SessionStatusEnum.CREATED,
            is_active=True,
            is_public=False
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

    def get_participating_sessions(
        self,
        user_id: int
    ) -> List[GameSession]:
        """
        Get all sessions where user is a participant (not necessarily owner).
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of GameSession objects
        """
        result = self.db.execute(
            select(GameSession)
            .join(SessionParticipant)
            .where(SessionParticipant.user_id == user_id)
            .where(GameSession.is_active == True)
            .order_by(SessionParticipant.joined_at.desc())
        )
        return list(result.scalars().all())

    def get_all_active_sessions(self) -> List[GameSession]:
        """Get all active sessions (for admin purposes)."""
        result = self.db.execute(
            select(GameSession)
            .where(GameSession.is_active == True)
            .order_by(GameSession.created_at.desc())
        )
        return list(result.scalars().all())

    # === UPDATE ===

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
        """Update current scene name for a session."""
        session = self.get_session_by_uuid(session_uuid)
        
        if not session:
            return False
            
        if owner_id is not None and session.owner_id != owner_id:
            return False
            
        session.current_scene_name = scene_name
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

    # === PARTICIPANT MANAGEMENT ===

    def add_participant(
        self,
        session_uuid: str,
        player_uuid: str,
        player_name: str,
        user_id: Optional[int] = None,
        character_id: Optional[int] = None,
        character_name: Optional[str] = None,
        role: str = "player"
    ) -> Optional[SessionParticipant]:
        """
        Add a participant to a session.
        
        Args:
            session_uuid: UUID of the session
            player_uuid: Unique UUID for the player
            player_name: Display name of the player
            user_id: Optional user ID (for registered users)
            character_id: Optional character ID
            character_name: Optional character name
            role: Player role (owner, player, observer)
            
        Returns:
            Created SessionParticipant or None if session not found
        """
        session = self.get_session_by_uuid(session_uuid)
        
        if not session:
            return None
            
        # Check if already a participant
        existing = self.db.execute(
            select(SessionParticipant).where(
                SessionParticipant.session_id == session.id,
                SessionParticipant.player_uuid == player_uuid
            )
        ).scalar_one_or_none()
        
        if existing:
            # Re-activate existing participation
            existing.is_connected = True
            existing.last_active_at = datetime.now()
            self.db.commit()
            self.db.refresh(existing)
            return existing
            
        participant = SessionParticipant(
            session_id=session.id,
            user_id=user_id,
            player_name=player_name,
            player_uuid=player_uuid,
            character_id=character_id,
            character_name=character_name,
            role=role,
            is_connected=True
        )
        
        self.db.add(participant)
        self.db.commit()
        self.db.refresh(participant)
        
        return participant

    def remove_participant(
        self,
        session_uuid: str,
        player_uuid: str
    ) -> bool:
        """Remove a participant from a session."""
        session = self.get_session_by_uuid(session_uuid)
        
        if not session:
            return False
            
        result = self.db.execute(
            delete(SessionParticipant).where(
                SessionParticipant.session_id == session.id,
                SessionParticipant.player_uuid == player_uuid
            )
        )
        
        self.db.commit()
        return result.rowcount > 0

    def update_participant_connection(
        self,
        session_uuid: str,
        player_uuid: str,
        is_connected: bool
    ) -> bool:
        """Update participant connection status."""
        session = self.get_session_by_uuid(session_uuid)
        
        if not session:
            return False
            
        participant = self.db.execute(
            select(SessionParticipant).where(
                SessionParticipant.session_id == session.id,
                SessionParticipant.player_uuid == player_uuid
            )
        ).scalar_one_or_none()
        
        if not participant:
            return False
            
        participant.is_connected = is_connected
        if is_connected:
            participant.last_active_at = datetime.now()
            
        self.db.commit()
        return True

    def get_session_participants(
        self,
        session_uuid: str
    ) -> List[SessionParticipant]:
        """Get all participants for a session."""
        session = self.get_session_by_uuid(session_uuid)
        
        if not session:
            return []
            
        result = self.db.execute(
            select(SessionParticipant)
            .where(SessionParticipant.session_id == session.id)
            .order_by(SessionParticipant.joined_at)
        )
        return list(result.scalars().all())

    # === SAVE MANAGEMENT ===

    def create_session_save(
        self,
        session_uuid: str,
        save_name: str,
        session_data: Dict[str, Any],
        save_type: str = "auto",
        game_state_summary: Optional[str] = None,
        turn_number: Optional[int] = None,
        in_game_time: Optional[str] = None
    ) -> Optional[SessionSave]:
        """Create a session save state."""
        session = self.get_session_by_uuid(session_uuid)
        
        if not session:
            return None
            
        save = SessionSave(
            session_id=session.id,
            save_name=save_name,
            save_type=save_type,
            session_data=session_data,
            game_state_summary=game_state_summary,
            turn_number=turn_number,
            in_game_time=in_game_time
        )
        
        self.db.add(save)
        self.db.commit()
        self.db.refresh(save)
        
        return save

    def get_session_saves(
        self,
        session_uuid: str
    ) -> List[SessionSave]:
        """Get all saves for a session."""
        session = self.get_session_by_uuid(session_uuid)
        
        if not session:
            return []
            
        result = self.db.execute(
            select(SessionSave)
            .where(SessionSave.session_id == session.id)
            .order_by(SessionSave.created_at.desc())
        )
        return list(result.scalars().all())

    def get_latest_session_save(
        self,
        session_uuid: str
    ) -> Optional[SessionSave]:
        """Get the most recent save for a session."""
        session = self.get_session_by_uuid(session_uuid)
        
        if not session:
            return None
            
        save = self.db.execute(
            select(SessionSave)
            .where(SessionSave.session_id == session.id)
            .order_by(SessionSave.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        
        return save

    def delete_session_save(
        self,
        save_id: int,
        session_uuid: Optional[str] = None
    ) -> bool:
        """Delete a session save."""
        query = delete(SessionSave).where(SessionSave.id == save_id)
        
        if session_uuid:
            session = self.get_session_by_uuid(session_uuid)
            if session:
                query = query.where(SessionSave.session_id == session.id)
                
        result = self.db.execute(query)
        self.db.commit()
        return result.rowcount > 0

    # === CHARACTER MANAGEMENT ===

    def add_session_character(
        self,
        session_uuid: str,
        character_id: int,
        character_type: str = "player"
    ) -> Optional[SessionCharacter]:
        """Add a character to a session."""
        session = self.get_session_by_uuid(session_uuid)
        
        if not session:
            return None
            
        session_character = SessionCharacter(
            session_id=session.id,
            character_id=character_id,
            character_type=character_type,
            is_active=True
        )
        
        self.db.add(session_character)
        self.db.commit()
        self.db.refresh(session_character)
        
        return session_character

    def get_session_characters(
        self,
        session_uuid: str,
        character_type: Optional[str] = None
    ) -> List[SessionCharacter]:
        """Get all characters in a session."""
        session = self.get_session_by_uuid(session_uuid)
        
        if not session:
            return []
            
        query = select(SessionCharacter).where(
            SessionCharacter.session_id == session.id,
            SessionCharacter.is_active == True
        )
        
        if character_type:
            query = query.where(SessionCharacter.character_type == character_type)
            
        result = self.db.execute(query)
        return list(result.scalars().all())


# Convenience function for creating repository with dependency injection
def get_repository(db: DBSession) -> SessionRepository:
    """Get session repository instance."""
    return SessionRepository(db)
