# 🚀 MAGGxDND Quick Start Guide

## Setup Instructions (5 minutes)

### 1. Environment Setup

```bash
# Navigate to project root
cd C:\VS_Code\MAGGxDND

# Copy environment template
copy .env.example .env

# Edit .env and add your Gemini API key
# Get one at: https://makersuite.google.com/app/apikey
notepad .env
```

**Minimum required in `.env`:**
```bash
GEMINI_API_KEY=your_actual_api_key_here
SECRET_KEY=change-this-for-production-abc123xyz
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install SKLS_core (required dependency)
pip install -e C:\VS_Code\SKLS_core

# Install UI dependencies
cd UI
npm install
cd ..
```

### 3. Build UI

```bash
cd UI
npm run build
cd ..
```

### 4. Start the Server

```bash
# Option 1: Using start.py (recommended)
python start.py

# Option 2: Direct uvicorn
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000
```

### 5. Open in Browser

```
http://localhost:8000
```

---

## 🧪 Quick Test

### Test API Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2026-03-10T..."
}
```

### Test Creating a Session

```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d "{\"session_name\": \"Test Session\", \"game_mode\": \"STORY\"}"
```

---

## 🛠 Development Mode

### Terminal 1 - Server
```bash
python -m uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2 - UI Dev Server
```bash
cd UI
npm run dev
```

Open: `http://localhost:5173` (Vite dev server)

---

## 📝 Common Issues

### "ModuleNotFoundError: No module named 'skls_generator'"
```bash
pip install -e C:\VS_Code\SKLS_core
```

### "UI not built"
```bash
cd UI
npm run build
cd ..
```

### "GEMINI_API_KEY not set"
1. Get API key from https://makersuite.google.com/app/apikey
2. Add to `.env`: `GEMINI_API_KEY=your_key_here`
3. Restart server

### CORS errors in browser
1. Check `.env` has correct `CORS_ORIGINS`
2. Add your frontend URL: `CORS_ORIGINS=http://localhost:5173,http://localhost:3000`
3. Restart server

### Port 8000 already in use
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /F /PID <PID>
```

---

## 📚 Next Steps

- Read [IMPROVEMENTS_SUMMARY.md](./IMPROVEMENTS_SUMMARY.md) for all enhancements
- Check [ENV_SETUP_GUIDE.md](./server/ENV_SETUP_GUIDE.md) for environment variables
- See [RUN_ON_8000.md](./RUN_ON_8000.md) for deployment options

---

## ✅ Verification Checklist

- [ ] `.env` file created with API key
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] SKLS_core installed
- [ ] UI built (`npm run build`)
- [ ] Server starts without errors
- [ ] Health endpoint responds (`/health`)
- [ ] UI loads in browser

---

**Need Help?** Check the documentation in `/docs` or open an issue.
