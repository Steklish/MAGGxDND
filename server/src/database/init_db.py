from .base import Base


def init_db(engine):
    """
    Initialize the database by creating all tables.
    """
    Base.metadata.create_all(bind=engine)