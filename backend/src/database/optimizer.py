"""
Database optimization utilities for SQLite
Helps fix common SQLite issues and optimize performance
"""
import sqlite3
import os
from pathlib import Path
from datetime import datetime


def get_database_path(db_url: str = "sqlite:///./data/maggxdnd.db") -> str:
    """Extract database file path from SQLAlchemy URL."""
    if db_url.startswith("sqlite:///"):
        return db_url.replace("sqlite:///", "./")
    return db_url


def optimize_database(db_path: str = None) -> dict:
    """
    Optimize SQLite database for better performance.
    Returns optimization statistics.
    """
    if db_path is None:
        db_path = get_database_path()
    
    if not os.path.exists(db_path):
        return {"status": "error", "message": "Database file not found"}
    
    stats = {
        "status": "success",
        "operations": [],
        "size_before": os.path.getsize(db_path),
        "size_after": 0,
    }
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Run VACUUM to defragment and reclaim space
        cursor.execute("VACUUM")
        stats["operations"].append("VACUUM completed")
        
        # 2. Run ANALYZE to update statistics for query optimizer
        cursor.execute("ANALYZE")
        stats["operations"].append("ANALYZE completed")
        
        # 3. Check integrity
        cursor.execute("PRAGMA integrity_check")
        integrity_result = cursor.fetchone()[0]
        if integrity_result == "ok":
            stats["operations"].append("Integrity check: PASSED")
        else:
            stats["operations"].append(f"Integrity check: FAILED - {integrity_result}")
        
        # 4. Optimize WAL mode (if supported)
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            journal_mode = cursor.fetchone()[0]
            stats["operations"].append(f"Journal mode: {journal_mode}")
        except Exception as e:
            stats["operations"].append(f"Journal mode change skipped: {str(e)}")
        
        # 5. Set optimal page size
        try:
            cursor.execute("PRAGMA page_size=4096")
            stats["operations"].append("Page size set to 4096")
        except Exception as e:
            stats["operations"].append(f"Page size change skipped: {str(e)}")
        
        # 6. Enable foreign keys
        cursor.execute("PRAGMA foreign_keys=ON")
        stats["operations"].append("Foreign keys enabled")
        
        conn.commit()
        
        # Get final size
        stats["size_after"] = os.path.getsize(db_path)
        stats["size_saved"] = stats["size_before"] - stats["size_after"]
        stats["size_saved_mb"] = round(stats["size_saved"] / (1024 * 1024), 2)
        
        conn.close()
        
    except Exception as e:
        stats["status"] = "error"
        stats["message"] = str(e)
    
    return stats


def backup_database(db_path: str = None, backup_dir: str = "./backups") -> str:
    """
    Create a backup of the database.
    Returns the backup file path.
    """
    if db_path is None:
        db_path = get_database_path()
    
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")
    
    # Create backup directory
    os.makedirs(backup_dir, exist_ok=True)
    
    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_name = os.path.basename(db_path)
    backup_filename = f"{db_name}.{timestamp}.bak"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    # Copy database file
    import shutil
    shutil.copy2(db_path, backup_path)
    
    return backup_path


def cleanup_old_backups(backup_dir: str = "./backups", keep_count: int = 5) -> int:
    """
    Remove old backups, keeping only the most recent ones.
    Returns number of files deleted.
    """
    if not os.path.exists(backup_dir):
        return 0
    
    # Get all backup files
    backup_files = [
        os.path.join(backup_dir, f)
        for f in os.listdir(backup_dir)
        if f.endswith('.bak')
    ]
    
    # Sort by modification time (newest first)
    backup_files.sort(key=os.path.getmtime, reverse=True)
    
    # Delete old backups
    deleted_count = 0
    for backup_file in backup_files[keep_count:]:
        os.remove(backup_file)
        deleted_count += 1
    
    return deleted_count


def reset_database(db_path: str = None) -> bool:
    """
    Reset database by deleting and recreating it.
    WARNING: This will delete all data!
    """
    if db_path is None:
        db_path = get_database_path()
    
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Create empty database
    conn = sqlite3.connect(db_path)
    conn.close()
    
    return True


def get_database_info(db_path: str = None) -> dict:
    """
    Get database information and statistics.
    """
    if db_path is None:
        db_path = get_database_path()
    
    if not os.path.exists(db_path):
        return {"status": "error", "message": "Database file not found"}
    
    info = {
        "path": db_path,
        "size_bytes": os.path.getsize(db_path),
        "size_mb": round(os.path.getsize(db_path) / (1024 * 1024), 2),
        "last_modified": datetime.fromtimestamp(os.path.getmtime(db_path)).isoformat(),
        "tables": [],
    }
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table list
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        info["tables"] = [table[0] for table in tables]
        
        # Get row counts for each table
        table_stats = {}
        for table in tables:
            table_name = table[0]
            if table_name != 'sqlite_sequence':
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                table_stats[table_name] = count
        
        info["table_stats"] = table_stats
        
        # Get database settings
        cursor.execute("PRAGMA journal_mode")
        info["journal_mode"] = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA page_size")
        info["page_size"] = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA foreign_keys")
        info["foreign_keys_enabled"] = bool(cursor.fetchone()[0])
        
        conn.close()
        
        info["status"] = "success"
        
    except Exception as e:
        info["status"] = "error"
        info["error"] = str(e)
    
    return info


if __name__ == "__main__":
    print("=" * 60)
    print("MAGGxDND Database Optimization Tool")
    print("=" * 60)
    print()
    
    # Get database info
    print("📊 Database Information:")
    info = get_database_info()
    if info["status"] == "success":
        print(f"   Path: {info['path']}")
        print(f"   Size: {info['size_mb']} MB")
        print(f"   Tables: {len(info.get('tables', []))}")
        print(f"   Journal Mode: {info.get('journal_mode', 'N/A')}")
        print(f"   Foreign Keys: {'Enabled' if info.get('foreign_keys_enabled') else 'Disabled'}")
        print()
        
        if 'table_stats' in info:
            print("   Table Row Counts:")
            for table, count in info['table_stats'].items():
                print(f"      - {table}: {count}")
            print()
    else:
        print(f"   Error: {info.get('message', 'Unknown error')}")
        print()
    
    # Optimize database
    print("⚙️  Optimizing Database...")
    stats = optimize_database()
    if stats["status"] == "success":
        for operation in stats["operations"]:
            print(f"   ✓ {operation}")
        print(f"   Size saved: {stats.get('size_saved_mb', 0)} MB")
    else:
        print(f"   Error: {stats.get('message', 'Unknown error')}")
    print()
    
    # Create backup
    print("💾 Creating Backup...")
    try:
        backup_path = backup_database()
        print(f"   ✓ Backup created: {backup_path}")
    except Exception as e:
        print(f"   Error: {str(e)}")
    print()
    
    # Cleanup old backups
    print("🧹 Cleaning Up Old Backups...")
    deleted = cleanup_old_backups(keep_count=5)
    print(f"   ✓ Deleted {deleted} old backup(s)")
    print()
    
    print("=" * 60)
    print("Optimization Complete!")
    print("=" * 60)
