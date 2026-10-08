"""
backend/tests/test_image_assets.py

Comprehensive Unit and Integration Tests for:
1. Model Schema persistence & engine session serialization
2. Asset storage directory management & 18 thematic SVG placeholders
3. FastAPI static asset mounting & SPA catch-all exclusion
4. GenAI Image Generation Service disk caching & fallback mechanism
5. Assets REST Router endpoints
"""
import pytest
import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from fastapi.testclient import TestClient

import logging
from unittest.mock import MagicMock

from core.schemas.in_game import Character, UnifiedObject, SceneNode, NPCCharacter, AbilityScores, CharacterClass, GameModes
from core.game.engine import Session
from core.game.event_pool import EventPool
from backend.main import app
from backend.src.config import settings
from backend.src.services.asset_manager import asset_manager
from backend.src.services.image_gen_service import image_gen_service
from backend.src.services.prompt_builder import PromptBuilder


# ===================================================================
# FIXTURES
# ===================================================================

@pytest.fixture(scope="module", autouse=True)
def setup_asset_environment():
    """Ensure asset directories and placeholders are seeded before tests."""
    asset_manager.initialize()
    yield


# ===================================================================
# 1. MODEL SCHEMA & ENGINE PERSISTENCE TESTS
# ===================================================================

class TestModelSchemaPersistence:
    """Test schema extensions and engine session roundtrip serialization."""

    def test_unified_object_image_url(self):
        """UnifiedObject must store, serialize, and deserialize image_url."""
        item = UnifiedObject(
            name="Flametongue Longsword",
            description="A blade of magical flame",
            damage_dice="1d8",
            image_url="/assets/items/flametongue.png",
        )
        assert item.image_url == "/assets/items/flametongue.png"
        data = item.model_dump()
        assert data["image_url"] == "/assets/items/flametongue.png"

        reconstructed = UnifiedObject(**data)
        assert reconstructed.image_url == "/assets/items/flametongue.png"

    def test_character_image_url(self):
        """Character must store and serialize portrait image_url."""
        stats = AbilityScores(
            strength=16, dexterity=14, constitution=15,
            intelligence=10, wisdom=12, charisma=8
        )
        hero = Character(
            name="Valeros",
            race="Human",
            char_class=CharacterClass.FIGHTER,
            level=3,
            max_hp=28,
            current_hp=28,
            stats=stats,
            image_url="/assets/characters/valeros.png",
        )
        assert hero.image_url == "/assets/characters/valeros.png"
        data = hero.model_dump()
        assert data["image_url"] == "/assets/characters/valeros.png"

        reconstructed = Character(**data)
        assert reconstructed.image_url == "/assets/characters/valeros.png"

    def test_scene_node_image_urls(self):
        """SceneNode must store narrative image_url and tactical battlemap_image_url."""
        scene = SceneNode(
            name="Dragon's Lair",
            description="A cavern piled with gold and scorched rock.",
            image_url="/assets/scenes/dragons_lair.png",
            battlemap_image_url="/assets/maps/dragons_lair_map.png",
        )
        assert scene.image_url == "/assets/scenes/dragons_lair.png"
        assert scene.battlemap_image_url == "/assets/maps/dragons_lair_map.png"

        data = scene.model_dump()
        assert data["image_url"] == "/assets/scenes/dragons_lair.png"
        assert data["battlemap_image_url"] == "/assets/maps/dragons_lair_map.png"

        reconstructed = SceneNode(**data)
        assert reconstructed.image_url == "/assets/scenes/dragons_lair.png"
        assert reconstructed.battlemap_image_url == "/assets/maps/dragons_lair_map.png"

    def test_legacy_model_backward_compatibility(self):
        """Models without image_url default cleanly to None without validation errors."""
        item = UnifiedObject(name="Rope")
        assert item.image_url is None

        stats = AbilityScores(
            strength=10, dexterity=10, constitution=10,
            intelligence=10, wisdom=10, charisma=10
        )
        char = Character(
            name="Commoner",
            race="Human",
            char_class=CharacterClass.FIGHTER,
            max_hp=4,
            current_hp=4,
            stats=stats,
        )
        assert char.image_url is None

        scene = SceneNode(name="Room", description="An empty room")
        assert scene.image_url is None
        assert scene.battlemap_image_url is None

    def test_engine_session_state_serialization_and_restore(self):
        """Engine session state serializes and restores image_url and battlemap_image_url without duplication."""
        # Setup mock session with orchestrator
        class MockOrchestrator:
            pass

        orchestrator = MockOrchestrator()
        mock_chroma = MagicMock()
        mock_logger = logging.getLogger("test_session")
        mock_gen = MagicMock()
        mock_pool = EventPool()
        mock_delivery = MagicMock()

        session = Session(
            session_name="Test Visual Campaign",
            chroma_client=mock_chroma,
            logger=mock_logger,
            generator=mock_gen,
            event_pool=mock_pool,
            delivery=mock_delivery,
        )
        session._init_orchestrator(orchestrator)
        session.game_mode = GameModes.STORY

        # Add player with image_url and item with image_url
        stats = AbilityScores(
            strength=16, dexterity=12, constitution=14,
            intelligence=10, wisdom=12, charisma=8
        )
        sword = UnifiedObject(name="Sunblade", image_url="/assets/items/sunblade.png")
        hero = Character(
            name="Eldrin",
            race="Elf",
            char_class=CharacterClass.FIGHTER,
            max_hp=20,
            current_hp=20,
            stats=stats,
            inventory=[sword],
            image_url="/assets/characters/eldrin.png",
        )
        player = session._init_player(hero, orchestrator)
        session.players.append(player)

        # Add current scene with narrative and battlemap URLs
        current_scene = SceneNode(
            name="Ancient Temple",
            description="Carved stone pillars and misty moonlight.",
            image_url="/assets/scenes/ancient_temple.png",
            battlemap_image_url="/assets/maps/ancient_temple_grid.png",
        )
        session.current_scene = current_scene
        session.all_locations[current_scene.name] = current_scene
        session.current_location_name = current_scene.name

        # Add NPC with image_url
        npc_char = NPCCharacter(
            name="Goblin Scout",
            race="Goblin",
            char_class=CharacterClass.ROGUE,
            max_hp=7,
            current_hp=7,
            stats=stats,
            current_scene=current_scene.name,
            image_url="/assets/characters/goblin_scout.png",
        )
        session._init_npc(npc_char)
        assert len(session.npcs) == 1

        # 1. Serialize session state
        serialized = session.get_session_state()
        assert serialized["current_scene"]["image_url"] == "/assets/scenes/ancient_temple.png"
        assert serialized["current_scene"]["battlemap_image_url"] == "/assets/maps/ancient_temple_grid.png"
        assert serialized["players"][0]["image_url"] == "/assets/characters/eldrin.png"
        assert serialized["players"][0]["inventory"][0]["image_url"] == "/assets/items/sunblade.png"
        assert serialized["npcs"][0]["image_url"] == "/assets/characters/goblin_scout.png"

        # 2. Restore into a new session
        new_session = Session(
            session_name="Restored Campaign",
            chroma_client=mock_chroma,
            logger=mock_logger,
            generator=mock_gen,
            event_pool=EventPool(),
            delivery=mock_delivery,
        )
        new_session._init_orchestrator(orchestrator)
        restored = new_session.restore_session_from_serialized(serialized)

        # Verify return True and no NPC duplication
        assert restored is True
        assert len(new_session.npcs) == 1, "NPC count must not double on session restore"
        assert len(new_session.players) == 1

        # Verify images survived restoration intact
        restored_player = new_session.players[0].character
        assert restored_player.image_url == "/assets/characters/eldrin.png"
        assert restored_player.inventory[0].image_url == "/assets/items/sunblade.png"

        restored_scene = new_session.current_scene
        assert restored_scene.image_url == "/assets/scenes/ancient_temple.png"
        assert restored_scene.battlemap_image_url == "/assets/maps/ancient_temple_grid.png"

        restored_npc = new_session.npcs[0].character
        assert restored_npc.image_url == "/assets/characters/goblin_scout.png"


# ===================================================================
# 2. ASSET MANAGER & SVG PLACEHOLDERS TESTS
# ===================================================================

class TestAssetManagerAndPlaceholders:
    """Test asset directories, 18 thematic SVG templates, and procedural SVGs."""

    def test_directory_tree_exists(self):
        """Assert all 5 asset directories exist."""
        for category in ["characters", "items", "scenes", "maps", "placeholders"]:
            cat_dir = asset_manager.base_dir / category
            assert cat_dir.is_dir(), f"Missing directory: {cat_dir}"

    def test_all_18_placeholders_seeded(self):
        """Assert all 18 bundled SVGs exist on disk and are non-empty."""
        placeholder_dir = asset_manager.base_dir / "placeholders"
        expected = [
            "character_default.svg", "character_warrior.svg", "character_wizard.svg",
            "character_rogue.svg", "character_cleric.svg",
            "item_default.svg", "item_weapon.svg", "item_armor.svg",
            "item_potion.svg", "item_scroll.svg",
            "scene_default.svg", "scene_tavern.svg", "scene_dungeon.svg", "scene_wilderness.svg",
            "battlemap_default.svg", "battlemap_stone.svg", "battlemap_dungeon.svg", "battlemap_wilderness.svg",
        ]
        assert len(expected) == 18
        for filename in expected:
            path = placeholder_dir / filename
            assert path.is_file(), f"Missing SVG placeholder: {filename}"
            assert path.stat().st_size > 0, f"Empty SVG placeholder: {filename}"

    def test_all_18_placeholders_valid_xml(self):
        """Parse all 18 SVGs to guarantee well-formed XML with SVG root and viewBox."""
        placeholder_dir = asset_manager.base_dir / "placeholders"
        for svg_path in placeholder_dir.glob("*.svg"):
            with open(svg_path, "r", encoding="utf-8") as f:
                content = f.read()
            root = ET.fromstring(content)
            assert root.tag.endswith("svg"), f"{svg_path.name} root tag must be svg"
            assert "viewBox" in root.attrib, f"{svg_path.name} missing viewBox"

    def test_fallback_placeholder_resolution(self):
        """Assert resolution logic maps subtypes to appropriate thematic SVGs."""
        # Characters
        assert "character_warrior.svg" in asset_manager.get_fallback_placeholder_url("character", "Fighter")
        assert "character_warrior.svg" in asset_manager.get_fallback_placeholder_url("character", "Barbarian")
        assert "character_wizard.svg" in asset_manager.get_fallback_placeholder_url("character", "Wizard")
        assert "character_rogue.svg" in asset_manager.get_fallback_placeholder_url("character", "Ranger")
        assert "character_cleric.svg" in asset_manager.get_fallback_placeholder_url("character", "Paladin")
        assert "character_default.svg" in asset_manager.get_fallback_placeholder_url("character", "Unknown")

        # Items
        assert "item_weapon.svg" in asset_manager.get_fallback_placeholder_url("item", "Sword")
        assert "item_armor.svg" in asset_manager.get_fallback_placeholder_url("item", "Shield")
        assert "item_potion.svg" in asset_manager.get_fallback_placeholder_url("item", "Elixir")
        assert "item_scroll.svg" in asset_manager.get_fallback_placeholder_url("item", "Scroll")
        assert "item_default.svg" in asset_manager.get_fallback_placeholder_url("item", "Artifact")

        # Scenes
        assert "scene_tavern.svg" in asset_manager.get_fallback_placeholder_url("scene", "Tavern")
        assert "scene_dungeon.svg" in asset_manager.get_fallback_placeholder_url("scene", "Crypt")
        assert "scene_wilderness.svg" in asset_manager.get_fallback_placeholder_url("scene", "Forest")
        assert "scene_default.svg" in asset_manager.get_fallback_placeholder_url("scene", "Castle")

        # Battlemaps
        assert "battlemap_stone.svg" in asset_manager.get_fallback_placeholder_url("battlemap", "Flagstone")
        assert "battlemap_dungeon.svg" in asset_manager.get_fallback_placeholder_url("battlemap", "Dungeon Arena")
        assert "battlemap_wilderness.svg" in asset_manager.get_fallback_placeholder_url("battlemap", "River Crossing")
        assert "battlemap_default.svg" in asset_manager.get_fallback_placeholder_url("battlemap", "Grid")

    def test_procedural_avatar_generation(self):
        """Verify dynamic SVG avatar contains monogram initials and name."""
        svg = asset_manager.generate_procedural_avatar("Kaelen Sunstride", "Paladin", "Elf")
        root = ET.fromstring(svg)
        assert root.tag.endswith("svg")
        assert "KS" in svg
        assert "KAELEN SUNSTRIDE" in svg
        assert "ELF" in svg
        assert "PALADIN" in svg

    def test_procedural_battlemap_generation(self):
        """Verify dynamic battlemap SVG contains grid units and title."""
        svg = asset_manager.generate_procedural_battlemap(15, 12, cell_size=50, title="Cave Hideout")
        root = ET.fromstring(svg)
        assert root.tag.endswith("svg")
        assert "CAVE HIDEOUT" in svg
        assert "15 x 12 TACTICAL GRID" in svg

    def test_storage_stats(self):
        """Verify storage stats reports healthy system and counts."""
        stats = asset_manager.get_storage_stats()
        assert stats["status"] == "healthy"
        assert stats["total_files"] >= 18
        assert "categories" in stats
        assert stats["categories"]["placeholders"]["file_count"] >= 18


# ===================================================================
# 3. STATIC FILE SERVING TESTS
# ===================================================================

class TestStaticFileServing:
    """Test root and API static file mounts, MIME types, and path traversal protection."""

    def test_serve_placeholder_root_mount(self, client: TestClient):
        """GET /assets/placeholders/character_warrior.svg serves SVG with image/svg+xml."""
        response = client.get("/assets/placeholders/character_warrior.svg")
        assert response.status_code == 200
        assert "image/svg+xml" in response.headers.get("content-type", "")
        assert b"<svg" in response.content

    def test_serve_placeholder_api_mount(self, client: TestClient):
        """GET /api/v1/assets/placeholders/scene_tavern.svg serves SVG via /api/v1 mount."""
        response = client.get("/api/v1/assets/placeholders/scene_tavern.svg")
        assert response.status_code == 200
        assert "image/svg+xml" in response.headers.get("content-type", "")
        assert b"<svg" in response.content

    def test_serve_binary_image_png(self, client: TestClient):
        """Verify binary PNG serving and image/png MIME header."""
        test_png = asset_manager.base_dir / "characters" / "unit_test_dummy.png"
        png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
        try:
            with open(test_png, "wb") as f:
                f.write(png_bytes)

            res1 = client.get("/assets/characters/unit_test_dummy.png")
            assert res1.status_code == 200
            assert res1.headers.get("content-type") == "image/png"
            assert res1.content == png_bytes

            res2 = client.get("/api/v1/assets/characters/unit_test_dummy.png")
            assert res2.status_code == 200
            assert res2.headers.get("content-type") == "image/png"
            assert res2.content == png_bytes
        finally:
            if test_png.exists():
                test_png.unlink()

    def test_nonexistent_asset_returns_404_not_spa_html(self, client: TestClient):
        """Nonexistent asset must return 404, not falling through to SPA index.html."""
        response = client.get("/assets/characters/completely_missing_asset_12345.png")
        assert response.status_code == 404
        assert b"<!DOCTYPE html>" not in response.content

    def test_path_traversal_blocked(self, client: TestClient):
        """Path traversal attempts are rejected with 404."""
        response = client.get("/assets/../../main.py")
        assert response.status_code == 404


# ===================================================================
# 4. GENAI IMAGE GENERATION SERVICE TESTS
# ===================================================================

class TestImageGenService:
    """Test deterministic caching, prompt construction, and offline fallback."""

    def test_hash_determinism(self):
        """Hash is strictly deterministic regardless of whitespace or casing."""
        h1 = image_gen_service.compute_hash("characters", "A brave dwarf warrior", "1:1")
        h2 = image_gen_service.compute_hash("characters", "  a BRAVE dwarf warrior  ", "1:1")
        assert h1 == h2
        assert len(h1) == 16

        h3 = image_gen_service.compute_hash("characters", "A sneaky rogue", "1:1")
        assert h1 != h3

    @pytest.mark.asyncio
    async def test_disk_cache_hit(self):
        """If file exists on disk, returns status='completed' and cached=True immediately."""
        prompt = "Unique test prompt for disk caching test"
        h = image_gen_service.compute_hash("characters", prompt, "1:1")
        file_path = image_gen_service.asset_dir / "characters" / f"{h}.png"

        dummy_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
        try:
            with open(file_path, "wb") as f:
                f.write(dummy_bytes)

            result = await image_gen_service._generate_with_cache(
                category="characters",
                prompt=prompt,
                negative_prompt="",
                aspect_ratio="1:1",
                entity_id="test_entity",
            )
            assert result.status == "completed"
            assert result.cached is True
            assert f"{h}.png" in result.image_url
        finally:
            if file_path.exists():
                file_path.unlink()

    @pytest.mark.asyncio
    async def test_fallback_when_offline_or_key_missing(self, monkeypatch):
        """When API key is not provided, service returns status='fallback' and thematic SVG."""
        monkeypatch.setattr(image_gen_service, "api_key", "")
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "")

        result = await image_gen_service.generate_character_portrait(
            character_id="hero_99",
            name="Aric",
            race="Human",
            char_class="Fighter",
        )
        assert result.status == "fallback"
        assert result.cached is False
        assert "character_warrior.svg" in result.image_url

    def test_prompt_builders(self):
        """Prompt builder constructs detailed prompts and negative prompts for all types."""
        # Character
        p, neg = PromptBuilder.build_character_prompt(
            name="Lyra", race="Elf", char_class="Wizard",
            appearance="Silver hair, star robes", backstory="Apprentice of the High Arcanist",
            personality=["Curious", "Cautious"], equipment=["Staff of Power", "Spellbook"]
        )
        assert "Lyra" in p
        assert "Elf Wizard" in p
        assert "modern clothing" in neg

        # Battlemap
        p_bm, neg_bm = PromptBuilder.build_battlemap_prompt(
            name="Crypt Hall",
            description="Ancient crypt with stone sarcophagi",
            dimensions=(16, 12),
            terrain_type="Flagstone floor",
            obstacles=["Pillars", "Altar"]
        )
        assert "orthographic aerial top-down perspective" in p_bm
        assert "16 by 12" in p_bm
        assert "isometric" in neg_bm
        assert "grid lines" in neg_bm
        assert "characters" in neg_bm

    def test_default_cheapest_models_priority(self):
        """Ensure the cheapest Google Gemini models are prioritized by default."""
        assert settings.IMAGEN_MODEL == "gemini-3.1-flash-lite-image"
        assert settings.GEMINI_MODEL == "gemini-3.5-flash-lite"
        assert image_gen_service.model == "gemini-3.1-flash-lite-image"

    def test_gemini_multimodal_image_dispatch(self, monkeypatch):
        """gemini-*-image models must route to client.models.generate_content."""
        from unittest.mock import MagicMock
        mock_client = MagicMock()
        mock_part = MagicMock()
        mock_part.inline_data.data = b"fake-gemini-image-bytes"
        mock_response = MagicMock()
        mock_response.parts = [mock_part]
        mock_client.models.generate_content.return_value = mock_response

        service = image_gen_service
        monkeypatch.setattr(service, "_client", mock_client)
        monkeypatch.setattr(service, "model", "gemini-3.1-flash-lite-image")

        res_bytes = service._call_imagen_sync("A wizard in a tower", "", "1:1")
        assert res_bytes == b"fake-gemini-image-bytes"
        mock_client.models.generate_content.assert_called_once()
        mock_client.models.generate_images.assert_not_called()

    def test_legacy_imagen_dispatch(self, monkeypatch):
        """imagen-* models must route to client.models.generate_images."""
        from unittest.mock import MagicMock
        mock_client = MagicMock()
        mock_img = MagicMock()
        mock_img.image.image_bytes = b"fake-imagen-bytes"
        mock_img.rai_filtered_reason = None
        mock_response = MagicMock()
        mock_response.generated_images = [mock_img]
        mock_client.models.generate_images.return_value = mock_response

        service = image_gen_service
        monkeypatch.setattr(service, "_client", mock_client)
        monkeypatch.setattr(service, "model", "imagen-3.0-generate-002")

        res_bytes = service._call_imagen_sync("A dragon on a hill", "", "16:9")
        assert res_bytes == b"fake-imagen-bytes"
        mock_client.models.generate_images.assert_called_once()
        mock_client.models.generate_content.assert_not_called()


# ===================================================================
# 5. ASSETS REST ROUTER TESTS
# ===================================================================

class TestAssetsRouter:
    """Test REST API routes on /api/v1/assets."""

    def test_get_asset_status(self, client: TestClient):
        """GET /api/v1/assets/status returns system health and category counts."""
        response = client.get("/api/v1/assets/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "categories" in data
        assert data["categories"]["placeholders"]["file_count"] >= 18

    def test_get_single_asset_info(self, client: TestClient):
        """GET /api/v1/assets/status/{cat}/{file} returns item metadata."""
        response = client.get("/api/v1/assets/status/placeholders/character_warrior.svg")
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "character_warrior.svg"
        assert data["category"] == "placeholders"
        assert data["mime_type"] == "image/svg+xml"
        assert data["is_placeholder"] is True

    def test_get_asset_info_invalid_category(self, client: TestClient):
        """Invalid category returns 400 Bad Request."""
        response = client.get("/api/v1/assets/status/invalid_category/test.svg")
        assert response.status_code == 400

    def test_get_asset_info_not_found(self, client: TestClient):
        """Nonexistent asset in valid category returns 404."""
        response = client.get("/api/v1/assets/status/characters/not_existing.png")
        assert response.status_code == 404

    def test_list_cached_assets(self, client: TestClient):
        """GET /api/v1/assets/list returns paginated asset items."""
        response = client.get("/api/v1/assets/list?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert len(data["items"]) <= 10
        if data["items"]:
            assert "url" in data["items"][0]
            assert "api_url" in data["items"][0]

    def test_generate_asset_fallback(self, client: TestClient, monkeypatch):
        """POST /api/v1/assets/generate returns thematic fallback without API key."""
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
        payload = {
            "entity_type": "character",
            "entity_id": "test_hero_42",
            "subtype": "Fighter",
            "description": "Armored champion of light"
        }
        response = client.post("/api/v1/assets/generate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "fallback"
        assert "character_warrior.svg" in data["image_url"]

    def test_regenerate_asset_alias(self, client: TestClient, monkeypatch):
        """POST /api/v1/assets/regenerate acts as generate alias with force flag."""
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
        payload = {
            "entity_type": "item",
            "entity_id": "sword_99",
            "subtype": "Weapon",
            "description": "Broadsword"
        }
        response = client.post("/api/v1/assets/regenerate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "fallback"
        assert "item_weapon.svg" in data["image_url"]

    def test_seed_placeholders_endpoint(self, client: TestClient):
        """POST /api/v1/assets/seed-placeholders ensures placeholders are seeded."""
        response = client.post("/api/v1/assets/seed-placeholders")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_procedural_avatar_endpoint(self, client: TestClient):
        """POST /api/v1/assets/procedural/avatar returns valid vector SVG."""
        payload = {"name": "Gimli Ironfoot", "char_class": "Warrior", "race": "Dwarf"}
        response = client.post("/api/v1/assets/procedural/avatar", json=payload)
        assert response.status_code == 200
        assert response.headers.get("content-type") == "image/svg+xml"
        assert b"GI" in response.content
        assert b"GIMLI IRONFOOT" in response.content

    def test_procedural_battlemap_endpoint(self, client: TestClient):
        """POST /api/v1/assets/procedural/battlemap returns valid grid SVG."""
        payload = {"width": 12, "height": 8, "title": "CRYPT ENTRANCE"}
        response = client.post("/api/v1/assets/procedural/battlemap", json=payload)
        assert response.status_code == 200
        assert response.headers.get("content-type") == "image/svg+xml"
        assert b"12 x 8 TACTICAL GRID" in response.content
