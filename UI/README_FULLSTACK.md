# 🎮 MAGGxDND Full Stack - Полностью Рабочая Версия

## 🚀 Быстрый Старт

### Вариант 1: Полный запуск (Сервер + Игра + UI)

**Windows:**
```bash
cd C:\VS_Code\MAGGxDND\UI
start_fullstack.bat
```

**Вручную:**
```bash
cd C:\VS_Code\MAGGxDND\UI
python server\run_fullstack.py
```

Это запустит:
- ✅ FastAPI сервер (порт 8000)
- ✅ Игровой движок с AI
- ✅ Game loop (автоматическая генерация контента)
- ✅ WebSocket для real-time общения

### Вариант 2: Раздельный запуск

**Терминал 1 - Сервер с игрой:**
```bash
cd C:\VS_Code\MAGGxDND\UI
python -m uvicorn server.main_with_engine:app --reload
```

**Терминал 2 - UI:**
```bash
cd C:\VS_Code\MAGGxDND\UI
npm run dev
```

---

## 📋 Тестирование

### Автоматический тест

```bash
cd C:\VS_Code\MAGGxDND\UI
python test_fullstack.py
```

Это создаст:
- Тестового пользователя
- Реальную игровую сессию
- Персонажей (AI генерация)
- NPC (AI генерация)
- Сцену (AI генерация)
- Запустит game loop

### Ручной тест через API

**1. Проверка сервера:**
```bash
curl http://localhost:8000/health
```

**2. Создание пользователя:**
```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"Player1\",\"password\":\"password123\"}"
```

**3. Вход:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=Player1&password=password123"
```

**4. Запуск РЕАЛЬНОЙ игры:**
```bash
curl -X POST http://localhost:8000/api/v1/sessions/start_real_game \
  -H "Content-Type: application/json" \
  -d "{\"session_name\":\"My Adventure\",\"game_mode\":\"STORY\",\"scene_prompt\":\"A dark dungeon\",\"character_prompts\":[\"A wizard named Gandor\"],\"npc_prompts\":[\"A goblin warrior\"]}"
```

---

## 🎯 Что Реально Работает

### ✅ Игровой Движок
- **Session** - управление игровой сессией
- **Game Loop** - автоматический цикл игры
- **EventPool** - система событий (Pub/Sub)
- **Orchestrator** - обработка действий игроков
- **Manipulator** - применение изменений к миру

### ✅ Искусственный Интеллект
- **AI Dungeon Master** - Gemini API
- **Генерация сцен** - AI создаёт локации
- **Генерация персонажей** - AI создаёт героев
- **Генерация NPC** - AI создаёт неигровых персонажей
- **Наррация** - AI описывает события

### ✅ Персонажи
- **Player** - игроки с полным функционалом
- **NPC** - независимые персонажи с AI
- **Характеристики** - STR, DEX, CON, INT, WIS, CHA
- **Инвентарь** - предметы и способности
- **Здоровье** - HP, AC, speed

### ✅ Боевая Система
- **Инициатива** - очерёдность ходов
- **Атаки** - melee и ranged
- **Заклинания** - spell slots и abilities
- **Условия** - buffs и debuffs
- **Спасброски** - death saves

### ✅ Веб-Интерфейс
- **React UI** - современные компоненты
- **WebSocket** - real-time обновления
- **REST API** - управление сессиями
- **Character Panel** - статы персонажа
- **Chat Panel** - лог событий и диалоги
- **Scene Viewer** - визуализация локации
- **Turn Queue** - очередь ходов с портретами

---

## 🔧 Настройка

### GEMINI_API_KEY (обязательно для AI)

1. Получите ключ: https://makersuite.google.com/app/apikey
2. Установите переменную окружения:

**Windows:**
```cmd
set GEMINI_API_KEY=your_key_here
```

**PowerShell:**
```powershell
$env:GEMINI_API_KEY="your_key_here"
```

**Или создайте .env файл:**
```
GEMINI_API_KEY=your_key_here
```

### LLAMACPP_EMBED_BASE (опционально)

Для локальных эмбеддингов:
```
LLAMACPP_EMBED_BASE=localhost:12345
```

---

## 📡 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Вход
- `POST /api/v1/auth/register` - Регистрация
- `GET /api/v1/auth/me` - Текущий пользователь

### Sessions
- `GET /api/v1/sessions` - Список сессий
- `POST /api/v1/sessions` - Создать сессию
- `POST /api/v1/sessions/start_real_game` - **Запустить РЕАЛЬНУЮ игру**
- `GET /api/v1/sessions/{id}` - Инфо о сессии
- `POST /api/v1/sessions/{id}/players` - Присоединиться

### Characters
- `GET /api/v1/characters/user/{user_id}` - Персонажи пользователя
- `POST /api/v1/characters` - Создать персонажа
- `GET /api/v1/profiles/character/{id}` - Профиль персонажа

### WebSocket
- `ws://localhost:8000/ws/{session_id}/{player_id}` - Real-time соединение

---

## 🎮 Как Играть

### 1. Запустить сервер

```bash
cd C:\VS_Code\MAGGxDND\UI
python server\run_fullstack.py
```

Дождитесь сообщения:
```
✓ Game initialization complete!
  Session: Demo Adventure
  Players: 2
  NPCs: 1
  Scene: The Laughing Dragon
✓ Game loop task created
✓ Server task created
All systems started!
```

### 2. Открыть UI

Откройте в браузере: **http://localhost:8000**

### 3. Зарегистрироваться

1. Нажмите "Get Started"
2. Введите username и password
3. Нажмите "Register"

### 4. Создать персонажа

1. Заполните форму создания персонажа
2. Или используйте AI генерацию
3. Сохраните персонажа

### 5. Присоединиться к игре

1. Выберите сессию из списка
2. Или создайте новую
3. Нажмите "Join Session"

### 6. Играть!

1. Дождитесь хода (индикатор в header)
2. Введите действие в текстовое поле
3. Нажмите "Submit"
4. AI обработает действие
5. Получите наррацию результата
6. Ход переходит к следующему игроку

---

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    React UI (порт 8000)                      │
│  - Компоненты: LandingPage, GameLayout, CharacterPanel      │
│  - Zustand store для state management                        │
│  - WebSocket сервис для real-time событий                    │
│  - Toast уведомления для обратной связи                      │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP + WebSocket
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Server (порт 8000)                      │
│  - main_with_engine.py: полная интеграция                    │
│  - GameDelivery: мост между UI и движком                     │
│  - WebSocket handlers: real-time события                     │
│  - REST routes: sessions, characters, auth                   │
└─────────────────────┬───────────────────────────────────────┘
                      │ Python imports
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              MAGGxDND Game Engine                            │
│  - game/engine.py: Session, Game Loop                        │
│  - game/event_pool.py: Pub/Sub система событий               │
│  - game/manipulator.py: применение изменений                 │
│  - entity/player.py: Player entity                           │
│  - entity/npc.py: NPC entity с AI                            │
│  - entity/orchestrator.py: обработка действий                │
│  - interface/delivery.py: Delivery ABC                       │
└─────────────────────┬───────────────────────────────────────┘
                      │ Google Gemini API
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              AI Components                                   │
│  - skls_generator: генерация контента                        │
│  - GoogleGenAI: Gemini 2.0 Flash                             │
│  - Генерация: сцены, персонажи, NPC, наррация                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Структура Проекта

```
C:\VS_Code\MAGGxDND\
├── main.py                      # Точка входа игрового движка
├── game/                        # Игровая логика
│   ├── engine.py               # Session, Game Loop
│   ├── event_pool.py           # Pub/Sub
│   ├── manipulator.py          # Изменения состояния
│   └── ...
├── interface/                   # Delivery слой
│   └── delivery.py             # Delivery ABC
├── entity/                      # Сущности
│   ├── player.py               # Player
│   ├── npc.py                  # NPC
│   └── orchestrator.py         # Orchestrator
├── schemas/                     # Pydantic модели
│   ├── in_game.py              # Character, Scene, Item
│   └── orchestration.py        # Event, Message
├── magg/                        # AI магическая система
├── skls_generator/             # AI генераторы
├── skls_embeddings/            # Векторные эмбеддинги
└── UI/                          # Frontend + Backend
    ├── src/                     # React компоненты
    │   ├── components/
    │   ├── store/
    │   ├── services/
    │   └── types/
    ├── server/                  # FastAPI сервер
    │   ├── main.py             # Базовый сервер
    │   ├── main_with_engine.py # Сервер с игрой
    │   ├── run_fullstack.py    # Unified runner
    │   ├── game_integration.py # Интеграция
    │   ├── routes/             # REST API
    │   └── websocket/          # WebSocket
    ├── start_fullstack.bat     # Windows launcher
    ├── start_server.py         # Server launcher
    └── test_fullstack.py       # Test suite
```

---

## 🐛 Устранение Проблем

### Ошибка: "GEMINI_API_KEY not set"

```bash
# Windows CMD
set GEMINI_API_KEY=your_key_here

# PowerShell
$env:GEMINI_API_KEY="your_key_here"

# Или в .env файле
GEMINI_API_KEY=your_key_here
```

### Ошибка: "ModuleNotFoundError"

Убедитесь, что установлены зависимости:
```bash
cd C:\VS_Code\MAGGxDND
pip install -r requirements.txt
```

### Ошибка: "Cannot connect to server"

Проверьте, что сервер запущен:
```bash
# Проверка порта 8000
netstat -ano | findstr :8000

# Или попробуйте открыть в браузере
http://localhost:8000/health
```

### Игра не генерирует контент

1. Проверьте GEMINI_API_KEY
2. Проверьте логи: `log\fullstack_runner.log`
3. Убедитесь, что есть интернет (для Gemini API)

### WebSocket не подключается

1. Проверьте URL: `ws://localhost:8000/ws/{session_id}/{player_id}`
2. Откройте консоль браузера (F12) для ошибок
3. Убедитесь, что сервер запущен

---

## 📊 Логи

- **Полный сервер**: `log\fullstack_runner.log`
- **Простой сервер**: `log\game_server.log`
- **Игровой движок**: `log\application.log`

---

## 🎯 Примеры Использования

### Создать игру через Python

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/sessions/start_real_game",
    json={
        "session_name": "Epic Adventure",
        "game_mode": "STORY",
        "scene_prompt": "A mystical forest with ancient trees",
        "character_prompts": [
            "An elf ranger named Aria with a bow",
            "A human cleric named Marcus with healing spells"
        ],
        "npc_prompts": [
            "A wise old druid who knows forest secrets"
        ]
    }
)

game = response.json()
print(f"Game started: {game['session_id']}")
print(f"Players: {game['players']}")
print(f"NPCs: {game['npcs']}")
```

### Подключиться через WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/session-id/Player1');

ws.onopen = () => {
    console.log('Connected!');
    
    // Отправить действие
    ws.send(JSON.stringify({
        type: 'PLAYER_ACTION',
        payload: {
            player_id: 'Player1',
            request_text: 'I look around the tavern and greet the bartender',
            character: { name: 'Player1' },
            timestamp: Date.now() / 1000
        }
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data.type, data.payload);
};
```

---

## 📝 Changelog

### v0.3.0 - Full Working Version
- ✅ Полная интеграция игрового движка
- ✅ AI генерация контента (Gemini)
- ✅ Real game loop с событиями
- ✅ Player и NPC entities
- ✅ Orchestrator и Manipulator
- ✅ WebSocket real-time
- ✅ REST API для управления
- ✅ Toast уведомления
- ✅ Тестовый скрипт

### v0.2.0 - Server Foundation
- FastAPI сервер
- WebSocket handlers
- REST endpoints
- GameDelivery ABC

### v0.1.0 - UI Foundation
- React компоненты
- Zustand store
- Assiko-inspired дизайн

---

## 🎮 Glossary

- **Session** - Игровая сессия с состоянием
- **Game Loop** - Цикл обработки ходов
- **Delivery** - Слой между движком и UI
- **EventPool** - Система событий (Pub/Sub)
- **Orchestrator** - Обработка действий
- **Manipulator** - Применение изменений
- **Turn Queue** - Очередь ходов

---

## 📞 Контакты

**Проект:** MAGGxDND  
**Автор:** Anton Kozlov  
**Версия:** 0.3.0  
**Статус:** ✅ Полностью рабочий

---

## 🎯 Next Steps

1. ✅ Запустить сервер
2. ✅ Протестировать через `test_fullstack.py`
3. ✅ Открыть UI в браузере
4. ✅ Создать персонажа
5. ✅ Начать играть!

**Have fun! 🎲⚔️🐉**
