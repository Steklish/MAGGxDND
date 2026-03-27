# 🧪 MAGGxDND - Test Guide

Полное руководство по запуску тестов и отчётам о покрытии кода.

---

## 🚀 Быстрый Запуск

### Windows
```bash
# Запустить все тесты с покрытием
.\run_tests.bat

# Или через npm
npm test
```

### Linux/Mac
```bash
# Запустить все тесты с покрытием
./run_tests.sh

# Или через npm
npm test
```

---

## 📋 Доступные Команды

### Все тесты с покрытием
```bash
.\run_tests.bat              # Windows
./run_tests.sh               # Linux/Mac
npm test                     # Любой OS
npm run test:coverage        # Любой OS
```

### Только Backend тесты
```bash
pytest backend/tests/ -v
pytest backend/tests/ --cov=backend.src --cov-report=html
```

### Только Frontend тесты
```bash
cd frontend
npm run test
npm run test:coverage
npm run test:ui              # С интерфейсом
```

### Отдельные файлы
```bash
# Backend
pytest backend/tests/test_health.py
pytest backend/tests/test_session_api.py -v

# Frontend
cd frontend
npm run test -- src/store/gameStore.test.ts
```

---

## 📊 Отчёты о Покрытии

После запуска тестов с покрытием, отчёты генерируются:

### Backend
- **HTML:** `backend/htmlcov/index.html`
- **XML:** `backend/coverage.xml`

### Frontend
- **HTML:** `frontend/coverage/index.html`

### 🌐 Автоматическое Открытие

Скрипт `run_tests.bat` автоматически открывает HTML отчёты в браузере после завершения тестов.

---

## 🏗️ Структура Тестов

```
MAGGxDND/
│
├── backend/tests/
│   ├── conftest.py           # Фикстуры pytest
│   ├── test_health.py        # Health check эндпоинты
│   ├── test_session_api.py   # Session REST API тесты
│   ├── test_websocket.py     # WebSocket тесты
│   │
│   ├── unit/                 # Unit тесты
│   │   ├── test_manipulator.py
│   │   └── test_orchestrator.py
│   │
│   └── integration/          # Integration тесты
│       ├── test_session_flow.py
│       └── test_auth_flow.py
│
├── frontend/tests/
│   ├── setup.ts              # Настройка тестов
│   │
│   └── src/
│       ├── components/       # Тесты компонентов
│       │   ├── GameLayout.test.tsx
│       │   └── CharacterPanel.test.tsx
│       ├── services/         # Тесты сервисов
│       │   └── api.test.ts
│       └── store/            # Тесты store
│           └── gameStore.test.ts
│
└── run_tests.bat             # Скрипт запуска всех тестов
```

---

## 🔧 Установка Зависимостей

### Backend
```bash
pip install pytest pytest-asyncio pytest-cov httpx
```

### Frontend
```bash
cd frontend
npm install --legacy-peer-deps
```

---

## 📝 Примеры Тестов

### Backend (Pytest)

```python
# backend/tests/test_health.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_health_live():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"
```

### Frontend (Vitest)

```tsx
// frontend/tests/src/store/gameStore.test.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { useGameStore } from '../../store/gameStore'

describe('gameStore', () => {
  beforeEach(() => {
    useGameStore.setState({ mode: 'menu' })
  })

  it('should update mode', () => {
    useGameStore.getState().setMode('playing')
    expect(useGameStore.getState().mode).toBe('playing')
  })

  it('should set generating state', () => {
    useGameStore.getState().setIsGenerating(true)
    expect(useGameStore.getState().isGenerating).toBe(true)
  })
})
```

---

## 🎯 Маркеры Pytest

```bash
# Запустить только unit тесты
pytest -m unit

# Запустить только integration тесты
pytest -m integration

# Запустить только slow тесты
pytest -m slow

# Исключить slow тесты
pytest -m "not slow"
```

---

## 📈 Покрытие Кода

### Минимальное Покрытие

В `pytest.ini` установлено минимальное покрытие **80%**:

```ini
--cov-min-percentage=80
```

Если покрытие ниже 80%, тесты упадут с ошибкой.

### Отчёт в Терминале

```
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
backend\src\api\routers\session.py       150     15    90%   45-50, 78-82
backend\src\game\session_manager.py      200     40    80%   120-125, 130-135
---------------------------------------------------------------------
TOTAL                                    350     55    84%
```

### HTML Отчёт

Открывает подробный HTML отчёт с подсветкой непокрытого кода:

```bash
start backend\htmlcov\index.html    # Windows
xdg-open backend/htmlcov/index.html # Linux/Mac
```

---

## 🐛 Отладка Тестов

### Backend
```bash
# Запустить с отладочным выводом
pytest -vvv -s

# Запустить один тест с pdb
pytest --pdb tests/test_file.py::test_function
```

### Frontend
```bash
# Запустить в режиме watch
npm run test -- --watch

# Запустить с UI
npm run test:ui
```

---

## 🎛️ Конфигурация

### Backend (pytest.ini)
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --cov=backend.src --cov-report=html -v
```

### Frontend (vitest.config.ts)
```ts
export default {
  test: {
    globals: true,
    environment: 'jsdom',
    coverage: {
      provider: 'v8',
      reporter: ['html', 'json'],
    },
  },
}
```

---

## 📊 CI/CD Интеграция

### GitHub Actions Пример

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Backend Dependencies
        run: pip install -r requirements.txt
      
      - name: Run Backend Tests
        run: pytest --cov=backend.src --cov-report=xml
      
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install Frontend Dependencies
        run: cd frontend && npm install
      
      - name: Run Frontend Tests
        run: cd frontend && npm run test -- --run --coverage
      
      - name: Upload Coverage
        uses: codecov/codecov-action@v3
```

---

## 🎯 Best Practices

1. **Именуйте тесты понятно**: `test_function_should_return_true_when_valid_input`
2. **Используйте фикстуры**: Для переиспользования setup/teardown кода
3. **Тестируйте граничные случаи**: Пустые значения, null, ошибки
4. **Поддерживайте покрытие >80%**: Критичный код должен быть покрыт на 100%
5. **Запускайте тесты локально**: Перед коммитом всегда проверяйте тесты

---

## 📞 Поддержка

Если тесты падают:

1. Проверите зависимости установлены
2. Проверите база данных очищена
3. Проверите сервер не запущен (для integration тестов)
4. Смотрите логи в `backend/logs/` и `frontend/logs/`

---

**🎉 Happy Testing!**
