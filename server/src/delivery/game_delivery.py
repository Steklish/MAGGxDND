"""
GameDelivery - реализация абстрактного класса Delivery для WebSocket.

Связывает игровой движок с WebSocket подключениями игроков.
ВАЖНО: GameDelivery хранит прямую ссылку на Session для немедленного доступа.
"""
from typing import TYPE_CHECKING, Optional
import asyncio
from logging import Logger
from interface.delivery import Delivery
from game.event_pool import SubscriberQueue

if TYPE_CHECKING:
    from game.engine import Session
    from entity.player import Player
    from schemas.in_game import Character


class GameDelivery(Delivery):
    """
    Реализация Delivery для отправки сообщений через WebSocket.
    
    Хранит прямую ссылку на Session для немедленного доступа к состоянию.
    """
    
    def __init__(
        self,
        session_id: str,
        session: 'Session',
        event_queue: SubscriberQueue,
        logger: Logger
    ):
        """
        Инициализировать GameDelivery для конкретной сессии.
        
        Args:
            session_id: ID игровой сессии
            session: Прямая ссылка на Session (для немедленного доступа)
            event_queue: Очередь событий для получения событий из EventPool
            logger: Логгер для доставки
        """
        # Вызываем конструктор базового класса
        super().__init__(event_queue, logger)
        
        self.session_id = session_id
        self.session = session  # ← Прямая ссылка на Session!
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
    
    def _get_event_loop(self) -> asyncio.AbstractEventLoop:
        """Получить event loop для асинхронных задач."""
        if self._loop is None:
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                # Если нет текущего loop, создаём новый
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop
    
    async def _send_to_websocket(self, player_id: str, message: dict) -> None:
        """
        Отправить сообщение конкретному игроку через WebSocket.
        
        Args:
            player_id: ID игрока
            message: Сообщение для отправки
        """
        from server.src.game.session_manager import session_manager
        
        websocket = session_manager.get_player_websocket(self.session_id, player_id)
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception as e:
                self.logger.debug(f"Ошибка отправки сообщения игроку {player_id}: {e}")
        else:
            self.logger.debug(f"WebSocket для игрока {player_id} не найден")

    async def _broadcast_to_session(self, message: dict, exclude_player: Optional[str] = None) -> None:
        """
        Отправить сообщение всем игрокам в сессии.
        
        Args:
            message: Сообщение для отправки
            exclude_player: ID игрока для исключения (отправитель)
        """
        from server.src.game.session_manager import session_manager
        
        websockets = session_manager.get_all_session_websockets(self.session_id)
        if not websockets:
            self.logger.debug(f"Нет подключенных игроков в сессии {self.session_id}")
            return
            
        for player_id, websocket in websockets.items():
            if exclude_player and player_id == exclude_player:
                continue
            try:
                await websocket.send_json(message)
                self.logger.debug(f"Отправлено игроку {player_id}: {message.get('type', 'unknown')}")
            except Exception as e:
                self.logger.debug(f"Ошибка отправки сообщения игроку {player_id}: {e}")
    
    def master_message(self, text: str, tag: Optional[str] = None) -> None:
        """
        Отобразить сообщение от ГМа (наррация, описание).
        
        Немедленно отправляет сообщение всем игрокам и логирует в Session.
        
        Args:
            text: Текст сообщения
            tag: Опциональный тег для категоризации
        """
        message = {
            "type": "MASTER_MESSAGE",
            "text": text,
            "tag": tag
        }
        
        # Логируем в Session (немедленная связь)
        self.session.logger.info(f"[MASTER] {text}")
        
        # Отправляем через WebSocket
        loop = self._get_event_loop()
        if loop.is_running():
            loop.create_task(self._broadcast_to_session(message))
        else:
            loop.run_until_complete(self._broadcast_to_session(message))
        
        # Добавляем сообщение в историю Session (немедленная связь)
        from schemas.orchestration import Message
        self.session.messages.append(
            Message(sender_name="GM", text=text, tag=tag or "narration")
        )
        
        # Ограничиваем историю
        if len(self.session.messages) > 20:
            self.session.messages = self.session.messages[-20:]
    
    def player_request(self, character: "Character") -> str:
        """
        Запросить действие от игрока.
        
        В WebSocket реализации это не блокирующий вызов,
        а триггер для ожидания сообщения от клиента.
        
        Args:
            character: Персонаж игрока
            
        Returns:
            Пустая строка (действие приходит через WebSocket)
        """
        message = {
            "type": "PLAYER_REQUEST",
            "character_id": character.id,
            "character_name": character.name
        }
        
        # Логируем в Session
        self.session.logger.debug(f"[PLAYER_REQUEST] {character.name}")
        
        # Отправляем через WebSocket
        loop = self._get_event_loop()
        if loop.is_running():
            loop.create_task(self._broadcast_to_session(message))
        else:
            loop.run_until_complete(self._broadcast_to_session(message))
        
        return ""
    
    def choose_player(self, session: "Session") -> "Player":
        """
        Выбрать следующего игрока для хода.
        
        Args:
            session: Игровая сессия
            
        Returns:
            Игрок, чей сейчас ход
        """
        if session.players:
            active_player = session.players[0]
            
            message = {
                "type": "TURN_UPDATE",
                "active_player_id": active_player.id,
                "active_player_name": active_player.character.name
            }
            
            # Логируем в Session
            session.logger.info(f"[TURN] Ход игрока {active_player.character.name}")
            
            # Отправляем через WebSocket
            loop = self._get_event_loop()
            if loop.is_running():
                loop.create_task(self._broadcast_to_session(message))
            else:
                loop.run_until_complete(self._broadcast_to_session(message))
            
            return active_player
        
        raise ValueError("No players in session")
    
    def session_updated(self, session: "Session") -> None:
        """
        Уведомить об обновлении состояния сессии.
        
        Немедленно отправляет обновление всем игрокам.
        
        Args:
            session: Обновлённая сессия
        """
        # Логируем обновление
        session.logger.debug(f"[SESSION_UPDATE] {session.session_name}")
        
        # Сериализуем важное состояние для отправки клиентам
        message = {
            "type": "SESSION_UPDATE",
            "data": {
                "session_name": session.session_name,
                "game_mode": session.game_mode.value,
                "scene_name": session.current_scene.name if session.current_scene else None,
                "player_count": len(session.players),
                "npc_count": len(session.npcs),
                "turn_queue": [
                    {
                        "entity_id": entity.id if hasattr(entity, 'id') else str(entity),
                        "entity_type": "player" if isinstance(entity, Player) else "npc"
                    }
                    for entity, _, _ in session.turn_queue
                ]
            }
        }
        
        # Отправляем через WebSocket
        loop = self._get_event_loop()
        if loop.is_running():
            loop.create_task(self._broadcast_to_session(message))
        else:
            loop.run_until_complete(self._broadcast_to_session(message))
    
    async def get_next_message(self) -> dict:
        """
        Получить следующее сообщение из очереди.
        
        Returns:
            Сообщение из очереди
        """
        return await self._message_queue.get()
    
    def send_to_player(self, player_id: str, message: dict) -> None:
        """
        Отправить сообщение конкретному игроку.
        
        Args:
            player_id: ID игрока
            message: Сообщение
        """
        self.session.logger.debug(f"[SEND_TO_PLAYER] {player_id}: {message.get('type', 'unknown')}")
        
        loop = self._get_event_loop()
        if loop.is_running():
            loop.create_task(self._send_to_websocket(player_id, message))
        else:
            loop.run_until_complete(self._send_to_websocket(player_id, message))
    
    def send_character_update(
        self,
        character_id: str,
        updates: dict,
        exclude_player: Optional[str] = None
    ) -> None:
        """
        Отправить обновление состояния персонажа.
        
        Args:
            character_id: ID персонажа
            updates: Данные для обновления
            exclude_player: Исключить игрока (отправителя)
        """
        message = {
            "type": "CHARACTER_UPDATE",
            "character_id": character_id,
            "updates": updates
        }
        
        self.session.logger.debug(f"[CHARACTER_UPDATE] {character_id}: {updates}")
        
        loop = self._get_event_loop()
        if loop.is_running():
            loop.create_task(self._broadcast_to_session(message, exclude_player))
        else:
            loop.run_until_complete(self._broadcast_to_session(message, exclude_player))
    
    def send_scene_update(self, scene_data: dict) -> None:
        """
        Отправить обновление сцены.
        
        Args:
            scene_data: Данные сцены
        """
        message = {
            "type": "SCENE_UPDATE",
            "scene": scene_data
        }
        
        self.session.logger.debug(f"[SCENE_UPDATE] {scene_data.get('name', 'unknown')}")
        
        loop = self._get_event_loop()
        if loop.is_running():
            loop.create_task(self._broadcast_to_session(message))
        else:
            loop.run_until_complete(self._broadcast_to_session(message))
    
    def send_combat_event(self, event_data: dict) -> None:
        """
        Отправить событие боя.
        
        Args:
            event_data: Данные события боя
        """
        message = {
            "type": "COMBAT_EVENT",
            "data": event_data
        }
        
        self.session.logger.info(f"[COMBAT_EVENT] {event_data}")
        
        loop = self._get_event_loop()
        if loop.is_running():
            loop.create_task(self._broadcast_to_session(message))
        else:
            loop.run_until_complete(self._broadcast_to_session(message))
