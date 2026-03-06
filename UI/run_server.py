"""
MAGGxDND Game Server Launcher
Запускает сервер с полной интеграцией игрового движка
"""

import sys
import os
import asyncio

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

# Import server app directly
# Run with uvicorn
if __name__ == "__main__":
    import uvicorn

    try:
        uvicorn.run(
            "server.main_with_engine:app",
            host="0.0.0.0",
            port=8000,
            reload=False,  # Disable reload for stability
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)
