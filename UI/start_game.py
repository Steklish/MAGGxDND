"""
Simple launcher for MAGGxDND Full Stack
Starts server with game engine
"""

import sys
import os

# Set UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("MAGGxDND Full Stack Launcher")
print("=" * 60)
print()

# Check GEMINI_API_KEY
api_key = os.getenv("GEMINI_API_KEY", "NO_KEY")
if api_key == "NO_KEY":
    print("[WARN] GEMINI_API_KEY not set!")
    print("       AI features may not work.")
    print("       Set: set GEMINI_API_KEY=your_key")
    print()

print("Starting server with game engine...")
print()

# Import and run
import uvicorn

uvicorn.run(
    "server.main_with_engine:app",
    host="0.0.0.0",
    port=8000,
    reload=False,
    log_level="info"
)
