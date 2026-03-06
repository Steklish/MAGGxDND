"""
REST API router для управления игровыми сессиями.

Эндпоинты:
- POST /sessions - Создать сессию
- GET /sessions - Список сессий
- GET /sessions/{session_id} - Информация о сессии
- DELETE /sessions/{session_id} - Удалить сессию
- POST /sessions/{session_id}/players - Добавить игрока
- DELETE /sessions/{session_id}/players/{player_id} - Удалить игрока
- POST /sessions/{session_id}/start - Запустить игровую сессию
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid

from server.src.game.session_manager import session_manager
from server.src.game.session_factory import session_factory, SessionConfig
from game.engine import Session
from game.event_pool import EventPool
from server.src.delivery.game_delivery import GameDelivery
from schemas.in_game import Character, NPCCharacter, GameModes
from entity.orchestrator import Orchestrator

router = APIRouter(prefix="/sessions", tags=["sessions"])

# Store for active players (temporary, until DB integration)
active_players: Dict[str, Dict[str, any]] = {}


# === Schemas ===

class SessionCreateRequest(BaseModel):
    """Запрос на создание сессии."""
    session_name: str = Field(..., description="Название сессии")
    game_mode: str = Field(default="STORY", description="Режим игры: STORY или COMBAT")
    max_players: int = Field(default=5, description="Максимум игроков")
    description: Optional[str] = Field(None, description="Описание сессии")
    guide: Optional[str] = Field(None, description="Сюжетная подсказка для AI")
    scene_prompt: Optional[str] = Field(None, description="Описание начальной сцены")
    character_prompts: List[str] = Field(default=[], description="Описания персонажей игроков")
    npc_prompts: List[str] = Field(default=[], description="Описания NPC")
    
    # Настройки AI (опционально)
    gemini_api_key: Optional[str] = Field(None, description="API ключ Gemini")
    gemini_model: str = Field(default="gemini-2.0-flash", description="Модель Gemini")


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
    player_name: str = Field(..., description="Имя игрока")
    character_name: Optional[str] = Field(None, description="Имя персонажа")
    character_prompt: Optional[str] = Field(None, description="Описание персонажа для генерации")


class PlayerResponse(BaseModel):
    """Информация об игроке."""
    player_id: str
    player_name: str
    character_name: Optional[str]
    connected: bool


class SessionStartRequest(BaseModel):
    """Запрос на запуск игровой сессии."""
    scene_prompt: str = Field(..., description="Описание начальной сцены")
    character_prompts: List[str] = Field(default=[], description="Описания персонажей")
    npc_prompts: List[str] = Field(default=[], description="Описания NPC")


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
        max_players=5,  # TODO: Get from session config
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
        from schemas.in_game import SceneNode, Coordinate2D, UnifiedObject, ObjectType
        
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
        from entity.player import Player
        from schemas.in_game import Character, CharacterClass, AbilityScores, SpellAbility, Condition
        
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
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    # Check if player already joined this session (by player_name)
    for existing_player_id, player_data in active_players.items():
        if player_data["session_id"] == session_id and player_data["player_name"] == request.player_name:
            raise HTTPException(
                status_code=400,
                detail=f"Player '{request.player_name}' has already joined this session"
            )

    # Check session capacity
    session_players_count = sum(1 for p in active_players.values() if p["session_id"] == session_id)
    session = session_manager.get_session(session_id)
    max_players = session.max_players if session else 5
    
    if session_players_count >= max_players:
        raise HTTPException(
            status_code=400,
            detail=f"Session is full (max {max_players} players)"
        )

    # Генерируем ID игрока
    player_id = str(uuid.uuid4())

    # Сохраняем игрока
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
    
    # TODO: Удалить игрока из session.players
    
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
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        # Get active session data
        from server.src.game.session_manager import session_manager as sm
        session_data = {}
        
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
        logger.error(f"Failed to get game info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get game info: {str(e)}")
