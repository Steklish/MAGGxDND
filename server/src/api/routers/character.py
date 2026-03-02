from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from server.src.database.session import get_db
from server.src.services import character_service
from server.src.schema.character import CharacterCreate, CharacterUpdate, CharacterInDB

router = APIRouter(prefix="/characters", tags=["characters"])


@router.post("/", response_model=CharacterInDB)
def create_character(character: CharacterCreate, db: Session = Depends(get_db)):
    """
    Create a new character for a user.
    """
    try:
        return character_service.create_character(db, character)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{character_id}", response_model=CharacterInDB)
def get_character(character_id: int, db: Session = Depends(get_db)):
    """
    Get a character by ID.
    """
    db_character = character_service.get_character(db, character_id)
    if db_character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    return db_character


@router.get("/user/{user_id}", response_model=List[CharacterInDB])
def get_user_characters(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get all characters for a specific user.
    """
    return character_service.get_characters_by_user(db, user_id, skip=skip, limit=limit)


@router.put("/{character_id}", response_model=CharacterInDB)
def update_character(character_id: int, character: CharacterUpdate, db: Session = Depends(get_db)):
    """
    Update a character by ID.
    """
    updated_character = character_service.update_character(db, character_id, character)
    if updated_character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    return updated_character


@router.delete("/{character_id}")
def delete_character(character_id: int, db: Session = Depends(get_db)):
    """
    Delete a character by ID.
    """
    success = character_service.delete_character(db, character_id)
    if not success:
        raise HTTPException(status_code=404, detail="Character not found")
    return {"message": "Character deleted successfully"}
