# 🐉 MAGGxDND

> AI-Powered D&D Game Engine with Real-Time Web Interface

<div align="center">
  <img src="./img/MAGGxDND.png" alt="MAGGxDND Logo" width="60%">
</div>

---

## 📖 О Проекте

**MAGGxDND** — это кроссовер двух важных вещей в моей жизни:
1. Проект, который заставил меня впервые загуглить "что такое API"
2. Проект, добавивший нотку нёрдости в мою персону

Это вторая попытка доделать оба проекта. Теперь с улучшенной архитектурой и веб-интерфейсом!

---

## 🚀 Быстрый Старт

### 1. Настройка окружения

```bash
# Скопируйте шаблон .env
cp .env.example .env

# Отредактируйте .env, добавьте ваш GEMINI_API_KEY
# Получить ключ: https://makersuite.google.com/app/apikey
```

### 2. Установка зависимостей

```bash
# Python зависимости
pip install -r requirements.txt

# SKLS_core (обязательно)
pip install -e C:\VS_Code\SKLS_core

# Frontend зависимости
cd frontend
npm install
npm run build
cd ..
```

### 3. Запуск

```bash
# Запуск сервера
python start.py

# ИЛИ через uvicorn напрямую
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 4. Открыть в браузере

```
http://localhost:8000
```

---

## 📁 Структура Проекта

```
MAGGxDND/
│
├── 📄 main.py                  # Точка входа (CLI версия)
├── 📄 start.py                 # Скрипт запуска сервера
├── 📄 requirements.txt         # Python зависимости
├── 📄 .env.example             # Шаблон переменных окружения
│
├── 📂 backend/                 # Backend сервер (FastAPI)
│   ├── main.py                # FastAPI приложение
│   ├── src/
│   │   ├── api/               # REST API routers
│   │   │   └── routers/
│   │   │       ├── session_router.py    # Управление сессиями
│   │   │       ├── websocket_game.py    # WebSocket для real-time
│   │   │       ├── character.py         # Персонажи API
│   │   │       ├── user.py              # Пользователи API
│   │   │       └── login.py             # Аутентификация
│   │   ├── auth/              # Аутентификация и авторизация
│   │   ├── config/            # Конфигурация приложения
│   │   │   └── settings.py    # Настройки из .env
│   │   ├── database/          # База данных (SQLAlchemy)
│   │   ├── delivery/          # Система доставки событий
│   │   ├── game/              # Менеджмент игровых сессий
│   │   │   ├── session_manager.py
│   │   │   └── session_factory.py
│   │   ├── models/            # SQLAlchemy модели
│   │   ├── repositories/      # Data access layer
│   │   ├── schema/            # Pydantic схемы
│   │   ├── services/          # Бизнес логика
│   │   └── utils/             # Утилиты backend
│   │       ├── security.py    # Хеширование, JWT
│   │       └── validation.py  # Валидация input
│   └── tests/                 # Тесты backend
│
├── 📂 frontend/                # Frontend приложение (React + Vite)
│   ├── src/
│   │   ├── components/        # React компоненты
│   │   │   ├── common/        # Переиспользуемые компоненты
│   │   │   │   ├── ErrorBoundary.tsx
│   │   │   │   ├── LoadingSpinner.tsx
│   │   │   │   ├── Skeleton.tsx
│   │   │   │   └── Toast.tsx
│   │   │   ├── ActionPanel.tsx
│   │   │   ├── CharacterPanel.tsx
│   │   │   ├── ChatPanel.tsx
│   │   │   ├── GameLayout.tsx
│   │   │   ├── LandingPage.tsx
│   │   │   ├── SceneViewer.tsx
│   │   │   ├── SessionCreation.tsx
│   │   │   └── ...
│   │   ├── services/          # API клиенты
│   │   │   ├── api.ts         # REST API клиент
│   │   │   ├── websocket.ts   # WebSocket сервис
│   │   │   ├── sessionAPI.ts  # Session API
│   │   │   └── characterAPI.ts # Character API
│   │   ├── store/             # State management (Zustand)
│   │   │   └── gameStore.ts   # Игровой store
│   │   ├── tests/             # Тесты frontend
│   │   ├── types/             # TypeScript типы
│   │   │   └── game.ts        # Игровые типы
│   │   ├── App.tsx            # Корневой компонент
│   │   └── main.tsx           # Точка входа React
│   ├── arts/                  # Графические ассеты
│   │   ├── backgrounds/       # Фоновые изображения
│   │   ├── characters/        # Портреты персонажей
│   │   ├── items/             # Иконки предметов
│   │   ├── locations/         # Изображения локаций
│   │   ├── effects/           # Визуальные эффекты
│   │   └── ui-elements/       # UI элементы
│   ├── public/                # Статические файлы
│   ├── package.json
│   └── vite.config.ts
│
├── 📂 core/                    # Ядро игрового движка
│   ├── game/                  # Игровой движок
│   │   ├── engine.py          # Основной движок Session
│   │   ├── event_pool.py      # Система событий
│   │   ├── manipulator.py     # Обработка действий
│   │   └── manipulators/      # Модули действий
│   ├── entity/                # Игровые сущности
│   │   ├── player.py          # Игрок
│   │   ├── npc.py             # NPC
│   │   ├── orchestrator.py    # Координатор действий
│   │   └── game_entity.py     # Базовая сущность
│   ├── schemas/               # Схемы данных
│   │   ├── in_game.py         # Игровые схемы
│   │   ├── orchestration.py   # Схемы оркестрации
│   │   └── save_game.py       # Схемы сохранений
│   ├── magg/                  # AI Game Master
│   │   ├── magg.py            # Мастер подземелий
│   │   ├── magg_schemas.py    # Схемы MAGG
│   │   └── plot_schemas.py    # Схемы сюжета
│   ├── interface/             # Интерфейсы доставки
│   │   ├── delivery.py        # Базовый интерфейс
│   │   └── native_terminal_delivery.py
│   └── utils/                 # Утилиты ядра
│       ├── colors.py          # Цвета для терминала
│       ├── dice_utils.py      # Броски кубиков
│       ├── naming_utils.py    # Генерация имен
│       └── spatial_utils.py   # Пространственная логика
│
├── 📂 docs/                    # Документация
│   ├── QUICKSTART.md          # Быстрый старт
│   ├── REORGANIZATION_GUIDE.md # Гид по реорганизации
│   ├── ENV_SETUP_GUIDE.md     # Настройка окружения
│   ├── SERVER_ARCHITECTURE.md # Архитектура сервера
│   ├── SESSION_API_GUIDE.md   # API сессий
│   └── prompts/               # AI промпты
│       ├── character_action_rules.md
│       ├── combat.md
│       ├── DM_personality.md
│       ├── npc.md
│       ├── plot_generation.md
│       └── story.md
│
├── 📂 chroma_db/              # Векторная база данных (ChromaDB)
├── 📂 log/                    # Логи приложения
├── 📂 img/                    # Изображения проекта
├── 📂 prompts/                # AI промпты (дубликат для совместимости)
│
└── 📄 README.md               # Этот файл
```

---

## 🎮 Компоненты

### Backend (FastAPI)

| Компонент | Описание |
|-----------|----------|
| **REST API** | Управление сессиями, персонажами, пользователями |
| **WebSocket** | Real-time обновления игрового состояния |
| **Auth** | JWT аутентификация и авторизация |
| **Rate Limiting** | Защита от злоупотреблений |
| **Validation** | Валидация всех входных данных |

### Frontend (React + Vite)

| Компонент | Описание |
|-----------|----------|
| **GameLayout** | Основной игровой интерфейс |
| **CharacterPanel** | Отображение характеристик |
| **ActionPanel** | Панель действий игрока |
| **ChatPanel** | Чат и лог событий |
| **SceneViewer** | Визуализация сцены |
| **SessionCreation** | Создание новой сессии |

### Core (Game Engine)

| Компонент | Описание |
|-----------|----------|
| **Session** | Управление игровой сессией |
| **EventPool** | Система событий |
| **Manipulator** | Обработка действий |
| **MAGG** | AI Dungeon Master |
| **Orchestrator** | Координация сущностей |

---

## 🔧 Конфигурация

### Переменные окружения

Создайте файл `.env` в корне проекта:

```bash
# Обязательно
GEMINI_API_KEY=your_api_key_here
SECRET_KEY=change-this-for-production

# Опционально
DEBUG=True
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
DATABASE_URL=sqlite:///./data/maggxdnd.db
```

Полный список: см. `.env.example`

---

## 📚 Документация

| Файл | Описание |
|------|----------|
| [QUICKSTART.md](./docs/QUICKSTART.md) | Быстрый старт за 5 минут |
| [ENV_SETUP_GUIDE.md](./backend/ENV_SETUP_GUIDE.md) | Полная настройка окружения |
| [REORGANIZATION_GUIDE.md](./docs/REORGANIZATION_GUIDE.md) | Гид по структуре проекта |
| [SERVER_ARCHITECTURE.md](./docs/SERVER_ARCHITECTURE.md) | Архитектура сервера |
| [SESSION_API_GUIDE.md](./docs/SESSION_API_GUIDE.md) | API управление сессиями |

---

## 🧪 Тестирование

### Backend тесты

```bash
cd backend
pytest tests/
```

### Frontend тесты

```bash
cd frontend
npm run test
```

---

## 🛠 Разработка

### Backend (Dev режим)

```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (Dev режим)

```bash
cd frontend
npm run dev
```

### Одновременный запуск

**Терминал 1** - Backend:
```bash
python start.py
```

**Терминал 2** - Frontend:
```bash
cd frontend
npm run dev
```

---

## 📦 Зависимости

### Python

- **FastAPI** - Web framework
- **Pydantic** - Валидация данных
- **SQLAlchemy** - ORM
- **ChromaDB** - Векторная база
- **Google Generative AI** - AI генерация
- **SlowAPI** - Rate limiting

### Node.js

- **React 19** - UI библиотека
- **Vite** - Build tool
- **Zustand** - State management
- **Axios** - HTTP клиент
- **TypeScript** - Типизация

---

## 🎨 UI Assets

Для настройки графики см. [`frontend/arts/README.md`](./frontend/arts/README.md)

### Required Assets

```
frontend/arts/
├── backgrounds/
│   ├── bg-login.jpg
│   ├── bg-game.jpg
│   └── bg-combat.jpg
├── characters/
│   ├── portrait-default.png
│   └── avatar-*.png
├── items/
│   └── icon-*.png
└── ui-elements/
    └── ui-*.png
```

---

## 🤝 Вклад

1. Fork репозиторий
2. Создай ветку (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в ветку (`git push origin feature/amazing-feature`)
5. Открой Pull Request

---

## 📝 License

Этот проект создан в образовательных целях.

---

## 👨‍💻 Автор

**anton kozlov**

---

<div align="center">

**MAGGxDND** - AI-Powered D&D Game Engine

[Документация](./docs/) • [API Docs](http://localhost:8000/docs) • [GitHub](#)

</div>
