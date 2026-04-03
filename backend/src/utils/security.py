from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
import uuid
from jose import JWTError, jwt
from backend.src.config import settings

# Guest token expires in 24 hours
GUEST_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours
# Remember me token expires in 30 days
REMEMBER_ME_EXPIRE_DAYS = 30


def get_password_hash(password: str) -> str:
    try:
        # Truncate password to 72 bytes if needed (bcrypt limitation)
        # Note: This truncation may reduce security, so consider using a different algorithm for very long passwords
        truncated_password = password[:72] if len(password) > 72 else password
        # Use bcrypt directly to avoid passlib's backend issues
        salt = bcrypt.gensalt(rounds=settings.HASHING_ROUNDS)
        return bcrypt.hashpw(truncated_password.encode('utf-8'), salt).decode('utf-8')
    except Exception as e:
        # If bcrypt fails, raise a more descriptive error
        raise ValueError(f"Failed to hash password: {str(e)}")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        # Truncate password to 72 bytes if needed (bcrypt limitation)
        truncated_password = plain_password[:72] if len(plain_password) > 72 else plain_password
        
        # Ensure the hashed password is in the right format
        if isinstance(hashed_password, str):
            hashed_bytes = hashed_password.encode('utf-8')
        else:
            hashed_bytes = hashed_password

        return bcrypt.checkpw(truncated_password.encode('utf-8'), hashed_bytes)
    except Exception as e:
        # If bcrypt verification fails, return False
        return False  # or raise an exception if preferred


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    except Exception as e:
        raise ValueError(f"Failed to create access token: {str(e)}")


def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def create_guest_token() -> tuple[str, datetime]:
    """
    Create a guest token for unauthorized users.
    Returns tuple of (token, expiration_datetime).
    """
    guest_id = str(uuid.uuid4())
    expires_delta = timedelta(minutes=GUEST_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    
    to_encode = {
        "sub": f"guest:{guest_id}",
        "is_guest": True,
        "guest_id": guest_id,
        "exp": expire
    }
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt, expire


def create_access_token_with_remember(data: dict, expires_delta: Optional[timedelta] = None, remember_me: bool = False):
    """
    Create access token with optional 'remember me' extended expiration.
    """
    to_encode = data.copy()
    
    if remember_me:
        # Extended expiration for 'remember me'
        expire = datetime.now(timezone.utc) + timedelta(days=REMEMBER_ME_EXPIRE_DAYS)
    elif expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt, expire