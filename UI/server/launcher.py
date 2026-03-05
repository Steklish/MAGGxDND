"""
MAGGxDND Game Server Launcher
Starts the FastAPI server and initializes the game engine
"""

import asyncio
import logging
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from logging.handlers import RotatingFileHandler

# Setup logging
os.makedirs('log', exist_ok=True)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                             datefmt='%Y-%m-%d %H:%M:%S')

file_handler = RotatingFileHandler(
    './log/game_server.log',
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
    logger.info("MAGGxDND Game Server Launcher")
    logger.info("=" * 60)
    
    # Import uvicorn
    import uvicorn
    
    # Run the FastAPI server
    logger.info("Starting FastAPI server on http://0.0.0.0:8000")
    
    uvicorn.run(
        "server.main:app",
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
