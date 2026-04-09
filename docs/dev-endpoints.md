# Developer Endpoints Documentation

These endpoints provide comprehensive access to all active game sessions and their data for debugging and monitoring purposes.

## Base URL

All endpoints are prefixed with `/api/v1/test`

**Example:** `http://localhost:8000/api/v1/test/sessions`

## Authentication

**No authentication required!** These endpoints are designed for development and debugging purposes and can be accessed without any tokens or login.

⚠️ **Warning:** These endpoints should only be used in development environments. Do not expose them in production without proper security measures.

---

## Endpoints

### 1. Get All Sessions

**Endpoint:** `GET /api/v1/test/sessions`

**Description:** Get a list of all sessions from both the database and active in-memory sessions.

**Response:**
```json
{
  "total_database_sessions": 12,
  "total_memory_sessions": 2,
  "database_sessions": [
    {
      "session_id": "uuid-here",
      "session_name": "My D&D Session",
      "owner_id": 1,
      "game_mode": "COMBAT",
      "status": "running",
      "created_at": "2026-04-09T10:00:00",
      "updated_at": "2026-04-09T12:00:00",
      "last_active_at": "2026-04-09T12:30:00",
      "is_running": true,
      "source": "database",
      "participants_count": 3,
      "session_data_preview": {
        "max_players": 5,
        "description": "An epic adventure...",
        "guide": "AI Game Master"
      }
    }
  ],
  "memory_sessions": [
    {
      "session_id": "uuid-here",
      "session_name": "Active Session",
      "player_count": 3,
      "event_count": 45,
      "game_mode": "COMBAT",
      "player_ids": ["player1", "player2", "player3"],
      "is_running": true,
      "source": "memory"
    }
  ]
}
```

---

### 2. Get Session Detail

**Endpoint:** `GET /api/v1/test/sessions/{session_id}`

**Description:** Get comprehensive data for a specific session including full session state, players, NPCs, scene, messages, and more.

**Response:**
```json
{
  "session_id": "uuid-here",
  "session_name": "My D&D Session",
  "game_mode": "COMBAT",
  "session_state": { /* Full serializable session state */ },
  "websocket_connections": {
    "player1": "connected",
    "player2": "connected"
  },
  "active_player_count": 2,
  "event_pool_size": 45,
  "message_count": 120,
  "npc_count": 5,
  "player_count": 3,
  "current_location": "Tavern"
}
```

---

### 3. Get Session Players

**Endpoint:** `GET /api/v1/test/sessions/{session_id}/players`

**Description:** Get detailed information about all players in a session, including character data, positions, stats, and connection status.

**Response:**
```json
{
  "session_id": "uuid-here",
  "total_players": 3,
  "connected_players": 2,
  "players": [
    {
      "player_id": "player1",
      "character_name": "Thorin Ironforge",
      "connected": true,
      "character_data": { /* Full character Pydantic dict */ }
    }
  ]
}
```

---

### 4. Get Session NPCs

**Endpoint:** `GET /api/v1/test/sessions/{session_id}/npcs`

**Description:** Get all NPCs in a session with their current state.

**Response:**
```json
{
  "session_id": "uuid-here",
  "total_npcs": 5,
  "npcs": [
    {
      "npc_name": "Goblin Chief",
      "current_scene": "Forest",
      "npc_data": { /* Full NPC Pydantic dict */ }
    }
  ]
}
```

---

### 5. Get Session Scene

**Endpoint:** `GET /api/v1/test/sessions/{session_id}/scene`

**Description:** Get the current scene data for a session.

**Response:**
```json
{
  "session_id": "uuid-here",
  "current_location": "Tavern",
  "scene": {
    "name": "The Rusty Dragon Tavern",
    "description": "...",
    "gm_secret": "...",
    "objects": [],
    "spatial_properties": {}
  },
  "all_locations_count": 12
}
```

---

### 6. Get Session Messages

**Endpoint:** `GET /api/v1/test/sessions/{session_id}/messages`

**Description:** Get the message history for a session (last 100 messages).

**Response:**
```json
{
  "session_id": "uuid-here",
  "total_messages": 250,
  "messages_returned": 100,
  "messages": [
    { /* Message Pydantic dict */ },
    { /* Message Pydantic dict */ }
  ]
}
```

---

### 7. Get Session Turn Queue

**Endpoint:** `GET /api/v1/test/sessions/{session_id}/turn-queue`

**Description:** Get the current turn queue for combat sessions.

**Response:**
```json
{
  "session_id": "uuid-here",
  "game_mode": "COMBAT",
  "turn_queue": {
    "current_turn": 3,
    "queue": ["Thorin", "Goblin Chief", "Elara"]
  }
}
```

---

### 8. Get Session Full State

**Endpoint:** `GET /api/v1/test/sessions/{session_id}/full-state`

**Description:** Get the complete serializable state of a session. This returns everything that would be saved to the database.

**Response:**
```json
{
  "session_id": "uuid-here",
  "timestamp": "2026-04-09T12:34:56.789Z",
  "session_state": {
    /* Complete session state as returned by session.get_session_state() */
  }
}
```

---

### 9. Get Session Event Pool

**Endpoint:** `GET /api/v1/test/sessions/{session_id}/event-pool`

**Description:** Get event pool statistics and recent events.

**Response:**
```json
{
  "session_id": "uuid-here",
  "event_count": 45,
  "subscriber_count": 3
}
```

---

### 10. Get Sessions Summary

**Endpoint:** `GET /api/v1/test/summary`

**Description:** Get a comprehensive summary of all active sessions with aggregated statistics.

**Response:**
```json
{
  "total_active_sessions": 2,
  "total_players_connected": 5,
  "total_events_in_pools": 89,
  "total_messages": 450,
  "sessions": [
    {
      "session_id": "uuid-1",
      "session_name": "Session 1",
      "game_mode": "COMBAT",
      "players_connected": 3,
      "total_players": 4,
      "total_npcs": 5,
      "event_pool_size": 45,
      "message_count": 250,
      "current_location": "Tavern"
    },
    {
      "session_id": "uuid-2",
      "session_name": "Session 2",
      "game_mode": "STORY",
      "players_connected": 2,
      "total_players": 2,
      "total_npcs": 3,
      "event_pool_size": 44,
      "message_count": 200,
      "current_location": "Forest"
    }
  ]
}
```

---

### 11. Get User Info (Existing)

**Endpoint:** `GET /api/v1/test/info`

**Description:** Get current user information (existing endpoint).

**Response:**
```json
{
  "data": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com"
  }
}
```

---

## Usage Examples

### Using curl

```bash
# Get all sessions
curl -X GET "http://localhost:8000/api/v1/test/sessions"

# Get session detail
curl -X GET "http://localhost:8000/api/v1/test/sessions/YOUR_SESSION_ID"

# Get summary
curl -X GET "http://localhost:8000/api/v1/test/summary"
```

### Using JavaScript/TypeScript

```typescript
// Get all sessions
const response = await fetch('/api/v1/test/sessions');
const data = await response.json();
console.log(data);

// Get session detail
const sessionResponse = await fetch(`/api/v1/test/sessions/${sessionId}`);
const sessionData = await sessionResponse.json();
console.log(sessionData);
```

### Using Python (requests)

```python
import requests

# Get all sessions
response = requests.get('http://localhost:8000/api/v1/test/sessions')
print(response.json())

# Get summary
summary = requests.get('http://localhost:8000/api/v1/test/summary')
print(summary.json())
```

---

## Interactive API Documentation

FastAPI provides interactive API documentation at:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

You can test these endpoints directly from the Swagger UI after logging in.

---

## Notes

- All endpoints return JSON responses
- **No authentication required** - these are dev-only endpoints
- Session IDs are UUIDs (e.g., `550e8400-e29b-41d4-a716-446655440000`)
- The `/test/sessions/{session_id}/messages` endpoint returns only the last 100 messages to avoid large payloads
- Game modes are either `"STORY"` or `"COMBAT"`
- If a session doesn't exist, endpoints return 404 error
- ⚠️ **Security Warning:** These endpoints expose sensitive game data and should only be used in development environments
