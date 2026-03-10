# MAGGxDND Project Structure Refactoring Guide

## 🎯 Overview

The project has been reorganized to improve maintainability and clarity. The main changes:

1. **`server/` → `backend/`** - All backend code moved to `backend/`
2. **`UI/` → `frontend/`** - All frontend code moved to `frontend/`
3. **Core modules → `core/`** - Game engine, entities, schemas moved to `core/`
4. **Documentation → `docs/`** - All documentation consolidated in `docs/`

---

## 📁 New Project Structure

```
MAGGxDND/
├── backend/                    # Backend server (was server/)
│   ├── src/
│   │   ├── api/               # REST API routers
│   │   ├── auth/              # Authentication logic
│   │   ├── config/            # Configuration & settings
│   │   ├── database/          # Database setup & sessions
│   │   ├── delivery/          # Event delivery systems
│   │   ├── game/              # Game session management
│   │   ├── models/            # SQLAlchemy models
│   │   ├── repositories/      # Data access layer
│   │   ├── schema/            # Pydantic schemas
│   │   ├── services/          # Business logic services
│   │   └── utils/             # Backend utilities
│   ├── main.py                # FastAPI application entry
│   ├── tests/                 # Backend tests
│   └── ENV_SETUP_GUIDE.md
│
├── frontend/                   # Frontend React app (was UI/)
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── services/          # API & WebSocket clients
│   │   ├── store/             # State management (Zustand)
│   │   ├── tests/             # Frontend tests
│   │   └── types/             # TypeScript types
│   ├── public/                # Static assets
│   ├── package.json
│   └── vite.config.ts
│
├── core/                       # Core game engine (NEW)
│   ├── game/                  # Game engine & loop
│   ├── entity/                # Player, NPC, Orchestrator
│   ├── schemas/               # Game data schemas
│   ├── magg/                  # AI Game Master
│   ├── interface/             # Delivery interfaces
│   └── utils/                 # Shared utilities
│
├── docs/                       # Documentation (consolidated)
│   ├── prompts/               # AI prompts
│   ├── IMPROVEMENTS_SUMMARY.md
│   ├── QUICKSTART.md
│   ├── RUN_ON_8000.md
│   └── ... (other docs)
│
├── chroma_db/                  # Vector database
├── log/                        # Application logs
├── img/                        # Images & assets
├── prompts/                    # → Moved to docs/prompts/
│
├── main.py                     # CLI entry point
├── start.py                    # Server launcher
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔄 Migration Steps

### Step 1: Update Python Path Imports

#### Backend imports (in `backend/`):

**Before:**
```python
from server.src.config import settings
from server.src.api.routers import session_router
```

**After:**
```python
from backend.src.config import settings
from backend.src.api.routers import session_router
```

#### Core module imports:

**Before:**
```python
from game.engine import Session
from entity.player import Player
from schemas.in_game import Character
from magg.magg import Magg
```

**After:**
```python
from core.game.engine import Session
from core.entity.player import Player
from core.schemas.in_game import Character
from core.magg.magg import Magg
```

### Step 2: Update Environment Variables

**`.env` file (root):**

```bash
# No changes needed - paths remain the same
DATABASE_URL=sqlite:///./maggxdnd.db
LOG_FILE=./log/server.log
```

### Step 3: Update Start Scripts

**`start.py`:**

```python
# Update import path
from backend.main import app  # was: from server.main import app

# Run with:
uvicorn.run(
    "backend.main:app",  # was: "server.main:app"
    host="0.0.0.0",
    port=8000
)
```

**`main.py`:**

```python
# Update all imports
from core.game.engine import Session
from core.game.event_pool import EventPool
from core.game.manipulator import Manipulator
from core.entity.orchestrator import Orchestrator
from core.interface.native_terminal_delivery import NativeTerminalDelivery
from core.schemas.in_game import Character, NPCCharacter, SceneNode
```

### Step 4: Update Package References

**`requirements.txt`:** No changes needed

**`backend/src/main.py`:** Update imports:
```python
# Before
from server.src.api.routers import dev, login, user, access_group
from server.src.database import init_db, engine

# After
from backend.src.api.routers import dev, login, user, access_group
from backend.src.database import init_db, engine
```

---

## 🔧 Files That Need Updates

### Critical Files (Must Update):

1. **`main.py`** (root) - Update all imports
2. **`start.py`** - Update uvicorn run path
3. **`backend/main.py`** - Update internal imports
4. **`backend/src/**/*.py`** - Update server → backend imports

### Optional Files (Should Update):

1. **`README.md`** - Update structure documentation
2. **`docs/QUICKSTART.md`** - Update paths
3. **`.github/workflows/`** (if exists) - Update CI/CD paths

---

## ✅ Verification Checklist

After migration, verify:

- [ ] `python main.py` runs without import errors
- [ ] `python start.py` starts the server
- [ ] Backend tests pass: `pytest backend/tests/`
- [ ] Frontend builds: `cd frontend && npm run build`
- [ ] API endpoints respond: `curl http://localhost:8000/health`
- [ ] WebSocket connects successfully

---

## 🚨 Common Issues & Solutions

### Issue 1: `ModuleNotFoundError: No module named 'server'`

**Solution:** Replace all `server.` with `backend.`

```bash
# Find and replace in all Python files
find . -name "*.py" -type f -exec sed -i 's/from server\./from backend./g' {} \;
find . -name "*.py" -type f -exec sed -i 's/import server\./import backend./g' {} \;
```

### Issue 2: `ModuleNotFoundError: No module named 'game'`

**Solution:** Replace all `from game` with `from core.game`

```bash
# Find and replace
find . -name "*.py" -type f -exec sed -i 's/from game\./from core.game./g' {} \;
find . -name "*.py" -type f -exec sed -i 's/from entity\./from core.entity./g' {} \;
find . -name "*.py" -type f -exec sed -i 's/from schemas\./from core.schemas./g' {} \;
find . -name "*.py" -type f -exec sed -i 's/from magg\./from core.magg./g' {} \;
```

### Issue 3: Frontend API calls breaking

**Solution:** No changes needed - API routes remain the same (`/api/v1/...`)

### Issue 4: Relative import errors in backend

**Solution:** Update `PYTHONPATH` or use absolute imports

```bash
# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/MAGGxDND"
```

---

## 📊 Benefits of New Structure

| Before | After | Benefit |
|--------|-------|---------|
| `server/` mixed with core | `backend/` separate | Clear separation of concerns |
| `UI/` in root | `frontend/` separate | Consistent naming |
| Core modules scattered | `core/` consolidated | Easy to find engine code |
| Docs in multiple places | `docs/` centralized | Single source of truth |
| Unclear boundaries | Clear module boundaries | Better maintainability |

---

## 🔙 Rollback Instructions

If you need to revert:

```bash
# Remove new directories
rm -rf backend frontend core

# Rename old directories back
mv server.bak server 2>/dev/null || true
mv UI.bak UI 2>/dev/null || true

# Restore core modules
mv core/game game 2>/dev/null || true
mv core/entity entity 2>/dev/null || true
# ... etc
```

---

## 📝 Notes

- **Core modules** (`game/`, `entity/`, `schemas/`, `magg/`, `interface/`, `utils/`) are **NOT modified** - only moved
- **All functionality** remains the same
- **No breaking changes** to API endpoints or business logic
- **Imports only** need to be updated

---

**Migration completed:** 2026-03-10
**Version:** 2.0.0
