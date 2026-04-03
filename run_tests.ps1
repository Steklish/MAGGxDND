# MAGGxDND - Test Runner with Coverage
# Run all tests and display coverage reports

Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       MAGGxDND - Test Suite Runner with Coverage         ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$PROJECT_ROOT = Get-Location
$TOTAL = 0
$PASSED = 0
$FAILED = 0

# ==================== BACKEND TESTS ====================
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "🐍 BACKEND TESTS (Pytest)" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

Set-Location $PROJECT_ROOT

# Check if pytest is installed
try {
    Get-Command pytest -ErrorAction Stop | Out-Null
} catch {
    Write-Host "❌ pytest not found! Installing..." -ForegroundColor Yellow
    pip install pytest pytest-asyncio pytest-cov httpx
}

# Run backend tests with coverage
Write-Host "Running backend tests with coverage..." -ForegroundColor White
Write-Host ""

$pytestArgs = @(
    "tests/backend/",
    "--cov=backend.src",
    "--cov-report=term-missing",
    "--cov-report=html=tests/reports/backend/htmlcov",
    "--cov-report=xml:tests/reports/backend/coverage.xml",
    "-v",
    "--tb=short"
)

& pytest $pytestArgs
$backendExitCode = $LASTEXITCODE

if ($backendExitCode -eq 0) {
    Write-Host ""
    Write-Host "✅ Backend tests PASSED" -ForegroundColor Green
    $PASSED++
} else {
    Write-Host ""
    Write-Host "❌ Backend tests FAILED" -ForegroundColor Red
    $FAILED++
}
$TOTAL++

Write-Host ""
Write-Host "📊 Backend Coverage Report:" -ForegroundColor Cyan
Write-Host "   HTML: $($PROJECT_ROOT)\tests\reports\backend\htmlcov\index.html"
Write-Host "   XML:  $($PROJECT_ROOT)\tests\reports\backend\coverage.xml"
Write-Host ""

# ==================== FRONTEND TESTS ====================
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Blue
Write-Host "⚛️  FRONTEND TESTS (Vitest)" -ForegroundColor Blue
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Blue
Write-Host ""

Set-Location "$PROJECT_ROOT\frontend"

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "⚠️  node_modules not found! Installing dependencies..." -ForegroundColor Yellow
    npm install --legacy-peer-deps
}

# Run frontend tests with coverage
Write-Host "Running frontend tests with coverage..." -ForegroundColor White
Write-Host ""

npm run test -- --run --coverage --coverage.reportsDirectory=../tests/reports/frontend/htmlcov
$frontendExitCode = $LASTEXITCODE

if ($frontendExitCode -eq 0) {
    Write-Host ""
    Write-Host "✅ Frontend tests PASSED" -ForegroundColor Green
    $PASSED++
} else {
    Write-Host ""
    Write-Host "❌ Frontend tests FAILED" -ForegroundColor Red
    $FAILED++
}
$TOTAL++

Write-Host ""
Write-Host "📊 Frontend Coverage Report:" -ForegroundColor Cyan
Write-Host "   HTML: $($PROJECT_ROOT)\tests\reports\frontend\htmlcov\index.html"
Write-Host ""

# ==================== SUMMARY ====================
Set-Location $PROJECT_ROOT
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Magenta
Write-Host "📈 TEST SUMMARY" -ForegroundColor Magenta
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Magenta
Write-Host ""
Write-Host "Total Test Suites: $TOTAL" -ForegroundColor White
Write-Host "✅ Passed: $PASSED" -ForegroundColor Green
Write-Host "❌ Failed: $FAILED" -ForegroundColor $(if ($FAILED -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($FAILED -eq 0) {
    Write-Host "🎉 All tests passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Coverage Reports:" -ForegroundColor Cyan
    Write-Host "   Backend:  file://$($PROJECT_ROOT)\tests\reports\backend\htmlcov\index.html"
    Write-Host "   Frontend: file://$($PROJECT_ROOT)\tests\reports\frontend\htmlcov\index.html"
    Write-Host ""

    # Open coverage reports in browser
    Write-Host "🌐 Opening coverage reports in browser..." -ForegroundColor Cyan
    Start-Process "$PROJECT_ROOT\tests\reports\backend\htmlcov\index.html"
    Start-Sleep -Seconds 2
    Start-Process "$PROJECT_ROOT\tests\reports\frontend\htmlcov\index.html"

    exit 0
} else {
    Write-Host "⚠️  Some tests failed. Check the output above for details." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "📊 Coverage Reports (partial):" -ForegroundColor Cyan
    Write-Host "   Backend:  file://$($PROJECT_ROOT)\tests\reports\backend\htmlcov\index.html"
    Write-Host "   Frontend: file://$($PROJECT_ROOT)\tests\reports\frontend\htmlcov\index.html"
    Write-Host ""

    exit 1
}
