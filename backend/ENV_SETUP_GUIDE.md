# MAGGxDND Environment Configuration Guide

This guide explains all environment variables used in the MAGGxDND project.

## Table of Contents

- [Server Environment Variables](#server-environment-variables)
- [UI Environment Variables](#ui-environment-variables)
- [Development vs Production](#development-vs-production)
- [Security Best Practices](#security-best-practices)

---

## Server Environment Variables

Create a `.env` file in the project root directory (`C:\VS_Code\MAGGxDND\.env`).

### **Required Variables**

```bash
# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
```

### **Security Settings**

```bash
# IMPORTANT: Change this in production!
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Password hashing
HASHING_ROUNDS=12
```

### **CORS Settings**

```bash
# Comma-separated list of allowed origins
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173

# Allow credentials (cookies, authorization headers)
CORS_ALLOW_CREDENTIALS=True

# Allowed HTTP methods
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,PATCH,OPTIONS

# Allowed headers
CORS_ALLOW_HEADERS=Authorization,Content-Type,Accept
```

### **Rate Limiting**

```bash
# Enable/disable rate limiting
RATE_LIMIT_ENABLED=True

# Default rate limit for all endpoints
RATE_LIMIT_DEFAULT=100/minute

# Stricter limits for authentication endpoints
RATE_LIMIT_AUTH=5/minute

# API endpoints limit
RATE_LIMIT_API=60/minute
```

### **Server Configuration**

```bash
# Server host and port
SERVER_HOST=127.0.0.1
SERVER_PORT=8000

# Debug mode (disable in production!)
DEBUG=False

# Logging
LOG_LEVEL=INFO
LOG_FILE=./log/server.log
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5
```

### **Database**

```bash
# SQLite (default)
DATABASE_URL=sqlite:///./maggxdnd.db

# PostgreSQL (for production)
# DATABASE_URL=postgresql://user:password@localhost:5432/maggxdnd
```

### **AI/ML Settings**

```bash
# Gemini AI
GEMINI_MODEL=gemini-2.0-flash

# LlamaCPP (optional alternative)
LLAMACPP_CHAT_BASE=http://localhost:8080

# AI generation retries
AI_GEN_RETRIES=3
MODEL_ROLE=model
```

### **WebSocket Settings**

```bash
# Heartbeat interval in seconds
WS_HEARTBEAT_INTERVAL=30

# Maximum message size in bytes
WS_MAX_MESSAGE_SIZE=1048576
```

### **Session Settings**

```bash
# Maximum players per session
SESSION_MAX_PLAYERS=5

# Session timeout in minutes
SESSION_TIMEOUT_MINUTES=120
```

---

## UI Environment Variables

Create a `.env` file in the UI directory (`C:\VS_Code\MAGGxDND\UI\.env`).

```bash
# API Base URL (for development)
VITE_API_BASE_URL=http://localhost:8000/api/v1

# WebSocket URL (for development)
VITE_WS_BASE_URL=ws://localhost:8000/ws

# Enable/disable features
VITE_ENABLE_ANALYTICS=false

# Analytics ID (if using analytics)
VITE_ANALYTICS_ID=
```

---

## Development vs Production

### **Development (.env)**

```bash
# Server
DEBUG=True
SECRET_KEY=dev-secret-key-not-for-production
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
LOG_LEVEL=DEBUG
RATE_LIMIT_ENABLED=False

# Database
DATABASE_URL=sqlite:///./maggxdnd.db
```

### **Production (.env.production or system env)**

```bash
# Server
DEBUG=False
SECRET_KEY=<generate-strong-random-key>
CORS_ORIGINS=https://yourdomain.com
LOG_LEVEL=INFO
RATE_LIMIT_ENABLED=True

# Database
DATABASE_URL=postgresql://user:password@host:5432/maggxdnd

# Security
CORS_ALLOW_CREDENTIALS=True
```

---

## Security Best Practices

### 🔒 **Critical Security Rules**

1. **Never commit `.env` files to version control**
   - They are already in `.gitignore`
   - Use `.env.example` for documentation

2. **Change SECRET_KEY in production**
   ```bash
   # Generate a secure random key
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **Use HTTPS/WSS in production**
   - Update CORS_ORIGINS to use `https://`
   - WebSocket connections will automatically use `wss://`

4. **Enable rate limiting**
   - Prevents abuse and DoS attacks
   - Adjust limits based on your needs

5. **Restrict CORS origins**
   - Don't use `*` in production
   - List only trusted domains

6. **Use environment-specific databases**
   - Separate DB for dev/staging/production
   - Never use production DB in development

### 📝 **Example .env.example**

Create `.env.example` (safe to commit):

```bash
# Copy this to .env and fill in your values

# Required: Gemini API Key
GEMINI_API_KEY=your_api_key_here

# Security - CHANGE IN PRODUCTION!
SECRET_KEY=change-this-to-a-random-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS - Add your frontend URLs
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
CORS_ALLOW_CREDENTIALS=True

# Server
DEBUG=True
SERVER_HOST=127.0.0.1
SERVER_PORT=8000

# Database
DATABASE_URL=sqlite:///./maggxdnd.db

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_DEFAULT=100/minute
```

---

## Troubleshooting

### **CORS Errors**

If you see CORS errors in the browser console:

1. Check `CORS_ORIGINS` includes your frontend URL
2. Ensure the URL matches exactly (including port)
3. Restart the server after changing CORS settings

### **Rate Limit Errors (429)**

If you're hitting rate limits:

1. Check `RATE_LIMIT_ENABLED`
2. Adjust `RATE_LIMIT_DEFAULT` or specific limits
3. Consider increasing limits for development

### **Database Connection Errors**

1. Verify `DATABASE_URL` format
2. Check database file permissions
3. For PostgreSQL, ensure the database exists

### **WebSocket Connection Fails**

1. Check firewall settings
2. Verify `SERVER_HOST` and `SERVER_PORT`
3. In production, ensure WSS is configured

---

## Quick Start

### **Development Setup**

```bash
# 1. Copy example env file
cp .env.example .env

# 2. Edit .env with your values
# Add your GEMINI_API_KEY at minimum

# 3. Start the server
cd C:\VS_Code\MAGGxDND
python start.py

# 4. Start the UI (in another terminal)
cd UI
npm run dev
```

### **Production Setup**

```bash
# 1. Set all production environment variables
# Use your deployment platform's environment variable settings

# 2. Generate secure SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. Set DEBUG=False

# 4. Configure production database

# 5. Set production CORS origins

# 6. Start server
uvicorn server.main:app --host 0.0.0.0 --port 8000
```

---

## Support

For issues or questions:
- Check the main [README.md](../README.md)
- Review [RUN_ON_8000.md](../RUN_ON_8000.md)
- Open an issue on the repository
