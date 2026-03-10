/**
 * Tests for game store (Zustand state management)
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useGameStore } from '../store/gameStore'

describe('gameStore', () => {
  beforeEach(() => {
    // Reset store before each test
    useGameStore.setState({
      isAuthenticated: false,
      userId: null,
      username: null,
      accessToken: null,
      characters: [],
      selectedCharacter: null,
      activeCharacter: null,
      activeSessions: [],
      currentSession: null,
      sessionId: null,
      mode: 'menu',
      error: null,
      isLoading: false,
      messages: [],
      events: [],
      turnQueue: [],
    })
  })

  describe('Auth State', () => {
    it('should set authentication state', () => {
      useGameStore.getState().setAuthenticated(true)
      expect(useGameStore.getState().isAuthenticated).toBe(true)

      useGameStore.getState().setAuthenticated(false)
      expect(useGameStore.getState().isAuthenticated).toBe(false)
    })

    it('should set user ID', () => {
      const mockId = 123
      useGameStore.getState().setUserId(mockId)
      expect(useGameStore.getState().userId).toBe(mockId)
    })

    it('should set username', () => {
      const mockName = 'TestUser'
      useGameStore.getState().setUsername(mockName)
      expect(useGameStore.getState().username).toBe(mockName)
    })

    it('should logout and clear all auth data', () => {
      // Set auth state
      useGameStore.getState().setAuthenticated(true)
      useGameStore.getState().setUserId(123)
      useGameStore.getState().setUsername('TestUser')
      useGameStore.getState().setAccessToken('token')

      // Logout
      useGameStore.getState().logout()

      const state = useGameStore.getState()
      expect(state.isAuthenticated).toBe(false)
      expect(state.userId).toBe(null)
      expect(state.username).toBe(null)
      expect(state.accessToken).toBe(null)
    })
  })

  describe('UI State', () => {
    it('should set mode', () => {
      useGameStore.getState().setMode('playing')
      expect(useGameStore.getState().mode).toBe('playing')

      useGameStore.getState().setMode('error')
      expect(useGameStore.getState().mode).toBe('error')
    })

    it('should set error', () => {
      const mockError = 'Test error message'
      useGameStore.getState().setError(mockError)
      expect(useGameStore.getState().error).toBe(mockError)

      useGameStore.getState().setError(null)
      expect(useGameStore.getState().error).toBe(null)
    })

    it('should set loading state', () => {
      useGameStore.getState().setLoading(true)
      expect(useGameStore.getState().isLoading).toBe(true)

      useGameStore.getState().setLoading(false)
      expect(useGameStore.getState().isLoading).toBe(false)
    })

    it('should set DM thinking state', () => {
      useGameStore.getState().setIsDMThinking(true)
      expect(useGameStore.getState().isDMThinking).toBe(true)

      useGameStore.getState().setIsDMThinking(false)
      expect(useGameStore.getState().isDMThinking).toBe(false)
    })
  })

  describe('Messages', () => {
    it('should add message', () => {
      const mockMessage = {
        sender_name: 'TestUser',
        text: 'Hello!',
        type: 'player',
        timestamp: new Date().toISOString(),
      }

      useGameStore.getState().addMessage(mockMessage)
      expect(useGameStore.getState().messages).toHaveLength(1)
      expect(useGameStore.getState().messages[0]).toEqual(mockMessage)
    })

    it('should prevent duplicate messages', () => {
      const mockMessage = {
        sender_name: 'TestUser',
        text: 'Hello!',
        type: 'player',
        timestamp: new Date().toISOString(),
      }

      // Add twice
      useGameStore.getState().addMessage(mockMessage)
      useGameStore.getState().addMessage(mockMessage)

      // Should only have one (duplicate prevention)
      expect(useGameStore.getState().messages).toHaveLength(1)
    })

    it('should add event', () => {
      const mockEvent = {
        event_type: 'TEST_EVENT',
        data: { key: 'value' },
        source: 'test',
      }

      useGameStore.getState().addEvent(mockEvent)
      expect(useGameStore.getState().events).toHaveLength(1)
    })
  })

  describe('Session Management', () => {
    it('should set current session', () => {
      const mockSession = {
        session_id: 'test-123',
        session_name: 'Test Session',
        game_mode: 'STORY',
        player_count: 1,
        max_players: 5,
        status: 'created',
        players: [],
        npcs: [],
      }

      useGameStore.getState().setCurrentSession(mockSession)
      
      const state = useGameStore.getState()
      expect(state.currentSession).toEqual(mockSession)
      expect(state.sessionId).toBe('test-123')
    })

    it('should clear session when set to null', () => {
      useGameStore.getState().setCurrentSession(null)
      
      const state = useGameStore.getState()
      expect(state.currentSession).toBe(null)
      expect(state.sessionId).toBe(null)
    })
  })

  describe('Character Management', () => {
    it('should set selected character', () => {
      const mockCharacter = {
        id: 1,
        user_id: 1,
        name: 'Test Character',
        race: 'Human',
        char_class: 'Fighter',
        level: 1,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      useGameStore.getState().setSelectedCharacter(mockCharacter)
      expect(useGameStore.getState().selectedCharacter).toEqual(mockCharacter)
    })

    it('should set active character', () => {
      const mockCharacter = {
        id: 1,
        user_id: 1,
        name: 'Test Character',
        race: 'Human',
        char_class: 'Fighter',
        level: 1,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      useGameStore.getState().setActiveCharacter(mockCharacter)
      expect(useGameStore.getState().activeCharacter).toEqual(mockCharacter)
    })
  })
})
