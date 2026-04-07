# Frontend-Backend Connection Issues

## ✅ Working Correctly

1. **Authentication** - All endpoints match (login, register, guest, OAuth)
2. **Session Management** - All endpoints match (create, list, join, start, etc.)
3. **WebSocket Connection** - Correct URL pattern
4. **Token Passing** - Bearer token via axios interceptor

## ❌ Critical Issues

### 1. Character Creation Payload Mismatch

**Frontend sends:**
```typescript
{
  user_id: userId,
  name: "Aldric",
  race: "Half-Elf",
  char_class: "Fighter",
  level: 1,
  backstory_summary: "...",
  personality_traits: "...",
  max_hp: 45,
  current_hp: 45,
  armor_class: 16,
  speed: 30,
  stats: { strength: 15, dexterity: 12, ... },
  abilities: [...],
  inventory: [...]
}
```

**Backend expects:**
```python
{
  session_id: "uuid-here",
  character_name: "Aldric",
  character_prompt: "A brave half-elf fighter",
  character_class: "Fighter",  # Optional
  character_race: "Half-Elf"   # Optional
}
```

**Problem:** Frontend creates characters as standalone database entities with pre-computed stats. Backend creates characters through session's AI/procedural generation via delivery.

**Impact:** Character creation will fail with validation errors.

### 2. Missing Character Endpoints

**Frontend calls:**
- `GET /api/v1/characters/user/{userId}` - Load user's characters on login
- `GET /api/v1/characters/{id}` - Get character details
- `PUT /api/v1/characters/{id}` - Update character
- `DELETE /api/v1/characters/{id}` - Delete character

**Backend has:**
- Only `POST /api/v1/characters/` - Create character in session

**Impact:** `loadCharacters()` in gameStore.ts will fail silently (returns empty array).

### 3. Profile API Deprecated

**Frontend calls:**
- `POST /api/v1/profiles/` - Create character profile
- `GET /api/v1/profiles/character/{id}` - Get profile

**Backend returns:** HTTP 410 Gone (deprecated)

**Impact:** Profile creation after character creation will fail.

### 4. App.tsx Missing Auth Header

**Issue:** `handleJoinSession` uses raw fetch without Bearer token.

**Impact:** Will get 401 Unauthorized.

---

## 🔧 Required Fixes

### Option 1: Update Frontend to Match Backend (Recommended)

Since the backend architecture is correct (characters created through sessions via delivery), update frontend to:

1. **Change character creation flow:**
   - Create session FIRST
   - Then create character WITHIN session via `POST /api/v1/characters/`
   - Remove pre-computed stats (backend generates them)

2. **Remove character list page:**
   - Characters are now session-specific
   - No "character library" concept
   - Show characters from active sessions instead

3. **Update character loading:**
   - Load characters from `GET /api/v1/sessions/{id}/game_info`
   - No standalone character endpoints needed

### Option 2: Add Backend Endpoints to Support Frontend

If you want to keep the current frontend flow:

1. Add `GET /api/v1/characters/user/{userId}` - Returns characters from user's sessions
2. Add `GET /api/v1/characters/{id}` - Get character from session_data
3. Update character creation to work both ways (standalone and session-based)

**Not recommended** - goes against the architecture where characters belong to sessions.

---

## 📊 Current Character Flow vs Correct Flow

### Current (Broken) Flow:
```
Frontend:
1. User goes to Character Creation page
2. Fills out full D&D character sheet
3. POST /api/v1/characters/ with pre-computed stats
4. POST /api/v1/profiles/ to create profile
5. Character stored in database

Backend:
❌ Fails - session_id missing
❌ Fails - field names don't match
❌ Fails - profile endpoint deprecated
```

### Correct Flow:
```
Frontend:
1. User creates/joins a session FIRST
2. In session, clicks "Create Character"
3. Fills simple form: name, class, race, description
4. POST /api/v1/characters/ with session_id + prompt
5. Backend generates character via AI/procedural
6. Character added to session and broadcast via WebSocket

Backend:
✅ Works - session exists
✅ Works - uses delivery to create character
✅ Works - notifies all players
✅ Works - character stored in session_data JSON
```

---

## 🎯 Recommended Action Plan

### Phase 1: Quick Fix (Make it work)

1. **Update CharacterCreation.tsx:**
   - Require session_id
   - Send correct payload format
   - Use characterAPI.ts instead of raw axios

2. **Update gameStore.ts:**
   - Remove `loadCharacters(userId)` call
   - Load characters from sessions instead

3. **Fix App.tsx:**
   - Add auth header to handleJoinSession

### Phase 2: Proper Fix (Make it right)

1. **Remove standalone character creation:**
   - Delete CharacterCreation.tsx as a separate page
   - Integrate character creation into session flow

2. **Update UI:**
   - After login, show session list
   - After joining session, show "Create Character" button
   - Character creation becomes part of session setup

3. **Remove deprecated endpoints:**
   - Delete profile API calls
   - Remove character CRUD (GET, PUT, DELETE)

---

## 💡 Implementation Details

See the fixes in:
- `frontend/src/components/CharacterCreation.tsx` - Update payload
- `frontend/src/store/gameStore.ts` - Update character loading
- `frontend/src/App.tsx` - Add auth header
- `frontend/src/services/characterAPI.ts` - Update method signatures
