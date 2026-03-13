"""
Compendium API Router
Endpoints for accessing D&D Beyond style encyclopedia
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from backend.src.database.session import get_db
from backend.src.services.compendium_service import CompendiumService
from backend.src.auth.dependencies import get_current_user
from backend.src.logging import get_logger

logger = get_logger('api.compendium')

router = APIRouter(prefix="/compendium", tags=["compendium"])


# Category Endpoints

@router.get("/categories", response_model=List[Dict[str, Any]])
async def get_all_categories(
    db: Session = Depends(get_db),
    include_entries: bool = Query(False, description="Include entries in each category")
):
    """
    Get all compendium categories
    
    Returns the main categories like Spells, Items, Monsters, etc.
    """
    service = CompendiumService(db)
    return service.get_all_categories(include_entries=include_entries)


@router.get("/categories/{category_id}", response_model=Dict[str, Any])
async def get_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Get category details with subcategories and entries
    """
    service = CompendiumService(db)
    category = service.get_category_by_id(category_id)
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return category


# Search Endpoint

@router.get("/search", response_model=Dict[str, Any])
async def search_compendium(
    q: str = Query(..., min_length=2, description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    type: Optional[str] = Query(None, description="Filter by entry type"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    Search the compendium
    
    Searches through spells, items, monsters, rules, and more.
    Supports filtering by category and type.
    """
    service = CompendiumService(db)
    results = service.search_entries(
        query=q,
        category=category,
        entry_type=type,
        limit=limit,
        offset=offset
    )
    
    return results


# Entry Endpoints

@router.get("/entries/{entry_id}", response_model=Dict[str, Any])
async def get_entry(
    entry_id: int,
    db: Session = Depends(get_db)
):
    """
    Get full details of a compendium entry
    
    Includes complete description, metadata, ratings, etc.
    """
    service = CompendiumService(db)
    entry = service.get_entry_by_id(entry_id)
    
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    return entry


@router.get("/entries", response_model=List[Dict[str, Any]])
async def get_entries_by_type(
    type: str = Query(..., description="Entry type (spell, item, monster, etc.)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get all entries of a specific type
    
    Example: Get all spells, all items, all monsters
    """
    service = CompendiumService(db)
    return service.get_entries_by_type(entry_type=type, limit=limit, offset=offset)


# Rating Endpoints

@router.post("/entries/{entry_id}/rating")
async def rate_entry(
    entry_id: int,
    rating: int = Query(..., ge=1, le=5),
    comment: str = Query("", max_length=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Rate a compendium entry (1-5 stars)
    
    Users can rate entries and optionally leave a comment.
    Each user can only rate once (can update their rating).
    """
    service = CompendiumService(db)
    
    user_id = current_user.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return service.add_rating(
        entry_id=entry_id,
        user_id=user_id,
        rating=rating,
        comment=comment
    )


# Comment Endpoints

@router.post("/entries/{entry_id}/comments")
async def add_comment(
    entry_id: int,
    content: str,
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Add a comment to a compendium entry
    
    Supports threaded comments (reply to existing comments).
    """
    service = CompendiumService(db)
    
    user_id = current_user.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if len(content) < 1 or len(content) > 2000:
        raise HTTPException(
            status_code=400,
            detail="Comment must be between 1 and 2000 characters"
        )
    
    return service.add_comment(
        entry_id=entry_id,
        user_id=user_id,
        content=content,
        parent_id=parent_id
    )


# Homebrew Endpoints

@router.post("/homebrew")
async def create_homebrew(
    homebrew_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create homebrew content
    
    Homebrew can be spells, items, races, classes, etc.
    Can be kept private or published to the community.
    """
    service = CompendiumService(db)
    
    user_id = current_user.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Validate required fields
    if 'name' not in homebrew_data or 'type' not in homebrew_data:
        raise HTTPException(
            status_code=400,
            detail="name and type are required"
        )
    
    return service.create_homebrew(user_id=user_id, data=homebrew_data)


@router.get("/homebrew/me", response_model=List[Dict[str, Any]])
async def get_my_homebrew(
    include_public: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get your homebrew content
    """
    service = CompendiumService(db)
    
    user_id = current_user.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return service.get_user_homebrew(user_id=user_id, include_public=include_public)


# Quick Access Endpoints

@router.get("/spells", response_model=List[Dict[str, Any]])
async def get_spells(
    level: Optional[int] = Query(None, ge=0, le=9),
    school: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Quick access to spells
    
    Can filter by level and school of magic.
    """
    service = CompendiumService(db)
    spells = service.get_entries_by_type(entry_type='spell', limit=limit)
    
    # Apply additional filters
    if level is not None:
        spells = [s for s in spells if s.get('metadata', {}).get('level') == level]
    
    if school:
        spells = [s for s in spells if s.get('metadata', {}).get('school') == school]
    
    return spells


@router.get("/items", response_model=List[Dict[str, Any]])
async def get_items(
    rarity: Optional[str] = Query(None),
    item_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Quick access to items
    """
    service = CompendiumService(db)
    items = service.get_entries_by_type(entry_type='item', limit=limit)
    
    # Apply additional filters
    if rarity:
        items = [i for i in items if i.get('metadata', {}).get('rarity') == rarity]
    
    if item_type:
        items = [i for i in items if i.get('metadata', {}).get('type') == item_type]
    
    return items


@router.get("/monsters", response_model=List[Dict[str, Any]])
async def get_monsters(
    challenge_rating: Optional[float] = Query(None),
    monster_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Quick access to monsters
    """
    service = CompendiumService(db)
    monsters = service.get_entries_by_type(entry_type='monster', limit=limit)
    
    # Apply additional filters
    if challenge_rating is not None:
        monsters = [m for m in monsters if m.get('metadata', {}).get('challenge_rating') == challenge_rating]
    
    if monster_type:
        monsters = [m for m in monsters if m.get('metadata', {}).get('type') == monster_type]
    
    return monsters


@router.get("/random/spell")
async def get_random_spell(
    level: Optional[int] = Query(None, ge=0, le=9),
    db: Session = Depends(get_db)
):
    """
    Get a random spell (optionally by level)
    
    Useful for random encounters or inspiration.
    """
    import random
    
    service = CompendiumService(db)
    spells = service.get_entries_by_type(entry_type='spell', limit=100)
    
    if level is not None:
        spells = [s for s in spells if s.get('metadata', {}).get('level') == level]
    
    if not spells:
        raise HTTPException(status_code=404, detail="No spells found")
    
    return random.choice(spells)


@router.get("/random/item")
async def get_random_item(
    rarity: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get a random item
    """
    import random
    
    service = CompendiumService(db)
    items = service.get_entries_by_type(entry_type='item', limit=100)
    
    if rarity:
        items = [i for i in items if i.get('metadata', {}).get('rarity') == rarity]
    
    if not items:
        raise HTTPException(status_code=404, detail="No items found")
    
    return random.choice(items)
