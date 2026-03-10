# MAGGxDND UI

React-based web interface for the MAGGxDND AI-powered D&D game engine.

## Tech Stack

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Zustand** - State management
- **Vite** - Build tool and dev server
- **WebSocket** - Real-time communication with game server

## Features

### 🎨 Design System
- **Dark theme** with Assiko-inspired color palette
- **Custom fonts**: Rajdhani (UI), Playwrite New Zealand Basic (lore)
- **CSS custom properties** for consistent theming
- **Responsive** layout with adaptive panels

### 📐 Layout
- **Resizable side panels** (15-50% width)
- **Collapsible panels** with icon navigation
- **Resizable header** (80-240px height)
- **Zero-width resize handles** (invisible until hovered)

### 👥 Character Panel (Left)
- List of all players and NPCs
- HP bars with color coding
- Click to view/select character
- Hover tooltips with full stats
- Yellow accent color scheme

### 💬 Chat Panel (Right)
- Game log with filtering (All/DM/Players/Events)
- Event icons with tooltips
- Color-coded messages
- Auto-scroll to latest
- Orange accent color scheme

### ⚔️ Turn Queue (Header)
- Vertical portrait rectangles
- Sorted by initiative
- Attitude-based colors:
  - Player: Purple
  - Ally: Green
  - Neutral: Yellow
  - Hostile: Orange
- Active turn highlighted (scale + glow)
- Death save counters for dying characters

### 🎯 Action Panel (Center Bottom)
- Action input textarea
- Submit/Clear/Skip Turn buttons
- Clarification messages from GM

### 📜 Footer
- Click gradient handle to reveal
- 3 sections: D&D Rules, Resources, About
- Links to official D&D resources
- Click outside to close
- Responsive grid (3→2→1 columns)

### 💡 Tooltips
- React Portal-based (no layout impact)
- Dynamic size based on content
- Character previews with full stats
- Filter descriptions
- Event type explanations

## Project Structure

```
UI/
├── src/
│   ├── components/
│   │   ├── ActionPanel.tsx       # Player action input
│   │   ├── CharacterPanel.tsx    # Character list and details
│   │   ├── ChatPanel.tsx         # Game log and messages
│   │   ├── Footer.tsx            # D&D resources footer
│   │   ├── GameLayout.tsx        # Main game layout
│   │   ├── SceneViewer.tsx       # Scene visualization
│   │   ├── Tooltip.tsx           # Reusable tooltip component
│   │   └── TurnQueue.tsx         # Turn order display
│   ├── store/
│   │   └── gameStore.ts          # Zustand state management
│   ├── types/
│   │   └── game.ts               # TypeScript type definitions
│   ├── App.tsx                   # Root component
│   ├── index.css                 # Global styles + fonts
│   └── main.tsx                  # Entry point
├── package.json
├── tsconfig.json
├── vite.config.ts
├── README.md
├── dev_diary.md                  # Development diary
└── server_requirements.md        # Server API specification
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

This starts the Vite dev server on `http://localhost:5173`.

### Build

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Color Scheme

| Color | Hex | Usage |
|-------|-----|-------|
| Background Primary | `#0a0a0a` | Main background |
| Background Secondary | `#141414` | Panels |
| Background Tertiary | `#1f1f1f` | Cards |
| Accent Orange | `#ff6b35` | Primary accent, Chat panel |
| Accent Gold | `#f4a261` | Gradient, Character panel |
| Accent Green | `#2a9d8f` | Ally NPCs, Story mode |
| Accent Yellow | `#e9c46a` | Neutral NPCs |
| Accent Purple | `#9d4edd` | Player characters, Header |
| Accent Red | `#e63946` | Hostile NPCs, Combat mode |

## Controls

### Panel Resizing
- **Drag** the border between panels to resize
- **Collapse** via buttons in panel headers
- **Expand** via icon strip when collapsed

### Turn Queue
- **Portraits** show current turn order
- **Active character** is highlighted (larger, full opacity)
- **Others** are dimmed (50% opacity)

### Footer
- **Click** the gradient handle at bottom to reveal
- **Click** outside footer to close
- **Links** open in new tabs

## Development Diary

See [dev_diary.md](./dev_diary.md) for detailed development logs.

## Server Requirements

See [server_requirements.md](./server_requirements.md) for WebSocket/REST API specification.

## License

Part of the MAGGxDND project.
