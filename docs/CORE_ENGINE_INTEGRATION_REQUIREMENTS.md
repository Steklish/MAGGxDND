# Core Game Engine Integration Requirements

## Problem Statement

The MAGGxDND project has two separate player management systems:
1. **Database Layer** - SQLAlchemy models in `backend/src/models/session.py`
2. **Game Engine Layer** - Core engine sessions in `core/game/engine.py`

Currently, these two systems are not properly synchronized, causing issues where:
- Players joining via `/api/v1/sessions/{session_id}/players` are added to the database but NOT to the game engine
- The `/api/v1/sessions/{session_id}/game_info` endpoint only returns players from the game engine, missing database players
- When a session is started, characters are generated but not properly linked to the players who joined

## Required Changes

### 1. Session Start Endpoint (`backend/src/api/routers/session_router.py`)

**Location:** `start_session()` function around line 539

**Required Changes:**
- When starting a session, sync database participants with game engine players
- For each participant in the database without a character, create a default character
- Link the generated character to the participant's identity (player_name)

**Implementation:**
```python
# After initializing game_session, sync DB participants
db_participants = repository.get_session_participants(session_id)
for participant in db_participants:
    # Check if this player already exists in game engine
    existing_player = next((p for p in game_session.players 
                           if hasattr(p, 'name') and p.name == participant.player_name), None)
    
    if not existing_player:
        # Generate default character for this player
        character = generate_default_character(participant.player_name)
        # Add to game engine session
        game_session.players.append(create_player_from_character(character))
```

### 2. Game Info Endpoint (`backend/src/api/routers/session_router.py`)

**Location:** `get_session_game_info()` function around line 1054

**Required Changes:**
- Merge data from both database participants AND game engine players
- Return comprehensive player list including:
  - Players from game engine with full character data
  - Players from database with basic info (for waiting room)

**Implementation:**
```python
# Get DB participants
db_participants = repository.get_session_participants(session_id)

# Build players from game engine
players_data = []
for player in game_session.players:
    if hasattr(player, 'character'):
        char = player.character
        players_data.append(build_player_response(char))

# Add DB participants without characters (waiting room players)
for participant in db_participants:
    if not any(p['name'] == participant.player_name for p in players_data):
        players_data.append({
            "name": participant.player_name,
            "race": "Human",  # Default
            "char_class": "Adventurer",  # Default
            "level": 1,
            # ... other defaults
        })
```

### 3. Player Join Endpoint (`backend/src/api/routers/session_router.py`)

**Location:** `join_session()` function around line 852

**Required Changes:**
- After adding player to database, also add to active game session if it exists
- This ensures real-time sync for waiting room

**Implementation:**
```python
# After adding to DB
game_session = active_game_sessions.get(session_id)
if game_session:
    # Add player to game engine's waiting room or player list
    game_session.add_participant(player_id, player_name)
```

### 4. Core Engine Session Class (`core/game/engine.py`)

**Required Changes:**
- Add method to add participants/players dynamically after session creation
- Add method to sync external player list with internal state

**New Methods:**
```python
def add_player(self, player_data: dict) -> Player:
    """Add a player to the session dynamically."""
    pass

def sync_players(self, player_list: list) -> None:
    """Synchronize internal player list with external source."""
    pass

def get_participants(self) -> list:
    """Get all participants (players + NPCs)."""
    pass
```

## Testing Requirements

1. **Test Case 1:** Create session → Start game without joining → Should generate owner character
2. **Test Case 2:** Create session → Join as player → Start game → Both players should have characters
3. **Test Case 3:** Create session → Join as player → Check game_info → Should show all players
4. **Test Case 4:** Start game → Join after start → Player should be added to active game

## Files to Modify

1. `backend/src/api/routers/session_router.py` - Main integration logic
2. `backend/src/game/session_manager.py` - Session lifecycle management
3. `backend/src/game/session_factory.py` - Session creation with player sync
4. `core/game/engine.py` - Core engine player management
5. `core/entity/player.py` - Player entity updates

## Dependencies

- SQLAlchemy session management
- FastAPI dependency injection
- Core game engine architecture
- Player/Character schemas

## Priority

**HIGH** - This is blocking the core gameplay functionality

## Notes

- Do NOT modify core engine architecture without understanding the event system
- Maintain backward compatibility with existing save/load functionality
- Ensure WebSocket integration points are preserved for future real-time features
