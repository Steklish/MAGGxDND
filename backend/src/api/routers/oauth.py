"""
OAuth2 authentication routers for Google and Discord
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from pydantic import BaseModel
import httpx
import secrets

from backend.src.database.session import get_db
from backend.src.schema.token import AuthResponse
from backend.src.utils import security
from backend.src.services import auth_service
from backend.src.models.user import User
from backend.src.repositories import user_repo
from backend.src.config import settings

router = APIRouter(prefix="/oauth", tags=["oauth"])

# OAuth state storage (in production, use Redis or database)
oauth_states = {}


class OAuthCallbackData(BaseModel):
    code: str
    state: str


@router.get("/google/login")
async def google_login(request: Request, response: Response):
    """
    Initiate Google OAuth login flow.
    Redirects user to Google's OAuth consent screen.
    """
    # Generate state token to prevent CSRF attacks
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {"provider": "google", "timestamp": datetime.now()}
    
    # Google OAuth URL
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={settings.GOOGLE_REDIRECT_URI}&"
        "response_type=code&"
        "scope=openid%20email%20profile&"
        f"state={state}&"
        "access_type=offline&"
        "prompt=select_account"
    )
    
    return RedirectResponse(url=google_auth_url)


@router.get("/google/callback")
async def google_callback(
    request: Request,
    response: Response,
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth callback.
    Exchanges authorization code for access token and creates/logs in user.
    """
    # Verify state token
    if state not in oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter"
        )
    
    state_data = oauth_states.pop(state)
    if state_data["provider"] != "google":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth provider"
        )
    
    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            }
        )
        
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code for token"
            )
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        # Get user info from Google
        userinfo_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if userinfo_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info"
            )
        
        user_info = userinfo_response.json()
    
    # Create or get user
    email = user_info.get("email")
    username = user_info.get("name", email.split("@")[0] if email else "google_user")
    
    # Check if user exists by email (stored in username for OAuth users)
    db_user = user_repo.get_user_by_username(db, f"google:{email}")
    
    if not db_user:
        # Create new user with random password
        random_password = secrets.token_urlsafe(32)
        db_user = user_repo.create_user(
            db,
            username=f"google:{email}",
            hashed_password=security.get_password_hash(random_password),
            group_id=None
        )
    
    # Create JWT token
    access_token_jwt, expire = security.create_access_token_with_remember(
        data={"sub": db_user.username, "oauth_provider": "google"},
        remember_me=True  # OAuth users are always remembered
    )
    
    # Set cookie
    response.set_cookie(
        key="access_token",
        value=access_token_jwt,
        httponly=True,
        samesite="lax",
        secure=settings.is_production(),
        path="/",
        max_age=30 * 24 * 60 * 60  # 30 days
    )
    
    # Redirect to frontend with success
    frontend_url = f"{settings.FRONTEND_URL}/auth/callback?provider=google&username={username}&user_id={db_user.id}"
    return RedirectResponse(url=frontend_url)


@router.get("/discord/login")
async def discord_login(request: Request, response: Response):
    """
    Initiate Discord OAuth login flow.
    Redirects user to Discord's OAuth consent screen.
    """
    # Generate state token to prevent CSRF attacks
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {"provider": "discord", "timestamp": datetime.now()}
    
    # Discord OAuth URL
    discord_auth_url = (
        "https://discord.com/api/oauth2/authorize?"
        f"client_id={settings.DISCORD_CLIENT_ID}&"
        f"redirect_uri={settings.DISCORD_REDIRECT_URI}&"
        "response_type=code&"
        "scope=identify%20email&"
        f"state={state}"
    )
    
    return RedirectResponse(url=discord_auth_url)


@router.get("/discord/callback")
async def discord_callback(
    request: Request,
    response: Response,
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """
    Handle Discord OAuth callback.
    Exchanges authorization code for access token and creates/logs in user.
    """
    # Verify state token
    if state not in oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter"
        )
    
    state_data = oauth_states.pop(state)
    if state_data["provider"] != "discord":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth provider"
        )
    
    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://discord.com/api/oauth2/token",
            data={
                "client_id": settings.DISCORD_CLIENT_ID,
                "client_secret": settings.DISCORD_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.DISCORD_REDIRECT_URI,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code for token"
            )
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        # Get user info from Discord
        userinfo_response = await client.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if userinfo_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info"
            )
        
        user_info = userinfo_response.json()
    
    # Create or get user
    user_id = user_info.get("id")
    username = user_info.get("username", f"discord_{user_id}")
    email = user_info.get("email", f"{user_id}@discord.local")
    
    # Check if user exists
    db_user = user_repo.get_user_by_username(db, f"discord:{user_id}")
    
    if not db_user:
        # Create new user with random password
        random_password = secrets.token_urlsafe(32)
        db_user = user_repo.create_user(
            db,
            username=f"discord:{user_id}",
            hashed_password=security.get_password_hash(random_password),
            group_id=None
        )
    
    # Create JWT token
    access_token_jwt, expire = security.create_access_token_with_remember(
        data={"sub": db_user.username, "oauth_provider": "discord"},
        remember_me=True  # OAuth users are always remembered
    )
    
    # Set cookie
    response.set_cookie(
        key="access_token",
        value=access_token_jwt,
        httponly=True,
        samesite="lax",
        secure=settings.is_production(),
        path="/",
        max_age=30 * 24 * 60 * 60  # 30 days
    )
    
    # Redirect to frontend with success
    frontend_url = f"{settings.FRONTEND_URL}/auth/callback?provider=discord&username={username}&user_id={db_user.id}"
    return RedirectResponse(url=frontend_url)


@router.get("/link/google")
async def link_google_account(request: Request, response: Response):
    """
    Link Google account to existing user.
    User must be authenticated first.
    """
    # TODO: Implement account linking
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Account linking not yet implemented"
    )


@router.get("/link/discord")
async def link_discord_account(request: Request, response: Response):
    """
    Link Discord account to existing user.
    User must be authenticated first.
    """
    # TODO: Implement account linking
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Account linking not yet implemented"
    )
