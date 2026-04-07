# type: ignore[reportGeneralTypeIssues, reportAttributeAccessIssue, reportArgumentType, reportUndefinedVariable, reportCallIssue]
"""
Character Profile router

Handles user's saved character profiles (templates) that can be reused across sessions.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.orm import Session

from backend.src.database.session import get_db
from backend.src.auth.dependencies import get_current_user
from backend.src.models.user import User
from backend.src.repositories.character_profile_repository import CharacterProfileRepository
from backend.src.schema.character_profile import (
    CharacterProfileCreate,
    CharacterProfileUpdate,
    CharacterProfileResponse,
    CharacterProfileListResponse
)

router = APIRouter(prefix="/characters", tags=["characters"])


def get_character_repo(db: Session = Depends(get_db)) -> CharacterProfileRepository:
    return CharacterProfileRepository(db)


@router.post("/", response_model=CharacterProfileResponse, status_code=201)
async def create_character_profile(
    profile: CharacterProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Save a character profile for future use.
    
    This allows users to create characters that can be reused across multiple game sessions.
    """
    repo = get_character_repo(db)
    
    created = repo.create(
        user_id=current_user.id,
        name=profile.name,
        race=profile.race,
        char_class=profile.char_class,
        character_data=profile.character_data,
        backstory_summary=profile.backstory_summary,
        personality_traits=profile.personality_traits,
        appearance_description=profile.appearance_description,
        background=profile.background,
        alignment=profile.alignment,
        max_hp=profile.max_hp,
        armor_class=profile.armor_class,
        speed=profile.speed,
        is_favorite=profile.is_favorite
    )
    
    return created


@router.get("/", response_model=CharacterProfileListResponse)
async def list_character_profiles(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all saved character profiles for the current user."""
    repo = get_character_repo(db)
    profiles = repo.get_by_user(current_user.id, skip=skip, limit=limit)
    
    # Count total for pagination
    total = len(repo.get_by_user(current_user.id, skip=0, limit=10000))
    
    return CharacterProfileListResponse(
        profiles=[CharacterProfileResponse.model_validate(p) for p in profiles],
        total=total
    )


@router.get("/{profile_id}", response_model=CharacterProfileResponse)
async def get_character_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific character profile."""
    repo = get_character_repo(db)
    profile = repo.get_by_id(profile_id, current_user.id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Character profile not found")
    
    return profile


@router.put("/{profile_id}", response_model=CharacterProfileResponse)
async def update_character_profile(
    profile_id: int,
    updates: CharacterProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a character profile."""
    repo = get_character_repo(db)
    
    update_dict = updates.model_dump(exclude_unset=True)
    if not update_dict:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    updated = repo.update(profile_id, current_user.id, **update_dict)
    
    if not updated:
        raise HTTPException(status_code=404, detail="Character profile not found")
    
    return updated


@router.delete("/{profile_id}", status_code=204)
async def delete_character_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a character profile."""
    repo = get_character_repo(db)
    deleted = repo.delete(profile_id, current_user.id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Character profile not found")
    
    return None
