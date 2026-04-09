# AI API Setup Guide

## Problem
The Google Gemini API is not configured, causing all AI-generated content (scenes, characters, NPCs) to fail and fall back to default templates.

**Error Message:**
```
400 User location is not supported for the API use.
```

## Solution

### Option 1: Set up Google Gemini API Key (Recommended)

1. **Get an API Key:**
   - Visit: https://makersuite.google.com/app/apikey
   - Sign in with your Google account
   - Click "Create API Key"
   - Copy the generated key

2. **Configure .env file:**
   ```bash
   # Open .env file in project root
   # Replace this line:
   GEMINI_API_KEY=your_gemini_api_key_here
   
   # With your actual key:
   GEMINI_API_KEY=AIzaSy...your_actual_key_here
   ```

3. **Restart the server:**
   ```bash
   # Stop current server (Ctrl+C or taskkill)
   python start.py
   ```

4. **Verify API key is loaded:**
   - Check server logs for: `Generator initialized with model: gemini-flash-latest`
   - No API errors should appear when starting a game session

### Option 2: Use Fallback Mode (No API Key Required)

The game now works **without** an API key using enhanced fallback data:

**Player Character (Fallback):**
- Name: Hero1
- Class: Fighter
- Race: Human
- Level: 1
- HP: 30/30
- AC: 12
- **Abilities:** Attack, Second Wind, Action Surge, Dodge
- **Inventory:** Longsword, Shield, Chain Mail, Rations, Health Potion
- **Stats:** STR 15, DEX 12, CON 14, INT 10, WIS 10, CHA 10

**NPC (Fallback):**
- Name: NPC1
- Role: Tavern Keeper
- Race: Human
- Level: 1
- HP: 20/20
- AC: 10
- **Abilities:** Help, Dodge
- **Inventory:** Dagger, Common Clothes, 10 gp

**Scene (Fallback):**
- Generated from your adventure wishes/prompt
- Uses default template if AI unavailable

## Testing

1. **Clear browser data:**
   - Open DevTools (F12)
   - Application → Storage → Clear site data
   - Or use Incognito mode

2. **Create new session:**
   - Click "Create Session"
   - Enter session name
   - Click "Create"

3. **Start game:**
   - Click "Ready" in waiting room
   - Click "Start Game"
   - Adventure wishes: "Create an exciting adventure..."

4. **Verify:**
   - ✅ Scene displays with name and description
   - ✅ Character panel shows Hero1 with full stats
   - ✅ Abilities tab shows 4 abilities
   - ✅ Inventory tab shows 5 items
   - ✅ NPC panel shows NPC1 (Tavern Keeper)

## Known Limitations (Fallback Mode)

- All players named "Hero1", "Hero2", etc.
- Generic appearance and backstory
- No AI-driven dynamic content generation
- NPC interactions are limited
- No procedural story generation

## Troubleshooting

### API Key Not Working

**Error:** `400 User location is not supported`
- **Cause:** Gemini API not available in your region
- **Solution:** Use VPN or fallback mode

**Error:** `403 API_KEY_INVALID`
- **Cause:** Wrong API key
- **Solution:** Regenerate key from Google AI Studio

**Error:** `429 Quota exceeded`
- **Cause:** Free tier limit reached
- **Solution:** Wait 24h or upgrade to paid tier

### Server Logs

Check logs for detailed errors:
```
C:\VS_Code\MAGGxDND\logs\api\api.log
C:\VS_Code\MAGGxDND\logs\game\game.log
C:\VS_Code\MAGGxDND\log\game_server.log
```

Look for:
- `Generator initialized` - API key loaded
- `Scene generated` - AI generation successful
- `using fallback` - AI failed, using defaults

## Environment Variables

Required for full AI features:
```env
GEMINI_API_KEY=AIzaSy...your_key
GEMINI_MODEL=gemini-flash-latest
AI_GEN_RETRIES=3
```

Optional:
```env
LLAMACPP_CHAT_BASE=http://localhost:8080  # Local LLM fallback
```

## Security Note

⚠️ **Never commit .env file to Git!**

The `.env` file is in `.gitignore` for security. API keys should be kept secret.

For production deployment, use environment variables or secrets manager.
