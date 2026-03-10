/**
 * Tests for TurnQueue component
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TurnQueue } from '../components/TurnQueue'

// Mock zustand
vi.mock('../store/gameStore', () => ({
  useGameStore: {
    getState: vi.fn(() => ({
      turnQueue: [
        {
          character_id: 1,
          character_name: 'TestChar1',
          initiative: 15,
          is_alive: true,
        },
        {
          character_id: 2,
          character_name: 'TestChar2',
          initiative: 12,
          is_alive: true,
        },
      ],
      activeCharacter: { name: 'TestChar1' },
    })),
  },
}))

describe('TurnQueue', () => {
  it('should render turn queue with characters', () => {
    render(<TurnQueue />)
    
    // Should render the component
    expect(screen.getByTestId('turn-queue')).toBeInTheDocument()
  })

  it('should sort characters by initiative', () => {
    render(<TurnQueue />)
    
    const portraits = screen.getAllByTestId('character-portrait')
    expect(portraits).toHaveLength(2)
    
    // First should have higher initiative
    expect(portraits[0]).toHaveTextContent('TestChar1')
  })

  it('should highlight active character', () => {
    render(<TurnQueue />)
    
    const activePortrait = screen.getByTestId('character-portrait-active')
    expect(activePortrait).toBeInTheDocument()
  })

  it('should show empty state when no turn queue', () => {
    vi.mocked(require('../store/gameStore').useGameStore.getState).mockReturnValue({
      turnQueue: [],
      activeCharacter: null,
    })

    render(<TurnQueue />)
    
    // Should handle empty state gracefully
    expect(screen.getByTestId('turn-queue')).toBeInTheDocument()
  })
})
