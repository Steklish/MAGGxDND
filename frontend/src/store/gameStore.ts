import { create } from 'zustand';
import { characterAPI, Character, CharacterProfile } from '../services/characterAPI';
import { sessionAPI, GameSession } from '../services/sessionAPI';
import { webSocketService } from '../services/websocket';

interface GameState {
    // Auth state
    isAuthenticated: boolean;
    userId: number | null;
    username: string | null;
    accessToken: string | null;
    isGuest: boolean;  // Track if user is a guest
    rememberMe: boolean;  // Track if remember me is enabled

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
    setIsGuest: (isGuest: boolean) => void;
    setRememberMe: (remember: boolean) => void;
    logout: () => void;
    checkAuthPersistence: () => void;  // Check localStorage on app start
    
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
    setActiveSessions: (sessions: GameSession[]) => void;
    connectWebSocket: (sessionId: string, playerId: string) => Promise<void>;
    disconnectWebSocket: () => void;
    
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
    isGuest: false,
    rememberMe: false,

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
    checkAuthPersistence: () => {
        // Check localStorage for persisted auth on app start
        const token = localStorage.getItem('access_token');
        const userId = localStorage.getItem('userId');
        const username = localStorage.getItem('username');
        const isGuest = localStorage.getItem('is_guest') === 'true';
        const rememberMe = localStorage.getItem('remember_me') === 'true';
        
        if (token) {
            set({
                isAuthenticated: true,
                accessToken: token,
                userId: userId ? parseInt(userId) : null,
                username: username || null,
                isGuest,
                rememberMe,
            });
            console.log('✅ Auth restored from localStorage:', { username, isGuest, rememberMe });
        }
    },

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

    setIsGuest: (isGuest) => {
        localStorage.setItem('is_guest', isGuest.toString());
        set({ isGuest });
    },

    setRememberMe: (remember) => {
        localStorage.setItem('remember_me', remember.toString());
        set({ rememberMe: remember });
    },

    logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('username');
        localStorage.removeItem('userId');
        localStorage.removeItem('is_guest');
        localStorage.removeItem('remember_me');
        localStorage.removeItem('currentSessionId');
        localStorage.removeItem('currentSessionName');
        localStorage.removeItem('currentPlayerId');
        localStorage.removeItem('activeSessionIds');
        localStorage.removeItem('selectedCharacterId');
        set({
            isAuthenticated: false,
            userId: null,
            username: null,
            accessToken: null,
            isGuest: false,
            rememberMe: false,
            characters: [],
            selectedCharacter: null,
            activeSessions: [],
            currentSession: null,
            session: null,
            sessionId: null,
            mode: 'menu',
        });
    },

    // Character actions
    // NOTE: Characters now belong to sessions, not users directly
    // Characters are loaded through session game_info endpoint
    loadCharacters: async (_userId) => {
        // Deprecated - characters are now loaded from sessions
        // Use loadSessions() to get sessions, then getGameInfo(sessionId) for characters
        console.warn('loadCharacters is deprecated. Characters belong to sessions.');
        set({ characters: [], isLoading: false });
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

    createCharacter: async (_data) => {
        // Deprecated - use createCharacterInSession instead
        console.warn('createCharacter deprecated. Use createCharacterInSession.');
        throw new Error('Deprecated: Use session-based character creation');
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
            const { userId, accessToken } = get();
            
            // Check if we have a valid token
            if (!accessToken) {
                console.warn('⚠️ No access token - skipping session load');
                set({ activeSessions: [] });
                return;
            }
            
            // Pass userId to filter sessions by owner
            const { sessions } = await sessionAPI.listSessions(userId || undefined);
            // Filter out duplicates by session_id
            const uniqueSessions = sessions.filter(
                (sess, index, self) => index === self.findIndex(s => s.session_id === sess.session_id)
            );
            set({ activeSessions: uniqueSessions });
            // Also persist session IDs to localStorage for recovery
            const sessionIds = uniqueSessions.map(s => s.session_id);
            localStorage.setItem('activeSessionIds', JSON.stringify(sessionIds));

            // Restore current session if it matches one from localStorage
            const storedSessionId = localStorage.getItem('currentSessionId');
            if (storedSessionId) {
                const matchingSession = uniqueSessions.find(s => s.session_id === storedSessionId);
                if (matchingSession) {
                    set({
                        currentSession: matchingSession,
                        session: matchingSession,
                        sessionId: storedSessionId,
                    });
                }
            }
        } catch (error: any) {
            // Handle 401 Unauthorized specifically
            if (error.status === 401) {
                console.warn('⚠️ 401 Unauthorized - token may be invalid');
                // Don't clear storage here - let the api interceptor handle it
            } else {
                console.warn('Failed to load sessions (using empty list):', error.message);
            }
            set({ activeSessions: [] });
        }
    },

    createSession: async (data: any): Promise<GameSession> => {
        set({ isLoading: true });
        try {
            const { userId, username } = get();
            // Add owner info to session
            const sessionData = {
                ...data,
                owner_id: userId,
                owner_name: username
            };
            const session = await sessionAPI.createSession(sessionData);
            set({
                currentSession: session,
                sessionId: session.session_id,
                isLoading: false,
            });
            
            // Persist to localStorage immediately for recovery
            localStorage.setItem('currentSessionId', session.session_id);
            localStorage.setItem('currentSessionName', session.session_name);
            
            // Refresh sessions list
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

    connectWebSocket: async (sessionId: string, playerId: string) => {
        try {
            // Check if already connected to this session
            if (webSocketService.isConnected() && 
                webSocketService.getSessionId() === sessionId && 
                webSocketService.getPlayerId() === playerId) {
                console.log(`%c🔌 [${new Date().toLocaleTimeString()}] WEBSOCKET ALREADY CONNECTED - SKIPPING`, 'background: #27ae60; color: white; padding: 4px 8px; border-radius: 3px;');
                return; // Already connected to the same session
            }

            console.log(`%c🔌 [${new Date().toLocaleTimeString()}] CONNECTING TO WEBSOCKET...`, 'background: #3498db; color: white; padding: 4px 8px; border-radius: 3px;');
            console.log(`   Session: ${sessionId}`);
            console.log(`   Player: ${playerId}`);

            // Disconnect any existing connection first (only if different session)
            if (webSocketService.getSessionId() !== sessionId) {
                console.log(`%c🔌 Disconnecting from previous session...`, 'background: #95a5a6; color: white; padding: 4px 8px; border-radius: 3px;');
                webSocketService.disconnect();
            }

            // Connect to WebSocket with message handler
            await webSocketService.connect(sessionId, playerId, (message) => {
                console.log(`%c📨 [${new Date().toLocaleTimeString()}] WEBSOCKET MESSAGE`, 'background: #16a085; color: white; padding: 4px 8px; border-radius: 3px;');
                console.log('   Type:', message.type);
                console.log('   Payload:', message.payload);

                const state = useGameStore.getState();

                // Handle different message types
                switch (message.type) {
                    case 'MASTER_MESSAGE':
                        // DM narration - add to chat
                        const dmMsg = {
                            sender_name: 'DM',
                            text: message.payload?.text || '',
                            type: 'dm',
                            timestamp: new Date().toISOString(),
                        };
                        state.addMessage(dmMsg);
                        state.setIsDMThinking(false);
                        break;

                    case 'GAME_EVENT':
                        // Game event - add to events and chat
                        const event = message.payload?.event;
                        if (event) {
                            state.addEvent(event);
                            
                            // Also add as chat message for visibility
                            const eventMsg = {
                                sender_name: 'Game',
                                text: event.description || `${event.event_type} occurred`,
                                type: 'event',
                                timestamp: new Date().toISOString(),
                                event_type: event.event_type,
                            };
                            state.addMessage(eventMsg);
                        }
                        break;

                    case 'SESSION_UPDATE':
                        // Session state update
                        if (message.payload?.session) {
                            // Update scene if provided
                            if (message.payload.session.current_scene) {
                                state.setCurrentScene(message.payload.session.current_scene);
                            }
                        }
                        break;

                    case 'SCENE_UPDATE':
                        // Scene changed
                        if (message.payload?.scene) {
                            state.setCurrentScene(message.payload.scene);
                        }
                        break;

                    case 'TURN_QUEUE_UPDATE':
                        // Turn queue updated
                        if (message.payload?.turn_queue) {
                            set({ turnQueue: message.payload.turn_queue });
                        }
                        break;

                    case 'ERROR':
                        // Error message
                        console.error('WebSocket error:', message.payload?.message);
                        const errorMsg = {
                            sender_name: 'System',
                            text: message.payload?.message || 'An error occurred',
                            type: 'environment',
                            timestamp: new Date().toISOString(),
                        };
                        state.addMessage(errorMsg);
                        state.setIsDMThinking(false);
                        break;

                    case 'ACTION_RESULT':
                        // Action result from server
                        if (message.payload?.dm_response) {
                            const dmResponse = {
                                sender_name: 'DM',
                                text: message.payload.dm_response,
                                type: 'dm',
                                timestamp: new Date().toISOString(),
                            };
                            state.addMessage(dmResponse);
                        }
                        state.setIsDMThinking(false);
                        break;

                    default:
                        console.log('Unhandled WebSocket message type:', message.type);
                }

                console.log('%c─────────────────────────────────────────────────────', 'color: #16a085;');
            });

            console.log(`%c✅ [${new Date().toLocaleTimeString()}] WEBSOCKET CONNECTED`, 'background: #27ae60; color: white; padding: 4px 8px; border-radius: 3px;');
            console.log('%c─────────────────────────────────────────────────────', 'color: #27ae60;');
        } catch (error) {
            console.error(`%c❌ [${new Date().toLocaleTimeString()}] WEBSOCKET CONNECTION FAILED`, 'background: #e74c3c; color: white; padding: 4px 8px; border-radius: 3px;');
            console.error('   Error:', error);
            console.log('%c─────────────────────────────────────────────────────', 'color: #e74c3c;');
            throw error;
        }
    },

    disconnectWebSocket: () => {
        console.log(`%c🔌 [${new Date().toLocaleTimeString()}] DISCONNECTING WEBSOCKET`, 'background: #95a5a6; color: white; padding: 4px 8px; border-radius: 3px;');
        webSocketService.disconnect();
        console.log('%c─────────────────────────────────────────────────────', 'color: #95a5a6;');
    },

    setCurrentSession: (session) => {
        set({
            currentSession: session,
            session: session, // Also update alias
            sessionId: session?.session_id || null,
        });
        // Persist to localStorage
        if (session?.session_id) {
            localStorage.setItem('currentSessionId', session.session_id);
            localStorage.setItem('currentSessionName', session.session_name);
        } else {
            localStorage.removeItem('currentSessionId');
            localStorage.removeItem('currentSessionName');
        }
    },

    setActiveSessions: (sessions) => {
        set({ activeSessions: sessions });
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
        const traceId = sessionStorage.getItem('current_trace_id');
        console.log('📝 Player action:', actionText);
        console.log('🏷️  Trace ID:', traceId);

        const state = useGameStore.getState();
        const sessionId = localStorage.getItem('currentSessionId') || 'unknown';
        const playerId = localStorage.getItem('currentPlayerId');

        // Log player action flow - sent
        console.log(`%c📤 [${new Date().toLocaleTimeString()}] PLAYER ACTION SENT`, 'background: #3498db; color: white; padding: 4px 8px; border-radius: 3px;');
        console.log(`   Character: ${character.name}`);
        console.log(`   Session: ${sessionId}`);
        console.log(`   Action: ${actionText}`);
        console.log(`   Trace ID: ${traceId}`);
        console.log('%c─────────────────────────────────────────────────────', 'color: #3498db;');

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

        // Send via WebSocket if connected, otherwise fallback to REST
        try {
            if (webSocketService.isConnected() && character) {
                console.log(`%c🌐 [${new Date().toLocaleTimeString()}] SENDING VIA WEBSOCKET...`, 'background: #9b59b6; color: white; padding: 4px 8px; border-radius: 3px;');
                
                // Send action through WebSocket
                webSocketService.sendAction(actionText, character);
                
                console.log(`%c✅ [${new Date().toLocaleTimeString()}] ACTION SENT VIA WEBSOCKET`, 'background: #27ae60; color: white; padding: 4px 8px; border-radius: 3px;');
                console.log('%c─────────────────────────────────────────────────────', 'color: #27ae60;');
            } else {
                console.log(`%c⚠️ [${new Date().toLocaleTimeString()}] WEBSOCKET NOT CONNECTED - USING REST FALLBACK`, 'background: #f39c12; color: white; padding: 4px 8px; border-radius: 3px;');
                
                // Fallback to REST API
                const response = await fetch(`/api/v1/sessions/${sessionId}/action`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Trace-ID': traceId || '',
                        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                    },
                    body: JSON.stringify({
                        character_name: character.name,
                        action: actionText,
                    }),
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();

                console.log(`%c✅ [${new Date().toLocaleTimeString()}] BACKEND RESPONSE RECEIVED (REST)`, 'background: #27ae60; color: white; padding: 4px 8px; border-radius: 3px;');
                console.log(`   Status: ${response.status}`);
                console.log(`   Success: ${data.success}`);
                console.log(`   Events: ${data.events?.length || 0}`);
                console.log(`   DM Response Length: ${data.dm_response?.length || 0}`);
                console.log('%c─────────────────────────────────────────────────────', 'color: #27ae60;');

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

                // Process and display game events
                if (data.events && data.events.length > 0) {
                    console.log(`%c⚡ [${new Date().toLocaleTimeString()}] GAME EVENTS RECEIVED`, 'background: #f39c12; color: white; padding: 4px 8px; border-radius: 3px;');
                    data.events.forEach((event: any, i: number) => {
                        console.log(`   Event ${i+1}: ${event.event_type} - ${event.description}`);
                        state.addEvent(event);

                        const eventMessage = {
                            sender_name: 'Game',
                            text: event.description || `${event.event_type} occurred`,
                            type: 'event',
                            timestamp: new Date().toISOString(),
                            event_type: event.event_type,
                        };
                        state.addMessage(eventMessage);
                    });
                    console.log('%c─────────────────────────────────────────────────────', 'color: #f39c12;');
                }
            }
        } catch (error) {
            console.error(`%c❌ [${new Date().toLocaleTimeString()}] ACTION PROCESSING FAILED`, 'background: #e74c3c; color: white; padding: 4px 8px; border-radius: 3px;');
            console.error('   Error:', error);
            console.error('   Trace ID:', traceId);
            console.log('%c─────────────────────────────────────────────────────', 'color: #e74c3c;');

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
    const sessionName = localStorage.getItem('currentSessionName');
    const playerId = localStorage.getItem('currentPlayerId');
    const gameStatus = localStorage.getItem('gameStatus');
    const activeSessionIds = localStorage.getItem('activeSessionIds');

    if (token && userId && username) {
        useGameStore.setState({
            isAuthenticated: true,
            userId: parseInt(userId),
            username,
            accessToken: token,
        });
    }

    // Restore active session IDs
    if (activeSessionIds) {
        try {
            const ids = JSON.parse(activeSessionIds);
            // Create placeholder sessions that will be refreshed by loadSessions
            const placeholderSessions = ids.map((id: string) => ({
                session_id: id,
                session_name: 'Loading...',
                game_mode: 'STORY',
                player_count: 0,
                max_players: 5,
                status: 'created',
                description: undefined,
            }));
            useGameStore.setState({
                activeSessions: placeholderSessions,
            });
        } catch (e) {
            console.warn('Failed to parse activeSessionIds from localStorage');
        }
    }

    // Restore current session if already joined
    if (sessionId && playerId) {
        const sessionData = {
            session_id: sessionId,
            session_name: sessionName || 'Active Session',
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
