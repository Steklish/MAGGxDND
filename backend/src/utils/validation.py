"""
Request validation and sanitization utilities.

This module provides helpers for validating and cleaning user input
to prevent injection attacks and ensure data integrity.
"""
import re
from typing import Optional, TypeVar
from pydantic import BaseModel, Field, validator
from backend.src.config import settings

T = TypeVar('T', bound=BaseModel)


# ===================================================================
# VALIDATION PATTERNS
# ===================================================================

# Allowed characters for names (letters, numbers, spaces, basic punctuation)
NAME_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_\'\"]+$')

# Prevent SQL injection patterns
SQL_INJECTION_PATTERNS = [
    r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE)\b)',
    r'(--|\#|\/\*)',  # SQL comments
    r'(\bOR\b\s+\d+\s*=\s*\d+)',  # OR 1=1 style
    r'(\bAND\b\s+\d+\s*=\s*\d+)',  # AND 1=1 style
    r'(;\s*(SELECT|INSERT|UPDATE|DELETE|DROP))',  # Stacked queries
]

# Prevent XSS patterns
XSS_PATTERNS = [
    r'<script[^>]*>',
    r'javascript:',
    r'on\w+\s*=',  # onclick=, onerror=, etc.
    r'<iframe[^>]*>',
    r'<object[^>]*>',
]


def sanitize_string(value: str, max_length: int = 500) -> str:
    """
    Sanitize a string by:
    1. Stripping leading/trailing whitespace
    2. Limiting length
    3. Removing null bytes

    Args:
        value: The string to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    if not value:
        return ""

    # Remove null bytes
    value = value.replace('\x00', '')

    # Strip whitespace
    value = value.strip()

    # Limit length
    if len(value) > max_length:
        value = value[:max_length]

    return value


def validate_name(value: str, field_name: str = "Name") -> str:
    """
    Validate a name field.

    Args:
        value: The name to validate
        field_name: Name of the field for error messages

    Returns:
        Validated name

    Raises:
        ValueError: If name is invalid
    """
    if not value or not value.strip():
        raise ValueError(f"{field_name} cannot be empty")

    value = sanitize_string(value, max_length=100)

    if len(value) < 2:
        raise ValueError(f"{field_name} must be at least 2 characters")

    if not NAME_PATTERN.match(value):
        raise ValueError(
            f"{field_name} contains invalid characters. "
            "Only letters, numbers, spaces, hyphens, and underscores are allowed."
        )

    return value


def detect_sql_injection(value: str) -> bool:
    """
    Detect potential SQL injection attempts.

    Args:
        value: String to check

    Returns:
        True if SQL injection pattern detected
    """
    value_upper = value.upper()
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, value_upper, re.IGNORECASE):
            return True
    return False


def detect_xss(value: str) -> bool:
    """
    Detect potential XSS attempts.

    Args:
        value: String to check

    Returns:
        True if XSS pattern detected
    """
    value_lower = value.lower()
    for pattern in XSS_PATTERNS:
        if re.search(pattern, value_lower, re.IGNORECASE):
            return True
    return False


def validate_safe_text(value: str, field_name: str = "Text") -> str:
    """
    Validate text for injection attacks.

    Args:
        value: Text to validate
        field_name: Name of the field for error messages

    Returns:
        Validated text

    Raises:
        ValueError: If injection pattern detected
    """
    if not value:
        return ""

    value = sanitize_string(value, max_length=5000)

    if detect_sql_injection(value):
        raise ValueError(f"{field_name} contains invalid patterns")

    if detect_xss(value):
        raise ValueError(f"{field_name} contains invalid HTML/JavaScript")

    return value


# ===================================================================
# BASE API RESPONSE SCHEMAS
# ===================================================================

class APIResponse(BaseModel):
    """Base API response schema."""
    success: bool = True
    message: str = "OK"
    timestamp: str = Field(
        default_factory=lambda: __import__("datetime").datetime.utcnow().isoformat()
    )


class APIError(BaseModel):
    """Base API error response schema."""
    success: bool = False
    error: str
    error_code: Optional[str] = None
    timestamp: str = Field(
        default_factory=lambda: __import__("datetime").datetime.utcnow().isoformat()
    )


class PaginatedResponse(BaseModel):
    """Paginated API response schema."""
    items: list = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0

    def __init__(self, **data):
        super().__init__(**data)
        if self.total and self.page_size:
            self.total_pages = (self.total + self.page_size - 1) // self.page_size


# ===================================================================
# VALIDATED REQUEST SCHEMAS
# ===================================================================

class ValidatedNameRequest(BaseModel):
    """Base schema for requests with name fields."""
    name: str

    @validator('name')
    def validate_name(cls, v):
        return validate_name(v, "Name")


class ValidatedSessionRequest(BaseModel):
    """Base schema for session-related requests."""
    session_name: str
    description: Optional[str] = None

    @validator('session_name')
    def validate_session_name(cls, v):
        return validate_name(v, "Session name")

    @validator('description')
    def validate_description(cls, v):
        if v:
            return validate_safe_text(v, "Description")
        return v
