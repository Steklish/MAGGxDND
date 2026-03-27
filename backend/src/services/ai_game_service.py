"""
AI Game Service

Прослойка между backend API и core ядром для работы с AI (Google Gemini).

Отвечает за:
- Инициализацию сессии через Generator + Session
- Обработку действий игроков через MAGG + Orchestrator
- Получение описания сцены и состояния игры
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from core.game.engine import Session
from core.magg.magg import Magg
from core.entity.orchestrator import Orchestrator
from core.schemas.in_game import SceneNode, Character, NPCCharacter
from core.schemas.orchestration import Event, Message
from core.game.manipulator import Manipulator

from backend.src.services.ai_game_exceptions import (
    AIServiceError,
    GenerationError,
    SessionNotInitializedError,
    APIError,
    CharacterNotFoundError,
    InvalidActionError
)

logger = logging.getLogger(__name__)


class AIGameService:
    """
    Сервис для работы с AI в игровых сессиях.
    
    Использует core ядро для:
    - Генерации контента через Generator (Google Gemini)
    - Обработки действий через Orchestrator + MAGG
    - Управления состоянием через Session engine
    """

    def __init__(self, session: Session):
        """
        Инициализация сервиса.
        
        Args:
            session: Активная игровая сессия из core engine
        """
        self.session = session
        self.logger = logging.getLogger(f'ai_game_service.{session.session_name}')
        
    async def initialize_session(
        self,
        scene_prompt: str,
        character_prompts: List[str],
        npc_prompts: List[str]
    ) -> Dict[str, Any]:
        """
        Инициализировать сессию через core Session engine.
        
        Генерирует сцену, персонажей и NPC через Google Gemini AI,
        затем инициализирует игровую сессию.
        
        Args:
            scene_prompt: Описание начальной сцены
            character_prompts: Список описаний персонажей игроков
            npc_prompts: Список описаний NPC
            
        Returns:
            dict с результатами инициализации:
            - success: bool
            - session_id: str
            - scene: SceneNode
            - characters: List[Character]
            - npcs: List[NPCCharacter]
            - message: str
            
        Raises:
            GenerationError: Если AI не смог сгенерировать контент
            SessionNotInitializedError: Если сессия уже инициализирована
        """
        try:
            self.logger.info(f"Initializing session with scene: {scene_prompt[:100]}...")
            
            # Проверяем, не инициализирована ли уже сессия
            if self.session.scene and self.session.players:
                self.logger.warning("Session already initialized")
                raise SessionNotInitializedError("Session is already initialized")
            
            # Генерируем сцену
            self.logger.info("Generating scene...")
            scene = await self._generate_scene(scene_prompt)
            self.logger.info(f"Scene generated: {scene.name}")
            
            # Генерируем персонажей
            characters = []
            for i, prompt in enumerate(character_prompts):
                self.logger.info(f"Generating character {i+1}/{len(character_prompts)}...")
                character = await self._generate_character(prompt)
                characters.append(character)
                self.logger.info(f"Character generated: {character.name}")
            
            # Генерируем NPC
            npcs = []
            for i, prompt in enumerate(npc_prompts):
                self.logger.info(f"Generating NPC {i+1}/{len(npc_prompts)}...")
                npc = await self._generate_npc(prompt)
                npcs.append(npc)
                self.logger.info(f"NPC generated: {npc.name}")
            
            # Инициализируем сессию
            self.logger.info("Initializing session engine...")
            self.session.init_new_session(
                scene=scene,
                player_characters=characters,
                npcs=npcs,
                npc_logger=self.logger,
                player_logger=self.logger
            )
            
            self.logger.info(f"Session initialized with {len(characters)} characters and {len(npcs)} NPCs")
            
            return {
                "success": True,
                "session_id": self.session.session_name,
                "scene": scene.model_dump(),
                "characters": [c.model_dump() for c in characters],
                "npcs": [n.model_dump() for n in npcs],
                "message": f"Session initialized: {scene.description or scene.name}"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to initialize session: {str(e)}", exc_info=True)
            if isinstance(e, AIServiceError):
                raise
            raise GenerationError(f"Failed to initialize session: {str(e)}") from e
    
    async def _generate_scene(self, prompt: str) -> SceneNode:
        """
        Сгенерировать сцену из промпта.
        
        Args:
            prompt: Описание сцены
            
        Returns:
            SceneNode: Сгенерированная сцена
        """
        try:
            generator = self.session.generator
            scene = generator.generate_one_shot(
                pydantic_model=SceneNode,
                prompt=prompt
            )
            return scene
        except Exception as e:
            self.logger.error(f"Failed to generate scene: {str(e)}")
            # Возвращаем дефолтную сцену при ошибке
            return SceneNode(
                name="Unknown Location",
                description=prompt or "A mysterious place.",
                objects=[],
                exits=[]
            )
    
    async def _generate_character(self, prompt: str) -> Character:
        """
        Сгенерировать персонажа из промпта.
        
        Args:
            prompt: Описание персонажа
            
        Returns:
            Character: Сгенерированный персонаж
        """
        try:
            generator = self.session.generator
            character = generator.generate_one_shot(
                pydantic_model=Character,
                prompt=prompt
            )
            return character
        except Exception as e:
            self.logger.error(f"Failed to generate character: {str(e)}")
            # Возвращаем дефолтного персонажа при ошибке
            return Character(
                name="Unknown Hero",
                description=prompt or "A brave adventurer.",
                health=100,
                max_health=100,
                armor_class=10,
                level=1
            )
    
    async def _generate_npc(self, prompt: str) -> NPCCharacter:
        """
        Сгенерировать NPC из промпта.
        
        Args:
            prompt: Описание NPC
            
        Returns:
            NPCCharacter: Сгенерированный NPC
        """
        try:
            generator = self.session.generator
            npc = generator.generate_one_shot(
                pydantic_model=NPCCharacter,
                prompt=prompt
            )
            return npc
        except Exception as e:
            self.logger.error(f"Failed to generate NPC: {str(e)}")
            # Возвращаем дефолтного NPC при ошибке
            return NPCCharacter(
                name="Unknown NPC",
                description=prompt or "A mysterious figure.",
                health=50,
                max_health=50,
                armor_class=10,
                level=1,
                attitude="neutral"
            )
    
    async def process_player_action(
        self,
        character_name: str,
        action: str
    ) -> Dict[str, Any]:
        """
        Обработать действие игрока через core MAGG.
        
        Использует Orchestrator для обработки действия и MAGG
        для генерации нарративного ответа.
        
        Args:
            character_name: Имя персонажа, выполняющего действие
            action: Описание действия
            
        Returns:
            dict с результатами:
            - success: bool
            - dm_response: текст ответа DM
            - events: список событий
            - game_state: текущее состояние игры
            - error: ошибка (если есть)
            
        Raises:
            CharacterNotFoundError: Если персонаж не найден
            InvalidActionError: Если действие недопустимо
            SessionNotInitializedError: Если сессия не инициализирована
        """
        try:
            self.logger.info(f"Processing action for {character_name}: {action}")
            
            # Проверяем инициализацию сессии
            if not self.session.scene:
                raise SessionNotInitializedError("Session not initialized")
            
            # Ищем персонажа
            character = self._find_character(character_name)
            if not character:
                raise CharacterNotFoundError(f"Character '{character_name}' not found")
            
            # Проверяем действие
            if not action or not action.strip():
                raise InvalidActionError("Action cannot be empty")
            
            # Получаем orchestrator
            orchestrator = self.session.orchestrator
            if not orchestrator:
                raise AIServiceError("Orchestrator not available")
            
            # Обрабатываем действие через orchestrator
            self.logger.info("Processing action through orchestrator...")
            result = await orchestrator.process_action(
                character_uuid=character.uuid,
                action_text=action
            )
            
            # Получаем события из event pool
            events = []
            if self.session.event_pool:
                events = self.session.event_pool.get_events()
            
            # Генерируем нарративный ответ через MAGG
            dm_response = await self._generate_dm_response(events, action)
            
            self.logger.info(f"Action processed. DM response: {dm_response[:100]}...")
            
            return {
                "success": True,
                "dm_response": dm_response,
                "events": [self._event_to_dict(e) for e in events],
                "game_state": self.get_game_state(),
                "character_updated": character.model_dump() if character else None
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process action: {str(e)}", exc_info=True)
            if isinstance(e, AIServiceError):
                raise
            raise AIServiceError(f"Failed to process action: {str(e)}") from e
    
    def _find_character(self, character_name: str) -> Optional[Character]:
        """
        Найти персонажа по имени.
        
        Args:
            character_name: Имя персонажа
            
        Returns:
            Character или None
        """
        if not self.session.players:
            return None
        
        # Ищем по точному совпадению
        for player in self.session.players:
            if player.name.lower() == character_name.lower():
                return player
        
        # Ищем по частичному совпадению
        for player in self.session.players:
            if character_name.lower() in player.name.lower():
                return player
        
        return None
    
    async def _generate_dm_response(
        self,
        events: List[Event],
        action: str
    ) -> str:
        """
        Сгенерировать нарративный ответ DM через MAGG.
        
        Args:
            events: Список событий
            action: Действие игрока
            
        Returns:
            str: Текст ответа DM
        """
        try:
            magg = self.session.magg
            if not magg:
                return self._fallback_dm_response(events, action)
            
            # Используем MAGG для комментария к событиям
            comment = magg.comment(events)
            if comment:
                return comment
            
            return self._fallback_dm_response(events, action)
            
        except Exception as e:
            self.logger.error(f"Failed to generate DM response: {str(e)}")
            return self._fallback_dm_response(events, action)
    
    def _fallback_dm_response(self, events: List[Event], action: str) -> str:
        """
        Резервный ответ DM при ошибке генерации.
        
        Args:
            events: Список событий
            action: Действие игрока
            
        Returns:
            str: Базовый текст ответа
        """
        if not events:
            return f"You attempt to {action}. The outcome is uncertain..."
        
        event_descriptions = []
        for event in events:
            event_type = event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type)
            event_descriptions.append(f"{event_type}: {event.description}")
        
        return "\n".join(event_descriptions) if event_descriptions else f"You {action}."
    
    def _event_to_dict(self, event: Event) -> Dict[str, Any]:
        """
        Конвертировать Event в dict для JSON сериализации.
        
        Args:
            event: Event объект
            
        Returns:
            dict: Сериализованное событие
        """
        return {
            "event_type": event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type),
            "description": event.description,
            "source": event.source,
            "targets": [str(t) for t in event.targets] if event.targets else [],
            "timestamp": event.timestamp.isoformat() if event.timestamp else None
        }
    
    def get_game_state(self) -> Dict[str, Any]:
        """
        Получить текущее состояние игры.
        
        Returns:
            dict с состоянием:
            - scene: текущая сцена
            - players: список игроков
            - npcs: список NPC
            - messages: последние сообщения
            - turn_queue: очередь ходов
        """
        state = {
            "scene": None,
            "players": [],
            "npcs": [],
            "messages": [],
            "turn_queue": []
        }
        
        try:
            # Сцена
            if self.session.scene:
                state["scene"] = self.session.scene.model_dump()
            
            # Игроки
            if self.session.players:
                state["players"] = [p.model_dump() for p in self.session.players]
            
            # NPC
            if self.session.npcs:
                state["npcs"] = [n.model_dump() for n in self.session.npcs]
            
            # Сообщения
            if hasattr(self.session, 'get_messages_formatted'):
                messages = self.session.get_messages_formatted()
                state["messages"] = [
                    {"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat()}
                    for m in messages
                ] if messages else []
            
            # Очередь ходов
            if hasattr(self.session, 'turn_queue'):
                state["turn_queue"] = list(self.session.turn_queue) if self.session.turn_queue else []
            
        except Exception as e:
            self.logger.error(f"Failed to get game state: {str(e)}")
        
        return state
    
    async def get_scene_description(self) -> str:
        """
        Получить описание сцены через MAGG.
        
        Returns:
            str: Описание сцены
        """
        try:
            if not self.session.scene:
                return "The scene is not initialized."
            
            magg = self.session.magg
            if magg:
                description = magg.get_simple_description()
                if description:
                    return description
            
            # Fallback
            return self.session.scene.description or self.session.scene.name
            
        except Exception as e:
            self.logger.error(f"Failed to get scene description: {str(e)}")
            return "Unable to describe the scene."
