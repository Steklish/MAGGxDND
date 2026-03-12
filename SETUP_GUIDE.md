# MAGGxDND - Setup & Configuration Guide

## 🎯 Overview

This guide will help you set up the MAGGxDND platform with:
- Landing page for first-time visitors
- Home page for authorized users (D&D Beyond inspired)
- Google & Discord OAuth authentication
- Optimized SQLite database

## 📋 Prerequisites

- Python 3.9+
- Node.js 18+
- Git

## 🚀 Quick Start

### 1. Backend Setup

```bash
# Navigate to project root
cd C:\VS_Code\MAGGxDND

# Create virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy environment file
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac

# Edit .env and add your API keys
# - GEMINI_API_KEY (required for AI features)
# - SECRET_KEY (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
```

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# This will install:
# - react-router-dom (for routing)
# - zustand (state management)
# - axios (HTTP client)
```

### 3. OAuth Configuration

#### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Google+ API"
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Set authorized redirect URI: `http://localhost:8000/api/v1/oauth/google/callback`
6. Copy Client ID and Client Secret to `.env`

```env
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/oauth/google/callback
```

#### Discord OAuth Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "OAuth2" section
4. Add redirect URI: `http://localhost:8000/api/v1/oauth/discord/callback`
5. Copy Client ID and Client Secret to `.env`

```env
DISCORD_CLIENT_ID=your_discord_client_id_here
DISCORD_CLIENT_SECRET=your_discord_client_secret_here
DISCORD_REDIRECT_URI=http://localhost:8000/api/v1/oauth/discord/callback
```

### 4. Database Optimization

The database is automatically optimized on startup with:
- WAL mode for better concurrency
- Foreign keys enabled
- 64MB cache size
- 5 second busy timeout

To manually optimize:

```bash
# Run database optimizer
python -m backend.src.database.optimizer
```

### 5. Run the Application

```bash
# From project root, run the server
python start.py

# Or use run_server.py
python run_server.py

# Server will start on http://localhost:8000
# API docs available at http://localhost:8000/docs
```

## 🌐 Application Flow

### First-Time Visitors
1. Land on **Landing Page** with project overview
2. Can explore features, how it works, about section
3. Click "Get Started" or "Sign In" to authenticate

### Authentication Options
1. **Username/Password** - Traditional registration
2. **Google OAuth** - One-click Google sign-in
3. **Discord OAuth** - One-click Discord sign-in
4. **Guest Mode** - Try without account (24-hour limit)

### After Authentication
1. New users → Character Creation flow
2. Returning users → **Home Page** (D&D Beyond style)

### Home Page Features
- **Overview Tab**: Recent sessions, characters, quick actions
- **Characters Tab**: Manage all your characters
- **Sessions Tab**: Browse and join game sessions
- **Quick Actions**: Create session, new character, quick play

## 📁 Project Structure

```
MAGGxDND/
├── backend/
│   ├── src/
│   │   ├── api/routers/
│   │   │   ├── oauth.py          # Google & Discord OAuth
│   │   │   ├── login.py          # Auth endpoints (updated with register)
│   │   │   └── ...
│   │   ├── database/
│   │   │   ├── optimizer.py      # Database optimization tools
│   │   │   └── init_db.py        # Updated with optimizations
│   │   └── config/settings.py    # Updated with OAuth settings
│   └── main.py                   # Updated with OAuth router
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── HomePage.tsx      # New: Home page for auth users
│       │   ├── HomePage.css
│       │   ├── OAuthCallback.tsx # New: OAuth callback handler
│       │   ├── OAuthCallback.css
│       │   ├── AuthModal.tsx     # Updated: OAuth buttons
│       │   └── LandingPage.tsx   # Existing: Landing page
│       ├── App.tsx               # Updated: Routing logic
│       └── main.tsx              # Updated: React Router setup
└── .env.example                  # Updated: OAuth variables
```

## 🔧 Database Optimization Features

The database now includes:

1. **WAL Mode** - Write-Ahead Logging for better concurrency
2. **Foreign Keys** - Enforced referential integrity
3. **Cache Size** - 64MB page cache for faster queries
4. **Busy Timeout** - 5 second wait for locked resources
5. **Auto-Vacuum** - Periodic cleanup of unused space

### Manual Database Tools

```python
from backend.src.database.optimizer import (
    optimize_database,
    backup_database,
    cleanup_old_backups,
    get_database_info,
    reset_database
)

# Get database info
info = get_database_info()
print(info)

# Optimize database
stats = optimize_database()
print(f"Saved: {stats['size_saved_mb']} MB")

# Create backup
backup_path = backup_database()
print(f"Backup created: {backup_path}")

# Cleanup old backups (keep last 5)
deleted = cleanup_old_backups(keep_count=5)
print(f"Deleted {deleted} old backups")
```

## 🎨 UI/UX Features

### Landing Page
- Animated gradient background
- Feature cards with hover effects
- How it works section
- Responsive design
- Dynamic scroll progress bar

### Home Page (D&D Beyond Inspired)
- Fixed navigation header with blur effect
- Hero section with user stats
- Tab-based navigation (Overview, Characters, Sessions)
- Recent activity cards
- Quick action buttons
- Character avatars with race icons
- Session status badges

### Auth Modal
- Google OAuth button
- Discord OAuth button
- Guest mode button
- Remember me option
- Password validation
- Error handling with animations

## 🔐 Security Features

1. **HttpOnly Cookies** - JWT tokens stored securely
2. **CSRF Protection** - State parameter for OAuth
3. **Password Hashing** - bcrypt with 12 rounds
4. **Rate Limiting** - 5 requests/minute for auth endpoints
5. **Token Expiration** - 30 days for OAuth, 24 hours for guests

## 🐛 Troubleshooting

### Database Issues

```bash
# If database is corrupted or has issues
python -m backend.src.database.optimizer

# Or reset completely (WARNING: deletes all data)
from backend.src.database.optimizer import reset_database
reset_database()
```

### OAuth Not Working

1. Check redirect URIs match exactly
2. Verify CLIENT_ID and CLIENT_SECRET are correct
3. Ensure CORS origins include frontend URL
4. Check browser console for errors

### Frontend Not Loading

```bash
cd frontend
npm install
npm run build
```

## 📝 Environment Variables Reference

```env
# Required
GEMINI_API_KEY=your_key_here
SECRET_KEY=your_secret_key_here

# OAuth (Optional but recommended)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/oauth/google/callback

DISCORD_CLIENT_ID=
DISCORD_CLIENT_SECRET=
DISCORD_REDIRECT_URI=http://localhost:8000/api/v1/oauth/discord/callback

FRONTEND_URL=http://localhost:5173

# Database
DATABASE_URL=sqlite:///./maggxdnd.db

# Server
SERVER_HOST=127.0.0.1
SERVER_PORT=8000
DEBUG=True

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_DEFAULT=100/minute
RATE_LIMIT_AUTH=5/minute
```

## 🎯 Next Steps

1. **Test Authentication Flow**
   - Register new account
   - Try OAuth providers
   - Test guest mode
   - Verify remember me

2. **Explore Home Page**
   - Check all tabs
   - Create a character
   - Create/join session

3. **Database Health**
   - Run optimizer
   - Check database info
   - Create backup

4. **Production Deployment**
   - Change SECRET_KEY
   - Enable HTTPS
   - Use PostgreSQL instead of SQLite
   - Configure proper CORS origins

## 📞 Support

For issues or questions:
- Check logs in `backend/log/`
- Review API docs at `/docs`
- Inspect browser console for frontend errors

---

**Happy Gaming! 🐉⚔️🎲**
