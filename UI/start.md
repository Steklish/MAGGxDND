# MAGGxDND - Единый сервер для запуска

## Быстрый старт

### Запуск сервера (порт 8000)

```bash
cd C:\VS_Code\MAGGxDND
python start.py
```

Или из папки UI:

```bash
cd C:\VS_Code\MAGGxDND\UI
python start.py
```

### Открытие приложения

Откройте в браузере: **http://localhost:8000**

---

## Что запускается

1. **FastAPI Server** (порт 8000)
   - REST API: `/api/v1/*`
   - WebSocket: `/ws/*`
   - UI статика: `/`

2. **Game Engine**
   - Session management
   - Event pool
   - Orchestrator

3. **React UI**
   - Сервится из `UI/dist/`
   - SPA роутинг

---

## Требования

### Переменные окружения

Создайте файл `.env` в корне проекта:

```env
# Google Gemini API (обязательно для AI функций)
GEMINI_API_KEY=your_api_key_here

# LlamaCPP Embeddings (опционально)
LLAMACPP_EMBED_BASE=localhost:12345
```

### Установка зависимостей

```bash
# Корневые зависимости
pip install -r requirements.txt

# UI зависимости
cd UI
npm install
```

---

## Режимы работы

### 1. Production (статический UI)

```bash
# Сначала соберите UI
cd UI
npm run build

# Запустите сервер
cd ..
python start.py
```

### 2. Development (Vite dev server)

В двух терминалах:

```bash
# Терминал 1: API сервер
python start.py --no-ui

# Терминал 2: UI dev сервер
cd UI
npm run dev
```

---

## API Endpoints

- **Health**: `GET http://localhost:8000/health`
- **API Docs**: `GET http://localhost:8000/docs`
- **Sessions**: `POST http://localhost:8000/api/v1/sessions`
- **WebSocket**: `ws://localhost:8000/ws/{session_id}/{player_id}`

---

## Структура

```
C:\VS_Code\MAGGxDND\
├── start.py              # Единый лаунчер
├── main.py               # Game engine (console)
├── server/main.py        # FastAPI сервер
├── UI/                   # React frontend
│   ├── src/              # Компоненты
│   ├── dist/             # Build (production)
│   └── start.py          # Лаунчер (ссылка на корневой)
└── log/                  # Логи
```

---

## Устранение проблем

### UI не отображается
```bash
# Соберите UI
cd UI
npm run build
```

### Ошибка GEMINI_API_KEY
```bash
# Установите переменную окружения
set GEMINI_API_KEY=your_key
```

### Порт 8000 занят
```bash
# Измените порт в start.py
# Или остановите процесс на порту 8000
```

---

## Логи

- `log/application.log` - Game engine
- `log/game_server.log` - FastAPI server

---

## Остановка

Нажмите `Ctrl+C` в терминале для остановки сервера.
