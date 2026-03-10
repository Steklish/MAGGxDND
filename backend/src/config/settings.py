import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings with secure defaults for production."""

    # ===================================================================
    # DATABASE SETTINGS
    # ===================================================================
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./maggxdnd.db")

    # ===================================================================
    # SECURITY SETTINGS
    # ===================================================================
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-this-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # Password hashing settings
    HASHING_ROUNDS: int = int(os.getenv("HASHING_ROUNDS", "12"))

    # ===================================================================
    # CORS SETTINGS
    # ===================================================================
    # Comma-separated list of allowed origins
    # Example: "http://localhost:3000,http://localhost:5173,https://myapp.com"
    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    ]
    CORS_ALLOW_CREDENTIALS: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "True").lower() == "true"
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    CORS_ALLOW_HEADERS: List[str] = ["Authorization", "Content-Type", "Accept"]

    # ===================================================================
    # RATE LIMITING SETTINGS
    # ===================================================================
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    RATE_LIMIT_DEFAULT: str = os.getenv("RATE_LIMIT_DEFAULT", "100/minute")
    RATE_LIMIT_AUTH: str = os.getenv("RATE_LIMIT_AUTH", "5/minute")
    RATE_LIMIT_API: str = os.getenv("RATE_LIMIT_API", "60/minute")

    # ===================================================================
    # SERVER SETTINGS
    # ===================================================================
    SERVER_HOST: str = os.getenv("SERVER_HOST", "127.0.0.1")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # ===================================================================
    # AI/ML SETTINGS
    # ===================================================================
    AI_GEN_RETRIES: int = int(os.getenv("AI_GEN_RETRIES", 3))
    MODEL_ROLE: str = os.getenv("MODEL_ROLE", "model")
    LLAMACPP_CHAT_BASE: str = os.getenv("LLAMACPP_CHAT_BASE", "http://localhost:8080")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    # ===================================================================
    # LOGGING SETTINGS
    # ===================================================================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "./log/server.log")
    LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10MB
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    # ===================================================================
    # WEBSOCKET SETTINGS
    # ===================================================================
    WS_HEARTBEAT_INTERVAL: int = int(os.getenv("WS_HEARTBEAT_INTERVAL", "30"))
    WS_MAX_MESSAGE_SIZE: int = int(os.getenv("WS_MAX_MESSAGE_SIZE", "1048576"))  # 1MB

    # ===================================================================
    # SESSION SETTINGS
    # ===================================================================
    SESSION_MAX_PLAYERS: int = int(os.getenv("SESSION_MAX_PLAYERS", "5"))
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "120"))

    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.DEBUG

    def validate(self) -> bool:
        """Validate critical settings. Returns True if valid, raises ValueError otherwise."""
        if self.is_production() and self.SECRET_KEY == "your-secret-key-here-change-this-in-production":
            raise ValueError(
                "SECRET_KEY must be changed in production! "
                "Set it via environment variable or .env file."
            )
        return True


# Create a global instance of settings
settings = Settings()