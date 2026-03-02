from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from server.src.api.routers import dev, login, user, access_group
from server.src.api.routers.session_router import router as session_router
from server.src.api.routers.websocket_game import router as websocket_router

from server.src.database import init_db, engine
import os

app = FastAPI(title="MAGGxDND - AI-Powered D&D Game Engine")

# This will be our sub-application to hold all the prefixed routes
sub_app = FastAPI()
sub_app.include_router(user.router)
sub_app.include_router(access_group.router)
sub_app.include_router(login.router)
sub_app.include_router(dev.router)
sub_app.include_router(session_router)


app.mount("/api/v1", sub_app)

# WebSocket router (не поддерживает префиксы, монтируем отдельно)
app.include_router(websocket_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://localhost:3001", "http://localhost:8080", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    # Initialize the database tables
    init_db(engine)


# Serve UI static files
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI_DIST_PATH = os.path.join(PROJECT_ROOT, "UI", "dist")
print(f"PROJECT_ROOT: {PROJECT_ROOT}")
print(f"UI_DIST_PATH: {UI_DIST_PATH}")
print(f"UI_DIST_PATH exists: {os.path.exists(UI_DIST_PATH)}")

@app.get("/")
async def serve_ui_root():
    """Serve UI index.html"""
    index_path = os.path.join(UI_DIST_PATH, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return {"error": "UI not built. Run: cd UI && npm run build"}

@app.get("/{full_path:path}")
async def serve_ui(full_path: str):
    """Serve UI files for all non-API routes."""
    # Skip API and docs routes
    if full_path.startswith("api/") or full_path in ["docs", "redoc", "openapi.json"]:
        return None
    
    # Build file path
    file_path = os.path.join(UI_DIST_PATH, full_path)
    
    # Check if file exists, otherwise serve index.html (for SPA routing)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # Serve index.html for SPA routes
    index_path = os.path.join(UI_DIST_PATH, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    
    return {"error": "File not found"}