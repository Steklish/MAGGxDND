# GameDelivery: Немедленная связь с Session

## Проблема

В исходной реализации `GameDelivery` не имел прямой ссылки на `Session`, что приводило к:
- Отсутствию немедленного логирования в Session
- Невозможности доступа к состоянию Session в момент отправки
- Разрыву между доставкой сообщений и состоянием игры

## Решение

`GameDelivery` теперь хранит **прямую ссылку** на `Session` и получает события через `SubscriberQueue`.

---

## Архитектура

### До изменений

```
┌─────────────────────────────────────────────────────────┐
│                  GameDelivery                            │
│  ┌────────────────────────────────────────────────────┐ │
│  │  session_id: str                                   │ │
│  │  (нет ссылки на Session!)                          │ │
│  └────────────────────────────────────────────────────┘ │
│                          │                                │
│                          ▼                                │
│            SessionManager.get_player_websocket()         │
│            (косвенный доступ через lookup)               │
└─────────────────────────────────────────────────────────┘
```

### После изменений

```
┌─────────────────────────────────────────────────────────┐
│                  GameDelivery                            │
│  ┌────────────────────────────────────────────────────┐ │
│  │  session: Session  ← ПРЯМАЯ ССЫЛКА                 │ │
│  │  session_id: str                                   │ │
│  │  event_queue: SubscriberQueue                      │ │
│  │  logger: Logger                                    │ │
│  └────────────────────────────────────────────────────┘ │
│          │                    │                          │
│          ▼                    ▼                          │
│    session.logger      session.event_pool                │
│    session.messages    session.players                   │
│    session.game_mode   session.current_scene             │
└─────────────────────────────────────────────────────────┘
```

---

## Изменения в коде

### 1. Конструктор GameDelivery

**Было:**
```python
class GameDelivery(Delivery):
    def __init__(self, session_id: str):
        self.session_id = session_id
        self._message_queue: asyncio.Queue = asyncio.Queue()
```

**Стало:**
```python
class GameDelivery(Delivery):
    def __init__(
        self,
        session_id: str,
        session: 'Session',          # ← Прямая ссылка!
        event_queue: SubscriberQueue,  # ← Для получения событий
        logger: Logger
    ):
        super().__init__(event_queue, logger)
        self.session_id = session_id
        self.session = session  # ← Прямая ссылка для немедленной связи!
        self._message_queue: asyncio.Queue = asyncio.Queue()
```

---

### 2. master_message

**Было:**
```python
def master_message(self, text: str, tag: Optional[str] = None) -> None:
    message = {"type": "MASTER_MESSAGE", "text": text, "tag": tag}
    asyncio.create_task(self._broadcast_to_session(message))
    asyncio.create_task(self._message_queue.put(message))
```

**Стало:**
```python
def master_message(self, text: str, tag: Optional[str] = None) -> None:
    message = {"type": "MASTER_MESSAGE", "text": text, "tag": tag}
    
    # ← Немедленная связь: логируем в Session
    self.session.logger.info(f"[MASTER] {text}")
    
    # Отправляем через WebSocket
    loop = self._get_event_loop()
    if loop.is_running():
        loop.create_task(self._broadcast_to_session(message))
    else:
        loop.run_until_complete(self._broadcast_to_session(message))
    
    # ← Немедленная связь: добавляем в историю Session
    from schemas.orchestration import Message
    self.session.messages.append(
        Message(sender_name="GM", text=text, tag=tag or "narration")
    )
    
    # Ограничиваем историю
    if len(self.session.messages) > 20:
        self.session.messages = self.session.messages[-20:]
```

---

### 3. session_updated

**Было:**
```python
def session_updated(self, session: "Session") -> None:
    message = {"type": "SESSION_UPDATE", "data": {...}}
    asyncio.create_task(self._broadcast_to_session(message))
```

**Стало:**
```python
def session_updated(self, session: "Session") -> None:
    # ← Немедленная связь: логируем обновление
    session.logger.debug(f"[SESSION_UPDATE] {session.session_name}")
    
    message = {"type": "SESSION_UPDATE", "data": {...}}
    
    # Отправляем через WebSocket
    loop = self._get_event_loop()
    if loop.is_running():
        loop.create_task(self._broadcast_to_session(message))
    else:
        loop.run_until_complete(self._broadcast_to_session(message))
```

---

### 4. Обработка asyncio loop

Проблема: `asyncio.create_task()` требует запущенного event loop.

**Решение:**
```python
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

# Использование
loop = self._get_event_loop()
if loop.is_running():
    loop.create_task(self._broadcast_to_session(message))
else:
    loop.run_until_complete(self._broadcast_to_session(message))
```

---

## Обновление SessionFactory

`SessionFactory` теперь создаёт `GameDelivery` с правильными зависимостями:

```python
def create_session(self, config: SessionConfig) -> Session:
    # 1. Создаём EventPool
    event_pool = EventPool()
    
    # 2. Создаём подписку для Delivery
    delivery_event_queue = event_pool.subscribe("delivery")
    
    # 3. Создаём Session (пока без delivery)
    session = Session(
        session_name=...,
        chroma_client=...,
        logger=...,
        generator=...,
        event_pool=event_pool,
        delivery=None  # Будет инжектирован
    )
    
    # 4. Создаём GameDelivery с прямой ссылкой на Session
    delivery = GameDelivery(
        session_id=session_id,
        session=session,  # ← Прямая ссылка!
        event_queue=delivery_event_queue,
        logger=logger.getChild("delivery")
    )
    
    # 5. Инжектируем delivery в сессию
    session.delivery = delivery
    
    return session
```

---

## Преимущества новой архитектуры

### 1. Немедленное логирование
```python
session.delivery.master_message("Дракон атакует!")
# → Сразу логируется в session.logger
# → Сразу добавляется в session.messages
# → Сразу отправляется игрокам через WebSocket
```

### 2. Доступ к состоянию
```python
def send_character_update(self, character_id: str, updates: dict):
    # ← Доступ к состоянию Session
    self.session.logger.debug(f"[CHARACTER_UPDATE] {character_id}")
    
    # ← Доступ к игрокам Session
    player = next(p for p in self.session.players 
                  if p.character.id == character_id)
```

### 3. Согласованность
Все изменения состояния немедленно отражаются:
- В логах Session
- В истории сообщений Session
- В WebSocket подключениях игроков

---

## Диаграмма потока

```
┌──────────┐
│  Game    │
│  Engine  │
└────┬─────┘
     │ session.delivery.master_message("...")
     ▼
┌──────────────────────────────────────────────────────────┐
│                   GameDelivery                            │
│  ┌────────────────────────────────────────────────────┐  │
│  │ 1. session.logger.info("[MASTER] ...")             │  │
│  │    (немедленная связь с Session)                   │  │
│  │                                                     │  │
│  │ 2. session.messages.append(...)                    │  │
│  │    (немедленная связь с Session)                   │  │
│  │                                                     │  │
│  │ 3. WebSocket.broadcast(...)                        │  │
│  │    (асинхронная отправка игрокам)                  │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
     │
     │ WebSocket
     ▼
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Player A │     │ Player B │     │ Player C │
└──────────┘     └──────────┘     └──────────┘
```

---

## Сравнение подходов

| Аспект | До изменений | После изменений |
|--------|--------------|-----------------|
| **Ссылка на Session** | ❌ Только session_id | ✅ Прямая ссылка |
| **Логирование** | ❌ Отсутствует | ✅ В session.logger |
| **История сообщений** | ❌ Отсутствует | ✅ В session.messages |
| **Доступ к состоянию** | ❌ Через SessionManager | ✅ Прямой доступ |
| **Согласованность** | ❌ Асинхронная | ✅ Немедленная + асинхронная |

---

## Обновлённые файлы

| Файл | Изменения |
|------|-----------|
| `server/src/delivery/game_delivery.py` | Полная переработка с прямой ссылкой на Session |
| `server/src/game/session_factory.py` | Создание GameDelivery с правильными зависимостями |
| `server/src/game/session_manager.py` | Без изменений (только реестр) |

---

## Тестирование

### Проверка немедленной связи

```python
from server.src.game.session_factory import SessionFactory, SessionConfig

factory = SessionFactory()
session = factory.create_session(SessionConfig(session_name="Test"))

# Логируем сообщение
session.delivery.master_message("Welcome!")

# Проверяем немедленную связь
assert len(session.messages) == 1
assert session.messages[0].text == "Welcome!"
assert session.logger.handlers[0].stream.name.endswith("Test.log")
```

### Проверка WebSocket отправки

```python
# Подключаем игрока
from server.src.game.session_manager import session_manager
await session_manager.register_player_websocket(session_id, player_id, websocket)

# Отправляем сообщение
session.delivery.master_message("Test")

# Проверяем что WebSocket получил сообщение
message = await websocket.receive_json()
assert message["type"] == "MASTER_MESSAGE"
assert message["text"] == "Test"
```

---

## Заключение

`GameDelivery` теперь имеет **немедленную связь** с `Session` через:
1. Прямую ссылку на объект Session
2. SubscriberQueue для получения событий
3. Logger для логирования в Session
4. Прямой доступ к состоянию Session

Это обеспечивает согласованность между доставкой сообщений и состоянием игры.
