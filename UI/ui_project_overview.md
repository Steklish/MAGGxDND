# MAGGxDND UI Project Documentation

## 📖 Что это за проект?

**MAGGxDND** — это система для проведения настольных ролевых игр (НРИ) в стиле Dungeons & Dragons с использованием искусственного интеллекта в качестве ведущего (Game Master). 

Данный проект представляет собой **UI-часть (Frontend)**, которая предоставляет веб-интерфейс для взаимодействия игроков с игровым движком.

---

## 🎯 Назначение UI

UI выполняет следующие функции:

1. **Отображение игрового состояния**
   - Визуализация сцены (карта с персонажами и объектами)
   - Отслеживание здоровья и статусов персонажей
   - Очередь ходов в боевом режиме

2. **Ввод действий игроков**
   - Форма для отправки действий персонажа
   - Выбор целей для атак/заклинаний
   - Мета-комментарии (вне игрового процесса)

3. **Получение narrации от GM**
   - Отображение сообщений от ведущего
   - Уведомления о результатах действий
   - Системные сообщения

4. **Управление сессией**
   - Создание/загрузка игровой сессии
   - Подключение/отключение игроков
   - Настройки игры

---

## 🏗️ Архитектура проекта

### Общая структура

```
┌─────────────────────────────────────────────────────────────┐
│                    Игровой движок (Python)                   │
│  C:\VS_Code\MAGGxDND\                                        │
│  - game/engine.py (Session, Game Loop)                       │
│  - interface/delivery.py (Abstract Delivery Layer)           │
│  - game/event_pool.py (Pub/Sub Events)                       │
│  - schemas/in_game.py (Character, Scene, Item, etc.)         │
│  - entity/player.py, entity/npc.py                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ WebSocket + REST API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    UI Сервер (Python FastAPI)                │
│  C:\VS_Code\MAGGxDND\UI\server\ (TO BE CREATED)              │
│  - GameDelivery (реализация абстрактного класса Delivery)    │
│  - WebSocket handlers (real-time events)                     │
│  - REST endpoints (session management)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP + WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    UI Клиент (React + TypeScript)            │
│  C:\VS_Code\MAGGxDND\UI\src\                                 │
│  - Компоненты React                                          │
│  - Zustand store (state management)                          │
│  - WebSocket client                                          │
│  - API client (axios)                                        │
└─────────────────────────────────────────────────────────────┘
```

### Ключевые концепции

#### 1. Delivery Pattern

`Delivery` — это абстрактный класс в `interface/delivery.py`, который определяет **контракт** между игровым движком и интерфейсом:

```python
class Delivery(ABC):
    @abstractmethod
    def master_message(self, text: str, tag: str | None = None):
        """Отобразить сообщение от ведущего (DM)"""
        pass

    @abstractmethod
    def player_request(self, character: Character) -> str:
        """Получить действие от игрока"""
        pass

    @abstractmethod
    def choose_player(self, session: "Session") -> "Player":
        """Выбрать игрока, который ходит следующим"""
        pass

    @abstractmethod
    def session_updated(self, session: "Session") -> None:
        """Callback при обновлении состояния сессии"""
        pass
```

**Наша задача:** Создать `GameDelivery` класс, который реализует эти методы через WebSocket.

#### 2. Event Pool (Pub/Sub)

Система событий построена на паттерне **Publish-Subscribe**:

```python
# Создание event pool
event_pool = EventPool()

# Подписка игрока на события
player_queue = event_pool.subscribe("Player1")

# Публикация события
event = Event(
    event_type=EventTypes.CHARACTER_MOVEMENT,
    event_initiator="Player1",
    description="Player1 moves to (5, 5)"
)
event_pool.add_event(event)  # Все подписчики получат

# Или только другим (кроме инициатора)
player_queue.publish_to_others(event)
```

**Типы событий** определены в `schemas/orchestration.py`:
- `CHARACTER_MOVEMENT` — перемещение персонажа
- `CHARACTER_STATUS_CHANGE` — изменение статуса (HP, условия)
- `ITEM_PICKUP` — подбор предмета
- `ACTION_RESULT` — результат действия
- И многие другие...

#### 3. Request Queue

Для обработки действий игроков используется **очередь запросов**:

```python
# Игрок отправляет действие
request = Request(
    player_id="Player1",
    request_text="Attack the goblin with my sword",
    timestamp=1234567890.0,
    character=character_data
)
delivery.put_request(request)

# Движок получает действие
request = delivery.wait_for_request(timeout=30.0)
if request:
    action = request.request_text
```

#### 4. Turn-Based System

Боевая система использует **очередь ходов** на основе инициативы:

```python
# Структура очереди ходов
turn_queue = [
    (character, time_added, next_turn_time),
    ...
]

# Инициатива рассчитывается как:
initiative_bonus = dexterity + speed
```

#### 5. Spatial System

Каждая сцена имеет **2D координаты**:

```python
# Сцена
scene = SceneNode(
    name="Tavern",
    dimensions=Coordinate2D(x=20.0, y=20.0),
    center_position=Coordinate2D(x=0.0, y=0.0)
)

# Персонаж
character = Character(
    name="Ogorek",
    position=Coordinate2D(x=3.5, y=7.2)
)
```

---

## 📁 Структура проекта

### Корневая папка: `C:\VS_Code\MAGGxDND\`

```
MAGGxDND/
├── main.py                    # Точка входа игрового движка
├── requirements.txt           # Python зависимости
├── game/                      # Игровая логика
│   ├── engine.py             # Session, Game Loop
│   ├── event_pool.py         # Pub/Sub система событий
│   ├── manipulator.py        # Манипуляции с состоянием
│   └── ...
├── interface/                 # Слой доставки (Delivery Layer)
│   ├── delivery.py           # Абстрактный класс Delivery
│   └── native_terminal_delivery.py  # Консольная реализация
├── entity/                    # Игровые сущности
│   ├── player.py             # Player entity
│   ├── npc.py                # NPC entity
│   └── orchestrator.py       # Orchestrator для управления
├── schemas/                   # Pydantic модели данных
│   ├── in_game.py            # Character, Scene, Item, etc.
│   ├── orchestration.py      # Event, Message, etc.
│   └── save_game.py          # Сохранения
├── prompts/                   # Промпты для AI
├── magg/                      # AI генерация
├── skls_generator/           # Генераторы
├── skls_embeddings/          # Векторные эмбеддинги
├── utils/                     # Утилиты
├── UI/                        # ← МЫ РАБОТАЕМ ЗДЕСЬ
│   ├── server_requirements.md    # Требования к серверу
│   ├── ui_project_overview.md    # Этот файл
│   ├── dev_diary.md              # Дневник разработки
│   ├── package.json              # Node.js зависимости
│   ├── vite.config.ts            # Vite конфиг
│   ├── tsconfig.json             # TypeScript конфиг
│   ├── index.html                # HTML шаблон
│   └── src/                      # Исходный код React
│       ├── main.tsx              # Точка входа React
│       ├── App.tsx               # Главный компонент
│       ├── components/           # React компоненты
│       ├── hooks/                # Custom hooks
│       ├── store/                # Zustand store
│       ├── services/             # API & WebSocket
│       └── types/                # TypeScript типы
└── ...
```

### UI папка: `C:\VS_Code\MAGGxDND\UI\`

```
UI/
├── server_requirements.md    # Подробные требования к серверу
├── ui_project_overview.md    # Общий обзор проекта (этот файл)
├── dev_diary.md              # Дневник разработки
├── package.json              # Зависимости и скрипты
├── vite.config.ts            # Конфигурация Vite
├── tsconfig.json             # Конфигурация TypeScript
├── tsconfig.node.json        # TypeScript для Node
├── eslint.config.js          # ESLint правила
├── .gitignore                # Git игнор
├── index.html                # HTML шаблон
└── src/
    ├── main.tsx              # Точка входа React
    ├── App.tsx               # Главный компонент
    ├── vite-env.d.ts         # Vite типы
    ├── components/           # UI компоненты
    │   ├── Scene/           # Компоненты сцены
    │   ├── Character/       # Компоненты персонажей
    │   ├── TurnQueue/       # Очередь ходов
    │   ├── Chat/            # Чат/лог событий
    │   └── common/          # Общие компоненты
    ├── hooks/               # Custom React hooks
    │   ├── useWebSocket.ts  # WebSocket хук
    │   └── useGameStore.ts  # Store хук
    ├── store/               # Zustand state management
    │   ├── gameStore.ts     # Основное состояние игры
    │   └── middleware/      # Middleware для store
    ├── services/            # API клиенты
    │   ├── websocket.ts     # WebSocket сервис
    │   └── api.ts           # REST API сервис
    └── types/               # TypeScript типы
        ├── game.ts          # Игровые типы
        └── api.ts           # API типы
```

---

## 🔧 Технологический стек

### Frontend (UI Client)

| Технология | Версия | Назначение |
|------------|--------|------------|
| React | 19.x | UI библиотека |
| TypeScript | 5.7.x | Типизация |
| Vite | 6.1.x | Сборщик |
| Zustand | 5.0.x | State management |
| Axios | 1.7.x | HTTP клиент |
| ESLint | 9.19.x | Линтинг |

### Backend (UI Server) - TO BE CREATED

| Технология | Версия | Назначение |
|------------|--------|------------|
| Python | 3.10+ | Язык сервера |
| FastAPI | 0.109+ | Web фреймворк |
| Uvicorn | 0.27+ | ASGI сервер |
| WebSockets | 12.0+ | Real-time связь |
| Pydantic | 2.0+ | Валидация данных |

---

## 📊 Основные типы данных

### Character (Персонаж)

```typescript
interface Character {
    // Идентификация
    name: string;
    race: string;
    char_class: CharacterClass;
    level: number;
    
    // Характеристики
    stats: {
        strength: number;
        dexterity: number;
        constitution: number;
        intelligence: number;
        wisdom: number;
        charisma: number;
    };
    
    // Состояние
    max_hp: number;
    current_hp: number;
    temp_hp: number;
    armor_class: number;
    speed: number;
    
    // Инвентарь и способности
    inventory: Item[];
    abilities: SpellAbility[];
    active_conditions_list: Condition[];
    
    // Позиция
    position: { x: number; y: number };
    
    // Вычисляемые поля
    proficiency_bonus: number;
    is_alive: boolean;
    initiative_bonus: number;
}
```

### Scene (Сцена)

```typescript
interface SceneNode {
    name: string;
    description: string;
    objects: UnifiedObject[];
    center_position: { x: number; y: number };
    dimensions: { x: number; y: number };
    scale_unit: string;
    // gm_secret - ТОЛЬКО СЕРВЕР, не отправлять клиенту!
}
```

### Event (Событие)

```typescript
interface Event {
    event_type: EventType;
    event_initiator?: string;
    event_subject?: string;
    event_target?: string;
    description: string;
}

type EventType = 
    | "CHARACTER_MOVEMENT"
    | "CHARACTER_STATUS_CHANGE"
    | "ITEM_PICKUP"
    | "ACTION_RESULT"
    | "SYSTEM"
    | "...";
```

---

## 🎮 Игровой цикл (Game Loop)

Упрощённая схема работы игрового движка:

```
1. Session.init() - Инициализация сессии
   ├─ Загрузка сцены
   ├─ Создание персонажей
   └─ Инициализация NPC

2. Game Loop (asyncio.run(session.game_loop()))
   ├─ while True:
   │   ├─ choose_player() - Выбрать кто ходит
   │   ├─ player_request() - Получить действие
   │   ├─ orchestrator.process() - Обработать действие
   │   ├─ manipulator.apply() - Применить изменения
   │   ├─ session_updated() - Уведомить UI
   │   └─ event_pool.add_event() - Опубликовать событие
   └─ repeat
```

---

## 🔗 Связь между компонентами

### Поток данных при действии игрока

```
1. Игрок вводит действие в UI
   ↓
2. React компонент отправляет через WebSocket
   ↓
3. GameDelivery.player_request() получает
   ↓
4. Orchestrator обрабатывает действие
   ↓
5. Manipulator применяет изменения к сессии
   ↓
6. Session.session_updated() уведомляет Delivery
   ↓
7. GameDelivery рассылает обновления через WebSocket
   ↓
8. UI получает и отображает изменения
```

### Поток событий

```
1. Событие происходит в движке
   ↓
2. EventPool.add_event(event)
   ↓
3. EventPool рассылает всем SubscriberQueue
   ↓
4. WebSocket handler читает из очереди
   ↓
5. Отправляет через WebSocket клиенту
   ↓
6. UI обрабатывает и отображает
```

---

## 📝 Глоссарий

| Термин | Определение |
|--------|-------------|
| **Delivery** | Абстрактный слой между движком и интерфейсом |
| **Session** | Игровая сессия с состоянием (сцена, персонажи, NPC) |
| **EventPool** | Централизованная система публикации/подписки на события |
| **SubscriberQueue** | Персональная очередь событий для подписчика |
| **RequestQueue** | Очередь действий игроков |
| **Orchestrator** | Компонент для обработки и вердиктов действий |
| **Manipulator** | Компонент для применения изменений к сессии |
| **Turn Queue** | Очередь ходов на основе инициативы |
| **Scene** | Игровая локация с 2D координатами |
| **Character** | Персонаж игрока или NPC |

---

## 🚀 Быстрый старт

### Для разработчиков UI

1. **Установка зависимостей**
   ```bash
   cd C:\VS_Code\MAGGxDND\UI
   npm install
   ```

2. **Запуск dev сервера** (после создания)
   ```bash
   npm run dev
   ```

3. **Сборка**
   ```bash
   npm run build
   ```

### Для разработчиков сервера

1. **Установка зависимостей** (после создания server/)
   ```bash
   pip install fastapi uvicorn websockets pydantic
   ```

2. **Запуск сервера**
   ```bash
   uvicorn server.main:app --reload
   ```

---

## 📚 Дополнительные ресурсы

- [server_requirements.md](./server_requirements.md) — Подробные требования к серверу
- [dev_diary.md](./dev_diary.md) — Дневник разработки
- [README.md](./README.md) — Основной README проекта

---

## ❓ FAQ

### Q: Почему WebSocket, а не только REST?
**A:** Игровой процесс требует real-time обновлений (ходы, события, narrация). REST polling был бы неэффективен.

### Q: Можно ли использовать готовый UI фреймворк?
**A:** Да, рекомендуется использовать Bootstrap/Material-UI для ускорения разработки.

### Q: Как обрабатывать GM секреты?
**A:** Никогда не отправлять поле `gm_secret` из `SceneNode` клиенту. Сервер должен фильтровать его при сериализации.

### Q: Как масштабировать на несколько сессий?
**A:** Каждая сессия имеет свой `EventPool` и `Delivery` экземпляр. WebSocket подключения мультиплексируются по `session_id`.

---

**Последнее обновление:** 2026-02-19
