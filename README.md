# 🐉 MAGGxDND

> AI-Powered D&D Game Engine with Real-Time Web Interface

<div align="center">
  <img src="./img/MAGGxDND.png" alt="MAGGxDND Logo" width="60%">
</div>

<div align="center">

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

</div>

---

## 📖 About

**MAGGxDND** is an AI-powered D&D 5e game engine with a real-time web interface. It features:

- 🤖 **AI Dungeon Master (MAGG)** — Powered by Google Gemini for dynamic storytelling
- 🎮 **Real-Time WebSocket Communication** — Bidirectional game updates via WebSockets
- 🌍 **Living World** — NPCs act independently with their own goals and motivations
- 📝 **Full Character Creation** — AI-powered character generation with procedural fallback
- 🎲 **D&D 5e Rules** — Complete combat system with story and combat modes
- 💾 **Save/Load** — Persistent game state with JSON serialization
- 🌐 **Multiplayer** — Multiple players can join the same session simultaneously

### Architecture Overview

MAGGxDND uses a **layered hexagonal architecture** with clean separation between concerns:

```
┌─────────────────────────────────────────────────────┐
│              Frontend (React + TypeScript)          │
│  Components ↔ Zustand Store ↔ WebSocket Service     │
└────────────────────┬────────────────────────────────┘
                     │ HTTP REST + WebSocket
┌────────────────────▼────────────────────────────────┐
│              Backend (FastAPI + Python)              │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │ Routers  │  │ SessionMgr   │  │  Database     │ │
│  │ REST+WS  │→ │ Singleton    │  │  SQLite       │ │
│  └──────────┘  └──────┬───────┘  └───────────────┘ │
│                       │                              │
│              ┌────────▼────────┐                     │
│              │  SessionFactory │                     │
│              │  (Builds all)   │                     │
│              └────────┬────────┘                     │
│                       │                              │
│              ┌────────▼────────┐                     │
│              │    Delivery     │                     │
│              │ (WebSocket/REST)│                     │
│              └────────┬────────┘                     │
└───────────────────────┼──────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────┐
│           Core Engine (Platform-Agnostic)            │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ Session  │←→│ EventPool│←→│   Orchestrator   │   │
│  │ (State)  │  │ (Pub/Sub)│  │ (Input Routing)  │   │
│  └────┬─────┘  └──────────┘  └────────┬─────────┘   │
│       │                                │             │
│       └───────────┬────────────────────┘             │
│                   │                                  │
│          ┌────────▼────────┐                         │
│          │   Manipulator   │                         │
│          │ (Event Handler) │                         │
│          └─────────────────┘                         │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ Entities │  │   MAGG   │  │    Schemas       │   │
│  │Player/NPC│  │ (AI GM)  │  │  (Pydantic)      │   │
│  └──────────┘  └──────────┘  └──────────────────┘   │
└──────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Delivery Pattern**: All communication between frontend and game engine flows through **Delivery** objects
   - `GameDelivery` for WebSocket (real-time bidirectional)
   - `RESTAPIDelivery` for HTTP requests (stateless operations)

2. **Event-Driven Architecture**: Game state changes are represented as events
   - Events published to `EventPool` (pub/sub system)
   - `Manipulators` handle specific event types (combat, movement, items)

3. **Session Isolation**: Each game session is fully isolated
   - Sessions created via `SessionFactory` with all dependencies injected
   - `SessionManager` tracks active sessions and WebSocket connections

4. **AI-First with Fallback**: AI handles narrative generation, but procedural generation works when AI unavailable

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI (Python 3.11+) |
| **Frontend** | React 19 + TypeScript + Vite |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **AI** | Google Gemini API |
| **Real-time** | WebSocket (ws://) |
| **State Management** | Zustand (frontend) |
| **Vector DB** | ChromaDB (embeddings) |
| **Auth** | JWT tokens + OAuth2 (Google/Discord) |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- A Google Gemini API key ([get one free](https://makersuite.google.com/app/apikey))

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/MAGGxDND.git
cd MAGGxDND

# Copy env template
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 2. Install Dependencies

```bash
# Python backend
pip install -r requirements.txt

# Frontend
cd frontend && npm install && npm run build && cd ..
```

### 3. Run

```bash
python start.py
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

### Development Mode

```bash
# Backend (Terminal 1)
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (Terminal 2)
cd frontend && npm run dev
```

### API Documentation

Once running, view interactive API docs at:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📁 Project Structure

```
MAGGxDND/
├── backend/                    # FastAPI web backend
│   ├── main.py                 # FastAPI application entry point
│   └── src/
│       ├── api/
│       │   ├── middleware/     # Request logging, rate limiting
│       │   └── routers/
│       │       ├── session_router.py    # Session CRUD, AI init, actions
│       │       ├── websocket_game.py    # WebSocket /ws/{session_id}/{player_id}
│       │       ├── user.py              # User management
│       │       ├── oauth.py             # Google/Discord OAuth
│       │       ├── character.py         # Character creation
│       │       └── profile.py           # User profiles
│       ├── auth/
│       │   └── dependencies.py   # JWT auth (get_current_user)
│       ├── config/
│       │   └── settings.py       # Environment configuration
│       ├── database/
│       │   ├── base.py           # SQLAlchemy engine setup
│       │   └── session.py        # Database session dependency
│       ├── delivery/
│       │   ├── game_delivery.py     # WebSocket delivery (GameDelivery)
│       │   └── rest_api_delivery.py # REST API delivery (RESTAPIDelivery)
│       ├── game/
│       │   ├── session_factory.py   # Creates sessions with dependencies
│       │   └── session_manager.py   # Singleton session registry
│       ├── models/
│       │   ├── user.py              # User SQLAlchemy model
│       │   └── session.py           # GameSession SQLAlchemy model
│       ├── repositories/
│       │   ├── user.py              # User CRUD operations
│       │   └── session_repository.py # Session CRUD operations
│       ├── schema/                   # Pydantic schemas for API
│       ├── services/                 # Business logic services
│       └── utils/                    # Validation, security utilities
│
├── core/                         # Core game engine (platform-agnostic)
│   ├── entity/
│   │   ├── player.py                # Player entity
│   │   ├── npc.py                   # NPC entity
│   │   └── orchestrator.py          # Input classification & routing
│   ├── game/
│   │   ├── engine.py                # Session class (main game state)
│   │   ├── event_pool.py            # Pub/Sub event system
│   │   ├── manipulator.py           # Main event router
│   │   └── manipulators/            # Specific event handlers
│   │       ├── melee_attack_manipulation.py
│   │       ├── ranged_attack_manipulation.py
│   │       ├── movement_manipulator.py
│   │       └── item_interaction_manipulator.py
│   ├── interface/
│   │   └── delivery.py              # Abstract Delivery interface
│   ├── magg/
│   │   └── magg.py                  # MAGG - AI Game Master
│   ├── schemas/
│   │   ├── in_game.py               # Character, NPC, Scene models
│   │   └── orchestration.py         # Event, Verdict models
│   └── utils/                       # Dice, spatial, naming utilities
│
├── frontend/                     # React + TypeScript + Vite
│   └── src/
│       ├── components/              # 58 React components
│       ├── services/
│       │   ├── api.ts               # Base API client
│       │   ├── sessionAPI.ts        # Session API calls
│       │   ├── characterAPI.ts      # Character API calls
│       │   └── websocket.ts         # WebSocket client
│       ├── store/
│       │   └── gameStore.ts         # Zustand global state
│       ├── hooks/                   # Custom React hooks
│       └── types/                   # TypeScript definitions
│
├── data/                         # SQLite database storage
├── saves/                        # Game save files (JSON)
├── chroma_db/                    # Vector database (embeddings)
├── log/                          # Application logs
└── docs/                         # Documentation
```

---

## 🎮 How It Works

### Session Lifecycle

1. **Create Session**: `POST /api/v1/sessions` → `SessionFactory` creates Session with all dependencies
2. **Join Session**: Players register via REST API, then connect via WebSocket
3. **Initialize Game**: AI generates scene, characters, NPCs (with procedural fallback)
4. **Play Game**: Player actions flow through:
   ```
   Browser → WebSocket → Delivery.process_player_action() 
     → Orchestrator (classify input, check rules) 
     → MAGG (AI narrative generation)
     → Manipulator (execute events) 
     → EventPool (publish changes) 
     → WebSocket → Browser
   ```

### Communication Patterns

#### WebSocket (Real-time)
```
Browser ←→ ws://localhost:8000/ws/{session_id}/{player_id}
  - Player actions (character moves, attacks, interactions)
  - Game events (combat, movement, scene changes)
  - Master messages (narration, descriptions)
  - Session updates (state changes)
```

#### REST API (Stateless Operations)
```
Browser → HTTP → FastAPI Routers
  - Session CRUD operations
  - User authentication
  - Character creation
  - Game state queries
```

### Event System

The game uses a publish-subscribe event system:
- **EventPool**: Central event bus with per-subscriber queues
- **SubscriberQueue**: Each session gets its own event queue
- **Manipulators**: Handle specific event types and generate side effects

Event types include:
- `MELEE_ATTACK`, `RANGED_ATTACK` - Combat actions
- `CHARACTER_MOVEMENT` - Character movement
- `OBJECT_TRANSFER` - Item movement between inventories
- `ITEM_USE`, `ITEM_PICKUP` - Item interactions
- `LOCATION_CHANGE`, `SCENE_UPDATE` - World state changes

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Architecture](./docs/ARCHITECTURE.md) | Detailed system architecture |
| [API Reference](http://localhost:8000/docs) | Interactive API documentation |
| [Contributing](./CONTRIBUTING.md) | How to contribute |
| [Security](./SECURITY.md) | Security policy |
| [Code of Conduct](./CODE_OF_CONDUCT.md) | Community guidelines |

---

## 🧪 Testing

```bash
# Backend tests
cd backend && pytest tests/

# Frontend tests
cd frontend && npm run test

# End-to-end tests
pytest tests/e2e/
```

---

## 🤝 Contributing

We welcome contributions! Please read our [Contributing Guide](./CONTRIBUTING.md) before submitting PRs.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## 🔒 Security

Found a security vulnerability? Please review our [Security Policy](./SECURITY.md).

---

## 📝 License

This project is licensed under the MIT License — see the [LICENSE](./LICENSE) file for details.

---

<div align="center">

**MAGGxDND** — Where AI meets dice & dragons 🐉🎲

[Documentation](./docs/) · [API Docs](http://localhost:8000/docs) · [Issues](../../issues) · [Pull Requests](../../pulls)

</div>
