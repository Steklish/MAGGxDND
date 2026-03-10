"""
Tests for session REST API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from http import HTTPStatus


class TestSessionEndpoints:
    """Test suite for /api/v1/sessions endpoints."""

    def test_create_session_success(self, client: TestClient, sample_session_data: dict):
        """Test successful session creation."""
        response = client.post("/api/v1/sessions", json=sample_session_data)
        
        assert response.status_code == HTTPStatus.CREATED
        data = response.json()
        
        assert "session_id" in data
        assert data["session_name"] == sample_session_data["session_name"]
        assert data["game_mode"] == sample_session_data["game_mode"]
        assert data["status"] == "created"

    def test_create_session_minimal_data(self, client: TestClient):
        """Test session creation with minimal required data."""
        response = client.post(
            "/api/v1/sessions",
            json={"session_name": "Minimal Session"}
        )
        
        assert response.status_code == HTTPStatus.CREATED
        data = response.json()
        assert data["session_name"] == "Minimal Session"

    def test_create_session_invalid_game_mode(self, client: TestClient):
        """Test session creation with invalid game mode."""
        response = client.post(
            "/api/v1/sessions",
            json={
                "session_name": "Invalid Session",
                "game_mode": "INVALID_MODE"
            }
        )
        
        # Should either accept default or validate
        assert response.status_code in [HTTPStatus.CREATED, HTTPStatus.UNPROCESSABLE_ENTITY]

    def test_list_sessions_empty(self, client: TestClient):
        """Test listing sessions when none exist."""
        response = client.get("/api/v1/sessions")
        
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert "sessions" in data
        assert "total" in data

    def test_list_sessions_after_create(self, client: TestClient, sample_session_data: dict):
        """Test listing sessions after creating one."""
        # Create session
        create_response = client.post("/api/v1/sessions", json=sample_session_data)
        assert create_response.status_code == HTTPStatus.CREATED
        
        # List sessions
        list_response = client.get("/api/v1/sessions")
        assert list_response.status_code == HTTPStatus.OK
        
        data = list_response.json()
        assert data["total"] >= 1
        assert any(s["session_name"] == sample_session_data["session_name"] for s in data["sessions"])

    def test_get_session_info(self, client: TestClient, sample_session_data: dict):
        """Test getting session info by ID."""
        # Create session
        create_response = client.post("/api/v1/sessions", json=sample_session_data)
        session_id = create_response.json()["session_id"]
        
        # Get session info
        response = client.get(f"/api/v1/sessions/{session_id}")
        
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["session_id"] == session_id

    def test_get_session_not_found(self, client: TestClient):
        """Test getting non-existent session."""
        response = client.get("/api/v1/sessions/non-existent-id")
        
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_delete_session(self, client: TestClient, sample_session_data: dict):
        """Test deleting a session."""
        # Create session
        create_response = client.post("/api/v1/sessions", json=sample_session_data)
        session_id = create_response.json()["session_id"]
        
        # Delete session
        delete_response = client.delete(f"/api/v1/sessions/{session_id}")
        assert delete_response.status_code == HTTPStatus.NO_CONTENT
        
        # Verify deletion
        get_response = client.get(f"/api/v1/sessions/{session_id}")
        assert get_response.status_code == HTTPStatus.NOT_FOUND

    def test_delete_session_not_found(self, client: TestClient):
        """Test deleting non-existent session."""
        response = client.delete("/api/v1/sessions/non-existent-id")
        
        assert response.status_code == HTTPStatus.NOT_FOUND


class TestPlayerEndpoints:
    """Test suite for player management endpoints."""

    def test_join_session_success(self, client: TestClient, sample_session_data: dict):
        """Test successful player joining."""
        # Create session first
        create_response = client.post("/api/v1/sessions", json=sample_session_data)
        session_id = create_response.json()["session_id"]
        
        # Join session
        join_response = client.post(
            f"/api/v1/sessions/{session_id}/players",
            json={"player_name": "TestPlayer"}
        )
        
        assert join_response.status_code == HTTPStatus.OK
        data = join_response.json()
        assert "player_id" in data
        assert data["player_name"] == "TestPlayer"

    def test_join_session_with_character(self, client: TestClient, sample_session_data: dict):
        """Test joining session with character name."""
        # Create session
        create_response = client.post("/api/v1/sessions", json=sample_session_data)
        session_id = create_response.json()["session_id"]
        
        # Join with character
        join_response = client.post(
            f"/api/v1/sessions/{session_id}/players",
            json={
                "player_name": "TestPlayer",
                "character_name": "MyCharacter"
            }
        )
        
        assert join_response.status_code == HTTPStatus.OK
        data = join_response.json()
        assert data["character_name"] == "MyCharacter"

    def test_get_session_players(self, client: TestClient, sample_session_data: dict):
        """Test getting list of players in session."""
        # Create session
        create_response = client.post("/api/v1/sessions", json=sample_session_data)
        session_id = create_response.json()["session_id"]
        
        # Add players
        client.post(f"/api/v1/sessions/{session_id}/players", json={"player_name": "Player1"})
        client.post(f"/api/v1/sessions/{session_id}/players", json={"player_name": "Player2"})
        
        # Get players
        response = client.get(f"/api/v1/sessions/{session_id}/players")
        
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_leave_session(self, client: TestClient, sample_session_data: dict):
        """Test player leaving session."""
        # Create session and join
        create_response = client.post("/api/v1/sessions", json=sample_session_data)
        session_id = create_response.json()["session_id"]
        
        join_response = client.post(
            f"/api/v1/sessions/{session_id}/players",
            json={"player_name": "TestPlayer"}
        )
        player_id = join_response.json()["player_id"]
        
        # Leave session
        leave_response = client.delete(f"/api/v1/sessions/{session_id}/players/{player_id}")
        
        assert leave_response.status_code == HTTPStatus.NO_CONTENT
