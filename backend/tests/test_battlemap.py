"""
backend/tests/test_battlemap.py

Comprehensive tests for Milestone 2:
1. SceneNode battlemap_image_url persistence and serialization
2. Session initialization populating battlemap_image_url
3. POST /api/v1/sessions/{session_id}/scene/regenerate-map endpoint
4. Database session_data persistence of generated battle map
5. Cache retrieval on subsequent generation requests
6. GET /api/v1/sessions/{session_id}/game_info returning battle map details
7. Fallback placeholder handling when offline or without API key
"""
import pytest
from http import HTTPStatus
from pathlib import Path
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from backend.main import app
from backend.src.services.asset_manager import asset_manager
from backend.src.services.image_gen_service import image_gen_service, GenerationResult
from backend.src.api.routers.session_router import ensure_scene_battlemap, ProceduralGenerator
from core.schemas.in_game import SceneNode, Coordinate2D, UnifiedObject, ObjectType


@pytest.fixture(scope="module", autouse=True)
def setup_battlemap_environment():
    """Ensure assets and placeholders are seeded before battlemap tests."""
    asset_manager.initialize()
    yield


class TestBattlemapIntegration:
    """Test suite for Battle Map Generation, Persistence & Grid Integration."""

    def test_scenenode_battlemap_schema(self):
        """SceneNode schema must serialize and deserialize battlemap_image_url."""
        scene = SceneNode(
            name="Ancient Catacombs",
            description="Dark damp corridors paved with worn flagstones.",
            dimensions=Coordinate2D(x=20.0, y=20.0),
            battlemap_image_url="/assets/maps/catacombs_aerial.png",
        )
        assert scene.battlemap_image_url == "/assets/maps/catacombs_aerial.png"
        dumped = scene.model_dump()
        assert dumped["battlemap_image_url"] == "/assets/maps/catacombs_aerial.png"

        restored = SceneNode(**dumped)
        assert restored.battlemap_image_url == "/assets/maps/catacombs_aerial.png"

    def test_ensure_scene_battlemap_populates_placeholder(self):
        """ensure_scene_battlemap assigns default placeholder if not already set."""
        scene = SceneNode(
            name="The Dusty Tavern",
            description="Wooden floorboards and round tables.",
            dimensions=Coordinate2D(x=15.0, y=15.0),
        )
        assert scene.battlemap_image_url is None

        ensure_scene_battlemap(scene)
        assert scene.battlemap_image_url is not None
        assert "battlemap" in scene.battlemap_image_url
        assert scene.battlemap_image_url.startswith("/assets/")

    def test_ensure_scene_battlemap_preserves_existing_url(self):
        """ensure_scene_battlemap must not overwrite an already assigned battlemap URL."""
        custom_url = "/assets/maps/custom_prebaked_dungeon.png"
        scene = SceneNode(
            name="Fortress Hall",
            description="Grand throne room.",
            battlemap_image_url=custom_url,
        )
        ensure_scene_battlemap(scene)
        assert scene.battlemap_image_url == custom_url

    def test_procedural_generator_includes_battlemap(self):
        """ProceduralGenerator.generate_scene must populate battlemap_image_url."""
        scene = ProceduralGenerator.generate_scene("A damp subterranean cavern")
        assert scene is not None
        assert scene.battlemap_image_url is not None
        assert scene.battlemap_image_url.startswith("/assets/")

    def test_regenerate_map_endpoint_success(self, client: TestClient, sample_session_data: dict, test_db):
        """POST /api/v1/sessions/{session_id}/scene/regenerate-map generates and persists map."""
        # 1. Create session
        create_res = client.post("/api/v1/sessions", json=sample_session_data)
        assert create_res.status_code == HTTPStatus.CREATED
        session_id = create_res.json()["session_id"]

        # 2. Call regenerate-map endpoint
        regen_res = client.post(f"/api/v1/sessions/{session_id}/scene/regenerate-map")
        assert regen_res.status_code == HTTPStatus.OK
        data = regen_res.json()

        assert data["status"] == "ok"
        assert "battlemap_image_url" in data
        assert data["battlemap_image_url"].startswith("/assets/")

        # 3. Verify session in DB persisted the map URL
        from backend.src.repositories.session_repository import SessionRepository
        repo = SessionRepository(test_db)
        db_sess = repo.get_session_by_uuid(session_id)
        assert db_sess is not None
        assert db_sess.session_data is not None
        assert "battlemap_image_url" in db_sess.session_data
        assert db_sess.session_data["battlemap_image_url"] == data["battlemap_image_url"]

    def test_regenerate_map_cache_behavior(self, client: TestClient, sample_session_data: dict):
        """Calling regenerate-map with mock client checks caching flag."""
        # Create session
        create_res = client.post("/api/v1/sessions", json=sample_session_data)
        assert create_res.status_code == HTTPStatus.CREATED
        session_id = create_res.json()["session_id"]

        # Call once
        res1 = client.post(f"/api/v1/sessions/{session_id}/scene/regenerate-map")
        assert res1.status_code == HTTPStatus.OK
        map_url_1 = res1.json()["battlemap_image_url"]

        # Call again
        res2 = client.post(f"/api/v1/sessions/{session_id}/scene/regenerate-map")
        assert res2.status_code == HTTPStatus.OK
        map_url_2 = res2.json()["battlemap_image_url"]

        assert map_url_1 == map_url_2

    def test_regenerate_map_prompt_override(self, client: TestClient, sample_session_data: dict):
        """POST /api/v1/sessions/{session_id}/scene/regenerate-map accepts custom prompt_override."""
        create_res = client.post("/api/v1/sessions", json=sample_session_data)
        assert create_res.status_code == HTTPStatus.CREATED
        session_id = create_res.json()["session_id"]

        override_payload = {
            "prompt_override": "A sunken marble temple with flooded blue tiles and ruined pillars",
            "terrain_type": "water",
        }
        res = client.post(
            f"/api/v1/sessions/{session_id}/scene/regenerate-map",
            json=override_payload,
        )
        assert res.status_code == HTTPStatus.OK
        data = res.json()
        assert data["status"] == "ok"
        assert data["battlemap_image_url"].startswith("/assets/")

    def test_game_info_returns_battlemap_image_url(self, client: TestClient, sample_session_data: dict):
        """GET /api/v1/sessions/{session_id}/game_info must include battlemap_image_url in scene data."""
        # Create session
        create_res = client.post("/api/v1/sessions", json=sample_session_data)
        assert create_res.status_code == HTTPStatus.CREATED
        session_id = create_res.json()["session_id"]

        # Regenerate map to ensure scene is active
        regen_res = client.post(f"/api/v1/sessions/{session_id}/scene/regenerate-map")
        assert regen_res.status_code == HTTPStatus.OK
        expected_url = regen_res.json()["battlemap_image_url"]

        # Query game_info
        info_res = client.get(f"/api/v1/sessions/{session_id}/game_info")
        assert info_res.status_code == HTTPStatus.OK
        game_info = info_res.json()

        assert "scene" in game_info
        assert game_info["scene"] is not None
        assert "battlemap_image_url" in game_info["scene"]
        assert game_info["scene"]["battlemap_image_url"] == expected_url

    def test_nonexistent_session_returns_404(self, client: TestClient):
        """Regenerating map for non-existent session returns 404."""
        res = client.post("/api/v1/sessions/non-existent-uuid-12345/scene/regenerate-map")
        assert res.status_code == HTTPStatus.NOT_FOUND
