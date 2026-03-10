from .base import Base
from ..models import user, character, character_profile


def init_db(engine):
    """
    Initialize the database by creating all tables.
    """
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")