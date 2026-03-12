from fastapi import APIRouter, Depends, FastAPI, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from pydantic import BaseModel
from typing import Optional

from backend.src.config import settings
from backend.src.database.session import get_db
from backend.src.schema.token import Token, AuthResponse, GuestToken
from backend.src.utils import security
from backend.src.services import auth_service
from backend.src.models.user import User
from backend.src.repositories import user_repo


router = APIRouter(prefix="/auth", tags=["auth"])

class GuestLoginRequest(BaseModel):
    """Request for guest login."""
    username: Optional[str] = None  # Optional guest username

class LoginRequest(BaseModel):
    """Extended login request with remember me."""
    username: str
    password: str
    remember_me: bool = False

class RegisterRequest(BaseModel):
    """Request for user registration."""
    username: str
    password: str

@router.post("/login", response_model=AuthResponse)
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
        secure=False,              # <-- Set to True in production with HTTPS
        path="/",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    return AuthResponse(
        access_token=token.access_token,
        token_type=token.token_type,
        is_guest=False
    )

@router.post("/login/json", response_model=AuthResponse)
def login_with_json(response: Response, request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login with JSON body (supports remember_me).
    """
    # Create OAuth2 form data from JSON request
    form_data = OAuth2PasswordRequestForm(username=request.username, password=request.password)
    
    # Authenticate user
    user = auth_service.authenticate_user(db=db, username=request.username, password=request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create token with remember_me option
    access_token, expire = security.create_access_token_with_remember(
        data={"sub": user.username},
        remember_me=request.remember_me
    )
    
    # Set cookie with appropriate expiration
    max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    if request.remember_me:
        max_age = 30 * 24 * 60 * 60  # 30 days
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True in production
        path="/",
        max_age=max_age
    )
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        is_guest=False,
        expires_at=expire
    )

@router.post("/guest", response_model=AuthResponse)
def guest_login(response: Response, request: Optional[GuestLoginRequest] = None):
    """
    Create a guest token for unauthorized users.
    Guests can explore the app with limited permissions.
    """
    guest_token, expire = security.create_guest_token()
    
    # Set guest cookie
    response.set_cookie(
        key="guest_token",
        value=guest_token,
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True in production
        path="/",
        max_age=24 * 60 * 60  # 24 hours
    )
    
    return AuthResponse(
        access_token=guest_token,
        token_type="bearer",
        is_guest=True,
        expires_at=expire
    )

@router.post("/logout")
def logout(response: Response):
    """
    Handles the user logout and clears all auth cookies.
    """
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="guest_token", path="/")
    return {"detail": "Successfully logged out"}

@router.post("/register", response_model=AuthResponse)
def register_user(response: Response, request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user and return authentication token.
    """
    # Validate username
    if len(request.username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be at least 3 characters long"
        )
    
    # Validate password
    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    # Check if username already exists
    existing_user = user_repo.get_by_username(db, username=request.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    hashed_password = security.get_password_hash(request.password)
    new_user = user_repo.create_user(
        db=db,
        username=request.username,
        hashed_password=hashed_password,
        group_id=None
    )
    
    # Create token with remember_me option (30 days for new users)
    access_token, expire = security.create_access_token_with_remember(
        data={"sub": new_user.username},
        remember_me=True
    )
    
    # Set cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True in production
        path="/",
        max_age=30 * 24 * 60 * 60  # 30 days
    )
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=new_user.id,
        username=new_user.username,
        is_guest=False,
        expires_at=expire
    )

@router.get("/me", response_model=AuthResponse)
def get_current_user_info(response: Response, access_token: Optional[str] = None):
    """
    Get current user information from token.
    Can use either access_token query param or cookie.
    """
    if not access_token:
        # Try to get from cookie (automatically handled by FastAPI)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = security.verify_token(access_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    is_guest = payload.get("is_guest", False)
    username = payload.get("sub", "")
    
    if is_guest:
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            is_guest=True,
            username=username.replace("guest:", "") if username.startswith("guest:") else username
        )
    else:
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            is_guest=False,
            username=username
        )