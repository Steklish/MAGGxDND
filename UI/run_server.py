"""
MAGGxDND Game Server Launcher
Запускает основной сервер с полной интеграцией игрового движка
"""

import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("MAGGxDND Game Server - Full Version")
print("=" * 60)
print()

# Check GEMINI_API_KEY
api_key = os.getenv("GEMINI_API_KEY", "NO_KEY")
if api_key == "NO_KEY":
    print("[WARN] GEMINI_API_KEY not set!")
    print("       AI generation will use default/no key.")
    print()
else:
    print("[OK] GEMINI_API_KEY found")
    print()

print("Starting server on http://localhost:8000")
print("API Docs: http://localhost:8000/docs")
print()
print("Press Ctrl+C to stop")
print("=" * 60)
print()

# Run with uvicorn - use main server from project root
if __name__ == "__main__":
    import uvicorn
    import subprocess
    
    # Change to project root for correct database path
    os.chdir(PROJECT_ROOT)
    print(f"Working directory: {os.getcwd()}")
    
    try:
        uvicorn.run(
            "server.main:app",  # Use main server
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)
