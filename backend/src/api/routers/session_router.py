"""
REST API router для управления игровыми сессиями.

Эндпоинты:
- POST /sessions - Создать сессию
- GET /sessions - Список сессий
- GET /sessions/{session_id} - Информация о сессии
- DELETE /sessions/{session_id} - Удалить сессию
- POST /sessions/{session_id}/players - Добавить игрока
- DELETE /sessions/{session_id}/players/{player_id} - Удалить игрока
- POST /sessions/start_real_game - Запустить игру с AI генерацией
- GET /sessions/{session_id}/game_info - Получить данные игры
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
import uuid
import os

from backend.src.config import settings
from backend.src.utils import validate_safe_text, sanitize_string
from backend.src.game.session_manager import session_manager
from backend.src.game.session_factory import session_factory, SessionConfig
from core.game.engine import Session
from core.game.event_pool import EventPool
from backend.src.delivery.game_delivery import GameDelivery
from backend.src.delivery.rest_api_delivery import RESTAPIDelivery
from core.schemas.in_game import Character, NPCCharacter, GameModes, SceneNode
from core.entity.orchestrator import Orchestrator
from core.entity.player import Player
from core.entity.npc import NPC
from skls_generator.generator import Generator
from skls_generator.gen_backends.google_gen import GoogleGenAI

router = APIRouter(prefix="/sessions", tags=["sessions"])

# Store for active players (temporary, until DB integration)
active_players: Dict[str, Dict[str, any]] = {}


# === Schemas ===

class SessionCreateRequest(BaseModel):
    """Запрос на создание сессии."""
    session_name: str = Field(..., description="Название сессии", min_length=2, max_length=100)
    game_mode: str = Field(default="STORY", description="Режим игры: STORY или COMBAT")
    max_players: int = Field(default=5, description="Максимум игроков", ge=1, le=20)
    description: Optional[str] = Field(None, description="Описание сессии", max_length=500)
    guide: Optional[str] = Field(None, description="Сюжетная подсказка для AI", max_length=2000)
    scene_prompt: Optional[str] = Field(None, description="Описание начальной сцены", max_length=2000)
    character_prompts: List[str] = Field(default=[], description="Описания персонажей игроков")
    npc_prompts: List[str] = Field(default=[], description="Описания NPC")

    # Настройки AI (опционально)
    gemini_api_key: Optional[str] = Field(None, description="API ключ Gemini")
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

    @validator('scene_prompt')
    def validate_scene_prompt(cls, v):
        if v:
            return validate_safe_text(v, "Scene prompt")
        return v


class SessionResponse(BaseModel):
    """Ответ с информацией о сессии."""
    session_id: str
    session_name: str
    game_mode: str
    player_count: int
    status: str
    description: Optional[str] = None


class SessionListResponse(BaseModel):
    """Список сессий."""
    sessions: List[SessionResponse]
    total: int


class PlayerJoinRequest(BaseModel):
    """Запрос на присоединение игрока."""
    player_name: str = Field(..., description="Имя игрока", min_length=2, max_length=100)
    character_name: Optional[str] = Field(None, description="Имя персонажа", max_length=100)
    character_prompt: Optional[str] = Field(None, description="Описание персонажа для генерации", max_length=1000)

    @validator('player_name')
    def validate_player_name(cls, v):
        v = sanitize_string(v, max_length=100)
        if len(v) < 2:
            raise ValueError("Player name must be at least 2 characters")
        return v

    @validator('character_name')
    def validate_character_name(cls, v):
        if v:
            return sanitize_string(v, max_length=100)
        return v

    @validator('character_prompt')
    def validate_character_prompt(cls, v):
        if v:
            return validate_safe_text(v, "Character prompt")
        return v


class PlayerResponse(BaseModel):
    """Информация об игроке."""
    player_id: str
    player_name: str
    character_name: Optional[str]
    connected: bool


class SessionStartRequest(BaseModel):
    """Запрос на запуск игровой сессии."""
    scene_prompt: str = Field(..., description="Описание начальной сцены", min_length=10, max_length=2000)
    character_prompts: List[str] = Field(default=[], description="Описания персонажей")
    npc_prompts: List[str] = Field(default=[], description="Описания NPC")

    @validator('scene_prompt')
    def validate_scene_prompt(cls, v):
        v = sanitize_string(v, max_length=2000)
        if len(v) < 10:
            raise ValueError("Scene prompt must be at least 10 characters")
        return validate_safe_text(v, "Scene prompt")

    @validator('character_prompts')
    def validate_character_prompts(cls, v):
        return [validate_safe_text(prompt, "Character prompt") for prompt in v if prompt]

    @validator('npc_prompts')
    def validate_npc_prompts(cls, v):
        return [validate_safe_text(prompt, "NPC prompt") for prompt in v if prompt]


class SessionInfoResponse(BaseModel):
    """Расширенная информация о сессии."""
    session_id: str
    session_name: str
    game_mode: str
    player_count: int
    max_players: int
    status: str
    description: Optional[str] = None
    players: List[PlayerResponse] = []


# === Helpers ===

def _create_session_internal(
    session_id: str,
    config: SessionConfig
) -> Session:
    """
    Внутренняя функция для создания сессии через SessionFactory.

    Создаёт Session со всеми зависимостями:
    - ChromaClient
    - Generator
    - Logger
    - EventPool
    - Delivery
    - Manipulator
    - Orchestrator
    """
    # Используем SessionFactory для создания полноценной сессии
    # SessionFactory автоматически регистрирует сессию в SessionManager
    session = session_factory.create_session(config)

    return session


# === Endpoints ===

@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(request: SessionCreateRequest):
    """
    Создать новую игровую сессию со всеми зависимостями.

    Создаёт:
    - Session с ChromaClient, Generator, Logger
    - EventPool для событий
    - Manipulator для обработки действий
    - Orchestrator для координации

    Returns:
        Информация о созданной сессии
    """
    import logging
    logger = logging.getLogger(__name__)
    
    session_id = str(uuid.uuid4())
    logger.info(f"🟢 Creating session: {session_id} - {request.session_name}")

    # Создаём конфигурацию
    config = SessionConfig(
        session_name=request.session_name,
        game_mode=request.game_mode,
        max_players=request.max_players,
        description=request.description,
        guide=request.guide,
        gemini_api_key=request.gemini_api_key,
        gemini_model=request.gemini_model
    )

    try:
        # Создаём сессию со всеми зависимостями
        session = _create_session_internal(session_id, config)
        logger.info(f"✅ Session created successfully: {session_id}")

        return SessionResponse(
            session_id=session_id,
            session_name=request.session_name,
            game_mode=request.game_mode,
            player_count=0,
            status="created",
            description=request.description
        )

    except ImportError as e:
        logger.error(f"❌ ImportError: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"SKLS зависимости не установлены: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ Exception: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при создании сессии: {str(e)}"
        )


@router.get("", response_model=SessionListResponse)
async def list_sessions():
    """Получить список всех активных сессий."""
    sessions = session_manager.get_all_sessions()
    
    session_list = []
    for session_id, session in sessions.items():
        info = session_manager.get_session_info(session_id)
        if info:
            session_list.append(SessionResponse(
                session_id=session_id,
                session_name=info["session_name"],
                game_mode=info["game_mode"],
                player_count=info["player_count"],
                status="active",
                description=None
            ))
    
    return SessionListResponse(
        sessions=session_list,
        total=len(session_list)
    )


@router.get("/{session_id}/info", response_model=SessionInfoResponse)
async def get_session_info(session_id: str):
    """Получить расширенную информацию о сессии."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Получаем игроков сессии
    players = []
    for player_id, player_data in active_players.items():
        if player_data["session_id"] == session_id:
            players.append(PlayerResponse(
                player_id=player_id,
                player_name=player_data["player_name"],
                character_name=player_data["character_name"],
                connected=player_data["connected"]
            ))

    return SessionInfoResponse(
        session_id=session_id,
        session_name=session.session_name,
        game_mode=session.game_mode,
        player_count=len(players),
        max_players=settings.SESSION_MAX_PLAYERS,  # Use settings instead of hardcoded value
        status="active",
        description=None,
        players=players
    )


@router.post("/{session_id}/start", response_model=SessionResponse)
async def start_session(session_id: str, request: SessionStartRequest):
    """
    Запустить игровую сессию с инициализацией сцены и персонажей.

    Инициализирует:
    - Начальную сцену
    - Персонажей игроков
    - NPC

    Returns:
        Информация о запущенной сессии
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        # Создаём тестовую сцену без AI генерации
        from core.schemas.in_game import SceneNode, Coordinate2D, UnifiedObject, ObjectType
        
        scene = SceneNode(
            name="The Drunken Dragon",
            description="A dimly lit tavern with worn wooden tables and the smell of ale.",
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
        session.current_scene = scene
        
        # Генерируем и добавляем персонажей игроков (без AI, создаём напрямую)
        from core.entity.player import Player
        from core.schemas.in_game import Character, CharacterClass, AbilityScores, SpellAbility, Condition
        
        for i, prompt in enumerate(request.character_prompts):
            # Создаём простого персонажа
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
                    strength=15,
                    dexterity=12,
                    constitution=14,
                    intelligence=10,
                    wisdom=10,
                    charisma=10
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
                generator=session.generator,
                logger=session.logger.getChild("player_orchestrator")
            )
            player_orchestrator.add_state(session)

            event_queue = session.event_pool.subscribe(character.name)

            player = Player(
                character=character,
                event_queuee=event_queue,
                logger=session.logger.getChild("player"),
                orchestrator=player_orchestrator
            )
            player.inject_state(session)
            session.players.append(player)

        # Генерируем и добавляем NPC
        for i, prompt in enumerate(request.npc_prompts):
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
                    strength=10,
                    dexterity=10,
                    constitution=10,
                    intelligence=10,
                    wisdom=10,
                    charisma=10
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
            session._init_npc(npc_character)

        session.logger.info(
            f"Сессия запущена: {len(session.players)} игроков, {len(session.npcs)} NPC"
        )

        # Отправляем сообщение всем игрокам через Delivery
        session.delivery.master_message(
            f"Welcome to {scene.name}! {scene.description}"
        )
        session.delivery.session_updated(session)

        return SessionResponse(
            session_id=session_id,
            session_name=session.session_name,
            game_mode=session.game_mode.value,
            player_count=len(session.players),
            status="running",
            description=None
        )

    except Exception as e:
        session.logger.error(f"Ошибка при запуске сессии: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при запуске сессии: {str(e)}"
        )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Получить информацию о конкретной сессии."""
    info = session_manager.get_session_info(session_id)
    
    if not info:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(
        session_id=session_id,
        session_name=info["session_name"],
        game_mode=info["game_mode"],
        player_count=info["player_count"],
        status="active",
        description=None
    )


@router.delete("/{session_id}", status_code=204)
async def delete_session(session_id: str):
    """
    Удалить сессию и отключить всех игроков.
    
    Внимание: Это действие необратимо!
    """
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    await session_manager.remove_session(session_id)
    return None


# Store for active players (temporary, until DB integration)
active_players: Dict[str, Dict[str, any]] = {}

@router.post("/{session_id}/players", response_model=PlayerResponse)
async def join_session(session_id: str, request: PlayerJoinRequest):
    """
    Добавить игрока в сессию.
    Возвращает player_id для подключения через WebSocket.
    """
    # For now, just create a player entry without checking session
    # Session existence check requires game engine integration
    
    # Generate player ID
    player_id = str(uuid.uuid4())

    # Store player
    active_players[player_id] = {
        "session_id": session_id,
        "player_name": request.player_name,
        "character_name": request.character_name,
        "connected": True
    }

    return PlayerResponse(
        player_id=player_id,
        player_name=request.player_name,
        character_name=request.character_name,
        connected=True
    )


@router.delete("/{session_id}/players/{player_id}", status_code=204)
async def leave_session(session_id: str, player_id: str):
    """Удалить игрока из сессии."""
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    # Отключаем WebSocket если подключен
    session_manager.unregister_player_websocket(session_id, player_id)
    session_manager.unsubscribe_player_from_events(session_id, player_id)

    # Удаляем игрока из active_players
    if player_id in active_players:
        del active_players[player_id]

    # Удаляем игрока из session.players если сессия активна
    session = session_manager.get_session(session_id)
    if session:
        session.players = [p for p in session.players if p.character.name != player_id]

    return None


@router.get("/{session_id}/players", response_model=List[PlayerResponse])
async def get_session_players(session_id: str):
    """Получить список всех игроков в сессии."""
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    # Возвращаем игроков для этой сессии
    players = []
    for player_id, player_data in active_players.items():
        if player_data["session_id"] == session_id:
            players.append(PlayerResponse(
                player_id=player_id,
                player_name=player_data["player_name"],
                character_name=player_data["character_name"],
                connected=player_data["connected"]
            ))

    return players


@router.get("/{session_id}/game_info", response_model=dict)
async def get_session_game_info(session_id: str):
    """
    Get detailed game session info including players, NPCs, and scene.
    For active game sessions with full engine integration.
    """
    # Try to get from active game sessions first
    session = game_session_managers.get(session_id)
    if not session:
        # Fallback to session manager
        session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        # Build players data
        players_data = []
        for player in session.players:
            if hasattr(player, 'character'):
                char = player.character
                stats = getattr(char, 'stats', None)
                players_data.append({
                    "name": getattr(char, 'name', 'Unknown'),
                    "race": getattr(char, 'race', 'Human'),
                    "char_class": getattr(char, 'char_class', 'Fighter'),
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
        for npc in session.npcs:
            if hasattr(npc, 'character'):
                char = npc.character
                stats = getattr(char, 'stats', None)
                npcs_data.append({
                    "name": getattr(char, 'name', 'Unknown'),
                    "race": getattr(char, 'race', 'Human'),
                    "char_class": getattr(char, 'char_class', 'Commoner'),
                    "alignment": getattr(char, 'alignment', 'Neutral'),
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

        # Build scene data
        scene_data = None
        if hasattr(session, 'current_scene') and session.current_scene:
            scene = session.current_scene
            scene_data = {
                "name": getattr(scene, 'name', 'Unknown'),
                "description": getattr(scene, 'description', ''),
            }

        return {
            "session_id": session_id,
            "session_name": session.session_name,
            "game_mode": session.game_mode.value if hasattr(session.game_mode, 'value') else str(session.game_mode),
            "status": "running",
            "players": players_data,
            "npcs": npcs_data,
            "scene": scene_data,
        }

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to get game info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get game info: {str(e)}")


# === Real Game Endpoints ===

class SessionInitRequest(BaseModel):
    session_name: str
    game_mode: str = "STORY"
    scene_prompt: Optional[str] = None
    character_prompts: List[str] = []
    npc_prompts: List[str] = []
    gemini_api_key: Optional[str] = None


# Global stores for active game sessions
active_game_sessions: Dict[str, Dict[str, Any]] = {}
game_session_managers: Dict[str, Session] = {}
game_event_pools: Dict[str, EventPool] = {}
game_deliveries: Dict[str, Any] = {}


@router.post("/start_real_game", response_model=dict)
async def start_real_game(request: SessionInitRequest, background_tasks: BackgroundTasks):
    """
    Start a REAL game session with the actual game engine running.
    This creates characters, NPCs, scene, and starts the game loop.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Starting REAL game session: {request.session_name}")

    try:
        session_id = str(uuid.uuid4())

        # Create event pool
        event_pool = EventPool()
        game_event_pools[session_id] = event_pool
        logger.info(f"[{session_id}] EventPool created")

        # Setup components
        generator = Generator(
            GoogleGenAI(
                api_key=request.gemini_api_key or os.getenv("GEMINI_API_KEY", "NO_KEY"),
                logger=logger,
                model_name="gemini-2.0-flash"
            ),
            logger_instance=logger
        )

        # Create session
        session = Session(
            session_name=request.session_name,
            chroma_client=None,  # Simplified mode without chroma
            logger=logger.getChild("session"),
            generator=generator,
            event_pool=event_pool,
            delivery=None  # Will be set after creation
        )

        # Set game mode
        if request.game_mode.upper() == "COMBAT":
            session.game_mode = GameModes.COMBAT
        else:
            session.game_mode = GameModes.STORY

        # Create delivery (REST API compatible)
        delivery_queue = event_pool.subscribe(f"delivery_{session_id}")
        delivery = RESTAPIDelivery(delivery_queue, logger, session_id)
        delivery.set_session(session)  # Set session reference
        session.delivery = delivery
        game_deliveries[session_id] = delivery
        logger.info(f"[{session_id}] RESTAPIDelivery created")

        # Create and set orchestrator
        orchestrator = Orchestrator(
            generator=generator,
            logger=logger.getChild("orchestrator")
        )
        orchestrator.add_state(session)
        session._init_orchestrator(orchestrator)

        # Generate scene (with fallback if AI fails)
        logger.info(f"[{session_id}] Generating scene...")
        try:
            scene = generator.generate_one_shot(
                pydantic_model=SceneNode,
                prompt=request.scene_prompt or "A medieval tavern"
            )
        except Exception as e:
            logger.warning(f"AI scene generation failed: {e}, using fallback")
            from core.schemas.in_game import Coordinate2D, UnifiedObject
            scene = SceneNode(
                name="Default Tavern",
                description="A cozy medieval tavern with warm fire and wooden tables.",
                objects=[],
                center_position=Coordinate2D(x=10, y=10),
                dimensions=Coordinate2D(x=20, y=20),
                scale_unit="meters"
            )
        session.current_scene = scene
        session.current_location_name = scene.name
        logger.info(f"[{session_id}] Scene: {scene.name}")

        # Generate player characters (with fallback if AI fails)
        character_prompts = request.character_prompts or ["A brave hero"]
        if not character_prompts:
            character_prompts = ["A brave hero"]
        for i, prompt in enumerate(character_prompts):
            try:
                char = generator.generate_one_shot(
                    pydantic_model=Character,
                    prompt=prompt
                )
            except Exception as e:
                logger.warning(f"AI character generation failed: {e}, using fallback")
                from core.schemas.in_game import AbilityScores
                char = Character(
                    name=f"Hero{i+1}",
                    race="Human",
                    char_class="Fighter",
                    level=1,
                    backstory_summary="A brave adventurer",
                    personality_traits=["Brave", "Kind"],
                    max_hp=10,
                    current_hp=10,
                    temp_hp=0,
                    armor_class=12,
                    speed=30,
                    stats=AbilityScores(strength=10, dexterity=10, constitution=10, intelligence=10, wisdom=10, charisma=10),
                    inventory=[],
                    active_conditions_list=[],
                    resources={},
                    position=Coordinate2D(x=10, y=10),
                    abilities=[],
                    active_conditions="",
                    proficiency_bonus=2,
                    is_alive=True,
                    initiative_bonus=0,
                    short_summary="A brave hero"
                )
            player_queue = event_pool.subscribe(f"player_{char.name}")
            player = Player(
                character=char,
                event_queuee=player_queue,
                logger=logger.getChild("player"),
                orchestrator=orchestrator
            )
            session.players.append(player)
            logger.info(f"[{session_id}] Player: {char.name}")

        # Generate NPCs (with fallback if AI fails)
        npc_prompts = request.npc_prompts or ["A mysterious stranger"]
        if not npc_prompts:
            npc_prompts = ["A mysterious stranger"]
        for i, prompt in enumerate(npc_prompts):
            try:
                npc_char = generator.generate_one_shot(
                    pydantic_model=NPCCharacter,
                    prompt=prompt
                )
            except Exception as e:
                logger.warning(f"AI NPC generation failed: {e}, using fallback")
                from core.schemas.in_game import AbilityScores
                npc_char = NPCCharacter(
                    name=f"NPC{i+1}",
                    race="Human",
                    char_class="Commoner",
                    level=1,
                    backstory_summary="A local villager",
                    personality_traits=["Friendly"],
                    max_hp=8,
                    current_hp=8,
                    temp_hp=0,
                    armor_class=10,
                    speed=30,
                    stats=AbilityScores(strength=10, dexterity=10, constitution=10, intelligence=10, wisdom=10, charisma=10),
                    inventory=[],
                    active_conditions_list=[],
                    resources={},
                    position=Coordinate2D(x=10, y=10),
                    abilities=[],
                    active_conditions="",
                    proficiency_bonus=2,
                    is_alive=True,
                    initiative_bonus=0,
                    short_summary="A villager",
                    motivation="To live peacefully",
                    alignment="Neutral Good",
                    memory="",
                    current_scene=scene.name
                )
            npc_char.current_scene = scene.name
            npc_queue = event_pool.subscribe(f"npc_{npc_char.name}")
            npc = NPC(
                character=npc_char,
                event_queuee=npc_queue,
                logger=logger.getChild("npc")
            )
            session.npcs.append(npc)
            logger.info(f"[{session_id}] NPC: {npc_char.name}")

        # Store session
        active_game_sessions[session_id] = {
            "delivery": delivery,
            "players": {p.character.name: p for p in session.players},
            "session_object": session
        }
        game_session_managers[session_id] = session

        logger.info(f"[{session_id}] REAL GAME STARTED!")

        return {
            "status": "running",
            "session_id": session_id,
            "session_name": request.session_name,
            "game_mode": request.game_mode,
            "scene": scene.name,
            "players": [p.character.name for p in session.players],
            "npcs": [n.character.name for n in session.npcs],
            "message": "Real game session started with AI!"
        }

    except Exception as e:
        logger.error(f"Failed to start real game: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start game: {str(e)}")


class PlayerActionRequest(BaseModel):
    character_name: str
    action: str


@router.post("/{session_id}/player_action", response_model=dict)
async def process_player_action(session_id: str, request: PlayerActionRequest):
    """
    Process player action through the game engine.
    Uses session's Delivery for proper interaction.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Get active session
    session = game_session_managers.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Active game session not found")
    
    try:
        logger.info(f"[{session_id}] Processing action for {request.character_name}: {request.action}")
        
        # Use session's delivery to process action
        if not session.delivery:
            raise ValueError("Session has no delivery")
        
        # Process through delivery
        result = session.delivery.process_player_action(
            character_name=request.character_name,
            action_text=request.action
        )
        
        logger.info(f"[{session_id}] Action result: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"[{session_id}] Failed to process action: {e}", exc_info=True)
        return {
            "session_id": session_id,
            "character": request.character_name,
            "action": request.action,
            "response": f"Error processing action: {str(e)}",
            "status": "error"
        }
