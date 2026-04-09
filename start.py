"""
MAGGxDND Unified Server Launcher
Starts FastAPI server with game engine integration
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Load .env file
load_dotenv(override=True)

# Set UTF-8 encoding for Windows
if os.name == 'nt':
    os.system('chcp 65001 >nul')
sys.stdout.reconfigure(encoding='utf-8') # type: ignore

logger = logging.getLogger(__name__)

logger.info("=" * 60)
logger.info("MAGGxDND Server")
logger.info("=" * 60)

# Change to project root directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Setup logging
os.makedirs('log', exist_ok=True)
log_file = os.path.join('log', 'game_server.log')

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

file_handler = RotatingFileHandler(
    log_file,
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

# Check API key
api_key = os.getenv("GEMINI_API_KEY", "NO_KEY")
if api_key == "NO_KEY":
    logger.warning("GEMINI_API_KEY not set! AI features will not work. Set: set GEMINI_API_KEY=your_key")

logger.info(f"Project Root: {os.getcwd()}")
logger.info(f"Log File: {log_file}")
logger.info("Starting server on http://localhost:8000")
logger.info("API Docs: http://localhost:8000/docs")
logger.info("Press Ctrl+C to stop")
logger.info("=" * 60)

# Import and run uvicorn
try:
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
except ImportError:
    logger.error("uvicorn not installed! Run: pip install uvicorn")
    sys.exit(1)
except KeyboardInterrupt:
    logger.info("Server stopped by user")
