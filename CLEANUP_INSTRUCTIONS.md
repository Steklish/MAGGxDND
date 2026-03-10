# 🧹 MAGGxDND Cleanup Instructions

After reorganizing the project structure, follow these steps to remove old duplicate files.

---

## ⚠️ Important

**DO NOT delete core/ directory!** This contains the main game engine.

The old directories (`game/`, `entity/`, `schemas/`, etc.) are duplicates and should be removed.

---

## 🪟 Windows (Manual)

### 1. Delete Duplicate Directories

Delete these folders from `C:\VS_Code\MAGGxDND\`:

```
❌ server/           (replaced by backend/)
❌ UI/               (replaced by frontend/)
❌ game/             (moved to core/game/)
❌ entity/           (moved to core/entity/)
❌ schemas/          (moved to core/schemas/)
❌ magg/             (moved to core/magg/)
❌ interface/        (moved to core/interface/)
❌ utils/            (moved to core/utils/)
❌ prompts/          (moved to docs/prompts/)
```

### 2. Delete Temporary Files

```
❌ migrate_imports.bat
❌ migrate_imports.ps1
❌ cleanup.bat
❌ IMPROVEMENTS_SUMMARY.md
❌ web_interface_async_plan.md
```

---

## 🚀 Automated Cleanup

### Run Cleanup Script

```bash
# From project root
cleanup.bat
```

This will automatically remove all duplicate and temporary files.

---

## ✅ Verify New Structure

After cleanup, your directory should look like:

```
MAGGxDND/
├── backend/           ✓
├── frontend/          ✓
├── core/              ✓
├── docs/              ✓
├── chroma_db/         ✓
├── log/               ✓
├── img/               ✓
├── main.py            ✓
├── start.py           ✓
├── README.md          ✓
├── INDEX.md           ✓
└── .env.example       ✓
```

---

## 🔍 Test After Cleanup

### 1. Test Backend

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 2. Test Frontend

```bash
cd frontend
npm run build
```

### 3. Test CLI

```bash
python main.py
```

---

## 🆘 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'game'"

**Solution:** Update imports in `main.py`:

```python
# Before
from game.engine import Session

# After
from core.game.engine import Session
```

### Error: "No module named 'server'"

**Solution:** Update imports to use `backend`:

```python
# Before
from server.main import app

# After
from backend.main import app
```

### Files Still There?

Some files may be in use. Close:
- Python processes
- Node.js processes
- Any IDE

Then try deleting again.

---

## 📊 Disk Space Saved

Expected cleanup results:

| Item | Size Saved |
|------|------------|
| Duplicate server/ | ~50 MB |
| Duplicate UI/node_modules/ | ~500 MB |
| Old core directories | ~20 MB |
| **Total** | **~570 MB** |

---

## 🎯 Next Steps

After cleanup:

1. ✅ Read [`INDEX.md`](./INDEX.md) for navigation
2. ✅ Review [`README.md`](./README.md) for setup
3. ✅ Check [`frontend/arts/README.md`](./frontend/arts/README.md) for UI assets
4. ✅ Run the application!

---

**Questions?** See [`REORGANIZATION_GUIDE.md`](./docs/REORGANIZATION_GUIDE.md)
