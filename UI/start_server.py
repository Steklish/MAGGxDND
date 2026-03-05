# Start MAGGxDND Game Server
# This script starts the FastAPI backend server

import os
import sys
import subprocess

def main():
    print("=" * 60)
    print("MAGGxDND Game Server")
    print("=" * 60)
    
    # Change to UI directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Run uvicorn
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "server.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Server error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nServer stopped by user")

if __name__ == "__main__":
    main()
