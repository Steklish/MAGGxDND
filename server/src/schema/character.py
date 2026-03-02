from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from server.src.schema.user import UserInDB


class CharacterBase(BaseModel):
    """Base character schema."""
    name: str = Field(..., description="Character name")
    race: str = Field(default="Human")
    char_class: str = Field(default="Fighter")
    level: int = Field(default=1)
    backstory_summary: str = Field(default="")
    personality_traits: str = Field(default="")


class CharacterCreate(CharacterBase):
    """Schema for creating a character."""
    user_id: int
    max_hp: int = Field(default=30)
    current_hp: int = Field(default=30)
    armor_class: int = Field(default=12)
    speed: int = Field(default=30)
    stats: Dict[str, int] = Field(default_factory=lambda: {
        "strength": 15,
        "dexterity": 12,
        "constitution": 14,
        "intelligence": 10,
        "wisdom": 10,
        "charisma": 10
    })
    abilities: List[Dict[str, Any]] = Field(default_factory=list)
    inventory: List[Dict[str, Any]] = Field(default_factory=list)


class CharacterUpdate(BaseModel):
    """Schema for updating a character."""
    name: Optional[str] = None
    race: Optional[str] = None
    char_class: Optional[str] = None
    level: Optional[int] = None
    backstory_summary: Optional[str] = None
    personality_traits: Optional[str] = None
    max_hp: Optional[int] = None
    current_hp: Optional[int] = None
    temp_hp: Optional[int] = None
    armor_class: Optional[int] = None
    speed: Optional[int] = None
    stats: Optional[Dict[str, int]] = None
    abilities: Optional[List[Dict[str, Any]]] = None
    inventory: Optional[List[Dict[str, Any]]] = None
    active_conditions: Optional[str] = None
    resources: Optional[str] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    is_alive: Optional[bool] = None


class CharacterInDB(CharacterBase):
    """Character schema in database."""
    id: int
    user_id: int
    level: int
    max_hp: int
    current_hp: int
    temp_hp: int
    armor_class: int
    speed: int
    stats: str  # JSON string
    inventory: str  # JSON string
    abilities: str  # JSON string
    active_conditions: str  # JSON string
    resources: str  # JSON string
    position_x: float
    position_y: float
    proficiency_bonus: int
    is_alive: bool
    initiative_bonus: int
    short_summary: str

    class Config:
        from_attributes = True


class CharacterWithUser(CharacterInDB):
    """Character schema with user info."""
    user: Optional[UserInDB] = None
