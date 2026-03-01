from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from server.src.config import settings
from server.src.database.session import get_db
from server.src.models.user import User
from server.src.schema.token import TokenData
from server.src.repositories.user import user_repo

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_current_user_from_headers(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # The user's ID is stored in the "sub" (subject) field of the token
        username: str = payload.get("sub") # type: ignore
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    # Get the user from the database
    user = user_repo.get_by_username(db, username)
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

def get_token_from_cookie(access_token: str | None = Cookie(None)) -> str | None:
    """
    Looks for a cookie named 'access_token' in the request and returns its value.
    If not found, it will return None.
    """
    return access_token

def get_current_user_from_cookie(
    token: str | None = Depends(get_token_from_cookie), 
    db: Session = Depends(get_db)
) -> User:
    """
    This is the dependency you will use in your protected endpoints.
    
    1. It depends on `get_token_from_cookie` to get the raw token.
    2. If the token is missing, it raises a 401 Unauthorized error.
    3. It decodes and validates the token.
    4. If the token is invalid, it raises a 401 error.
    5. It fetches the user from the database.
    6. If the user doesn't exist, it raises a 401 error.
    7. If everything is successful, it returns the SQLAlchemy User object.
    """
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated: No token provided"
        )
        
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub") # type: ignore
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = user_repo.get_by_username(db, username=username) 
    if user is None:
        raise credentials_exception
        
    return user


def require_group(required_group: str):
    """
    Dependency Factory: Returns a dependency that checks if the current user
    is a member of the specified group.
    """
    print(f"[DBG] checking user's group - group {required_group} required")
    def check_user_group(current_user: User = Depends(get_current_user_from_cookie)) -> User:
        print(f"[DBG] User {current_user.username} - {current_user.group}/{current_user.group_id}")
        if required_group != (current_user.group.name if current_user.group else ''):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Requires '{required_group}' role.",
            )
        return current_user

    return check_user_group