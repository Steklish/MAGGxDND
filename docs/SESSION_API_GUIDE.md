# Руководство по использованию Session API

## Обзор

Session API позволяет создавать и управлять игровыми сессиями MAGGxDND через REST API и WebSocket.

## Быстрый старт

### 1. Создание сессии

```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "session_name": "Friday Night D&D",
    "game_mode": "STORY",
    "max_players": 4,
    "guide": "A dark cave where ancient worms guard a magical artifact"
  }'
```

**Ответ:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_name": "Friday Night D&D",
  "game_mode": "STORY",
  "player_count": 0,
  "status": "created"
}
```

### 2. Запуск сессии с инициализацией

```bash
curl -X POST http://localhost:8000/api/v1/sessions/550e8400-e29b-41d4-a716-446655440000/start \
  -H "Content-Type: application/json" \
  -d '{
    "scene_prompt": "A dimly lit cavern with glowing mushrooms and ancient stone walls",
    "character_prompts": [
      "A wise wizard named Ogorek who specializes in fire magic",
      "A brave warrior named Kiron with a sword and shield"
    ],
    "npc_prompts": [
      "An evil giant worm that guards the cave entrance",
      "A mysterious merchant who sells magical items"
    ]
  }'
```

**Ответ:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_name": "Friday Night D&D",
  "game_mode": "STORY",
  "player_count": 2,
  "status": "running"
}
```

### 3. Подключение игрока через WebSocket

```javascript
const session_id = "550e8400-e29b-41d4-a716-446655440000";
const player_id = "player-123";  // Получается из endpoint'а players

const ws = new WebSocket(`ws://localhost:8000/ws/${session_id}/${player_id}`);

ws.onopen = () => {
  console.log("Подключено к сессии!");
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case "CONNECTED":
      console.log("Успешное подключение:", data.message);
      break;
      
    case "MASTER_MESSAGE":
      // Сообщение от ГМа (наррация)
      displayNarration(data.text);
      break;
      
    case "SESSION_UPDATE":
      // Обновление состояния сессии
      updateGameState(data.data);
      break;
      
    case "CHARACTER_UPDATE":
      // Обновление персонажа
      updateCharacter(data.character_id, data.updates);
      break;
      
    case "TURN_UPDATE":
      // Обновление очереди ходов
      updateTurnQueue(data.active_player_id);
      break;
  }
};

// Отправка действия
function sendAction(actionType, actionData) {
  ws.send(JSON.stringify({
    event_type: "PLAYER_ACTION",
    data: {
      action: actionType,
      ...actionData
    }
  }));
}

// Пример: Атака в бою
sendAction("melee_attack", {
  target: "evil_worm",
  weapon: "sword"
});

// Пример: Перемещение
sendAction("move", {
  target_x: 5,
  target_y: 3
});
```

---

## Полное API

### REST Endpoints

#### POST /api/v1/sessions
Создать новую сессию.

**Request Body:**
```json
{
  "session_name": "string (required)",
  "game_mode": "STORY|COMBAT (default: STORY)",
  "max_players": "integer (default: 5)",
  "description": "string (optional)",
  "guide": "string (optional) - Сюжетная подсказка для AI",
  "gemini_api_key": "string (optional)",
  "gemini_model": "string (default: gemini-flash-latest)"
}
```

**Response:** `SessionResponse`

---

#### GET /api/v1/sessions
Получить список всех активных сессий.

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "...",
      "session_name": "Friday Night D&D",
      "game_mode": "STORY",
      "player_count": 2,
      "status": "running"
    }
  ],
  "total": 1
}
```

---

#### GET /api/v1/sessions/{session_id}
Получить информацию о конкретной сессии.

**Response:** `SessionResponse`

---

#### DELETE /api/v1/sessions/{session_id}
Удалить сессию и отключить всех игроков.

**Response:** `204 No Content`

---

#### POST /api/v1/sessions/{session_id}/start
Запустить сессию с инициализацией сцены и персонажей.

**Request Body:**
```json
{
  "scene_prompt": "string (required) - Описание сцены для AI",
  "character_prompts": ["string"] - Описания персонажей игроков,
  "npc_prompts": ["string"] - Описания NPC
}
```

**Response:** `SessionResponse`

---

#### POST /api/v1/sessions/{session_id}/players
Добавить игрока в сессию.

**Request Body:**
```json
{
  "player_name": "string (required)",
  "character_name": "string (optional)",
  "character_prompt": "string (optional) - Описание для генерации персонажа"
}
```

**Response:**
```json
{
  "player_id": "uuid",
  "player_name": "Alice",
  "character_name": "Ogorek",
  "connected": false
}
```

---

#### GET /api/v1/sessions/{session_id}/players
Получить список игроков в сессии.

**Response:** `List[PlayerResponse]`

---

#### DELETE /api/v1/sessions/{session_id}/players/{player_id}
Удалить игрока из сессии.

**Response:** `204 No Content`

---

### WebSocket API

#### Подключение

```
ws://localhost:8000/ws/{session_id}/{player_id}
```

#### Сообщения Клиент → Сервер

**PLAYER_ACTION:**
```json
{
  "event_type": "PLAYER_ACTION",
  "data": {
    "action": "melee_attack",
    "target": "orc_warrior",
    "weapon": "sword"
  }
}
```

**MOVE:**
```json
{
  "event_type": "PLAYER_ACTION",
  "data": {
    "action": "move",
    "target_x": 5,
    "target_y": 3
  }
}
```

**CAST_SPELL:**
```json
{
  "event_type": "PLAYER_ACTION",
  "data": {
    "action": "cast_spell",
    "spell_name": "fireball",
    "target": "group_of_orcs"
  }
}
```

**INTERACT:**
```json
{
  "event_type": "PLAYER_ACTION",
  "data": {
    "action": "interact",
    "object": "chest",
    "interaction": "open"
  }
}
```

---

#### Сообщения Сервер → Клиент

**CONNECTED:**
```json
{
  "type": "CONNECTED",
  "session_id": "...",
  "player_id": "...",
  "message": "Successfully connected to game session"
}
```

**MASTER_MESSAGE:**
```json
{
  "type": "MASTER_MESSAGE",
  "text": "Дракон просыпается и рычит на вас!",
  "tag": "narration"
}
```

**SESSION_UPDATE:**
```json
{
  "type": "SESSION_UPDATE",
  "data": {
    "session_name": "Friday Night D&D",
    "game_mode": "COMBAT",
    "scene_name": "Dragon's Lair",
    "player_count": 3,
    "turn_queue": [
      {"entity_id": "...", "entity_type": "player"},
      {"entity_id": "...", "entity_type": "npc"}
    ]
  }
}
```

**CHARACTER_UPDATE:**
```json
{
  "type": "CHARACTER_UPDATE",
  "character_id": "...",
  "updates": {
    "hp": 45,
    "position": {"x": 5, "y": 3},
    "status_effects": ["burning"]
  }
}
```

**SCENE_UPDATE:**
```json
{
  "type": "SCENE_UPDATE",
  "scene": {
    "name": "Dragon's Lair",
    "description": "A vast cavern with lava flows",
    "objects": [...]
  }
}
```

**COMBAT_EVENT:**
```json
{
  "type": "COMBAT_EVENT",
  "data": {
    "attacker": "Ogorek",
    "target": "Dragon",
    "damage": 15,
    "attack_type": "fireball"
  }
}
```

**TURN_UPDATE:**
```json
{
  "type": "TURN_UPDATE",
  "active_player_id": "...",
  "active_player_name": "Ogorek"
}
```

**ACTION_CONFIRMED:**
```json
{
  "type": "ACTION_CONFIRMED",
  "event": {
    "event_type": "PLAYER_ACTION",
    "data": {...}
  }
}
```

---

## Примеры использования

### Python клиент

```python
import asyncio
import websockets
import json

async def play_game():
    session_id = "550e8400-e29b-41d4-a716-446655440000"
    player_id = "player-123"
    
    async with websockets.connect(
        f"ws://localhost:8000/ws/{session_id}/{player_id}"
    ) as ws:
        # Ждём подтверждения подключения
        welcome = await ws.recv()
        print(f"Подключено: {welcome}")
        
        # Слушаем события
        async for message in ws:
            data = json.loads(message)
            
            if data["type"] == "MASTER_MESSAGE":
                print(f"ГМ: {data['text']}")
                
            elif data["type"] == "TURN_UPDATE":
                if data["active_player_id"] == player_id:
                    print("Ваш ход!")
                    # Отправляем действие
                    await ws.send(json.dumps({
                        "event_type": "PLAYER_ACTION",
                        "data": {
                            "action": "move",
                            "target_x": 5,
                            "target_y": 3
                        }
                    }))

asyncio.run(play_game())
```

### JavaScript/TypeScript клиент

```typescript
class GameSession {
  private ws: WebSocket | null = null;
  private sessionId: string;
  private playerId: string;
  
  constructor(sessionId: string, playerId: string) {
    this.sessionId = sessionId;
    this.playerId = playerId;
  }
  
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(
        `ws://localhost:8000/ws/${this.sessionId}/${this.playerId}`
      );
      
      this.ws.onopen = () => resolve();
      this.ws.onerror = (e) => reject(e);
      
      this.ws.onmessage = (event) => this.handleMessage(JSON.parse(event.data));
    });
  }
  
  private handleMessage(data: any) {
    switch(data.type) {
      case 'MASTER_MESSAGE':
        this.displayNarration(data.text);
        break;
      case 'CHARACTER_UPDATE':
        this.updateCharacter(data.character_id, data.updates);
        break;
      case 'TURN_UPDATE':
        this.onTurnUpdate(data.active_player_id);
        break;
    }
  }
  
  sendAction(action: string, data: Record<string, any>) {
    if (this.ws) {
      this.ws.send(JSON.stringify({
        event_type: 'PLAYER_ACTION',
        data: { action, ...data }
      }));
    }
  }
  
  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Использование
const game = new GameSession(sessionId, playerId);
await game.connect();
game.sendAction('melee_attack', { target: 'orc', weapon: 'sword' });
```

---

## Обработка ошибок

### HTTP Ошибки

| Код | Описание |
|-----|----------|
| 404 | Сессия не найдена |
| 503 | SKLS зависимости не установлены |
| 500 | Внутренняя ошибка сервера |

### WebSocket Коды закрытия

| Код | Описание |
|-----|----------|
| 4004 | Session not found |
| 4005 | Subscription failed |
| 4003 | Authentication failed (TODO) |

---

## Конфигурация

### Переменные окружения

```env
# AI Settings
GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL=gemini-flash-latest

# Database
CHROMA_DB_PATH=./chroma_db/data.db

# Server
SERVER_HOST=127.0.0.1
SERVER_PORT=8000

# Logging
LOG_DIR=./log
```

---

## Best Practices

### 1. Управление подключением

```javascript
// ✅ ХОРОШО: Автоматическое переподключение
class ResilientWebSocket {
  constructor(url) {
    this.url = url;
    this.connect();
  }
  
  connect() {
    this.ws = new WebSocket(this.url);
    this.ws.onclose = () => {
      setTimeout(() => this.connect(), 5000);
    };
  }
}

// ❌ ПЛОХО: Без обработки отключения
const ws = new WebSocket(url);
```

### 2. Обработка событий

```javascript
// ✅ ХОРОШО: Централизованная обработка
class GameClient {
  handleMessage(data) {
    const handlers = {
      'MASTER_MESSAGE': (d) => this.showNarration(d.text),
      'COMBAT_EVENT': (d) => this.updateCombat(d.data),
      'ERROR': (d) => this.showError(d.message)
    };
    
    handlers[data.type]?.(data);
  }
}
```

### 3. Оптимистичные обновления

```javascript
// ✅ ХОРОШО: Показываем сразу, подтверждаем позже
function attack(target) {
  // Оптимистичное обновление UI
  this.showAttackAnimation(this.character, target);
  
  // Отправляем на сервер
  ws.send(JSON.stringify({
    event_type: 'PLAYER_ACTION',
    data: { action: 'attack', target }
  }));
  
  // Если ошибка - откатываем
  ws.onmessage = (e) => {
    if (e.data.type === 'ACTION_DENIED') {
      this.rollbackAttack();
    }
  };
}
```

---

## Тестирование

### cURL примеры

```bash
# Создать сессию
SESSION_ID=$(curl -s -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"session_name":"Test"}' | jq -r '.session_id')

# Получить информацию
curl http://localhost:8000/api/v1/sessions/$SESSION_ID

# Запустить сессию
curl -X POST http://localhost:8000/api/v1/sessions/$SESSION_ID/start \
  -H "Content-Type: application/json" \
  -d '{
    "scene_prompt": "A test room",
    "character_prompts": ["A test wizard"],
    "npc_prompts": ["A test goblin"]
  }'

# Удалить сессию
curl -X DELETE http://localhost:8000/api/v1/sessions/$SESSION_ID
```

---

## См. также

- [`SESSION_OWNERSHIP.md`](./SESSION_OWNERSHIP.md) - Модель владения сессией
- [`SERVER_ARCHITECTURE.md`](./SERVER_ARCHITECTURE.md) - Архитектура сервера
- [`/docs`](../) - Полная документация проекта
