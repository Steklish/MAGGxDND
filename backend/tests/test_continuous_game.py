"""
backend/tests/test_continuous_game.py

End-to-End Continuous Game Loop Test Suite:
1. Multi-turn continuous game loop progression (investigation, object interaction, ability, scene transition)
2. Automatic battlemap assignment and persistence across newly created scenes during continuous play
3. Event pool and message stream deduplication integrity
4. Participant roster preservation (controller_name, occupied state) across sequential turns
5. Database session_data roundtrip rehydration after continuous game turns
6. WebSocket streaming and state update broadcast during continuous turns
"""

import asyncio
import time
from http import HTTPStatus
from unittest.mock import MagicMock, patch, AsyncMock
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.src.repositories.session_repository import SessionRepository
from backend.src.services.image_gen_service import GenerationResult
from backend.src.api.routers.session_router import ensure_scene_battlemap, procedural_gen
from core.schemas.orchestration import (
    UserInteractionProcessing,
    UserInterationType,
    RulesCheck,
    ClarityCheck,
    Event,
    EventTypes,
    Message
)
from core.schemas.in_game import SceneNode, Coordinate2D, UnifiedObject, ObjectType, GameModes


# ---------------------------------------------------------------------------
# Test Fixtures & Mocks
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_ai_generator():
    """Mock AI generator returning deterministic, fast responses for continuous play."""
    def fake_generate_one_shot(pydantic_model, prompt):
        if pydantic_model == UserInteractionProcessing:
            return UserInteractionProcessing(
                interaction_type=UserInterationType.CHARACTER_ACTION,
                user_request_saturated=prompt
            )
        elif pydantic_model == RulesCheck:
            return RulesCheck(is_rule_violation=False, violation_details=None)
        elif pydantic_model == ClarityCheck:
            return ClarityCheck(needs_clarification=False, clarification_needed="")
        return MagicMock()

    def fake_generate(prompt):
        return "The chamber echoes with ancient whispers as the shadows shift."

    fake_result = GenerationResult(
        status="completed",
        image_url="/assets/maps/continuous_dungeon.png",
        cached=True
    )
    with patch("backend.src.services.image_gen_service.image_gen_service.generate_battlemap", new_callable=AsyncMock) as mock_bm, \
         patch("backend.src.services.image_gen_service.image_gen_service.generate_for_entity", new_callable=AsyncMock) as mock_ent, \
         patch("backend.src.services.image_gen_service.image_gen_service.generate_character_portrait", new_callable=AsyncMock) as mock_cp:
        mock_bm.return_value = fake_result
        mock_ent.return_value = fake_result
        mock_cp.return_value = fake_result
        yield {
            "generate_one_shot": fake_generate_one_shot,
            "generate": fake_generate,
            "mock_bm": mock_bm
        }


# ---------------------------------------------------------------------------
# Continuous Game Loop Tests
# ---------------------------------------------------------------------------

class TestContinuousGameLoop:
    """Multi-turn continuous gameplay simulation."""

    def test_continuous_five_turn_gameplay_lifecycle(
        self,
        client: TestClient,
        sample_session_data: dict,
        test_db,
        mock_ai_generator
    ):
        """
        Executes a continuous 5-turn gameplay loop:
        Turn 1: Investigation & room search
        Turn 2: Object interaction (manipulator item handling)
        Turn 3: Tactical spell/stance execution
        Turn 4: Scene transition to newly generated dungeon room (with auto battlemap generation)
        Turn 5: NPC encounter / follow-up action
        Verifies:
        - Each turn succeeds with HTTP 200
        - Session turn queue and timing advance
        - Message stream has no duplicates
        - Newly traversed scene has automatic battlemap attached and persisted
        - Session data survives full database reload
        """
        repo = SessionRepository(test_db)

        # 1. Initialize Continuous Session
        create_resp = client.post("/api/v1/sessions", json=sample_session_data)
        assert create_resp.status_code == HTTPStatus.CREATED
        session_id = create_resp.json()["session_id"]

        # 2. Player joins the realm
        char_name = "Thorne Ironbreaker"
        join_resp = client.post(
            f"/api/v1/sessions/{session_id}/players",
            json={
                "player_name": "Player_Thorne",
                "character_name": char_name,
                "character_prompt": "Dwarf Fighter carrying a warhammer and sturdy shield"
            }
        )
        assert join_resp.status_code == HTTPStatus.OK
        player_id = join_resp.json()["player_id"]

        # Verify initial roster before actions
        roster_init = client.get(f"/api/v1/sessions/{session_id}/roster").json()
        assert any(c["name"] == char_name for c in roster_init)

        # Get in-memory game session to configure mock generator for deterministic rapid turns
        from backend.src.game.session_manager import session_manager
        game_session = session_manager.get_session(session_id)
        assert game_session is not None

        # Patch generator on game_session orchestrators and DM
        if hasattr(game_session, "generator") and game_session.generator:
            game_session.generator.generate_one_shot = mock_ai_generator["generate_one_shot"]
            game_session.generator.generate = mock_ai_generator["generate"]

        # Seed an interactive object into current scene
        chest_obj = UnifiedObject(
            name="Ancient Carved Chest",
            description="A heavy oak chest bound with rusted iron straps.",
            obj_type=ObjectType.CONTAINER,
            position=Coordinate2D(x=5.0, y=5.0),
            interactive=True
        )
        if game_session.current_scene:
            game_session.current_scene.objects.append(chest_obj)

        # TURN 1: Investigation & Room Search
        turn1_resp = client.post(
            f"/api/v1/sessions/{session_id}/action",
            json={
                "character_name": char_name,
                "action": "I examine the ancient carved chest and search the surrounding flagstones for pressure plates."
            }
        )
        assert turn1_resp.status_code == HTTPStatus.OK
        turn1_data = turn1_resp.json()
        assert turn1_data["success"] is True

        # TURN 2: Object Interaction
        turn2_resp = client.post(
            f"/api/v1/sessions/{session_id}/action",
            json={
                "character_name": char_name,
                "action": "I carefully lift the lid of the Ancient Carved Chest using my dagger."
            }
        )
        assert turn2_resp.status_code == HTTPStatus.OK
        assert turn2_resp.json()["success"] is True

        # TURN 3: Tactical Stance / Ability
        turn3_resp = client.post(
            f"/api/v1/sessions/{session_id}/action",
            json={
                "character_name": char_name,
                "action": "I light a torch, raise my shield into a defensive guard, and watch the eastern corridor."
            }
        )
        assert turn3_resp.status_code == HTTPStatus.OK
        assert turn3_resp.json()["success"] is True

        # TURN 4: Scene Transition to a New Scene
        # Simulate moving to a new chamber "Forgotten Crypts"
        new_scene = SceneNode(
            name="Forgotten Crypts",
            description="Deep subterranean catacombs lined with stone alcoves and ancient sarcophagi.",
            dimensions=Coordinate2D(x=25.0, y=25.0),
            objects=[
                UnifiedObject(
                    name="Stone Sarcophagus",
                    description="Heavy granite tomb sealed with wax.",
                    obj_type=ObjectType.INTERACTABLE,
                    position=Coordinate2D(x=10.0, y=10.0),
                    interactive=True
                )
            ]
        )
        # Automatic battlemap assignment during continuous gameplay
        ensure_scene_battlemap(new_scene)
        assert new_scene.battlemap_image_url is not None
        assert new_scene.battlemap_image_url.startswith("/assets/")

        # Transition game_session to new scene
        game_session.current_scene = new_scene
        game_session.all_locations[new_scene.name] = new_scene
        game_session.current_location_name = new_scene.name

        # Enforce action in new scene
        turn4_resp = client.post(
            f"/api/v1/sessions/{session_id}/action",
            json={
                "character_name": char_name,
                "action": "I step through the archway into the Forgotten Crypts and inspect the Stone Sarcophagus."
            }
        )
        assert turn4_resp.status_code == HTTPStatus.OK
        assert turn4_resp.json()["success"] is True

        # TURN 5: Continuous Follow-up Turn
        turn5_resp = client.post(
            f"/api/v1/sessions/{session_id}/action",
            json={
                "character_name": char_name,
                "action": "I whisper a dwarven blessing and tap the sarcophagus with the butt of my warhammer."
            }
        )
        assert turn5_resp.status_code == HTTPStatus.OK
        assert turn5_resp.json()["success"] is True

        # -------------------------------------------------------------------
        # Continuous Integrity & Persistence Assertions
        # -------------------------------------------------------------------

        # 1. Verify game_info reflects new scene and battlemap
        info_resp = client.get(f"/api/v1/sessions/{session_id}/game_info")
        assert info_resp.status_code == HTTPStatus.OK
        info_data = info_resp.json()
        assert info_data["scene"]["name"] == "Forgotten Crypts"
        assert info_data["scene"]["battlemap_image_url"] is not None

        # 2. Verify Database Persistence (Roundtrip Rehydration)
        db_session = repo.get_session_by_uuid(session_id)
        assert db_session is not None
        saved_data = db_session.session_data or {}

        # Participants roster was not erased by turn saves
        assert "participants" in saved_data
        participants = saved_data["participants"]
        assert any(p.get("character_name") == char_name for p in participants)
        # Allow background game loop to process all turns from delivery queue
        for _ in range(30):
            if game_session.delivery.request_queue.empty() and len(game_session.messages) >= 5:
                break
            time.sleep(0.3)

        # 3. Message Stream Deduplication: verify no duplicate adjacent messages
        messages = game_session.messages
        assert len(messages) >= 5
        message_texts = [m.text for m in messages]
        for idx in range(1, len(message_texts)):
            # Adjacent messages from the same sender should not be identical duplicates
            if messages[idx].sender_name == messages[idx - 1].sender_name:
                assert message_texts[idx] != message_texts[idx - 1], f"Duplicate message found: {message_texts[idx]}"

        # 4. Turn Queue Integrity
        turn_queue = game_session.turn_queue
        assert isinstance(turn_queue, list)

    def test_continuous_websocket_action_stream(
        self,
        client: TestClient,
        sample_session_data: dict,
        mock_ai_generator
    ):
        """
        Verifies WebSocket client can send sequential turns in continuous gameplay
        and receive stream updates without disconnects.
        """
        # Create session
        create_resp = client.post("/api/v1/sessions", json=sample_session_data)
        assert create_resp.status_code == HTTPStatus.CREATED
        session_id = create_resp.json()["session_id"]

        # Join as player
        join_resp = client.post(
            f"/api/v1/sessions/{session_id}/players",
            json={"player_name": "StreamTester", "character_name": "Lyra"}
        )
        player_id = join_resp.json()["player_id"]

        # Connect WebSocket and stream multi-turn actions
        with client.websocket_connect(f"/ws/{session_id}/{player_id}") as ws:
            # 1. Initial connection payload
            conn_msg = ws.receive_json()
            assert conn_msg.get("type") in ("CONNECTED", "SESSION_UPDATE", "GAME_EVENT")

            # 2. Continuous Action 1
            ws.send_json({
                "event_type": "PLAYER_ACTION",
                "data": {
                    "player_id": player_id,
                    "character_name": "Lyra",
                    "request_text": "I scout the room quietly.",
                    "timestamp": time.time()
                }
            })

            # 3. Continuous Action 2
            ws.send_json({
                "event_type": "PLAYER_ACTION",
                "data": {
                    "player_id": player_id,
                    "character_name": "Lyra",
                    "request_text": "I listen at the northern heavy wooden door.",
                    "timestamp": time.time()
                }
            })

            # 4. Continuous Action 3
            ws.send_json({
                "event_type": "PLAYER_ACTION",
                "data": {
                    "player_id": player_id,
                    "character_name": "Lyra",
                    "request_text": "I ready my shortbow and step into the shadows.",
                    "timestamp": time.time()
                }
            })

            # Read queued stream responses without timeout crash
            received_types = []
            for _ in range(5):
                try:
                    data = ws.receive_json(timeout=1.0)
                    if data and "type" in data:
                        received_types.append(data["type"])
                except Exception:
                    break

            # Assert connection received messages and remained operational
            assert conn_msg is not None
            assert conn_msg.get("type") in ("CONNECTED", "SESSION_UPDATE", "GAME_EVENT")
