# Player Input Processing Pipeline Analysis

## Overview

This document explains the complete player input processing pipeline, the game loop with round determinator, and the differences between terminal delivery and async API delivery.

---

## 1. Player Input Processing Pipeline

### Flow: API Endpoint → Game Session

```
Frontend Request
    ↓
POST /api/v1/sessions/{session_id}/action
    ↓
session_router.py:player_action()
    ↓
game_delivery.py:process_player_action()
    ↓
orchestrator.request() - Classifies interaction (CHARACTER_ACTION vs META_COMMENT)
    ↓
orchestrator.character_action_story() or character_action_combat()
    ↓
Returns OrchestrationVerdict (ALLOWED, ILLEGAL, or CLARIFICATION_NEEDED)
    ↓
manipulator._external_action_as_an_entity() - Creates events from action
    ↓
manipulator.execute_events() - Executes events, applies side effects
    ↓
game_master.handle_events() - AI generates narrative
    ↓
Response sent to frontend
```

### Key Files:
- **Entry Point**: `backend/src/api/routers/session_router.py:player_action()` (line 2097)
- **Processing**: `backend/src/delivery/game_delivery.py:process_player_action()` (line 307)
- **Orchestration**: `core/entity/orchestrator.py`
- **Manipulation**: `core/game/manipulator.py`
- **AI Narrative**: `core/magg/magg.py`

---

## 2. Game Loop with Round Determinator

### The Game Loop (`core/game/engine.py:game_loop()`)

The game loop is a **turn-based system** that processes characters in initiative order:

```python
async def game_loop(self):
    self._initialize_turn_queue()
    while True:
        char = self._get_next_character_turn()
        
        if isinstance(char, NPC):
            char.run()  # NPC acts autonomously
            
        elif isinstance(char, Player):
            if self.game_mode == GameModes.COMBAT:
                char.run()  # Block for player input
            if self.game_mode == GameModes.STORY:
                # Story mode: process when NPCs are done
                are_npcs_done = all(npc.event_queue.empty for npc in self.turn_queue)
                if are_npcs_done:
                    char_acting = self.delivery.choose_player(self)
                    char_acting.run_story()
                    
        elif isinstance(char, RoundDeterminator):
            char.run()  # Process round-based events, check mode changes
```

### Turn Queue System

**Structure**: `List[Tuple[Player | NPC | RoundDeterminator, float, float]]`
- Element 0: Character object
- Element 1: Time when character was added
- Element 2: Next turn time

**Initialization**:
```python
def _initialize_turn_queue(self):
    self.turn_queue = []
    self.turn_time = 0.0
    self._add_all_characters_to_turn_queue()  # Add all alive characters
    self._add_round_determinator_to_turn_queue()  # Always added last
```

**Turn Calculation**:
```python
next_move_time = self.turn_time + (time_added / character.initiative_bonus)
```
Higher initiative = lower next_turn_time = acts sooner.

**Round Determinator**:
- Special object with `ROUND_DURATION` (default: 10)
- Processes **after all characters** have acted
- Checks for **game mode changes** (STORY ↔ COMBAT)
- Processes **periodic conditions** (damage over time, buffs, etc.)
- Has **lowest priority** in turn queue

### Story Mode vs Combat Mode

| Aspect | Story Mode | Combat Mode |
|--------|-----------|-------------|
| **Who can act** | Anyone (async requests) | Only current turn character |
| **Turn enforcement** | Loose (queue exists but not enforced) | Strict (only current player) |
| **Input handling** | Any player can submit action anytime | Only active player's turn |
| **NPC behavior** | Autonomous, act when their turn comes | Autonomous, act when their turn comes |
| **Round Determinator** | Checks for combat trigger | Checks for combat end |

---

## 3. Terminal Delivery vs Async API Delivery

### Terminal Delivery (Simple, Blocking)

**Location**: Used in `main.py` and terminal-based gameplay

**How it works**:
```python
def run_story(self):
    request = self.session.delivery.player_request(self.character)
    # BLOCKS until user types input in terminal
    # Processes input immediately
    # Returns events
```

**Characteristics**:
- **Blocking**: Waits for user input before continuing
- **Synchronous**: One action at a time
- **Single player**: Only one player can act
- **Direct control**: Game loop waits for input
- **Simple flow**: Input → Process → Output → Next turn

### Async API Delivery (Complex, Non-blocking)

**Location**: `backend/src/delivery/game_delivery.py`

**How it works**:
```python
async def process_player_action(self, character_name, action_text, player_id=None):
    # 1. Find player in session
    # 2. Put request in delivery queue
    # 3. Process through orchestrator
    # 4. Execute through manipulator
    # 5. Get AI narrative from MAGG
    # 6. Broadcast to all players via WebSocket
    # 7. Save to database
    # 8. Return response
```

**Characteristics**:
- **Non-blocking**: Returns immediately with response
- **Asynchronous**: Multiple players can submit actions
- **Multi-player**: Supports multiple connected players
- **WebSocket-based**: Real-time updates to all clients
- **Complex flow**: Request → Queue → Process → Broadcast → Save → Response

### Key Differences

| Aspect | Terminal Delivery | API Delivery |
|--------|------------------|--------------|
| **Input method** | Terminal stdin (blocking) | HTTP request (non-blocking) |
| **Player selection** | `delivery.choose_player()` blocks | Any player can send request |
| **Turn enforcement** | Strict in both modes | **NOT ENFORCED** in story mode |
| **Concurrency** | Single player only | Multiple players simultaneously |
| **State management** | In-memory only | Database persistence |
| **Response delivery** | Console output | WebSocket broadcast |

---

## 4. Current Issues

### Issue 1: ✅ FIXED - Repository Not Defined
**Error**: `name 'repository' is not defined`
**Location**: `backend/src/api/routers/session_router.py:2174`
**Fix**: Added `repository = get_session_repository(db)` before use

### Issue 2: ✅ FIXED - Session Reconnection Not Implemented
**Problem**: When a player reconnects to an existing session, the system recreates it instead of loading from database.

**Solution Implemented**:
- Modified `start_session()` endpoint to check database for existing session state
- If session exists in DB with saved state, restore it using `game_session.restore_session_state()`
- Skip fresh scene/character generation when restoration succeeds
- Return `SessionStartResponse` with restoration status
- Save restored state back to database to ensure consistency

**New Flow**:
```
POST /sessions/{id}/start
    ↓
Check if session in session_manager (in-memory)
    ↓
If not found → Check database for session data
    ↓  
If session_data exists → Create session + restore state → Return early with success
    ↓
If no session_data → Generate fresh session (old behavior)
```

### Issue 3: ⚠️ Story Mode Turn Queue Not Enforced
**Problem**: In story mode, ANY player can submit actions at ANY time, ignoring the turn queue.

**Expected Behavior** (from your requirements):
- **Story Mode**: Players are added to a request queue, processed in order
- **Combat Mode**: Only current turn player can act

**Current Behavior**:
- **Story Mode**: No queue, immediate processing
- **Combat Mode**: Only current player (correct)

---

## 5. Recommended Fixes

### Fix 1: Implement Session Reconnection

**Location**: `backend/src/api/routers/session_router.py:start_session()`

**Logic**:
```python
game_session = session_manager.get_session(session_id)

if not game_session:
    # Check if session exists in database with state
    db_session = repository.get_session_by_uuid(session_id)
    
    if db_session and db_session.session_data:
        # Session exists in DB - restore it
        config = SessionConfig(...)
        game_session = session_factory.create_session(config, session_id)
        
        # Restore state from database
        restored = game_session.restore_session_state(db_session.session_data)
        if restored:
            logger.info(f"Session restored from database: {len(game_session.players)} players")
        else:
            logger.warning("Failed to restore, generating fresh")
            # Generate fresh session...
    else:
        # No saved state - create fresh session
        game_session = session_factory.create_session(...)
        # Generate scene, characters, etc.
```

### Fix 2: Implement Story Mode Request Queue

**Location**: `backend/src/delivery/game_delivery.py:process_player_action()`

**Logic**:
```python
# In Session class
self.action_request_queue: List[Tuple[str, str, str]] = []  # (player_id, character_name, action)

# In process_player_action()
if self.session.game_mode == GameModes.STORY:
    # Add to request queue instead of immediate processing
    self.session.action_request_queue.append((player_id, character_name, action_text))
    return {
        "success": True,
        "dm_response": "Action queued. Waiting for your turn.",
        "events": [],
        "queued": True
    }

# In game_loop() for story mode
if self.game_mode == GameModes.STORY:
    # Process queued requests in turn order
    for player_id, char_name, action in self.action_request_queue:
        if current_turn_character.name == char_name:
            process_action(char_name, action)
            self.action_request_queue.remove((player_id, char_name, action))
            break
```

---

## 6. Architecture Recommendations

### 6.1. Turn-Based Action Request System

Create a new component: `ActionRequestQueue`

```python
class ActionRequestQueue:
    """Manages player action requests in story mode"""
    
    def __init__(self):
        self._queue: List[ActionRequest] = []
        self._lock = asyncio.Lock()
    
    async def add_request(self, player_id: str, character_name: str, action: str):
        async with self._lock:
            self._queue.append(ActionRequest(player_id, character_name, action, time.time()))
    
    async def get_next_for_character(self, character_name: str) -> Optional[ActionRequest]:
        """Get next queued request for specific character"""
        async with self._lock:
            for req in self._queue:
                if req.character_name == character_name:
                    return self._queue.pop(self._queue.index(req))
            return None
```

### 6.2. Session Lifecycle Management

Implement proper session lifecycle:
1. **Creation**: First time `/sessions/{id}/start` is called
2. **Persistence**: Auto-save after every action (✅ already implemented)
3. **Restoration**: Load from DB when server restarts
4. **Cleanup**: Archive or delete when session ends

### 6.3. WebSocket Event Streaming

Instead of polling, stream events to clients:
```python
@router.websocket("/{session_id}/events")
async def event_stream(websocket: WebSocket, session_id: str):
    await websocket.accept()
    session = session_manager.get_session(session_id)
    
    while True:
        events = await session.delivery.get_next_message()
        if events:
            await websocket.send_json(events)
```

---

## 7. Summary

### What Works:
✅ Event processing pipeline (Orchestrator → Manipulator → Events → MAGG)
✅ Turn queue initialization and sorting
✅ Round determinator mode changes
✅ Database persistence (after repository fix)
✅ WebSocket broadcasting
✅ Session reconnection from database (NEW)

### What Needs Work:
❌ Story mode action request queue (no turn enforcement)
❌ Game loop integration with async API (terminal delivery blocks, API doesn't)
❌ Proper turn-based input handling in story mode

### Completed Fixes:
✅ Fix repository undefined error
✅ Implement session reconnection from database
✅ Document player input processing pipeline
✅ Document game loop and round determinator
✅ Document terminal vs API delivery differences

### Next Steps:
1. Add action request queue for story mode
2. Update game loop to process queued requests
3. Add WebSocket event streaming for real-time updates
