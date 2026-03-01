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
    session = session_factory.create_session(config)
    
    # Регистрируем сессию в SessionManager
    session_manager.register_session(session_id, session)
    
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
    session_id = str(uuid.uuid4())
    
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
        
        return SessionResponse(
            session_id=session_id,
            session_name=request.session_name,
            game_mode=request.game_mode,
            player_count=0,
            status="created",
            description=request.description
        )
        
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"SKLS зависимости не установлены: {str(e)}"
        )
    except Exception as e:
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
        # Используем SessionFactory для инициализации
        session_factory.init_new_session(
            session=session,
            scene_prompt=request.scene_prompt,
            player_characters=[],  # Будут сгенерированы внутри
            npcs=[],
        )
        
        # Генерируем и добавляем персонажей игроков
        from entity.player import Player
        for i, prompt in enumerate(request.character_prompts):
            character = session.generator.generate_one_shot(
                pydantic_model=Character,
                prompt=prompt
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
        for prompt in request.npc_prompts:
            npc_character = session.generator.generate_one_shot(
                pydantic_model=NPCCharacter,
                prompt=prompt
            )
            session._init_npc(npc_character)
        
        session.logger.info(
            f"Сессия запущена: {len(session.players)} игроков, {len(session.npcs)} NPC"
        )
        
        # Отправляем сообщение всем игрокам через Delivery
        scene = session.current_scene
        session.delivery.master_message(
            f"Добро пожаловать в {scene.name}! {scene.description}"
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


@router.post("/{session_id}/players", response_model=PlayerResponse)
async def join_session(session_id: str, request: PlayerJoinRequest):
    """
    Добавить игрока в сессию.
    
    Возвращает player_id для подключения через WebSocket.
    """
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Генерируем ID игрока
    player_id = str(uuid.uuid4())
    
    # TODO: Здесь нужно добавить реальную логику добавления игрока в сессию
    # - Создать Player объект
    # - Добавить в session.players
    # - Создать персонажа если указано character_name
    
    return PlayerResponse(
        player_id=player_id,
        player_name=request.player_name,
        character_name=request.character_name,
        connected=False  # Подключится через WebSocket
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
    
    websockets = session_manager.get_all_session_websockets(session_id)
    
    # TODO: Получить реальных игроков из session.players
    # Для пока возвращаем только подключенные WebSocket
    
    players = []
    for player_id in websockets.keys():
        players.append(PlayerResponse(
            player_id=player_id,
            player_name="Unknown",  # TODO: Получить из Player объекта
            character_name=None,
            connected=True
        ))
    
    return players
