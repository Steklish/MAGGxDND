# MAGGxDND Game Server

FastAPI + WebSocket server that bridges the MAGGxDND game engine with the React UI.

## Architecture

```
┌─────────────────┐         WebSocket + REST         ┌─────────────────┐
│   React UI      │◄────────────────────────────────►│   Game Server   │
│  (port 8000)    │                                  │  (port 8000)    │
└─────────────────┘                                  └────────┬────────┘
                                                              │
                                                              │ Python imports
                                                              ▼
                                                     ┌─────────────────┐
                                                     │  Game Engine    │
                                                     │  (Session, NPC, │
                                                     │   Player, etc.) │
                                                     └─────────────────┘
```

## Features

- **WebSocket Real-time Communication**: Bidirectional communication for game events
- **REST API**: Session and character management
- **GameDelivery**: Implements the Delivery ABC from the game engine
- **Event Pool Integration**: Subscribes to game events and broadcasts to clients
- **Request Queue**: Handles player actions and sends to game engine

## Quick Start

### 1. Start the Game Server

```bash
cd C:\VS_Code\MAGGxDND\UI
python start_server.py
```

Or directly with uvicorn:

```bash
cd C:\VS_Code\MAGGxDND\UI
python -m uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start the UI Dev Server

In a separate terminal:

```bash
cd C:\VS_Code\MAGGxDND\UI
npm run dev
```

### 3. Access the Application

- UI: http://localhost:8000
- API Docs: http://localhost:8000/docs
- WebSocket: ws://localhost:8000/ws/{session_id}/{player_id}

## API Endpoints

### Authentication

- `POST /api/v1/auth/login` - Login with username/password
- `POST /api/v1/auth/register` - Register new user
- `GET /api/v1/auth/me` - Get current user

### Sessions

- `GET /api/v1/sessions` - List all sessions
- `POST /api/v1/sessions` - Create new session
- `GET /api/v1/sessions/{session_id}` - Get session info
- `DELETE /api/v1/sessions/{session_id}` - Delete session
- `POST /api/v1/sessions/{session_id}/players` - Join session
- `DELETE /api/v1/sessions/{session_id}/players/{player_id}` - Leave session
- `POST /api/v1/sessions/{session_id}/start` - Start game session

### Characters

- `GET /api/v1/characters/user/{user_id}` - Get user's characters
- `POST /api/v1/characters` - Create new character
- `GET /api/v1/characters/{character_id}` - Get character info
- `DELETE /api/v1/characters/{character_id}` - Delete character
- `GET /api/v1/profiles/character/{character_id}` - Get character profile
- `POST /api/v1/profiles` - Create character profile
- `PUT /api/v1/profiles/character/{character_id}` - Update profile

## WebSocket API

### Connection

```
ws://localhost:8000/ws/{session_id}/{player_id}
```

### Client → Server Messages

```typescript
// Player Action
{
    "type": "PLAYER_ACTION",
    "payload": {
        "player_id": "Player1",
        "request_text": "Attack the goblin",
        "character": { /* Character data */ },
        "timestamp": 1234567890.0
    }
}

// Subscribe to Events
{
    "type": "SUBSCRIBE_EVENTS",
    "payload": {
        "subscriber_id": "Player1"
    }
}
```

### Server → Client Messages

```typescript
// Connection Confirmed
{
    "type": "CONNECTED",
    "session_id": "uuid",
    "player_id": "Player1"
}

// Master Message (GM narration)
{
    "type": "MASTER_MESSAGE",
    "payload": {
        "text": "The dragon roars!",
        "tag": "Narration"
    }
}

// Session Update
{
    "type": "SESSION_UPDATE",
    "payload": {
        "session": {
            "session_name": "My Campaign",
            "game_mode": "COMBAT",
            "players": [...],
            "npcs": [...],
            "turn_queue": [...],
            "current_scene": {...}
        }
    }
}

// Game Event
{
    "type": "GAME_EVENT",
    "payload": {
        "event": {
            "event_type": "CHARACTER_MOVEMENT",
            "description": "Player1 moves to (5, 5)"
        }
    }
}

// Error
{
    "type": "ERROR",
    "payload": {
        "message": "Error description",
        "details": "Optional details"
    }
}
```

## GameDelivery Class

The `GameDelivery` class extends the `Delivery` ABC from the game engine:

```python
class GameDelivery(Delivery):
    """WebSocket-based delivery implementation."""
    
    async def master_message(self, text: str, tag: Optional[str] = None):
        """Broadcast GM message to all clients."""
        
    async def player_request(self, character: Character) -> str:
        """Wait for player input."""
        
    async def choose_player(self, session) -> 'Player':
        """Select which player acts next."""
        
    async def session_updated(self, session) -> None:
        """Broadcast session state to clients."""
```

## Integration with Game Engine

To integrate with the game engine:

1. Create EventPool for the session
2. Create GameDelivery instance
3. Pass delivery to Session constructor
4. Start game loop

Example:

```python
from game.event_pool import EventPool
from server.main import GameDelivery

# Create event pool
event_pool = EventPool()

# Create delivery
delivery = GameDelivery(
    event_queue=event_pool.subscribe("session_1"),
    logger_instance=logger
)

# Create session with delivery
session = Session(
    session_name="test",
    chroma_client=client,
    logger=logger,
    generator=generator,
    event_pool=event_pool,
    delivery=delivery
)

# Start game loop
asyncio.run(session.game_loop())
```

## Development

### Project Structure

```
UI/server/
├── main.py              # FastAPI app, GameDelivery, WebSocket handler
├── launcher.py          # Server launcher
├── start_server.py      # Start script
├── routes/
│   ├── sessions.py      # Session REST endpoints
│   ├── characters.py    # Character REST endpoints
│   └── auth.py          # Authentication endpoints
└── websocket/
    └── __init__.py
```

### Logging

Logs are written to `C:\VS_Code\MAGGxDND\log\game_server.log`

### Testing

Test WebSocket connection:

```bash
# Using websocat
websocat ws://localhost:8000/ws/test-session/player1

# Using Python
python -c "
import asyncio
import websockets

async def test():
    async with websockets.connect('ws://localhost:8000/ws/test-session/player1') as ws:
        msg = await ws.recv()
        print('Received:', msg)

asyncio.run(test())
"
```

## TODO

- [ ] Integrate real game engine Session with server
- [ ] Implement game loop management
- [ ] Add database persistence (SQLite/PostgreSQL)
- [ ] Implement proper JWT authentication
- [ ] Add rate limiting
- [ ] Add session state serialization
- [ ] Implement GM controls for choosing players
- [ ] Add support for multiple concurrent game sessions
- [ ] Implement proper error handling and recovery

## License

Part of MAGGxDND project
