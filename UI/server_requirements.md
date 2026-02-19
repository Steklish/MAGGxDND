# Server Requirements for MAGGxDND UI

## Overview

This document defines the requirements for a WebSocket-based game server that will enable the UI to interact with the MAGGxDND game engine. The server must expose the functionality defined in `interface/delivery.py` and support real-time communication with the frontend.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Server Requirements](#core-server-requirements)
3. [WebSocket API Specification](#websocket-api-specification)
4. [Data Models](#data-models)
5. [Event System](#event-system)
6. [Session Management](#session-management)
7. [Error Handling](#error-handling)
8. [Security Considerations](#security-considerations)

---

## Architecture Overview

### Current System Structure

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   UI (Frontend) │────▶│  WebSocket Server │────▶│  Game Engine    │
│   (React/Vue)   │◀────│  (FastAPI/Flask)  │◀────│  (Session)      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │
                                ▼
                        ┌──────────────────┐
                        │  Event Pool      │
                        │  (Pub/Sub)       │
                        └──────────────────┘
```

### Key Components from `delivery.py`

The `Delivery` abstract base class defines four core abstract methods that the server must implement:

1. **`master_message(text, tag)`** - Display messages from the Game Master (DM)
2. **`player_request(character)`** - Allow players to submit actions
3. **`choose_player(session)`** - Select which player acts next
4. **`session_updated(session)`** - Callback when session state changes

---

## Core Server Requirements

### 1. WebSocket Server Framework

**Recommended:** FastAPI with WebSocket support

```python
# Example structure
from fastapi import FastAPI, WebSocket
from game.event_pool import EventPool, SubscriberQueue
from interface.delivery import Delivery

app = FastAPI()
```

### 2. Threading & Concurrency

- The server MUST be thread-safe (see `threading.Lock` in `delivery.py`)
- Request queues use Python's `queue.Queue` for thread-safe operations
- Event pool uses `threading.RLock` for recursive locking

### 3. Request Queue System

The server must maintain a request queue per delivery instance:

```python
from queue import Queue

class GameDelivery(Delivery):
    def __init__(self, event_queue: SubscriberQueue, logger: Logger):
        super().__init__(event_queue, logger)
        # self.request_queue is inherited from Delivery
```

**Required Queue Operations:**
- `put_request(request: Request)` - Add player request
- `has_requests()` - Check if queue has requests
- `get_first_request()` - Get oldest request
- `get_first_request_by_player(player_id: str)` - Get request by specific player
- `wait_for_request(timeout: float)` - Block until request available
- `wait_for_request_from_player(player_id: str, timeout: float)` - Wait for specific player

### 4. Event Subscription

Each player/NPC must have a dedicated event queue:

```python
# From event_pool.py
event_pool = EventPool()
player_queue = event_pool.subscribe("player_name")
```

**Event Flow:**
1. Game engine publishes events to `EventPool`
2. `EventPool` distributes to all subscriber queues
3. UI subscribes to WebSocket and receives events in real-time

---

## WebSocket API Specification

### Connection Endpoint

```
ws://localhost:8000/ws/{session_id}/{player_id}
```

### Message Types

#### Client → Server Messages

```typescript
// Player Action Request
interface PlayerAction {
    type: "PLAYER_ACTION";
    payload: {
        player_id: string;
        request_text: string;
        character: Character;
        timestamp: number;
    };
}

// Choose Player Action
interface ChoosePlayer {
    type: "CHOOSE_PLAYER";
    payload: {
        selected_player_id: string;
    };
}

// Subscribe to Events
interface SubscribeEvents {
    type: "SUBSCRIBE_EVENTS";
    payload: {
        subscriber_id: string;
    };
}
```

#### Server → Client Messages

```typescript
// Master Message (DM narration)
interface MasterMessage {
    type: "MASTER_MESSAGE";
    payload: {
        text: string;
        tag?: string;  // "Clarification", "Illegal", "Meta"
    };
}

// Session Update
interface SessionUpdate {
    type: "SESSION_UPDATE";
    payload: {
        session: Session;
    };
}

// Game Event
interface GameEvent {
    type: "GAME_EVENT";
    payload: {
        event: Event;
    };
}

// Player Action Request (prompt for input)
interface ActionRequest {
    type: "ACTION_REQUEST";
    payload: {
        character: Character;
    };
}

// Turn Queue Update
interface TurnQueueUpdate {
    type: "TURN_QUEUE_UPDATE";
    payload: {
        turn_queue: Array<[Character, number, number]>;
        turn_time: number;
    };
}

// Scene Update
interface SceneUpdate {
    type: "SCENE_UPDATE";
    payload: {
        scene: SceneNode;
        characters: Character[];
        npcs: NPCCharacter[];
        objects: UnifiedObject[];
    };
}
```

### WebSocket Handler Example

```python
@app.websocket("/ws/{session_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, player_id: str):
    await websocket.accept()
    
    # Subscribe to event pool
    event_queue = event_pool.subscribe(player_id)
    
    # Get session and delivery instance
    session = get_session(session_id)
    delivery = session.delivery
    
    # Send initial session state
    await websocket.send_json({
        "type": "SESSION_UPDATE",
        "payload": {"session": serialize_session(session)}
    })
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_json()
            
            if data["type"] == "PLAYER_ACTION":
                # Add to request queue
                request = Request(**data["payload"])
                delivery.put_request(request)
                
            elif data["type"] == "SUBSCRIBE_EVENTS":
                # Forward events from queue to websocket
                while True:
                    event = event_queue.get()
                    if event:
                        await websocket.send_json({
                            "type": "GAME_EVENT",
                            "payload": {"event": event.dict()}
                        })
                        
    except WebSocketDisconnect:
        event_pool.unsubscribe(player_id)
```

---

## Data Models

### Character Schema

Based on `schemas/in_game.py`:

```typescript
interface Character {
    // Identity
    name: string;
    race: string;
    char_class: "Peasant" | "Fighter" | "Wizard" | "Rogue" | "Cleric" | "Ranger" | "Paladin" | "Barbarian" | "Bard";
    level: number;
    backstory_summary: string;
    personality_traits: string[];
    
    // Vitals
    max_hp: number;
    current_hp: number;
    temp_hp: number;
    armor_class: number;
    speed: number;
    
    // Stats
    stats: {
        strength: number;
        dexterity: number;
        constitution: number;
        intelligence: number;
        wisdom: number;
        charisma: number;
    };
    
    // State
    inventory: Item[];
    active_conditions_list: Condition[];
    resources: Record<string, number>;
    position: Coordinate2D;
    abilities: SpellAbility[];
    
    // Computed (auto-generated)
    active_conditions: string;  // newline-separated
    proficiency_bonus: number;
    is_alive: boolean;
    initiative_bonus: number;
    short_summary: string;
}
```

### Session Schema

```typescript
interface Session {
    session_name: string;
    current_scene: SceneNode | null;
    game_mode: "STORY" | "COMBAT";
    players: Player[];
    npcs: NPC[];
    messages: Message[];
    turn_queue: Array<[Character, number, number]>;  // [character, time_added, next_turn]
    turn_time: number;
    current_location_name: string | null;
    
    // Spatial
    spatial_enabled: boolean;
}
```

### SceneNode Schema

```typescript
interface SceneNode {
    name: string;
    description: string;
    gm_secret: string;  // Server-side only, never send to client
    objects: UnifiedObject[];
    center_position: Coordinate2D;
    dimensions: Coordinate2D;
    scale_unit: string;
}
```

### Coordinate2D Schema

```typescript
interface Coordinate2D {
    x: number;
    y: number;
}
```

### Event Schema

```typescript
interface Event {
    event_type: EventType;
    event_initiator: string | null;
    event_subject: string | null;
    event_target: string | null;
    description: string;
}

type EventType = 
    | "LOCATION_CHANGE"
    | "LOCATION_MUTATION"
    | "LOCATION_STATUS_CHANGE"
    | "OBJECT_TRANSFER"
    | "ITEM_TRANSFER"
    | "ITEM_MOVEMENT"
    | "ITEM_MUTATION"
    | "ITEM_INTERACTION"
    | "ITEM_PICKUP"
    | "ITEM_DROP"
    | "CONTAINER_ACCESS"
    | "CONTAINER_TRANSFER"
    | "CHARACTER_STATUS_CHANGE"
    | "CHARACTER_DEATH"
    | "CHARACTER_STATS_UPDATE"
    | "CHARACTER_MOVEMENT"
    | "CHARACTER_TRANSFER"
    | "CHARACTER_POSITION_UPDATE"
    | "ACTION_RESULT"
    | "CHARACTER_MELEE_ATTACK"
    | "CHARACTER_RANGED_ATTACK"
    | "SYSTEM";
```

---

## Event System

### Publishing Events

```python
from schemas.orchestration import Event, EventTypes

# Create event
event = Event(
    event_type=EventTypes.CHARACTER_MOVEMENT,
    event_initiator="Player1",
    event_subject="Player1",
    description="Player1 moves from (0,0) to (5,5)"
)

# Publish to all except initiator
player_queue.publish_to_others(event)

# Or add to global pool
event_pool.add_event(event)
```

### Subscribing to Events

```python
# Each player gets their own queue
player_queue = event_pool.subscribe("Player1")

# In WebSocket handler, forward events to client
while True:
    event = player_queue.get()
    if event:
        await websocket.send_json({
            "type": "GAME_EVENT",
            "payload": event.dict()
        })
```

---

## Session Management

### Session Lifecycle

1. **Create Session**
   ```python
   @app.post("/sessions")
   async def create_session(config: SessionConfig):
       session_id = str(uuid.uuid4())
       event_pool = EventPool()
       delivery = GameDelivery(event_pool.subscribe("delivery"), logger)
       session = Session(
           session_name=session_id,
           chroma_client=chroma_client,
           logger=logger,
           generator=generator,
           event_pool=event_pool,
           delivery=delivery
       )
       sessions[session_id] = session
       return {"session_id": session_id}
   ```

2. **Join Session**
   ```python
   @app.post("/sessions/{session_id}/players")
   async def join_session(session_id: str, player_data: PlayerConfig):
       session = sessions[session_id]
       character = Character(**player_data.dict())
       player = session._init_player(character, orchestrator)
       return {"player_id": character.name}
   ```

3. **End Session**
   ```python
   @app.delete("/sessions/{session_id}")
   async def end_session(session_id: str):
       session = sessions.pop(session_id)
       # Cleanup resources
   ```

### Turn-Based System

The server must support the turn queue system from `delivery.py`:

```python
def _print_turn_queue(self, session):
    """
    Turn queue structure:
    [(character, time_added, next_turn), ...]
    Sorted by next_turn to determine action order
    """
```

**WebSocket Update:**
```python
async def broadcast_turn_queue(session):
    sorted_queue = sorted(session.turn_queue, key=lambda x: x[2])
    for ws in session_websockets[session.session_name]:
        await ws.send_json({
            "type": "TURN_QUEUE_UPDATE",
            "payload": {
                "turn_queue": [
                    {"character": c.name, "next_turn": nt}
                    for c, _, nt in sorted_queue
                ],
                "turn_time": session.turn_time
            }
        })
```

---

## Error Handling

### Request Validation

```python
from pydantic import ValidationError

class Request(BaseModel):
    player_id: str
    request_text: str
    timestamp: float
    character: Character

try:
    request = Request(**data)
except ValidationError as e:
    await websocket.send_json({
        "type": "ERROR",
        "payload": {"message": "Invalid request format", "details": e.errors()}
    })
    return
```

### Queue Timeout Handling

```python
def wait_for_request(self, timeout: Optional[float] = None) -> Optional[Request]:
    try:
        return self.request_queue.get(timeout=timeout)
    except Empty:
        return None  # Handle timeout gracefully
```

### Session State Errors

```python
if not session.current_scene:
    await websocket.send_json({
        "type": "ERROR",
        "payload": {"message": "No current scene loaded"}
    })
```

---

## Security Considerations

### 1. Authentication

- Implement player authentication before joining session
- Validate `player_id` matches authenticated user
- Use JWT tokens for WebSocket connections

### 2. Input Validation

- Sanitize all `request_text` inputs
- Validate character actions against game rules
- Use Pydantic models for strict type validation

### 3. Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.websocket("/ws/{session_id}/{player_id}")
@limiter.limit("10/second")  # Max 10 messages per second
async def websocket_endpoint(...):
    ...
```

### 4. GM Secrets Protection

**Never send `gm_secret` field to clients:**

```python
def serialize_scene(scene: SceneNode) -> dict:
    data = scene.dict()
    data.pop("gm_secret", None)  # Remove sensitive info
    return data
```

---

## Implementation Checklist

### Phase 1: Core Server

- [ ] Set up FastAPI with WebSocket support
- [ ] Implement `GameDelivery` class extending `Delivery`
- [ ] Create WebSocket endpoint for player connections
- [ ] Implement request queue handling
- [ ] Set up event pool subscription

### Phase 2: Session Management

- [ ] Create session CRUD endpoints (REST)
- [ ] Implement player join/leave logic
- [ ] Add session state serialization
- [ ] Handle session cleanup on disconnect

### Phase 3: Real-time Updates

- [ ] Forward game events to WebSocket clients
- [ ] Broadcast session updates
- [ ] Implement turn queue notifications
- [ ] Send scene updates on changes

### Phase 4: Game Flow

- [ ] Implement `master_message` WebSocket handler
- [ ] Implement `player_request` flow
- [ ] Implement `choose_player` selection
- [ ] Add `session_updated` callback

### Phase 5: Polish

- [ ] Add error handling and logging
- [ ] Implement authentication
- [ ] Add rate limiting
- [ ] Write API documentation
- [ ] Create client SDK/types

---

## Example Server Structure

```
UI/
├── server/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── websocket.py         # WebSocket handlers
│   ├── routes.py            # REST endpoints
│   ├── delivery.py          # GameDelivery implementation
│   ├── session_manager.py   # Session lifecycle
│   └── models.py            # Pydantic models for API
├── client/
│   ├── (your frontend code)
├── server_requirements.md   # This file
└── README.md
```

---

## Quick Start Example

```python
# server/main.py
from fastapi import FastAPI, WebSocket
from game.event_pool import EventPool
from interface.delivery import Delivery
from schemas.orchestration import Event
import asyncio

app = FastAPI()
event_pool = EventPool()

class GameDelivery(Delivery):
    def master_message(self, text: str, tag: str | None = None):
        # Broadcast to all connected UI clients
        pass
    
    def player_request(self, character: Character) -> str:
        # Wait for WebSocket message
        pass
    
    def choose_player(self, session: Session) -> Player:
        # Let UI select player
        pass
    
    def session_updated(self, session: Session) -> None:
        # Send session state to UI
        pass

@app.websocket("/ws/{session_id}/{player_id}")
async def connect(websocket: WebSocket, session_id: str, player_id: str):
    await websocket.accept()
    # ... connection logic
```

---

## Contact & Support

For questions about the game engine integration, refer to:
- `interface/delivery.py` - Core delivery interface
- `game/event_pool.py` - Event pub/sub system
- `schemas/in_game.py` - Game data models
- `schemas/orchestration.py` - Event and message schemas
