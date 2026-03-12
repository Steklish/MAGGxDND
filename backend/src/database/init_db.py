from .base import Base
from ..models import user, character, character_profile
import sqlite3


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
            db_path = db_url.replace("sqlite:///", "./")
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
            
            print("✓ Database optimizations applied (WAL mode, foreign keys, cache)")
    except Exception as e:
        print(f"⚠ Warning: Could not apply database optimizations: {e}")
    
    print("Database initialized successfully!")