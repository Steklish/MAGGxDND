# Frontend-Server Communication Quick Reference

## 📊 Summary

| Category | Count | Details |
|---|---|---|
| **Server → Client WebSocket** | 14 types | See section below |
| **Client → Server WebSocket** | 4 types | 2 actively used, 2 unused |
| **Core Game Events** | 22 types | EventTypes enum |
| **REST API Types** | 20+ interfaces | Sessions, Characters, etc. |

---

## 📨 Server → Client WebSocket Messages

| Type | Purpose | Status |
|---|---|---|
| `CONNECTED` | Connection confirmation | ✅ Active |
| `MASTER_MESSAGE` | DM/AI narration | ✅ Active |
| `SESSION_UPDATE` | Full session state | ✅ Active |
| `TURN_UPDATE` | Current turn notification | ✅ Active |
| `TURN_QUEUE_UPDATE` | Full turn queue | ✅ Active |
| `GAME_EVENT` | Game mechanics events | ✅ Active |
| `ERROR` | Error notifications | ✅ Active |
| `PONG` | Heartbeat response | ✅ Active |
| `ACTION_CONFIRMED` | Action acknowledgment | ✅ Active |
| `ACTION_RESULT` | Action processing result | ⚠️ REST fallback |
| `PLAYER_REQUEST` | Player input request | ⚠️ Not handled in frontend |
| `ACTION_REQUEST` | Character action prompt | ⚠️ Not sent by backend |
| `SCENE_UPDATE` | Scene change | ⚠️ Not emitted by backend |
| `CHARACTER_STATUS_UPDATE` | Status change | ✅ Handled |

---

## 📤 Client → Server WebSocket Messages

| Type | Purpose | Status |
|---|---|---|
| `PLAYER_ACTION` | Submit player action | ✅ Active |
| `PING` | Keepalive heartbeat | ✅ Active |
| `CHOOSE_PLAYER` | Select player | ❌ Type only, never sent |
| `SUBSCRIBE_EVENTS` | Event subscription | ❌ Type only, never sent |

---

## 🎮 Core Game Event Types (22 total)

**Combat:**
- `CHARACTER_MELEE_ATTACK`
- `CHARACTER_RANGED_ATTACK`

**Movement:**
- `CHARACTER_MOVEMENT`
- `CHARACTER_POSITION_UPDATE`
- `CHARACTER_TRANSFER`

**Items:**
- `ITEM_PICKUP`
- `ITEM_DROP`
- `ITEM_TRANSFER`
- `ITEM_MOVEMENT`
- `ITEM_INTERACTION`
- `ITEM_MUTATION`
- `OBJECT_TRANSFER`
- `CONTAINER_ACCESS`
- `CONTAINER_TRANSFER`

**Character State:**
- `CHARACTER_STATUS_CHANGE`
- `CHARACTER_DEATH`
- `CHARACTER_STATS_UPDATE`

**Locations:**
- `LOCATION_CHANGE`
- `LOCATION_MUTATION`
- `LOCATION_STATUS_CHANGE`

**Other:**
- `ACTION_RESULT`
- `SYSTEM`

---

## ⚠️ Known Issues

1. **PLAYER_REQUEST** - Backend sends, frontend doesn't handle
2. **ACTION_REQUEST** - Frontend handles, backend never sends
3. **SCENE_UPDATE** - Frontend handles, backend never emits via WebSocket
4. **CHOOSE_PLAYER** - Type defined but never used
5. **SUBSCRIBE_EVENTS** - Type defined but never used

---

## 📁 Key Files

### Frontend
- `frontend/src/services/websocket.ts` - WebSocket handling
- `frontend/src/store/gameStore.ts` - Store & message handling
- `frontend/src/types/game.ts` - Type definitions

### Backend
- `backend/src/api/routers/websocket_game.py` - WebSocket router
- `backend/src/delivery/game_delivery.py` - Delivery methods
- `core/schemas/orchestration.py` - EventTypes enum

---

## 🔗 Full Documentation

See `docs/frontend-server-communication.md` for complete documentation with:
- Detailed type definitions
- Message handling flows
- Usage examples
- Manipulator mappings
- All file references
