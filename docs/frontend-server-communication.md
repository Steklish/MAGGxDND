# Frontend-Server Communication Reference

Complete documentation of all event types and data structures exchanged between the frontend and server.

---

## Table of Contents

1. [WebSocket Server → Client Messages](#1-websocket-server--client-messages)
2. [WebSocket Client → Server Messages](#2-websocket-client--server-messages)
3. [Core Game Event Types](#3-core-game-event-types)
4. [REST API Response Types](#4-rest-api-response-types)
5. [Message Handling Flow](#5-message-handling-flow)
6. [Manipulator Event Mapping](#6-manipulator-event-mapping)

---

## 1. WebSocket Server → Client Messages

These are all message types the **backend sends** to the frontend via WebSocket.

### 1.1 CONNECTED

**Purpose:** Sent immediately after successful WebSocket connection  
**Defined in:** `backend/src/api/routers/websocket_game.py:241`  
**Handled in:** `frontend/src/services/websocket.ts:394`

```typescript
{
  type: "CONNECTED",
  session_id: string,
  player_id: string,
  message: "Successfully connected to game session"
}
```

**Frontend behavior:** Logs connection success, returns `null` (no store update)

---

### 1.2 MASTER_MESSAGE

**Purpose:** DM/GM narration or AI Game Master response, broadcast to all players  
**Defined in:** `backend/src/delivery/game_delivery.py:78`  
**Handled in:** `frontend/src/services/websocket.ts:398`, `frontend/src/store/gameStore.ts:390`

```typescript
{
  type: "MASTER_MESSAGE",
  text: string,
  tag: string | null
}
```

**Frontend normalizes to:**
```typescript
{
  type: "MASTER_MESSAGE",
  payload: {
    text: string,
    tag?: string
  }
}
```

**Frontend behavior:**
- Adds to chat messages as `{sender_name: "DM", text, type: "dm"}`
- Clears `isDMThinking` state (shows DM finished processing)

---

### 1.3 SESSION_UPDATE

**Purpose:** Full session state broadcast, sent after major state changes  
**Defined in:** `backend/src/delivery/game_delivery.py:157`  
**Handled in:** `frontend/src/services/websocket.ts:408`, `frontend/src/store/gameStore.ts:420`

```typescript
{
  type: "SESSION_UPDATE",
  payload: {
    session: {
      // Full session state from session.get_session_state()
      // Includes: players, npcs, current_scene, game_mode, messages, etc.
    }
  }
}
```

**Frontend normalizes to:**
```typescript
{
  type: "SESSION_UPDATE",
  payload: {
    session: Session
  }
}
```

**Frontend behavior:**
- If `current_scene` is present, updates `currentScene` in store
- Provides complete session synchronization

---

### 1.4 TURN_UPDATE

**Purpose:** Notifies whose turn it is in combat mode  
**Defined in:** `backend/src/delivery/game_delivery.py:146`  
**Handled in:** `frontend/src/services/websocket.ts:417-418`, `frontend/src/store/gameStore.ts:437-438`

```typescript
{
  type: "TURN_UPDATE",
  active_player_id: string | null,
  active_player_name: string
}
```

**Frontend normalizes to:**
```typescript
{
  type: "TURN_QUEUE_UPDATE",
  payload: {
    turn_queue: [{
      character_name: string,
      type: string,
      is_active: true
    }],
    turn_time: number
  }
}
```

**Frontend behavior:**
- Creates minimal single-entry turn queue
- Shows whose turn it is in the UI

---

### 1.5 TURN_QUEUE_UPDATE

**Purpose:** Full turn order update with complete queue  
**Defined in:** Frontend handles this as alternative to `TURN_UPDATE`  
**Handled in:** `frontend/src/services/websocket.ts:417`, `frontend/src/store/gameStore.ts:437`

```typescript
{
  type: "TURN_QUEUE_UPDATE",
  payload: {
    turn_queue: Array<{
      character: string,
      next_turn: number
    }>,
    turn_time: number
  }
}
```

**Frontend behavior:**
- Updates `turnQueue` store with full queue
- Displays turn order in TurnQueue component

---

### 1.6 PLAYER_REQUEST

**Purpose:** Signals game engine is waiting for player input in COMBAT mode  
**Defined in:** `backend/src/delivery/game_delivery.py:104`  
**Handled in:** ⚠️ **NOT HANDLED** in frontend switch/case (would fall to default)

```typescript
{
  type: "PLAYER_REQUEST",
  character_id: string | null,
  character_name: string
}
```

**⚠️ Issue:** This type is sent by backend but not explicitly handled in frontend. Would need a case statement to properly prompt the player.

---

### 1.7 GAME_EVENT

**Purpose:** Core game events from EventPool (combat, movement, items, etc.)  
**Defined in:** `backend/src/api/routers/websocket_game.py:46` (event_stream_sender)  
**Handled in:** `frontend/src/services/websocket.ts:489`, `frontend/src/store/gameStore.ts:402`

```typescript
{
  type: "GAME_EVENT",
  payload: {
    event: {
      event_type: string,
      event_initiator: string | null,
      event_subject: string | null,
      event_target: string | null,
      description: string
    }
  }
}
```

**Frontend normalizes to:**
```typescript
{
  type: "GAME_EVENT",
  payload: {
    event: Event
  }
}
```

**Frontend behavior:**
- Adds to `events` array
- Adds to chat messages as `{sender_name: "Game", text: event.description, type: "event"}`

---

### 1.8 ACTION_CONFIRMED

**Purpose:** Acknowledgment when unknown event type is received by server  
**Defined in:** `backend/src/api/routers/websocket_game.py:166`  
**Handled in:** `frontend/src/services/websocket.ts:457`

```typescript
{
  type: "ACTION_CONFIRMED",
  event: {
    event_type: string,
    data: any
  }
}
```

**Frontend behavior:**
- Converts to `GAME_EVENT` with `event_type: "ACTION_RESULT"`
- Description: `"Action confirmed: ..."`

---

### 1.9 ACTION_REQUEST

**Purpose:** Prompt for specific character action  
**Defined in:** Frontend type definitions only  
**Handled in:** `frontend/src/services/websocket.ts:448`

```typescript
{
  type: "ACTION_REQUEST",
  payload: {
    character: Character
  }
}
```

**⚠️ Issue:** Frontend handles this type but backend does not currently emit it.

---

### 1.10 ACTION_RESULT

**Purpose:** Direct action processing result (primarily from REST API fallback)  
**Defined in:** Frontend handling only  
**Handled in:** `frontend/src/services/websocket.ts:472`, `frontend/src/store/gameStore.ts:458`

```typescript
{
  type: "ACTION_RESULT",
  success: boolean,
  dm_response: string,
  game_state: any,
  error: string | null
}
```

**Frontend behavior:**
- Clears `isDMThinking` state
- Does NOT add DM response to chat (that arrives via `MASTER_MESSAGE`)
- Used primarily for REST API action processing fallback

---

### 1.11 SCENE_UPDATE

**Purpose:** Scene change notification  
**Defined in:** Frontend type definitions  
**Handled in:** `frontend/src/services/websocket.ts:498`, `frontend/src/store/gameStore.ts:430`

```typescript
{
  type: "SCENE_UPDATE",
  payload: {
    scene: SceneNode,
    characters: Character[],
    npcs: NPCCharacter[],
    objects: UnifiedObject[]
  }
}
```

**Frontend behavior:**
- Updates `currentScene` in store
- **⚠️ Issue:** Not currently emitted by backend WebSocket, only handled

---

### 1.12 CHARACTER_STATUS_UPDATE

**Purpose:** Character status change notification  
**Defined in:** Frontend handling only  
**Handled in:** `frontend/src/services/websocket.ts:510`

```typescript
{
  type: "CHARACTER_STATUS_UPDATE",
  payload: {
    character_name: string,
    event_type: string,
    description: string
  }
}
```

**Frontend behavior:**
- Converts to `GAME_EVENT` with payload data as event
- Not a full Character object, just event notification

---

### 1.13 ERROR

**Purpose:** Error notification  
**Defined in:** `backend/src/api/routers/websocket_game.py:106,122`  
**Handled in:** `frontend/src/services/websocket.ts:522`, `frontend/src/store/gameStore.ts:445`

```typescript
{
  type: "ERROR",
  message: string
}
```

**Frontend normalizes to:**
```typescript
{
  type: "ERROR",
  payload: {
    message: string,
    details?: any
  }
}
```

**Frontend behavior:**
- Adds to chat as `{sender_name: "System", text: message, type: "environment"}`
- Clears `isDMThinking` state

---

### 1.14 PONG

**Purpose:** Heartbeat response to client PING  
**Defined in:** `backend/src/api/routers/websocket_game.py:150`  
**Handled in:** `frontend/src/services/websocket.ts:532`

```typescript
{
  type: "PONG",
  timestamp: string  // ISO timestamp
}
```

**Frontend behavior:** Ignored (returns `null`), used for connection keepalive

---

## 2. WebSocket Client → Server Messages

These are all message types the **frontend sends** to the backend via WebSocket.

### 2.1 PLAYER_ACTION

**Purpose:** Player submits an action/narration  
**Defined in:** `frontend/src/types/game.ts`, `frontend/src/services/websocket.ts` (sendAction method)  
**Handled in:** `backend/src/api/routers/websocket_game.py:107`

```typescript
{
  type: "PLAYER_ACTION",
  payload: {
    player_id: string,
    request_text: string,
    character: Character,
    timestamp: number
  }
}
```

**Backend flow:**
1. Enqueued into delivery request queue
2. Game loop picks up via `player_request()`
3. Orchestrator classifies input
4. Manipulator executes events
5. Events published to EventPool → WebSocket → all clients

---

### 2.2 PING

**Purpose:** Keepalive heartbeat sent every 30 seconds  
**Defined in:** `frontend/src/services/websocket.ts` (startHeartbeat, line 326)  
**Handled in:** `backend/src/api/routers/websocket_game.py:147`

```typescript
{
  type: "PING",
  payload: {
    timestamp: number
  }
}
```

**Backend responds with:** `PONG` message

---

### 2.3 CHOOSE_PLAYER

**Purpose:** Type defined but no send method exists  
**Defined in:** `frontend/src/types/game.ts`

```typescript
{
  type: "CHOOSE_PLAYER",
  payload: {
    selected_player_id: string
  }
}
```

**⚠️ Issue:** Type exists but is never sent.

---

### 2.4 SUBSCRIBE_EVENTS

**Purpose:** Type defined but no send method exists  
**Defined in:** `frontend/src/types/game.ts`

```typescript
{
  type: "SUBSCRIBE_EVENTS",
  payload: {
    subscriber_id: string
  }
}
```

**⚠️ Issue:** Type exists but is never sent.

---

## 3. Core Game Event Types

These are the **game event types** that flow through the EventPool system. They represent specific game mechanics and actions.

**Defined in:** `core/schemas/orchestration.py` (EventTypes enum, lines 11-49)  
**Frontend mirror:** `frontend/src/types/game.ts` (line 145, EventType type union)

| Event Type | Description | Manipulator |
|---|---|---|
| `LOCATION_CHANGE` | Moving characters between locations/scenes | MovementManipulator |
| `LOCATION_MUTATION` | Changing properties of a location itself | - |
| `LOCATION_STATUS_CHANGE` | Updating the status of a location | - |
| `OBJECT_TRANSFER` | Moving objects between containers/scene/inventory | ObjectTransferManipulator |
| `ITEM_TRANSFER` | Moving items between inventories, scenes, or containers | ObjectTransferManipulator |
| `ITEM_MOVEMENT` | Moving items within a scene | SceneObjectMovementManipulator |
| `ITEM_MUTATION` | Changing properties of an item | - |
| `ITEM_INTERACTION` | Interacting with an item (opening, using) | ItemInteractionManipulator |
| `ITEM_PICKUP` | Picking up a item from the scene | ObjectTransferManipulator |
| `ITEM_DROP` | Dropping an item into the scene | ObjectTransferManipulator |
| `CONTAINER_ACCESS` | Opening/closing/accessing containers | - |
| `CONTAINER_TRANSFER` | Moving items between containers | ObjectTransferManipulator |
| `CHARACTER_STATUS_CHANGE` | Changing character status (poisoned, stunned) | - |
| `CHARACTER_DEATH` | Character death events | - |
| `CHARACTER_STATS_UPDATE` | Updating character statistics | - |
| `CHARACTER_MOVEMENT` | Character movement within a scene | MovementManipulator |
| `CHARACTER_TRANSFER` | Moving characters between locations | - |
| `CHARACTER_POSITION_UPDATE` | Updating character position in space | MovementManipulator |
| `ACTION_RESULT` | Result of an action taken in the game | - |
| `CHARACTER_MELEE_ATTACK` | Melee attack by a character | MeleeAttackManipulator |
| `CHARACTER_RANGED_ATTACK` | Ranged attack by a character | RangedAttackManipulator |
| `SYSTEM` | Messages provided by the system | - |

**Total: 22 event types**

---

## 4. REST API Response Types

### 4.1 Session Types

**Defined in:** `frontend/src/services/sessionAPI.ts`

| Interface | Fields | Purpose |
|---|---|---|
| `GameSession` | `session_id`, `session_name`, `game_mode`, `status`, `players`, `npcs`, `turn_queue` | Full session object |
| `SessionCreateRequest` | `session_name`, `max_players`, `description` | Create session input |
| `SessionStartRequest` | `wishes`, `scene_prompt`, `character_prompts`, `character_description`, `npc_prompts` | Start session with AI generation |
| `PlayerJoinRequest` | `player_name`, `character_id?` | Join session input |
| `PlayerInfo` | `player_id`, `player_name`, `is_ready`, `role` | Player data |
| `WaitingRoomInfo` | `session_id`, `session_name`, `players`, `owner_id`, `game_mode` | Waiting room state |
| `PlayerReadyRequest` | `is_ready: boolean` | Set ready status |

---

### 4.2 Character Types

**Defined in:** `frontend/src/services/characterAPI.ts`

| Interface | Fields | Purpose |
|---|---|---|
| `CharacterProfile` | `id`, `name`, `race`, `class`, `level`, `background`, `alignment?` | Saved character template |
| `CharacterProfileCreate` | `name`, `race`, `class`, `background` | Create profile input |
| `CharacterProfileUpdate` | `name?`, `race?`, `class?`, etc. | Update profile input |
| `CharacterInSession` | Full character data with stats, inventory, abilities | Character from session |
| `CharacterCreateInSessionData` | `name`, `description` | Create character in session |

---

### 4.3 Core Game Types (Frontend)

**Defined in:** `frontend/src/types/game.ts`

| Type/Interface | Key Fields | Purpose |
|---|---|---|
| `Character` | `name`, `hp`, `ac`, `ability_scores`, `inventory`, `abilities`, `conditions`, `position` | Full PC/NPC object |
| `NPCCharacter extends Character` | `+ motivation`, `alignment`, `memory`, `current_scene` | NPC with AI behavior |
| `SceneNode` | `name`, `description`, `objects`, `center_position`, `dimensions`, `scale_unit` | Game location/scene |
| `UnifiedObject` | `name`, `description`, `obj_type`, `quantity`, `is_equipped`, `damage_dice`, `position`, `tags` | Inventory item or scene object |
| `Session` | `players`, `npcs`, `turn_queue`, `current_scene`, `game_mode`, `messages` | Full session state |
| `Event` | `event_type`, `event_initiator`, `event_subject`, `event_target`, `description` | Game event |
| `Message` | `sender_name`, `text`, `type`, `timestamp` | Chat message |
| `PlayerEntity` | `{ character: Character }` | Player wrapper |
| `NPC` | `{ character: NPCCharacter }` | NPC wrapper |
| `TurnQueueEntry` | `[Character, number, number]` | Turn queue tuple |
| `AbilityScores` | `str`, `dex`, `con`, `int`, `wis`, `cha` | D&D ability scores |
| `Condition` | `name`, `rounds_remaining`, `trigger`, `periodic_effect_description` | Status effect |
| `SpellAbility` | `name`, `level`, `description`, `damage_dice`, `healing_dice`, `tags` | Spell/ability |
| `Coordinate2D` | `x: number`, `y: number` | 2D position |

---

## 5. Message Handling Flow

### 5.1 WebSocket Inbound Flow (Server → Frontend)

```
WebSocket.onmessage
  ↓
WebSocketService.handleMessage()
  ↓
parseServerMessage() -- normalizes raw server JSON into ServerMessage union type
  ↓
messageHandlers.forEach(handler) -- gameStore.connectWebSocket() callback
  ↓
switch(message.type):
  ├─ MASTER_MESSAGE
  │   → addMessage({sender: "DM", text, type: "dm"})
  │   → setIsDMThinking(false)
  │
  ├─ GAME_EVENT
  │   → addEvent(event)
  │   → addMessage({sender: "Game", text: event.description, type: "event"})
  │
  ├─ SESSION_UPDATE
  │   → if session.current_scene: setCurrentScene(session.current_scene)
  │
  ├─ SCENE_UPDATE
  │   → setCurrentScene(scene)
  │
  ├─ TURN_QUEUE_UPDATE / TURN_UPDATE
  │   → set({ turnQueue: payload.turn_queue })
  │
  ├─ ERROR
  │   → addMessage({sender: "System", text: message, type: "environment"})
  │   → setIsDMThinking(false)
  │
  ├─ ACTION_RESULT
  │   → setIsDMThinking(false)
  │   (DM response comes via MASTER_MESSAGE, not here)
  │
  ├─ CONNECTED
  │   → log connection, return null
  │
  ├─ PONG
  │   → ignored (heartbeat response)
  │
  └─ (default)
      → log unknown message type
```

---

### 5.2 WebSocket Outbound Flow (Frontend → Server)

```
gameStore.sendAction(actionText)
  ↓
WebSocketService.sendAction(actionText, character)
  ↓
send({
  type: "PLAYER_ACTION",
  payload: {
    player_id,
    request_text: actionText,
    character,
    timestamp: Date.now()
  }
})
  ↓
backend websocket_game.py event_receiver()
  ↓
session.delivery.put_request(Request(...))
  ↓
Game loop picks up via player_request()
  ↓
Orchestrator classifies input (STORY vs COMBAT mode)
  ↓
MAGG (AI GM) processes and validates
  ↓
Manipulator executes events
  ↓
Events published to EventPool
  ↓
Subscriber queues → event_stream_sender → WebSocket
  ↓
All clients receive GAME_EVENT, MASTER_MESSAGE, etc.
```

---

### 5.3 REST API Flow

```
Frontend API call (sessionAPI.ts, characterAPI.ts)
  ↓
HTTP request with auth headers/cookies
  ↓
FastAPI router (session_router.py, etc.)
  ↓
Authentication (get_current_user dependency)
  ↓
Business logic (repository, session_manager, etc.)
  ↓
JSON response
  ↓
Frontend parses into TypeScript interface
  ↓
Store updated via gameStore
```

---

## 6. Manipulator Event Mapping

Each backend manipulator handles specific event types from the EventPool:

| Manipulator | File | Event Types Handled |
|---|---|---|
| **MeleeAttackManipulator** | `core/game/manipulators/melee_attack_manipulation.py` | `CHARACTER_MELEE_ATTACK` |
| **RangedAttackManipulator** | `core/game/manipulators/ranged_attack_manipulation.py` | `CHARACTER_RANGED_ATTACK` |
| **MovementManipulator** | `core/game/manipulators/movement_manipulator.py` | `CHARACTER_MOVEMENT`, `CHARACTER_POSITION_UPDATE` |
| **ObjectTransferManipulator** | `core/game/manipulators/object_transfer_manipulator.py` | `OBJECT_TRANSFER`, `ITEM_TRANSFER`, `ITEM_PICKUP`, `ITEM_DROP`, `CONTAINER_TRANSFER` |
| **ItemInteractionManipulator** | `core/game/manipulators/item_interaction_manipulator.py` | `ITEM_INTERACTION` |
| **SceneObjectMovementManipulator** | `core/game/manipulators/scene_object_movement_manipulator.py` | `ITEM_MOVEMENT`, `OBJECT_TRANSFER` |

---

## 7. Summary Statistics

### WebSocket Message Types

| Direction | Count | Types |
|---|---|---|
| **Server → Client** | 14 | CONNECTED, MASTER_MESSAGE, SESSION_UPDATE, TURN_UPDATE, TURN_QUEUE_UPDATE, PLAYER_REQUEST, GAME_EVENT, ACTION_CONFIRMED, ACTION_REQUEST, ACTION_RESULT, SCENE_UPDATE, CHARACTER_STATUS_UPDATE, ERROR, PONG |
| **Client → Server** | 4 | PLAYER_ACTION, PING, CHOOSE_PLAYER (unused), SUBSCRIBE_EVENTS (unused) |

### Core Game Event Types: **22 total**

### Known Issues

⚠️ **PLAYER_REQUEST** - Sent by backend but not handled in frontend  
⚠️ **ACTION_REQUEST** - Handled in frontend but never sent by backend  
⚠️ **SCENE_UPDATE** - Handled in frontend but not emitted by backend WebSocket  
⚠️ **CHOOSE_PLAYER** - Type exists but never sent  
⚠️ **SUBSCRIBE_EVENTS** - Type exists but never sent  

---

## 8. Game Mode Types

| Mode | Description | Behavior |
|---|---|---|
| **STORY** | Narrative/peaceful scenes | Non-blocking, players act in narrative flow |
| **COMBAT** | Structured combat with turn order | Turn-based, blocking character actions |

**Default:** Sessions start in STORY mode  
**Dynamic switching:** RoundDeterminator can change mode at runtime based on events

---

## 9. Key Files Reference

### Frontend

| File | Purpose |
|---|---|
| `frontend/src/services/websocket.ts` | WebSocket service, message parsing and handlers |
| `frontend/src/store/gameStore.ts` | Zustand store, message/event handling |
| `frontend/src/types/game.ts` | Core TypeScript type definitions |
| `frontend/src/services/sessionAPI.ts` | Session REST API types and functions |
| `frontend/src/services/characterAPI.ts` | Character REST API types and functions |

### Backend

| File | Purpose |
|---|---|
| `backend/src/api/routers/websocket_game.py` | WebSocket router, event stream sender |
| `backend/src/delivery/game_delivery.py` | Delivery methods (master_message, session_updated, etc.) |
| `core/schemas/orchestration.py` | EventTypes enum, Event schema |
| `core/schemas/in_game.py` | GameModes enum, Character, SceneNode, etc. |
| `core/game/event_pool.py` | Pub/sub event system |
| `core/game/manipulators/*.py` | Event type handlers |

---

## 10. Usage Examples

### Example 1: Processing a PLAYER_ACTION

**Frontend sends:**
```json
{
  "type": "PLAYER_ACTION",
  "payload": {
    "player_id": "player-123",
    "request_text": "I attack the goblin with my sword",
    "character": { /* Character object */ },
    "timestamp": 1712678400000
  }
}
```

**Server responds with (multiple messages):**
```json
// 1. DM thinking (MASTER_MESSAGE)
{
  "type": "MASTER_MESSAGE",
  "text": "You swing your sword at the goblin...",
  "tag": "narration"
}

// 2. Game event (GAME_EVENT)
{
  "type": "GAME_EVENT",
  "payload": {
    "event": {
      "event_type": "CHARACTER_MELEE_ATTACK",
      "event_initiator": "Thorin",
      "event_subject": "Goblin",
      "description": "Thorin attacks the Goblin with a longsword"
    }
  }
}

// 3. Action result (MASTER_MESSAGE)
{
  "type": "MASTER_MESSAGE",
  "text": "The goblin takes 8 damage!",
  "tag": "combat"
}
```

---

### Example 2: Turn Queue Update

**Server sends:**
```json
{
  "type": "TURN_UPDATE",
  "active_player_id": "player-123",
  "active_player_name": "Thorin"
}
```

**Frontend normalizes to:**
```json
{
  "type": "TURN_QUEUE_UPDATE",
  "payload": {
    "turn_queue": [{
      "character_name": "Thorin",
      "type": "player",
      "is_active": true
    }],
    "turn_time": 1712678400000
  }
}
```

---

### Example 3: Scene Update via SESSION_UPDATE

**Server sends:**
```json
{
  "type": "SESSION_UPDATE",
  "payload": {
    "session": {
      "current_scene": {
        "name": "The Rusty Dragon Tavern",
        "description": "A warm, bustling tavern...",
        "objects": [],
        "center_position": { "x": 0, "y": 0 }
      },
      // ... other session data
    }
  }
}
```

**Frontend behavior:**
```typescript
if (session.current_scene) {
  set({ currentScene: session.current_scene });
}
```

---

This reference provides a complete picture of all communication between the frontend and server in the MAGGxDND system.
