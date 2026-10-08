"""
backend/src/api/routers/assets_router.py

Assets REST Router for MAGGxDND.
Endpoints for asset system status, cached asset listing,
individual asset metadata, generation triggers, and procedural graphics.
"""
from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Optional, Any

from backend.src.services.asset_manager import asset_manager
from backend.src.services.image_gen_service import image_gen_service
from backend.src.config import settings

router = APIRouter(prefix="/assets", tags=["Assets"])


# ===================================================================
# SCHEMAS
# ===================================================================

class AssetItem(BaseModel):
    filename: str
    category: str
    url: str
    api_url: str
    size_bytes: int
    mime_type: str
    modified_at: str
    is_placeholder: bool


class AssetListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[AssetItem]


class CategoryStats(BaseModel):
    file_count: int
    size_bytes: int
    directory_exists: bool


class AssetStatusResponse(BaseModel):
    status: str
    storage_path: str
    total_files: int
    total_size_bytes: int
    total_size_mb: float
    categories: Dict[str, CategoryStats]


class AssetGenerateRequest(BaseModel):
    entity_type: Literal["character", "item", "scene", "battlemap"]
    entity_id: str
    description: Optional[str] = ""
    metadata: Optional[Dict[str, Any]] = None
    prompt_override: Optional[str] = None
    subtype: Optional[str] = None
    force: bool = False


class AssetGenerateResponse(BaseModel):
    status: Literal["completed", "processing", "fallback", "failed"]
    image_url: str
    cached: bool
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    message: Optional[str] = None


class ProceduralAvatarRequest(BaseModel):
    name: str
    char_class: str = "Warrior"
    race: str = "Human"


class ProceduralBattlemapRequest(BaseModel):
    width: int = Field(default=10, ge=4, le=50)
    height: int = Field(default=10, ge=4, le=50)
    cell_size: int = Field(default=60, ge=20, le=200)
    title: str = "BATTLEFIELD"


# ===================================================================
# ENDPOINTS
# ===================================================================

@router.get("/status", response_model=AssetStatusResponse, summary="Retrieve asset subsystem status")
async def get_asset_status():
    """Returns disk usage, file counts per category, and directory health."""
    return asset_manager.get_storage_stats()


@router.get("/status/{category}/{filename}", response_model=AssetItem, summary="Get metadata for a specific asset")
async def get_asset_info(category: str, filename: str):
    """Retrieve metadata (size, MIME type, URL) for an individual asset."""
    if category not in asset_manager.categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category '{category}'. Allowed: {asset_manager.categories}"
        )
    if not asset_manager.asset_exists(category, filename):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset '{filename}' not found in category '{category}'"
        )
    path = asset_manager.get_asset_path(category, filename)
    stat = path.stat()
    mime, _ = __import__("mimetypes").guess_type(filename)
    return AssetItem(
        filename=filename,
        category=category,
        url=asset_manager.get_asset_url(category, filename),
        api_url=asset_manager.get_api_asset_url(category, filename),
        size_bytes=stat.st_size,
        mime_type=mime or "application/octet-stream",
        modified_at=__import__("datetime").datetime.fromtimestamp(stat.st_mtime, tz=__import__("datetime").timezone.utc).isoformat(),
        is_placeholder=(category == "placeholders")
    )


@router.get("/list", response_model=AssetListResponse, summary="List cached assets with pagination")
async def list_cached_assets(
    category: Optional[Literal["characters", "items", "scenes", "maps", "placeholders"]] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List assets stored on disk, optionally filtered by category."""
    items, total = asset_manager.list_assets(category=category, limit=limit, offset=offset)
    return AssetListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[AssetItem(**item) for item in items]
    )


@router.post("/generate", response_model=AssetGenerateResponse, summary="Generate or retrieve visual asset")
async def generate_asset(request: AssetGenerateRequest):
    """
    Generate or retrieve a visual asset for an entity.
    Respects deterministic disk cache, uses google-genai when configured,
    and seamlessly falls back to thematic SVGs.
    """
    result = await image_gen_service.generate_for_entity(
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        description=request.description or "",
        metadata=request.metadata,
        prompt_override=request.prompt_override,
        subtype=request.subtype,
    )

    return AssetGenerateResponse(
        status=result.status,  # type: ignore
        image_url=result.image_url,
        cached=result.cached,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        message=result.error or ("Cached asset returned" if result.cached else "Generated asset"),
    )


@router.post("/regenerate", response_model=AssetGenerateResponse, summary="Trigger asset regeneration")
async def regenerate_asset(request: AssetGenerateRequest):
    """Alias for /generate with force flag."""
    request.force = True
    return await generate_asset(request)


@router.post("/seed-placeholders", summary="Seed standard SVG fallback placeholders")
async def seed_placeholders():
    """Ensure all standard bundled SVG files exist in data/assets/placeholders/."""
    count = asset_manager.seed_default_placeholders()
    return {"status": "ok", "seeded_count": count}


@router.post("/procedural/avatar", summary="Generate procedural SVG avatar")
async def generate_procedural_avatar_endpoint(request: ProceduralAvatarRequest):
    """Generate dynamic SVG monogram avatar."""
    svg = asset_manager.generate_procedural_avatar(request.name, request.char_class, request.race)
    return Response(content=svg, media_type="image/svg+xml")


@router.post("/procedural/battlemap", summary="Generate procedural SVG tactical battlemap")
async def generate_procedural_battlemap_endpoint(request: ProceduralBattlemapRequest):
    """Generate dynamic SVG grid battlemap."""
    svg = asset_manager.generate_procedural_battlemap(
        width=request.width,
        height=request.height,
        cell_size=request.cell_size,
        title=request.title
    )
    return Response(content=svg, media_type="image/svg+xml")
