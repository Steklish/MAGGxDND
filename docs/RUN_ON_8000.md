# MAGGxDND - Запуск на порту 8000

## Быстрый старт

### 1. Установка зависимостей

**UI:**
```bash
cd UI
npm install
```

**Сервер:**
```bash
# Установить SKLS_core
pip install -e C:\VS_Code\SKLS_core

# Установить остальные зависимости
pip install -r requirements.txt
```

### 2. Запуск сервера (порт 8000)

```bash
# Из корневой директории проекта
set PYTHONPATH=C:\VS_Code\MAGGxDND
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000
```

Или через Python:
```bash
cd server
set PYTHONPATH=..
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 3. Открыть в браузере

Перейдите на **http://localhost:8000**

## Режимы разработки

### Production режим (рекомендуется)
Сервер раздает UI файлы и API на одном порту (8000):

```bash
set PYTHONPATH=C:\VS_Code\MAGGxDND
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000
```

- **UI:** http://localhost:8000
- **API:** http://localhost:8000/api/v1
- **WebSocket:** ws://localhost:8000/ws/{session_id}/{player_id}
- **Docs:** http://localhost:8000/docs

### Dev режим (разработка UI)

**Терминал 1 - Сервер:**
```bash
set PYTHONPATH=C:\VS_Code\MAGGxDND
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000
```

**Терминал 2 - UI Dev Server:**
```bash
cd UI
npm run dev
```

Vite dev server будет работать на порту 8000 с проксированием API/WebSocket на сервер.

## Структура

```
MAGGxDND/
├── server/              # FastAPI сервер
│   ├── main.py         # Точка входа (раздает UI + API)
│   └── src/            # Исходный код сервера
├── UI/                  # React UI
│   ├── src/            # Исходный код UI
│   ├── dist/           # Production сборка (раздается сервером)
│   └── vite.config.ts  # Конфиг Vite (порт 8000)
├── requirements.txt     # Python зависимости
└── RUN_ON_8000.md       # Этот файл
```

## Как это работает

1. **Production режим**: Сервер раздает статические файлы из `UI/dist/`
2. **Dev режим**: Vite dev server на порту 8000 с проксированием API/WebSocket
3. **WebSocket**: Автоматически подключается к тому же хосту (`window.location.host`)
4. **API**: Все запросы идут на `/api/v1` (относительный путь)

## API Endpoints

- `GET /` - UI (React приложение)
- `GET /api/v1/sessions` - Список сессий
- `POST /api/v1/sessions` - Создать сессию
- `GET /api/v1/sessions/{id}` - Информация о сессии
- `DELETE /api/v1/sessions/{id}` - Удалить сессию
- `POST /api/v1/sessions/{id}/start` - Запустить сессию
- `POST /api/v1/sessions/{id}/players` - Присоединиться к сессии
- `WS /ws/{session_id}/{player_id}` - WebSocket для real-time событий

## Документация API

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Требования

- Python 3.12+
- Node.js 18+
- SKLS_core (устанавливается отдельно)

## Troubleshooting

### Ошибка "ModuleNotFoundError: No module named 'skls_generator'"
```bash
pip install -e C:\VS_Code\SKLS_core
```

### Ошибка "UI not built"
```bash
cd UI
npm run build
```

### Порт 8000 занят
```bash
# Найти процесс
netstat -ano | findstr :8000

# Убить процесс (замените PID на нужный)
taskkill /F /PID <PID>
```
