"""
Pytest fixtures for server tests
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from fastapi import FastAPI

from backend.main import app


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create test client for API testing."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_session_data() -> dict:
    """Sample session creation data."""
    return {
        "session_name": "Test Session",
        "game_mode": "STORY",
        "max_players": 5,
        "description": "Test session for unit tests",
        "scene_prompt": "A cozy tavern with warm fire",
        "character_prompts": ["A brave warrior", "A wise wizard"],
        "npc_prompts": ["A mysterious stranger"],
    }


@pytest.fixture
def sample_character_data() -> dict:
    """Sample character creation data."""
    return {
        "name": "Test Character",
        "race": "Human",
        "char_class": "Fighter",
        "level": 1,
        "backstory": "A brave adventurer",
    }


@pytest.fixture
def sample_user_data() -> dict:
    """Sample user registration data."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
    }


@pytest.fixture(scope="function")
def clean_database() -> None:
    """Clean database before each test."""
    # TODO: Implement database cleanup
    yield
    # TODO: Cleanup after test
