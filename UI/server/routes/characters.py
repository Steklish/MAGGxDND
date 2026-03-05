"""
Character management REST API endpoints
"""

import logging
import os
import sys
import uuid
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

logger = logging.getLogger("game_server.characters")

router = APIRouter()

# In-memory character storage
characters_db: Dict[int, dict] = {}
profiles_db: Dict[int, dict] = {}


# Request/Response models
class CharacterCreateRequest(BaseModel):
    user_id: int
    name: str
    race: str = "Human"
    char_class: str = "Fighter"
    level: int = 1
    backstory_summary: Optional[str] = None
    personality_traits: List[str] = []


class CharacterResponse(BaseModel):
    id: int
    user_id: int
    name: str
    race: str
    char_class: str
    level: int
    created_at: float


class CharacterProfile(BaseModel):
    id: int
    character_id: int
    name: str
    race: str
    char_class: str
    level: int
    alignment: str = "True Neutral"
    background: Optional[str] = None
    appearance_description: str = ""
    max_hp: int = 10
    current_hp: int = 10
    armor_class: int = 10
    speed: int = 30
    stats: Dict[str, int] = {}


class CharacterProfileCreateRequest(BaseModel):
    character_id: int
    name: str
    race: str
    char_class: str
    level: int = 1
    alignment: str = "True Neutral"
    background: Optional[str] = None
    appearance_description: str = ""
    max_hp: int = 10
    current_hp: int = 10
    armor_class: int = 10
    speed: int = 30
    stats: Optional[Dict[str, int]] = None


@router.get("/characters/user/{user_id}", response_model=List[CharacterResponse])
async def get_user_characters(user_id: int):
    """Get all characters for a user."""
    logger.info(f"Getting characters for user {user_id}")
    
    user_characters = [
        char for char in characters_db.values()
        if char["user_id"] == user_id
    ]
    
    return [
        CharacterResponse(
            id=char["id"],
            user_id=char["user_id"],
            name=char["name"],
            race=char["race"],
            char_class=char["char_class"],
            level=char["level"],
            created_at=char["created_at"]
        )
        for char in user_characters
    ]


@router.post("/characters", response_model=CharacterResponse)
async def create_character(request: CharacterCreateRequest):
    """Create a new character."""
    logger.info(f"Creating character: {request.name} for user {request.user_id}")
    
    character_id = len(characters_db) + 1
    
    character_data = {
        "id": character_id,
        "user_id": request.user_id,
        "name": request.name,
        "race": request.race,
        "char_class": request.char_class,
        "level": request.level,
        "backstory_summary": request.backstory_summary,
        "personality_traits": request.personality_traits,
        "created_at": __import__('time').time()
    }
    
    characters_db[character_id] = character_data
    
    logger.info(f"Character created: {character_id}")
    
    return CharacterResponse(
        id=character_id,
        user_id=request.user_id,
        name=request.name,
        race=request.race,
        char_class=request.char_class,
        level=request.level,
        created_at=character_data["created_at"]
    )


@router.get("/characters/{character_id}", response_model=CharacterResponse)
async def get_character(character_id: int):
    """Get character by ID."""
    if character_id not in characters_db:
        raise HTTPException(status_code=404, detail="Character not found")
    
    char = characters_db[character_id]
    
    return CharacterResponse(
        id=char["id"],
        user_id=char["user_id"],
        name=char["name"],
        race=char["race"],
        char_class=char["char_class"],
        level=char["level"],
        created_at=char["created_at"]
    )


@router.delete("/characters/{character_id}")
async def delete_character(character_id: int):
    """Delete a character."""
    if character_id not in characters_db:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Also delete profile if exists
    if character_id in profiles_db:
        del profiles_db[character_id]
    
    del characters_db[character_id]
    
    logger.info(f"Character deleted: {character_id}")
    return {"status": "deleted", "character_id": character_id}


@router.get("/profiles/character/{character_id}", response_model=CharacterProfile)
async def get_character_profile(character_id: int):
    """Get character profile."""
    if character_id not in profiles_db:
        # Create default profile if doesn't exist
        if character_id not in characters_db:
            raise HTTPException(status_code=404, detail="Character not found")
        
        char = characters_db[character_id]
        default_profile = {
            "id": character_id,
            "character_id": character_id,
            "name": char["name"],
            "race": char["race"],
            "char_class": char["char_class"],
            "level": char["level"],
            "alignment": "True Neutral",
            "background": None,
            "appearance_description": "",
            "max_hp": 10,
            "current_hp": 10,
            "armor_class": 10,
            "speed": 30,
            "stats": {
                "strength": 10,
                "dexterity": 10,
                "constitution": 10,
                "intelligence": 10,
                "wisdom": 10,
                "charisma": 10
            }
        }
        profiles_db[character_id] = default_profile
    
    return CharacterProfile(**profiles_db[character_id])


@router.post("/profiles", response_model=CharacterProfile)
async def create_character_profile(request: CharacterProfileCreateRequest):
    """Create character profile."""
    logger.info(f"Creating profile for character {request.character_id}")
    
    if request.character_id not in characters_db:
        raise HTTPException(status_code=404, detail="Character not found")
    
    profile_data = {
        "id": request.character_id,
        "character_id": request.character_id,
        "name": request.name,
        "race": request.race,
        "char_class": request.char_class,
        "level": request.level,
        "alignment": request.alignment,
        "background": request.background,
        "appearance_description": request.appearance_description,
        "max_hp": request.max_hp,
        "current_hp": request.current_hp,
        "armor_class": request.armor_class,
        "speed": request.speed,
        "stats": request.stats or {
            "strength": 10,
            "dexterity": 10,
            "constitution": 10,
            "intelligence": 10,
            "wisdom": 10,
            "charisma": 10
        }
    }
    
    profiles_db[request.character_id] = profile_data
    
    logger.info(f"Profile created for character {request.character_id}")
    
    return CharacterProfile(**profile_data)


@router.put("/profiles/character/{character_id}", response_model=CharacterProfile)
async def update_character_profile(character_id: int, request: CharacterProfileCreateRequest):
    """Update character profile."""
    if character_id not in profiles_db:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile_data = {
        "id": character_id,
        "character_id": character_id,
        "name": request.name,
        "race": request.race,
        "char_class": request.char_class,
        "level": request.level,
        "alignment": request.alignment,
        "background": request.background,
        "appearance_description": request.appearance_description,
        "max_hp": request.max_hp,
        "current_hp": request.current_hp,
        "armor_class": request.armor_class,
        "speed": request.speed,
        "stats": request.stats or profiles_db[character_id]["stats"]
    }
    
    profiles_db[character_id] = profile_data
    
    logger.info(f"Profile updated for character {character_id}")
    
    return CharacterProfile(**profile_data)


@router.delete("/profiles/character/{character_id}")
async def delete_character_profile(character_id: int):
    """Delete character profile."""
    if character_id not in profiles_db:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    del profiles_db[character_id]
    
    logger.info(f"Profile deleted for character {character_id}")
    return {"status": "deleted", "character_id": character_id}
