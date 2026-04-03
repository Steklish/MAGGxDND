import uvicorn
import sys

print("Starting server...")
sys.stdout.flush()

try:
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
