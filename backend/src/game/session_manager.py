"""
Session Manager - Singleton для управления игровыми сессиями.

Обеспечивает централизованный доступ к сессиям игры из любого места FastAPI приложения.

ВАЖНО: SessionManager не владеет сессиями - он только предоставляет доступ к ним.
Владелец сессии - это сам объект Session, который содержит event_pool, players, npcs и т.д.
"""
from typing import Dict, Optional, Set
import asyncio
from fastapi import WebSocket
import threading

from core.game.engine import Session
from core.game.event_pool import EventPool, SubscriberQueue
from core.schemas.orchestration import Event


# ANSI color codes for console
class Colors:
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    PURPLE = '\033[35m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class SessionManager:
    """
    Singleton-реестр для управления доступом к игровым сессиям.
    
    НЕ владеет сессиями - только предоставляет доступ из веб-слоя.
    Session остаётся единственным источником истины для состояния игры.
    
    Хранит:
    - Ссылки на Session объекты
    - WebSocket подключения игроков
    - SubscriberQueue для каждого игрока (для получения событий)
    """
    
    _instance: Optional['SessionManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        # Инициализация только один раз
        if self._initialized:
            return
            
        self._sessions: Dict[str, Session] = {}
        # НЕ храним EventPool отдельно - берём из session.event_pool!
        self._player_websockets: Dict[str, Dict[str, WebSocket]] = {}
        self._player_subscriber_queues: Dict[str, Dict[str, SubscriberQueue]] = {}
        self._session_locks: Dict[str, asyncio.Lock] = {}
        self._initialized = True
    
    @classmethod
    def get_instance(cls) -> 'SessionManager':
        """Получить экземпляр SessionManager."""
        return cls()
    
    def register_session(
        self,
        session_id: str,
        session: Session
    ) -> None:
        """
        Зарегистрировать игровую сессию в реестре.

        Args:
            session_id: Уникальный ID сессии
            session: Экземпляр Session (владеет своим event_pool)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        with self._lock:
            logger.info(f"📝 Registering session: {session_id} - {session.session_name}")
            if session_id in self._sessions:
                logger.warning(f"⚠️ Session {session_id} already exists! Overwriting.")
            self._sessions[session_id] = session
            self._player_websockets[session_id] = {}
            self._player_subscriber_queues[session_id] = {}
            self._session_locks[session_id] = asyncio.Lock()
            logger.info(f"✅ Session registered: {session_id}")
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Получить сессию по ID."""
        return self._sessions.get(session_id)
    
    def get_event_pool(self, session_id: str) -> Optional[EventPool]:
        """
        Получить EventPool сессии.
        
        NOTE: EventPool принадлежит Session, не храним отдельную ссылку.
        """
        session = self._sessions.get(session_id)
        return session.event_pool if session else None
    
    def get_all_sessions(self) -> Dict[str, Session]:
        """Получить все активные сессии."""
        return self._sessions.copy()
    
    def session_exists(self, session_id: str) -> bool:
        """Проверить существование сессии."""
        return session_id in self._sessions
    
    async def get_session_lock(self, session_id: str) -> asyncio.Lock:
        """Получить asyncio.Lock для синхронизации доступа к сессии."""
        return self._session_locks.get(session_id, asyncio.Lock())
    
    # === WebSocket Management ===
    
    async def register_player_websocket(
        self,
        session_id: str,
        player_id: str,
        websocket: WebSocket
    ) -> bool:
        """
        Зарегистрировать WebSocket подключение игрока.
        
        Args:
            session_id: ID сессии
            player_id: ID игрока
            websocket: WebSocket подключение
            
        Returns:
            True если успешно, False если сессия не найдена
        """
        if session_id not in self._player_websockets:
            return False
            
        self._player_websockets[session_id][player_id] = websocket
        return True
    
    def unregister_player_websocket(
        self,
        session_id: str,
        player_id: str
    ) -> None:
        """Отключить игрока от сессии."""
        if session_id in self._player_websockets:
            self._player_websockets[session_id].pop(player_id, None)
    
    def get_player_websocket(
        self,
        session_id: str,
        player_id: str
    ) -> Optional[WebSocket]:
        """Получить WebSocket игрока."""
        return self._player_websockets.get(session_id, {}).get(player_id)
    
    def get_all_session_websockets(
        self,
        session_id: str
    ) -> Dict[str, WebSocket]:
        """Получить все WebSocket подключения сессии."""
        return self._player_websockets.get(session_id, {}).copy()
    
    # === Subscriber Queue Management ===
    
    def subscribe_player_to_events(
        self,
        session_id: str,
        player_id: str,
        exclude_self: bool = False
    ) -> Optional[SubscriberQueue]:
        """
        Подписать игрока на события сессии.
        
        Args:
            session_id: ID сессии
            player_id: ID игрока
            exclude_self: Если True, игрок не получает свои собственные события
            
        Returns:
            SubscriberQueue для игрока или None если сессия не найдена
        """
        # Берём EventPool из Session (единственный источник истины)
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        event_pool = session.event_pool
        subscriber_id = f"{session_id}:{player_id}"
        
        queue = event_pool.subscribe(subscriber_id)
        
        if session_id not in self._player_subscriber_queues:
            self._player_subscriber_queues[session_id] = {}
        
        self._player_subscriber_queues[session_id][player_id] = queue
        return queue
    
    def unsubscribe_player_from_events(
        self,
        session_id: str,
        player_id: str
    ) -> None:
        """Отписать игрока от событий."""
        if session_id in self._player_subscriber_queues:
            self._player_subscriber_queues[session_id].pop(player_id, None)
        
        session = self._sessions.get(session_id)
        if session:
            subscriber_id = f"{session_id}:{player_id}"
            session.event_pool.unsubscribe(subscriber_id)
    
    def get_subscriber_queue(
        self,
        session_id: str,
        player_id: str
    ) -> Optional[SubscriberQueue]:
        """Получить SubscriberQueue игрока."""
        return self._player_subscriber_queues.get(session_id, {}).get(player_id)
    
    # === Broadcasting ===

    async def broadcast_to_session(
        self,
        session_id: str,
        event: Event,
        exclude_player_id: Optional[str] = None
    ) -> None:
        """
        Отправить событие всем игрокам в сессии.

        Args:
            session_id: ID сессии
            event: Событие для отправки
            exclude_player_id: ID игрока для исключения (отправитель)
        """
        # Берём EventPool из Session
        session = self._sessions.get(session_id)
        if not session:
            return

        # Log journey stage
        print(f"\n{Colors.PURPLE}┌{'─' * 90}{Colors.RESET}")
        print(f"{Colors.PURPLE}│{Colors.RESET} ⚙️ {Colors.BOLD}CORE ENGINE PROCESSING: STAGE 3/5{Colors.RESET}")
        print(f"{Colors.PURPLE}├{'─' * 90}{Colors.RESET}")
        print(f"{Colors.PURPLE}│{Colors.RESET}    Session: {session_id}")
        print(f"{Colors.PURPLE}│{Colors.RESET}    Event Type: {Colors.YELLOW}{event.event_type}{Colors.RESET}")
        print(f"{Colors.PURPLE}│{Colors.RESET}    Source: {event.source}")
        print(f"{Colors.PURPLE}│{Colors.RESET}    Journey Stage: {Colors.MAGENTA}Backend → Core Engine → EventPool{Colors.RESET}")
        print(f"{Colors.PURPLE}│{Colors.RESET}    Next: {Colors.CYAN}EventPool → WebSocket{Colors.RESET}")
        print(f"{Colors.PURPLE}└{'─' * 90}{Colors.RESET}\n")

        if exclude_player_id:
            publisher_id = f"{session_id}:{exclude_player_id}"
            session.event_pool.publish_to_others(publisher_id, event)
        else:
            session.event_pool.add_event(event)
    
    async def broadcast_to_all_sessions(self, event: Event) -> None:
        """Отправить событие всем игрокам во всех сессиях."""
        for session_id, session in self._sessions.items():
            session.event_pool.add_event(event)
    
    # === Session Cleanup ===
    
    async def remove_session(self, session_id: str) -> None:
        """
        Удалить сессию и освободить ресурсы.
        
        Args:
            session_id: ID сессии для удаления
        """
        with self._lock:
            # Отключить всех игроков
            if session_id in self._player_websockets:
                for player_id, websocket in self._player_websockets[session_id].items():
                    try:
                        await websocket.close()
                    except Exception:
                        pass
                del self._player_websockets[session_id]
            
            # Очистить subscriber queues
            if session_id in self._player_subscriber_queues:
                del self._player_subscriber_queues[session_id]
            
            # Session и его EventPool удаляются автоматически (garbage collection)
            # когда все ссылки на них будут удалены
            
            # Удалить сессию из реестра
            self._sessions.pop(session_id, None)
            
            # Удалить lock
            self._session_locks.pop(session_id, None)
    
    def get_session_info(self, session_id: str) -> Optional[dict]:
        """Получить информацию о сессии."""
        if session_id not in self._sessions:
            return None
        
        session = self._sessions[session_id]
        return {
            "session_id": session_id,
            "session_name": session.session_name,
            "player_count": len(self._player_websockets.get(session_id, {})),
            "event_count": session.event_pool.get_event_count(),
            "game_mode": session.game_mode.value,
        }


# Глобальный экземпляр
session_manager = SessionManager.get_instance()
