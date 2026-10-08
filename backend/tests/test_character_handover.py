import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_session_roster_and_claim_flow():
    # 1. Create a guest token
    guest_resp = client.post("/api/v1/auth/guest", json={"username": "Tester_Alrik"})
    assert guest_resp.status_code == 200
    token = guest_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create a session
    create_resp = client.post(
        "/api/v1/sessions",
        json={
            "session_name": "Handover Test Realm",
            "scene_prompt": "An echoing vaulted stone chamber with torches.",
        },
        headers=headers
    )
    assert create_resp.status_code in (200, 201)
    session_data = create_resp.json()
    session_id = session_data["session_id"]
    assert session_id

    # 3. Join with character Valeros
    join_resp = client.post(
        f"/api/v1/sessions/{session_id}/players",
        json={
            "player_name": "Tester_Alrik",
            "character_name": "Valeros",
            "character_prompt": "Level 1 Fighter"
        },
        headers=headers
    )
    assert join_resp.status_code == 200
    player_id = join_resp.json()["player_id"]

    # 4. Check roster BEFORE websocket connection: player is offline -> character is AI-controlled & claimable
    roster_offline = client.get(f"/api/v1/sessions/{session_id}/roster").json()
    valeros_offline = next((c for c in roster_offline if c["name"] == "Valeros"), None)
    assert valeros_offline is not None
    assert valeros_offline["is_occupied"] is False
    assert valeros_offline["is_ai_controlled"] is True
    assert valeros_offline["can_claim"] is True

    # 5. Connect via WebSocket: player is online -> character is occupied & player-controlled
    with client.websocket_connect(f"/ws/{session_id}/{player_id}") as ws:
        roster_online = client.get(f"/api/v1/sessions/{session_id}/roster").json()
        valeros_online = next((c for c in roster_online if c["name"] == "Valeros"), None)
        assert valeros_online is not None
        assert valeros_online["is_occupied"] is True
        assert valeros_online["is_ai_controlled"] is False
        assert valeros_online["can_claim"] is False

    import time
    time.sleep(0.3)

    # 6. After disconnect: character is handed back to AI companion
    roster_after_disc = client.get(f"/api/v1/sessions/{session_id}/roster").json()
    valeros_disc = next((c for c in roster_after_disc if c["name"] == "Valeros"), None)
    print("\n*** VALEROS DISC ***", valeros_disc)
    assert valeros_disc is not None
    assert valeros_disc["is_occupied"] is False
    assert valeros_disc["is_ai_controlled"] is True
    assert valeros_disc["can_claim"] is True

    # 7. Another player claims Valeros from AI
    claimer_guest = client.post("/api/v1/auth/guest", json={"username": "Tester_Claimer"}).json()
    claimer_headers = {"Authorization": f"Bearer {claimer_guest['access_token']}"}
    claim_resp = client.post(
        f"/api/v1/sessions/{session_id}/claim-character",
        json={"character_name": "Valeros", "player_name": "Tester_Claimer"},
        headers=claimer_headers
    )
    assert claim_resp.status_code == 200
    claimed_player_id = claim_resp.json()["player_id"]

    # 8. New player connects via WebSocket -> character is occupied by Tester_Claimer
    with client.websocket_connect(f"/ws/{session_id}/{claimed_player_id}") as ws:
        roster_claimed = client.get(f"/api/v1/sessions/{session_id}/roster").json()
        valeros_claimed = next((c for c in roster_claimed if c["name"] == "Valeros"), None)
        assert valeros_claimed is not None
        assert valeros_claimed["is_occupied"] is True
        assert valeros_claimed["is_ai_controlled"] is False
        assert valeros_claimed["controller_name"] == "Tester_Claimer"
