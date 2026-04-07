from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from backend.src.api.routers import dev, login, user, access_group, oauth  # , compendium
from backend.src.api.routers.session_router import router as session_router
from backend.src.api.routers.websocket_game import router as websocket_router
from backend.src.api.routers import character, profile, character_profile
from backend.src.api.middleware import APILoggingMiddleware, SlowRequestMiddleware
from backend.src.config import settings
from backend.src.database import init_db, engine
from backend.src.logging import setup_logging, get_logger
import os
import sys
import logging

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8') # type: ignore

# Setup comprehensive logging
setup_logging(
    log_dir='./logs',
    console_level=logging.INFO,
    file_level=logging.DEBUG,
    enable_json_logs=True
)

# Completely disable uvicorn access logger (we use custom APILoggingMiddleware instead)
logging.getLogger("uvicorn.access").handlers = []
logging.getLogger("uvicorn.access").propagate = False
logging.getLogger("uvicorn.access").disabled = True

logger = get_logger('main')

app = FastAPI(
    title="MAGGxDND - AI-Powered D&D Game Engine",
    description="Real-time AI-powered D&D game engine with web interface",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
    enabled=settings.RATE_LIMIT_ENABLED,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler) # type: ignore

# This will be our sub-application to hold all the prefixed routes
sub_app = FastAPI()
sub_app.include_router(user.router)
sub_app.include_router(access_group.router)
sub_app.include_router(login.router)
sub_app.include_router(dev.router)
sub_app.include_router(session_router)
sub_app.include_router(character.router)
sub_app.include_router(character_profile.router)
sub_app.include_router(profile.router)
sub_app.include_router(oauth.router)
# sub_app.include_router(compendium.router)  # Temporarily disabled

# Apply rate limiting to auth endpoints
login.router.dependencies.insert(0, limiter.limit(settings.RATE_LIMIT_AUTH)) # type: ignore

app.mount("/api/v1", sub_app)

# Add logging middleware (verbose=False reduces console spam)
app.add_middleware(APILoggingMiddleware, log_request_body=True, log_response_body=False, verbose=False)
app.add_middleware(SlowRequestMiddleware, threshold_seconds=2.0)

# WebSocket router (не поддерживает префиксы, монтируем отдельно)
app.include_router(websocket_router)

# CORS Middleware - restricted origins from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Global exception handler for better error responses
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions gracefully."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__,
        }
    )

@app.on_event("startup")
async def on_startup():
    """Initialize application on startup."""
    logger.info("="*80)
    logger.info("MAGGxDND Server Starting")
    logger.info("="*80)
    
    # Validate settings in production
    if settings.is_production():
        try:
            settings.validate()
            logger.info("✓ Settings validated for production")
        except ValueError as e:
            logger.error(f"Settings validation failed: {e}")
            raise

    # Initialize the database tables
    init_db(engine)
    logger.info(f"✓ Database initialized: {settings.DATABASE_URL}")
    logger.info(f"✓ CORS origins configured: {settings.CORS_ORIGINS}")
    logger.info(f"✓ Rate limiting: {settings.RATE_LIMIT_ENABLED} ({settings.RATE_LIMIT_DEFAULT})")
    logger.info(f"✓ Server running on {settings.SERVER_HOST}:{settings.SERVER_PORT}")
    logger.info("="*80)


# ===================================================================
# HEALTH CHECK & MONITORING ENDPOINTS
# ===================================================================

@app.get("/health", tags=["Health"], summary="Health check endpoint")
async def health_check():
    """
    Basic health check endpoint.
    Returns 200 OK if the server is running.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": __import__("datetime").datetime.utcnow().isoformat()
    }


# Temporarily disabled due to import caching issue
# @app.get("/health/ready", tags=["Health"], summary="Readiness check endpoint")
# async def health_ready():
#     """
#     Readiness check endpoint.
#     Returns 200 OK if the server is ready to accept requests.
#     """
#     try:
#         # Check database connection - import directly from session module
#         from backend.src.database.session import get_db
#         db = next(get_db())
#         db.execute("SELECT 1")
#         db.close()
#         return {
#             "status": "ready",
#             "database": "connected",
#             "timestamp": __import__("datetime").datetime.utcnow().isoformat()
#         }
#     except Exception as e:
#         logger.error(f"Readiness check failed: {e}")
#         return JSONResponse(
#             status_code=503,
#             content={
#                 "status": "not ready",
#                 "database": "disconnected",
#                 "error": str(e),
#                 "timestamp": __import__("datetime").datetime.utcnow().isoformat()
#             }
#         )


@app.get("/health/live", tags=["Health"], summary="Liveness check endpoint")
async def health_live():
    """
    Liveness check endpoint.
    Returns 200 OK if the server is alive and responsive.
    """
    return {
        "status": "alive",
        "uptime": "running",
        "timestamp": __import__("datetime").datetime.utcnow().isoformat()
    }


# ===================================================================
# UI STATIC FILES SERVING
# ===================================================================

# Serve UI static files
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI_DIST_PATH = os.path.join(PROJECT_ROOT, "frontend", "dist")
UI_ARTS_PATH = os.path.join(PROJECT_ROOT, "frontend", "arts")
print(f"PROJECT_ROOT: {PROJECT_ROOT}")
print(f"UI_DIST_PATH: {UI_DIST_PATH}")
print(f"UI_DIST_PATH exists: {os.path.exists(UI_DIST_PATH)}")

@app.get("/favicon.ico")
async def serve_favicon():
    """Serve favicon from arts folder."""
    favicon_path = os.path.join(UI_ARTS_PATH, "icons", "app.png")
    if os.path.isfile(favicon_path):
        return FileResponse(favicon_path, media_type="image/png")
    # Fallback to dist version
    favicon_dist_path = os.path.join(UI_DIST_PATH, "arts", "icons", "app.png")
    if os.path.isfile(favicon_dist_path):
        return FileResponse(favicon_dist_path, media_type="image/png")
    return {"error": "Favicon not found"}

@app.get("/")
async def serve_ui_root():
    """Serve UI index.html"""
    index_path = os.path.join(UI_DIST_PATH, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return {"error": "UI not built. Run: npm run build"}

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