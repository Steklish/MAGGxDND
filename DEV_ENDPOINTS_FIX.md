# Developer Endpoints - Fixed and Working

## What Was Fixed

The original issue was that the dev endpoints only checked **in-memory sessions** (SessionManager), which only contains sessions that are **currently running**. Sessions that were created but not actively running would not show up.

### Solution

Updated the endpoints to fetch from **both sources**:
1. **Database sessions** - All persisted sessions from the database
2. **In-memory sessions** - Currently running/active sessions with live state

## What You'll See Now

### GET /api/v1/test/sessions

Returns both database and memory sessions:

```json
{
  "total_database_sessions": 12,
  "total_memory_sessions": 0,
  "database_sessions": [
    {
      "session_id": "7e3657b7-f2fa-4c65-82c9-1da8b2982ef3",
      "session_name": "wqe",
      "owner_id": 1,
      "game_mode": "STORY",
      "status": "running",
      "created_at": "2026-04-08T07:54:53",
      "updated_at": "2026-04-08T11:02:51.734392",
      "last_active_at": "2026-04-08T11:02:51.734395",
      "is_running": false,
      "source": "database",
      "participants_count": 0,
      "session_data_preview": {}
    }
  ],
  "memory_sessions": []
}
```

**Key fields:**
- `source`: `"database"` or `"memory"` - tells you where the data came from
- `is_running`: `true` if the session is currently active in memory
- `session_data_preview`: Shows key fields without the full data dump

### GET /api/v1/test/sessions/{session_id}

Intelligently fetches from memory first (if running), then falls back to database:

**For running sessions:**
```json
{
  "session_id": "...",
  "source": "memory",
  "is_running": true,
  "session_state": { /* Full live state */ },
  "websocket_connections": {...},
  "event_pool_size": 45,
  "message_count": 120
}
```

**For database sessions:**
```json
{
  "session_id": "...",
  "source": "database",
  "is_running": false,
  "session_data": { /* Complete persisted data */ },
  "created_at": "...",
  "updated_at": "..."
}
```

### GET /api/v1/test/summary

Provides overview of both session types:

```json
{
  "total_database_sessions": 12,
  "total_active_memory_sessions": 0,
  "total_players_connected": 0,
  "database_sessions": [...],
  "memory_sessions": [...]
}
```

## Testing Results

All endpoints tested and working:

✅ **GET /api/v1/test/sessions** - Returns 12 database sessions  
✅ **GET /api/v1/test/sessions/{id}** - Returns full session data  
✅ **GET /api/v1/test/summary** - Returns complete summary  
✅ **No authentication required** - Direct access  

## Your Current Sessions

You currently have **12 sessions** in the database:

| Name | Session ID (start) | Mode | Status |
|------|-------------------|------|--------|
| ijk | 4fed355b... | STORY | running |
| wer | b77129ae... | STORY | running |
| lih | d1cbd290... | STORY | running |
| rttrgdfs | 2254e495... | STORY | running |
| asd | 321eb989... | STORY | running |
| фуц | cb2a44db... | STORY | running |
| asdf | 1ea7233a... | STORY | running |
| asd | e0eca9a8... | STORY | running |
| 4t334 | 5dc49f3c... | STORY | running |
| ade | a3503b62... | STORY | running |
| ikj | 0d89a807... | COMBAT | running |
| wqe | 7e3657b7... | STORY | running |

**Note:** All show `is_running: false` because they're not currently loaded in memory (server was restarted).

## Quick Start

1. **Start the server:**
   ```bash
   python start.py
   ```

2. **Test in browser:**
   - All sessions: http://localhost:8000/api/v1/test/sessions
   - Summary: http://localhost:8000/api/v1/test/summary
   - Specific session: http://localhost:8000/api/v1/test/sessions/YOUR_SESSION_ID

3. **Test with curl:**
   ```bash
   curl http://localhost:8000/api/v1/test/sessions
   curl http://localhost:8000/api/v1/test/summary
   ```

4. **Interactive docs:**
   - Swagger UI: http://localhost:8000/docs

## Architecture Note

**Database Sessions** vs **Memory Sessions**:

- **Database**: Persisted sessions that survive server restarts. Contains complete game state as JSON.
- **Memory**: Currently running sessions with live state (players, NPCs, events, WebSocket connections). Only exists while server is running and session is active.

The dev endpoints now show **both**, so you can see:
- Historical/persisted sessions (database)
- Currently active sessions (memory)
- Which database sessions are currently running (is_running flag)
