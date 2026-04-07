"""
Character Profile API router - DEPRECATED

Profile data is now stored in session_data JSON field.
This router is kept for backward compatibility only.
"""
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.post("/")
async def create_profile():
    """DEPRECATED: Profiles are now stored in session_data JSON."""
    raise HTTPException(
        status_code=410,
        detail="Profile creation is now handled through session data. Use the session endpoints instead."
    )


@router.get("/character/{character_id}")
async def get_character_profile(character_id: int):
    """DEPRECATED: Profile data is now in session_data JSON."""
    raise HTTPException(
        status_code=410,
        detail="Profile data is now stored in session data. Use /sessions/{session_id}/game_info instead."
    )


@router.put("/character/{character_id}")
async def update_character_profile(character_id: int):
    """DEPRECATED: Profile updates now go through session_data."""
    raise HTTPException(
        status_code=410,
        detail="Profile updates are now handled through session data. Use the session endpoints instead."
    )
