"""
Authentication REST API endpoints
"""

import logging
import os
import sys
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

logger = logging.getLogger("game_server.auth")

router = APIRouter()

# In-memory user storage
users_db: dict = {}
tokens_db: dict = {}

# Simple token secret (in production, use environment variable)
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# Request/Response models
class UserCreate(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    group_id: Optional[int] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_user_by_username(username: str):
    """Get user by username."""
    for user in users_db.values():
        if user["username"] == username:
            return user
    return None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create access token (simplified - in production use JWT)."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Simplified token generation (in production use proper JWT)
    token = str(uuid.uuid4())
    tokens_db[token] = to_encode
    
    return token


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from token."""
    if token not in tokens_db:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_data = tokens_db[token]
    username = user_data.get("sub")
    
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


@router.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate):
    """Create a new user."""
    logger.info(f"Creating user: {user.username}")
    
    # Check if user already exists
    existing_user = get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Create user
    user_id = len(users_db) + 1
    user_data = {
        "id": user_id,
        "username": user.username,
        "password": user.password,  # In production, hash this!
        "group_id": None
    }
    
    users_db[user_id] = user_data
    
    logger.info(f"User created: {user_id}")
    
    return UserResponse(
        id=user_id,
        username=user.username,
        group_id=None
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """Get user by ID."""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = users_db[user_id]
    
    return UserResponse(
        id=user["id"],
        username=user["username"],
        group_id=user.get("group_id")
    )


@router.get("/users/username/{username}", response_model=UserResponse)
async def get_user_by_username_endpoint(username: str):
    """Get user by username."""
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user["id"],
        username=user["username"],
        group_id=user.get("group_id")
    )


@router.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get access token."""
    logger.info(f"Login attempt: {form_data.username}")
    
    # Find user
    user = get_user_by_username(form_data.username)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    # Verify password
    if user["password"] != form_data.password:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user["username"], "user_id": user["id"]}
    )
    
    logger.info(f"Login successful: {form_data.username}")
    
    return Token(access_token=access_token)


@router.post("/auth/register", response_model=UserResponse)
async def register(user: UserCreate):
    """Register a new user."""
    return await create_user(user)


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_endpoint(current_user: UserResponse = Depends(get_current_user)):
    """Get current authenticated user."""
    return current_user
