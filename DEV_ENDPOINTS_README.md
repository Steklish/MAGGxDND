# Developer Endpoints

Quick access to all sessions and their data for debugging and monitoring.

## Quick Start

1. **Start the server:**
   ```bash
   python start.py
   ```

2. **Access the endpoints (no auth required!):**
   - All sessions: `http://localhost:8000/api/v1/test/sessions`
   - Summary: `http://localhost:8000/api/v1/test/summary`
   - Interactive docs: `http://localhost:8000/docs`

3. **⚠️ Development only** - These endpoints should not be exposed in production

## Available Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/test/sessions` | List all active sessions |
| `GET /api/v1/test/sessions/{id}` | Full session details |
| `GET /api/v1/test/sessions/{id}/players` | Session players |
| `GET /api/v1/test/sessions/{id}/npcs` | Session NPCs |
| `GET /api/v1/test/sessions/{id}/scene` | Current scene |
| `GET /api/v1/test/sessions/{id}/messages` | Message history |
| `GET /api/v1/test/sessions/{id}/turn-queue` | Turn queue |
| `GET /api/v1/test/sessions/{id}/full-state` | Complete state |
| `GET /api/v1/test/sessions/{id}/event-pool` | Event pool stats |
| `GET /api/v1/test/summary` | All sessions summary |

## Testing

Run the test script while the server is running:

```bash
python test_dev_endpoints.py
```

## Documentation

See `docs/dev-endpoints.md` for full documentation with examples.
