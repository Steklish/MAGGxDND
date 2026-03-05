@echo off
REM MAGGxDND Full Stack Launcher for Windows
REM Запускает сервер + игровой движок + game loop

echo ============================================================
echo MAGGxDND Full Stack Launcher
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.10+
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found! Please install Node.js
    pause
    exit /b 1
)

echo Starting MAGGxDND Full Stack...
echo.
echo Components:
echo   - FastAPI Server (port 8000)
echo   - Game Engine with AI
echo   - React UI
echo.
echo Press Ctrl+C to stop
echo ============================================================
echo.

REM Start the fullstack runner
cd /d "%~dp0"
python server\run_fullstack.py

pause
