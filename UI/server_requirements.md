# Server Requirements for MAGGxDND UI

## Overview

This document defines the requirements for a **WebSocket-based game server** that enables the React/TypeScript UI to interact with the MAGGxDND Python game engine. The server must expose all functionality defined in `interface/delivery.py` and support real-time bidirectional communication.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Server Requirements](#core-server-requirements)
3. [WebSocket API Specification](#websocket-api-specification)
4. [REST API Specification](#rest-api-specification)
5. [Data Models](#data-models)
6. [Event System](#event-system)
7. [Session Management](#session-management)
8. [Turn-Based Combat System](#turn-based-combat-system)
9. [Spatial System](#spatial-system)
10. [Error Handling](#error-handling)
11. [Security Considerations](#security-considerations)
12. [Implementation Checklist](#implementation-checklist)

---

## Architecture Overview

### System Structure

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         UI Layer (React + TypeScript)                    │
│  C:\VS_Code\MAGGxDND\UI\                                                │
│  - Components for scene visualization, character status, turn queue     │
│  - WebSocket client for real-time communication                         │
│  - State management with Zustand                                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ WebSocket + REST
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Game Server (Python - FastAPI)                     │
│  C:\VS_Code\MAGGxDND\UI\server\ (TO BE CREATED)                         │
│  - WebSocket handlers for real-time game events                         │
│  - REST endpoints for session management                                │
│  - GameDelivery implementation extending Delivery ABC                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Direct Python imports
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Game Engine (Python Core)                          │
│  C:\VS_Code\MAGGxDND\                                                   │
│  - interface/delivery.py (Abstract Delivery class)                      │
│  - game/engine.py (Session management, game loop)                       │
│  - game/event_pool.py (Pub/Sub event system)                            │
│  - entity/player.py, entity/npc.py (Character entities)                 │
│  - schemas/in_game.py (Pydantic data models)                            │
│  - schemas/orchestration.py (Event schemas)                             │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Components from `delivery.py`

The `Delivery` abstract base class defines **four core abstract methods** that the server MUST implement:

| Method | Purpose | UI Equivalent |
|--------|---------|---------------|
| `master_message(text, tag)` | Display GM/DM narration messages | Toast/notification component |
| `player_request(character)` | Allow players to submit actions | Action input form |
| `choose_player(session)` | Select which player acts next | Player selection UI |
| `session_updated(session)` | Callback when session state changes | State synchronization |

### Inherited Queue Methods

The `Delivery` class provides these **thread-safe queue operations**:

```python
put_request(request: Request)           # Add player request
has_requests() -> bool                  # Check if queue has requests
get_first_request() -> Optional[Request]  # Get oldest request
get_first_request_by_player(player_id: str) -> Optional[Request]
wait_for_request(timeout: float) -> Optional[Request]
wait_for_request_from_player(player_id: str, timeout: float) -> Optional[Request]
```

---

## Core Server Requirements

### 1. WebSocket Server Framework

**Required:** Python FastAPI with WebSocket support

```python
# server/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from game.event_pool import EventPool, SubscriberQueue
from interface.delivery import Delivery
from logging import Logger

app = FastAPI(title="MAGGxDND Game Server")
event_pool = EventPool()
```

### 2. Threading & Concurrency

**CRITICAL:** The server MUST be thread-safe:
- `Delivery` class uses `threading.Lock` for queue operations
- `EventPool` uses `threading.RLock` for recursive locking
- Request queues use Python's `queue.Queue` (thread-safe by design)
- WebSocket handlers MUST use `asyncio` for non-blocking I/O

### 3. Event Subscription Architecture

Each player/NPC must have a **dedicated event queue**:

```python
# Each player subscribes to their own queue
player_queue: SubscriberQueue = event_pool.subscribe("Player1")

# Events are published to all except initiator
player_queue.publish_to_others(event)

# Or broadcast to all
event_pool.add_event(event)
```

**Event Flow:**
1. Game engine publishes events to `EventPool`
2. `EventPool` distributes to all subscriber queues based on routing rules
3. Server forwards events from queues to WebSocket clients in real-time
4. UI receives and displays events

### 4. Request Queue System

The server must maintain a **request queue per delivery instance**:

```python
from queue import Queue
from schemas.in_game import Character

class GameDelivery(Delivery):
    """WebSocket-based delivery implementation."""

    def __init__(self, event_queue: SubscriberQueue, logger: Logger):
        super().__init__(event_queue, logger)
        # self.request_queue is inherited from Delivery
        # self.game_event_queue is set by parent

    def master_message(self, text: str, tag: str | None = None):
        """Broadcast GM message to all connected UI clients."""
        # Implementation: Send via WebSocket to all clients

    def player_request(self, character: Character) -> str:
        """Wait for player input via WebSocket."""
        # Implementation: Block until WebSocket message received

    def choose_player(self, session: "Session") -> "Player":
        """Let UI select which player acts next."""
        # Implementation: Send player list, wait for selection

    def session_updated(self, session: "Session") -> None:
        """Broadcast session state to all clients."""
        # Implementation: Serialize and send via WebSocket
```

---

## WebSocket API Specification

### Connection Endpoint

```
ws://localhost:8000/ws/{session_id}/{player_id}
```

**Parameters:**
- `session_id` (string): Unique session identifier
- `player_id` (string): Player character name or ID

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
        timestamp: number;  // Unix timestamp
    };
}

// Choose Player Action (for GM)
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

// Meta Request (out-of-character)
interface MetaRequest {
    type: "META_REQUEST";
    payload: {
        player_id: string;
        message: string;
    };
}
```

#### Server → Client Messages

```typescript
// Master Message (GM narration)
interface MasterMessage {
    type: "MASTER_MESSAGE";
    payload: {
        text: string;
        tag?: "Clarification" | "Illegal" | "Meta" | string;
    };
}

// Session Update (full state sync)
interface SessionUpdate {
    type: "SESSION_UPDATE";
    payload: {
        session: SerializedSession;
    };
}

// Game Event (incremental update)
interface GameEvent {
    type: "GAME_EVENT";
    payload: {
        event: Event;
    };
}

// Action Request (prompt for input)
interface ActionRequest {
    type: "ACTION_REQUEST";
    payload: {
        character: Character;
        prompt?: string;
    };
}

// Turn Queue Update
interface TurnQueueUpdate {
    type: "TURN_QUEUE_UPDATE";
    payload: {
        turn_queue: Array<{
            character_name: string;
            character_type: "player" | "npc" | "round_determinator";
            next_turn: number;
            is_next: boolean;
        }>;
        turn_time: number;  // Global game time
    };
}

// Scene Update
interface SceneUpdate {
    type: "SCENE_UPDATE";
    payload: {
        scene: {
            name: string;
            description: string;
            objects: SerializedObject[];
            center_position: { x: number; y: number };
            dimensions: { x: number; y: number };
            scale_unit: string;
        };
        players: SerializedCharacter[];
        npcs: SerializedCharacter[];
        objects: SerializedObject[];
    };
}

// Character Status Update
interface CharacterStatusUpdate {
    type: "CHARACTER_STATUS_UPDATE";
    payload: {
        character_name: string;
        current_hp: number;
        max_hp: number;
        temp_hp: number;
        active_conditions: Condition[];
        position: { x: number; y: number };
    };
}

// Error Message
interface ErrorMessage {
    type: "ERROR";
    payload: {
        message: string;
        details?: string;
        code?: string;
    };
}
```

### WebSocket Handler Example

```python
# server/websocket_handler.py
from fastapi import WebSocket
from interface.delivery import Request
import asyncio
import time

class WebSocketHandler:
    def __init__(self, session, delivery: GameDelivery, event_queue: SubscriberQueue):
        self.session = session
        self.delivery = delivery
        self.event_queue = event_queue
        self.websocket: WebSocket | None = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.websocket = websocket

        # Send initial session state
        await self.send_session_update()

        # Start event listener task
        asyncio.create_task(self.listen_for_events())

    async def receive_message(self, data: dict):
        """Handle incoming WebSocket messages."""
        msg_type = data.get("type")
        payload = data.get("payload", {})

        if msg_type == "PLAYER_ACTION":
            # Create Request object and add to queue
            request = Request(
                player_id=payload["player_id"],
                request_text=payload["request_text"],
                timestamp=payload["timestamp"],
                character=Character(**payload["character"])
            )
            self.delivery.put_request(request)

        elif msg_type == "CHOOSE_PLAYER":
            # Handle player selection
            selected_id = payload["selected_player_id"]
            player = next(p for p in self.session.players if p.character.name == selected_id)
            # Store selection for choose_player() method
            self._pending_player_choice = player

        elif msg_type == "SUBSCRIBE_EVENTS":
            # Already subscribed via event_queue, just acknowledge
            await self.websocket.send_json({
                "type": "SUBSCRIBED",
                "payload": {"subscriber_id": payload["subscriber_id"]}
            })

    async def send_session_update(self):
        """Send full session state to client."""
        if self.websocket:
            await self.websocket.send_json({
                "type": "SESSION_UPDATE",
                "payload": {
                    "session": self._serialize_session(self.session)
                }
            })

    async def send_master_message(self, text: str, tag: str | None = None):
        """Send GM message to client."""
        if self.websocket:
            await self.websocket.send_json({
                "type": "MASTER_MESSAGE",
                "payload": {"text": text, "tag": tag}
            })

    async def listen_for_events(self):
        """Continuously listen for events from event_queue and forward to client."""
        while self.websocket:
            event = self.event_queue.get()
            if event:
                await self.websocket.send_json({
                    "type": "GAME_EVENT",
                    "payload": {"event": event.dict()}
                })
            else:
                # No event available, wait briefly before checking again
                await asyncio.sleep(0.1)

    def _serialize_session(self, session) -> dict:
        """Convert Session object to JSON-serializable dict."""
        # Remove gm_secret from scenes
        # Convert all Pydantic models to dicts
        # Handle circular references
        ...
```

---

## REST API Specification

### Session Management Endpoints

#### Create Session
```http
POST /api/sessions
Content-Type: application/json

{
    "session_name": "My Campaign",
    "game_mode": "COMBAT",
    "spatial_enabled": true
}
```

**Response:**
```json
{
    "session_id": "uuid-here",
    "status": "created"
}
```

#### Join Session
```http
POST /api/sessions/{session_id}/players
Content-Type: application/json

{
    "character": { /* Character schema */ },
    "player_name": "Player1"
}
```

#### Get Session State
```http
GET /api/sessions/{session_id}
```

#### End Session
```http
DELETE /api/sessions/{session_id}
```

### Character Management Endpoints

#### Add Character to Session
```http
POST /api/sessions/{session_id}/characters
Content-Type: application/json

{
    "character": { /* Character schema */ },
    "is_player": true
}
```

#### Update Character
```http
PUT /api/sessions/{session_id}/characters/{character_name}
Content-Type: application/json

{
    "current_hp": 25,
    "position": { "x": 5.0, "y": 10.0 }
}
```

#### Remove Character
```http
DELETE /api/sessions/{session_id}/characters/{character_name}
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
    level: number;  // 1-20
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

    // Inventory & State
    inventory: Item[];
    active_conditions_list: Condition[];
    resources: Record<string, number>;

    // Spatial
    position: { x: number; y: number };

    // Abilities
    abilities: SpellAbility[];

    // Computed (auto-generated on serialization)
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

    // Turn-based system
    turn_queue: Array<[Character, number, number]>;  // [character, time_added, next_turn]
    turn_time: number;  // Global game time

    // Location
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
    // gm_secret is SERVER-SIDE ONLY - never send to client
    objects: UnifiedObject[];
    center_position: { x: number; y: number };
    dimensions: { x: number; y: number };
    scale_unit: string;
}
```

### UnifiedObject Schema

```typescript
interface UnifiedObject {
    // Core
    id?: string;
    name: string;
    description?: string;

    // Type
    obj_type?: "Prop" | "Container" | "Interactable";
    state?: string;  // "closed", "open", "broken", "active"

    // Properties
    quantity: number;
    is_equipped: boolean;

    // Combat
    damage_dice?: string;  // e.g., "1d8"
    damage_type?: "Slashing" | "Piercing" | "Bludgeoning" | "Fire" | "Cold" | "Lightning";

    // Interaction
    is_locked?: boolean;
    is_hidden?: boolean;

    // Container
    content?: string[];
    capacity?: number;
    contained_objects?: UnifiedObject[];

    // Spatial
    position?: { x: number; y: number };

    // Metadata
    tags?: string[];
    item_description?: string;

    // Computed
    short_summary: string;
}
```

### Condition Schema

```typescript
interface Condition {
    name: string;
    rounds_remaining?: number;
    trigger: "End of Round" | "Passive" | "On Action";
    periodic_effect_description: string;
    short_summary: string;
}
```

### SpellAbility Schema

```typescript
interface SpellAbility {
    name: string;
    level: number;  // 0-9
    description: string;
    duration: string;
    damage_dice?: string;
    damage_type?: string;
    healing_dice?: string;
    tags: string[];
    short_summary: string;
}
```

### Event Schema

Based on `schemas/orchestration.py`:

```typescript
interface Event {
    event_type: EventType;
    event_initiator?: string;
    event_subject?: string;
    event_target?: string;
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

# Or broadcast to all
event_pool.add_event(event)
```

### Event Routing Rules

| Event Type | Recipients |
|------------|------------|
| `CHARACTER_MOVEMENT` | All players in same scene |
| `CHARACTER_STATUS_CHANGE` | All players |
| `ITEM_PICKUP` | All players in same scene |
| `MASTER_MESSAGE` | All players |
| `SYSTEM` | All players |

---

## Session Management

### Session Lifecycle

1. **Create Session**
   ```python
   session = Session(
       session_name="example_session",
       chroma_client=chroma_client,
       logger=engine_logger,
       generator=generator,
       event_pool=event_pool,
       delivery=game_delivery
   )
   ```

2. **Initialize Players**
   ```python
   player = session._init_player(character, orchestrator)
   ```

3. **Initialize NPCs**
   ```python
   session.init_new_session(
       scene=scene,
       player_characters=[ch1, ch2],
       npcs=[npc1],
       npc_logger=npc_logger,
       player_logger=player_logger
   )
   ```

4. **Run Game Loop**
   ```python
   asyncio.run(session.game_loop())
   ```

### Turn Queue System

The turn queue structure from `delivery.py`:

```python
# Turn queue structure:
# [(character, time_added, next_turn), ...]
# Sorted by next_turn to determine action order

def _print_turn_queue(self, session):
    sorted_queue = sorted(session.turn_queue, key=lambda x: x[2])
    for i, (char, time_added, next_turn) in enumerate(sorted_queue):
        is_next = i == 0
        # Display turn order
```

**Initiative Calculation:**
```python
# From Character schema
initiative_bonus = stats.dexterity + speed
```

---

## Spatial System

### Scene Grid Visualization

Based on `draw_ascii_scene()` in `delivery.py`:

```python
# Grid calculation for visualization
grid_size = 20  # Fixed grid size
x_scale = grid_size / width
y_scale = grid_size / height

# Map position to grid
grid_x = int((char.position.x - min_x) * x_scale)
grid_y = int((char.position.y - min_y) * y_scale)
```

### Position Updates

```typescript
// Character movement event
interface CharacterMovement {
    type: "CHARACTER_MOVEMENT";
    payload: {
        character_name: string;
        from: { x: number; y: number };
        to: { x: number; y: number };
    };
}
```

---

## Error Handling

### Request Validation

```python
from pydantic import ValidationError

try:
    request = Request(**data)
except ValidationError as e:
    await websocket.send_json({
        "type": "ERROR",
        "payload": {
            "message": "Invalid request format",
            "details": e.errors()
        }
    })
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
- Use JWT tokens for WebSocket connections:
  ```
  ws://localhost:8000/ws/{session_id}/{player_id}?token={jwt_token}
  ```

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

**CRITICAL:** Never send `gm_secret` field to clients:

```python
def serialize_scene(scene: SceneNode) -> dict:
    data = scene.dict()
    data.pop("gm_secret", None)  # Remove sensitive info
    data.pop("gm_secrets", None)  # Also check plural form
    return data
```

### 5. CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Implementation Checklist

### Phase 1: Core Server Setup

- [ ] Set up FastAPI project structure in `UI/server/`
- [ ] Create `GameDelivery` class extending `Delivery` ABC
- [ ] Implement WebSocket endpoint `/ws/{session_id}/{player_id}`
- [ ] Implement request queue handling (`put_request`, `get_first_request`, etc.)
- [ ] Set up event pool subscription for each player
- [ ] Create basic WebSocket message handlers

### Phase 2: Session Management (REST)

- [ ] Create session CRUD endpoints (`POST /api/sessions`, `GET`, `DELETE`)
- [ ] Implement player join/leave logic
- [ ] Add session state serialization (remove `gm_secret`)
- [ ] Handle session cleanup on disconnect
- [ ] Implement character management endpoints

### Phase 3: Real-time Updates (WebSocket)

- [ ] Forward game events from `event_queue` to WebSocket clients
- [ ] Broadcast session updates on state changes
- [ ] Implement turn queue notifications
- [ ] Send scene updates on changes
- [ ] Implement character status updates

### Phase 4: Game Flow Implementation

- [ ] Implement `master_message` WebSocket handler (broadcast to all)
- [ ] Implement `player_request` flow (wait for WebSocket message)
- [ ] Implement `choose_player` selection (send list, wait for choice)
- [ ] Add `session_updated` callback (broadcast state)
- [ ] Handle turn-based combat flow

### Phase 5: Spatial System

- [ ] Implement scene grid calculation logic
- [ ] Send position updates on character movement
- [ ] Visualize players, NPCs, and objects on grid
- [ ] Handle coordinate transformations (scene → grid)

### Phase 6: Polish & Security

- [ ] Add comprehensive error handling
- [ ] Implement JWT authentication
- [ ] Add rate limiting
- [ ] Write API documentation (OpenAPI/Swagger)
- [ ] Create TypeScript types for client
- [ ] Add logging and monitoring
- [ ] Write unit tests for server logic

---

## Server Project Structure

```
UI/
├── server/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Server configuration
│   ├── websocket/
│   │   ├── __init__.py
│   │   ├── handlers.py      # WebSocket message handlers
│   │   └── manager.py       # Connection manager
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── sessions.py      # Session REST endpoints
│   │   └── characters.py    # Character REST endpoints
│   ├── delivery/
│   │   ├── __init__.py
│   │   └── game_delivery.py # GameDelivery implementation
│   ├── session_manager.py   # Session lifecycle management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── api.py           # Pydantic models for API
│   │   └── serializers.py   # Session/Character serializers
│   └── middleware/
│       ├── __init__.py
│       ├── auth.py          # JWT authentication
│       └── rate_limit.py    # Rate limiting
├── client/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom React hooks
│   │   ├── store/           # Zustand state management
│   │   ├── services/        # API & WebSocket clients
│   │   └── types/           # TypeScript type definitions
│   ├── package.json
│   └── vite.config.ts
├── server_requirements.md   # This file
└── README.md
```

---

## Quick Start Example

```python
# server/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from game.event_pool import EventPool
from interface.delivery import Delivery
from schemas.in_game import Character
from schemas.orchestration import Event
import asyncio
import logging

app = FastAPI(title="MAGGxDND Game Server")
event_pool = EventPool()
logger = logging.getLogger("server")

# Store active sessions and connections
sessions: dict[str, Session] = {}
connections: dict[str, WebSocketHandler] = {}


class GameDelivery(Delivery):
    """WebSocket-based delivery implementation."""

    def __init__(self, event_queue: SubscriberQueue, logger: Logger):
        super().__init__(event_queue, logger)
        self.connections: list[WebSocketHandler] = []

    def master_message(self, text: str, tag: str | None = None):
        """Broadcast GM message to all connected clients."""
        for conn in self.connections:
            asyncio.create_task(conn.send_master_message(text, tag))

    def player_request(self, character: Character) -> str:
        """Wait for player input - blocking call."""
        # Check queue first
        request = self.get_first_request_by_player(character.name)
        if request:
            return request.request_text

        # Wait for WebSocket message (handled in WebSocketHandler)
        # This is a simplified example - actual implementation needs async handling
        raise NotImplementedError("Requires async WebSocket handling")

    def choose_player(self, session: "Session") -> "Player":
        """Let UI select player - blocking call."""
        # Send player list to UI, wait for selection
        # Actual implementation needs async handling
        raise NotImplementedError("Requires async WebSocket handling")

    def session_updated(self, session: "Session") -> None:
        """Broadcast session state to all clients."""
        for conn in self.connections:
            asyncio.create_task(conn.send_session_update())


@app.websocket("/ws/{session_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, player_id: str):
    """Handle WebSocket connections."""
    if session_id not in sessions:
        await websocket.close(code=4004, reason="Session not found")
        return

    session = sessions[session_id]
    event_queue = event_pool.subscribe(player_id)

    handler = WebSocketHandler(session, session.delivery, event_queue)
    await handler.connect(websocket)
    connections[f"{session_id}:{player_id}"] = handler

    try:
        while True:
            data = await websocket.receive_json()
            await handler.receive_message(data)
    except WebSocketDisconnect:
        event_pool.unsubscribe(player_id)
        del connections[f"{session_id}:{player_id}"]
        logger.info(f"Player {player_id} disconnected from session {session_id}")


# Start server with: uvicorn server.main:app --reload
```

---

## Dependencies

### Server (Python)

```txt
# requirements-server.txt
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
websockets>=12.0
pydantic>=2.0
python-jose[cryptography]  # JWT
slowapi>=0.1.9  # Rate limiting
```

### Client (TypeScript/React)

Already defined in `package.json`:
- React 19
- Zustand (state management)
- Axios (HTTP client)

---

## Testing

### Server Tests

```python
# tests/test_delivery.py
import pytest
from server.delivery.game_delivery import GameDelivery
from game.event_pool import EventPool

def test_put_request():
    event_pool = EventPool()
    queue = event_pool.subscribe("test")
    delivery = GameDelivery(queue, logger)

    request = Request(
        player_id="Player1",
        request_text="Attack the goblin",
        timestamp=1234567890.0,
        character=test_character
    )

    delivery.put_request(request)
    assert delivery.has_requests()

    retrieved = delivery.get_first_request()
    assert retrieved.player_id == "Player1"
    assert retrieved.request_text == "Attack the goblin"
```

### Client Tests

```typescript
// src/services/__tests__/websocket.test.ts
import { WebSocketService } from '../websocket';

test('connects to WebSocket server', async () => {
    const service = new WebSocketService('ws://localhost:8000/ws/test/Player1');
    await service.connect();
    expect(service.isConnected()).toBe(true);
});
```

---

## Contact & Support

For questions about the game engine integration, refer to:

| File | Purpose |
|------|---------|
| `interface/delivery.py` | Core delivery interface (ABC) |
| `interface/native_terminal_delivery.py` | Reference implementation |
| `game/event_pool.py` | Event pub/sub system |
| `game/engine.py` | Session and game loop |
| `schemas/in_game.py` | Game data models |
| `schemas/orchestration.py` | Event and message schemas |
| `entity/player.py` | Player entity |
| `entity/npc.py` | NPC entity |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-19 | Initial requirements based on `delivery.py` analysis |
