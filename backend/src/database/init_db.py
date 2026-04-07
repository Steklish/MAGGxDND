from .base import Base
from ..models import user, session
from ..config import settings
import sqlite3
import logging

logger = logging.getLogger(__name__)


def init_db(engine):
    """
    Initialize the database by creating all tables.
    Also applies SQLite optimizations.
    """
    Base.metadata.create_all(bind=engine)

    # Apply SQLite optimizations
    try:
        db_url = str(engine.url)
        if db_url.startswith("sqlite"):
            # Extract database path from SQLAlchemy URL
            # Handle both sqlite:///absolute/path and sqlite:///./relative/path
            if db_url.startswith("sqlite:///"):
                db_path = db_url.replace("sqlite:///", "")
                # If it's a relative path (starts with ./), make it absolute
                if db_path.startswith("./") or not db_path.startswith("C:") and not db_path.startswith("/"):
                    db_path = db_path.lstrip("./")
                    # Use settings.PROJECT_ROOT if available, otherwise use current directory
                    from pathlib import Path
                    CURRENT_FILE = Path(__file__).resolve()
                    PROJECT_ROOT = CURRENT_FILE.parents[3]  # backend/src/database -> ... -> project root
                    db_path = str(PROJECT_ROOT / db_path)
            
            logger.info(f"Applying SQLite optimizations to: {db_path}")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")

            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys=ON")

            # Set cache size
            cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache

            # Set busy timeout
            cursor.execute("PRAGMA busy_timeout=5000")  # 5 second timeout

            conn.commit()
            conn.close()

            logger.info("✓ Database optimizations applied (WAL mode, foreign keys, cache)")
    except Exception as e:
        logger.warning(f"⚠ Could not apply database optimizations: {e}")

    logger.info("Database initialized successfully!")