"""
MAGGxDND Unified Server Launcher
Starts FastAPI server with game engine integration
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler

# Set UTF-8 encoding for Windows
if os.name == 'nt':
    os.system('chcp 65001 >nul')
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("MAGGxDND Server")
print("=" * 60)

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
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# Check API key
api_key = os.getenv("GEMINI_API_KEY", "NO_KEY")
if api_key == "NO_KEY":
    print("[WARN] GEMINI_API_KEY not set!")
    print("       AI features will not work.")
    print("       Set: set GEMINI_API_KEY=your_key")
    print()

print(f"Project Root: {os.getcwd()}")
print(f"Log File: {log_file}")
print()
print("Starting server on http://localhost:8000")
print("API Docs: http://localhost:8000/docs")
print()
print("Press Ctrl+C to stop")
print("=" * 60)

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
    print("[ERROR] uvicorn not installed!")
    print("        Run: pip install uvicorn")
    sys.exit(1)
except KeyboardInterrupt:
    print("\nServer stopped by user")
