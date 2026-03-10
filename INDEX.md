# 🗺️ MAGGxDND Project Index

Quick navigation guide for the MAGGxDND project.

---

## 🚀 Getting Started

| Resource | Location | Description |
|----------|----------|-------------|
| **Quick Start** | [`docs/QUICKSTART.md`](./docs/QUICKSTART.md) | 5-minute setup guide |
| **README** | [`README.md`](./README.md) | Main project documentation |
| **Env Setup** | [`.env.example`](./.env.example) | Environment variables template |

---

## 📂 Core Directories

### Backend (`backend/`)

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `backend/src/api/routers/` | REST API endpoints | [`session_router.py`](./backend/src/api/routers/session_router.py), [`websocket_game.py`](./backend/src/api/routers/websocket_game.py) |
| `backend/src/config/` | Configuration | [`settings.py`](./backend/src/config/settings.py) |
| `backend/src/game/` | Session management | [`session_manager.py`](./backend/src/game/session_manager.py) |
| `backend/src/auth/` | Authentication | [`dependencies.py`](./backend/src/auth/dependencies.py) |
| `backend/src/utils/` | Utilities | [`validation.py`](./backend/src/utils/validation.py), [`security.py`](./backend/src/utils/security.py) |
| `backend/tests/` | Backend tests | [`test_health.py`](./backend/tests/test_health.py) |

### Frontend (`frontend/`)

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `frontend/src/components/` | React components | [`GameLayout.tsx`](./frontend/src/components/GameLayout.tsx), [`CharacterPanel.tsx`](./frontend/src/components/CharacterPanel.tsx) |
| `frontend/src/services/` | API clients | [`api.ts`](./frontend/src/services/api.ts), [`websocket.ts`](./frontend/src/services/websocket.ts) |
| `frontend/src/store/` | State management | [`gameStore.ts`](./frontend/src/store/gameStore.ts) |
| `frontend/src/types/` | TypeScript types | [`game.ts`](./frontend/src/types/game.ts) |
| `frontend/arts/` | UI assets | [`README.md`](./frontend/arts/README.md) |

### Core Engine (`core/`)

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `core/game/` | Game engine | [`engine.py`](./core/game/engine.py), [`event_pool.py`](./core/game/event_pool.py) |
| `core/entity/` | Game entities | [`player.py`](./core/entity/player.py), [`npc.py`](./core/entity/npc.py) |
| `core/schemas/` | Data schemas | [`in_game.py`](./core/schemas/in_game.py) |
| `core/magg/` | AI Game Master | [`magg.py`](./core/magg/magg.py) |
| `core/utils/` | Game utilities | [`dice_utils.py`](./core/utils/dice_utils.py) |

### Documentation (`docs/`)

| File | Description |
|------|-------------|
| [`QUICKSTART.md`](./docs/QUICKSTART.md) | Quick start guide |
| [`REORGANIZATION_GUIDE.md`](./docs/REORGANIZATION_GUIDE.md) | Project structure guide |
| [`SERVER_ARCHITECTURE.md`](./docs/SERVER_ARCHITECTURE.md) | Server architecture |
| [`SESSION_API_GUIDE.md`](./docs/SESSION_API_GUIDE.md) | Session API documentation |
| [`prompts/`](./docs/prompts/) | AI prompts for game generation |

---

## 🔑 Key Entry Points

| File | Purpose | Command |
|------|---------|---------|
| [`main.py`](./main.py) | CLI game launcher | `python main.py` |
| [`start.py`](./start.py) | Server launcher | `python start.py` |
| [`backend/main.py`](./backend/main.py) | FastAPI application | `uvicorn backend.main:app` |
| [`frontend/src/main.tsx`](./frontend/src/main.tsx) | React entry point | `npm run dev` |

---

## 🧪 Testing

| Command | Description |
|---------|-------------|
| `pytest backend/tests/` | Run backend tests |
| `npm run test` (in frontend/) | Run frontend tests |
| `npm run test:coverage` | Test coverage report |

---

## 🔗 API Endpoints

### Health Checks
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness check
- `GET /health/live` - Liveness check

### Sessions
- `GET /api/v1/sessions` - List sessions
- `POST /api/v1/sessions` - Create session
- `GET /api/v1/sessions/{id}` - Get session info
- `DELETE /api/v1/sessions/{id}` - Delete session
- `POST /api/v1/sessions/{id}/start` - Start session
- `POST /api/v1/sessions/{id}/players` - Join session
- `DELETE /api/v1/sessions/{id}/players/{id}` - Leave session

### WebSocket
- `WS /ws/{session_id}/{player_id}` - Real-time game updates

### Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 🎨 UI Components

### Common Components
| Component | File | Description |
|-----------|------|-------------|
| ErrorBoundary | [`ErrorBoundary.tsx`](./frontend/src/components/common/ErrorBoundary.tsx) | Error handling |
| LoadingSpinner | [`LoadingSpinner.tsx`](./frontend/src/components/common/LoadingSpinner.tsx) | Loading indicator |
| Skeleton | [`Skeleton.tsx`](./frontend/src/components/common/Skeleton.tsx) | Loading placeholder |
| Toast | [`Toast.tsx`](./frontend/src/components/common/Toast.tsx) | Notifications |

### Game Components
| Component | File | Description |
|-----------|------|-------------|
| GameLayout | [`GameLayout.tsx`](./frontend/src/components/GameLayout.tsx) | Main game layout |
| ActionPanel | [`ActionPanel.tsx`](./frontend/src/components/ActionPanel.tsx) | Player actions |
| CharacterPanel | [`CharacterPanel.tsx`](./frontend/src/components/CharacterPanel.tsx) | Character stats |
| ChatPanel | [`ChatPanel.tsx`](./frontend/src/components/ChatPanel.tsx) | Chat & event log |
| SceneViewer | [`SceneViewer.tsx`](./frontend/src/components/SceneViewer.tsx) | Scene visualization |

---

## ⚙️ Configuration

| File | Purpose |
|------|---------|
| [`.env.example`](./.env.example) | Environment variables template |
| [`backend/src/config/settings.py`](./backend/src/config/settings.py) | Settings loader |
| [`frontend/vite.config.ts`](./frontend/vite.config.ts) | Vite configuration |
| [`requirements.txt`](./requirements.txt) | Python dependencies |
| [`frontend/package.json`](./frontend/package.json) | Node.js dependencies |

---

## 📦 Build & Deploy

### Development
```bash
# Backend
python -m uvicorn backend.main:app --reload

# Frontend
cd frontend && npm run dev
```

### Production
```bash
# Build frontend
cd frontend && npm run build

# Start server
python start.py
```

---

## 🆘 Support

| Issue | Solution |
|-------|----------|
| Import errors | Run `pip install -e C:\VS_Code\SKLS_core` |
| UI not found | Run `cd frontend && npm run build` |
| CORS errors | Check `CORS_ORIGINS` in `.env` |
| WebSocket fails | Verify server is running on port 8000 |

---

## 📊 Project Stats

| Category | Count |
|----------|-------|
| Backend Routers | 8 |
| React Components | 20+ |
| API Endpoints | 15+ |
| Core Modules | 6 |
| Documentation Files | 10+ |

---

**Last Updated**: 2026-03-10  
**Version**: 2.0.0
