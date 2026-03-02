from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json

from server.src.database.session import get_db
from server.src.services import character_profile_service
from server.src.schema.character_profile import CharacterProfileCreate, CharacterProfileUpdate, CharacterProfileInDB

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/character/{character_id}", response_model=CharacterProfileInDB)
def get_character_profile(character_id: int, db: Session = Depends(get_db)):
    """Get character profile by character ID."""
    profile = character_profile_service.get_by_character_id(db, character_id)
    if profile is None:
        # Create default profile if doesn't exist
        create_data = CharacterProfileCreate(character_id=character_id)
        profile = character_profile_service.create_profile(db, create_data)
    return profile


@router.post("/", response_model=CharacterProfileInDB)
def create_character_profile(profile: CharacterProfileCreate, db: Session = Depends(get_db)):
    """Create a new character profile."""
    return character_profile_service.create_profile(db, profile)


@router.put("/{profile_id}", response_model=CharacterProfileInDB)
def update_character_profile(profile_id: int, profile: CharacterProfileUpdate, db: Session = Depends(get_db)):
    """Update a character profile."""
    updated = character_profile_service.update_profile(db, profile_id, profile)
    if updated is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return updated


@router.put("/character/{character_id}", response_model=CharacterProfileInDB)
def update_character_profile_by_char_id(character_id: int, profile: CharacterProfileUpdate, db: Session = Depends(get_db)):
    """Update character profile by character ID."""
    updated = character_profile_service.update_by_character_id(db, character_id, profile)
    if updated is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return updated
