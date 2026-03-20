"""
REST API router для управления игровыми сессиями с поддержкой БД и владения.

Эндпоинты:
- POST /sessions - Создать сессию (требуется аутентификация)
- GET /sessions - Список сессий пользователя (требуется аутентификация)
- GET /sessions/{session_id} - Информация о сессии
- PUT /sessions/{session_id} - Обновить сессию (только владелец)
- DELETE /sessions/{session_id} - Удалить сессию (только владелец)
- POST /sessions/{session_id}/players - Добавить игрока
- DELETE /sessions/{session_id}/players/{player_id} - Удалить игрока
- POST /sessions/{session_id}/start - Запустить игру
- GET /sessions/{session_id}/game_info - Получить данные игры
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
import uuid
import os
from datetime import datetime

from sqlalchemy.orm import Session

from backend.src.config import settings
from backend.src.database.session import get_db
from backend.src.auth.dependencies import get_current_user
from backend.src.models.user import User
from backend.src.models.session import GameSession, SessionStatusEnum
from backend.src.repositories.session_repository import SessionRepository
from backend.src.utils import validate_safe_text, sanitize_string
from backend.src.game.session_manager import session_manager
from backend.src.game.session_factory import session_factory, SessionConfig
from core.game.engine import Session
from core.schemas.in_game import GameModes

router = APIRouter(prefix="/sessions", tags=["sessions"])

# Store for active game sessions (in-memory engine sessions)
# Key: session_uuid, Value: Session engine object
active_game_sessions: Dict[str, Session] = {}

# Store for active players (temporary, until full WebSocket integration)
active_players: Dict[str, Dict[str, any]] = {}

# Store for player ready status in waiting room
# Key: session_id, Value: Dict[user_id, is_ready] - track by user_id to prevent duplicates
waiting_room_ready_status: Dict[str, Dict[int, bool]] = {}


# === Schemas ===

class SessionCreateRequest(BaseModel):
    """Запрос на создание сессии."""
    session_name: str = Field(..., description="Название сессии", min_length=2, max_length=100)
    game_mode: str = Field(default="STORY", description="Режим игры: STORY или COMBAT")
    max_players: int = Field(default=5, description="Максимум игроков", ge=1, le=20)
    description: Optional[str] = Field(None, description="Описание сессии", max_length=500)
    guide: Optional[str] = Field(None, description="Сюжетная подсказка для AI", max_length=2000)
    is_public: bool = Field(default=False, description="Публичная сессия")
    
    # Настройки AI (опционально)
    gemini_model: str = Field(default="gemini-2.0-flash", description="Модель Gemini")

    @validator('session_name')
    def validate_session_name(cls, v):
        v = sanitize_string(v, max_length=100)
        if len(v) < 2:
            raise ValueError("Session name must be at least 2 characters")
        return v

    @validator('description')
    def validate_description(cls, v):
        if v:
            return validate_safe_text(v, "Description")
        return v

    @validator('guide')
    def validate_guide(cls, v):
        if v:
            return validate_safe_text(v, "Guide")
        return v


class SessionResponse(BaseModel):
    """Ответ с информацией о сессии."""
    session_id: str  # UUID
    session_name: str
    game_mode: str
    player_count: int
    status: str
    description: Optional[str] = None
    owner_id: int
    owner_name: Optional[str] = None
    created_at: str
    is_owner: bool = False  # True if current user is the owner


class SessionListResponse(BaseModel):
    """Список сессий."""
    sessions: List[SessionResponse]
    total: int


class SessionUpdateRequest(BaseModel):
    """Запрос на обновление сессии."""
    session_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    guide: Optional[str] = Field(None, max_length=2000)
    max_players: Optional[int] = Field(None, ge=1, le=20)
    is_public: Optional[bool] = None
    
    @validator('session_name')
    def validate_session_name(cls, v):
        if v:
            v = sanitize_string(v, max_length=100)
            if len(v) < 2:
                raise ValueError("Session name must be at least 2 characters")
        return v


class PlayerJoinRequest(BaseModel):
    """Запрос на присоединение игрока."""
    player_name: str = Field(..., description="Имя игрока", min_length=2, max_length=100)
    character_name: Optional[str] = Field(None, description="Имя персонажа", max_length=100)

    @validator('player_name')
    def validate_player_name(cls, v):
        v = sanitize_string(v, max_length=100)
        if len(v) < 2:
            raise ValueError("Player name must be at least 2 characters")
        return v


class PlayerResponse(BaseModel):
    """Информация об игроке."""
    player_id: str
    player_name: str
    character_name: Optional[str]
    connected: bool
    role: str = "player"
    is_ready: bool = False  # Ready status for waiting room


class SessionStartRequest(BaseModel):
    """Запрос на запуск игровой сессии."""
    scene_prompt: Optional[str] = Field(None, description="Описание начальной сцены", max_length=2000)
    character_prompts: List[str] = Field(default_factory=list, description="Описания персонажей")
    npc_prompts: List[str] = Field(default_factory=list, description="Описания NPC")
    # Frontend GameSetup fields (alternative format)
    wishes: Optional[str] = Field(None, description="Adventure preferences from GameSetup", max_length=1000)
    character_choice: Optional[str] = Field(None, description="Character selection choice")
    character_description: Optional[str] = Field(None, description="Character description for AI creation")
    # Extra field from frontend (ignored)
    sessionId: Optional[str] = Field(None, description="Session ID from frontend")
    
    class Config:
        extra = "ignore"  # Ignore extra fields from frontend


class SessionInfoResponse(BaseModel):
    """Расширенная информация о сессии."""
    session_id: str
    session_name: str
    game_mode: str
    player_count: int
    max_players: int
    status: str
    description: Optional[str] = None
    owner_id: int
    owner_name: str
    is_owner: bool
    players: List[PlayerResponse] = []


class WaitingRoomResponse(BaseModel):
    """Waiting room information."""
    session_id: str
    session_name: str
    game_mode: str
    player_count: int
    max_players: int
    status: str
    description: Optional[str] = None
    owner_id: int
    owner_name: str
    is_owner: bool
    players: List[PlayerResponse] = []


class PlayerReadyRequest(BaseModel):
    """Player ready status update."""
    is_ready: bool


# === Helper Functions ===

def get_session_repository(db: Session) -> SessionRepository:
    """Get session repository instance."""
    return SessionRepository(db)


def get_session_by_uuid_or_404(
    session_uuid: str,
    repository: SessionRepository
) -> GameSession:
    """Get session by UUID or raise 404."""
    session = repository.get_session_by_uuid(session_uuid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


def verify_session_owner(
    session: GameSession,
    current_user: User
) -> None:
    """Verify that current user is the session owner."""
    if session.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized: Only the session owner can perform this action"
        )


# === Endpoints ===

@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(
    request: SessionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создать новую игровую сессию.
    
    Требуется аутентификация. Сессия будет закреплена за создателем.
    """
    import logging
    logger = logging.getLogger(__name__)

    session_uuid = str(uuid.uuid4())
    logger.info(f"Creating session: {session_uuid} - {request.session_name} for user {current_user.id}")

    repository = get_session_repository(db)

    try:
        # Step 1: Create session in database FIRST
        db_session = repository.create_session(
            session_uuid=session_uuid,
            session_name=request.session_name,
            owner_id=current_user.id,
            game_mode=request.game_mode,
            max_players=request.max_players,
            description=request.description,
            guide=request.guide,
            gemini_model=request.gemini_model
        )

        logger.info(f"Database session created: {db_session.id} (UUID: {db_session.session_uuid}, owner_id={db_session.owner_id})")

        # Step 2: Create in-memory game session with the SAME UUID
        config = SessionConfig(
            session_name=request.session_name,
            game_mode=request.game_mode,
            max_players=request.max_players,
            description=request.description,
            guide=request.guide,
            gemini_model=request.gemini_model
        )

        # Pass the session_uuid to factory so it uses the same ID
        game_session = session_factory.create_session(config, session_id=session_uuid)
        active_game_sessions[session_uuid] = game_session

        logger.info(f"Game session created in memory: {session_uuid}")

        # Step 3: Add owner as participant in database
        participant = repository.add_participant(
            session_uuid=session_uuid,
            player_uuid=str(uuid.uuid4()),
            player_name=current_user.username,
            user_id=current_user.id,
            role="owner"
        )

        logger.info(f"Owner added as participant: {participant.id if participant else 'FAILED'}")

        # Step 4: Verify session is in database
        verify_session = repository.get_session_by_uuid(session_uuid)
        if not verify_session:
            logger.error(f"VERIFICATION FAILED: Session not found in database after creation!")
        else:
            logger.info(f"VERIFIED: Session exists in database with owner_id={verify_session.owner_id}")

        return SessionResponse(
            session_id=db_session.session_uuid,
            session_name=db_session.session_name,
            game_mode=db_session.game_mode.value,
            player_count=1,
            status=db_session.status.value,
            description=db_session.description,
            owner_id=db_session.owner_id,
            owner_name=current_user.username,
            created_at=db_session.created_at.isoformat(),
            is_owner=True
        )

    except ImportError as e:
        logger.error(f"ImportError: {e}")
        raise HTTPException(status_code=503, detail=f"SKLS dependencies not installed: {str(e)}")
    except Exception as e:
        logger.error(f"Exception: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить список сессий пользователя.
    
    Возвращает только сессии, принадлежащие текущему пользователю.
    """
    repository = get_session_repository(db)
    
    # Get only user's own sessions
    db_sessions = repository.get_owner_sessions(owner_id=current_user.id, active_only=True)
    
    session_list = []
    for db_session in db_sessions:
        # Check if session has active game engine
        game_session = active_game_sessions.get(db_session.session_uuid)
        player_count = 0
        
        if game_session:
            player_count = len(game_session.players)
        else:
            # Get from DB
            participants = repository.get_session_participants(db_session.session_uuid)
            player_count = len([p for p in participants if p.is_connected])
        
        session_list.append(SessionResponse(
            session_id=db_session.session_uuid,
            session_name=db_session.session_name,
            game_mode=db_session.game_mode.value,
            player_count=player_count,
            status=db_session.status.value,
            description=db_session.description,
            owner_id=db_session.owner_id,
            owner_name=current_user.username,
            created_at=db_session.created_at.isoformat(),
            is_owner=True
        ))
    
    return SessionListResponse(
        sessions=session_list,
        total=len(session_list)
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить информацию о конкретной сессии."""
    repository = get_session_repository(db)
    
    db_session = get_session_by_uuid_or_404(session_id, repository)
    
    # Get player count
    game_session = active_game_sessions.get(session_id)
    player_count = 0
    
    if game_session:
        player_count = len(game_session.players)
    else:
        participants = repository.get_session_participants(session_id)
        player_count = len([p for p in participants if p.is_connected])
    
    return SessionResponse(
        session_id=db_session.session_uuid,
        session_name=db_session.session_name,
        game_mode=db_session.game_mode.value,
        player_count=player_count,
        status=db_session.status.value,
        description=db_session.description,
        owner_id=db_session.owner_id,
        owner_name=current_user.username if db_session.owner_id == current_user.id else None,
        created_at=db_session.created_at.isoformat(),
        is_owner=(db_session.owner_id == current_user.id)
    )


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    request: SessionUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновить сессию.
    
    Только владелец может обновлять сессию.
    """
    repository = get_session_repository(db)
    
    db_session = get_session_by_uuid_or_404(session_id, repository)
    verify_session_owner(db_session, current_user)
    
    # Update fields
    if request.session_name is not None:
        db_session.session_name = request.session_name
    if request.description is not None:
        db_session.description = request.description
    if request.guide is not None:
        db_session.guide = request.guide
    if request.max_players is not None:
        db_session.max_players = request.max_players
    if request.is_public is not None:
        db_session.is_public = request.is_public
        
    db_session.updated_at = datetime.now()
    db.commit()
    db.refresh(db_session)
    
    # Get player count
    participants = repository.get_session_participants(session_id)
    player_count = len([p for p in participants if p.is_connected])
    
    return SessionResponse(
        session_id=db_session.session_uuid,
        session_name=db_session.session_name,
        game_mode=db_session.game_mode.value,
        player_count=player_count,
        status=db_session.status.value,
        description=db_session.description,
        owner_id=db_session.owner_id,
        owner_name=current_user.username,
        created_at=db_session.created_at.isoformat(),
        is_owner=True
    )


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Удалить сессию.
    
    Только владелец может удалить сессию. Это действие необратимо!
    """
    repository = get_session_repository(db)
    
    db_session = get_session_by_uuid_or_404(session_id, repository)
    verify_session_owner(db_session, current_user)
    
    # Remove from active game sessions
    game_session = active_game_sessions.get(session_id)
    if game_session:
        await session_manager.remove_session(session_id)
        del active_game_sessions[session_id]
    
    # Delete from database
    repository.delete_session(session_id, owner_id=current_user.id)


@router.post("/{session_id}/start", response_model=SessionResponse)
async def start_session(
    session_id: str,
    request: SessionStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Запустить игровую сессию с инициализацией сцены и персонажей.

    Только владелец может запустить сессию.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"[START] Session {session_id} - Request data: {request.dict()}")
    
    repository = get_session_repository(db)

    db_session = get_session_by_uuid_or_404(session_id, repository)
    verify_session_owner(db_session, current_user)

    # Get or create game session
    game_session = active_game_sessions.get(session_id)

    if not game_session:
        # Session exists in DB but not in memory - need to initialize it
        logger.warning(f"[START] Session {session_id} found in DB but not in memory. Initializing...")
        
        # Initialize the game session from DB
        try:
            config = SessionConfig(
                session_name=db_session.session_name,
                game_mode=db_session.game_mode.value,
                max_players=db_session.max_players,
                description=db_session.description,
                guide=db_session.guide,
                gemini_model=db_session.gemini_model or "gemini-2.0-flash"
            )
            game_session = session_factory.create_session(config, session_id=session_id)
            active_game_sessions[session_id] = game_session
            logger.info(f"[START] Session {session_id} restored from DB")
        except Exception as e:
            logger.error(f"[START] Failed to restore session {session_id}: {e}")
            raise HTTPException(
                status_code=400,
                detail="Session not initialized. Please recreate the session."
            )

    logger.info(f"[START] Game session found, starting with wishes={request.wishes}, character_description={request.character_description}")

    try:
        # Initialize scene and characters
        from core.schemas.in_game import SceneNode, Coordinate2D, UnifiedObject, ObjectType
        from core.entity.player import Player
        from core.schemas.in_game import Character, CharacterClass, AbilityScores
        from core.entity.orchestrator import Orchestrator

        # Use wishes as scene prompt if provided, otherwise use default
        scene_description = request.wishes or request.scene_prompt or "A dimly lit tavern with worn wooden tables and the smell of ale."
        
        # Create scene
        scene = SceneNode(
            name="The Drunken Dragon",
            description=scene_description,
            objects=[
                UnifiedObject(
                    name="Wooden Table",
                    obj_type=ObjectType.PROP,
                    quantity=1,
                    is_equipped=False,
                    position=Coordinate2D(x=5.0, y=5.0),
                    short_summary="A sturdy wooden table"
                ),
            ],
            center_position=Coordinate2D(x=10.0, y=10.0),
            dimensions=Coordinate2D(x=20.0, y=20.0),
            scale_unit="feet"
        )
        game_session.current_scene = scene

        # Update DB
        repository.update_session_scene(session_id, scene.name, owner_id=current_user.id)
        repository.update_session_status(session_id, "running", owner_id=current_user.id)

        # Initialize player characters from prompts
        # If character_description is provided (from GameSetup), use it
        character_prompts_to_use = request.character_prompts
        if request.character_description and not character_prompts_to_use:
            character_prompts_to_use = [request.character_description]
        
        for i, prompt in enumerate(character_prompts_to_use):
            character = Character(
                name=f"Character{i+1}",
                race="Human",
                char_class=CharacterClass.FIGHTER,
                level=1,
                backstory_summary=prompt,
                personality_traits=["Brave"],
                max_hp=30,
                current_hp=30,
                temp_hp=0,
                armor_class=12,
                speed=30,
                stats=AbilityScores(
                    strength=15, dexterity=12, constitution=14,
                    intelligence=10, wisdom=10, charisma=10
                ),
                inventory=[],
                active_conditions_list=[],
                resources={},
                position=Coordinate2D(x=float(i*2), y=float(i*2)),
                abilities=[],
                active_conditions="",
                proficiency_bonus=2,
                is_alive=True,
                initiative_bonus=11,
                short_summary=f"Character{i+1} the Fighter"
            )
            
            player_orchestrator = Orchestrator(
                generator=game_session.generator,
                logger=game_session.logger.getChild("player_orchestrator")
            )
            player_orchestrator.add_state(game_session)
            
            event_queue = game_session.event_pool.subscribe(character.name)
            
            player = Player(
                character=character,
                event_queuee=event_queue,
                logger=game_session.logger.getChild("player"),
                orchestrator=player_orchestrator
            )
            player.inject_state(game_session)
            game_session.players.append(player)
        
        # Initialize NPCs
        for i, prompt in enumerate(request.npc_prompts):
            from core.schemas.in_game import NPCCharacter
            npc_character = NPCCharacter(
                name=f"NPC{i+1}",
                race="Human",
                char_class=CharacterClass.PEASANT,
                level=1,
                backstory_summary=prompt,
                personality_traits=["Neutral"],
                max_hp=20,
                current_hp=20,
                temp_hp=0,
                armor_class=10,
                speed=30,
                stats=AbilityScores(
                    strength=10, dexterity=10, constitution=10,
                    intelligence=10, wisdom=10, charisma=10
                ),
                inventory=[],
                active_conditions_list=[],
                resources={},
                position=Coordinate2D(x=15.0, y=15.0),
                abilities=[],
                active_conditions="",
                proficiency_bonus=2,
                is_alive=True,
                initiative_bonus=10,
                short_summary=f"NPC{i+1}",
                motivation="Unknown",
                alignment="True Neutral",
                memory="",
                current_scene=scene.name
            )
            game_session._init_npc(npc_character)
        
        game_session.logger.info(
            f"Сессия запущена: {len(game_session.players)} игроков, {len(game_session.npcs)} NPC"
        )
        
        # Send welcome message
        game_session.delivery.master_message(
            f"Welcome to {scene.name}! {scene.description}"
        )
        game_session.delivery.session_updated(game_session)
        
        return SessionResponse(
            session_id=session_id,
            session_name=db_session.session_name,
            game_mode=db_session.game_mode.value,
            player_count=len(game_session.players),
            status="running",
            description=db_session.description,
            owner_id=db_session.owner_id,
            owner_name=current_user.username,
            created_at=db_session.created_at.isoformat(),
            is_owner=True
        )
        
    except Exception as e:
        game_session.logger.error(f"Ошибка при запуске сессии: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при запуске сессии: {str(e)}"
        )


@router.get("/{session_id}/info", response_model=SessionInfoResponse)
async def get_session_info(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get extended session information."""
    repository = get_session_repository(db)
    
    db_session = get_session_by_uuid_or_404(session_id, repository)
    
    # Get game session
    game_session = active_game_sessions.get(session_id)
    
    # Get players
    players = []
    player_count = 0
    
    if game_session:
        player_count = len(game_session.players)
        # Get from active game session
        for i, player in enumerate(game_session.players):
            if hasattr(player, 'character'):
                char = player.character
                players.append(PlayerResponse(
                    player_id=f"player_{i}",
                    player_name=getattr(char, 'name', 'Unknown'),
                    character_name=getattr(char, 'name', None),
                    connected=True,
                    role="player"
                ))
    else:
        # Get from DB
        participants = repository.get_session_participants(session_id)
        player_count = len(participants)
        for p in participants:
            players.append(PlayerResponse(
                player_id=p.player_uuid,
                player_name=p.player_name,
                character_name=p.character_name,
                connected=p.is_connected,
                role=p.role
            ))
    
    return SessionInfoResponse(
        session_id=db_session.session_uuid,
        session_name=db_session.session_name,
        game_mode=db_session.game_mode.value,
        player_count=player_count,
        max_players=db_session.max_players,
        status=db_session.status.value,
        description=db_session.description,
        owner_id=db_session.owner_id,
        owner_name=current_user.username if db_session.owner_id == current_user.id else "Unknown",
        is_owner=(db_session.owner_id == current_user.id),
        players=players
    )


@router.post("/{session_id}/players", response_model=PlayerResponse)
async def join_session(
    session_id: str,
    request: PlayerJoinRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Join a session as a player.

    Returns player_id for WebSocket connection.
    Each player can only join once per session.
    """
    repository = get_session_repository(db)

    # Validate session exists
    db_session = get_session_by_uuid_or_404(session_id, repository)

    # Check if session is active
    if db_session.status != SessionStatusEnum.RUNNING and db_session.status != SessionStatusEnum.CREATED:
        raise HTTPException(
            status_code=400,
            detail=f"Session is not accepting players (status: {db_session.status.value})"
        )

    # Check if player already joined (by user_id or player_name)
    existing_participants = repository.get_session_participants(session_id)
    
    # Check if current user already joined
    for participant in existing_participants:
        if participant.user_id == current_user.id:
            # User already joined - return existing player_id
            return PlayerResponse(
                player_id=participant.player_uuid,
                player_name=participant.player_name,
                character_name=participant.character_name,
                connected=participant.is_connected,
                role=participant.role
            )
        # Also check by player_name for guest users
        if participant.player_name == request.player_name and participant.user_id is None:
            raise HTTPException(
                status_code=400,
                detail=f"Player '{request.player_name}' is already in this session"
            )

    # Check max players
    if len(existing_participants) >= db_session.max_players:
        raise HTTPException(
            status_code=400,
            detail=f"Session is full (max {db_session.max_players} players)"
        )

    # Determine role - owner gets 'owner' role
    role = "owner" if db_session.owner_id == current_user.id else "player"

    # Generate player ID
    player_id = str(uuid.uuid4())

    # Add player to session
    participant = repository.add_participant(
        session_uuid=session_id,
        player_uuid=player_id,
        player_name=request.player_name,
        user_id=current_user.id,
        character_name=request.character_name,
        role=role
    )

    if not participant:
        raise HTTPException(status_code=500, detail="Failed to add player to session")

    return PlayerResponse(
        player_id=player_id,
        player_name=request.player_name,
        character_name=request.character_name,
        connected=True,
        role=role
    )


@router.delete("/{session_id}/players/{player_id}", status_code=204)
async def leave_session(
    session_id: str,
    player_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove a player from a session.
    
    Players can remove themselves, or the session owner can kick any player.
    """
    repository = get_session_repository(db)

    # Get session to check ownership
    db_session = get_session_by_uuid_or_404(session_id, repository)
    
    # Get participant to check if it's the current user
    participants = repository.get_session_participants(session_id)
    participant = next((p for p in participants if p.player_uuid == player_id), None)
    
    if not participant:
        raise HTTPException(status_code=404, detail="Player not found in session")
    
    # Check if current user is the player being removed or the session owner
    is_own_action = participant.user_id == current_user.id
    is_owner = db_session.owner_id == current_user.id
    
    if not is_own_action and not is_owner:
        raise HTTPException(
            status_code=403,
            detail="Only the player themselves or the session owner can remove this player"
        )

    # Remove from DB
    repository.remove_participant(session_id, player_id)

    # Unsubscribe from events
    session_manager.unregister_player_websocket(session_id, player_id)
    session_manager.unsubscribe_player_from_events(session_id, player_id)

    return None


@router.post("/{session_id}/players/{player_id}/kick", status_code=204)
async def kick_player(
    session_id: str,
    player_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Kick a player from the session.
    
    Only the session owner can kick players.
    """
    repository = get_session_repository(db)

    # Get session to check ownership
    db_session = get_session_by_uuid_or_404(session_id, repository)
    
    # Verify current user is the owner
    if db_session.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the session owner can kick players"
        )
    
    # Get participant
    participants = repository.get_session_participants(session_id)
    participant = next((p for p in participants if p.player_uuid == player_id), None)
    
    if not participant:
        raise HTTPException(status_code=404, detail="Player not found in session")
    
    # Cannot kick the owner
    if participant.role == "owner":
        raise HTTPException(
            status_code=400,
            detail="Cannot kick the session owner"
        )

    # Remove from DB
    repository.remove_participant(session_id, player_id)

    # Unsubscribe from events
    session_manager.unregister_player_websocket(session_id, player_id)
    session_manager.unsubscribe_player_from_events(session_id, player_id)

    return None


@router.get("/{session_id}/players", response_model=List[PlayerResponse])
async def get_session_players_endpoint(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all players in a session."""
    repository = get_session_repository(db)

    db_session = get_session_by_uuid_or_404(session_id, repository)

    participants = repository.get_session_participants(session_id)

    return [
        PlayerResponse(
            player_id=p.player_uuid,
            player_name=p.player_name,
            character_name=p.character_name,
            connected=p.is_connected,
            role=p.role
        )
        for p in participants
    ]


@router.get("/{session_id}/game_info", response_model=dict)
async def get_session_game_info(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed game session info including players, NPCs, and scene.
    For active game sessions with full engine integration.
    """
    repository = get_session_repository(db)
    
    db_session = get_session_by_uuid_or_404(session_id, repository)
    
    # Try to get from active game sessions
    game_session = active_game_sessions.get(session_id)
    
    if not game_session:
        raise HTTPException(
            status_code=400,
            detail="Session is not an active game session"
        )
    
    try:
        # Build players data
        players_data = []
        for player in game_session.players:
            if hasattr(player, 'character'):
                char = player.character
                stats = getattr(char, 'stats', None)
                players_data.append({
                    "name": getattr(char, 'name', 'Unknown'),
                    "race": getattr(char, 'race', 'Human'),
                    "char_class": str(getattr(char, 'char_class', 'Fighter')),
                    "level": getattr(char, 'level', 1),
                    "current_hp": getattr(char, 'current_hp', 10),
                    "max_hp": getattr(char, 'max_hp', 10),
                    "armor_class": getattr(char, 'armor_class', 10),
                    "speed": getattr(char, 'speed', 30),
                    "proficiency_bonus": getattr(char, 'proficiency_bonus', 2),
                    "initiative_bonus": getattr(char, 'initiative_bonus', 0),
                    "is_alive": getattr(char, 'is_alive', True),
                    "stats": {
                        "strength": getattr(stats, 'strength', 10) if stats else 10,
                        "dexterity": getattr(stats, 'dexterity', 10) if stats else 10,
                        "constitution": getattr(stats, 'constitution', 10) if stats else 10,
                        "intelligence": getattr(stats, 'intelligence', 10) if stats else 10,
                        "wisdom": getattr(stats, 'wisdom', 10) if stats else 10,
                        "charisma": getattr(stats, 'charisma', 10) if stats else 10,
                    } if stats else {
                        "strength": 10, "dexterity": 10, "constitution": 10,
                        "intelligence": 10, "wisdom": 10, "charisma": 10,
                    },
                })
        
        # Build NPCs data
        npcs_data = []
        for npc in game_session.npcs:
            if hasattr(npc, 'character'):
                char = npc.character
                stats = getattr(char, 'stats', None)
                npcs_data.append({
                    "name": getattr(char, 'name', 'Unknown'),
                    "race": getattr(char, 'race', 'Human'),
                    "char_class": str(getattr(char, 'char_class', 'Commoner')),
                    "alignment": getattr(char, 'alignment', 'Neutral'),
                    "current_hp": getattr(char, 'current_hp', 10),
                    "max_hp": getattr(char, 'max_hp', 10),
                    "armor_class": getattr(char, 'armor_class', 10),
                    "speed": getattr(char, 'speed', 30),
                    "is_alive": getattr(char, 'is_alive', True),
                })
        
        # Build scene data
        scene_data = None
        if game_session.current_scene:
            scene = game_session.current_scene
            scene_data = {
                "name": getattr(scene, 'name', 'Unknown'),
                "description": getattr(scene, 'description', ''),
            }
        
        return {
            "session_id": session_id,
            "session_name": db_session.session_name,
            "game_mode": db_session.game_mode.value,
            "status": db_session.status.value,
            "owner_id": db_session.owner_id,
            "players": players_data,
            "npcs": npcs_data,
            "current_scene": scene_data,
        }
        
    except Exception as e:
        game_session.logger.error(f"Error getting game info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting game info: {str(e)}"
        )


@router.get("/{session_id}/waiting-room", response_model=WaitingRoomResponse)
async def get_waiting_room(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get waiting room information for a session.
    
    Returns session details with player ready status.
    """
    repository = get_session_repository(db)

    db_session = get_session_by_uuid_or_404(session_id, repository)

    # Get players from DB
    participants = repository.get_session_participants(session_id)
    player_count = len([p for p in participants if p.is_connected])
    
    # Get ready status for this session (tracked by user_id)
    session_ready_status = waiting_room_ready_status.get(session_id, {})
    
    players = []
    for p in participants:
        # Get ready status by user_id (None for guest users without account)
        user_id_key = p.user_id if p.user_id is not None else hash(p.player_uuid)
        is_ready = session_ready_status.get(user_id_key, False)
        players.append(PlayerResponse(
            player_id=p.player_uuid,
            player_name=p.player_name,
            character_name=p.character_name,
            connected=p.is_connected,
            role=p.role,
            is_ready=is_ready
        ))

    return WaitingRoomResponse(
        session_id=db_session.session_uuid,
        session_name=db_session.session_name,
        game_mode=db_session.game_mode.value,
        player_count=player_count,
        max_players=db_session.max_players,
        status=db_session.status.value,
        description=db_session.description,
        owner_id=db_session.owner_id,
        owner_name=current_user.username if db_session.owner_id == current_user.id else "Unknown",
        is_owner=(db_session.owner_id == current_user.id),
        players=players
    )


@router.post("/{session_id}/ready", status_code=200)
async def set_player_ready(
    session_id: str,
    request: PlayerReadyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Set player ready status in waiting room.
    
    Players can toggle their ready status before game start.
    Each user can only join once per session.
    """
    repository = get_session_repository(db)

    # Validate session exists
    db_session = get_session_by_uuid_or_404(session_id, repository)

    # Verify player is in the session - check by user_id
    participants = repository.get_session_participants(session_id)
    participant = next((p for p in participants if p.user_id == current_user.id), None)
    
    if not participant:
        raise HTTPException(
            status_code=404,
            detail="Player not found in session. Please join the session first."
        )
    
    # Check if player is already connected (prevent double connection)
    if participant.is_connected:
        # Player already connected - this is fine, just update ready status
        pass

    # Initialize session ready status if not exists
    if session_id not in waiting_room_ready_status:
        waiting_room_ready_status[session_id] = {}
    
    # Set ready status using user_id as key (prevents duplicates)
    waiting_room_ready_status[session_id][current_user.id] = request.is_ready

    return {
        "success": True,
        "user_id": current_user.id,
        "player_name": participant.player_name,
        "is_ready": request.is_ready,
        "session_id": session_id
    }


@router.post("/{session_id}/start-game", response_model=SessionResponse)
async def start_game_from_waiting_room(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start the game from waiting room.
    
    Only the session owner can start the game.
    ALL connected players must be ready before starting.
    """
    import logging
    logger = logging.getLogger(__name__)

    repository = get_session_repository(db)

    db_session = get_session_by_uuid_or_404(session_id, repository)
    
    # Verify current user is the owner
    if db_session.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the session owner can start the game"
        )

    # Get all connected players
    participants = repository.get_session_participants(session_id)
    connected_players = [p for p in participants if p.is_connected]
    
    if not connected_players:
        raise HTTPException(
            status_code=400,
            detail="No connected players. Wait for players to join before starting."
        )
    
    # Check if ALL connected players are ready
    session_ready_status = waiting_room_ready_status.get(session_id, {})
    
    not_ready_players = []
    for player in connected_players:
        user_id_key = player.user_id if player.user_id is not None else hash(player.player_uuid)
        is_ready = session_ready_status.get(user_id_key, False)
        if not is_ready:
            not_ready_players.append(player.player_name)
    
    if not_ready_players:
        raise HTTPException(
            status_code=400,
            detail=f"Waiting for players to ready: {', '.join(not_ready_players)}"
        )

    logger.info(f"[START-GAME] Session {session_id} - Starting from waiting room with {len(connected_players)} ready players")

    # Get or create game session
    game_session = active_game_sessions.get(session_id)

    if not game_session:
        # Initialize the game session from DB
        logger.warning(f"[START-GAME] Session {session_id} found in DB but not in memory. Initializing...")

        try:
            from backend.src.game.session_factory import SessionConfig
            config = SessionConfig(
                session_name=db_session.session_name,
                game_mode=db_session.game_mode.value,
                max_players=db_session.max_players,
                description=db_session.description,
                guide=db_session.guide,
                gemini_model=db_session.gemini_model or "gemini-2.0-flash"
            )
            game_session = session_factory.create_session(config, session_id=session_id)
            active_game_sessions[session_id] = game_session
            logger.info(f"[START-GAME] Session {session_id} restored from DB")
        except Exception as e:
            logger.error(f"[START-GAME] Failed to restore session {session_id}: {e}")
            raise HTTPException(
                status_code=400,
                detail="Session not initialized. Please recreate the session."
            )

    try:
        # Initialize scene and characters
        from core.schemas.in_game import SceneNode, Coordinate2D, UnifiedObject, ObjectType
        from core.entity.player import Player
        from core.schemas.in_game import Character, CharacterClass, AbilityScores
        from core.entity.orchestrator import Orchestrator

        # Create initial scene
        scene_description = db_session.guide or "A dimly lit tavern with worn wooden tables and the smell of ale."

        scene = SceneNode(
            name="The Drunken Dragon",
            description=scene_description,
            objects=[
                UnifiedObject(
                    name="Wooden Table",
                    obj_type=ObjectType.PROP,
                    quantity=1,
                    is_equipped=False,
                    position=Coordinate2D(x=5.0, y=5.0),
                    short_summary="A sturdy wooden table"
                ),
            ],
            center_position=Coordinate2D(x=10.0, y=10.0),
            dimensions=Coordinate2D(x=20.0, y=20.0),
            scale_unit="feet"
        )
        game_session.current_scene = scene

        # Update DB status
        repository.update_session_scene(session_id, scene.name, owner_id=current_user.id)
        repository.update_session_status(session_id, "running", owner_id=current_user.id)

        # Initialize player characters from ALL connected players
        for i, participant in enumerate(connected_players):
            character = Character(
                name=participant.character_name or participant.player_name,
                race="Human",
                char_class=CharacterClass.FIGHTER,
                level=1,
                backstory_summary=f"{participant.player_name}'s character",
                personality_traits=["Brave"],
                max_hp=30,
                current_hp=30,
                temp_hp=0,
                armor_class=12,
                speed=30,
                stats=AbilityScores(
                    strength=15, dexterity=12, constitution=14,
                    intelligence=10, wisdom=10, charisma=10
                ),
                inventory=[],
                active_conditions_list=[],
                resources={},
                position=Coordinate2D(x=float(i*2), y=float(i*2)),
                abilities=[],
                active_conditions="",
                proficiency_bonus=2,
                is_alive=True,
                initiative_bonus=11,
                short_summary=f"{participant.player_name}'s character"
            )

            player_orchestrator = Orchestrator(
                generator=game_session.generator,
                logger=game_session.logger.getChild("player_orchestrator")
            )
            player_orchestrator.add_state(game_session)

            event_queue = game_session.event_pool.subscribe(character.name)

            player = Player(
                character=character,
                event_queuee=event_queue,
                logger=game_session.logger.getChild("player"),
                orchestrator=player_orchestrator
            )
            player.inject_state(game_session)
            game_session.players.append(player)

        game_session.logger.info(
            f"Сессия запущена: {len(game_session.players)} игроков"
        )

        # Send welcome message
        game_session.delivery.master_message(
            f"Welcome to {scene.name}! {scene.description}"
        )
        game_session.delivery.session_updated(game_session)

        # Clear waiting room ready status
        if session_id in waiting_room_ready_status:
            del waiting_room_ready_status[session_id]

        return SessionResponse(
            session_id=session_id,
            session_name=db_session.session_name,
            game_mode=db_session.game_mode.value,
            player_count=len(game_session.players),
            status="running",
            description=db_session.description,
            owner_id=db_session.owner_id,
            owner_name=current_user.username,
            created_at=db_session.created_at.isoformat(),
            is_owner=True
        )

    except Exception as e:
        game_session.logger.error(f"Ошибка при запуске сессии: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при запуске сессии: {str(e)}"
        )
