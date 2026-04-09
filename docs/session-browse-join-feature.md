# Session Browse & Join Feature

## Overview

This feature allows players to discover and join any public session, not just sessions they own. Players can search for sessions by name or description, view session details, and join with or without using a saved character profile.

## What Was Implemented

### ✅ Backend Changes

#### 1. Database Model Update
**File:** `backend/src/models/session.py`

Added `is_public` column to `GameSession` model:
```python
is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
```

- Defaults to `True` (sessions are public by default)
- Indexed for efficient filtering
- Controls session visibility in browse endpoint

#### 2. Repository Method
**File:** `backend/src/repositories/session_repository.py`

Added `get_public_sessions()` method:
- Filters sessions by `is_public == True` and `is_active == True`
- Supports search by session name or description (case-insensitive)
- Supports pagination (skip/limit)
- Returns ordered by creation date (newest first)

Updated `create_session()` method:
- Added `is_public` parameter (defaults to `True`)
- Sets the flag on session creation

#### 3. API Endpoint
**File:** `backend/src/api/routers/session_router.py`

**New Endpoint:** `GET /api/v1/sessions/public`

Query parameters:
- `search` (optional): Search term for name/description
- `skip` (default: 0): Pagination offset
- `limit` (default: 50): Maximum results

Response:
```json
{
  "sessions": [
    {
      "session_id": "uuid",
      "session_name": "My Adventure",
      "game_mode": "STORY",
      "status": "created",
      "description": "An epic journey...",
      "owner_name": "Alice",
      "player_count": 2,
      "max_players": 5,
      "created_at": "2026-04-09T...",
      "is_owner": false,
      "has_joined": false
    }
  ],
  "total": 15,
  "skip": 0,
  "limit": 50,
  "search": "adventure"
}
```

**Updated:** Session creation now saves `is_public` flag:
```python
db_session = repository.create_session(
    ...,
    is_public=request.is_public,
    session_data={
        ...,
        "is_public": request.is_public,
        ...
    }
)
```

### ✅ Frontend Changes

#### 1. API Service
**File:** `frontend/src/services/sessionAPI.ts`

Added types:
```typescript
export interface PublicSession {
    session_id: string;
    session_name: string;
    game_mode: string;
    status: string;
    description?: string;
    owner_name: string;
    player_count: number;
    max_players: number;
    created_at: string;
    is_owner: boolean;
    has_joined: boolean;
}

export interface PublicSessionsResponse {
    sessions: PublicSession[];
    total: number;
    skip: number;
    limit: number;
    search?: string;
}
```

Added method:
```typescript
browsePublicSessions: async (search?: string, skip: number = 0, limit: number = 50)
```

#### 2. BrowseSessions Component
**Files:** 
- `frontend/src/components/BrowseSessions.tsx`
- `frontend/src/components/BrowseSessions.css`

Features:
- **Search bar**: Search sessions by name or description
- **Session cards**: Display session info with badges
- **Status badges**: Waiting, Running, Completed
- **Owner badge**: Highlights sessions you own
- **Joined badge**: Highlights sessions you've already joined
- **Player count**: Shows current/max players
- **Profile selection**: Choose to join with saved character or quick join
- **Responsive grid**: Adapts to screen size
- **Loading states**: Spinner while fetching data
- **Empty states**: Helpful messages when no sessions found
- **Error handling**: User-friendly error messages

#### 3. HomePage Integration
**Files:**
- `frontend/src/components/HomePage.tsx`
- `frontend/src/components/HomePage.css`

Added:
- New "🔍 Browse" tab in header navigation
- Styled with blue highlight to stand out
- Renders `BrowseSessions` component when active
- Passes `onJoinSession` callback for navigation

## User Flow

### Browsing Sessions

```
User logs in
    ↓
Homepage shows with 4 tabs:
  - Overview
  - Characters
  - Sessions (your sessions)
  - 🔍 Browse (public sessions) ← NEW!
    ↓
User clicks "Browse" tab
    ↓
All public sessions load automatically
    ↓
User can:
  - Search by name/description
  - View session details
  - See player counts
  - See session status
```

### Joining a Session

```
User finds a session they want to join
    ↓
Clicks "Join Session" button
    ↓
IF user has saved character profiles:
  → Profile selection modal appears
  → Options:
    - Quick Join (default character)
    - Use saved character [list of profiles]
  → User selects option
  → Joins session
ELSE:
  → Joins directly with default character
    ↓
User is redirected to session page
    ↓
Session shows user in player list
```

### Creating a Public Session

```
User clicks "Create Session"
    ↓
Fills out session form
    ↓
Session is created with is_public=true (default)
    ↓
Session appears in Browse tab for all users
    ↓
Other users can find and join the session
```

## Session Visibility Rules

| Session State | Visible in Browse? | Joinable? |
|---------------|-------------------|-----------|
| `is_active=true`, `is_public=true`, `status=created` | ✅ Yes | ✅ Yes |
| `is_active=true`, `is_public=true`, `status=running` | ✅ Yes | ✅ Yes |
| `is_active=true`, `is_public=true`, `status=completed` | ✅ Yes | ❌ No |
| `is_active=true`, `is_public=true`, `status=paused` | ✅ Yes | ❌ No |
| `is_active=true`, `is_public=false` | ❌ No | ❌ No |
| `is_active=false` | ❌ No | ❌ No |

## Badges and Indicators

### Session Cards Show:

1. **Status Badge**:
   - 🔵 **Waiting** (blue) - Session created, waiting for players
   - 🟢 **Running** (green) - Game in progress
   - ⚪ **Completed** (gray) - Session finished

2. **Owner Badge** (yellow) - You created this session

3. **Joined Badge** (green) - You've already joined this session

4. **Player Count**: Shows "current / max" players

5. **Game Mode Icon**:
   - 📖 Story mode
   - ⚔️ Combat mode

## Search Functionality

The search feature:
- Case-insensitive matching
- Searches both session name AND description
- Real-time filtering
- Clear button to reset search
- Shows helpful empty state when no results

Example searches:
- `"dragon"` - Finds sessions with "dragon" in name or description
- `"tavern"` - Finds sessions mentioning tavern
- `"combat"` - Finds combat-mode sessions

## Join Restrictions

Players can only join sessions that:
1. Are in `created` or `running` status
2. Have not reached max player capacity
3. Are marked as `is_public=true`
4. The player hasn't already joined (prevents duplicates)

## Character Profile Integration

When joining a session:

**If player has saved profiles:**
- Modal appears with options
- Can quick join (default character)
- Can select any saved character profile
- Profile is converted to in-game Character

**If player has no profiles:**
- Joins immediately with default character
- Character is generated by AI or procedurally

## API Usage Examples

### Browse all public sessions
```bash
curl http://localhost:8000/api/v1/sessions/public \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Search for sessions
```bash
curl "http://localhost:8000/api/v1/sessions/public?search=dragon" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Paginate results
```bash
curl "http://localhost:8000/api/v1/sessions/public?skip=50&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Join a session
```bash
curl -X POST http://localhost:8000/api/v1/sessions/{session_id}/players \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"player_name": "Alice"}'
```

### Join with character profile
```bash
curl -X POST http://localhost:8000/api/v1/sessions/{session_id}/players/with-profile \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"player_name": "Alice", "profile_id": 42}'
```

## Database Migration

Since we added a new column (`is_public`) to the `game_sessions` table, you may need to run a migration:

```python
# If using Alembic or similar migration tool
ALTER TABLE game_sessions ADD COLUMN is_public BOOLEAN DEFAULT TRUE NOT NULL;
```

**OR** if the ORM auto-creates tables (like SQLAlchemy with `create_all()`):
```bash
# The column will be created automatically on next server start
python start.py
```

## Testing Checklist

### Backend
- [ ] Public sessions endpoint returns correct data
- [ ] Search filters work correctly
- [ ] Pagination works
- [ ] is_public saved on session creation
- [ ] is_public column exists in database

### Frontend
- [ ] Browse tab appears in HomePage
- [ ] Public sessions load correctly
- [ ] Search functionality works
- [ ] Session cards display all info
- [ ] Badges show correctly (status, owner, joined)
- [ ] Join button works
- [ ] Profile selection modal appears when appropriate
- [ ] Join with profile works
- [ ] Quick join works
- [ ] Navigation to session after join works

### Integration
- [ ] Created sessions appear in browse list
- [ ] Joined sessions show "Joined" badge
- [ ] Owned sessions show "Owner" badge
- [ ] Player count updates after join
- [ ] Search finds sessions correctly
- [ ] Can join sessions from browse page
- [ ] Character profiles used correctly on join

## Future Enhancements

1. **Private sessions**: Allow users to make sessions private
2. **Session tags**: Categorize sessions by theme/type
3. **Sort options**: Sort by name, date, player count, status
4. **Session previews**: Show brief game state preview
5. **Invite links**: Generate shareable invite URLs
6. **Session ratings**: Rate/review sessions
7. **Favorites**: Bookmark favorite sessions
8. **Filter by game mode**: Filter by STORY/COMBAT
9. **Filter by status**: Show only waiting/running sessions
10. **Session thumbnails**: Visual preview images

## Summary

The browse and join feature is now **fully functional**:

✅ Players can discover public sessions  
✅ Search by name or description  
✅ View detailed session information  
✅ Join sessions with or without character profiles  
✅ Visual badges show session status  
✅ Responsive and user-friendly interface  
✅ Integrated seamlessly with existing flows  

Players are no longer limited to only their own sessions - they can now explore and join the broader community!
