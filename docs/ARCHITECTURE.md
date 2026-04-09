# MAGGxDND Architecture Guide

## System Overview

MAGGxDND is a full-stack AI-powered D&D game engine with real-time multiplayer support. The system uses a **layered hexagonal architecture** with clear separation between frontend, backend API, game engine core, and AI components.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     FRONTEND (Browser)                              │
│  React 19 + TypeScript + Vite + Zustand                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │Components│  │  Store   │  │ Services │  │   Hooks  │           │
│  │  (58)    │←→│ (Zustand)│←→│API + WS  │  │          │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
└────────────────────────────┬────────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │ HTTP REST + WebSocket (ws://)│
              └──────────────┬──────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                     BACKEND (FastAPI)                               │
│  Python 3.11+                                                       │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │              API Layer (Routers)                         │      │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │      │
│  │  │ Sessions │  │   Auth   │  │  Users   │ │ Characters │  │      │
│  │  │   REST   │  │  JWT+OAuth│ │ Profiles │ │  Creation  │  │      │
│  │  └────┬─────┘  └──────────┘  └──────────┘ └────────────┘  │      │
│  │       │                                                     │      │
│  │  ┌────▼─────────────────────────────────────────────────┐  │      │
│  │  │          WebSocket Router                            │  │      │
│  │  │  /ws/{session_id}/{player_id}                        │  │      │
│  │  └────┬─────────────────────────────────────────────────┘  │      │
│  └───────┼─────────────────────────────────────────────────────┘      │
│          │                                                             │
│  ┌───────▼─────────────────────────────────────────────────────────┐  │
│  │              Session Management Layer                           │  │
│  │  ┌─────────────────────┐    ┌──────────────────────┐          │  │
│  │  │  SessionManager     │    │  SessionFactory       │          │  │
│  │  │  (Singleton Registry)│   │  (Dependency Builder) │          │  │
│  │  │  - Active sessions  │    │  - Creates sessions   │          │  │
│  │  │  - WebSocket track  │    │  - Injects deps       │          │  │
│  │  │  - Subscriber queues│    │  - Full isolation     │          │  │
│  │  └─────────┬───────────┘    └──────────┬───────────┘          │  │
│  └────────────┼────────────────────────────┼─────────────────────┘  │
│               │                            │                         │
│  ┌────────────▼────────────────────────────┼─────────────────────┐  │
│  │              Delivery Layer             │                      │  │
│  │  ┌──────────────────────┐              │                      │  │
│  │  │  GameDelivery        │              │                      │  │
│  │  │  (WebSocket bridge)  │◄─────────────┘                      │  │
│  │  │  - process_player_action()                                   │  │
│  │  │  - master_message()                                          │  │
│  │  │  - session_updated()                                         │  │
│  │  │  - send_*_update()                                           │  │
│  │  └──────────────────────┘                                      │  │
│  │  ┌──────────────────────┐                                      │  │
│  │  │  RESTAPIDelivery     │                                      │  │
│  │  │  (HTTP bridge)       │                                      │  │
│  │  │  - process_player_action()                                   │  │
│  │  │  - get_session_state()                                       │  │
│  │  └──────────────────────┘                                      │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │              Data Layer                                         │  │
│  │  ┌──────────────────┐  ┌──────────────────┐                    │  │
│  │  │  Database        │  │  Repositories    │                    │  │
│  │  │  SQLAlchemy ORM  │  │  - UserRepository│                    │  │
│  │  │  - users         │  │  - SessionRepo   │                    │  │
│  │  │  - game_sessions │  │                  │                    │  │
│  │  │  - access_groups │  │                  │                    │  │
│  │  └──────────────────┘  └──────────────────┘                    │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
┌───────────────────────────────▼───────────────────────────────────────┐
│                   CORE ENGINE (Platform-Agnostic)                     │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │              Session (Game State Holder)                        │  │
│  │  - players: List[Player]                                        │  │
│  │  - npcs: List[NPC]                                              │  │
│  │  - current_scene: SceneNode                                     │  │
│  │  - event_pool: EventPool                                        │  │
│  │  - delivery: Delivery                                           │  │
│  │  - orchestrator: Orchestrator                                   │  │
│  │  - manipulator: Manipulator                                     │  │
│  │  - turn_queue: List[(entity, action, priority)]                │  │
│  │  - location_graph: LocationGraph                                │  │
│  └───────────────┬─────────────────────────┬─────────────────────┘  │
│                  │                         │                          │
│  ┌───────────────▼──────────┐  ┌──────────▼──────────────────────┐  │
│  │    EventPool (Pub/Sub)   │  │     Orchestrator                │  │
│  │  - Subscriber queues     │  │  - Input classification         │  │
│  │  - Thread-safe           │  │  - Rule validation              │  │
│  │  - Event streaming       │  │  - Clarity checking             │  │
│  │                          │  │  - Story/Combat modes           │  │
│  │                          │  └──────────┬──────────────────────┘  │
│  └──────────────┬───────────┘             │                          │
│                 │                         │                          │
│  ┌──────────────▼─────────────────────────▼──────────────────────┐  │
│  │                    Manipulator                                 │  │
│  │  Routes events to specialized handlers:                        │  │
│  │  ┌──────────────────────────────────────────────────────┐     │  │
│  │  │  MeleeAttackManipulator  - Close combat              │     │  │
│  │  │  RangedAttackManipulator - Ranged weapons            │     │  │
│  │  │  MovementManipulator     - Character movement        │     │  │
│  │  │  ObjectTransferManip     - Item transfers            │     │  │
│  │  │  ItemInteractionManip    - Item use/pickup/drop      │     │  │
│  │  └──────────────────────────────────────────────────────┘     │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │              AI & Entity Layer                                  │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │  │
│  │  │  MAGG    │  │ Entities │  │ Schemas  │  │   Utils      │   │  │
│  │  │ (AI GM)  │  │Player/NPC│  │Pydantic  │  │ Dice/Spatial │   │  │
│  │  │ Gemini   │  │          │  │Models    │  │ Naming       │   │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────┘
```

## Communication Patterns

### The Delivery Pattern

The **Delivery** pattern is the core communication mechanism between the frontend and game engine. All game interactions flow through Delivery objects:

```
Browser → WebSocket → Delivery → Orchestrator → MAGG → Manipulator → Events → WebSocket → Browser
```

#### Delivery Interface

```python
# Abstract Delivery interface (core/interface/delivery.py)
class Delivery(ABC):
    @abstractmethod
    def master_message(self, text: str, tag: Optional[str] = None) -> None:
        """Broadcast GM narration to all players"""
    
    @abstractmethod
    def player_request(self, character: Character) -> str:
        """Prompt player for action"""
    
    @abstractmethod
    def choose_player(self, session: Session) -> Player:
        """Select next player turn"""
    
    @abstractmethod
    def session_updated(self, session: Session) -> None:
        """Notify clients of state changes"""
```

#### GameDelivery (WebSocket Implementation)

```python
# backend/src/delivery/game_delivery.py
class GameDelivery(Delivery):
    async def process_player_action(
        self, 
        character_name: str, 
        action_text: str, 
        player_id: Optional[str] = None
    ) -> dict:
        """Main input pipeline for player actions"""
        # 1. Find player in session
        # 2. Put request in delivery queue
        # 3. Process through orchestrator
        # 4. Execute events via manipulator
        # 5. Broadcast session update
        # 6. Return result dict
```

#### RESTAPIDelivery (HTTP Implementation)

```python
# backend/src/delivery/rest_api_delivery.py
class RESTAPIDelivery(Delivery):
    def process_player_action(self, character_name: str, action_text: str) -> dict:
        """Process action via REST API (synchronous)"""
        # Similar flow but synchronous
    
    def get_session_state(self) -> dict:
        """Get current session state for API"""
```

### Data Flow Examples

#### Player Action Flow

```
1. Player clicks "Submit Action" in browser
   ↓
2. Frontend sends action via WebSocket
   ws.send(JSON.stringify({
     type: "PLAYER_ACTION",
     character_name: "Aldric",
     action: "I attack the orc with my longsword"
   }))
   ↓
3. Backend WebSocket router receives message
   websocket_game.py::event_receiver()
   ↓
4. Router calls delivery
   await session.delivery.process_player_action(
     character_name="Aldric",
     action_text="I attack the orc with my longsword",
     player_id="player-uuid"
   )
   ↓
5. GameDelivery queues request and calls orchestrator
   orchestrator.character_action_combat(player)  # or story mode
   ↓
6. Orchestrator classifies input
   - Checks: CHARACTER_ACTION vs META_COMMENT
   - Validates: Follows combat rules?
   - Returns: OrchestrationVerdict
   ↓
7. Orchestrator calls MAGG (AI) for narrative
   magg.generate_verdict(...)
   ↓
8. MAGG returns narrative description
   "You swing your longsword at the orc..."
   ↓
9. Events generated (if any)
   - MELEE_ATTACK event
   ↓
10. Manipulator executes events
    manipulator.execute_events([melee_attack_event])
    ↓
11. MeleeAttackManipulator processes event
    - Calculates hit/miss
    - Rolls damage
    - Returns new events (damage applied)
    ↓
12. Events published to EventPool
    event_pool.publish(damage_event)
    ↓
13. EventPool broadcasts to all subscribers
    - All connected players receive event
    ↓
14. Event stream sender pushes via WebSocket
    event_stream_sender() → ws.send(event_data)
    ↓
15. Browser receives and displays result
    - Chat panel shows narration
    - Character panels update HP
    - Combat log shows damage
```

#### Session Creation Flow

```
1. User fills out session creation form
   - Session name, game mode, max players
   - Scene prompt, character prompts
   ↓
2. Frontend sends POST /api/v1/sessions
   Headers: { Authorization: "Bearer <token>" }
   Body: {
     session_name: "Dragon's Lair",
     game_mode: "COMBAT",
     max_players: 4,
     scene_prompt: "A dark cave with glowing crystals",
     character_prompts: ["A brave fighter", "A wise wizard"]
   }
   ↓
3. Backend authenticates user (JWT)
   get_current_user dependency
   ↓
4. Session router creates database record
   SessionRepository.create({
     session_uuid: uuid4(),
     owner_id: user.id,
     session_name: "Dragon's Lair",
     game_mode: "COMBAT",
     status: "waiting_room"
   })
   ↓
5. SessionFactory builds session
   SessionFactory.create_session(SessionConfig(...))
   ↓
6. Factory initializes dependencies
   a. ChromaClient (vector embeddings)
   b. Generator (AI via Gemini)
   c. EventPool (pub/sub system)
   d. GameDelivery (WebSocket bridge)
   e. Manipulator (event router)
   f. Orchestrator (input classifier)
   ↓
7. Session registered with SessionManager
   session_manager.register_session(session_id, session)
   ↓
8. AI generates initial content
   - Scene from prompt (or procedural fallback)
   - Characters from prompts (or procedural fallback)
   - NPCs if specified (or procedural fallback)
   ↓
9. Session returned to frontend
   Response: {
     session_id: "uuid",
     session_name: "Dragon's Lair",
     game_mode: "COMBAT",
     player_count: 1,
     status: "waiting_room",
     players: [...],
     npcs: [...]
   }
   ↓
10. Frontend navigates to waiting room
    Players can join, ready up, chat
```

## Component Details

### SessionManager

**Location**: `backend/src/game/session_manager.py`

**Purpose**: Singleton registry for active game sessions

**Key Methods**:
- `register_session(session_id, session)` - Add session to registry
- `get_session(session_id)` - Retrieve session by UUID
- `register_player_websocket(session_id, player_id, websocket)` - Track WS connection
- `get_player_websocket(session_id, player_id)` - Get player's WS
- `get_all_session_websockets(session_id)` - Get all WS for session
- `broadcast_to_session(session_id, message, exclude_player_id)` - Send to all

**Thread Safety**: Uses `asyncio.Lock` per session for concurrent access

### SessionFactory

**Location**: `backend/src/game/session_factory.py`

**Purpose**: Creates fully-initialized Session objects with all dependencies

**Creation Flow**:
```python
def create_session(self, config: SessionConfig) -> Session:
    # 1. Create ChromaClient for embeddings
    chroma_client = ChromaClient(...)
    
    # 2. Create Generator (AI interface)
    generator = Generator(chroma_client, config.gemini_model)
    
    # 3. Create EventPool
    event_pool = EventPool()
    
    # 4. Create delivery event queue
    delivery_event_queue = SubscriberQueue()
    event_pool.subscribe(delivery_event_queue)
    
    # 5. Create Session (without delivery)
    session = Session(
        session_name=config.session_name,
        chroma_client=chroma_client,
        logger=logger,
        generator=generator,
        event_pool=event_pool,
        delivery=None  # Will be injected
    )
    
    # 6. Create GameDelivery
    delivery = GameDelivery(
        session_id=session_id,
        session=session,  # Direct reference
        event_queue=delivery_event_queue,
        logger=logger.getChild("delivery")
    )
    
    # 7. Inject delivery into session
    session.delivery = delivery
    
    # 8. Set game mode
    session.game_mode = GameModes(config.game_mode)
    
    # 9. Create and inject Manipulator
    manipulator = self._create_manipulator(config, session, logger)
    session.inject_manipulator(manipulator)
    
    # 10. Create and inject Orchestrator
    orchestrator = self._create_orchestrator(config, session, logger)
    session._init_orchestrator(orchestrator)
    
    # 11. Initialize plot (if guide provided)
    if config.guide:
        session._init_plot(config.guide)
    
    # 12. Return ready session
    return session
```

### Orchestrator

**Location**: `core/entity/orchestrator.py`

**Purpose**: Classifies player input and validates against game rules

**Input Classification**:
- `CHARACTER_ACTION` - In-character action (move, attack, interact)
- `META_COMMENT` - Out-of-character comment (question, joke, instruction)

**Validation**:
- Story Mode: Checks narrative consistency
- Combat Mode: Validates combat rules (action economy, range, etc.)
- Clarity: Determines if action needs clarification

**Output**: `OrchestrationVerdict` with:
- `summary` - What happened (AI-generated narrative)
- `events` - List of events to execute
- `needs_clarification` - True if action unclear
- `clarification_question` - What to ask player

### Manipulator System

**Location**: `core/game/manipulator.py` + `core/game/manipulators/`

**Purpose**: Route events to specialized handlers

**Main Manipulator** (`core/game/manipulator.py`):
```python
class Manipulator:
    def execute_events(self, events: List[Event]) -> List[Event]:
        """Execute events by routing to appropriate handler"""
        new_events = []
        for event in events:
            manipulator = self._get_manipulator(event.event_type)
            if manipulator:
                new_events.extend(manipulator.execute(event, self))
        return new_events
    
    def _get_manipulator(self, event_type: str):
        """Get manipulator for event type"""
        mapping = {
            "MELEE_ATTACK": self.melee_attack_manipulator,
            "RANGED_ATTACK": self.ranged_attack_manipulator,
            "CHARACTER_MOVEMENT": self.movement_manipulator,
            "OBJECT_TRANSFER": self.object_transfer_manipulator,
            "ITEM_USE": self.item_interaction_manipulator,
            # ... more mappings
        }
        return mapping.get(event_type)
```

**Specialized Manipulators**:
- `MeleeAttackManipulator` - Handles close combat attacks
- `RangedAttackManipulator` - Handles ranged weapon attacks
- `MovementManipulator` - Handles character movement
- `ObjectTransferManipulator` - Handles item transfers
- `ItemInteractionManipulator` - Handles item use/pickup/drop

Each manipulator:
1. Receives an event
2. Validates event (legal move, valid target, etc.)
3. Applies changes to game state
4. Returns new events (side effects)

### EventPool

**Location**: `core/game/event_pool.py`

**Purpose**: Publish-subscribe event system

**Architecture**:
- Single `EventPool` per session
- Multiple `SubscriberQueue` objects (one per client)
- Thread-safe publishing and consumption
- Events consumed via `get_next_message()` (blocking)

**Usage**:
```python
# Publish event
event = Event(
    event_type=EventTypes.MELEE_ATTACK,
    event_initiator="Aldric",
    target="Orc Warrior",
    damage=12
)
event_pool.publish(event)

# Subscribe to events
queue = SubscriberQueue()
event_pool.subscribe(queue)

# Consume events (blocking)
event = queue.get_next_message()  # Blocks until event available
```

## Database Schema

### Tables

**users**:
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    group_id INTEGER REFERENCES access_groups(id),
    email VARCHAR(255)
)
```

**access_groups**:
```sql
CREATE TABLE access_groups (
    id INTEGER PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
)
```

**game_sessions**:
```sql
CREATE TABLE game_sessions (
    id INTEGER PRIMARY KEY,
    session_uuid VARCHAR(36) UNIQUE NOT NULL,
    owner_id INTEGER REFERENCES users(id),
    session_name VARCHAR(100) NOT NULL,
    game_mode VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    session_data JSON,  -- Complete session state
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
)
```

**session_data JSON structure**:
```json
{
  "description": "A dark cave with glowing crystals",
  "guide": "Players explore an abandoned mine",
  "max_players": 4,
  "is_public": false,
  "gemini_model": "gemini-flash-latest",
  "participants": [
    {
      "user_id": 1,
      "username": "Aldric",
      "character_name": "Aldric Stormwind",
      "connected": true,
      "role": "player",
      "is_ready": true
    }
  ],
  "players": [...],
  "npcs": [...],
  "scene": {...}
}
```

## Authentication Flow

### JWT Authentication

```
1. User logs in via /api/v1/auth/login/json
   Body: { username: "...", password: "..." }
   ↓
2. Backend validates credentials
   - Find user in database
   - Verify password with bcrypt
   ↓
3. Generate JWT token
   token = jwt.encode({
     "sub": user.username,
     "user_id": user.id,
     "exp": datetime.utcnow() + timedelta(hours=24)
   }, SECRET_KEY, algorithm="HS256")
   ↓
4. Return token
   Response: { access_token: "...", token_type: "bearer" }
   ↓
5. Frontend stores token
   - localStorage (persistent)
   - Zustand store (runtime)
   ↓
6. Frontend sends token with requests
   Headers: { Authorization: "Bearer <token>" }
   ↓
7. Backend validates token
   - Decode JWT
   - Check expiration
   - Extract user info
   ↓
8. Inject user into request
   get_current_user dependency
   ↓
9. Router uses current_user
   - Check ownership
   - Validate permissions
   - Log actions
```

### OAuth2 Flow (Google/Discord)

```
1. User clicks "Login with Google"
   ↓
2. Frontend redirects to OAuth URL
   https://accounts.google.com/o/oauth2/auth?
     client_id=...&
     redirect_uri=http://localhost:8000/api/v1/auth/google/callback&
     response_type=code&
     scope=email profile
   ↓
3. User authorizes application
   ↓
4. OAuth provider redirects back with code
   /api/v1/auth/google/callback?code=...
   ↓
5. Backend exchanges code for token
   token_response = requests.post(token_url, {
     code: "...",
     client_id: "...",
     client_secret: "...",
     redirect_uri: "..."
   })
   ↓
6. Backend fetches user info
   user_info = requests.get(user_info_url, {
     headers: { Authorization: "Bearer " + access_token }
   })
   ↓
7. Backend creates/finds user
   - Check if user exists (by email or provider ID)
   - Create if new
   ↓
8. Generate JWT token
   (same as password flow)
   ↓
9. Redirect to frontend with token
   http://localhost:3000/auth/callback?token=...
   ↓
10. Frontend extracts and stores token
    (continues as normal)
```

## Frontend Architecture

### Zustand Store Structure

```typescript
// frontend/src/store/gameStore.ts
interface GameState {
  // Auth
  token: string | null;
  userId: number | null;
  username: string | null;
  isGuest: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Characters
  characters: Character[];
  selectedCharacter: Character | null;
  activeCharacter: Character | null;
  
  // Sessions
  sessions: Session[];
  currentSession: Session | null;
  sceneData: SceneNode | null;
  
  // Messages
  messages: Message[];
  gameEvents: GameEvent[];
  turnQueue: TurnQueueEntry[];
  
  // UI
  mode: 'home' | 'waiting_room' | 'game' | 'character_creation';
  isDMThinking: boolean;
  
  // Actions
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  loadSessions: () => Promise<void>;
  createSession: (data: SessionCreateData) => Promise<Session>;
  joinSession: (sessionId: string) => Promise<void>;
  sendMessage: (message: string) => void;
  // ... more actions
}
```

### WebSocket Service

```typescript
// frontend/src/services/websocket.ts
class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  
  connect(sessionId: string, playerId: string, token: string) {
    const wsUrl = `ws://localhost:8000/ws/${sessionId}/${playerId}?token=${token}`;
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };
    
    this.ws.onclose = () => {
      this.reconnect(sessionId, playerId, token);
    };
  }
  
  private handleMessage(data: WebSocketMessage) {
    switch (data.type) {
      case 'MASTER_MESSAGE':
        // Add to chat
        break;
      case 'SESSION_UPDATE':
        // Update game state
        break;
      case 'CHARACTER_UPDATE':
        // Update character panel
        break;
      case 'COMBAT_EVENT':
        // Show combat animation
        break;
      // ... more message types
    }
  }
  
  send(message: WebSocketMessage) {
    this.ws?.send(JSON.stringify(message));
  }
  
  private reconnect(sessionId: string, playerId: string, token: string) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        this.connect(sessionId, playerId, token);
      }, 1000 * this.reconnectAttempts);
    }
  }
}
```

## Performance Considerations

### Backend Optimizations

1. **Database**:
   - WAL mode for better concurrent read/write
   - 64MB cache size
   - Foreign keys enabled
   - 5s busy timeout

2. **Session Isolation**:
   - Each session has its own EventPool
   - asyncio.Lock per session for thread safety
   - No shared state between sessions

3. **WebSocket**:
   - AsyncIO for non-blocking I/O
   - asyncio.create_task() for broadcasting
   - Connection tracking for efficient routing

4. **AI Calls**:
   - Procedural generation fallback when AI unavailable
   - Async AI processing where possible
   - Caching for repeated requests

### Frontend Optimizations

1. **State Management**:
   - Zustand for minimal boilerplate
   - Selective subscriptions to prevent re-renders
   - localStorage persistence for auth

2. **WebSocket**:
   - Auto-reconnect with exponential backoff
   - Heartbeat (PING/PONG) for connection health
   - Message batching for efficiency

3. **Components**:
   - React.memo for expensive components
   - Lazy loading for code splitting
   - Debounced input for search/filter

## Security Measures

1. **Authentication**:
   - JWT tokens with expiration
   - bcrypt password hashing (12 rounds)
   - OAuth2 for third-party login
   - Rate limiting (100/min default, 5/min for auth)

2. **Authorization**:
   - Session ownership checks
   - Role-based access control
   - Input validation and sanitization

3. **Data Protection**:
   - CORS configured for allowed origins
   - HTTPS in production
   - Secure cookie flags (HttpOnly, Secure, SameSite)
   - Input sanitization to prevent XSS

4. **Session Security**:
   - UUID session IDs (not sequential)
   - Token required for WebSocket connection
   - Connection tracking to prevent impersonation

## Testing Strategy

### Backend Tests

```python
# Unit tests
def test_session_creation():
    session = SessionFactory.create_session(config)
    assert session.session_name == "Test"
    assert len(session.players) == 0

# Integration tests
def test_player_action_flow():
    session = create_test_session()
    result = session.delivery.process_player_action(
        character_name="Aldric",
        action_text="I look around"
    )
    assert result['success'] == True
    assert result['dm_response'] != ""

# API tests
async def test_create_session_endpoint():
    async with AsyncClient() as client:
        response = await client.post(
            "/api/v1/sessions",
            json={"session_name": "Test", ...},
            headers={"Authorization": "Bearer ..."}
        )
        assert response.status_code == 201
```

### Frontend Tests

```typescript
// Component tests
test('GameSetup creates session', async () => {
  render(<GameSetup />);
  fireEvent.change(screen.getByLabelText('Session Name'), {
    target: { value: 'Test Session' }
  });
  fireEvent.click(screen.getByText('Create'));
  await waitFor(() => {
    expect(mockAPI.createSession).toHaveBeenCalledWith({
      session_name: 'Test Session'
    });
  });
});

// WebSocket tests
test('WebSocket reconnects on disconnect', async () => {
  const ws = new WebSocketService();
  ws.connect('session-id', 'player-id', 'token');
  
  // Simulate disconnect
  ws.ws?.close();
  
  // Verify reconnect attempt
  await waitFor(() => {
    expect(mockWebSocket.connect).toHaveBeenCalledTimes(2);
  });
});
```

## Deployment

### Development

```bash
# Terminal 1: Backend
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```

### Production

```bash
# Build frontend
cd frontend && npm run build

# Start backend (serves frontend)
python start.py
```

### Environment Variables

```bash
# .env file
GEMINI_API_KEY=your-api-key-here
DATABASE_URL=sqlite:///data/maggxdnd.db
SECRET_KEY=your-secret-key-here
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
DISCORD_CLIENT_ID=...
DISCORD_CLIENT_SECRET=...
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## Future Improvements

1. **Scalability**:
   - Redis for session storage (horizontal scaling)
   - Message queue for events (RabbitMQ, Kafka)
   - Load balancing for multiple backend instances

2. **Features**:
   - Voice chat integration
   - Dice rolling animations
   - Dynamic map rendering
   - NPC AI behavior trees
   - Campaign persistence

3. **Performance**:
   - GraphQL API alternative
   - WebSocket compression
   - CDN for static assets
   - Database connection pooling

4. **Developer Experience**:
   - API versioning
   - Better error messages
   - Debug mode with detailed logs
   - Hot reload for frontend+backend
