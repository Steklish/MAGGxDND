/**
 * Tests for TurnQueue component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TurnQueue } from '../components/TurnQueue'
import * as gameStoreModule from '../store/gameStore'

describe('TurnQueue', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('should render turn queue with characters', () => {
    vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
      turnQueue: [
        { character: 'TestChar1', next_turn: 1 },
        { character: 'TestChar2', next_turn: 2 },
      ],
      activeCharacter: { name: 'TestChar1' },
    } as any)

    render(<TurnQueue />)
    expect(screen.getByTestId('turn-queue')).toBeInTheDocument()
  })

  it('should sort characters by next_turn', () => {
    vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
      turnQueue: [
        { character: 'TestChar2', next_turn: 5 },
        { character: 'TestChar1', next_turn: 1 },
      ],
      activeCharacter: { name: 'TestChar1' },
    } as any)

    render(<TurnQueue />)
    const active = screen.getByTestId('character-portrait-active')
    expect(active).toHaveTextContent('TestChar1')
  })

  it('should highlight active character', () => {
    vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
      turnQueue: [
        { character: 'TestChar1', next_turn: 1 },
        { character: 'TestChar2', next_turn: 2 },
      ],
      activeCharacter: { name: 'TestChar1' },
    } as any)

    render(<TurnQueue />)
    const activePortrait = screen.getByTestId('character-portrait-active')
    expect(activePortrait).toBeInTheDocument()
  })

  it('should show empty state when no turn queue', () => {
    vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
      turnQueue: [],
      activeCharacter: null,
    } as any)

    render(<TurnQueue />)
    expect(screen.getByTestId('turn-queue')).toBeInTheDocument()
    expect(screen.getByText('Turn Queue: Empty')).toBeInTheDocument()
  })
})
