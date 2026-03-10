# Server Tests

Test suite for MAGGxDND FastAPI server.

## Running Tests

```bash
cd server

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_session_api.py

# Run specific test
pytest tests/test_session_api.py::TestSessionEndpoints::test_create_session_success

# Run with coverage
pytest --cov=src --cov-report=html

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

## Test Structure

```
tests/
├── conftest.py           # Pytest fixtures
├── test_health.py        # Health check tests
├── test_session_api.py   # Session REST API tests
├── test_websocket.py     # WebSocket tests
└── ...
```

## Test Categories

- **Unit Tests** (`-m unit`): Test individual functions/classes
- **Integration Tests** (`-m integration`): Test API endpoints
- **WebSocket Tests** (`-m websocket`): Test WebSocket connections
- **API Tests** (`-m api`): Test REST API endpoints

## Fixtures

- `client`: TestClient for making HTTP requests
- `sample_session_data`: Sample session creation data
- `sample_character_data`: Sample character data
- `sample_user_data`: Sample user registration data
- `clean_database`: Database cleanup fixture

## Requirements

```bash
pip install pytest pytest-asyncio pytest-cov httpx
```
