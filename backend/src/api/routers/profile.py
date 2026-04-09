"""
Character Profile API router

Handles character profile creation for the /profiles/ prefix.
This provides compatibility with frontend code that calls /api/v1/profiles/
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import ValidationError

from backend.src.database.session import get_db
from backend.src.auth.dependencies import get_current_user
from backend.src.models.user import User
from backend.src.repositories.character_profile_repository import CharacterProfileRepository
from backend.src.schema.character_profile import CharacterProfileCreate, CharacterProfileResponse

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.post("/", response_model=CharacterProfileResponse, status_code=201)
async def create_profile(
    profile_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a character profile.
    
    Accepts flexible dict data from frontend and saves to character_profiles table.
    """
    repo = CharacterProfileRepository(db)

    # Extract fields with defaults
    created = repo.create(
        user_id=current_user.id,
        name=profile_data.get('name', 'Unnamed Character'),
        race=profile_data.get('race', 'Human'),
        char_class=profile_data.get('char_class', 'Fighter'),
        level=profile_data.get('level', 1),
        character_data=profile_data.get('character_data'),
        backstory_summary=profile_data.get('backstory_summary'),
        personality_traits=profile_data.get('personality_traits'),
        appearance_description=profile_data.get('appearance_description'),
        background=profile_data.get('background'),
        alignment=profile_data.get('alignment'),
        max_hp=profile_data.get('max_hp', 10),
        armor_class=profile_data.get('armor_class', 10),
        speed=profile_data.get('speed', 30),
        is_favorite=profile_data.get('is_favorite', False)
    )

    return CharacterProfileResponse(
        id=created.id,
        user_id=created.user_id,
        name=created.name,
        race=created.race,
        char_class=created.char_class,
        level=created.level,
        character_data=created.character_data,
        backstory_summary=created.backstory_summary,
        personality_traits=created.personality_traits,
        appearance_description=created.appearance_description,
        background=created.background,
        alignment=created.alignment,
        max_hp=created.max_hp,
        armor_class=created.armor_class,
        speed=created.speed,
        is_favorite=bool(created.is_favorite),
        created_at=created.created_at,
        updated_at=created.updated_at
    )
