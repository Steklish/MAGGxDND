"""
MAGGxDND Full Stack Launcher
Starts the game server with full game engine integration
"""

import asyncio
import logging
import os
import sys

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from logging.handlers import RotatingFileHandler

# Setup logging
os.makedirs('log', exist_ok=True)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                             datefmt='%Y-%m-%d %H:%M:%S')

file_handler = RotatingFileHandler(
    './log/fullstack_server.log',
    maxBytes=10*1024*1024,
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

logger = logging.getLogger("launcher")


async def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("MAGGxDND Full Stack Server")
    logger.info("Game Engine + FastAPI + WebSocket + React UI")
    logger.info("=" * 60)
    
    # Import uvicorn
    import uvicorn
    
    # Run the FastAPI server with game engine integration
    logger.info("Starting FastAPI server on http://0.0.0.0:8000")
    logger.info("API Docs: http://localhost:8000/docs")
    logger.info("WebSocket: ws://localhost:8000/ws/{session_id}/{player_id}")
    
    # Set environment variable for game engine
    os.environ['MAGGXDND_SERVER_MODE'] = 'true'
    
    uvicorn.run(
        "server.main_with_engine:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
