from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TokenData(BaseModel):
    username: str | None = None
    user_id: Optional[int] = None
    is_guest: bool = False

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_at: Optional[datetime] = None
    is_guest: bool = False

class GuestToken(BaseModel):
    """Token for guest (unauthorized) users."""
    access_token: str
    token_type: str = "bearer"
    guest_id: str
    expires_at: datetime
    is_guest: bool = True

class AuthResponse(BaseModel):
    """Response for authentication endpoints."""
    access_token: str
    token_type: str
    user_id: Optional[int] = None
    username: Optional[str] = None
    is_guest: bool = False
    expires_at: Optional[datetime] = None