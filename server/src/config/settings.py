import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./maggxdnd.db")
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-this-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Password hashing settings
    HASHING_ROUNDS: int = int(os.getenv("HASHING_ROUNDS", "12"))
    
    # Server settings
    SERVER_HOST: str = os.getenv("SERVER_HOST", "127.0.0.1")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    AI_GEN_RETRIES = int(os.getenv("AI_GEN_RETRIES", 3))
    MODEL_ROLE = os.getenv("MODEL_ROLE", "model")
    LLAMACPP_CHAT_BASE = os.getenv("LLAMACPP_CHAT_BASE", "http://localhost:8080")

# Create a global instance of settings
settings = Settings()