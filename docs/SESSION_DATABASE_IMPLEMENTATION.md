# Session Database Persistence Implementation

## Overview

Sessions are now persisted in the database with full ownership support. The creator (owner) has full control over their sessions.

## Changes Made

### 1. Database Models (`backend/src/models/session.py`)

Created 4 new models:

#### GameSession
Main session table with ownership:
- `session_uuid` - Unique identifier (UUID)
- `owner_id` - Foreign key to users table (creator)
- `session_name` - Session name
- `game_mode` - STORY/COMBAT/SANDBOX
- `status` - created/running/paused/completed/archived
- `max_players` - Maximum player count
- `description` - Session description
- `guide` - AI plot hint
- `is_public` - Public/private flag
- `created_at`, `updated_at`, `last_active_at` - Timestamps

#### SessionParticipant
Players participating in sessions:
- `session_id` - Foreign key to game_sessions
- `user_id` - Optional (for registered users)
- `player_uuid` - Unique player identifier
- `player_name` - Display name
- `character_id` - Optional character reference
- `role` - owner/player/observer
- `is_connected` - Connection status

#### SessionSave
Session save states:
- `session_id` - Foreign key to game_sessions
- `save_name` - Save file name
- `session_data` - JSON serialized session state
- `save_type` - auto/manual/checkpoint
- `turn_number`, `in_game_time` - Game state metadata

#### SessionCharacter
Characters linked to sessions:
- `session_id` - Foreign key
- `character_id` - Foreign key to characters
- `character_type` - player/npc
- `is_active` - Active status

### 2. Session Repository (`backend/src/repositories/session_repository.py`)

Complete CRUD operations:

**Create:**
- `create_session()` - Create new session with owner

**Read:**
- `get_session_by_id()` - Get by database ID
- `get_session_by_uuid()` - Get by UUID
- `get_owner_sessions()` - Get all sessions owned by user
- `get_participating_sessions()` - Get sessions where user participates
- `get_all_active_sessions()` - Get all active sessions

**Update:**
- `update_session_status()` - Update session status
- `update_session_scene()` - Update current scene
- `update_session_activity()` - Update last active timestamp
- `deactivate_session()` - Soft delete

**Delete:**
- `delete_session()` - Hard delete (owner only)

**Participants:**
- `add_participant()` - Add player to session
- `remove_participant()` - Remove player
- `update_participant_connection()` - Update connection status
- `get_session_participants()` - Get all players

**Saves:**
- `create_session_save()` - Create save state
- `get_session_saves()` - Get all saves
- `get_latest_session_save()` - Get most recent save
- `delete_session_save()` - Delete save

**Characters:**
- `add_session_character()` - Add character to session
- `get_session_characters()` - Get all characters

### 3. Updated Session Router (`backend/src/api/routers/session_router.py`)

**Authentication Required Endpoints:**

| Endpoint | Method | Auth | Owner Only | Description |
|----------|--------|------|------------|-------------|
| `/sessions` | POST | ✅ | N/A | Create new session |
| `/sessions` | GET | ✅ | N/A | List user's sessions |
| `/sessions/{id}` | GET | ✅ | ❌ | Get session info |
| `/sessions/{id}` | PUT | ✅ | ✅ | Update session |
| `/sessions/{id}` | DELETE | ✅ | ✅ | Delete session |
| `/sessions/{id}/start` | POST | ✅ | ✅ | Start game session |
| `/sessions/{id}/info` | GET | ✅ | ❌ | Extended info |
| `/sessions/{id}/players` | GET | ❌ | ❌ | Get players |
| `/sessions/{id}/players` | POST | ❌ | ❌ | Join session |
| `/sessions/{id}/players/{pid}` | DELETE | ❌ | ❌ | Leave session |
| `/sessions/{id}/game_info` | GET | ✅ | ❌ | Game state info |

**Key Features:**
- All sessions are tied to their creator (owner_id)
- Only owner can modify, start, or delete session
- Users can only see their own sessions in the list
- Guests can join running sessions without authentication
- Automatic participant tracking in database

### 4. Updated User Model (`backend/src/models/user.py`)

Added relationships:
```python
# Sessions owned by user
sessions: Mapped[List["GameSession"]] = relationship(...)

# Sessions user participates in
session_participations: Mapped[List["SessionParticipant"]] = relationship(...)
```

## Database Schema

```
┌─────────────┐       ┌──────────────────┐       ┌───────────────────┐
│   users     │       │  game_sessions   │       │session_participants│
├─────────────┤       ├──────────────────┤       ├───────────────────┤
│ id (PK)     │◄──────│ owner_id (FK)    │       │ id (PK)           │
│ username    │       │ session_uuid     │───────│ session_id (FK)   │
│ ...         │       │ session_name     │       │ user_id (FK)      │
└─────────────┘       │ game_mode        │       │ player_uuid       │
                      │ status           │       │ player_name       │
                      │ ...              │       │ role              │
                      └──────────────────┘       │ ...               │
                               │                 └───────────────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                ▼              ▼              ▼
      ┌────────────────┐ ┌────────────┐ ┌──────────────────┐
      │ session_saves  │ │session_... │ │     characters   │
      ├────────────────┤ │characters  │ ├──────────────────┤
      │ id (PK)        │ ├────────────┤ │ id (PK)          │
      │ session_id (FK)│ │session_id  │ │ user_id (FK)     │
      │ session_data   │ │character_id│ │ ...              │
      │ ...            │ │character_..│ └──────────────────┘
      └────────────────┘ │ ...        │
                         └────────────┘
```

## Usage Examples

### Create Session (Authenticated)

```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Cookie: access_token=YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_name": "My Campaign",
    "game_mode": "STORY",
    "max_players": 5,
    "description": "Epic adventure",
    "guide": "Heroes must defeat the dragon"
  }'
```

Response:
```json
{
  "session_id": "uuid-here",
  "session_name": "My Campaign",
  "game_mode": "STORY",
  "player_count": 1,
  "status": "created",
  "description": "Epic adventure",
  "owner_id": 1,
  "owner_name": "username",
  "created_at": "2026-03-16T12:00:00",
  "is_owner": true
}
```

### List User's Sessions

```bash
curl http://localhost:8000/api/v1/sessions \
  -H "Cookie: access_token=YOUR_JWT_TOKEN"
```

Returns only sessions owned by the authenticated user.

### Update Session (Owner Only)

```bash
curl -X PUT http://localhost:8000/api/v1/sessions/{session_id} \
  -H "Cookie: access_token=YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_name": "Updated Name",
    "description": "New description"
  }'
```

### Delete Session (Owner Only)

```bash
curl -X DELETE http://localhost:8000/api/v1/sessions/{session_id} \
  -H "Cookie: access_token=YOUR_JWT_TOKEN"
```

### Join Session (No Auth Required)

```bash
curl -X POST http://localhost:8000/api/v1/sessions/{session_id}/players \
  -H "Content-Type: application/json" \
  -d '{
    "player_name": "GuestPlayer",
    "character_name": "Hero"
  }'
```

## Migration Notes

### Automatic Migration
New tables are created automatically on first run:
- `game_sessions`
- `session_participants`
- `session_saves`
- `session_characters`

### Existing Data
No existing data is affected. The changes are additive.

### Backwards Compatibility
The in-memory session system still works for active games. Database persistence provides:
- Session recovery after server restart
- Ownership enforcement
- Better session listing and filtering

## Testing Checklist

- [x] Database models created and importable
- [x] Repository CRUD operations implemented
- [x] Router endpoints updated with auth
- [x] Ownership validation in place
- [x] Database tables created
- [x] Server starts without errors
- [ ] Create session via API (manual test)
- [ ] List sessions returns only owner's sessions (manual test)
- [ ] Non-owner cannot delete session (manual test)
- [ ] Session persists after server restart (manual test)

## Files Modified

1. `backend/src/models/session.py` - NEW
2. `backend/src/models/user.py` - Updated relationships
3. `backend/src/models/__init__.py` - Export new models
4. `backend/src/repositories/session_repository.py` - NEW
5. `backend/src/api/routers/session_router.py` - Complete rewrite
6. `backend/src/api/routers/session_router.py.bak` - Backup of original

## Next Steps

1. Test session creation through the UI
2. Implement session save/load functionality
3. Add WebSocket support for real-time updates
4. Implement session sharing (make public/private)
5. Add session search and filtering
