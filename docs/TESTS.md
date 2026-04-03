# 🧪 Quick Test Guide

## Запустить все тесты с покрытием

```bash
.\run_tests.bat          # Windows
./run_tests.sh           # Linux/Mac
npm test                 # Любой OS
```

## Отчёты

После запуска тестов откроются HTML отчёты о покрытии:
- **Backend:** `backend/htmlcov/index.html`
- **Frontend:** `frontend/coverage/index.html`

## Быстрые команды

### Backend
```bash
pytest backend/tests/ -v                           # Все тесты
pytest backend/tests/test_health.py -v            # Один файл
pytest --cov=backend.src --cov-report=html        # С покрытием
```

### Frontend
```bash
cd frontend
npm run test                 # Все тесты
npm run test:coverage        # С покрытием
npm run test:ui             # С интерфейсом
```

---

**📊 Полная документация:** [TEST_GUIDE.md](./TEST_GUIDE.md)
