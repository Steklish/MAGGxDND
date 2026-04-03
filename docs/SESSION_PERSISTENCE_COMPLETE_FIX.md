# Session Persistence Fix - Complete

## Problem
Sessions were not being persisted correctly after creation. The issue had multiple causes:

1. **Duplicate Database Files**: Two separate SQLite database files existed:
   - `C:\VS_Code\MAGGxDND\maggxdnd.db` (root) - **Correct**
   - `C:\VS_Code\MAGGxDND\backend\maggxdnd.db` (backend folder) - **Duplicate**

2. **Database Path Resolution**: The database path was being resolved differently depending on the working directory, causing the server to write to different database files.

3. **Frontend localStorage**: Session IDs were not being persisted to browser localStorage consistently, causing sessions to disappear on page refresh.

## Solution

### Backend Fixes

#### 1. Fixed Database Path Configuration
**File**: `backend/src/config/settings.py`

**Changes**:
- Use absolute path calculation from `__file__` location
- Load `.env` file from project root using absolute path
- Added logging for database URL configuration

```python
# Get project root directory using absolute path
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[3]  # config -> src -> backend -> project root

# Load .env from project root
env_file_path = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=env_file_path, override=True)

# Database URL with absolute path
_db_url = os.getenv("DATABASE_URL")
if _db_url:
    DATABASE_URL: str = _db_url
else:
    db_path = PROJECT_ROOT / "maggxdnd.db"
    DATABASE_URL: str = f"sqlite:///{str(db_path).replace('\\', '/')}"
```

#### 2. Fixed Database Initialization
**File**: `backend/src/database/init_db.py`

**Changes**:
- Use absolute path for SQLite optimizations
- Added proper path resolution for both absolute and relative database URLs
- Changed from `print()` to proper logging

```python
# Handle both sqlite:///absolute/path and sqlite:///./relative/path
if db_url.startswith("sqlite:///"):
    db_path = db_url.replace("sqlite:///", "")
    # If it's a relative path, make it absolute
    if db_path.startswith("./") or not db_path.startswith("C:") and not db_path.startswith("/"):
        db_path = db_path.lstrip("./")
        PROJECT_ROOT = CURRENT_FILE.parents[3]
        db_path = str(PROJECT_ROOT / db_path)
```

#### 3. Removed Duplicate Database File
**Action**: Deleted `C:\VS_Code\MAGGxDND\backend\maggxdnd.db` and related WAL files

### Frontend Fixes

#### 1. Enhanced Session Persistence in Store
**File**: `frontend/src/store/gameStore.ts`

**Changes**:
- Persist `currentSessionId` and `currentSessionName` to localStorage on session creation
- Restore session from localStorage on app initialization
- Clear session data from localStorage on logout
- Restore active session IDs from localStorage

```typescript
createSession: async (data: any): Promise<GameSession> => {
    const session = await sessionAPI.createSession(sessionData);
    
    // Persist to localStorage immediately
    localStorage.setItem('currentSessionId', session.session_id);
    localStorage.setItem('currentSessionName', session.session_name);
    
    await get().loadSessions();
    return session;
}
```

#### 2. Fixed Session Creation Callback in App.tsx
**File**: `frontend/src/App.tsx`

**Changes**:
- Accept `sessionId` parameter in `handleSessionComplete`
- Persist session ID to localStorage immediately after creation

```typescript
const handleSessionComplete = (sessionId: string) => {
    if (sessionId) {
        localStorage.setItem('currentSessionId', sessionId);
        console.log('✓ Session persisted to localStorage:', sessionId);
    }
    setCurrentPage('home');
    loadSessions();
};
```

#### 3. Fixed Session Creation Modal in HomePage.tsx
**File**: `frontend/src/components/HomePage.tsx**

**Changes**:
- Persist session ID to localStorage in modal's `onComplete` handler

```typescript
onComplete={(sessionId: string) => {
    setShowSessionCreation(false);
    if (sessionId) {
        localStorage.setItem('currentSessionId', sessionId);
        console.log('✓ Session persisted to localStorage:', sessionId);
    }
    loadSessions();
}}
```

## Files Modified

### Backend
1. `backend/src/config/settings.py` - Fixed database path resolution
2. `backend/src/database/init_db.py` - Fixed SQLite path handling

### Frontend
1. `frontend/src/store/gameStore.ts` - Enhanced localStorage persistence
2. `frontend/src/App.tsx` - Fixed session creation callback
3. `frontend/src/components/HomePage.tsx` - Fixed modal session persistence

### Cleanup
1. Deleted `backend/maggxdnd.db` (duplicate)
2. Deleted `backend/maggxdnd.db-shm` (duplicate WAL)
3. Deleted `backend/maggxdnd.db-wal` (duplicate WAL)

## Verification

### Database Check
Run the verification script:
```bash
python test_session_fix.py
```

Expected output:
```
✓ game_sessions table: N sessions
✓ session_participants table: N participants
✓ Only one database file found: C:\VS_Code\MAGGxDND\maggxdnd.db
```

### Manual Testing

1. **Create a session**:
   - Login to the application
   - Click "Create Session"
   - Fill in session details and submit
   - Check browser console for: `✓ Session persisted to localStorage: <uuid>`

2. **Verify database persistence**:
   - Open `C:\VS_Code\MAGGxDND\maggxdnd.db` with a SQLite browser
   - Check `game_sessions` table for the new session
   - Check `session_participants` table for the owner participant

3. **Verify localStorage persistence**:
   - Open browser DevTools → Application → Local Storage
   - Check for `currentSessionId` key
   - Refresh the page
   - Session should still be visible in the UI

4. **Verify session list**:
   - Navigate to "Sessions" tab
   - Created session should appear in the list
   - Session count should match database

## Database Schema

```sql
CREATE TABLE game_sessions (
    id INTEGER PRIMARY KEY,
    session_uuid TEXT UNIQUE NOT NULL,
    session_name TEXT NOT NULL,
    owner_id INTEGER NOT NULL REFERENCES users(id),
    game_mode TEXT NOT NULL,
    max_players INTEGER NOT NULL,
    description TEXT,
    guide TEXT,
    status TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    is_active BOOLEAN NOT NULL,
    is_public BOOLEAN NOT NULL
);

CREATE TABLE session_participants (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES game_sessions(id),
    user_id INTEGER REFERENCES users(id),
    player_uuid TEXT UNIQUE NOT NULL,
    player_name TEXT NOT NULL,
    role TEXT NOT NULL,
    is_connected BOOLEAN NOT NULL,
    joined_at DATETIME NOT NULL
);
```

## Next Steps

1. **Session Save/Load**: Implement full session state serialization and restoration
2. **WebSocket Integration**: Real-time session state synchronization
3. **Session Sharing**: Allow users to share sessions with other players
4. **Session History**: Track session history and statistics

## Related Documentation

- `SESSION_PERSISTENCE_FIX.md` - Previous fix attempt
- `SESSION_DATABASE_IMPLEMENTATION.md` - Database schema design
- `docs/SESSION_API_GUIDE.md` - Session API documentation
