# MAGGxDND Full Stack - Инструкция по запуску

## Быстрый старт

### Шаг 1: Запуск сервера с игровым движком

```bash
cd C:\VS_Code\MAGGxDND\UI

# Вариант 1: Простой сервер (без игрового движка)
python start_server.py

# Вариант 2: Полный сервер с игровым движком
python server/launcher_fullstack.py
```

Или напрямую через uvicorn:

```bash
cd C:\VS_Code\MAGGxDND\UI

# Простой сервер
python -m uvicorn server.main:app --reload --host 0.0.0.0 --port 8000

# Сервер с игровым движком
python -m uvicorn server.main_with_engine:app --reload --host 0.0.0.0 --port 8000
```

### Шаг 2: Запуск UI (React)

В отдельном терминале:

```bash
cd C:\VS_Code\MAGGxDND\UI
npm run dev
```

### Шаг 3: Открытие приложения

Откройте в браузере:
- **UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws/{session_id}/{player_id}

---

## Тестирование API

### 1. Проверка здоровья сервера

```bash
curl http://localhost:8000/health
```

Ответ:
```json
{"status":"healthy"}
```

### 2. Создание сессии

```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d "{\"session_name\":\"Test Campaign\",\"game_mode\":\"STORY\"}"
```

### 3. Инициализация игровой сессии (с игровым движком)

```bash
curl -X POST http://localhost:8000/api/v1/sessions/init \
  -H "Content-Type: application/json" \
  -d "{
    \"session_name\": \"My Adventure\",
    \"game_mode\": \"STORY\",
    \"scene_prompt\": \"A dark dungeon with flickering torches\"
  }"
```

### 4. Регистрация пользователя

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"Player1\",\"password\":\"password123\"}"
```

### 5. Вход

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=Player1&password=password123"
```

---

## Подключение WebSocket

### Через JavaScript (в браузере)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/test-session/Player1');

ws.onopen = () => {
    console.log('Connected!');
    
    // Отправить действие
    ws.send(JSON.stringify({
        type: 'PLAYER_ACTION',
        payload: {
            player_id: 'Player1',
            request_text: 'Look around the room',
            character: { name: 'Player1' },
            timestamp: Date.now() / 1000
        }
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```

### Через Python

```python
import asyncio
import websockets
import json

async def test_websocket():
    async with websockets.connect('ws://localhost:8000/ws/test-session/Player1') as ws:
        # Получить подтверждение подключения
        msg = await ws.recv()
        print('Connected:', msg)
        
        # Отправить действие
        await ws.send(json.dumps({
            'type': 'PLAYER_ACTION',
            'payload': {
                'player_id': 'Player1',
                'request_text': 'Look around',
                'character': {'name': 'Player1'},
                'timestamp': 1234567890.0
            }
        }))
        
        # Получить ответ
        response = await ws.recv()
        print('Response:', response)

asyncio.run(test_websocket())
```

---

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    React UI (порт 8000)                      │
│  - Компоненты: GameLayout, CharacterPanel, ChatPanel, etc.  │
│  - Zustand store для управления состоянием                   │
│  - WebSocket сервис для real-time общения                    │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP + WebSocket
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Server (порт 8000)                      │
│  - main.py: GameDelivery, WebSocket handlers                 │
│  - routes/: REST API endpoints                               │
│  - game_integration.py: интеграция с игровым движком         │
└─────────────────────┬───────────────────────────────────────┘
                      │ Python imports
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              MAGGxDND Game Engine                            │
│  - game/engine.py: Session, Game Loop                        │
│  - entity/player.py, entity/npc.py                           │
│  - interface/delivery.py: Delivery ABC                       │
│  - game/event_pool.py: Pub/Sub система                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Структура проекта

```
C:\VS_Code\MAGGxDND\
├── main.py                      # Точка входа игрового движка
├── game/                        # Игровая логика
│   ├── engine.py               # Session, Game Loop
│   ├── event_pool.py           # Pub/Sub система
│   └── ...
├── interface/                   # Delivery слой
│   └── delivery.py             # Delivery ABC
├── entity/                      # Игровые сущности
│   ├── player.py               # Player
│   ├── npc.py                  # NPC
│   └── ...
└── UI/                          # Frontend + Backend
    ├── src/                     # React компоненты
    ├── server/                  # FastAPI сервер
    │   ├── main.py             # Базовый сервер
    │   ├── main_with_engine.py # Сервер с игровым движком
    │   ├── game_integration.py # Модуль интеграции
    │   ├── routes/             # REST endpoints
    │   │   ├── sessions.py
    │   │   ├── characters.py
    │   │   └── auth.py
    │   └── websocket/          # WebSocket handlers
    └── start_server.py         # Скрипт запуска
```

---

## Режимы работы

### 1. Простой сервер (без игрового движка)

- Только REST API и WebSocket
- Нет реальной игровой логики
- Подходит для тестирования UI

```bash
python -m uvicorn server.main:app --reload
```

### 2. Полный сервер (с игровым движком)

- Полная интеграция с MAGGxDND
- Реальный game loop
- AI Dungeon Master через Gemini API

```bash
python -m uvicorn server.main_with_engine:app --reload
```

**Требования:**
- GEMINI_API_KEY (переменная окружения)
- LLAMACPP_EMBED_BASE (опционально, для эмбеддингов)

---

## Переменные окружения

Создайте файл `.env` в корне проекта:

```env
# Google Gemini API
GEMINI_API_KEY=your_api_key_here

# LlamaCPP Embeddings (опционально)
LLAMACPP_EMBED_BASE=localhost:12345

# Server settings
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

---

## Логирование

Логи пишутся в:
- `C:\VS_Code\MAGGxDND\log\game_server.log` - простой сервер
- `C:\VS_Code\MAGGxDND\log\fullstack_server.log` - полный сервер

---

## Устранение проблем

### Ошибка: "ModuleNotFoundError: No module named 'server'"

Убедитесь, что запускаете из папки `UI`:
```bash
cd C:\VS_Code\MAGGxDND\UI
python -m uvicorn server.main:app --reload
```

### Ошибка: "GEMINI_API_KEY not set"

Установите переменную окружения:
```bash
set GEMINI_API_KEY=your_key_here
```

Или в `.env` файле.

### WebSocket не подключается

1. Проверьте, что сервер запущен
2. Проверьте URL: `ws://localhost:8000/ws/{session_id}/{player_id}`
3. Откройте консоль браузера (F12) для ошибок

### UI не видит API

1. Проверьте, что оба сервера запущены (UI и API)
2. Проверьте proxy в `vite.config.ts`
3. Попробуйте открыть http://localhost:8000/api/v1/sessions напрямую

---

## Следующие шаги

1. **Тестирование UI**: Откройте http://localhost:8000 и попробуйте создать сессию
2. **Подключение WebSocket**: Используйте браузерную консоль для тестирования
3. **Запуск игры**: Инициализируйте сессию через API и подключитесь через WebSocket
4. **Интеграция с AI**: Настройте GEMINI_API_KEY для AI Dungeon Master

---

## Контакты

Проект: MAGGxDND
Автор: Anton Kozlov
Версия: 0.2.0
