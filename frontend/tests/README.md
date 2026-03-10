# UI Tests

Test suite for MAGGxDND React UI components.

## Running Tests

```bash
cd UI

# Install test dependencies
npm install

# Run all tests
npm run test

# Run tests in watch mode
npm run test -- --watch

# Run with UI
npm run test:ui

# Run with coverage
npm run test:coverage

# Run specific test file
npm run test -- src/store/gameStore.test.ts
```

## Test Structure

```
src/
├── components/
│   ├── TurnQueue.test.tsx    # TurnQueue component tests
│   └── ...
├── services/
│   └── api.test.ts           # API service tests
├── store/
│   ├── gameStore.test.ts     # Zustand store tests
│   └── ...
└── tests/
    └── setup.ts              # Test setup file
```

## Testing Libraries

- **Vitest**: Test runner (Vite-native)
- **@testing-library/react**: React component testing
- **@testing-library/jest-dom**: DOM matchers
- **jsdom**: Browser-like environment

## Writing Tests

### Component Test Example

```tsx
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { MyComponent } from './MyComponent'

describe('MyComponent', () => {
  it('should render correctly', () => {
    render(<MyComponent title="Test" />)
    expect(screen.getByText('Test')).toBeInTheDocument()
  })
})
```

### Store Test Example

```ts
import { describe, it, expect, beforeEach } from 'vitest'
import { useGameStore } from '../store/gameStore'

describe('gameStore', () => {
  beforeEach(() => {
    // Reset state
    useGameStore.setState({ mode: 'menu' })
  })

  it('should update mode', () => {
    useGameStore.getState().setMode('playing')
    expect(useGameStore.getState().mode).toBe('playing')
  })
})
```

### API Service Test Example

```ts
import { describe, it, expect, vi } from 'vitest'
import { myAPI } from './api'

global.fetch = vi.fn()

describe('myAPI', () => {
  it('should fetch data', async () => {
    fetch.mockResolvedValue({ ok: true, json: async () => ({ id: 1 }) })
    const result = await myAPI.getData()
    expect(result.id).toBe(1)
  })
})
```

## Common Matchers

```ts
// DOM
toBeInTheDocument()
toBeVisible()
toHaveTextContent()
toHaveAttribute()
toHaveClass()

// Values
toBe(value)
toEqual(object)
.toHaveLength(number)
.toContain(item)
.toThrow()

// Async
.resolves
.rejects
```

## Mocking

### Mock Module

```ts
vi.mock('../store/gameStore', () => ({
  useGameStore: {
    getState: vi.fn(() => ({ /* mock state */ })),
  },
}))
```

### Mock Fetch

```ts
global.fetch = vi.fn()
fetch.mockResolvedValue({ ok: true, json: async () => data })
```

### Mock Function

```ts
const mockFn = vi.fn()
mockFn.mockReturnValue(42)
mockFn.mockResolvedValue(data)

expect(mockFn).toHaveBeenCalled()
expect(mockFn).toHaveBeenCalledWith(arg1, arg2)
```
