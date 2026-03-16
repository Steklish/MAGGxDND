"""
Quick test to verify session persistence after fixes.
"""
import sqlite3
import sys
from pathlib import Path

# Database path
DB_PATH = Path("C:/VS_Code/MAGGxDND/maggxdnd.db")

print("=" * 60)
print("Session Persistence Verification")
print("=" * 60)
print(f"Database: {DB_PATH}")
print(f"Database exists: {DB_PATH.exists()}")
print()

if not DB_PATH.exists():
    print("ERROR: Database file not found!")
    sys.exit(1)

# Connect and check tables
conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r['name'] for r in cursor.fetchall()]
print(f"Tables ({len(tables)}): {', '.join(tables)}")
print()

# Check game_sessions
if 'game_sessions' in tables:
    cursor.execute("SELECT COUNT(*) as count FROM game_sessions")
    count = cursor.fetchone()['count']
    print(f"✓ game_sessions table: {count} sessions")
    
    cursor.execute("SELECT id, session_uuid, session_name, owner_id, status, created_at FROM game_sessions ORDER BY created_at DESC LIMIT 5")
    sessions = cursor.fetchall()
    for s in sessions:
        print(f"  - [{s['id']}] {s['session_uuid'][:8]}... | {s['session_name']} | Owner: {s['owner_id']} | Status: {s['status']}")
else:
    print("✗ game_sessions table NOT FOUND!")

print()

# Check session_participants
if 'session_participants' in tables:
    cursor.execute("SELECT COUNT(*) as count FROM session_participants")
    count = cursor.fetchone()['count']
    print(f"✓ session_participants table: {count} participants")
    
    cursor.execute("""
        SELECT sp.id, sp.player_name, sp.role, gs.session_name
        FROM session_participants sp
        JOIN game_sessions gs ON sp.session_id = gs.id
        ORDER BY sp.joined_at DESC LIMIT 5
    """)
    participants = cursor.fetchall()
    for p in participants:
        print(f"  - {p['player_name']} ({p['role']}) in '{p['session_name']}'")
else:
    print("✗ session_participants table NOT FOUND!")

print()

# Check for duplicate database files
print("Checking for duplicate database files...")
import subprocess
result = subprocess.run(['dir', '/s', '/b', 'maggxdnd.db'], shell=True, capture_output=True, text=True, cwd=r'C:\VS_Code\MAGGxDND')
db_files = [f for f in result.stdout.strip().split('\n') if f]
if len(db_files) > 1:
    print(f"⚠ WARNING: Found {len(db_files)} database files:")
    for f in db_files:
        print(f"  - {f}")
else:
    print(f"✓ Only one database file found: {db_files[0] if db_files else 'NONE'}")

conn.close()
print()
print("=" * 60)
print("Verification complete!")
print("=" * 60)
