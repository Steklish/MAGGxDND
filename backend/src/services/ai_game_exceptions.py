"""
AI Game Service Exceptions

Базовые классы ошибок для AI сервиса.
"""


class AIServiceError(Exception):
    """Базовая ошибка AI сервиса."""
    pass


class GenerationError(AIServiceError):
    """Ошибка генерации контента."""
    pass


class SessionNotInitializedError(AIServiceError):
    """Сессия не инициализирована."""
    pass


class APIError(AIServiceError):
    """Ошибка API (Google Gemini)."""
    pass


class CharacterNotFoundError(AIServiceError):
    """Персонаж не найден."""
    pass


class InvalidActionError(AIServiceError):
    """Недопустимое действие."""
    pass
