# WebSocket API Requirements for MAGGxDND UI

## Overview

This document specifies the WebSocket API requirements for the UI to communicate with the game server. The UI expects real-time bidirectional communication for game state updates, player actions, and GM narration.

---

## Connection

### WebSocket Endpoint
```
ws://localhost:8000/ws/{session_id}/{player_id}
```

**Parameters:**
- `session_id` (string): Unique game session identifier
- `player_id` (string): Player character name/ID

### Connection Flow
1. UI connects to WebSocket endpoint
2. Server accepts connection and sends initial session state
3. UI subscribes to event stream
4. Real-time communication begins

---

## Client → Server Messages

### 1. Player Action
**When:** Player submits an action via the input form

```typescript
{
    type: "PLAYER_ACTION",
    payload: {
        player_id: string,
        request_text: string,      // User's action description
        character: Character,      // Full character object
        timestamp: number          // Unix timestamp
    }
}
```

**UI Trigger:** Click "Submit" button in ActionPanel

---

### 2. Skip Turn
**When:** Player clicks "Skip Turn" button

```typescript
{
    type: "SKIP_TURN",
    payload: {
        player_id: string,
        timestamp: number
    }
}
```

---

### 3. Subscribe to Events
**When:** After connection established

```typescript
{
    type: "SUBSCRIBE_EVENTS",
    payload: {
        subscriber_id: string  // Usually player_id
    }
}
```

---

### 4. Choose Player (GM Only)
**When:** GM selects which character acts next

```typescript
{
    type: "CHOOSE_PLAYER",
    payload: {
        selected_player_id: string
    }
}
```

---

## Server → Client Messages

### 1. Session Update
**When:** Initial connection or major state change

```typescript
{
    type: "SESSION_UPDATE",
    payload: {
        session: {
            session_name: string,
            current_scene: SceneNode,
            game_mode: "STORY" | "COMBAT",
            players: PlayerEntity[],
            npcs: NPC[],
            messages: Message[],
            turn_queue: TurnQueueEntry[],
            turn_time: number,
            current_location_name: string,
            spatial_enabled: boolean
        }
    }
}
```

---

### 2. Master Message (GM Narration)
**When:** GM sends narration/clarification

```typescript
{
    type: "MASTER_MESSAGE",
    payload: {
        text: string,
        tag?: "Clarification" | "Illegal" | "Meta" | string
    }
}
```

**UI Behavior:**
- Displays in dialogue messages area with **orange** border
- `tag="Clarification"`: Shows in clarification box above input form
- `tag="Illegal"`: Indicates invalid action

---

### 3. Game Event
**When:** Any game event occurs (movement, attacks, etc.)

```typescript
{
    type: "GAME_EVENT",
    payload: {
        event: {
            event_type: EventType,
            event_initiator: string | null,
            event_subject: string | null,
            event_target: string | null,
            description: string
        }
    }
}
```

**Event Types:**
- `CHARACTER_MOVEMENT` - Character moved
- `CHARACTER_STATUS_CHANGE` - HP/conditions changed
- `CHARACTER_MELEE_ATTACK` - Melee attack made
- `CHARACTER_RANGED_ATTACK` - Ranged attack made
- `CHARACTER_DEATH` - Character died
- `ITEM_PICKUP` - Item picked up
- `ITEM_DROP` - Item dropped
- `ACTION_RESULT` - Action resolved
- `SYSTEM` - System message

---

### 4. Action Request
**When:** It's a player's turn to act

```typescript
{
    type: "ACTION_REQUEST",
    payload: {
        character: Character  // Character whose turn it is
    }
}
```

**UI Behavior:**
- Activates input form for this character
- Highlights character in Turn Queue
- Shows "Your turn!" indicator

---

### 5. Turn Queue Update
**When:** Turn order changes

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

**UI Behavior:**
- Updates header portrait order
- Shows current turn character with purple highlight

---

### 6. Scene Update
**When:** Scene changes or objects are modified

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

---

### 7. Character Status Update
**When:** Character HP, conditions, or position changes

```typescript
{
    type: "CHARACTER_STATUS_UPDATE",
    payload: {
        character_name: string,
        current_hp: number,
        max_hp: number,
        temp_hp: number,
        active_conditions: Condition[],
        position: { x: number, y: number }
    }
}
```

**UI Behavior:**
- Updates CharacterPanel HP bar
- Updates condition tags
- Updates position on scene grid

---

### 8. Error
**When:** Something goes wrong

```typescript
{
    type: "ERROR",
    payload: {
        message: string,
        details?: any,
        code?: string
    }
}
```

**UI Behavior:**
- Shows error notification
- May disconnect if critical

---

## Data Models

### Character
```typescript
interface Character {
    // Identity
    name: string;
    race: string;
    char_class: string;
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
    inventory: UnifiedObject[];
    active_conditions_list: Condition[];
    resources: Record<string, number>;
    position: { x: number, y: number };
    abilities: SpellAbility[];

    // Computed
    active_conditions: string;
    proficiency_bonus: number;
    is_alive: boolean;
    initiative_bonus: number;
    short_summary: string;
}
```

### SceneNode
```typescript
interface SceneNode {
    name: string;
    description: string;
    objects: UnifiedObject[];
    center_position: { x: number, y: number };
    dimensions: { x: number, y: number };
    scale_unit: string;
    // gm_secret: string  // NEVER send to client!
}
```

### UnifiedObject
```typescript
interface UnifiedObject {
    name: string;
    obj_type: "Prop" | "Container" | "Interactable";
    quantity: number;
    is_equipped: boolean;
    position?: { x: number, y: number };
    is_locked?: boolean;
    is_hidden?: boolean;
    tags?: string[];
    short_summary: string;
}
```

### Condition
```typescript
interface Condition {
    name: string;
    rounds_remaining: number | null;
    trigger: "End of Round" | "Passive" | "On Action";
    periodic_effect_description: string;
    short_summary: string;
}
```

### SpellAbility
```typescript
interface SpellAbility {
    name: string;
    level: number;
    description: string;
    duration: string;
    damage_dice?: string;
    damage_type?: string;
    healing_dice?: string;
    tags: string[];
    short_summary: string;
}
```

---

## Message Type Classification (for Dialogue Colors)

The UI classifies messages by sender type for color-coded dialogue:

| Type | Color | Source |
|------|-------|--------|
| `dm` | Orange | Messages from DM/Game Master |
| `player` | Purple | Messages from player characters |
| `ally_npc` | Green | NPCs with Good alignment |
| `hostile_npc` | Red | NPCs with Evil/Chaotic alignment |
| `neutral_npc` | Yellow | NPCs with Neutral alignment |
| `environment` | White | System/environment messages |

**Server should include `type` field in Message objects, or UI will auto-classify based on sender name and session data.**

---

## Expected Flow

### 1. Connection
```
UI → Server: Connect to ws://localhost:8000/ws/session1/Player1
Server → UI: SESSION_UPDATE (initial state)
UI → Server: SUBSCRIBE_EVENTS
```

### 2. Player Turn
```
Server → UI: ACTION_REQUEST (character: Player1)
UI: Activates input form
User: Types "Attack the goblin"
UI → Server: PLAYER_ACTION (request_text: "Attack the goblin")
Server → UI: MASTER_MESSAGE (text: "You swing your sword...")
Server → UI: GAME_EVENT (event_type: CHARACTER_MELEE_ATTACK)
Server → UI: CHARACTER_STATUS_UPDATE (goblin HP changed)
Server → UI: TURN_QUEUE_UPDATE (next turn)
```

### 3. GM Narration
```
Server → UI: MASTER_MESSAGE (text: "The cave echoes with strange sounds", tag: null)
UI: Displays orange-bordered message in dialogue area
```

### 4. Illegal Action
```
UI → Server: PLAYER_ACTION (request_text: "Fly to the moon")
Server → UI: MASTER_MESSAGE (text: "You can't fly!", tag: "Illegal")
UI: Shows clarification box with error message
```

---

## Implementation Notes

### Threading
- Server MUST be thread-safe (use asyncio for WebSocket handlers)
- Delivery layer uses threading.Lock for queue operations
- EventPool uses threading.RLock for recursive locking

### Performance
- UI expects low-latency responses (<500ms for action acknowledgment)
- Batch multiple events if they occur in same game tick
- Compress large session updates if possible

### Security
- Validate all incoming message payloads
- Never send `gm_secret` fields to client
- Implement rate limiting (suggested: 10 messages/second per player)
- Consider JWT authentication for production

### Error Handling
- Always send ERROR message before closing connection
- Include error code for programmatic handling
- UI will attempt reconnection on unexpected disconnect

---

## Testing Checklist

- [ ] WebSocket connection established successfully
- [ ] Initial SESSION_UPDATE received with full game state
- [ ] PLAYER_ACTION sent and acknowledged
- [ ] MASTER_MESSAGE displayed with correct styling
- [ ] GAME_EVENT received and visualized
- [ ] TURN_QUEUE_UPDATE updates header portraits
- [ ] CHARACTER_STATUS_UPDATE updates HP bars and conditions
- [ ] SCENE_UPDATE reflects object/position changes
- [ ] ERROR message displayed appropriately
- [ ] Reconnection after disconnect works

---

## Contact

For questions about UI requirements, refer to:
- `ui_project_overview.md` - General UI architecture
- `server_requirements.md` - Detailed server implementation guide
- `dev_diary.md` - Development notes and decisions
