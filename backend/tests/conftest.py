"""
Pytest Configuration for MAGGxDND Backend
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.src.database.base import Base, get_db
from backend.src.config import settings
from backend.src.main import app


# Test database configuration
TEST_DATABASE_URL = "sqlite:///./test_maggxdnd.db"


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db(test_engine) -> Generator:
    """Create test database session"""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(test_db) -> Generator[TestClient, None, None]:
    """Create test client with overridden database dependency"""
    
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_user_data() -> dict:
    """Test user data fixture"""
    return {
        'username': 'testuser',
        'password': 'TestPassword123!',
        'email': 'test@example.com'
    }


@pytest.fixture
def test_character_data() -> dict:
    """Test character data fixture"""
    return {
        'name': 'Test Character',
        'race': 'Human',
        'char_class': 'Fighter',
        'level': 1,
        'backstory_summary': 'A brave warrior',
        'max_hp': 30,
        'current_hp': 30,
        'armor_class': 12,
        'stats': {
            'strength': 15,
            'dexterity': 12,
            'constitution': 14,
            'intelligence': 10,
            'wisdom': 10,
            'charisma': 10
        }
    }


@pytest.fixture
def auth_headers(client: TestClient, test_user_data: dict) -> dict:
    """Create authenticated headers for testing"""
    # Register test user
    client.post('/api/v1/auth/register', json=test_user_data)
    
    # Login and get token
    response = client.post(
        '/api/v1/auth/login/json',
        json={
            'username': test_user_data['username'],
            'password': test_user_data['password']
        }
    )
    
    token = response.json()['access_token']
    
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }


# Helper functions for tests
def create_test_user(db, username: str = 'testuser', password: str = 'Test123!'):
    """Helper to create test user"""
    from backend.src.models.user import User
    from backend.src.utils.security import get_password_hash
    
    user = User(
        username=username,
        hashed_password=get_password_hash(password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def cleanup_test_data(db):
    """Cleanup test data after tests"""
    # Delete in reverse order of dependencies
    from backend.src.models.character import CharacterModel
    from backend.src.models.user import User
    
    db.query(CharacterModel).delete()
    db.query(User).delete()
    db.commit()


# Pytest hooks
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    # Auto-mark slow tests
    for item in items:
        if 'slow' in item.nodeid:
            item.add_marker(pytest.mark.slow)
