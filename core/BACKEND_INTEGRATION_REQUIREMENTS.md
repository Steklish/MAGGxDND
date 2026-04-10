# Core AI Integration Requirements

## Цель
Документ описывает требования к интеграции AI (Google Gemini) через ядро `core/` для backend'а MAGGxDND.

---

## 1. Существующие компоненты ядра

### 1.1 MAGG (AI Dungeon Master)
**Файл:** `core/magg/magg.py`

**Возможности:**
- `get_simple_description()` - генерация описания сцены
- `comment(events: List[Event])` - нарративная обработка событий игры
- `get_plot_development()` - развитие сюжета
- `intervene()` - вмешательство в игровой процесс

**Требования:**
```python
from core.magg.magg import Magg
from core.game.engine import Session
from skls_generator.generator import Generator

# MAGG требует:
# 1. Generator (обёртка над Google Gemini API)
# 2. Session (ссылка на игровую сессию)
# 3. Logger
# 4. EventPool subscriber queue
```

### 1.2 Session Engine
**Файл:** `core/game/engine.py`

**Возможности:**
- `init_new_session(scene, player_characters, npcs)` - инициализация сессии
- `game_loop()` - основной игровой цикл
- `get_session_context()` - контекст сессии для AI
- `get_messages_formatted()` - история сообщений для AI

**Возвращает:**
- SceneNode - текущая сцена
- List[Player] - игроки
- List[NPC] - NPC
- Messages - история сообщений

### 1.3 Схемы данных
**Файл:** `core/schemas/in_game.py`
- `SceneNode` - сцена с объектами
- `Character` - персонаж игрока
- `NPCCharacter` - NPC
- `GameModes` - режимы игры (STORY, COMBAT)

**Файл:** `core/schemas/orchestration.py`
- `Event` - игровые события
- `EventTypes` - типы событий
- `Message` - сообщения

---

## 2. Что нужно реализовать в backend

### 2.1 Session Manager (уже есть)
**Файл:** `backend/src/game/session_manager.py`

**Задачи:**
- Хранение активных сессий в памяти
- Создание Session engine через SessionFactory
- Регистрация/отписка WebSocket игроков

### 2.2 Session Factory (уже есть)
**Файл:** `backend/src/game/session_factory.py`

**Задачи:**
- Создание Session engine с правильными зависимостями
- Инициализация ChromaDB для эмбеддингов
- Создание Generator с Google Gemini API
- Создание EventPool
- Создание Delivery (REST API или WebSocket)

### 2.3 AI Service (ТРЕБУЕТСЯ СОЗДАТЬ)
**Файл:** `backend/src/services/ai_game_service.py`

**Назначение:** Прослойка между backend API и core ядром

**Методы:**
```python
class AIGameService:
    def __init__(self, session: Session):
        self.session = session
    
    async def initialize_session(
        self,
        scene_prompt: str,
        character_prompts: List[str],
        npc_prompts: List[str]
    ) -> dict:
        """
        Инициализировать сессию через core Session engine.
        
        Использует:
        - Generator.generate_one_shot() для создания SceneNode
        - Generator.generate_one_shot() для создания Character
        - Generator.generate_one_shot() для создания NPCCharacter
        - Session.init_new_session() для инициализации
        
        Возвращает:
        - session_id
        - scene description
        - characters created
        - npcs created
        """
        pass
    
    async def process_player_action(
        self,
        character_name: str,
        action: str
    ) -> dict:
        """
        Обработать действие игрока через core MAGG.
        
        Использует:
        - Orchestrator для обработки действия
        - Magg.comment() для нарратива
        - EventPool для событий
        
        Возвращает:
        - dm_response: текст ответа DM
        - events: список событий
        - game_state: текущее состояние игры
        """
        pass
    
    async def get_scene_description(self) -> str:
        """
        Получить описание сцены через MAGG.
        
        Использует:
        - Magg.get_simple_description()
        
        Возвращает:
        - description: строка с описанием
        """
        pass
```

### 2.4 Delivery Interface (уже есть)
**Файл:** `backend/src/delivery/rest_api_delivery.py`

**Задачи:**
- Получение событий от Session engine
- Отправка событий в frontend через REST API polling
- Хранение последнего состояния для retrieval

**Методы:**
- `master_message(text)` - сообщение от DM
- `session_updated(session)` - обновление состояния
- `player_request(character)` - запрос от игрока

---

## 3. Поток данных

### 3.1 Создание сессии
```
Frontend → Backend API → SessionFactory → Session Engine
                              ↓
                        Generator (Google Gemini)
                              ↓
                        SceneNode, Character, NPC
                              ↓
                        Session.init_new_session()
                              ↓
Backend API ← Session Manager ← active_game_sessions
```

### 3.2 Обработка действия игрока
```
Frontend → Backend API → Session Manager → Session Engine
                              ↓
                        Orchestrator.process()
                              ↓
                        Magg.comment(events)
                              ↓
                        EventPool.publish()
                              ↓
Backend API ← RESTAPIDelivery ← event_queue
```

### 3.3 Получение состояния
```
Frontend polling → Backend API → RESTAPIDelivery
                                    ↓
                              last_dm_message
                              last_action_result
```

---

## 4. Требования к API

### 4.1 Endpoints
```python
POST /api/v1/sessions/{session_id}/start
Body: {
    "scene_prompt": str,
    "character_prompts": List[str],
    "npc_prompts": List[str]
}
Response: {
    "session_id": str,
    "status": "running",
    "scene_description": str,
    "characters": List[dict],
    "npcs": List[dict]
}

POST /api/v1/sessions/{session_id}/action
Body: {
    "character_name": str,
    "action": str
}
Response: {
    "dm_response": str,
    "events": List[dict],
    "game_state": dict
}

GET /api/v1/sessions/{session_id}/state
Response: {
    "scene": SceneNode,
    "players": List[Character],
    "npcs": List[NPCCharacter],
    "messages": List[Message],
    "turn_queue": List[dict]
}
```

---

## 5. Зависимости

### 5.1 От ядра
```python
from core.game.engine import Session
from core.magg.magg import Magg
from core.entity.orchestrator import Orchestrator
from core.entity.player import Player
from core.entity.npc import NPC
from core.schemas.in_game import SceneNode, Character, NPCCharacter
from core.schemas.orchestration import Event, Message, EventTypes
from core.game.event_pool import EventPool
```

### 5.2 От SKLS
```python
from skls_generator.generator import Generator
from skls_generator.gen_backends.google_gen import GoogleGenAI
from skls_embeddings.chroma_client import ChromaClient
from skls_embeddings.embedding_client import EmbeddingClient
```

### 5.3 Конфигурация
```python
# .env
GEMINI_API_KEY=xxx
GEMINI_MODEL=gemini-flash-lite-latest
LLAMACPP_CHAT_BASE=http://localhost:8080  # опционально
AI_GEN_RETRIES=3
```

---

## 6. Что изменить в ядре (рекомендации)

### 6.1 Не менять (стабильно)
- ✅ `core/magg/magg.py` - работает
- ✅ `core/game/engine.py` - работает
- ✅ `core/schemas/*.py` - работает
- ✅ `core/entity/*.py` - работает

### 6.2 Добавить (опционально)
```python
# core/magg/magg.py
def generate_scene_description(self, scene_prompt: str) -> SceneNode:
    """Сгенерировать сцену из промпта."""
    pass

def generate_character(self, character_prompt: str) -> Character:
    """Сгенерировать персонажа из промпта."""
    pass

def generate_npc(self, npc_prompt: str) -> NPCCharacter:
    """Сгенерировать NPC из промпта."""
    pass

def process_action(self, character_name: str, action: str) -> ActionResponse:
    """Обработать действие игрока."""
    pass
```

### 6.3 Создать
```python
# core/magg/ai_responses.py
class AIResponse(BaseModel):
    """Базовый класс для AI ответов."""
    success: bool
    message: str
    data: Optional[dict]

class SceneGenerationResponse(AIResponse):
    scene: SceneNode

class CharacterGenerationResponse(AIResponse):
    character: Character

class ActionProcessingResponse(AIResponse):
    dm_response: str
    events: List[Event]
    game_state_update: dict
```

---

## 7. Пример использования

```python
# backend/src/api/routers/session_router.py
from backend.src.services.ai_game_service import AIGameService
from backend.src.game.session_manager import session_manager

@router.post("/{session_id}/start")
async def start_session(session_id: str, request: SessionStartRequest):
    # Получить сессию из менеджера
    session = session_manager.get_session(session_id)
    
    # Создать AI сервис
    ai_service = AIGameService(session)
    
    # Инициализировать через AI
    result = await ai_service.initialize_session(
        scene_prompt=request.scene_prompt or request.wishes,
        character_prompts=request.character_prompts or [request.character_description] if request.character_description else [],
        npc_prompts=request.npc_prompts or []
    )
    
    return result

@router.post("/{session_id}/action")
async def player_action(session_id: str, request: ActionRequest):
    session = session_manager.get_session(session_id)
    ai_service = AIGameService(session)
    
    result = await ai_service.process_player_action(
        character_name=request.character_name,
        action=request.action
    )
    
    return result
```

---

## 8. Обработка ошибок

```python
class AIServiceError(Exception):
    """Базовая ошибка AI сервиса."""
    pass

class GenerationError(AIServiceError):
    """Ошибка генерации контента."""
    pass

class SessionNotInitializedError(AIServiceError):
    """Сессия не инициализирована."""
    pass

class APIError(AIServiceError):
    """Ошибка API (Google Gemini)."""
    pass
```

---

## 9. Логирование

```python
logger = logging.getLogger('ai_game_service')

# Логировать:
# 1. Запросы к AI (промпты)
# 2. Ответы от AI
# 3. Ошибки генерации
# 4. Время обработки запросов
```

---

## 10. Тесты

```python
# backend/tests/test_ai_game_service.py
async def test_initialize_session():
    session = create_test_session()
    ai_service = AIGameService(session)
    
    result = await ai_service.initialize_session(
        scene_prompt="A dark cave",
        character_prompts=["A brave warrior"],
        npc_prompts=["A wise wizard"]
    )
    
    assert result['success'] == True
    assert 'scene' in result
    assert 'characters' in result

async def test_process_player_action():
    session = create_test_session()
    ai_service = AIGameService(session)
    
    result = await ai_service.process_player_action(
        character_name="Warrior",
        action="Attack the dragon"
    )
    
    assert 'dm_response' in result
    assert len(result['events']) > 0
```
