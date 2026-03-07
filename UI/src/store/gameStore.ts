import { create } from 'zustand';
import { characterAPI, Character, CharacterProfile } from '../services/characterAPI';
import { sessionAPI, GameSession } from '../services/sessionAPI';

interface GameState {
    // Auth state
    isAuthenticated: boolean;
    userId: number | null;
    username: string | null;
    accessToken: string | null;
    
    // Character state
    characters: Character[];
    selectedCharacter: Character | null;
    characterProfiles: Map<number, CharacterProfile>;
    activeCharacter: Character | null; // Currently active character for actions
    
    // Game session state
    activeSessions: GameSession[];
    currentSession: GameSession | null;
    session: GameSession | null; // Alias for currentSession (for compatibility)
    sessionId: string | null;
    currentScene: any | null; // Current scene data
    
    // UI state
    mode: 'menu' | 'connecting' | 'playing' | 'error' | null;
    error: string | null;
    isLoading: boolean;
    isGenerating: boolean; // For game generation loading state
    generationStatus: string; // Status message during generation
    isDMThinking: boolean; // DM is thinking about player action
    
    // Game messages/events
    messages: any[];
    events: any[];
    turnQueue: any[];

    // Actions - Messages
    addMessage: (message: any) => void;
    addEvent: (event: any) => void;
    
    // Actions - Auth
    setAuthenticated: (value: boolean) => void;
    setUserId: (id: number) => void;
    setUsername: (name: string) => void;
    setAccessToken: (token: string) => void;
    logout: () => void;
    
    // Actions - Characters
    loadCharacters: (userId: number) => Promise<void>;
    setSelectedCharacter: (character: Character | null) => void;
    setActiveCharacter: (character: Character | null) => void;
    createCharacter: (data: any) => Promise<Character>;
    deleteCharacter: (characterId: number) => Promise<void>;
    loadCharacterProfile: (characterId: number) => Promise<CharacterProfile | null>;
    
    // Actions - Sessions
    loadSessions: () => Promise<void>;
    createSession: (data: any) => Promise<GameSession>;
    joinSession: (sessionId: string, playerName: string) => Promise<void>;
    leaveSession: (sessionId: string, playerId: string) => Promise<void>;
    setCurrentSession: (session: GameSession | null) => void;
    
    // Actions - UI
    setMode: (mode: 'menu' | 'connecting' | 'playing' | 'error' | null) => void;
    setError: (error: string | null) => void;
    setLoading: (loading: boolean) => void;
    setIsGenerating: (generating: boolean) => void;
    setGenerationStatus: (status: string) => void;
    setIsDMThinking: (thinking: boolean) => void;
    setMessages: (messages: any[]) => void;
    setEvents: (events: any[]) => void;
    setCurrentScene: (scene: any) => void;
    sendAction: (actionText: string, character: any) => void;
    getMessageType: (senderName: string) => string;
    isActionPending: boolean;
    clarificationText: string;
}

export const useGameStore = create<GameState>((set, get) => ({
    // Initial state - NO demo data
    isAuthenticated: false,
    userId: null,
    username: null,
    accessToken: null,

    characters: [],
    selectedCharacter: null,
    characterProfiles: new Map(),
    activeCharacter: null,

    activeSessions: [],
    currentSession: null,
    session: null,
    sessionId: null,

    mode: 'menu',
    error: null,
    isLoading: false,
    isGenerating: false,
    generationStatus: '',
    isDMThinking: false,
    messages: [],
    events: [],
    turnQueue: [],
    currentScene: null,
    
    // Auth actions
    setAuthenticated: (value) => set({ isAuthenticated: value }),

    setUserId: (id) => {
        localStorage.setItem('userId', id.toString());
        set({ userId: id });
    },

    setUsername: (name) => {
        localStorage.setItem('username', name);
        set({ username: name });
    },

    setAccessToken: (token) => {
        localStorage.setItem('access_token', token);
        set({ accessToken: token });
    },

    logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('username');
        localStorage.removeItem('userId');
        set({
            isAuthenticated: false,
            userId: null,
            username: null,
            accessToken: null,
            characters: [],
            selectedCharacter: null,
            activeSessions: [],
            currentSession: null,
            sessionId: null,
            mode: 'menu',
        });
    },

    // Character actions
    loadCharacters: async (userId) => {
        set({ isLoading: true });
        try {
            const characters = await characterAPI.getUserCharacters(userId);
            set({ characters, isLoading: false });

            // Load profiles for each character
            const profiles = new Map<number, CharacterProfile>();
            for (const char of characters) {
                try {
                    const profile = await characterAPI.getCharacterProfile(char.id);
                    profiles.set(char.id, profile);
                } catch (e) {
                    console.warn(`Failed to load profile for character ${char.id}`);
                }
            }
            set({ characterProfiles: profiles });
        } catch (error: any) {
            console.warn('Failed to load characters (using empty list):', error.message);
            set({ characters: [], isLoading: false });
        }
    },

    setSelectedCharacter: (character) => {
        set({ selectedCharacter: character });
        if (character) {
            localStorage.setItem('selectedCharacterId', character.id.toString());
        }
    },

    setActiveCharacter: (character) => {
        set({ activeCharacter: character });
    },

    createCharacter: async (data) => {
        set({ isLoading: true });
        try {
            const character = await characterAPI.createCharacter(data);
            
            // Create profile
            if (data.profileData) {
                await characterAPI.createCharacterProfile({
                    character_id: character.id,
                    ...data.profileData,
                });
            }
            
            // Refresh characters list
            const { userId } = get();
            if (userId) {
                await get().loadCharacters(userId);
            }
            
            set({ isLoading: false });
            return character;
        } catch (error: any) {
            console.error('Failed to create character:', error);
            set({ 
                error: error.response?.data?.detail || 'Failed to create character',
                isLoading: false 
            });
            throw error;
        }
    },

    deleteCharacter: async (characterId) => {
        try {
            await characterAPI.deleteCharacter(characterId);
            
            // Refresh characters list
            const { userId } = get();
            if (userId) {
                await get().loadCharacters(userId);
            }
            
            // Clear selected if deleted
            const { selectedCharacter } = get();
            if (selectedCharacter?.id === characterId) {
                set({ selectedCharacter: null });
            }
        } catch (error: any) {
            console.error('Failed to delete character:', error);
            throw error;
        }
    },

    loadCharacterProfile: async (characterId) => {
        try {
            const profile = await characterAPI.getCharacterProfile(characterId);
            const { characterProfiles } = get();
            const newProfiles = new Map(characterProfiles);
            newProfiles.set(characterId, profile);
            set({ characterProfiles: newProfiles });
            return profile;
        } catch (error: any) {
            console.error('Failed to load character profile:', error);
            return null;
        }
    },
    
    // Session actions
    loadSessions: async () => {
        try {
            const { sessions } = await sessionAPI.listSessions();
            // Filter out duplicates by session_id
            const uniqueSessions = sessions.filter(
                (sess, index, self) => index === self.findIndex(s => s.session_id === sess.session_id)
            );
            set({ activeSessions: uniqueSessions });
        } catch (error: any) {
            console.warn('Failed to load sessions (using empty list):', error.message);
            set({ activeSessions: [] });
        }
    },

    createSession: async (data: any): Promise<GameSession> => {
        set({ isLoading: true });
        try {
            const session = await sessionAPI.createSession(data);
            set({ 
                currentSession: session,
                sessionId: session.session_id,
                isLoading: false,
            });
            await get().loadSessions();
            return session;
        } catch (error: any) {
            console.error('Failed to create session:', error);
            set({ 
                error: error.response?.data?.detail || 'Failed to create session',
                isLoading: false 
            });
            throw error;
        }
    },

    joinSession: async (sessionId: string, playerName: string) => {
        try {
            await sessionAPI.joinSession(sessionId, { player_name: playerName });
            await get().loadSessions();
        } catch (error: any) {
            console.error('Failed to join session:', error);
            throw error;
        }
    },

    leaveSession: async (sessionId: string, playerId: string) => {
        try {
            await sessionAPI.leaveSession(sessionId, playerId);
            set({ currentSession: null, sessionId: null });
            await get().loadSessions();
        } catch (error: any) {
            console.error('Failed to leave session:', error);
            throw error;
        }
    },

    setCurrentSession: (session) => {
        set({
            currentSession: session,
            session: session, // Also update alias
            sessionId: session?.session_id || null,
        });
    },

    // Actions - UI
    setMode: (mode) => set({ mode }),
    setError: (error) => set({ error }),
    setLoading: (loading) => set({ isLoading: loading }),
    setIsGenerating: (generating) => set({ isGenerating: generating }),
    setGenerationStatus: (status) => set({ generationStatus: status }),
    setIsDMThinking: (thinking) => set({ isDMThinking: thinking }),
    setMessages: (messages) => set({ messages }),
    setEvents: (events) => set({ events }),
    addMessage: (message) => set((state) => {
        // Prevent duplicate messages
        const isDuplicate = state.messages.some(
            m => m.sender_name === message.sender_name && 
                 m.text === message.text && 
                 Math.abs(new Date(m.timestamp).getTime() - new Date(message.timestamp).getTime()) < 1000
        );
        if (isDuplicate) {
            return state;
        }
        return { messages: [...state.messages, message] };
    }),
    addEvent: (event) => set((state) => ({ events: [...state.events, event] })),
    setCurrentScene: (scene) => set({ currentScene: scene }),

    // Send action to backend for AI processing
    sendAction: async (actionText: string, character: any) => {
        console.log('📝 Player action:', actionText);
        
        const state = useGameStore.getState();
        
        // Add player message to store immediately
        const playerMessage = {
            sender_name: character.name,
            text: actionText,
            type: 'player',
            timestamp: new Date().toISOString(),
        };
        state.addMessage(playerMessage);
        
        // Set DM thinking state
        state.setIsDMThinking(true);
        
        // Send to backend for AI processing
        const sessionId = localStorage.getItem('currentSessionId');
        try {
            const response = await fetch(`/api/v1/sessions/${sessionId}/player_action`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    character_name: character.name,
                    action: actionText,
                }),
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            // Clear thinking state
            state.setIsDMThinking(false);
            
            // Add AI response from backend
            const dmResponse = {
                sender_name: 'DM',
                text: data.response || data.dm_response || 'The DM considers your action...',
                type: 'dm',
                timestamp: new Date().toISOString(),
            };
            state.addMessage(dmResponse);
            
        } catch (error) {
            console.error('❌ Failed to process action:', error);
            state.setIsDMThinking(false);
            
            // Show error message
            const errorResponse = {
                sender_name: 'System',
                text: `Failed to process action: ${error instanceof Error ? error.message : 'Unknown error'}`,
                type: 'environment',
                timestamp: new Date().toISOString(),
            };
            state.addMessage(errorResponse);
        }
    },
    
    // Placeholder functions for compatibility
    getMessageType: (senderName: string) => {
        if (senderName === 'DM') return 'dm';
        if (senderName === 'System') return 'environment';
        return 'player';
    },
    isActionPending: false,
    clarificationText: '',
}));

// Initialize store from localStorage
const initStore = () => {
    const token = localStorage.getItem('access_token');
    const userId = localStorage.getItem('userId');
    const username = localStorage.getItem('username');
    const sessionId = localStorage.getItem('currentSessionId');
    const playerId = localStorage.getItem('currentPlayerId');
    const gameStatus = localStorage.getItem('gameStatus');

    if (token && userId && username) {
        useGameStore.setState({
            isAuthenticated: true,
            userId: parseInt(userId),
            username,
            accessToken: token,
        });
    }

    // Restore session if already joined
    if (sessionId && playerId) {
        const sessionData = {
            session_id: sessionId,
            session_name: 'Active Session',
            game_mode: 'STORY',
            player_count: 1,
            max_players: 5,
            status: gameStatus === 'running' ? 'running' : 'created',
            description: undefined,
            players: [{ player_id: playerId, player_name: username || 'Player', character_name: undefined, character: undefined }],
            npcs: [],
        };
        useGameStore.setState({
            sessionId,
            currentSession: sessionData,
            session: sessionData, // Also set 'session' for compatibility
        });
    }
};

initStore();

export default useGameStore;
