@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ╔═══════════════════════════════════════════════════════════╗
echo ║          MAGGxDND - Full Test Suite Runner               ║
echo ║                   with Coverage Report                   ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM Save current directory
set "PROJECT_ROOT=%CD%"

REM Counters
set "TOTAL_TESTS=0"
set "PASSED_TESTS=0"
set "FAILED_TESTS=0"

REM ==================== BACKEND TESTS ====================
echo ═══════════════════════════════════════════════════════
echo 🐍 BACKEND TESTS (Pytest)
echo ═══════════════════════════════════════════════════════
echo.

cd /d "%PROJECT_ROOT%"

REM Check if pytest is installed
where pytest >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ❌ pytest not found! Installing...
    pip install pytest pytest-asyncio pytest-cov httpx
)

REM Run backend tests with coverage
echo Running backend tests with coverage...
echo.
pytest backend/tests/ ^
    --cov=backend.src ^
    --cov-report=term-missing ^
    --cov-report=html:backend/htmlcov ^
    --cov-report=xml:backend/coverage.xml ^
    -v ^
    --tb=short

if %ERRORLEVEL% equ 0 (
    echo.
    echo ✅ Backend tests PASSED
    set /a PASSED_TESTS+=1
) else (
    echo.
    echo ❌ Backend tests FAILED
    set /a FAILED_TESTS+=1
)
set /a TOTAL_TESTS+=1

echo.
echo 📊 Backend Coverage Report:
echo    HTML: %PROJECT_ROOT%\backend\htmlcov\index.html
echo    XML:  %PROJECT_ROOT%\backend\coverage.xml
echo.

REM ==================== FRONTEND TESTS ====================
echo ═══════════════════════════════════════════════════════
echo ⚛️  FRONTEND TESTS (Vitest)
echo ═══════════════════════════════════════════════════════
echo.

cd /d "%PROJECT_ROOT%\frontend"

REM Check if node_modules exists
if not exist "node_modules" (
    echo ⚠️  node_modules not found! Installing dependencies...
    call npm install --legacy-peer-deps
)

REM Run frontend tests with coverage
echo Running frontend tests with coverage...
echo.
call npm run test -- --run --coverage

if %ERRORLEVEL% equ 0 (
    echo.
    echo ✅ Frontend tests PASSED
    set /a PASSED_TESTS+=1
) else (
    echo.
    echo ❌ Frontend tests FAILED
    set /a FAILED_TESTS+=1
)
set /a TOTAL_TESTS+=1

echo.
echo 📊 Frontend Coverage Report:
echo    HTML: %PROJECT_ROOT%\frontend\coverage\index.html
echo.

REM ==================== SUMMARY ====================
cd /d "%PROJECT_ROOT%"
echo.
echo ═══════════════════════════════════════════════════════
echo 📈 TEST SUMMARY
echo ═══════════════════════════════════════════════════════
echo.
echo Total Test Suites: %TOTAL_TESTS%
echo ✅ Passed: %PASSED_TESTS%
echo ❌ Failed: %FAILED_TESTS%
echo.

if %FAILED_TESTS% equ 0 (
    echo 🎉 All tests passed!
    echo.
    echo 📊 Coverage Reports:
    echo    Backend:  file:///%PROJECT_ROOT%\backend\htmlcov\index.html
    echo    Frontend: file:///%PROJECT_ROOT%\frontend\coverage\index.html
    echo.
    
    REM Try to open coverage reports in browser
    echo 🌐 Opening coverage reports in browser...
    start "" "%PROJECT_ROOT%\backend\htmlcov\index.html"
    timeout /t 2 /nobreak >nul
    start "" "%PROJECT_ROOT%\frontend\coverage\index.html"
    
    exit /b 0
) else (
    echo ⚠️  Some tests failed. Check the output above for details.
    echo.
    echo 📊 Coverage Reports (partial):
    echo    Backend:  file:///%PROJECT_ROOT%\backend\htmlcov\index.html
    echo    Frontend: file:///%PROJECT_ROOT%\frontend\coverage\index.html
    echo.
    
    exit /b 1
)
