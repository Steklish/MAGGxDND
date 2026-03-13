# 📝 Система Логирования MAGGxDND

## 🎯 Обзор

Всеобъемлющая система логирования для отслеживания всех операций в приложении.

---

## 📁 Структура Логов

```
logs/
├── application.log          # Основные логи приложения
├── application.json         # JSON логи (структурированные)
├── errors.log               # Только ошибки
├── api/
│   └── api.log             # API запросы
├── ai/
│   ├── requests.log        # AI запросы (полные)
│   └── responses.log       # AI ответы (полные)
├── database/
│   └── database.log        # Database queries
├── game/
│   └── game.log            # Game engine events
└── websocket/
    └── websocket.log       # WebSocket events
```

---

## 🔧 Использование

### Базовое Логирование

```python
from backend.src.logging import get_logger

logger = get_logger('my_module')

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.exception("Exception with traceback")
```

### Логирование с Контекстом

```python
from backend.src.logging import LogContext

with LogContext(logger, user_id=123, action='create_character'):
    logger.info("Character created")
    # Log will include: user_id=123, action='create_character'
```

### AI Логирование

```python
from backend.src.services.ai_service_logger import AIServiceLogger

ai_logger = AIServiceLogger(ai_client)

# All interactions are automatically logged
response = await ai_logger.generate("Describe a dragon")

# Logs include:
# - Full request (prompt, parameters)
# - Full response
# - Processing time
# - Token estimates
```

### API Логирование

```python
# Automatically logged by APILoggingMiddleware
# No manual intervention needed

# Every API request logs:
# - Method, path, headers
# - Request body (for POST/PUT/PATCH)
# - Response status code
# - Processing time
# - User information
```

---

## 📊 Уровни Логирования

| Уровень | Описание | Пример |
|---------|----------|--------|
| DEBUG | Детальная отладочная информация | Полные запросы/ответы |
| INFO | Общая информация о работе | "API Request started" |
| WARNING | Предупреждения | "Slow request detected" |
| ERROR | Ошибки | "Database connection failed" |
| CRITICAL | Критические ошибки | "System shutdown" |

---

## 🎨 Форматы

### Console (Colored)
```
2026-03-12 19:00:00 - main - INFO - MAGGxDND Server Starting
2026-03-12 19:00:01 - api - 📥 API Request [api_20260312_190001_0]
2026-03-12 19:00:01 - ai - 🤖 AI Generation Started [req_20260312_190001_0]
```

### File (Detailed)
```
2026-03-12 19:00:00 - main - INFO - [main.on_startup:95] - MAGGxDND Server Starting
```

### JSON (Structured)
```json
{
  "timestamp": "2026-03-12T19:00:00.000Z",
  "level": "INFO",
  "logger": "main",
  "message": "MAGGxDND Server Starting",
  "module": "main",
  "function": "on_startup",
  "line": 95
}
```

---

## 📈 Метрики

### AI Statistics
```python
stats = ai_logger.get_stats()
# {
#   'total_requests': 100,
#   'total_tokens': 50000,
#   'total_time_seconds': 45.2,
#   'avg_time_per_request': 0.45
# }
```

### API Statistics
```python
stats = api_middleware.get_stats()
# {
#   'total_requests': 1000,
#   'total_errors': 15,
#   'error_rate': 1.5
# }
```

---

## 🔍 Поиск и Анализ

### Поиск по Request ID
```bash
# Найти все логи для конкретного запроса
grep "req_20260312_190001_0" logs/ai/requests.log
grep "req_20260312_190001_0" logs/ai/responses.log
```

### Поиск Ошибок
```bash
# Найти все ошибки за сегодня
grep "ERROR" logs/application.log | grep "2026-03-12"
```

### Анализ Медленных Запросов
```bash
# Найти запросы медленнее 2 секунд
grep "Slow Request" logs/application.log
```

---

## 🛠️ Настройка

### Изменение Уровня Логирования

```python
setup_logging(
    log_dir='./logs',
    console_level=logging.INFO,    # Уровень для консоли
    file_level=logging.DEBUG,      # Уровень для файлов
    max_bytes=10*1024*1024,        # 10MB до ротации
    backup_count=5,                # Хранить 5 файлов
    enable_json_logs=True          # Включить JSON логи
)
```

### Добавление Нового Логгера

```python
from backend.src.logging import get_logger

# Создать логгер для нового модуля
websocket_logger = get_logger('websocket')

# Автоматически будет писать в logs/websocket/websocket.log
```

---

## 📝 Примеры Использования

### 1. Логирование в Сервисе

```python
from backend.src.logging import get_logger, LogContext

logger = get_logger('character_service')

class CharacterService:
    async def create_character(self, user_id: int, data: dict):
        with LogContext(logger, user_id=user_id, action='create_character'):
            logger.info(
                "Creating character",
                extra={
                    'character_name': data.get('name'),
                    'character_class': data.get('char_class')
                }
            )
            
            try:
                character = await self._create(data)
                
                logger.info(
                    "Character created successfully",
                    extra={'character_id': character.id}
                )
                
                return character
                
            except Exception as e:
                logger.error(
                    "Failed to create character",
                    extra={'error': str(e)},
                    exc_info=True
                )
                raise
```

### 2. Логирование API Запросов

```python
# Автоматически обрабатывается middleware
# Пример того что логируется:

📥 API Request [api_20260312_190001_0]
   Method: POST
   Path: /api/v1/characters
   Client: 127.0.0.1
   User: {'id': 1, 'username': 'testuser'}
   Body: {"name": "Gandalf", "class": "Wizard"}

✅ [200] POST /api/v1/characters
   Time: 125.45ms
```

### 3. Логирование AI Взаимодействий

```python
# Полный цикл AI запроса:

🤖 AI Generation Started [req_20260312_190001_0]
   Model: gemini-2.0-flash
   Prompt: Describe a dark cave...
   Length: 150 chars

📝 Full request logged to: logs/ai/requests.log
{
  "request_id": "req_20260312_190001_0",
  "timestamp": "2026-03-12T19:00:01.000Z",
  "model": "gemini-2.0-flash",
  "prompt": "Describe a dark cave...",
  "parameters": {...}
}

✅ AI Generation Complete [req_20260312_190001_0]
   Response Length: 500 chars
   Time: 1250.00ms

📝 Full response logged to: logs/ai/responses.log
{
  "request_id": "req_20260312_190001_0",
  "timestamp": "2026-03-12T19:00:02.250Z",
  "success": true,
  "response": "The cave is dark and eerie...",
  "metrics": {...}
}
```

---

## 🚨 Обработка Ошибок

### Логирование Исключений

```python
try:
    result = risky_operation()
except Exception as e:
    logger.error(
        "Operation failed",
        extra={
            'error': str(e),
            'error_type': type(e).__name__,
            'operation': 'risky_operation'
        },
        exc_info=True  # Включает traceback
    )
```

### Critical Errors

```python
logger.critical(
    "Database connection lost",
    extra={
        'database': settings.DATABASE_URL,
        'retry_count': retry_count
    },
    exc_info=True
)
```

---

## 📊 Анализ и Мониторинг

### Просмотр Логов в Реальном Времени

```bash
# Следить за логами
tail -f logs/application.log

# Следить за ошибками
tail -f logs/errors.log

# Следить за AI запросами
tail -f logs/ai/requests.log
```

### Поиск Паттернов

```bash
# Количество ошибок по типам
grep "error_type" logs/application.log | sort | uniq -c

# Среднее время ответа API
grep "processing_time_ms" logs/application.log | awk '{sum+=$NF; count++} END {print sum/count}'

# Топ медленных запросов
grep "Slow Request" logs/application.log | sort -t: -k4 -n | tail -10
```

---

## 🔒 Безопасность

### Чувствительные Данные

```python
# Middleware автоматически исключает:
headers = {k: v for k, v in headers.items() 
           if k not in ['authorization', 'cookie']}

# Никогда не логируйте:
# - Пароли
# - Токены доступа
# - Личные данные пользователей
```

---

## 📈 Best Practices

1. ✅ Используйте контекст для добавления мета-данных
2. ✅ Логируйте все исключения с `exc_info=True`
3. ✅ Используйте структурированные данные в `extra`
4. ✅ Избегайте логирования чувствительных данных
5. ✅ Разделяйте логи по компонентам
6. ✅ Настройте ротацию логов
7. ✅ Используйте разные уровни для разных целей

---

## 🎯 Следующие Шаги

- [ ] Настроить централизованный сбор логов (ELK Stack)
- [ ] Добавить алерты для критических ошибок
- [ ] Настроить дашборды для мониторинга
- [ ] Интегрировать с Sentry для отслеживания ошибок
- [ ] Добавить метрики в Prometheus

---

**Логируйте всё! 📝**
