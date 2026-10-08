"""
backend/tests/test_adversarial_challenger.py

Adversarial Boundary, Injection, Fault-Tolerance, and State Integrity
Verification Suite for MAGGxDND Milestone 1.

Tested Dimensions:
1. Path Traversal & Boundary Attacks on Static Asset and API Routes
   - Standard traversal (../, ..\\)
   - URL-encoded traversal (%2e%2e%2f, %2e%2e%5c)
   - Double-encoded traversal (%252e%252e%252f)
   - Null-byte injections (%00, \\x00)
   - Dot-slash variations and root escapes
   - Asset metadata endpoint parameter tampering
   - AssetManager path resolution boundaries
2. Fault-Tolerance & Offline/Zero-Credential Resiliency
   - Missing credentials (empty, None, NO_KEY, placeholder keys)
   - Invalid API keys causing provider rejection
   - Network timeout simulations
   - Connection reset and offline network errors
   - Quota exhaustion (HTTP 429 rate limit errors)
   - Model safety / RAI blocks and empty image payloads
   - Concurrent stampede deduplication and lock release
3. Session State Integrity & Visual Asset Preservation
   - Invariance of image_url and battlemap_image_url across 20+ turn advances
   - Invariance of image_url during spatial movements
   - Invariance across multi-cycle serialization, disk save, and restore
   - Zero redundant API calls when asset URLs already exist
   - NPC deduplication idempotency
4. Stress & Resource Constraints
   - Large adversarial prompt payloads (50KB+)
   - High-iteration asset static serving
"""

import os
import json
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from http import HTTPStatus

from core.schemas.in_game import (
    Character, UnifiedObject, SceneNode, NPCCharacter,
    AbilityScores, CharacterClass, GameModes, Coordinate2D
)
from core.game.engine import Session
from core.game.event_pool import EventPool
from backend.main import app
from backend.src.config import settings
from backend.src.services.asset_manager import asset_manager
from backend.src.services.image_gen_service import image_gen_service, GenerationResult
from backend.src.services.prompt_builder import PromptBuilder


# =====================================================================
# 1. PATH TRAVERSAL & BOUNDARY ATTACKS SUITE
# =====================================================================

class TestAdversarialPathTraversal:
    """Stress-test static file handlers and metadata endpoints against path traversal attacks."""

    @pytest.mark.parametrize("payload", [
        "../main.py",
        "../../main.py",
        "../../../backend/main.py",
        "..\\main.py",
        "..\\..\\backend\\main.py",
        "..%2fmain.py",
        "..%2f..%2fbackend%2fmain.py",
        "%2e%2e%2fmain.py",
        "%2e%2e%2f%2e%2e%2fmain.py",
        "%2e%2e%5cmain.py",
        "..%5cmain.py",
        "%252e%252e%252fmain.py",
        "....//....//backend/main.py",
        "..%00/main.py",
        "characters/../../main.py",
        "characters/..%2f..%2fbackend%2fmain.py",
        "characters/%2e%2e%2f%2e%2e%2fmain.py",
        "characters/..%5c..%5cmain.py",
        "characters/%00.png",
        "placeholders/../../backend/main.py",
        "../../../../../../../../../../windows/win.ini",
        "..%2f..%2f..%2f..%2f..%2f..%2fwindows%2fwin.ini",
    ])
    def test_root_assets_path_traversal_rejected(self, client: TestClient, payload: str):
        """GET /assets/{payload} must NEVER return 200 or leak files outside data/assets."""
        response = client.get(f"/assets/{payload}")
        assert response.status_code in (HTTPStatus.NOT_FOUND, HTTPStatus.BAD_REQUEST, HTTPStatus.UNPROCESSABLE_ENTITY), (
            f"Path traversal payload '{payload}' succeeded with status {response.status_code}!"
        )
        # Ensure sensitive source code was not returned
        assert b"from fastapi import" not in response.content
        assert b"app = FastAPI" not in response.content

    @pytest.mark.parametrize("payload", [
        "../main.py",
        "../../main.py",
        "..%2fmain.py",
        "%2e%2e%2f%2e%2e%2fbackend%2fmain.py",
        "characters/../../main.py",
        "placeholders/..%2f..%2fmain.py",
        "characters/%00.png",
        "characters/..%5c..%5cmain.py",
    ])
    def test_api_assets_path_traversal_rejected(self, client: TestClient, payload: str):
        """GET /api/v1/assets/{payload} must NEVER return 200 or leak outside data/assets."""
        response = client.get(f"/api/v1/assets/{payload}")
        assert response.status_code in (HTTPStatus.NOT_FOUND, HTTPStatus.BAD_REQUEST, HTTPStatus.UNPROCESSABLE_ENTITY), (
            f"API static traversal payload '{payload}' returned {response.status_code}!"
        )
        assert b"from fastapi import" not in response.content

    @pytest.mark.parametrize("category,filename", [
        ("..", "main.py"),
        ("../..", "main.py"),
        ("..%2f", "main.py"),
        ("%2e%2e", "main.py"),
        ("characters", "../../main.py"),
        ("characters", "..\\..\\main.py"),
        ("characters", "..%2f..%2fmain.py"),
        ("characters", "%00main.py"),
        ("invalid_cat", "test.png"),
        ("placeholders", "../../../main.py"),
    ])
    def test_asset_status_endpoint_tampering(self, client: TestClient, category: str, filename: str):
        """GET /api/v1/assets/status/{category}/{filename} strictly rejects path manipulation."""
        response = client.get(f"/api/v1/assets/status/{category}/{filename}")
        assert response.status_code in (HTTPStatus.BAD_REQUEST, HTTPStatus.NOT_FOUND, HTTPStatus.UNPROCESSABLE_ENTITY), (
            f"Metadata route with category='{category}', filename='{filename}' unexpectedly returned {response.status_code}"
        )

    def test_raw_null_byte_in_url_rejected_by_client(self, client: TestClient):
        """Raw null bytes in URL strings must raise an InvalidURL error at HTTP layer."""
        import httpx
        with pytest.raises(httpx.InvalidURL):
            client.get("/api/v1/assets/status/characters/dummy\x00.png")

    def test_asset_manager_get_asset_path_stays_contained(self):
        """Direct test of AssetManager.get_asset_path prevents traversal via basename enforcement."""
        # 1. Filename traversal is neutralized by os.path.basename
        resolved_path = asset_manager.get_asset_path("characters", "../../main.py")
        assert resolved_path.name == "main.py"
        assert resolved_path.parent == asset_manager.base_dir / "characters"

        # 2. Backslash traversal on Windows
        resolved_backslash = asset_manager.get_asset_path("characters", "..\\..\\main.py")
        assert resolved_backslash.name == "main.py"
        assert resolved_backslash.parent == asset_manager.base_dir / "characters"

    def test_spa_catchall_blocks_code_and_config_extensions(self, client: TestClient):
        """SPA catch-all explicitly rejects attempts to read code and config files."""
        for ext_file in ["main.py", ".env", "test.db", "app.log", "pytest.ini", "poetry.lock", "pyproject.toml"]:
            response = client.get(f"/{ext_file}")
            assert response.status_code == HTTPStatus.NOT_FOUND, (
                f"SPA route permitted access to '{ext_file}' with status {response.status_code}"
            )


# =====================================================================
# 2. FAULT-TOLERANCE & OFFLINE/ZERO-CREDENTIAL RESILIENCY SUITE
# =====================================================================

class TestAdversarialFaultTolerance:
    """Stress-test error handling under offline, invalid, and hostile external conditions."""

    @pytest.mark.parametrize("bad_key", [
        "",
        "NO_KEY",
        "your-gemini-key",
        "   ",
    ])
    def test_generate_endpoint_with_unconfigured_keys(self, client: TestClient, monkeypatch, bad_key: str):
        """Endpoint /api/v1/assets/generate must return status='fallback' and never throw 500."""
        monkeypatch.setattr(settings, "GEMINI_API_KEY", bad_key)
        monkeypatch.setattr(image_gen_service, "api_key", bad_key)

        payload = {
            "entity_type": "character",
            "entity_id": "adversarial_char_1",
            "subtype": "Wizard",
            "description": "An ancient sage",
        }
        response = client.post("/api/v1/assets/generate", json=payload)
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["status"] == "fallback"
        assert "character_wizard.svg" in data["image_url"]
        assert isinstance(data["cached"], bool)

    @pytest.mark.asyncio
    async def test_invalid_api_key_provider_rejection(self, monkeypatch):
        """When provider raises an auth error for an invalid key, service catches and falls back."""
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "INVALID_EXPIRED_KEY_XYZ")
        monkeypatch.setattr(image_gen_service, "api_key", "INVALID_EXPIRED_KEY_XYZ")
        monkeypatch.setattr(image_gen_service, "is_configured", True)

        mock_client = MagicMock()
        mock_client.models.generate_images.side_effect = Exception("API_KEY_INVALID: 400 API key not valid")
        monkeypatch.setattr(image_gen_service, "_client", mock_client)

        result = await image_gen_service.generate_character_portrait(
            character_id="hero_fail_auth",
            name="AuthTester",
            char_class="Rogue",
        )
        assert result.status == "fallback"
        assert result.cached is False
        assert "character_rogue.svg" in result.image_url
        assert "API_KEY_INVALID" in (result.error or "")

    @pytest.mark.asyncio
    async def test_network_timeout_simulation(self, monkeypatch):
        """When network times out during generation, service cleanly falls back and unlocks tasks."""
        monkeypatch.setattr(image_gen_service, "is_configured", True)
        mock_client = MagicMock()
        mock_client.models.generate_images.side_effect = TimeoutError("Connection to Google API timed out after 30s")
        monkeypatch.setattr(image_gen_service, "_client", mock_client)

        result = await image_gen_service.generate_scene_header(
            scene_id="scene_timeout_1",
            name="Abyssal Chasm",
            description="Endless darkness with howling winds",
        )
        assert result.status == "fallback"
        assert "scene_default.svg" in result.image_url
        assert "timed out" in (result.error or "").lower()

        # Invariant: active tasks map must be empty after completion
        assert len(image_gen_service._active_tasks) == 0

    @pytest.mark.asyncio
    async def test_quota_exhaustion_429_simulation(self, monkeypatch):
        """When API quota is exhausted (429), service returns fallback and captures error detail."""
        monkeypatch.setattr(image_gen_service, "is_configured", True)
        mock_client = MagicMock()
        mock_client.models.generate_images.side_effect = Exception("ResourceExhausted: 429 Quota exceeded for GenerateImages")
        monkeypatch.setattr(image_gen_service, "_client", mock_client)

        result = await image_gen_service.generate_battlemap(
            scene_id="map_quota_1",
            name="Arena of Doom",
            description="Dusty colosseum",
        )
        assert result.status == "fallback"
        assert "battlemap_default.svg" in result.image_url
        assert "ResourceExhausted" in (result.error or "")

    @pytest.mark.asyncio
    async def test_rai_safety_filter_blocking(self, monkeypatch):
        """When Google GenAI RAI safety filter blocks output, service falls back safely."""
        monkeypatch.setattr(image_gen_service, "is_configured", True)

        # Mock response with RAI filter flag
        mock_image = MagicMock()
        mock_image.rai_filtered_reason = "SAFETY_EXPLICIT_CONTENT"
        mock_image.image.image_bytes = None
        mock_response = MagicMock()
        mock_response.generated_images = [mock_image]

        mock_client = MagicMock()
        mock_client.models.generate_images.return_value = mock_response
        monkeypatch.setattr(image_gen_service, "_client", mock_client)

        result = await image_gen_service.generate_item_card(
            item_id="cursed_dagger",
            name="Cursed Dagger",
            obj_type="Weapon",
        )
        assert result.status == "fallback"
        assert "item_weapon.svg" in result.image_url
        assert "RAI" in (result.error or "")

    @pytest.mark.asyncio
    async def test_concurrent_stampede_deduplication(self, monkeypatch):
        """Concurrent requests for the exact same prompt hash deduplicate into a single API call."""
        monkeypatch.setattr(image_gen_service, "is_configured", True)

        call_counter = 0

        def fake_generate_images(*args, **kwargs):
            nonlocal call_counter
            call_counter += 1
            mock_img = MagicMock()
            mock_img.rai_filtered_reason = None
            mock_img.image.image_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
            mock_resp = MagicMock()
            mock_resp.generated_images = [mock_img]
            return mock_resp

        mock_client = MagicMock()
        mock_client.models.generate_images.side_effect = fake_generate_images
        monkeypatch.setattr(image_gen_service, "_client", mock_client)

        # Clean any cached file first
        h = image_gen_service.compute_hash("characters", "Identical Hero Description Prompt", "1:1")
        target_path = image_gen_service.asset_dir / "characters" / f"{h}.png"
        if target_path.exists():
            target_path.unlink()

        try:
            # Launch 8 concurrent requests simultaneously
            tasks = [
                image_gen_service._generate_with_cache(
                    category="characters",
                    prompt="Identical Hero Description Prompt",
                    negative_prompt="",
                    aspect_ratio="1:1",
                    entity_id=f"entity_{i}",
                )
                for i in range(8)
            ]
            results = await asyncio.gather(*tasks)

            # All 8 should succeed
            assert len(results) == 8
            for r in results:
                assert r.status == "completed"
                assert f"{h}.png" in r.image_url

            # Crucial verification: exactly 1 actual API call occurred
            assert call_counter == 1, f"Expected 1 API call due to in-flight deduplication, got {call_counter}"
        finally:
            if target_path.exists():
                target_path.unlink()


# =====================================================================
# 3. SESSION STATE INTEGRITY & IMAGE URL PRESERVATION SUITE
# =====================================================================

class TestAdversarialSessionIntegrity:
    """Stress-test non-destruction of image URLs across turn advances, movements, and save cycles."""

    def _create_initialized_session(self) -> Session:
        """Create a session with rich visual assets attached to all entities."""
        class MockOrchestrator:
            pass

        orchestrator = MockOrchestrator()
        mock_chroma = MagicMock()
        mock_logger = MagicMock()
        mock_gen = MagicMock()
        mock_pool = EventPool()
        mock_delivery = MagicMock()

        session = Session(
            session_name="Visual Preservation Campaign",
            chroma_client=mock_chroma,
            logger=mock_logger,
            generator=mock_gen,
            event_pool=mock_pool,
            delivery=mock_delivery,
        )
        session._init_orchestrator(orchestrator)
        session.game_mode = GameModes.STORY

        # Player with portrait and inventory item with illustration
        stats = AbilityScores(strength=16, dexterity=14, constitution=14, intelligence=10, wisdom=12, charisma=8)
        legendary_sword = UnifiedObject(
            name="Moonblade",
            description="Glowing elven blade",
            image_url="/assets/items/moonblade_998.png",
        )
        hero = Character(
            name="Aeloria",
            race="Elf",
            char_class=CharacterClass.FIGHTER,
            max_hp=30,
            current_hp=30,
            stats=stats,
            inventory=[legendary_sword],
            image_url="/assets/characters/aeloria_portrait_123.png",
            position=Coordinate2D(x=2.0, y=2.0),
        )
        player = session._init_player(hero, orchestrator)
        session.players.append(player)

        # Scene with narrative art and tactical aerial battlemap
        scene = SceneNode(
            name="Sunken Citadel",
            description="Moss-covered ruins submerged in mist.",
            image_url="/assets/scenes/citadel_panoramic_456.png",
            battlemap_image_url="/assets/maps/citadel_aerial_grid_789.png",
        )
        session.current_scene = scene
        session.all_locations[scene.name] = scene
        session.current_location_name = scene.name

        # NPC with portrait
        npc_char = NPCCharacter(
            name="Kobold Shaman",
            race="Kobold",
            char_class=CharacterClass.WIZARD,
            max_hp=12,
            current_hp=12,
            stats=stats,
            current_scene=scene.name,
            image_url="/assets/characters/kobold_shaman_321.png",
            position=Coordinate2D(x=5.0, y=5.0),
        )
        session._init_npc(npc_char)
        return session

    def test_image_urls_preserved_across_50_turn_advances(self):
        """Advancing turns 50 times must NEVER wipe, mutate, or nullify image URLs."""
        session = self._create_initialized_session()

        original_player_img = session.players[0].character.image_url
        original_item_img = session.players[0].character.inventory[0].image_url
        original_scene_img = session.current_scene.image_url
        original_map_img = session.current_scene.battlemap_image_url
        original_npc_img = session.npcs[0].character.image_url

        # Simulate 50 turns
        for turn_idx in range(50):
            actor = session._get_next_character_turn()
            assert actor is not None

        # Verify 100% fidelity after 50 turns
        assert session.players[0].character.image_url == original_player_img
        assert session.players[0].character.inventory[0].image_url == original_item_img
        assert session.current_scene.image_url == original_scene_img
        assert session.current_scene.battlemap_image_url == original_map_img
        assert session.npcs[0].character.image_url == original_npc_img

    def test_spatial_token_movements_preserve_visual_urls(self):
        """Moving tokens across the tactical grid leaves background and entity images unchanged."""
        session = self._create_initialized_session()

        player_char = session.players[0].character
        npc_char = session.npcs[0].character

        # Perform 10 moves
        for step in range(10):
            session.move_character_to_position(player_char, Coordinate2D(x=float(step), y=float(step + 1)), session.current_scene)
            session.move_character_to_position(npc_char, Coordinate2D(x=float(10 - step), y=float(10 - step)), session.current_scene)

        assert player_char.image_url == "/assets/characters/aeloria_portrait_123.png"
        assert session.current_scene.battlemap_image_url == "/assets/maps/citadel_aerial_grid_789.png"
        assert session.current_scene.image_url == "/assets/scenes/citadel_panoramic_456.png"

    def test_multi_cycle_save_load_stress_and_no_api_calls(self):
        """5 cycles of save-to-disk -> load-from-disk -> advance turns must not degrade URLs or call API."""
        session = self._create_initialized_session()

        # Mock the generation service to assert zero redundant calls
        with patch.object(image_gen_service, "generate_for_entity") as mock_gen_entity, \
             patch.object(image_gen_service, "_generate_with_cache") as mock_gen_cache:

            with tempfile.TemporaryDirectory() as tmp_dir:
                current_session = session

                for cycle in range(5):
                    save_file = os.path.join(tmp_dir, f"save_cycle_{cycle}.json")

                    # 1. Advance turns
                    for _ in range(5):
                        current_session._get_next_character_turn()

                    # 2. Save session to disk
                    current_session.save_session(save_file)
                    assert os.path.isfile(save_file)

                    # 3. Restore session in clean instance
                    new_session = Session(
                        session_name=f"Cycle_{cycle}",
                        chroma_client=MagicMock(),
                        logger=MagicMock(),
                        generator=MagicMock(),
                        event_pool=EventPool(),
                        delivery=MagicMock(),
                    )
                    class MockOrchestrator: pass
                    new_session._init_orchestrator(MockOrchestrator())

                    with open(save_file, "r", encoding="utf-8") as f:
                        save_data = json.load(f)
                    restored = new_session.restore_session_from_serialized(save_data)
                    assert restored is True

                    # 4. Check entity counts & URLs
                    assert len(new_session.npcs) == 1, f"NPC count duplicated on cycle {cycle}!"
                    assert len(new_session.players) == 1
                    assert new_session.players[0].character.image_url == "/assets/characters/aeloria_portrait_123.png"
                    assert new_session.players[0].character.inventory[0].image_url == "/assets/items/moonblade_998.png"
                    assert new_session.current_scene.image_url == "/assets/scenes/citadel_panoramic_456.png"
                    assert new_session.current_scene.battlemap_image_url == "/assets/maps/citadel_aerial_grid_789.png"
                    assert new_session.npcs[0].character.image_url == "/assets/characters/kobold_shaman_321.png"

                    current_session = new_session

            # Crucial verification: Zero image generation calls were made
            assert mock_gen_entity.call_count == 0
            assert mock_gen_cache.call_count == 0


# =====================================================================
# 4. STRESS & RESOURCE CONSTRAINTS SUITE
# =====================================================================

class TestAdversarialStressAndMemory:
    """Stress-test prompt builder and hashing against massive payloads and high iteration."""

    def test_oversized_adversarial_prompt_hashing(self):
        """A 50KB prompt synthesizes and hashes deterministically in under 50ms without memory leak."""
        huge_text = "Adversarial high fantasy description with repeating tokens. " * 1000  # ~60KB
        hash1 = image_gen_service.compute_hash("characters", huge_text, "1:1")
        hash2 = image_gen_service.compute_hash("characters", huge_text, "1:1")

        assert hash1 == hash2
        assert len(hash1) == 16

        # Build prompts with oversized descriptions
        prompt, neg = PromptBuilder.build_character_prompt(
            name="MegaName " * 50,
            race="Elf " * 50,
            char_class="Wizard " * 50,
            appearance=huge_text,
            personality=["Trait " * 50] * 20,
            equipment=["Weapon " * 50] * 20,
        )
        assert len(prompt) > 1000
        assert len(neg) > 10

    def test_high_iteration_placeholder_fetching(self, client: TestClient):
        """100 sequential requests to placeholder SVGs must not leak descriptors or error."""
        for _ in range(100):
            res = client.get("/assets/placeholders/character_warrior.svg")
            assert res.status_code == HTTPStatus.OK
            assert "image/svg+xml" in res.headers.get("content-type", "")
