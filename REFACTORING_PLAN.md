# 🚀 MAGGxDND - План Масштабного Рефакторинга

## 📋 Обзор Задачи

Полная переработка проекта в стиле **D&D Beyond** с добавлением:
- ✅ Продвинутого логирования
- ✅ Тестирования (unit, integration, e2e)
- ✅ Новых фич
- ✅ Оптимизации производительности
- ✅ Улучшенной архитектуры

---

## 🎯 Цели Рефакторинга

### 1. Архитектура в стиле D&D Beyond
- Модульная структура
- Микросервисный подход
- Четкое разделение ответственности
- Масштабируемость

### 2. Всеобъемлющее Логирование
- Логирование всех API запросов
- Логирование AI взаимодействий (запросы/ответы)
- Логирование ядра приложения
- Логирование базы данных
- Логирование WebSocket событий
- Централизованная система логов

### 3. Тестирование
- Unit тесты (>80% coverage)
- Integration тесты
- E2E тесты
- Load тесты
- Snapshot тесты для UI

### 4. Новые Фичи (D&D Beyond Style)
- **Character Builder 2.0** - Продвинутый конструктор персонажей
- **Compendium** - Энциклопедия правил, заклинаний, предметов
- **Homebrew Builder** - Создание домашнего контента
- **Campaign Manager** - Управление кампаниями
- **Encounter Builder** - Конструктор встреч
- **Dice Roller** - Продвинутый бросок кубиков с историей
- **Dynamic Lighting** - Динамическое освещение для карт
- **Fog of War** - Туман войны для карт
- **Jukebox** - Фоновая музыка и звуковые эффекты
- **Video Integration** - Встроенные видеозвонки

### 5. Производительность
- Database query optimization
- Caching layer (Redis)
- Lazy loading компонентов
- Code splitting
- Image optimization
- WebSocket оптимизация

### 6. UI/UX Улучшения
- Адаптивный дизайн
- Темы (светлая/темная/авто)
- Accessibility (a11y)
- PWA поддержка
- Offline режим
- Keyboard shortcuts

---

## 📁 Новая Структура Проекта

```
MAGGxDND/
├── backend/
│   ├── src/
│   │   ├── api/                    # API Layer
│   │   │   ├── v1/                 # API Version 1
│   │   │   │   ├── routes/         # Route definitions
│   │   │   │   ├── middleware/     # Custom middleware
│   │   │   │   └── validators/     # Request validators
│   │   │   └── websocket/          # WebSocket handlers
│   │   │
│   │   ├── core/                   # Core Business Logic
│   │   │   ├── game/               # Game engine
│   │   │   ├── character/          # Character logic
│   │   │   ├── session/            # Session management
│   │   │   └── rules/              # D&D 5e rules engine
│   │   │
│   │   ├── services/               # Business Services
│   │   │   ├── auth_service.py
│   │   │   ├── ai_service.py       # AI interactions
│   │   │   ├── game_service.py
│   │   │   ├── character_service.py
│   │   │   └── notification_service.py
│   │   │
│   │   ├── repositories/           # Data Access Layer
│   │   │   ├── user_repo.py
│   │   │   ├── character_repo.py
│   │   │   └── session_repo.py
│   │   │
│   │   ├── models/                 # Database Models
│   │   │   ├── user.py
│   │   │   ├── character.py
│   │   │   └── session.py
│   │   │
│   │   ├── schemas/                # Pydantic Schemas
│   │   │   ├── user.py
│   │   │   ├── character.py
│   │   │   └── requests/
│   │   │   └── responses/
│   │   │
│   │   ├── logging/                # Logging System ⭐ NEW
│   │   │   ├── config.py           # Logging configuration
│   │   │   ├── formatters.py       # Custom formatters
│   │   │   ├── handlers.py         # Custom handlers
│   │   │   ├── filters.py          # Log filters
│   │   │   └── contexts.py         # Logging contexts
│   │   │
│   │   ├── monitoring/             # Monitoring & Metrics ⭐ NEW
│   │   │   ├── metrics.py          # Prometheus metrics
│   │   │   ├── health.py           # Health checks
│   │   │   └── tracing.py          # Distributed tracing
│   │   │
│   │   └── utils/                  # Utilities
│   │
│   ├── tests/                      # Backend Tests ⭐ NEW
│   │   ├── unit/                   # Unit tests
│   │   ├── integration/            # Integration tests
│   │   ├── e2e/                    # E2E tests
│   │   ├── fixtures/               # Test fixtures
│   │   └── conftest.py             # Pytest configuration
│   │
│   └── logs/                       # Log Files
│       ├── api/                    # API logs
│       ├── ai/                     # AI interaction logs
│       ├── game/                   # Game engine logs
│       ├── database/               # Database logs
│       └── errors/                 # Error logs
│
├── frontend/
│   ├── src/
│   │   ├── components/             # React Components
│   │   │   ├── common/             # Reusable components
│   │   │   ├── layout/             # Layout components
│   │   │   ├── characters/         # Character components
│   │   │   ├── game/               # Game components
│   │   │   └── compendium/         # Compendium components ⭐ NEW
│   │   │
│   │   ├── pages/                  # Page Components ⭐ NEW
│   │   │   ├── Home/
│   │   │   ├── Characters/
│   │   │   ├── Compendium/
│   │   │   ├── Campaigns/
│   │   │   └── Settings/
│   │   │
│   │   ├── services/               # API Services
│   │   │   ├── api.ts              # API client
│   │   │   ├── websocket.ts        # WebSocket client
│   │   │   └── interceptors.ts     # Request interceptors
│   │   │
│   │   ├── store/                  # State Management
│   │   │   ├── slices/             # Redux/Zustand slices
│   │   │   └── middleware/         # Store middleware
│   │   │
│   │   ├── hooks/                  # Custom Hooks
│   │   │   ├── useAuth.ts
│   │   │   ├── useGame.ts
│   │   │   └── useWebSocket.ts
│   │   │
│   │   ├── utils/                  # Utilities
│   │   │   ├── logger.ts           # Frontend logging ⭐ NEW
│   │   │   ├── analytics.ts        # Analytics ⭐ NEW
│   │   │   └── helpers.ts
│   │   │
│   │   ├── types/                  # TypeScript Types
│   │   └── styles/                 # Global Styles
│   │
│   ├── tests/                      # Frontend Tests ⭐ NEW
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   │
│   └── __mocks__/                  # Test Mocks
│
├── shared/                         # Shared Code ⭐ NEW
│   ├── types/                      # Shared TypeScript types
│   ├── constants/                  # Shared constants
│   └── utils/                      # Shared utilities
│
├── docs/                           # Documentation ⭐ NEW
│   ├── api/                        # API Documentation
│   ├── architecture/               # Architecture docs
│   ├── deployment/                 # Deployment guides
│   └── development/                # Development guides
│
├── scripts/                        # Build & Deploy Scripts ⭐ NEW
│   ├── build/
│   ├── deploy/
│   └── maintenance/
│
├── docker/                         # Docker Configuration ⭐ NEW
│   ├── backend/
│   ├── frontend/
│   └── docker-compose.yml
│
├── .github/                        # GitHub Actions ⭐ NEW
│   └── workflows/
│       ├── ci.yml                  # Continuous Integration
│       ├── cd.yml                  # Continuous Deployment
│       └── tests.yml               # Test workflows
│
└── config/                         # Configuration Files ⭐ NEW
    ├── jest/                       # Jest config
    ├── eslint/                     # ESLint config
    ├── prettier/                   # Prettier config
    └── tsconfig/                   # TypeScript config
```

---

## 🔧 Технические Улучшения

### 1. Логирование (Backend)

```python
# Пример продвинутого логирования
from backend.src.logging import get_logger, LogContext

logger = get_logger("ai_service")

class AIService:
    async def generate_response(self, prompt: str) -> str:
        # Log AI request
        logger.info(
            "AI request initiated",
            extra={
                "prompt_length": len(prompt),
                "prompt_preview": prompt[:100],
                "model": "gemini-2.0-flash",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Log full request to file
        logger.debug(
            "Full AI request",
            extra={"request": prompt},
            log_to_file="ai/requests.log"
        )
        
        try:
            response = await self.ai_client.generate(prompt)
            
            # Log AI response
            logger.info(
                "AI response received",
                extra={
                    "response_length": len(response),
                    "response_preview": response[:100],
                    "processing_time_ms": processing_time
                }
            )
            
            # Log full response to file
            logger.debug(
                "Full AI response",
                extra={"response": response},
                log_to_file="ai/responses.log"
            )
            
            return response
            
        except Exception as e:
            logger.error(
                "AI generation failed",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "prompt_preview": prompt[:100]
                },
                exc_info=True
            )
            raise
```

### 2. Логирование (Frontend)

```typescript
// Пример логирования на фронтенде
import { logger } from './utils/logger';

class GameService {
  async joinSession(sessionId: string) {
    // Log API call start
    logger.info('🔵 Joining session', { sessionId });
    
    // Log full request
    logger.debug('Session join request', {
      url: `/api/v1/sessions/${sessionId}/players`,
      method: 'POST',
      payload: { player_name: this.username }
    });
    
    try {
      const response = await api.post(`/sessions/${sessionId}/players`, {
        player_name: this.username
      });
      
      // Log successful response
      logger.info('✅ Session joined', {
        sessionId,
        playerId: response.data.player_id,
        responseTime: Date.now() - startTime
      });
      
      // Log full response
      logger.debug('Full response', response.data);
      
      return response.data;
      
    } catch (error) {
      // Log error with context
      logger.error('❌ Failed to join session', {
        sessionId,
        error: error.message,
        statusCode: error.response?.status,
        responseData: error.response?.data
      });
      
      throw error;
    }
  }
}
```

### 3. Тестирование (Backend)

```python
# tests/unit/test_ai_service.py
import pytest
from backend.src.services.ai_service import AIService

class TestAIService:
    @pytest.fixture
    def ai_service(self):
        return AIService()
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, ai_service):
        """Test successful AI response generation"""
        prompt = "Describe a dark cave"
        
        response = await ai_service.generate_response(prompt)
        
        assert response is not None
        assert len(response) > 0
        assert isinstance(response, str)
    
    @pytest.mark.asyncio
    async def test_generate_response_logs_request(self, ai_service, caplog):
        """Test that AI requests are properly logged"""
        prompt = "Test prompt"
        
        with caplog.at_level("INFO"):
            await ai_service.generate_response(prompt)
        
        assert "AI request initiated" in caplog.text
        assert "prompt_length" in caplog.text
    
    @pytest.mark.asyncio
    async def test_generate_response_handles_errors(self, ai_service):
        """Test error handling in AI generation"""
        # Mock AI client to raise exception
        ai_service.ai_client.generate = AsyncMock(side_effect=Exception("API Error"))
        
        with pytest.raises(Exception):
            await ai_service.generate_response("test")
```

### 4. Тестирование (Frontend)

```typescript
// tests/unit/components/CharacterPanel.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { CharacterPanel } from '../../../src/components/CharacterPanel';

describe('CharacterPanel', () => {
  const mockCharacter = {
    id: 1,
    name: 'Test Character',
    level: 5,
    class: 'Wizard',
    race: 'Human',
    hp: { current: 30, max: 30 }
  };

  it('renders character information correctly', () => {
    render(<CharacterPanel character={mockCharacter} />);
    
    expect(screen.getByText('Test Character')).toBeInTheDocument();
    expect(screen.getByText('Level 5 Human Wizard')).toBeInTheDocument();
    expect(screen.getByText('30/30 HP')).toBeInTheDocument();
  });

  it('calls onCharacterSelect when clicked', () => {
    const mockOnSelect = jest.fn();
    render(<CharacterPanel character={mockCharacter} onSelect={mockOnSelect} />);
    
    fireEvent.click(screen.getByTestId('character-panel'));
    
    expect(mockOnSelect).toHaveBeenCalledWith(mockCharacter.id);
  });
});
```

---

## 📊 Метрики и Мониторинг

### Backend Metrics (Prometheus)

```python
from prometheus_client import Counter, Histogram, Gauge

# API metrics
api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status_code']
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['endpoint']
)

# AI metrics
ai_generations_total = Counter(
    'ai_generations_total',
    'Total AI generations',
    ['model', 'status']
)

ai_generation_duration = Histogram(
    'ai_generation_duration_seconds',
    'AI generation duration'
)

# Game metrics
active_sessions = Gauge(
    'active_sessions',
    'Number of active game sessions'
)

connected_players = Gauge(
    'connected_players',
    'Number of connected players'
)
```

### Frontend Analytics

```typescript
// Analytics tracking
interface AnalyticsEvent {
  event: string;
  category: 'auth' | 'game' | 'character' | 'ui';
  action: string;
  label?: string;
  value?: number;
  metadata?: Record<string, any>;
}

function trackEvent(event: AnalyticsEvent) {
  // Send to analytics service
  analytics.track(event.event, {
    category: event.category,
    action: event.action,
    label: event.label,
    value: event.value,
    ...event.metadata
  });
  
  // Log for debugging
  logger.debug('Analytics event', event);
}

// Usage
trackEvent({
  event: 'session_joined',
  category: 'game',
  action: 'join',
  label: sessionId,
  metadata: {
    playerCount: session.players.length,
    gameMode: session.game_mode
  }
});
```

---

## 🎯 Приоритеты Реализации

### Фаза 1: Фундамент (Неделя 1-2)
1. ✅ Настройка системы логирования
2. ✅ Настройка тестирования
3. ✅ CI/CD пайплайны
4. ✅ Базовая документация

### Фаза 2: Рефакторинг (Неделя 3-4)
1. ✅ Рефакторинг API layer
2. ✅ Улучшение архитектуры БД
3. ✅ Оптимизация запросов
4. ✅ Кэширование

### Фаза 3: Новые Фичи (Неделя 5-8)
1. ✅ Compendium
2. ✅ Character Builder 2.0
3. ✅ Homebrew Builder
4. ✅ Encounter Builder

### Фаза 4: Полировка (Неделя 9-10)
1. ✅ UI/UX улучшения
2. ✅ Производительность
3. ✅ Тестирование
4. ✅ Документация

---

## 📈 Ожидаемые Результаты

После завершения рефакторинга:

- ✅ **Логирование**: 100% покрытие всех критических операций
- ✅ **Тесты**: >80% code coverage
- ✅ **Производительность**: <100ms API response time
- ✅ **Надежность**: 99.9% uptime
- ✅ **Масштабируемость**: Поддержка 1000+ concurrent users
- ✅ **Документация**: Полная документация API и архитектуры

---

**Это живый документ - будет обновляться в процессе разработки!**
