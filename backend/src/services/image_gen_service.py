"""
backend/src/services/image_gen_service.py

High-performance, non-blocking GenAI Image Generation Service for MAGGxDND.
Uses google-genai SDK reading GEMINI_API_KEY with deterministic SHA-256 disk caching,
fallback placeholders, concurrency throttling, and structured error handling.
"""

import os
import hashlib
import asyncio
import logging
import weakref
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
from pydantic import BaseModel, Field

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None  # type: ignore
    types = None  # type: ignore

from backend.src.config import settings
from backend.src.services.asset_manager import asset_manager
from backend.src.services.prompt_builder import PromptBuilder

logger = logging.getLogger("image_gen_service")


class GenerationResult(BaseModel):
    """Result schema for asset generation."""
    status: str = Field(..., description="'completed', 'processing', 'fallback', or 'failed'")
    image_url: str = Field(..., description="Web-accessible URL path to the image or placeholder")
    cached: bool = Field(False, description="True if retrieved from local disk cache")
    error: Optional[str] = Field(None, description="Error detail if generation failed or fell back")
    prompt_used: Optional[str] = Field(None, description="Synthesized prompt sent to the model")


class ImageGenService:
    """
    Coordinates Google GenAI / Imagen image generation for characters, items,
    scene narratives, and top-down tactical battle maps.
    """

    CATEGORIES = ("characters", "items", "scenes", "maps", "placeholders")

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        asset_root: Optional[str] = None,
        max_concurrency: int = 3,
    ):
        self.api_key = api_key or getattr(settings, "GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
        self.model = model or getattr(settings, "IMAGEN_MODEL", "gemini-3.1-flash-lite-image")

        if asset_root:
            self.asset_dir = Path(asset_root)
        elif hasattr(settings, "ASSETS_DIR"):
            self.asset_dir = Path(settings.ASSETS_DIR)
        else:
            project_root = getattr(settings, "PROJECT_ROOT", Path(__file__).resolve().parents[3])
            self.asset_dir = project_root / "data" / "assets"

        self._ensure_directories()

        self.max_concurrency = max_concurrency
        self._locks: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()
        self._semaphores: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()
        self._active_tasks: Dict[str, asyncio.Future] = {}

        # Initialize Google GenAI client if key is provided and SDK available
        self.is_configured = bool(
            GENAI_AVAILABLE
            and self.api_key
            and self.api_key not in ("NO_KEY", "your-gemini-key", "")
        )
        self._client = None
        if self.is_configured and GENAI_AVAILABLE:
            try:
                self._client = genai.Client(api_key=self.api_key)
                logger.info(f"ImageGenService initialized with model '{self.model}'")
            except Exception as e:
                logger.error(f"Failed to initialize google-genai client: {e}")
                self.is_configured = False
        else:
            logger.info("ImageGenService: Running in fallback placeholder mode (API key not configured or offline).")

    def _ensure_directories(self) -> None:
        """Create category storage folders on startup."""
        self.asset_dir.mkdir(parents=True, exist_ok=True)
        for cat in self.CATEGORIES:
            (self.asset_dir / cat).mkdir(parents=True, exist_ok=True)

    def _get_lock(self) -> asyncio.Lock:
        """Lazily initialize and return an asyncio.Lock bound to the currently running event loop."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.Lock()
        lock = self._locks.get(loop)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[loop] = lock
        return lock

    def _get_semaphore(self) -> asyncio.Semaphore:
        """Lazily initialize and return an asyncio.Semaphore bound to the currently running event loop."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.Semaphore(self.max_concurrency)
        sem = self._semaphores.get(loop)
        if sem is None:
            sem = asyncio.Semaphore(self.max_concurrency)
            self._semaphores[loop] = sem
        return sem

    @property
    def _lock(self) -> asyncio.Lock:
        """Property returning the loop-bound asyncio.Lock for backward compatibility."""
        return self._get_lock()

    @_lock.setter
    def _lock(self, value: asyncio.Lock) -> None:
        try:
            loop = asyncio.get_running_loop()
            self._locks[loop] = value
        except RuntimeError:
            pass

    @property
    def _semaphore(self) -> asyncio.Semaphore:
        """Property returning the loop-bound asyncio.Semaphore for backward compatibility."""
        return self._get_semaphore()

    @_semaphore.setter
    def _semaphore(self, value: asyncio.Semaphore) -> None:
        try:
            loop = asyncio.get_running_loop()
            self._semaphores[loop] = value
        except RuntimeError:
            pass

    def compute_hash(self, category: str, prompt: str, aspect_ratio: str = "1:1") -> str:
        """Compute deterministic 16-character SHA-256 hash."""
        normalized = " ".join(prompt.strip().lower().split())
        key = f"{category}|{aspect_ratio}|{normalized}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]

    def get_asset_url(self, category: str, filename: str) -> str:
        """Return standardized static URL."""
        return f"/assets/{category}/{filename}"

    def get_fallback_placeholder_url(self, category: str, subtype: Optional[str] = None) -> str:
        """Delegate to AssetManager for fallback placeholder path."""
        return asset_manager.get_fallback_placeholder_url(category, subtype)

    async def generate_character_portrait(
        self,
        character_id: str,
        name: str,
        race: str = "Human",
        char_class: str = "Fighter",
        appearance: Optional[str] = None,
        backstory: Optional[str] = None,
        personality: Optional[List[str]] = None,
        equipment: Optional[List[str]] = None,
    ) -> GenerationResult:
        """Generate high-fantasy bust portrait (1:1)."""
        prompt, negative = PromptBuilder.build_character_prompt(
            name=name,
            race=race,
            char_class=char_class,
            appearance=appearance,
            backstory=backstory,
            personality=personality,
            equipment=equipment,
        )
        return await self._generate_with_cache(
            category="characters",
            prompt=prompt,
            negative_prompt=negative,
            aspect_ratio="1:1",
            entity_id=character_id,
            subtype=char_class,
        )

    async def generate_item_card(
        self,
        item_id: str,
        name: str,
        obj_type: Optional[str] = None,
        description: Optional[str] = None,
        damage_dice: Optional[str] = None,
        damage_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> GenerationResult:
        """Generate studio equipment illustration (1:1)."""
        prompt, negative = PromptBuilder.build_item_prompt(
            name=name,
            obj_type=obj_type,
            description=description,
            damage_dice=damage_dice,
            damage_type=damage_type,
            tags=tags,
        )
        return await self._generate_with_cache(
            category="items",
            prompt=prompt,
            negative_prompt=negative,
            aspect_ratio="1:1",
            entity_id=item_id,
            subtype=obj_type,
        )

    async def generate_scene_header(
        self,
        scene_id: str,
        name: str,
        description: str,
        environment_type: Optional[str] = None,
        mood: Optional[str] = None,
    ) -> GenerationResult:
        """Generate widescreen cinematic landscape (16:9)."""
        prompt, negative = PromptBuilder.build_scene_prompt(
            name=name,
            description=description,
            environment_type=environment_type,
            mood=mood,
        )
        return await self._generate_with_cache(
            category="scenes",
            prompt=prompt,
            negative_prompt=negative,
            aspect_ratio="16:9",
            entity_id=scene_id,
        )

    async def generate_battlemap(
        self,
        scene_id: str,
        name: str,
        description: str,
        dimensions: Tuple[int, int] = (20, 20),
        terrain_type: Optional[str] = None,
        obstacles: Optional[List[str]] = None,
    ) -> GenerationResult:
        """Generate 2D orthographic aerial tactical map (1:1 or 16:9, no tokens, no baked grid)."""
        aspect_ratio = "1:1" if dimensions[0] == dimensions[1] else "16:9"
        prompt, negative = PromptBuilder.build_battlemap_prompt(
            name=name,
            description=description,
            dimensions=dimensions,
            terrain_type=terrain_type,
            obstacles=obstacles,
        )
        return await self._generate_with_cache(
            category="maps",
            prompt=prompt,
            negative_prompt=negative,
            aspect_ratio=aspect_ratio,
            entity_id=scene_id,
        )

    async def generate_for_entity(
        self,
        entity_type: str,
        entity_id: str,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        prompt_override: Optional[str] = None,
        subtype: Optional[str] = None,
    ) -> GenerationResult:
        """General routing generator for any entity type."""
        meta = metadata or {}
        e_type = entity_type.lower().strip()

        if prompt_override:
            category = "characters" if e_type == "character" else "items" if e_type == "item" else "scenes" if e_type == "scene" else "maps"
            aspect = "16:9" if category == "scenes" else "1:1"
            return await self._generate_with_cache(
                category=category,
                prompt=prompt_override,
                negative_prompt="",
                aspect_ratio=aspect,
                entity_id=entity_id,
                subtype=subtype,
            )

        if e_type == "character":
            return await self.generate_character_portrait(
                character_id=entity_id,
                name=meta.get("name", entity_id),
                race=meta.get("race", "Human"),
                char_class=subtype or meta.get("char_class", "Fighter"),
                appearance=description or meta.get("appearance"),
                backstory=meta.get("backstory"),
                personality=meta.get("personality"),
                equipment=meta.get("equipment"),
            )
        elif e_type == "item":
            return await self.generate_item_card(
                item_id=entity_id,
                name=meta.get("name", entity_id),
                obj_type=subtype or meta.get("obj_type"),
                description=description or meta.get("description"),
                damage_dice=meta.get("damage_dice"),
                damage_type=meta.get("damage_type"),
                tags=meta.get("tags"),
            )
        elif e_type == "scene":
            return await self.generate_scene_header(
                scene_id=entity_id,
                name=meta.get("name", entity_id),
                description=description or meta.get("description", "A mysterious fantasy scene"),
                environment_type=meta.get("environment_type"),
                mood=meta.get("mood"),
            )
        elif e_type in ["battlemap", "map"]:
            dim = meta.get("dimensions", (20, 20))
            if isinstance(dim, list):
                dim = tuple(dim)
            return await self.generate_battlemap(
                scene_id=entity_id,
                name=meta.get("name", entity_id),
                description=description or meta.get("description", "Tactical battlefield"),
                dimensions=dim,
                terrain_type=meta.get("terrain_type"),
                obstacles=meta.get("obstacles"),
            )
        else:
            fallback_url = self.get_fallback_placeholder_url("characters")
            return GenerationResult(
                status="fallback",
                image_url=fallback_url,
                cached=False,
                error=f"Unknown entity_type '{entity_type}'",
            )

    async def _generate_with_cache(
        self,
        category: str,
        prompt: str,
        negative_prompt: str,
        aspect_ratio: str,
        entity_id: str,
        subtype: Optional[str] = None,
    ) -> GenerationResult:
        """Check cache, deduplicate in-flight requests, invoke GenAI API, save to disk."""
        cache_hash = self.compute_hash(category, prompt, aspect_ratio)
        png_filename = f"{cache_hash}.png"
        svg_filename = f"{cache_hash}.svg"
        png_path = self.asset_dir / category / png_filename
        svg_path = self.asset_dir / category / svg_filename

        # 1. Check disk cache for existing PNG or SVG
        if png_path.exists() and png_path.stat().st_size > 0:
            logger.debug(f"[CACHE HIT PNG] {category}/{png_filename} for entity {entity_id}")
            return GenerationResult(
                status="completed",
                image_url=self.get_asset_url(category, png_filename),
                cached=True,
                prompt_used=prompt,
            )
        if svg_path.exists() and svg_path.stat().st_size > 0:
            logger.debug(f"[CACHE HIT SVG] {category}/{svg_filename} for entity {entity_id}")
            return GenerationResult(
                status="completed",
                image_url=self.get_asset_url(category, svg_filename),
                cached=True,
                prompt_used=prompt,
            )

        # 2. Check if API is configured
        setting_key = getattr(settings, "GEMINI_API_KEY", None)
        if self.api_key == "" or setting_key == "":
            api_key = ""
        else:
            api_key = self.api_key or setting_key or os.getenv("GEMINI_API_KEY", "")

        if not api_key or api_key in ("NO_KEY", "your-gemini-key", "") or not GENAI_AVAILABLE:
            placeholder_url = self.get_fallback_placeholder_url(category, subtype)
            return GenerationResult(
                status="fallback",
                image_url=placeholder_url,
                cached=False,
                error="Google GenAI API key not configured. Using fallback placeholder.",
                prompt_used=prompt,
            )

        # Ensure client is created if api_key became available
        if not self._client and GENAI_AVAILABLE:
            try:
                self._client = genai.Client(api_key=api_key)
                self.is_configured = True
            except Exception as e:
                placeholder_url = self.get_fallback_placeholder_url(category, subtype)
                return GenerationResult(
                    status="fallback",
                    image_url=placeholder_url,
                    cached=False,
                    error=f"Client initialization error: {e}",
                    prompt_used=prompt,
                )

        # 3. Deduplicate concurrent requests for identical hash
        loop = asyncio.get_running_loop()
        existing_future: Optional[asyncio.Future] = None
        future: Optional[asyncio.Future] = None

        async with self._get_lock():
            if cache_hash in self._active_tasks:
                cand = self._active_tasks[cache_hash]
                try:
                    cand_loop = cand.get_loop()
                    if cand_loop is loop and not cand.cancelled():
                        logger.debug(f"[DEDUP] Attaching to existing task for {cache_hash}")
                        existing_future = cand
                except Exception:
                    pass

            if existing_future is None:
                future = loop.create_future()
                self._active_tasks[cache_hash] = future

        # Release lock before awaiting existing future to avoid blocking concurrent callers
        if existing_future is not None:
            return await existing_future

        # 4. Execute generation pipeline under semaphore
        try:
            image_url = None
            async with self._get_semaphore():
                logger.info(f"[GENERATE START] {category} for entity {entity_id} (hash={cache_hash})")

                # Strategy A: Try raster diffusion/multimodal generation (works if account has image quota/billing)
                raster_success = False
                try:
                    raw_data = await asyncio.to_thread(
                        self._call_imagen_sync,
                        prompt=prompt,
                        negative_prompt=negative_prompt,
                        aspect_ratio=aspect_ratio,
                    )
                    image_bytes = raw_data
                    if hasattr(raw_data, "generated_images") and raw_data.generated_images:
                        gen_img = raw_data.generated_images[0]
                        if getattr(gen_img, "rai_filtered_reason", None):
                            image_bytes = None
                        else:
                            image_bytes = getattr(gen_img.image, "image_bytes", None)

                    if image_bytes:
                        saved_size = self._save_image_safely(image_bytes, png_path)
                        image_url = self.get_asset_url(category, png_filename)
                        raster_success = True
                        logger.info(f"[GENERATE RASTER COMPLETE] Saved {png_path} ({saved_size} bytes)")
                except Exception as raster_err:
                    logger.info(f"[RASTER NOT AVAILABLE] ({raster_err}). Engaging Free-Tier Gemini Generation.")

                # Strategy B: Free-Tier Gemini Vector Generation
                # When raster models are quota-capped (limit: 0 on free tier) or unavailable,
                # use Gemini text model to synthesize bespoke standalone SVG artwork.
                if not raster_success:
                    svg_content = await asyncio.to_thread(
                        self._generate_svg_via_gemini_sync,
                        prompt=prompt,
                        category=category,
                        aspect_ratio=aspect_ratio,
                    )
                    tmp_svg = svg_path.with_suffix(".tmp")
                    with open(tmp_svg, "w", encoding="utf-8") as f:
                        f.write(svg_content)
                    os.replace(tmp_svg, svg_path)
                    image_url = self.get_asset_url(category, svg_filename)
                    logger.info(f"[GENERATE SVG COMPLETE] Saved {svg_path} ({len(svg_content)} chars)")

            result = GenerationResult(
                status="completed",
                image_url=image_url or self.get_fallback_placeholder_url(category, subtype),
                cached=False,
                prompt_used=prompt,
            )
            if future is not None and not future.done():
                future.set_result(result)
            return result

        except Exception as exc:
            logger.warning(f"[GENERATE FALLBACK] {category} for {entity_id}: {exc}")
            placeholder_url = self.get_fallback_placeholder_url(category, subtype)
            result = GenerationResult(
                status="fallback",
                image_url=placeholder_url,
                cached=False,
                error=str(exc),
                prompt_used=prompt,
            )
            if future is not None and not future.done():
                future.set_result(result)
            return result

        finally:
            if future is not None and not future.done():
                future.cancel()
            async with self._get_lock():
                if future is not None and self._active_tasks.get(cache_hash) is future:
                    self._active_tasks.pop(cache_hash, None)

    @staticmethod
    def _normalize_image_bytes(raw_data: Any) -> bytes:
        """Decode base64, data URIs, or raw bytes into verified binary image bytes."""
        import base64
        if isinstance(raw_data, str):
            if raw_data.startswith("data:image"):
                raw_data = raw_data.split(",", 1)[-1]
            try:
                return base64.b64decode(raw_data)
            except Exception:
                return raw_data.encode("utf-8")
        elif isinstance(raw_data, (bytes, bytearray)):
            if raw_data.startswith(b"data:image"):
                raw_data = raw_data.split(b",", 1)[-1]
                return base64.b64decode(raw_data)
            elif (
                raw_data.startswith(b"iVBORw0KGgo")
                or raw_data.startswith(b"/9j/")
                or raw_data.startswith(b"UklGR")
            ):
                try:
                    return base64.b64decode(raw_data)
                except Exception:
                    pass
            return bytes(raw_data)
        raise ValueError(f"Unsupported image data type: {type(raw_data)}")

    def _save_image_safely(self, image_data: Any, target_path: Path) -> int:
        """Validate and write image to disk, re-encoding via Pillow when available."""
        import io
        raw_bytes = self._normalize_image_bytes(image_data)
        if len(raw_bytes) < 32:
            raise ValueError(f"Image payload too small ({len(raw_bytes)} bytes)")

        tmp_path = target_path.with_suffix(".tmp")
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(raw_bytes))
            img.verify()
            # Re-open for clean PNG output
            img = Image.open(io.BytesIO(raw_bytes))
            img.save(tmp_path, format="PNG")
        except Exception:
            # Fallback if Pillow verification fails: ensure magic header
            if not (
                raw_bytes.startswith(b"\x89PNG\r\n\x1a\n")
                or raw_bytes.startswith(b"\xff\xd8\xff")
                or raw_bytes.startswith(b"RIFF")
            ):
                raise ValueError("Image data failed integrity check: missing PNG/JPEG/WEBP magic bytes")
            with open(tmp_path, "wb") as f:
                f.write(raw_bytes)

        os.replace(tmp_path, target_path)
        return target_path.stat().st_size

    def _call_imagen_sync(self, prompt: str, negative_prompt: str, aspect_ratio: str) -> Optional[bytes]:
        """
        Synchronous GenAI image execution supporting both:
        1. Gemini multimodal image models (e.g. gemini-3.1-flash-lite-image) via generate_content.
        2. Imagen models (e.g. imagen-3.0-generate-002) via generate_images.
        Returns raw image bytes or None.
        """
        if not self._client:
            return None

        # 1. Gemini multimodal image generation (gemini-3.1-flash-lite-image, etc.)
        if "gemini" in self.model.lower() and "image" in self.model.lower():
            response = self._client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(
                        aspect_ratio=aspect_ratio,
                    ),
                ),
            )
            if response and getattr(response, "parts", None):
                for part in response.parts:
                    inline = getattr(part, "inline_data", None)
                    if inline and getattr(inline, "data", None):
                        return inline.data
            if response and getattr(response, "candidates", None) and len(response.candidates) > 0:
                cand = response.candidates[0]
                if getattr(cand, "content", None) and getattr(cand.content, "parts", None):
                    for part in cand.content.parts:
                        inline = getattr(part, "inline_data", None)
                        if inline and getattr(inline, "data", None):
                            return inline.data
            return None

        # 2. Legacy Imagen generation
        response = self._client.models.generate_images(
            model=self.model,
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio=aspect_ratio,
                output_mime_type="image/png",
                person_generation="allow_adult",
                safety_filter_level="block_medium_and_above",
            ),
        )
        if response and getattr(response, "generated_images", None) and len(response.generated_images) > 0:
            gen_img = response.generated_images[0]
            if not getattr(gen_img, "rai_filtered_reason", None):
                return getattr(gen_img.image, "image_bytes", None)
        return None

    def _generate_svg_via_gemini_sync(self, prompt: str, category: str, aspect_ratio: str = "1:1") -> str:
        """
        Synthesizes a bespoke, high-quality standalone SVG vector illustration
        using the Gemini text model. Fully compatible with free tier tokens.
        """
        import re
        import xml.etree.ElementTree as ET

        viewbox = "0 0 800 450" if aspect_ratio == "16:9" else "0 0 512 512"
        sys_prompt = (
            f"You are a professional graphic artist and illustrator for a dark fantasy tabletop RPG.\n"
            f"Generate a beautiful, standalone SVG graphic illustration for a {category} asset.\n"
            f"STRICT REQUIREMENTS:\n"
            f"1. Output ONLY valid XML starting with <svg and ending with </svg>.\n"
            f"2. Do NOT include markdown code fences, backticks, or explanatory text.\n"
            f"3. Must specify viewBox='{viewbox}' and xmlns='http://www.w3.org/2000/svg'.\n"
            f"4. Craft a cohesive aesthetic with rich gradients, dark fantasy palettes, layered silhouettes, and distinct vector shapes.\n"
        )

        text_model = getattr(settings, "GEMINI_MODEL", "gemini-3.5-flash-lite")
        if text_model in ("gemini-2.5-flash",):
            text_model = "gemini-3.1-flash-lite"

        response = self._client.models.generate_content(
            model=text_model,
            contents=f"{sys_prompt}\nAsset Subject & Description:\n{prompt}",
        )
        raw_text = (response.text or "").strip()
        match = re.search(r"<svg.*?</svg>", raw_text, re.DOTALL)
        if not match:
            raise ValueError("Gemini response did not contain a valid <svg>...</svg> element")

        svg_content = match.group(0)
        # Validate XML well-formedness
        ET.fromstring(svg_content)
        return svg_content


# Global singleton instance
image_gen_service = ImageGenService()
