from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from backend.src.config import settings
from backend.src.models.user import User
from backend.src.schema.token import Token
from backend.src.utils import security
from backend.src.repositories import user_repo


class AuthService:
    def authenticate_user(self, db: Session, *, username: str, password: str) -> User | None:
        """
        Core authentication logic.
        1. Fetches the user by username.
        2. Verifies the provided password against the stored hash.
        3. Returns the SQLAlchemy user object on success, otherwise None.
        """
        db_user = user_repo.get_by_username(db, username=username)

        # Check if user exists and password is correct
        if not db_user or not security.verify_password(password, db_user.hashed_password):
            return None

        return db_user

    def login_and_create_token(self, db: Session, form_data: OAuth2PasswordRequestForm) -> Token:
        """
        High-level function for the login endpoint.
        Orchestrates authentication and token creation.
        """
        # Step 1: Authenticate the user using our core logic
        user = self.authenticate_user(
            db, username=form_data.username, password=form_data.password
        )
        
        if not user:
            # It's important to raise the correct exception for the API layer
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Step 2: Create the JWT access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )

        # Step 3: Return the token in the format defined by the Pydantic schema
        return Token(access_token=access_token, token_type="bearer")

# Singleton instance for easy import
auth_service = AuthService()