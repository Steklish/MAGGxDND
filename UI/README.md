# MAGGxDND UI

React-based web interface for the MAGGxDND AI-powered D&D game engine.

## Tech Stack

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Zustand** - State management
- **Vite** - Build tool and dev server
- **WebSocket** - Real-time communication with game server

## Project Structure

```
UI/
├── src/
│   ├── components/       # React components
│   │   ├── ActionPanel.tsx       # Player action input
│   │   ├── CharacterPanel.tsx    # Character list and details
│   │   ├── ChatPanel.tsx         # Game log and messages
│   │   ├── ConnectionScreen.tsx  # Login/connection screen
│   │   ├── GameLayout.tsx        # Main game layout
│   │   ├── SceneViewer.tsx       # Scene visualization (grid map)
│   │   └── TurnQueue.tsx         # Turn order display
│   ├── store/
│   │   └── gameStore.ts  # Zustand state management
│   ├── types/
│   │   └── game.ts       # TypeScript type definitions
│   ├── App.tsx           # Root component
│   ├── App.css           # Global styles
│   ├── main.tsx          # Entry point
│   └── index.css         # Base styles
├── package.json
├── tsconfig.json
├── vite.config.ts
└── server_requirements.md  # Server API specification
```

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
cd UI
npm install
```

### Development

```bash
npm run dev
```

This starts the Vite dev server on `http://localhost:3000`.

The dev server is configured to proxy:
- WebSocket connections (`/ws`) to `ws://localhost:8000`
- API requests (`/api`) to `http://localhost:8000`

### Build

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Features

### Connection Screen
- Enter session ID and player ID
- Quick start option for development
- Connection status display

### Game Layout
- **Header**: Game title, current scene, game mode (Story/Combat), turn queue
- **Left Panel**: Character list with HP bars, stats, and conditions
- **Center**: Scene viewer with grid map and action input panel
- **Right Panel**: Chat/game log with filtering options

### Character Panel
- List of all players and NPCs
- HP bars with color coding (green > 50%, yellow > 25%, red < 25%)
- Click to view detailed stats, abilities, and inventory
- Shows active conditions

### Scene Viewer
- 20x20 grid visualization
- Characters positioned based on coordinates
- Color-coded: Blue (players), Red (NPCs), Yellow (objects)
- Character status panel with HP, position, and conditions
- Legend for easy reference

### Action Panel
- Context-aware action input
- Shows whose turn it is
- Clarification messages from GM
- Action tips and guidelines
- Pending state indicator

### Chat Panel
- Filter by: All, DM, Players, Events
- Color-coded messages
- Event icons for different game events
- Auto-scroll to latest message

## Game State Management

The app uses Zustand for state management with the following key states:

- `mode`: UI mode (connecting, lobby, playing, error)
- `websocket`: WebSocket connection
- `session`: Current game session data
- `activeCharacter`: Currently selected/active character
- `messages`: Chat message history
- `events`: Game event history
- `turnQueue`: Turn order queue
- `isActionPending`: Waiting for GM response

## WebSocket Communication

### Client → Server Messages

```typescript
// Player action
{ type: "PLAYER_ACTION", payload: { player_id, request_text, character, timestamp } }

// Choose player
{ type: "CHOOSE_PLAYER", payload: { selected_player_id } }

// Subscribe to events
{ type: "SUBSCRIBE_EVENTS", payload: { subscriber_id } }
```

### Server → Client Messages

```typescript
// DM narration
{ type: "MASTER_MESSAGE", payload: { text, tag? } }

// Session update
{ type: "SESSION_UPDATE", payload: { session } }

// Game event
{ type: "GAME_EVENT", payload: { event } }

// Action request (prompt for input)
{ type: "ACTION_REQUEST", payload: { character } }

// Turn queue update
{ type: "TURN_QUEUE_UPDATE", payload: { turn_queue, turn_time } }

// Scene update
{ type: "SCENE_UPDATE", payload: { scene, characters, npcs, objects } }

// Error
{ type: "ERROR", payload: { message, details? } }
```

## Type Definitions

All TypeScript types are defined in `src/types/game.ts` and mirror the Python Pydantic models from:
- `schemas/in_game.py` - Character, Scene, Item, etc.
- `schemas/orchestration.py` - Event, Message, etc.

## Styling

The app uses CSS custom properties (variables) for theming:

```css
:root {
    --bg-primary: #0d1117;
    --bg-secondary: #161b22;
    --bg-tertiary: #21262d;
    --border-color: #30363d;
    --text-primary: #f0f6fc;
    --text-secondary: #8b949e;
    --accent-blue: #58a6ff;
    --accent-green: #3fb950;
    --accent-red: #f85149;
    --accent-yellow: #d29922;
    --accent-purple: #bc8cff;
}
```

## Next Steps

1. **Server Implementation**: Build the FastAPI WebSocket server per `server_requirements.md`
2. **Authentication**: Add player authentication
3. **Character Creation**: Add character creation flow
4. **Dice Rolling**: Add visual dice rolling
5. **Rich Text**: Support formatted text for descriptions
6. **Sound Effects**: Add ambient sounds and SFX
7. **Responsive Design**: Optimize for mobile/tablet

## License

Part of the MAGGxDND project.
