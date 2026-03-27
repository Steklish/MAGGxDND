# Quick Test Guide

## Server Status
- ✅ Server running on http://localhost:8000
- ✅ API Docs: http://localhost:8000/docs
- ✅ Health: http://localhost:8000/health

## Testing Steps

### 1. Open Application
```
http://localhost:8000
```

### 2. Login/Register
- Use existing account or create new one
- Guest login available for quick testing

### 3. Create Session
1. Click "New Session"
2. Enter session name
3. Click "Create"

### 4. Waiting Room
1. Click "Ready" when ready
2. Wait for other players (or test solo)
3. Owner clicks "Start Game"

### 5. Game Interface
**Expected results:**
- ✅ Scene displayed with name and description
- ✅ Player character shown with stats (HP, AC, abilities)
- ✅ 2 NPCs listed in character panel
- ✅ Turn queue shows active characters
- ✅ Chat panel has DM welcome message

### 6. Verify Data
Open browser console (F12) and check for:
```
📦 Game info loaded: {players: [...], npcs: [...], current_scene: {...}}
🎭 Players loaded: 1
🎭 NPCs loaded: 2
🏰 Scene: The Whispering Cairns (or similar)
```

## Troubleshooting

### No Characters Generated
**Check logs:**
```powershell
Get-Content log\game_server.log -Tail 50
```

**Look for:**
- `[START] ✓ Character ... added to session`
- `[START] ✓ Procedural character generated`

### No NPCs Generated
**Check for:**
- `[START] ✓ Procedural NPC generated`
- `[START] === Session initialized: X players, Y NPCs ===`

### AI Generation Fails
This is normal if:
- No GEMINI_API_KEY set
- API not available in your region

**Solution:** Procedural generation should auto-fallback

## Console Commands for Testing

### Check Server Health
```powershell
Invoke-WebRequest -Uri 'http://localhost:8000/health' -UseBasicParsing
```

### View Latest Logs
```powershell
Get-Content log\game_server.log -Tail 30
```

### Check Active Sessions
```powershell
Get-ChildItem log\*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 5
```

## Expected Character Stats
A procedurally generated character should have:
- **Name**: Random (e.g., "Aldric Stormwind")
- **Class**: FIGHTER, WIZARD, ROGUE, or CLERIC
- **Level**: 1
- **HP**: 20-30 (varies by class)
- **AC**: 10-16 (varies by armor)
- **Stats**: 8-16 in each ability
- **Abilities**: 2-3 class-specific abilities
- **Inventory**: 4-5 items

## Expected NPCs
Should generate 2 NPCs:
- **Mysterious Stranger**: Has important information
- **Local Merchant**: Shopkeeper or trader

Each NPC has:
- Name and occupation
- Basic stats
- Simple inventory
- Motivation trait

## Success Criteria
✅ All tests pass if:
1. Scene displays with description
2. Player character has full stats
3. At least 2 NPCs present
4. No console errors
5. Turn queue populated

## Known Issues
- AI generation may fail without valid API key (procedural fallback works)
- Some graphics may be missing (placeholder assets)
- WebSocket may need page refresh to connect
