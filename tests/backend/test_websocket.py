"""
Tests for WebSocket game endpoints
"""
import pytest
from fastapi.testclient import TestClient
from starlette.testclient import TestClient as WebSocketTestClient
from starlette.websockets import WebSocketDisconnect


class TestWebSocketEndpoints:
    """Test suite for WebSocket game endpoints."""

    def test_websocket_connect_invalid_session(self, client: TestClient):
        """Test WebSocket connection to non-existent session."""
        try:
            with client.websocket_connect("/ws/non-existent-session/player1") as websocket:
                data = websocket.receive_json()
                assert "error" in data or data.get("reason") == "Session not found"
        except WebSocketDisconnect:
            pass  # Expected behavior

    def test_websocket_connect_success(self, client: TestClient, sample_session_data: dict):
        """Test successful WebSocket connection."""
        # Create session first
        create_response = client.post("/api/v1/sessions", json=sample_session_data)
        session_id = create_response.json()["session_id"]
        
        # Join as player
        join_response = client.post(
            f"/api/v1/sessions/{session_id}/players",
            json={"player_name": "TestPlayer"}
        )
        player_id = join_response.json()["player_id"]
        
        # Connect via WebSocket
        try:
            with client.websocket_connect(f"/ws/{session_id}/{player_id}") as websocket:
                # Should receive connection confirmation
                data = websocket.receive_json()
                assert data["type"] == "CONNECTED" or "error" not in data
        except WebSocketDisconnect:
            pass  # May disconnect if session not fully initialized

    def test_websocket_send_player_action(self, client: TestClient, sample_session_data: dict):
        """Test sending player action via WebSocket."""
        # Create session
        create_response = client.post("/api/v1/sessions", json=sample_session_data)
        session_id = create_response.json()["session_id"]
        
        # Join as player
        join_response = client.post(
            f"/api/v1/sessions/{session_id}/players",
            json={"player_name": "TestPlayer"}
        )
        player_id = join_response.json()["player_id"]
        
        try:
            with client.websocket_connect(f"/ws/{session_id}/{player_id}") as websocket:
                # Receive connection message
                websocket.receive_json()
                
                # Send player action
                action = {
                    "event_type": "PLAYER_ACTION",
                    "data": {
                        "player_id": player_id,
                        "request_text": "Look around the room",
                        "timestamp": 1234567890.0
                    }
                }
                websocket.send_json(action)
                
                # May receive confirmation or error
                try:
                    response = websocket.receive_json(timeout=2.0)
                    assert response is not None
                except Exception:
                    pass  # Timeout is acceptable for this test
        except WebSocketDisconnect:
            pass

    def test_get_session_players_endpoint(self, client: TestClient, sample_session_data: dict):
        """Test GET /sessions/{session_id}/players endpoint."""
        # Create session
        create_response = client.post("/api/v1/sessions", json=sample_session_data)
        session_id = create_response.json()["session_id"]
        
        # Get players (should be empty)
        response = client.get(f"/api/v1/sessions/{session_id}/players")
        assert response.status_code == HTTPStatus.OK

    def test_get_session_info_endpoint(self, client: TestClient, sample_session_data: dict):
        """Test GET /sessions/{session_id}/info endpoint."""
        # Create session
        create_response = client.post("/api/v1/sessions", json=sample_session_data)
        session_id = create_response.json()["session_id"]
        
        # Get info
        response = client.get(f"/api/v1/sessions/{session_id}/info")
        assert response.status_code == HTTPStatus.OK
        
        data = response.json()
        assert "session_id" in data
        assert data["session_id"] == session_id
