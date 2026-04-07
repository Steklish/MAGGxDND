"""
Character Profile Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class CharacterProfileCreate(BaseModel):
    """Schema for creating a character profile."""
    name: str = Field(..., min_length=1, max_length=100)
    race: str = Field(default="Human", max_length=50)
    char_class: str = Field(..., max_length=50)
    level: int = Field(default=1, ge=1, le=20)
    
    # Full character data (optional - can be generated from basic info)
    character_data: Optional[Dict[str, Any]] = None
    
    # Descriptive fields
    backstory_summary: Optional[str] = Field(None, max_length=2000)
    personality_traits: Optional[List[str]] = None
    appearance_description: Optional[str] = Field(None, max_length=2000)
    background: Optional[str] = Field(None, max_length=100)
    alignment: Optional[str] = Field(None, max_length=50)
    
    # Computed stats
    max_hp: int = Field(default=10, ge=1)
    armor_class: int = Field(default=10)
    speed: int = Field(default=30)
    
    is_favorite: bool = False


class CharacterProfileUpdate(BaseModel):
    """Schema for updating a character profile."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    backstory_summary: Optional[str] = Field(None, max_length=2000)
    appearance_description: Optional[str] = Field(None, max_length=2000)
    is_favorite: Optional[bool] = None
    character_data: Optional[Dict[str, Any]] = None


class CharacterProfileResponse(BaseModel):
    """Response schema for character profile."""
    id: int
    user_id: int
    name: str
    race: str
    char_class: str
    level: int
    backstory_summary: Optional[str] = None
    personality_traits: Optional[List[str]] = None
    appearance_description: Optional[str] = None
    background: Optional[str] = None
    alignment: Optional[str] = None
    max_hp: int
    armor_class: int
    speed: int
    is_favorite: bool
    character_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CharacterProfileListResponse(BaseModel):
    """Schema for listing character profiles."""
    profiles: List[CharacterProfileResponse]
    total: int
