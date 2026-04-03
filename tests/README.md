# MAGGxDND Test Suite

This folder contains all tests for the MAGGxDND project, organized by type and component.

## 📁 Structure

```
tests/
├── backend/                 # Backend (Python/FastAPI) tests
│   ├── unit/               # Unit tests for backend components
│   │   ├── test_ai_service_logger.py
│   │   └── test_api_logging.py
│   ├── integration/        # Integration tests
│   │   └── test_api_integration.py
│   ├── conftest.py         # Pytest fixtures and configuration
│   ├── pytest.ini          # Pytest configuration
│   ├── test_health.py      # Health check tests
│   ├── test_session_api.py # Session API tests
│   └── test_websocket.py   # WebSocket tests
│
├── frontend/               # Frontend (React/TypeScript) tests
│   ├── components/         # Component tests
│   ├── store/              # State management tests
│   │   └── gameStore.test.ts
│   └── services/           # Service tests
│       └── api.test.ts
│
├── e2e/                    # End-to-End tests
│   ├── test_app.py
│   ├── test_auth.py
│   ├── test_browser_auth.py
│   ├── test_compendium.py
│   ├── test_import.py
│   ├── test_logging.py
│   ├── test_session_fix.py
│   └── test_session_persistence.py
│
└── reports/                # Generated test reports (gitignored)
    ├── backend/            # Backend coverage reports
    │   └── htmlcov/
    └── frontend/           # Frontend coverage reports
        └── htmlcov/
```

## 🚀 Running Tests

### All Tests (with Coverage)

**PowerShell (Windows):**
```powershell
.\run_tests.ps1
```

**CMD (Windows):**
```cmd
run_tests.bat
```

**Bash (Linux/Mac):**
```bash
./run_tests.sh
```

### Backend Tests Only

```bash
# From project root
pytest tests/backend/ --cov=backend.src --cov-report=term-missing -v
```

### Frontend Tests Only

```bash
# From project root
cd frontend
npm run test -- --run
```

### E2E Tests Only

```bash
# From project root
pytest tests/e2e/ -v
```

## 📊 Coverage Reports

After running tests, coverage reports are generated in:

- **Backend:** `tests/reports/backend/htmlcov/index.html`
- **Frontend:** `tests/reports/frontend/htmlcov/index.html`

Open these files in a browser to view detailed coverage information.

## 🧪 Test Types

### Unit Tests (`tests/backend/unit/`)
- Test individual components in isolation
- Fast execution
- No external dependencies

### Integration Tests (`tests/backend/integration/`)
- Test component interactions
- May require database or API
- Slower than unit tests

### E2E Tests (`tests/e2e/`)
- Test complete user flows
- Require running server
- Slowest but most comprehensive

## 📝 Writing Tests

### Backend (Python/pytest)

```python
def test_example():
    """Example test"""
    assert True

@pytest.mark.asyncio
async def test_async_example():
    """Async test"""
    assert True
```

### Frontend (TypeScript/Vitest)

```typescript
import { describe, it, expect } from 'vitest'

describe('Example', () => {
  it('should pass', () => {
    expect(true).toBe(true)
  })
})
```

## 🔧 Configuration

- **Pytest:** `tests/backend/pytest.ini`
- **Vitest:** `frontend/vitest.config.ts`
- **Fixtures:** `tests/backend/conftest.py`

## 📚 Documentation

- [Pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [Testing Best Practices](../../docs/TESTING.md)
