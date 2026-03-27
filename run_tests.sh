#!/bin/bash

# MAGGxDND - Full Test Suite Runner with Coverage Report

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║          MAGGxDND - Full Test Suite Runner               ║"
echo "║                   with Coverage Report                   ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Save current directory
PROJECT_ROOT="$(pwd)"

# Counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# ==================== BACKEND TESTS ====================
echo "═══════════════════════════════════════════════════════"
echo "🐍 BACKEND TESTS (Pytest)"
echo "═══════════════════════════════════════════════════════"
echo ""

cd "$PROJECT_ROOT" || exit 1

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found! Installing..."
    pip install pytest pytest-asyncio pytest-cov httpx
fi

# Run backend tests with coverage
echo "Running backend tests with coverage..."
echo ""
pytest backend/tests/ \
    --cov=backend.src \
    --cov-report=term-missing \
    --cov-report=html:backend/htmlcov \
    --cov-report=xml:backend/coverage.xml \
    -v \
    --tb=short

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Backend tests PASSED"
    ((PASSED_TESTS++))
else
    echo ""
    echo "❌ Backend tests FAILED"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))

echo ""
echo "📊 Backend Coverage Report:"
echo "   HTML: $PROJECT_ROOT/backend/htmlcov/index.html"
echo "   XML:  $PROJECT_ROOT/backend/coverage.xml"
echo ""

# ==================== FRONTEND TESTS ====================
echo "═══════════════════════════════════════════════════════"
echo "⚛️  FRONTEND TESTS (Vitest)"
echo "═══════════════════════════════════════════════════════"
echo ""

cd "$PROJECT_ROOT/frontend" || exit 1

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "⚠️  node_modules not found! Installing dependencies..."
    npm install --legacy-peer-deps
fi

# Run frontend tests with coverage
echo "Running frontend tests with coverage..."
echo ""
npm run test -- --run --coverage

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Frontend tests PASSED"
    ((PASSED_TESTS++))
else
    echo ""
    echo "❌ Frontend tests FAILED"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))

echo ""
echo "📊 Frontend Coverage Report:"
echo "   HTML: $PROJECT_ROOT/frontend/coverage/index.html"
echo ""

# ==================== SUMMARY ====================
cd "$PROJECT_ROOT" || exit 1
echo ""
echo "═══════════════════════════════════════════════════════"
echo "📈 TEST SUMMARY"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "Total Test Suites: $TOTAL_TESTS"
echo "✅ Passed: $PASSED_TESTS"
echo "❌ Failed: $FAILED_TESTS"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo "🎉 All tests passed!"
    echo ""
    echo "📊 Coverage Reports:"
    echo "   Backend:  file://$PROJECT_ROOT/backend/htmlcov/index.html"
    echo "   Frontend: file://$PROJECT_ROOT/frontend/coverage/index.html"
    echo ""
    
    # Try to open coverage reports in browser
    echo "🌐 Opening coverage reports in browser..."
    if command -v xdg-open &> /dev/null; then
        xdg-open "$PROJECT_ROOT/backend/htmlcov/index.html" &
        xdg-open "$PROJECT_ROOT/frontend/coverage/index.html" &
    elif command -v open &> /dev/null; then
        open "$PROJECT_ROOT/backend/htmlcov/index.html" &
        open "$PROJECT_ROOT/frontend/coverage/index.html" &
    fi
    
    exit 0
else
    echo "⚠️  Some tests failed. Check the output above for details."
    echo ""
    echo "📊 Coverage Reports (partial):"
    echo "   Backend:  file://$PROJECT_ROOT/backend/htmlcov/index.html"
    echo "   Frontend: file://$PROJECT_ROOT/frontend/coverage/index.html"
    echo ""
    
    exit 1
fi
