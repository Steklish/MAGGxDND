/**
 * Tests for API services
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { characterAPI, Character } from './characterAPI'
import { sessionAPI, GameSession } from './sessionAPI'

// Mock fetch
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('API Services', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('characterAPI', () => {
    const mockCharacter: Character = {
      id: 1,
      user_id: 1,
      name: 'Test Character',
      race: 'Human',
      char_class: 'Fighter',
      level: 1,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    describe('createCharacter', () => {
      it('should create character successfully', async () => {
        mockFetch.mockResolvedValueOnce({
          ok: true,
          json: async () => mockCharacter,
        })

        const result = await characterAPI.createCharacter({
          name: 'Test Character',
          race: 'Human',
          char_class: 'Fighter',
        })

        expect(result).toEqual(mockCharacter)
        expect(mockFetch).toHaveBeenCalledWith(
          '/api/v1/characters',
          expect.objectContaining({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
          })
        )
      })

      it('should handle API error', async () => {
        mockFetch.mockResolvedValueOnce({
          ok: false,
          status: 400,
          json: async () => ({ detail: 'Invalid character data' }),
        })

        await expect(
          characterAPI.createCharacter({ name: '' })
        ).rejects.toThrow('Invalid character data')
      })
    })

    describe('getUserCharacters', () => {
      it('should get user characters', async () => {
        mockFetch.mockResolvedValueOnce({
          ok: true,
          json: async () => [mockCharacter],
        })

        const result = await characterAPI.getUserCharacters(1)
        expect(result).toEqual([mockCharacter])
        expect(mockFetch).toHaveBeenCalledWith('/api/v1/characters?user_id=1')
      })
    })

    describe('deleteCharacter', () => {
      it('should delete character successfully', async () => {
        mockFetch.mockResolvedValueOnce({
          ok: true,
        })

        await characterAPI.deleteCharacter(1)
        expect(mockFetch).toHaveBeenCalledWith(
          '/api/v1/characters/1',
          expect.objectContaining({ method: 'DELETE' })
        )
      })
    })
  })

  describe('sessionAPI', () => {
    const mockSession: GameSession = {
      session_id: 'test-123',
      session_name: 'Test Session',
      game_mode: 'STORY',
      player_count: 1,
      max_players: 5,
      status: 'created',
      players: [],
      npcs: [],
    }

    describe('createSession', () => {
      it('should create session successfully', async () => {
        mockFetch.mockResolvedValueOnce({
          ok: true,
          json: async () => mockSession,
        })

        const result = await sessionAPI.createSession({
          session_name: 'Test Session',
          game_mode: 'STORY',
        })

        expect(result).toEqual(mockSession)
        expect(mockFetch).toHaveBeenCalledWith(
          '/api/v1/sessions',
          expect.objectContaining({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
          })
        )
      })
    })

    describe('listSessions', () => {
      it('should list sessions', async () => {
        mockFetch.mockResolvedValueOnce({
          ok: true,
          json: async () => ({ sessions: [mockSession], total: 1 }),
        })

        const result = await sessionAPI.listSessions()
        expect(result.sessions).toEqual([mockSession])
        expect(result.total).toBe(1)
      })
    })

    describe('joinSession', () => {
      it('should join session', async () => {
        mockFetch.mockResolvedValueOnce({
          ok: true,
          json: async () => ({ player_id: 'player-123' }),
        })

        const result = await sessionAPI.joinSession('test-123', {
          player_name: 'TestPlayer',
        })

        expect(result.player_id).toBe('player-123')
      })
    })
  })
})
