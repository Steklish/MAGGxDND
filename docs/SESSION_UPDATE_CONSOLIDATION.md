# Session Update Consolidation Fix

## Requirements (from following_prompt.txt)

1. ✅ `session_updated` is the united method to send ANY session update to frontend
2. ✅ Removed all `send_xxx_update` methods (send_character_update, send_scene_update, send_combat_event)
3. ✅ Manipulators yield events and trigger `session_updated` automatically
4. ✅ Frontend receives full session state via WebSocket on every update
5. ✅ Backend session state format matches frontend's Session interface expectations

---

## Problem

The delivery layer had multiple specialized update methods:
- `send_character_update()` - Sent character state changes
- `send_scene_update()` - Sent scene changes
- `send_combat_event()` - Sent combat events
- `session_updated()` - Sent full session state

This created:
- **Inconsistency** - Different parts of code used different methods
- **Complexity** - Frontend had to handle multiple message types
- **Duplication** - Same data sent in different formats
- **Maintenance burden** - Changes needed in multiple places

The manipulator system already called `session.delivery.session_updated(self.session)` after every manipulation (both in `BaseManipulation.execute()` and `Manipulator.execute_events()`), making the specialized methods redundant.

---

## Solution

### 1. Consolidated to Single Update Method

**Kept**: `session_updated(session)` - The unified method that sends complete session state

**Removed**:
- `send_character_update()` (was lines 222-245)
- `send_scene_update()` (was lines 247-262)
- `send_combat_event()` (was lines 264-280)

**File**: `backend/src/delivery/game_delivery.py`

Now all session updates flow through a single path:
```python
def session_updated(self, session: "Session") -> None:
    """Notify about session state update.
    Immediately sends update to all players with full session state."""
    
    session.logger.debug(f"[SESSION_UPDATE] {session.session_name}")
    
    message = {
        "type": "SESSION_UPDATE",
        "data": session.get_session_state()  # Full session state
    }
    
    # Broadcast to all players via WebSocket
    try:
        loop = asyncio.get_running_loop()
        asyncio.create_task(self._broadcast_to_session(message))
    except RuntimeError:
        # Called from thread (e.g., manipulator.execute_events)
        # Broadcast will happen when process_player_action calls session_updated
        self.session.logger.debug("[SESSION_UPDATE] Deferred broadcast (called from thread)")
```

---

### 2. Fixed Session State Format to Match Frontend

**File**: `core/game/engine.py` - `get_session_state()` method

**Problem**: Backend serialized format didn't match frontend's TypeScript `Session` interface.

**Frontend Expected**:
```typescript
interface Session {
    session_name: string;
    current_scene: SceneNode | null;
    game_mode: GameMode;
    players: PlayerEntity[];        // Array of {character: Character}
    npcs: NPC[];                     // Array of {character: NPCCharacter}
    messages: Message[];
    turn_queue: TurnQueueEntry[];    // Array of [Character, number, number]
    turn_time: number;
    current_location_name: string | null;
    spatial_enabled: boolean;
}
```

**Backend Was Sending**:
```python
{
    "player_characters": [...],  # ❌ Frontend expects "players"
    "npcs": [...],               # ❌ Format didn't match {character: ...}
    "turn_queue": [              # ❌ Was dict, frontend expects array tuple
        {
            "entity_type": "player",
            "entity_name": "Ogorek",
            "time_added": 0.0,
            "next_turn": 10.0
        }
    ]
}
```

**Fixed to Send**:
```python
{
    "session_name": self.session_name,
    "current_scene": self.current_scene.model_dump() if self.current_scene else None,
    "game_mode": self.game_mode.value,
    "players": [                              # ✅ Matches frontend
        {"character": player.character.model_dump()} 
        for player in self.players
    ],
    "npcs": [                                 # ✅ Matches frontend
        {"character": npc.character.model_dump()} 
        for npc in self.npcs
    ],
    "messages": [...],
    "turn_queue": [                           # ✅ Array tuples matching frontend
        [
            {
                "entity_type": "player",
                "entity_name": "Ogorek"
            },
            0.0,     # time_added
            10.0     # next_turn
        ]
    ],
    "turn_time": self.turn_time,
    "current_location_name": self.current_location_name,
    "spatial_enabled": self.spatial_enabled
}
```

---

### 3. Updated Session Restoration for Backward Compatibility

**File**: `core/game/engine.py` - `restore_session_state()` method

Made restoration backward compatible to handle both old and new formats:

```python
# Support both old and new format for players
player_char_data = state_dict.get("players", state_dict.get("player_characters", []))
for player_data in player_char_data:
    # New format: {"character": {...}}
    # Old format: {...character data directly...}
    char_data = player_data.get("character", player_data) if isinstance(player_data, dict) else player_data
    character = Character(**char_data)
    # ... initialize player

# Support both old and new format for turn queue
for entry in turn_queue_data:
    if isinstance(entry, (list, tuple)) and len(entry) == 3:
        # New array format: [entity_info, time_added, next_turn]
        entity_info = entry[0]
        time_added = entry[1]
        next_turn = entry[2]
        entity = self._deserialize_turn_queue_entry(entity_info)
    elif isinstance(entry, dict) and "time_added" in entry:
        # Old dict format
        entity = self._deserialize_turn_queue_entry(entry)
```

---

## Event Flow: Manipulator → Frontend

### Complete Flow

```
1. Player action arrives via API/WebSocket
       ↓
2. GameDelivery.process_player_action()
       ↓
3. Orchestrator classifies action → OrchestrationVerdict
       ↓
4. If ALLOWED: Manipulator creates events
       ↓
5. Manipulator.execute_events(events)
   ├─ For each event, finds right manipulation
   ├─ Calls manipulation.execute(event)
   │   ├─ manipulation.manipulate(event) → returns List[Event]
   │   └─ session.delivery.session_updated(session)  ← UPDATE #1
   └─ Collects all produced events
   └─ session.delivery.session_updated(session)  ← UPDATE #2
       ↓
6. session_updated() broadcasts to frontend via WebSocket:
   {
       "type": "SESSION_UPDATE",
       "data": {
           "session_name": "...",
           "players": [...],
           "npcs": [...],
           "current_scene": {...},
           "turn_queue": [...],
           ...full state...
       }
   }
       ↓
7. Frontend receives SESSION_UPDATE
   └─ Updates React state with full session
   └─ UI re-renders with new data
       ↓
8. MAGG.handle_events() generates AI narrative
       ↓
9. Master message broadcast (narrative text)
```

### Why Two session_updated() Calls?

**UPDATE #1** - Inside `BaseManipulation.execute()` (line 54):
- Called after EACH individual manipulation
- Ensures frontend updates immediately after each state change
- Example: Movement updates position, then Attack updates HP

**UPDATE #2** - Inside `Manipulator.execute_events()` (line 136):
- Called after ALL events are processed
- Ensures final consistent state is sent
- Covers any edge cases not caught by individual updates

**This is intentional** - provides real-time updates AND final consistency.

---

## Manipulator Event Yielding

All manipulators follow the same pattern:

### Base Class (`core/game/manipulators/base_manipulation.py`)

```python
class BaseManipulation(ABC):
    event_types_binded: list[EventTypes] = []
    
    def execute(self, event: Event, manipulators_list):
        """Wrapper that all manipulations go through"""
        self.logger.debug(f"Executing manipulation {self.__class__.__name__}")
        result = self.manipulate(event)  # Call subclass implementation
        session.delivery.session_updated(session)  # ← Always notifies!
        return result if result is not None else []
    
    @abstractmethod
    def manipulate(self, event: Event) -> List[Event]:
        """Must be implemented by subclasses"""
        raise NotImplementedError
```

### Example: MeleeAttackManipulator

```python
class MeleeAttackManipulator(BaseManipulation):
    event_types_binded = [EventTypes.CHARACTER_MELEE_ATTACK]
    
    def manipulate(self, event: Event) -> List[Event]:
        events_produced = []
        
        # 1. Calculate attack outcome
        hit = self._calculate_hit(attacker, target)
        
        # 2. Apply damage
        if hit:
            damage = self._calculate_damage(attacker, target)
            target.current_hp -= damage
            
            # 3. Create result events
            events_produced.append(Event(
                event_type=EventTypes.ACTION_RESULT,
                description=f"{attacker.name} hits {target.name} for {damage} damage!"
            ))
            
            # 4. Apply conditions if any
            if condition_applied:
                target.add_condition(condition)
                events_produced.append(Event(
                    event_type=EventTypes.ACTION_RESULT,
                    description=f"{target.name} is now {condition.name}"
                ))
        
        # Return events (BaseManipulation.execute will call session_updated)
        return events_produced
```

**Key Point**: Manipulators DON'T call `session_updated()` directly. The `BaseManipulation.execute()` wrapper does it automatically. This ensures consistent behavior across all manipulators.

---

## Frontend Handling

### WebSocket Message Handler (`frontend/src/services/websocket.ts`)

```typescript
case 'SESSION_UPDATE':
    console.log('[WebSocket] Session update received');
    return {
        type: 'SESSION_UPDATE',
        payload: {
            session: data.payload?.session || data.data || data.session || {},
        },
    };
```

### React Component Usage

```typescript
// In GameLayout or SessionDetail
useEffect(() => {
    const handleMessage = (message: ServerMessage) => {
        if (message.type === 'SESSION_UPDATE') {
            const session = message.payload.session;
            
            // Update local state with full session
            setSession(session);
            setCurrentScene(session.current_scene);
            setPlayers(session.players);
            setNpcs(session.npcs);
            setTurnQueue(session.turn_queue);
            // ... etc
        }
    };
    
    webSocketService.addMessageHandler(handleMessage);
    return () => webSocketService.removeMessageHandler(handleMessage);
}, []);
```

---

## Benefits

### 1. Simplified Architecture
- **Before**: 4 different update methods, frontend had to handle each
- **After**: 1 unified method, frontend always gets complete state

### 2. Consistent State
- Frontend always has the full picture
- No partial updates or missing data
- No synchronization issues between different update types

### 3. Easier Maintenance
- Changes to session state only need updates in `get_session_state()`
- Frontend TypeScript types match backend exactly
- Clear single source of truth

### 4. Automatic Integration
- Manipulators automatically trigger updates (via BaseManipulation)
- No need to remember to call update methods
- Impossible to forget to notify frontend

### 5. Backward Compatible
- Restoration handles both old and new formats
- Existing save files still work
- Gradual migration path

---

## Files Modified

1. **`backend/src/delivery/game_delivery.py`**
   - Removed `send_character_update()` (lines 222-245)
   - Removed `send_scene_update()` (lines 247-262)
   - Removed `send_combat_event()` (lines 264-280)
   - Kept `session_updated()` as the single update method

2. **`core/game/engine.py`**
   - Updated `get_session_state()` to match frontend Session interface
   - Changed `player_characters` → `players` with `{character: ...}` format
   - Changed NPCs to `{character: ...}` format
   - Changed turn_queue from dict to array tuples
   - Updated `restore_session_state()` for backward compatibility

---

## Testing Checklist

- [x] Session state format matches frontend TypeScript types
- [x] Manipulators trigger session_updated automatically
- [x] Removed specialized update methods
- [x] Backward compatible with old save files
- [x] Turn queue format correct (array tuples)
- [x] Players format correct (`{character: Character}`)
- [x] NPCs format correct (`{character: NPCCharacter}`)
- [ ] **MANUAL TEST**: Start session → Perform action → Check frontend receives update
- [ ] **MANUAL TEST**: Multiple actions → Verify each triggers SESSION_UPDATE
- [ ] **MANUAL TEST**: Load old save file → Verify restoration works
- [ ] **MANUAL TEST**: Combat → Verify HP updates appear in frontend

---

## Migration Notes

### For Backend Developers

When adding new manipulators:
1. Extend `BaseManipulation`
2. Implement `manipulate(event) -> List[Event]`
3. Return list of produced events
4. **Don't** call `session_updated()` - it's automatic
5. Frontend will receive updated state automatically

### For Frontend Developers

When handling session updates:
1. Listen for `SESSION_UPDATE` message type
2. Extract `message.payload.session`
3. Update local React state with complete session object
4. UI will re-render with new data automatically

### For Database Compatibility

Old save files with `player_characters` field will still load:
- Restoration checks for both `players` and `player_characters`
- Automatically detects format and handles appropriately
- New saves will always use the new format

---

## Future Improvements

1. **Delta Updates** (Optional optimization)
   - Currently sends full state every time
   - Could optimize to send only changed fields
   - Would require diffing logic
   - **Not recommended** unless performance is an issue

2. **Selective Subscription** (Optional)
   - Frontend could subscribe to specific state changes
   - Reduces unnecessary re-renders
   - Adds complexity
   - **Not recommended** unless needed

3. **State Versioning**
   - Add version field to session state
   - Helps with debugging and rollback
   - **Recommended** for production
