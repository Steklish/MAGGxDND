from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class CharacterProfileBase(BaseModel):
    """Base character profile schema."""
    alignment: str = Field(default="True Neutral")
    deity: Optional[str] = None
    homeland: Optional[str] = None
    background: Optional[str] = None
    appearance_description: str = Field(default="")
    hit_dice: str = Field(default="1d10")
    proficiency_bonus: int = Field(default=2)
    inspiration: bool = Field(default=False)
    passive_wisdom: int = Field(default=10)


class CharacterProfileCreate(CharacterProfileBase):
    """Schema for creating a character profile."""
    character_id: int


class CharacterProfileUpdate(BaseModel):
    """Schema for updating a character profile."""
    portrait_url: Optional[str] = None
    background_image_url: Optional[str] = None
    appearance_description: Optional[str] = None
    alignment: Optional[str] = None
    deity: Optional[str] = None
    homeland: Optional[str] = None
    background: Optional[str] = None
    hit_dice: Optional[str] = None
    proficiency_bonus: Optional[int] = None
    inspiration: Optional[bool] = None
    passive_wisdom: Optional[int] = None
    saving_throws: Optional[Dict[str, int]] = None
    skills: Optional[Dict[str, int]] = None
    attacks: Optional[List[Dict[str, Any]]] = None
    spell_slots: Optional[Dict[str, int]] = None
    equipment: Optional[List[Dict[str, Any]]] = None
    features_traits: Optional[List[str]] = None
    notes: Optional[str] = None
    journal: Optional[str] = None


class CharacterProfileInDB(CharacterProfileBase):
    """Character profile in database."""
    id: int
    character_id: int
    portrait_url: Optional[str] = None
    background_image_url: Optional[str] = None
    saving_throws: str  # JSON string
    skills: str  # JSON string
    attacks: str  # JSON string
    spell_slots: str  # JSON string
    equipment: str  # JSON string
    features_traits: str  # JSON string
    notes: Optional[str] = None
    journal: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
