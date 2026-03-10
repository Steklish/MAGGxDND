from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from fastapi import Response

from backend.src.config import settings
from backend.src.database.session import get_db
from backend.src.schema import Token
from backend.src.utils import security
from backend.src.services import auth_service


router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=Token)
def login_for_access_token(response: Response, db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Handles the user login and returns a JWT access token.
    All logic is delegated to the AuthService.
    """
    token = auth_service.login_and_create_token(db=db, form_data=form_data)
    # Set the token in a secure, HttpOnly cookie
    response.set_cookie(
        key="access_token",
        value=token.access_token,
        httponly=True,             # <-- Prevents JavaScript from accessing the cookie
        samesite="lax",            # <-- Provides CSRF protection ('strict' is even better)
        secure=True,               # <-- Ensures cookie is only sent over HTTPS in production
        path="/"
    )
    return token

@router.post("/logout")
def logout(response: Response):
    """
    Handles the user logout and clears the access token cookie.
    """
    response.delete_cookie(key="access_token", path="/")
    return {"detail": "Successfully logged out"}