# 🚀 Request Journey Logging System

## Overview

This system provides **comprehensive console logging** for all communication between the frontend and backend, tracking the complete journey of every request through all layers of the application.

## Journey Stages

Every request follows this path:

```
┌──────────────────────────────────────────────────────────────────┐
│                    REQUEST JOURNEY (5 STAGES)                     │
├──────────────────────────────────────────────────────────────────┤
│ Stage 1/5: Frontend → Backend API                                │
│ Stage 2/5: Backend → WebSocket → Core Engine                     │
│ Stage 3/5: Core Engine → EventPool                               │
│ Stage 4/5: Core Engine → EventPool → WebSocket                   │
│ Stage 5/5: WebSocket → Frontend (COMPLETE)                       │
└──────────────────────────────────────────────────────────────────┘
```

## Features

### ✅ End-to-End Trace ID Tracking

- Each request gets a unique **Trace ID**
- Trace ID follows the request through all layers
- Easy to correlate frontend and backend logs

### ✅ Visual Console Output

- Color-coded log messages
- Boxed format for easy reading
- Stage indicators (1/5, 2/5, etc.)
- Journey path visualization

### ✅ Timing Information

- Request duration
- Total journey time
- Per-stage timing

### ✅ Error Tracking

- Clear error visualization
- Stage where error occurred
- Full error details

---

## Frontend Logs (Browser Console)

### Outgoing Request (Stage 1/5)

```
╔═══════════════════════════════════════════════════════════╗
║ 🚀 JOURNEY START: POST /api/v1/sessions                  ║
╠═══════════════════════════════════════════════════════════╣
║ Trace ID: trace_abc123_xyz                               ║
║ Time: 14:30:45                                           ║
║ Description: Initiating request from frontend to backend ║
╠═══════════════════════════════════════════════════════════╣
║ Stage 1/5: Frontend → Backend API                        ║
╚═══════════════════════════════════════════════════════════╝

┌───────────────────────────────────────────────────────────┐
│ Stage 1/5: Frontend → Backend API                        │
├───────────────────────────────────────────────────────────┤
│ Request prepared and sending                             │
│ Data: {"session_name": "test"}                          │
└───────────────────────────────────────────────────────────┘
```

### Incoming Response (Stage 5/5)

```
┌───────────────────────────────────────────────────────────┐
│ Stage 5/5: Response → Frontend                           │
├───────────────────────────────────────────────────────────┤
│ Response received (200)                                  │
│ Data: {"session_id": "123"}                             │
└───────────────────────────────────────────────────────────┘

╔═══════════════════════════════════════════════════════════╗
║ ✅ JOURNEY COMPLETE: POST /api/v1/sessions               ║
╠═══════════════════════════════════════════════════════════╣
║ Trace ID: trace_abc123_xyz                               ║
║ Total Duration: 245ms                                    ║
║ Time: 14:30:45                                           ║
╠═══════════════════════════════════════════════════════════╣
║ ✓ Frontend → Backend API                                 ║
║ ✓ Backend API → Core Engine                              ║
║ ✓ Core Engine Processing                                 ║
║ ✓ Core Engine → Event Pool → WebSocket                   ║
║ ✓ WebSocket → Frontend                                   ║
╚═══════════════════════════════════════════════════════════╝
```

### WebSocket Player Action

```
╔═══════════════════════════════════════════════════════════╗
║ 🚀 JOURNEY START: PLAYER_ACTION: Wizard                  ║
╠═══════════════════════════════════════════════════════════╣
║ Trace ID: trace_def456_abc                               ║
║ Time: 14:31:00                                           ║
║ Description: Player action: Cast fireball spell...       ║
╠═══════════════════════════════════════════════════════════╣
║ Stage 1/5: Frontend → WebSocket                          ║
╚═══════════════════════════════════════════════════════════╝
```

---

## Backend Logs (Server Console)

### Incoming API Request (Stage 1/5)

```
┌──────────────────────────────────────────────────────────────────┐
│ 🚀 REQUEST JOURNEY START                                         │
├──────────────────────────────────────────────────────────────────┤
│    Trace ID: trace_abc123_xyz                                    │
│    Request ID: api_20260329_143045_0                             │
│    Method: POST                                                  │
│    Path: /api/v1/sessions                                        │
│    Client: 127.0.0.1                                             │
│    Journey: Frontend → Backend API (START)                       │
│    Stage: 1/5                                                    │
└──────────────────────────────────────────────────────────────────┘
```

### WebSocket Message Received (Stage 2/5)

```
┌──────────────────────────────────────────────────────────────────┐
│ 📥 WS MESSAGE RECEIVED: STAGE 2/5                                │
├──────────────────────────────────────────────────────────────────┤
│    Timestamp: 14:31:00                                           │
│    Session: session_123                                          │
│    Player: player_456                                            │
│    Event Type: PLAYER_ACTION                                     │
│    Journey Stage: Frontend → WebSocket → Backend                 │
│    Next: Backend → Core Engine                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Core Engine Processing (Stage 3/5)

```
┌──────────────────────────────────────────────────────────────────┐
│ ⚙️  CORE ENGINE PROCESSING: STAGE 3/5                            │
├──────────────────────────────────────────────────────────────────┤
│    Session: session_123                                          │
│    Event Type: PLAYER_ACTION                                     │
│    Source: player_456                                            │
│    Journey Stage: Backend → Core Engine → EventPool              │
│    Next: EventPool → WebSocket                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Event Pool → WebSocket (Stage 4/5)

```
┌──────────────────────────────────────────────────────────────────┐
│ 📤 EVENT JOURNEY: STAGE 4/5                                      │
├──────────────────────────────────────────────────────────────────┤
│    Timestamp: 14:31:01                                           │
│    Session: session_123                                          │
│    Player: player_456                                            │
│    Event Type: ACTION_RESULT                                     │
│    Event Count: #1                                               │
│    Journey Stage: Core Engine → EventPool → WebSocket            │
│    Next: WebSocket → Frontend                                    │
└──────────────────────────────────────────────────────────────────┘
```

### Response Complete (Stage 5/5)

```
┌──────────────────────────────────────────────────────────────────┐
│ ✅ REQUEST JOURNEY COMPLETE                                      │
├──────────────────────────────────────────────────────────────────┤
│    Trace ID: trace_abc123_xyz                                    │
│    Request ID: api_20260329_143045_0                             │
│    Status: ✅ 200                                                │
│    Method: POST                                                  │
│    Path: /api/v1/sessions                                        │
│    Processing Time: 234.56ms                                     │
│    Total Journey Time: 245.12ms                                  │
│    Journey Path: Frontend → Backend API → Core Engine → ...      │
│    Journey: Backend → Frontend (COMPLETE)                        │
│    Stage: 5/5                                                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Files Modified

### Frontend (TypeScript)

| File | Changes |
|------|---------|
| `frontend/src/utils/requestLogger.ts` | Added journey tracking functions: `logJourneyStart`, `logJourneyStage`, `logJourneyComplete` |
| `frontend/src/services/api.ts` | Added journey logging to API interceptors |
| `frontend/src/services/websocket.ts` | Added journey logging for player actions |

### Backend (Python)

| File | Changes |
|------|---------|
| `backend/src/api/middleware/logging.py` | Enhanced with journey stage tracking |
| `backend/src/api/routers/websocket_game.py` | Added journey logging for WebSocket messages |
| `backend/src/game/session_manager.py` | Added journey logging for event broadcasting |
| `backend/src/services/ai_game_service.py` | Enhanced core engine logging with journey stages |

---

## Color Legend

| Color | Meaning |
|-------|---------|
| 🔵 Blue | Outgoing requests (Frontend → Backend) |
| 🟢 Green | Incoming responses / Success |
| 🔴 Red | Errors |
| 🟡 Yellow | Data payloads |
| 🟣 Purple | Core engine processing |
| 🔷 Cyan | Info / Metadata |

---

## Usage Example

### 1. Player Makes a Request

```typescript
// Frontend: Character panel sends action
const response = await api.post('/sessions/123/action', {
    character_name: 'Wizard',
    action: 'Cast fireball'
});
```

**Console Output:**
- Journey Start box (Stage 1/5)
- Request details
- Response received (Stage 5/5)
- Journey Complete box with all stages

### 2. Player Joins via WebSocket

```typescript
// Frontend: Connect to game session
await webSocketService.connect(sessionId, playerId, handleMessage);

// Send action
webSocketService.sendAction('Cast fireball', character);
```

**Console Output:**
- WebSocket connection logs
- Journey Start for player action
- All intermediate stages
- Journey Complete when result arrives

---

## Benefits

1. **Easy Debugging**: See exactly where requests fail
2. **Performance Analysis**: Identify slow stages
3. **Request Correlation**: Match frontend requests with backend processing
4. **Learning Tool**: Understand the application architecture
5. **Production Monitoring**: Detailed logs for troubleshooting

---

## Disabling Logs

To reduce log verbosity in production:

### Frontend
```typescript
// Set environment variable
process.env.NODE_ENV = 'production';
```

### Backend
```python
# Adjust logging level in settings
LOG_LEVEL = 'WARNING'
```

---

## Future Enhancements

- [ ] Add log aggregation service integration
- [ ] Export journey logs to file
- [ ] Add performance metrics dashboard
- [ ] Integrate with distributed tracing systems (Jaeger, Zipkin)

---

## Support

For issues or questions about the logging system, check:
- `frontend/src/utils/requestLogger.ts` - Frontend logging utilities
- `backend/src/logging/request_tracing.py` - Backend trace ID system
- `backend/src/api/middleware/logging.py` - API request logging

---

**Last Updated:** 2026-03-29  
**Author:** MAGGxDND Team
