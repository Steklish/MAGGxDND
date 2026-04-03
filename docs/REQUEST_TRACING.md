# 🔍 Request Tracing & Logging System

MAGGxDND now includes comprehensive request tracing that logs the full journey of each request from frontend to backend and back.

## 📊 What Gets Logged

### Frontend (Browser Console)

Every API request from the frontend is logged with:
- **📤 Outgoing Request**
  - Trace ID (unique identifier for tracking)
  - HTTP Method & Endpoint
  - Request headers (with masked auth tokens)
  - Request body/data
  - Timestamp

- **📥 Incoming Response**
  - Trace ID (matching the request)
  - Status code
  - Response time (duration)
  - Response data
  - Headers

- **❌ Errors**
  - Network errors
  - HTTP errors (4xx, 5xx)
  - Detailed error information

### Backend (Server Console)

Every API request received by the backend is logged with:
- **📥 Incoming Request**
  - Trace ID (from frontend if available)
  - Request ID (internal backend ID)
  - HTTP Method & Path
  - Client IP address
  - User information (if authenticated)
  - Query parameters
  - Request body (for POST/PUT/PATCH)

- **🔄 Processing**
  - Entry into route handlers
  - Database operations
  - Core engine interactions
  - Service layer calls

- **📤 Outgoing Response**
  - Trace ID
  - Status code
  - Processing time
  - Success/Error status

- **❌ Exceptions**
  - Full error details
  - Error type
  - Stack trace
  - Processing time until error

## 🎨 Visual Format

### Frontend Console (Browser)

```
╔═══════════════════════════════════════════════════════════╗
║ 📤 [14:30:45] REQUEST → POST /api/v1/sessions            ║
║   Trace ID: abc12345                                      ║
║   Base URL: /api/v1                                       ║
║   Method: POST                                            ║
║   URL: /sessions                                          ║
║   Request Body: {"session_name": "My Game", ...}         ║
║   Headers: {"X-Trace-ID": "abc12345", ...}               ║
╚═══════════════════════════════════════════════════════════╝
─────────────────────────────────────────────────────

╔═══════════════════════════════════════════════════════════╗
║ 📥 [14:30:46] RESPONSE ← 201 POST /api/v1/sessions       ║
║   Trace ID: abc12345                                      ║
║   Status: 201 Created                                     ║
║   Duration: 245ms                                         ║
║   Response Data: {"session_id": "...", ...}              ║
╚═══════════════════════════════════════════════════════════╝
─────────────────────────────────────────────────────
```

### Backend Console (Server)

```
┌──────────────────────────────────────────────────────────────┐
│ 📥 INCOMING REQUEST                                          │
│    Trace ID: abc12345                                        │
│    Request ID: api_20260327_143045_0                         │
│    Method: POST                                              │
│    Path: /api/v1/sessions                                    │
│    Client: 127.0.0.1                                         │
│    User: {'id': 1, 'username': 'testuser'}                  │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ 🚀 ENTERING: create_session                                  │
│   Trace ID: abc12345                                         │
│   Session UUID: 550e8400-e29b-41d4-a716-446655440000        │
│   User ID: 1                                                 │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ 📤 OUTGOING RESPONSE                                         │
│    Trace ID: abc12345                                        │
│    Request ID: api_20260327_143045_0                         │
│    Status: ✅ 201                                            │
│    Method: POST                                              │
│    Path: /api/v1/sessions                                    │
│    Processing Time: 245.32ms                                 │
└──────────────────────────────────────────────────────────────┘
```

## 🔧 How It Works

### 1. Frontend Request Interceptor

When a request is made from the frontend:
1. A unique **Trace ID** is generated (or reused from sessionStorage)
2. The Trace ID is added to request headers as `X-Trace-ID`
3. Request details are logged to browser console
4. Start time is recorded for duration calculation

### 2. Backend Middleware

When the backend receives a request:
1. Trace ID is extracted from headers (if present)
2. Request details are logged with Trace ID
3. Request is processed normally
4. Trace ID is added to response headers
5. Response details are logged with processing time

### 3. Backend Route Handlers

In route handlers (e.g., `create_session`):
1. Entry is logged with Trace ID and parameters
2. Key operations are logged (DB calls, engine calls, etc.)
3. Exit is logged with success/error status

### 4. Frontend Response Handler

When the response returns to frontend:
1. Trace ID is extracted from response headers
2. Duration is calculated
3. Response details are logged
4. Visual formatting shows success (green) or error (red)

## 📁 Files Modified

### Frontend
- `frontend/src/services/api.ts`
  - Added request/response interceptors with logging
  - Trace ID generation and management
  - Visual console formatting with colors

### Backend
- `backend/src/logging/request_tracing.py` (NEW)
  - RequestTracer class
  - Trace ID context management
  - FrontendRequestLogger utility

- `backend/src/api/middleware/logging.py`
  - Enhanced with Trace ID support
  - Color-coded console output
  - Request/Response boxing

- `backend/src/api/routers/session_router.py`
  - Example implementation in `create_session`
  - Entry/Exit logging with Trace ID

## 🚀 Usage

### For Developers

#### Frontend (TypeScript)

```typescript
// Logging is automatic via axios interceptors
// Just make normal API calls:

const response = await api.post('/sessions', {
    session_name: 'My Game',
    game_mode: 'STORY'
});

// Check browser console for detailed logs
```

#### Backend (Python)

```python
from backend.src.logging.request_tracing import get_trace_id, RequestTracer
from backend.src.api.middleware.logging import Colors

@router.post("/example")
async def example_endpoint():
    trace_id = get_trace_id()
    
    # Log entry
    print(f"{Colors.MAGENTA}🚀 ENTERING: example_endpoint{Colors.RESET}")
    print(f"{Colors.MAGENTA}   Trace ID: {trace_id}{Colors.RESET}")
    
    # Use RequestTracer context manager
    with RequestTracer("database_operation", {"query": "SELECT *"}):
        # Your code here
        pass
    
    # Log exit
    print(f"{Colors.GREEN}✅ EXITING: example_endpoint{Colors.RESET}")
```

### For Debugging

1. **Open Browser DevTools** (F12)
2. **Go to Console tab**
3. **Make a request** from the frontend
4. **Look for colored log boxes**:
   - Blue: Outgoing requests
   - Green: Successful responses
   - Red: Errors
5. **Note the Trace ID**
6. **Check server console** for matching Trace ID
7. **Follow the request** through the entire system

## 🎯 Benefits

- **End-to-End Visibility**: Track requests from frontend to backend and back
- **Easy Debugging**: Match frontend requests with backend logs using Trace ID
- **Performance Monitoring**: See request/response times
- **Error Tracking**: Quickly identify where errors occur
- **Audit Trail**: Complete log of all API interactions

## 📊 Example Trace Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER ACTION                             │
│              (e.g., "Create Session" button click)              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Browser)                           │
│  📤 REQUEST: POST /api/v1/sessions                              │
│     Trace ID: abc123                                            │
│     Data: {"session_name": "My Game"}                          │
└─────────────────────────────────────────────────────────────────┘
                            ↓ (HTTP)
┌─────────────────────────────────────────────────────────────────┐
│                 BACKEND (FastAPI Server)                        │
│  📥 INCOMING: POST /api/v1/sessions                             │
│     Trace ID: abc123                                            │
│     ↓                                                           │
│  🚀 ENTER: create_session                                       │
│     ↓                                                           │
│  💾 DATABASE: Create session record                             │
│     ↓                                                           │
│  ⚙️  ENGINE: Create game session                                │
│     ↓                                                           │
│  📤 RESPONSE: 201 Created                                       │
│     Trace ID: abc123                                            │
└─────────────────────────────────────────────────────────────────┘
                            ↓ (HTTP)
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Browser)                           │
│  📥 RESPONSE: 201 Created                                       │
│     Trace ID: abc123                                            │
│     Duration: 245ms                                             │
│     Data: {"session_id": "..."}                                │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                       UI UPDATE                                 │
│            (Navigate to session, show success)                  │
└─────────────────────────────────────────────────────────────────┘
```

## 🔒 Security Notes

- **Auth tokens are masked** in logs (shows "Bearer ***" only)
- **Sensitive headers excluded** from logging
- **Trace IDs are random** and non-guessable
- **Logs are client-side only** (browser console) unless server logging is enabled

## 📝 Best Practices

1. **Always check Trace ID** when debugging - it's the common thread
2. **Use console grouping** - logs are grouped for easier reading
3. **Filter by Trace ID** to follow specific requests
4. **Monitor processing times** - look for slow operations
5. **Check both frontend and backend** - full picture requires both

## 🐛 Troubleshooting

### No logs appearing in browser console?
- Make sure DevTools is open (F12)
- Check console filter settings
- Look for collapsed groups (click to expand)

### Trace ID not matching?
- Trace ID is generated per-page-load by default
- Check that `X-Trace-ID` header is being sent
- Verify backend is extracting the header

### Backend logs not showing?
- Check logging configuration
- Ensure middleware is registered
- Verify log level settings

## 📚 Related Documentation

- [API Documentation](./API.md)
- [Logging Configuration](./LOGGING.md)
- [Debugging Guide](./DEBUGGING.md)
