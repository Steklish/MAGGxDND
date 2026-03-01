from fastapi import APIRouter, Depends, HTTPException
import fastapi
from sqlalchemy.orm import Session
from typing import List

from server.src.auth.dependencies import require_group
from server.src.database.session import get_db
from server.src.services import user_service
from server.src.schema import UserCreate, UserUpdate, UserInDB

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserInDB)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user.
    """
    try:
        return user_service.create_user(db, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}", response_model=UserInDB)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Get a user by ID.
    """
    db_user = user_service.get_user(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.get("/", response_model=List[UserInDB])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get a list of users with pagination.
    """
    return user_service.get_users(db, skip=skip, limit=limit)


@router.put("/{user_id}", response_model=UserInDB)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    """
    Update a user by ID.
    """
    updated_user = user_service.update_user(db, user_id, user)
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        return updated_user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Delete a user by ID.
    """
    success = user_service.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}


@router.get("/username/{username}", response_model=UserInDB)
def get_user_by_username(username: str, db: Session = Depends(get_db)):
    """
    Get a user by username.
    """
    db_user = user_service.get_user_by_username(db, username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user