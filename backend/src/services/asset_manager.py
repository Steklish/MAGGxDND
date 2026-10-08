"""
backend/src/services/asset_manager.py

Asset Manager Service for MAGGxDND.
Handles local disk asset lifecycle, directory initialization,
fallback SVG seeding, and procedural asset generation.
"""
import os
import html
import shutil
import datetime
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Literal

from backend.src.config import settings
from backend.src.logging import get_logger
from backend.src.services.placeholder_templates import BUNDLED_PLACEHOLDERS

logger = get_logger("asset_manager")

AssetCategory = Literal["characters", "items", "scenes", "maps", "placeholders", "vectors", "web-backgrounds"]
EntityType = Literal["character", "item", "scene", "battlemap"]


class AssetManager:
    """Manages the static visual asset filesystem, placeholders, and procedural assets."""

    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir:
            self.base_dir = Path(base_dir)
        elif hasattr(settings, "ASSETS_DIR"):
            self.base_dir = Path(settings.ASSETS_DIR)
        else:
            project_root = getattr(settings, "PROJECT_ROOT", Path(__file__).resolve().parents[3])
            self.base_dir = project_root / "data" / "assets"

        self.categories: List[str] = ["characters", "items", "scenes", "maps", "placeholders", "vectors", "web-backgrounds"]

    def initialize(self) -> None:
        """Create directory structure and seed default SVG placeholders."""
        self.ensure_directories()
        self.seed_default_placeholders()

    def ensure_directories(self) -> None:
        """Ensure all required asset subdirectories exist."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        for category in self.categories:
            cat_dir = self.base_dir / category
            cat_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Verified asset directory tree at {self.base_dir}")

    def get_asset_path(self, category: str, filename: str) -> Path:
        """Safely resolve asset file path preventing directory traversal."""
        clean_filename = os.path.basename(filename)
        return self.base_dir / category / clean_filename

    def asset_exists(self, category: str, filename: str) -> bool:
        """Check if asset file exists on disk."""
        path = self.get_asset_path(category, filename)
        return path.is_file()

    def get_asset_url(self, category: str, filename: str) -> str:
        """Standard frontend web URL for root static mount."""
        clean_filename = os.path.basename(filename)
        return f"/assets/{category}/{clean_filename}"

    def get_api_asset_url(self, category: str, filename: str) -> str:
        """API URL for /api/v1 static mount."""
        clean_filename = os.path.basename(filename)
        return f"/api/v1/assets/{category}/{clean_filename}"

    def get_fallback_placeholder_url(self, entity_type: str, subtype: Optional[str] = None) -> str:
        """Return relative URL to appropriate fallback SVG."""
        filename = self.resolve_placeholder_filename(entity_type, subtype)
        return f"/assets/placeholders/{filename}"

    def resolve_placeholder_filename(self, entity_type: str, subtype: Optional[str] = None) -> str:
        """Map entity type and subtype to one of the 18 bundled SVGs."""
        sub = (subtype or "").lower().strip()
        e_type = entity_type.lower().strip()

        if e_type in ["dm", "master", "dungeon_master"]:
            return "dm_emblem.svg"

        if e_type in ["character", "characters"]:
            if any(k in sub for k in ["dm", "master", "dungeon master"]):
                return "dm_emblem.svg"
            if any(k in sub for k in ["warrior", "fighter", "barbarian"]):
                return "character_warrior.svg"
            if any(k in sub for k in ["wizard", "mage", "sorcerer", "warlock"]):
                return "character_wizard.svg"
            if any(k in sub for k in ["rogue", "thief", "assassin", "ranger"]):
                return "character_rogue.svg"
            if any(k in sub for k in ["cleric", "paladin", "priest"]):
                return "character_cleric.svg"
            return "character_default.svg"

        elif e_type in ["item", "items"]:
            if any(k in sub for k in ["weapon", "sword", "dagger", "axe", "bow"]):
                return "item_weapon.svg"
            if any(k in sub for k in ["armor", "shield", "helmet", "mail"]):
                return "item_armor.svg"
            if any(k in sub for k in ["potion", "flask", "elixir"]):
                return "item_potion.svg"
            if any(k in sub for k in ["scroll", "tome", "book", "map"]):
                return "item_scroll.svg"
            return "item_default.svg"

        elif e_type in ["scene", "scenes"]:
            if any(k in sub for k in ["tavern", "inn", "pub"]):
                return "scene_tavern.svg"
            if any(k in sub for k in ["dungeon", "crypt", "cave", "cellar"]):
                return "scene_dungeon.svg"
            if any(k in sub for k in ["wilderness", "forest", "woods", "mountain"]):
                return "scene_wilderness.svg"
            return "scene_default.svg"

        elif e_type in ["battlemap", "maps", "map"]:
            if any(k in sub for k in ["stone", "flagstone", "hall"]):
                return "battlemap_stone.svg"
            if any(k in sub for k in ["dungeon", "arena", "pillars"]):
                return "battlemap_dungeon.svg"
            if any(k in sub for k in ["wilderness", "river", "glade"]):
                return "battlemap_wilderness.svg"
            return "battlemap_default.svg"

        return "character_default.svg"

    def list_assets(
        self,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[dict], int]:
        """List cached assets with pagination and metadata."""
        target_categories = [category] if category else self.categories
        items = []

        for cat in target_categories:
            cat_dir = self.base_dir / cat
            if not cat_dir.is_dir():
                continue
            for file in cat_dir.iterdir():
                if file.is_file():
                    stat = file.stat()
                    mime, _ = mimetypes.guess_type(file.name)
                    items.append({
                        "filename": file.name,
                        "category": cat,
                        "url": f"/assets/{cat}/{file.name}",
                        "api_url": f"/api/v1/assets/{cat}/{file.name}",
                        "size_bytes": stat.st_size,
                        "mime_type": mime or "application/octet-stream",
                        "modified_at": datetime.datetime.fromtimestamp(stat.st_mtime, tz=datetime.timezone.utc).isoformat(),
                        "is_placeholder": (cat == "placeholders")
                    })

        items.sort(key=lambda x: x["modified_at"], reverse=True)
        total = len(items)
        paginated = items[offset : offset + limit]
        return paginated, total

    def get_storage_stats(self) -> dict:
        """Calculate disk consumption and file counts per category."""
        total_files = 0
        total_bytes = 0
        categories_stats = {}

        for cat in self.categories:
            cat_dir = self.base_dir / cat
            cat_files = 0
            cat_bytes = 0
            if cat_dir.is_dir():
                for f in cat_dir.iterdir():
                    if f.is_file():
                        cat_files += 1
                        cat_bytes += f.stat().st_size
            categories_stats[cat] = {
                "file_count": cat_files,
                "size_bytes": cat_bytes,
                "directory_exists": cat_dir.is_dir()
            }
            total_files += cat_files
            total_bytes += cat_bytes

        return {
            "status": "healthy",
            "storage_path": str(self.base_dir),
            "total_files": total_files,
            "total_size_bytes": total_bytes,
            "total_size_mb": round(total_bytes / (1024 * 1024), 2),
            "categories": categories_stats
        }

    def seed_default_placeholders(self) -> int:
        """Seed all 18 standard thematic SVGs into placeholders directory."""
        placeholder_dir = self.base_dir / "placeholders"
        placeholder_dir.mkdir(parents=True, exist_ok=True)
        seeded = 0

        for filename, svg_content in BUNDLED_PLACEHOLDERS.items():
            dest = placeholder_dir / filename
            if not dest.exists():
                with open(dest, "w", encoding="utf-8") as f:
                    f.write(svg_content.strip())
                seeded += 1
        return seeded

    def generate_procedural_avatar(self, name: str, char_class: str = "Warrior", race: str = "Human") -> str:
        """Generate a custom procedural SVG avatar."""
        initials = "".join([part[0].upper() for part in name.strip().split() if part])[:2] or "H"
        clean_initials = html.escape(initials)
        clean_name = html.escape(name.upper())
        clean_subtitle = html.escape(f"{race.upper()} • {char_class.upper()}")
        class_colors = {
            "warrior": ("#dc2626", "#450a0a"),
            "fighter": ("#dc2626", "#450a0a"),
            "barbarian": ("#b91c1c", "#450a0a"),
            "wizard": ("#9333ea", "#3b0764"),
            "mage": ("#9333ea", "#3b0764"),
            "sorcerer": ("#7c3aed", "#2e1065"),
            "rogue": ("#10b981", "#022c22"),
            "ranger": ("#059669", "#064e3b"),
            "cleric": ("#eab308", "#422006"),
            "paladin": ("#f59e0b", "#451a03"),
            "bard": ("#ec4899", "#500724"),
            "druid": ("#16a34a", "#052e16"),
            "monk": ("#f97316", "#431407"),
            "warlock": ("#6366f1", "#1e1b4b"),
        }
        primary, dark = class_colors.get(char_class.lower(), ("#3b82f6", "#172554"))
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <defs>
    <radialGradient id="grad-proc" cx="50%" cy="40%" r="65%">
      <stop offset="0%" stop-color="{primary}" stop-opacity="0.4"/>
      <stop offset="100%" stop-color="{dark}"/>
    </radialGradient>
  </defs>
  <rect width="512" height="512" rx="32" fill="url(#grad-proc)"/>
  <rect x="16" y="16" width="480" height="480" rx="24" fill="none" stroke="{primary}" stroke-width="2" opacity="0.6"/>
  <circle cx="256" cy="210" r="90" fill="{dark}" stroke="{primary}" stroke-width="4"/>
  <text x="256" y="235" fill="#f8fafc" font-family="system-ui, sans-serif" font-size="72" font-weight="bold" text-anchor="middle">{clean_initials}</text>
  <text x="256" y="370" fill="#f8fafc" font-family="system-ui, sans-serif" font-size="24" font-weight="bold" letter-spacing="3" text-anchor="middle">{clean_name}</text>
  <text x="256" y="405" fill="{primary}" font-family="system-ui, sans-serif" font-size="14" font-weight="bold" letter-spacing="2" text-anchor="middle">{clean_subtitle}</text>
</svg>"""

    def generate_procedural_battlemap(self, width: int = 10, height: int = 10, cell_size: int = 60, title: str = "BATTLEFIELD") -> str:
        """Generate a procedural grid battlemap with custom dimensions."""
        total_w = width * cell_size
        total_h = height * cell_size
        clean_title = html.escape(title.upper())
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_w} {total_h}" width="100%" height="100%">
  <defs>
    <pattern id="proc-grid" width="{cell_size}" height="{cell_size}" patternUnits="userSpaceOnUse">
      <rect width="{cell_size}" height="{cell_size}" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="1"/>
      <circle cx="{cell_size//2}" cy="{cell_size//2}" r="1.5" fill="rgba(255,255,255,0.2)"/>
    </pattern>
  </defs>
  <rect width="{total_w}" height="{total_h}" fill="#0f172a"/>
  <rect width="{total_w}" height="{total_h}" fill="url(#proc-grid)"/>
  <rect x="4" y="4" width="{total_w - 8}" height="{total_h - 8}" fill="none" stroke="#475569" stroke-width="2"/>
  <text x="{total_w // 2}" y="{total_h // 2}" fill="rgba(255,255,255,0.08)" font-family="system-ui, sans-serif" font-size="36" font-weight="bold" letter-spacing="8" text-anchor="middle">{clean_title}</text>
  <text x="{total_w // 2}" y="{total_h - 16}" fill="#94a3b8" font-family="system-ui, sans-serif" font-size="12" font-weight="bold" letter-spacing="2" text-anchor="middle">{width} x {height} TACTICAL GRID</text>
</svg>"""


# Global singleton instance
asset_manager = AssetManager()
