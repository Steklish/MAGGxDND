# Архитектура сервера MAGGxDND

## Обзор

Сервер обеспечивает реальное время взаимодействие между игроками в общих игровых сессиях (лобби) через WebSocket и REST API.

## Компоненты

```
server/
├── main.py                          # Точка входа FastAPI
├── src/
│   ├── api/
│   │   └── routers/
│   │       ├── user.py              # CRUD пользователей
│   │       ├── access_group.py      # Группы доступа
│   │       ├── login.py             # Аутентификация
│   │       ├── dev.py               # Dev эндпоинты
│   │       ├── session_router.py    # REST API сессий ✨
│   │       └── websocket_game.py    # WebSocket для игры ✨
│   ├── game/
│   │   └── session_manager.py       # Singleton для сессий ✨
│   ├── delivery/
│   │   └── game_delivery.py         # Связь движка с WebSocket ✨
│   ├── config/
│   ├── database/
│   ├── models/
│   ├── schema/
│   ├── services/
│   ├── repositories/
│   ├── auth/
│   └── utils/
```

✨ - новые файлы для поддержки игровых сессий

---

## Управление сессиями (Session Manager)

### Проблема
Несколько игроков должны взаимодействовать с **одним экземпляром** `Session` в реальном времени.

### Решение
`SessionManager` - Singleton который хранит:
- `Dict[session_id, Session]` - игровые сессии
- `Dict[session_id, EventPool]` - очереди событий для каждой сессии
- `Dict[session_id, Dict[player_id, WebSocket]]` - подключения игроков
- `Dict[session_id, Dict[player_id, SubscriberQueue]]` - очереди подписчиков

### Pattern: Event Sourcing + Pub/Sub

```
Игрок A ──┐
          ├──> WebSocket ──> EventPool ──> SubscriberQueue ──> Игрок B
Игрок B ──┘                    │
                               └─> SubscriberQueue ──> Игрок A
```

1. Игрок отправляет действие через WebSocket
2. Действие публикуется в `EventPool` сессии
3. `EventPool` копирует событие в `SubscriberQueue` каждого игрока
4. Каждый игрок получает события из своей очереди

---

## REST API

### Базовый URL: `/api/v1`

#### Сессии

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| POST | `/sessions` | Создать сессию |
| GET | `/sessions` | Список сессий |
| GET | `/sessions/{id}` | Информация о сессии |
| DELETE | `/sessions/{id}` | Удалить сессию |
| POST | `/sessions/{id}/players` | Добавить игрока |
| GET | `/sessions/{id}/players` | Список игроков |
| DELETE | `/sessions/{id}/players/{id}` | Удалить игрока |

#### WebSocket

| Эндпоинт | Описание |
|----------|----------|
| `ws://localhost:8000/ws/{session_id}/{player_id}` | Подключение к сессии |

---

## Формат сообщений WebSocket

### Клиент → Сервер

```json
{
  "event_type": "PLAYER_ACTION",
  "data": {
    "action": "move",
    "target": {"x": 5, "y": 3}
  }
}
```

### Сервер → Клиент

```json
{
  "event_type": "CHARACTER_STATUS_UPDATE",
  "data": {
    "character_id": "...",
    "hp": 45,
    "position": {"x": 5, "y": 3}
  },
  "source": "player_123",
  "timestamp": "2026-03-01T12:00:00Z"
}
```

### Типы событий

- `PLAYER_ACTION` - Действие игрока
- `CHARACTER_STATUS_UPDATE` - Обновление статуса персонажа
- `SCENE_UPDATE` - Обновление сцены
- `COMBAT_EVENT` - Событие боя
- `TURN_UPDATE` - Обновление очереди ходов
- `MASTER_MESSAGE` - Сообщение от ГМа
- `SESSION_UPDATE` - Обновление состояния сессии

---

## Жизненный цикл сессии

### 1. Создание сессии

```python
# POST /api/v1/sessions
{
  "session_name": "Friday Night D&D",
  "game_mode": "COMBAT",
  "max_players": 5
}

# Response:
{
  "session_id": "uuid...",
  "session_name": "Friday Night D&D",
  "game_mode": "COMBAT",
  "player_count": 0,
  "status": "active"
}
```

### 2. Присоединение игрока

```python
# POST /api/v1/sessions/{session_id}/players
{
  "player_name": "Alice",
  "character_name": "Ogorek the Wizard"
}

# Response:
{
  "player_id": "uuid...",
  "player_name": "Alice",
  "character_name": "Ogorek the Wizard",
  "connected": false
}
```

### 3. WebSocket подключение

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/{session_id}/{player_id}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'CONNECTED':
      console.log('Подключен к сессии');
      break;
    case 'MASTER_MESSAGE':
      displayNarration(data.text);
      break;
    case 'CHARACTER_UPDATE':
      updateCharacter(data.updates);
      break;
    case 'SESSION_UPDATE':
      syncGameState(data.data);
      break;
  }
};

// Отправка действия
ws.send(JSON.stringify({
  event_type: 'PLAYER_ACTION',
  data: { action: 'cast_spell', target: 'orc_warrior' }
}));
```

### 4. Игра использует Session

```python
from server.src.game.session_manager import session_manager

# Получить сессию
session = session_manager.get_session(session_id)

# Получить EventPool
event_pool = session_manager.get_event_pool(session_id)

# Опубликовать событие
event = Event(
    event_type=EventTypes.CHARACTER_STATUS_UPDATE,
    data={"hp": 45},
    source="game_engine"
)
event_pool.add_event(event)

# Обновить UI через Delivery
session.delivery.master_message("Орк атакует!")
session.delivery.send_character_update(orc_id, {"hp": 30})
```

---

## Синхронизация состояния

### Проблема гонки данных
Несколько игроков могут отправлять действия одновременно.

### Решение: asyncio.Lock на сессию

```python
async with await session_manager.get_session_lock(session_id):
    # Критическая секция - только один игрок может изменить состояние
    session.players[0].character.hp -= 10
    session.delivery.send_character_update(...)
```

### EventPool автоматически потокобезопасен
Использует `threading.RLock` для защиты от гонок между:
- Потоком FastAPI (WebSocket)
- Потоком игрового движка

---

## Интеграция с игровым движком

### GameDelivery - мост между движком и WebSocket

```python
from server.src.delivery.game_delivery import GameDelivery

# При создании сессии
delivery = GameDelivery(session_id=session_id)

session = Session(
    session_name="My Game",
    chroma_client=...,
    logger=...,
    generator=...,
    event_pool=event_pool,
    delivery=delivery  # ← Доставляет сообщения через WebSocket
)
```

### Методы Delivery

| Метод | Описание |
|-------|----------|
| `master_message(text, tag)` | Рассылает narration всем игрокам |
| `player_request(character)` | Запрашивает действие (не блокирует) |
| `choose_player(session)` | Объявляет чей ход |
| `session_updated(session)` | Рассылает обновление состояния |
| `send_to_player(player_id, msg)` | Личное сообщение |
| `send_character_update(id, updates)` | Обновление персонажа |
| `send_scene_update(data)` | Обновление сцены |
| `send_combat_event(data)` | Событие боя |

---

## Безопасность

### JWT Аутентификация для WebSocket

```python
@router.websocket("/ws/{session_id}/{player_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    player_id: str,
    token: str = Query(...)  # ← JWT токен
):
    # Проверка токена
    payload = verify_token(token)
    if payload["user_id"] != player_id:
        await websocket.close(code=4003)
        return
```

**TODO:** Добавить JWT проверку в `websocket_game.py`

### Фильтрация gm_secret

При сериализации состояния сессии исключать `gm_secret` поля:

```python
def serialize_session(session: Session) -> dict:
    return {
        "session_name": session.session_name,
        "game_mode": session.game_mode.value,
        # Исключить session.game_master.secret_plans
    }
```

---

## Развёртывание

### Запуск сервера

```bash
# Development
uvicorn server.main:app --reload --host 127.0.0.1 --port 8000

# Production
uvicorn server.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Переменные окружения

```env
# Server
SERVER_HOST=127.0.0.1
SERVER_PORT=8000
DEBUG=false

# Security
SECRET_KEY=your-secret-key-here-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=sqlite:///./maggxdnd.db

# AI
LLAMACPP_CHAT_BASE=http://localhost:8080
```

---

## Пример использования

### 1. Создать сессию

```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "session_name": "Test Session",
    "game_mode": "STORY",
    "max_players": 3
  }'
```

### 2. Присоединиться

```bash
curl -X POST http://localhost:8000/api/v1/sessions/{session_id}/players \
  -H "Content-Type: application/json" \
  -d '{
    "player_name": "Alice",
    "character_name": "Ogorek"
  }'
```

### 3. Подключиться через WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/{session_id}/{player_id}');
```

### 4. Запустить игру

```python
from server.src.game.session_manager import session_manager

session = session_manager.get_session(session_id)
session.delivery.master_message("Добро пожаловать в подземелье!")
```

---

## TODO

- [ ] Добавить JWT аутентификацию для WebSocket
- [ ] Реализовать создание Session с зависимостями (chroma_client, logger, generator)
- [ ] Добавить фильтрацию gm_secret при сериализации
- [ ] Реализовать rate limiting через slowapi
- [ ] Добавить сохранение/загрузку сессий в БД
- [ ] Реализовать историю событий для новых игроков
- [ ] Добавить голосовой чат (опционально)

---

## Диаграмма последовательности

```
Игрок A          WebSocket        SessionManager      EventPool        Игрок B
  │                  │                  │                 │                │
  │──Connect WS─────>│                  │                 │                │
  │                  │──Register───────>│                 │                │
  │                  │                  │──Subscribe─────>│                │
  │                  │<─Connected───────│                 │                │
  │<─Connected───────│                  │                 │                │
  │                  │                  │                 │                │
  │──Action─────────>│                  │                 │                │
  │                  │──Publish─────────────────────────>│                │
  │                  │                  │                 │──Queue────────>│
  │<─Confirm─────────│                  │                 │                │
  │                  │                  │                 │                │
  │                  │                  │                 │──Queue────────>│
  │<─Event───────────│                  │                 │<─Read─────────│
  │                  │                  │                 │                │
```
