"""
SessionFactory - фабрика для создания игровых сессий со всеми зависимостями.

Инициализирует:
- ChromaClient (векторная база данных)
- Generator (AI генерация)
- Logger (логирование)
- EventPool (события)
- Delivery (доставка сообщений)
- Manipulator (обработка действий)
- Orchestrator (координация)
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional, List
import uuid

from game.engine import Session
from game.event_pool import EventPool
from game.manipulator import Manipulator
from entity.orchestrator import Orchestrator
from entity.player import Player
from entity.npc import NPC
from schemas.in_game import Character, NPCCharacter, SceneNode, GameModes
from server.src.delivery.game_delivery import GameDelivery
from game.event_pool import EventPool
from logging import Logger

# Импорты для SKLS (внешние зависимости)
try:
    from skls_embeddings.chroma_client import ChromaClient
    from skls_embeddings.embedding_client import EmbeddingClient
    from skls_generator.generator import Generator
    from skls_generator.gen_backends.google_gen import GoogleGenAI
    SKLS_AVAILABLE = True
except ImportError:
    SKLS_AVAILABLE = False
    ChromaClient = None  # type: ignore
    EmbeddingClient = None  # type: ignore
    Generator = None  # type: ignore
    GoogleGenAI = None  # type: ignore


class SessionConfig:
    """Конфигурация для создания сессии."""
    
    def __init__(
        self,
        session_name: str,
        game_mode: str = "STORY",
        max_players: int = 5,
        description: Optional[str] = None,
        guide: Optional[str] = None,  # Сюжетная подсказка для AI
        llamacpp_embed_base: str = "localhost:12345",
        llamacpp_chat_base: str = "http://localhost:8080",
        gemini_api_key: Optional[str] = None,
        gemini_model: str = "gemini-2.0-flash",
        log_dir: str = "./log",
        chroma_db_path: str = "./chroma_db/data.db",
    ):
        self.session_name = session_name
        self.game_mode = game_mode
        self.max_players = max_players
        self.description = description
        self.guide = guide
        self.llamacpp_embed_base = llamacpp_embed_base
        self.llamacpp_chat_base = llamacpp_chat_base
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "NO_KEY")
        self.gemini_model = gemini_model
        self.log_dir = log_dir
        self.chroma_db_path = chroma_db_path


class SessionFactory:
    """
    Фабрика для создания полноценных игровых сессий.
    
    Пример использования:
        factory = SessionFactory()
        session = factory.create_session(config)
    """
    
    def __init__(self):
        self._sessions: dict[str, Session] = {}
        self._loggers: dict[str, logging.Logger] = {}
    
    def create_session(self, config: SessionConfig) -> Session:
        """
        Создать новую игровую сессию со всеми зависимостями.
        
        Args:
            config: Конфигурация сессии
            
        Returns:
            Инициализированная Session
            
        Raises:
            ImportError: Если SKLS зависимости не установлены
            ValueError: Если конфигурация некорректна
        """
        if not SKLS_AVAILABLE:
            raise ImportError(
                "SKLS dependencies не установлены. "
                "Установите skls_generator и skls_embeddings."
            )
        
        session_id = str(uuid.uuid4())
        
        # 1. Создаём логгер для сессии
        logger = self._create_logger(config.session_name, config.log_dir)
        
        # 2. Создаём ChromaClient для векторной базы данных
        chroma_client = self._create_chroma_client(config, logger)
        
        # 3. Создаём Generator для AI генерации
        generator = self._create_generator(config, logger)
        
        # 4. Создаём EventPool для событий
        event_pool = EventPool()
        
        # 5. Создаём подписку для Delivery (чтобы получать события)
        delivery_event_queue = event_pool.subscribe("delivery")
        
        # 6. Создаём Session (пока без delivery, будет инжектирован после создания)
        session = Session(
            session_name=config.session_name,
            chroma_client=chroma_client,
            logger=logger.getChild("engine"),
            generator=generator,
            event_pool=event_pool,
            delivery=None  # type: ignore  # Будет создан и инжектирован ниже
        )
        
        # 7. Создаём GameDelivery с прямой ссылкой на Session
        delivery = GameDelivery(
            session_id=session_id,
            session=session,  # ← Прямая ссылка для немедленной связи!
            event_queue=delivery_event_queue,
            logger=logger.getChild("delivery")
        )
        
        # 8. Инжектируем delivery в сессию
        session.delivery = delivery
        
        # 9. Устанавливаем режим игры
        session.game_mode = GameModes(config.game_mode)
        
        # 10. Создаём и инжектируем Manipulator
        manipulator = self._create_manipulator(config, session, logger)
        session.inject_manipulator(manipulator)
        
        # 11. Создаём и инжектируем Orchestrator
        orchestrator = self._create_orchestrator(config, session, logger)
        session._init_orchestrator(orchestrator)
        
        # 12. Инициализируем сюжет (если есть guide)
        if config.guide:
            session._init_plot(config.guide)
        
        # 13. Регистрируем сессию в SessionManager
        from server.src.game.session_manager import session_manager
        session_manager.register_session(session_id, session)
        
        # Сохраняем сессию в фабрике
        self._sessions[session_id] = session
        
        logger.info(f"Сессия '{config.session_name}' создана с ID: {session_id}")
        
        return session
    
    def _create_logger(self, session_name: str, log_dir: str) -> logging.Logger:
        """Создать логгер для сессии."""
        logger_name = f"session.{session_name}"
        
        if logger_name in self._loggers:
            return self._loggers[logger_name]
        
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        
        # Избегаем дублирования хендлеров
        if not logger.handlers:
            # Создаём директорию для логов
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f"{session_name}.log")
            
            # File handler
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        self._loggers[logger_name] = logger
        return logger
    
    def _create_chroma_client(self, config: SessionConfig, logger: logging.Logger) -> ChromaClient:
        """Создать ChromaClient для векторной базы данных."""
        embedding_client = EmbeddingClient(config.llamacpp_embed_base)
        chroma_client = ChromaClient(
            embedding_client,
            path=config.chroma_db_path,
            logger_instance=logger
        )
        logger.info(f"ChromaClient инициализирован: {config.chroma_db_path}")
        return chroma_client
    
    def _create_generator(self, config: SessionConfig, logger: logging.Logger) -> Generator:
        """Создать Generator для AI генерации."""
        google_genai = GoogleGenAI(
            api_key=config.gemini_api_key,
            logger=logger,
            model_name=config.gemini_model
        )
        generator = Generator(
            google_genai,
            logger_instance=logger
        )
        logger.info(f"Generator инициализирован: {config.gemini_model}")
        return generator
    
    def _create_manipulator(
        self,
        config: SessionConfig,
        session: Session,
        logger: logging.Logger
    ) -> Manipulator:
        """Создать Manipulator для обработки действий."""
        manipulator = Manipulator(
            generator=session.generator,
            session=session,
            archive=None,  # TODO: Добавить archive если нужен
            logger=logger.getChild("manipulator")
        )
        logger.info(f"Manipulator инициализирован: {len(manipulator.manipulations)} манипуляций")
        return manipulator
    
    def _create_orchestrator(
        self,
        config: SessionConfig,
        session: Session,
        logger: logging.Logger
    ) -> Orchestrator:
        """Создать Orchestrator для координации действий."""
        orchestrator = Orchestrator(
            generator=session.generator,
            logger=logger.getChild("orchestrator")
        )
        orchestrator.add_state(session)
        return orchestrator
    
    # === Методы для инициализации игроков и сцены ===
    
    def init_scene(
        self,
        session: Session,
        scene_prompt: str
    ) -> SceneNode:
        """
        Инициализировать начальную сцену.
        
        Args:
            session: Игровая сессия
            scene_prompt: Описание сцены для AI генерации
            
        Returns:
            Сгенерированная SceneNode
        """
        scene = session.generator.generate_one_shot(
            pydantic_model=SceneNode,
            prompt=scene_prompt
        )
        session.current_scene = scene
        session.current_location_name = scene.name
        session.all_locations[scene.name] = scene
        session.location_graph[scene.name] = set()
        
        session.logger.info(f"Сцена инициализирована: {scene.name}")
        return scene
    
    def init_player(
        self,
        session: Session,
        character_prompt: str,
        player_name: str,
        player_id: str
    ) -> Player:
        """
        Инициализировать игрока и его персонажа.
        
        Args:
            session: Игровая сессия
            character_prompt: Описание персонажа для AI генерации
            player_name: Имя игрока
            player_id: ID игрока
            
        Returns:
            Инициализированный Player
        """
        character = session.generator.generate_one_shot(
            pydantic_model=Character,
            prompt=character_prompt
        )
        
        # Подписываем игрока на события
        event_queue = session.event_pool.subscribe(character.name)
        
        # Создаём Orchestrator для игрока
        player_orchestrator = Orchestrator(
            generator=session.generator,
            logger=session.logger.getChild("player_orchestrator")
        )
        player_orchestrator.add_state(session)
        
        player = Player(
            character=character,
            event_queuee=event_queue,
            logger=session.logger.getChild("player"),
            orchestrator=player_orchestrator
        )
        player.inject_state(session)
        
        session.players.append(player)
        
        session.logger.info(f"Игрок '{player_name}' инициализирован с персонажем '{character.name}'")
        return player
    
    def init_npc(
        self,
        session: Session,
        npc_prompt: str
    ) -> NPC:
        """
        Инициализировать NPC.
        
        Args:
            session: Игровая сессия
            npc_prompt: Описание NPC для AI генерации
            
        Returns:
            Инициализированный NPC
        """
        npc_character = session.generator.generate_one_shot(
            pydantic_model=NPCCharacter,
            prompt=npc_prompt
        )
        
        npc = session._init_npc(npc_character)
        
        session.logger.info(f"NPC инициализирован: {npc_character.name}")
        return npc
    
    def init_new_session(
        self,
        session: Session,
        scene_prompt: str,
        player_characters: List[Character],
        npcs: List[NPCCharacter],
        player_names: Optional[List[str]] = None,
        player_ids: Optional[List[str]] = None
    ) -> None:
        """
        Полная инициализация новой сессии.
        
        Args:
            session: Сессия для инициализации
            scene_prompt: Описание начальной сцены
            player_characters: Список персонажей игроков
            npcs: Список NPC
            player_names: Имена игроков (опционально)
            player_ids: ID игроков (опционально)
        """
        # 1. Инициализируем сцену
        self.init_scene(session, scene_prompt)
        
        # 2. Инициализируем игроков
        for i, character in enumerate(player_characters):
            player_name = player_names[i] if player_names and i < len(player_names) else f"Player_{i}"
            player_id = player_ids[i] if player_ids and i < len(player_ids) else str(uuid.uuid4())
            
            event_queue = session.event_pool.subscribe(character.name)
            
            player_orchestrator = Orchestrator(
                generator=session.generator,
                logger=session.logger.getChild("player_orchestrator")
            )
            player_orchestrator.add_state(session)
            
            player = Player(
                character=character,
                event_queuee=event_queue,
                logger=session.logger.getChild("player"),
                orchestrator=player_orchestrator
            )
            player.inject_state(session)
            session.players.append(player)
        
        # 3. Инициализируем NPC
        for npc_character in npcs:
            session._init_npc(npc_character)
        
        session.logger.info(
            f"Сессия инициализирована: {len(session.players)} игроков, {len(session.npcs)} NPC"
        )
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Получить сессию по ID."""
        return self._sessions.get(session_id)
    
    def get_all_sessions(self) -> dict[str, Session]:
        """Получить все созданные сессии."""
        return self._sessions.copy()
    
    def remove_session(self, session_id: str) -> bool:
        """
        Удалить сессию.
        
        Args:
            session_id: ID сессии
            
        Returns:
            True если сессия удалена, False если не найдена
        """
        if session_id not in self._sessions:
            return False
        
        session = self._sessions[session_id]
        session.logger.info(f"Сессия '{session.session_name}' удалена")
        
        # Очищаем логгеры
        logger_name = session.logger.name
        if logger_name in self._loggers:
            # Закрываем хендлеры
            for handler in self._loggers[logger_name].handlers:
                handler.close()
            del self._loggers[logger_name]
        
        del self._sessions[session_id]
        return True


# Глобальный экземпляр фабрики
session_factory = SessionFactory()
