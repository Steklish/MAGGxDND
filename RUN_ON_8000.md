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
pip install -r requirements.txt
```

### 2. Запуск сервера (порт 8000)

```bash
# Из корневой директории проекта
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

Или через Python:
```bash
cd server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Открыть в браузере

Перейдите на **http://localhost:8000**

## Режимы разработки

### Вариант 1: Сервер с UI (рекомендуется)
Сервер раздает UI файлы и API на одном порту:
```bash
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```
- UI: http://localhost:8000
- API: http://localhost:8000/api/v1
- WebSocket: ws://localhost:8000/ws/{session_id}/{player_id}
- Docs: http://localhost:8000/docs

### Вариант 2: Раздельный запуск (для разработки UI)

**Терминал 1 - Сервер:**
```bash
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

**Терминал 2 - UI Dev Server:**
```bash
cd UI
npm run dev
```
- UI: http://localhost:8000 (Vite dev server)
- API проксируется на http://localhost:8000

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
└── requirements.txt     # Python зависимости
```

## Как это работает

1. **Production режим**: Сервер раздает статические файлы из `UI/dist/`
2. **Dev режим**: Vite dev server на порту 8000 с проксированием API/WebSocket
3. **WebSocket**: Автоматически подключается к тому же хосту (`window.location.host`)
4. **API**: Все запросы идут на `/api/v1` (относительный путь)

## API Endpoints

- `GET /` - Информация об API
- `GET /api/v1/sessions` - Список сессий
- `POST /api/v1/sessions` - Создать сессию
- `GET /api/v1/sessions/{id}` - Информация о сессии
- `DELETE /api/v1/sessions/{id}` - Удалить сессию
- `POST /api/v1/sessions/{id}/start` - Запустить сессию
- `POST /api/v1/sessions/{id}/players` - Присоединиться к сессии
- `WS /ws/{session_id}/{player_id}` - WebSocket для real-time событий

## Документация

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
