# Модель владения сессией в MAGGxDND

## Краткий ответ

**Владелец сессии:** `Session` (из `game/engine.py`)

**SessionManager:** Только реестр для доступа из веб-слоя, НЕ владеет сессиями.

---

## Иерархия владения

```
┌─────────────────────────────────────────────────────────────┐
│                     Session (Владелец)                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  self.event_pool : EventPool                          │  │
│  │  self.players : List[Player]                          │  │
│  │  self.npcs : List[NPC]                                │  │
│  │  self.delivery : Delivery                             │  │
│  │  self.orchestrator : Orchestrator                     │  │
│  │  self.game_master : Magg                              │  │
│  │  self.current_scene : SceneNode                       │  │
│  │  ...                                                  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         ▲
         │ (ссылка из реестра)
         │
┌─────────────────────────────────────────────────────────────┐
│                  SessionManager (Реестр)                     │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  _sessions: Dict[str, Session]  ← только ссылки       │  │
│  │  _player_websockets: Dict[str, WebSocket]             │  │
│  │  _player_subscriber_queues: Dict[str, SubscriberQueue]│  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Почему Session владеет состоянием?

### 1. Session создаётся с зависимостями

```python
# game/engine.py
class Session:
    def __init__(self,
                 session_name,
                 chroma_client: ChromaClient,
                 logger: Logger,
                 generator: Generator,
                 event_pool: EventPool,      # ← Создаётся для сессии
                 delivery: Delivery,
                 ) -> None:
        self.event_pool = event_pool         # ← Принадлежит сессии
        self.players = []
        self.npcs = []
        # ...
```

**Важно:** `EventPool` создаётся **для** сессии и является её частью.

### 2. Player и NPC подписываются на Session.event_pool

```python
# game/engine.py
def _init_player(self, character: Character, orchestrator: 'Orchestrator', ...):
    new_player = Player(
        character=character,
        event_queuee=self.event_pool.subscribe(character.name),  # ← Из сессии
        logger=logger_to_use,
        orchestrator=orchestrator
    )
    self.players.append(new_player)
```

### 3. Delivery получает уведомления от Session

```python
# game/engine.py (пример использования)
session.delivery.master_message("Дракон просыпается!")
session.delivery.session_updated(session)  # ← Передаёт себя
```

---

## Роль SessionManager

`SessionManager` — это **глобальный реестр** (Singleton) который:

1. ✅ Хранит **ссылки** на активные `Session` объекты
2. ✅ Управляет WebSocket подключениями игроков
3. ✅ Управляет `SubscriberQueue` для каждого игрока
4. ✅ Предоставляет доступ к сессиям из HTTP/WebSocket handlers
5. ❌ **НЕ создаёт** Session (это делает код инициализации игры)
6. ❌ **НЕ владеет** EventPool (берёт из `session.event_pool`)
7. ❌ **НЕ изменяет** состояние сессии напрямую

### Правильное использование

```python
# ✅ ПРАВИЛЬНО: Получить сессию и работать с ней
from server.src.game.session_manager import session_manager

session = session_manager.get_session(session_id)
if session:
    # Session владеет состоянием, работаем через неё
    session.delivery.master_message("Ход игрока Alice")
    session.event_pool.add_event(event)

# ❌ НЕПРАВИЛЬНО: Пытаться обойти Session
event_pool = session_manager._event_pools[session_id]  # ← Такого поля больше нет!
```

---

## Жизненный цикл сессии

### 1. Создание (вне SessionManager)

```python
# main.py или factory функция
from game.engine import Session
from game.event_pool import EventPool
from server.src.delivery.game_delivery import GameDelivery
from server.src.game.session_manager import session_manager

# Создаём зависимости
event_pool = EventPool()
delivery = GameDelivery(session_id="session-123")

# Создаём Session (владелец состояния!)
session = Session(
    session_name="Friday Night D&D",
    chroma_client=chroma_client,
    logger=logger,
    generator=generator,
    event_pool=event_pool,      # ← Принадлежит сессии
    delivery=delivery
)

# Регистрируем в реестре (только ссылка!)
session_manager.register_session("session-123", session)
```

### 2. Подключение игрока

```python
# websocket_game.py
@router.websocket("/ws/{session_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, player_id: str):
    # Получаем сессию из реестра
    session = session_manager.get_session(session_id)
    if not session:
        await websocket.close()
        return
    
    # Подписываем игрока на СОБЫТИЯ сессии
    subscriber_queue = session_manager.subscribe_player_to_events(
        session_id=session_id,
        player_id=player_id
    )
    # subscriber_queue получает события из session.event_pool
```

### 3. Удаление сессии

```python
# SessionManager.remove_session()
async def remove_session(self, session_id: str) -> None:
    # 1. Отключаем WebSocket
    for websocket in self._player_websockets[session_id].values():
        await websocket.close()
    
    # 2. Удаляем ссылку из реестра
    self._sessions.pop(session_id, None)
    
    # 3. Session и его event_pool удаляются автоматически (GC)
    #    если нет других ссылок на них
```

---

## Синхронизация доступа

### Проблема

Несколько игроков могут отправлять действия одновременно:

```
Игрок A ──> WebSocket ──┐
                        ├─> Session (состояние) ──> Гонка данных!
Игрок B ──> WebSocket ──┘
```

### Решение: asyncio.Lock на сессию

```python
# server/src/game/session_manager.py
async def get_session_lock(self, session_id: str) -> asyncio.Lock:
    return self._session_locks.get(session_id, asyncio.Lock())

# Использование в WebSocket handler
async with await session_manager.get_session_lock(session_id):
    # Критическая секция - только один запрос меняет состояние
    session.players[0].character.hp -= 10
    session.delivery.send_character_update(...)
```

### EventPool уже потокобезопасен

```python
# game/event_pool.py
class EventPool:
    def __init__(self):
        self._lock = threading.RLock()  # ← Потокобезопасность
    
    def add_event(self, event: Event) -> None:
        with self._lock:  # ← Защита от гонок
            self._events.append(event)
            for queue in self._subscriber_queues.values():
                queue.put(event)
```

---

## Диаграмма последовательности

```
┌─────────┐    ┌──────────────┐    ┌─────────┐    ┌───────────┐    ┌─────────┐
│ Игрок A │    │ SessionManager│    │ Session │    │ EventPool │    │ Игрок B │
└────┬────┘    └──────┬───────┘    └────┬────┘    └─────┬─────┘    └────┬────┘
     │                │                 │               │               │
     │ Connect WS     │                 │               │               │
     │───────────────>│                 │               │               │
     │                │ register        │               │               │
     │                │────────────────>│               │               │
     │                │ subscribe       │               │               │
     │                │────────────────────────────────>│               │
     │<─Connected─────│                 │               │               │
     │                │                 │               │               │
     │ Action         │                 │               │               │
     │───────────────>│                 │               │               │
     │                │                 │               │               │
     │                │ [Получить Session]              │               │
     │                │────────────────>│               │               │
     │                │                 │               │               │
     │                │ session.event_pool.publish_to_others()          │
     │                │────────────────────────────────>│               │
     │                │                 │               │               │
     │                │                 │               │ Queue Event   │
     │                │                 │               │──────────────>│
     │<─Confirm───────│                 │               │               │
     │                │                 │               │               │
     │                │                 │               │ Get Event     │
     │                │                 │               │<──────────────│
     │                │                 │               │               │
     │                │                 │               │<──────────────│
     │                │                 │               │  Event        │
     │                │                 │               │               │
```

---

## Сравнение с другими паттернами

### ❌ Не используем: Shared State в FastAPI state

```python
# ❌ ПЛОХО: Состояние в app.state
@app.on_event("startup")
async def startup():
    app.state.sessions = {}

# Проблема: Нет контроля за потокобезопасностью, сложно тестировать
```

### ❌ Не используем: Глобальные переменные

```python
# ❌ ПЛОХО: Глобальная переменная
sessions: Dict[str, Session] = {}

# Проблема: Нет инкапсуляции, сложно управлять жизненным циклом
```

### ✅ Используем: Singleton Registry

```python
# ✅ ХОРОШО: Singleton с явным управлением
class SessionManager:
    _instance: Optional['SessionManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

# Преимущества:
# - Контролируемый доступ
# - Явное управление жизненным циклом
# - Легко тестировать (можно замокать)
# - Потокобезопасность через locks
```

---

## Часто задаваемые вопросы

### Q: Может ли быть несколько SessionManager?

**A:** Нет, это Singleton. Все части приложения получают один экземпляр:

```python
from server.src.game.session_manager import session_manager
# Всегда один и тот же объект
```

### Q: Что если Session нужен вне веб-контекста?

**A:** Session создаётся независимо от SessionManager:

```python
# Запуск игры без веб-сервера
session = Session(...)  # ← Работает без SessionManager
session.game_loop()
```

### Q: Как тестировать?

**A:** Мокаем SessionManager:

```python
# test_websocket.py
def test_websocket_connection():
    mock_session = Mock(spec=Session)
    mock_session.event_pool = Mock(spec=EventPool)
    
    session_manager = SessionManager()
    session_manager.register_session("test-id", mock_session)
    
    # Тестируем WebSocket handler
```

### Q: Где хранить постоянные данные сессии?

**A:** Session хранит **оперативное** состояние. Для персистентности:

```python
# Сохранение в БД
async def save_session(session_id: str):
    session = session_manager.get_session(session_id)
    await db.sessions.update(
        {"id": session_id},
        {"state": session.serialize(), "updated_at": datetime.now()}
    )
```

---

## Выводы

| Компонент | Владеет | Роль |
|-----------|---------|------|
| **Session** | ✅ `event_pool`, `players`, `npcs`, `delivery` | Состояние игры |
| **SessionManager** | ❌ Только ссылки на `Session` | Реестр + WebSocket менеджмент |
| **EventPool** | ✅ `events`, `subscriber_queues` | Pub/Sub для событий |
| **Delivery** | ❌ Только отправка сообщений | Мост к WebSocket |

**Золотое правило:** Session — единственный источник истины для состояния игры. Все изменения состояния происходят **через Session**.
