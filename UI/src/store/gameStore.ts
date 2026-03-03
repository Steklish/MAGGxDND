import { create } from 'zustand';
import { characterAPI, Character, CharacterProfile } from '../services/characterAPI';
import { sessionAPI, GameSession } from '../services/sessionAPI';
import { Session, Message, Event, SceneNode, NPCCharacter } from '../types/game';

// Demo data for offline/development mode
const demoScene: SceneNode = {
    name: "Slime Cave",
    description: "A dark and eerie cavern where dark slimy worms live. The air is thick with moisture and the sound of dripping water echoes through the tunnels.",
    objects: [
        { name: "Stone Altar", short_summary: "Prop", obj_type: "Prop", quantity: 1, is_equipped: false, position: { x: 10, y: 5 } },
        { name: "Treasure Chest", short_summary: "Container | Locked", obj_type: "Container", quantity: 1, is_equipped: false, is_locked: true, position: { x: 15, y: 12 } },
    ],
    center_position: { x: 10, y: 10 },
    dimensions: { x: 20, y: 20 },
    scale_unit: "feet"
};

const demoCharacter: Character = {
    id: 1,
    user_id: 1,
    name: "Ogorek",
    race: "Human",
    char_class: "Wizard",
    level: 5,
    backstory_summary: "A powerful wizard seeking ancient knowledge",
    personality_traits: '["Curious", "Brave"]',
    max_hp: 30,
    current_hp: 24,
    armor_class: 12,
    speed: 30,
    stats: {
        strength: 8,
        dexterity: 14,
        constitution: 13,
        intelligence: 18,
        wisdom: 12,
        charisma: 10
    },
    abilities: [],
    inventory: []
} as any;

const demoSession: Session = {
    session_name: "demo_session",
    current_scene: demoScene,
    game_mode: "STORY",
    players: [{ character: demoCharacter }],
    npcs: [],
    messages: [
        { sender_name: "DM", text: "Welcome to the Slime Cave! The air is thick and you can hear strange sounds.", type: 'dm' }
    ],
    turn_queue: [[demoCharacter, Date.now() / 1000, Date.now() / 1000 + 10]],
    turn_time: 0,
    current_location_name: "Slime Cave",
    spatial_enabled: true
} as any;

// Combined state for backward compatibility with existing components
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
    
    // Game session state (new API)
    activeSessions: GameSession[];
    currentSession: GameSession | null;
    sessionId: string | null;
    
    // Legacy game state (for existing components)
    session: Session | null;
    currentScene: SceneNode | null;
    messages: Message[];
    events: Event[];
    turnQueue: Array<{ character: string; next_turn: number }>;
    turnTime: number;
    activeCharacter: Character | null;
    isActionPending: boolean;
    clarificationText: string | null;
    
    // UI state
    mode: 'menu' | 'connecting' | 'playing' | 'error' | null;
    error: string | null;
    isLoading: boolean;
    
    // Actions - Auth
    setAuthenticated: (value: boolean) => void;
    setUserId: (id: number) => void;
    setUsername: (name: string) => void;
    setAccessToken: (token: string) => void;
    logout: () => void;
    
    // Actions - Characters
    loadCharacters: (userId: number) => Promise<void>;
    setSelectedCharacter: (character: Character | null) => void;
    createCharacter: (data: any) => Promise<Character>;
    deleteCharacter: (characterId: number) => Promise<void>;
    loadCharacterProfile: (characterId: number) => Promise<CharacterProfile | null>;
    
    // Actions - Sessions
    loadSessions: () => Promise<void>;
    createSession: (data: any) => Promise<GameSession>;
    joinSession: (sessionId: string, playerName: string) => Promise<void>;
    leaveSession: (sessionId: string, playerId: string) => Promise<void>;
    setCurrentSession: (session: GameSession | null) => void;
    
    // Actions - Legacy
    sendAction: (requestText: string, character: Character) => void;
    getMessageType: (senderName: string) => Message['type'];
    setActiveCharacter: (character: Character | null) => void;
    connect: (sessionId: string, playerId: string) => Promise<void>;

    // Actions - UI
    setMode: (mode: 'menu' | 'connecting' | 'playing' | 'error' | null) => void;
    setError: (error: string | null) => void;
    setLoading: (loading: boolean) => void;
}

export const useGameStore = create<GameState>((set, get) => ({
    // Initial state
    isAuthenticated: false,
    userId: null,
    username: null,
    accessToken: null,

    characters: [],
    selectedCharacter: null,
    characterProfiles: new Map(),

    activeSessions: [],
    currentSession: null,
    sessionId: null,

    // Legacy game state (for existing components)
    session: demoSession,
    currentScene: demoScene,
    messages: demoSession.messages,
    events: [],
    turnQueue: [],
    turnTime: 0,
    activeCharacter: demoCharacter,
    isActionPending: false,
    clarificationText: null,

    mode: 'playing',
    error: null,
    isLoading: false,
    
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
            console.error('Failed to load characters:', error);
            set({ isLoading: false });
        }
    },
    
    setSelectedCharacter: (character) => {
        set({ selectedCharacter: character });
        if (character) {
            localStorage.setItem('selectedCharacterId', character.id.toString());
        }
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
            set({ activeSessions: sessions });
        } catch (error: any) {
            console.error('Failed to load sessions:', error);
        }
    },
    
    createSession: async (data) => {
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
    
    leaveSession: async (sessionId, playerId) => {
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
            sessionId: session?.session_id || null,
        });
    },

    // Legacy actions for backward compatibility
    sendAction: (_requestText: string, _character: Character) => {
        // Demo mode - simulate action
        console.log('Demo mode: simulating action');
        set({ isActionPending: true });

        setTimeout(() => {
            const newMessage: Message = {
                sender_name: `DM`,
                text: `You attempt to act... (demo response)`,
                type: 'dm',
            };
            set((state) => ({
                messages: [...state.messages, newMessage],
                isActionPending: false,
            }));
        }, 1000);
    },

    getMessageType: (senderName: string): Message['type'] => {
        if (!senderName) return 'environment';
        if (senderName.startsWith('DM') || senderName === 'Game Master') return 'dm';
        return 'player';
    },

    setActiveCharacter: (character: Character | null) => {
        set({ activeCharacter: character as any });
    },

    connect: async (sessionId: string, playerId: string) => {
        console.log('Connecting to session:', sessionId, playerId);
        set({ mode: 'connecting' });
        // For demo mode, just set playing mode
        setTimeout(() => {
            set({ mode: 'playing', sessionId, error: null });
        }, 500);
    },

    // UI actions
    setMode: (mode) => set({ mode }),
    setError: (error) => set({ error }),
    setLoading: (loading) => set({ isLoading: loading }),
}));

// Initialize store from localStorage
const initStore = () => {
    const token = localStorage.getItem('access_token');
    const userId = localStorage.getItem('userId');
    const username = localStorage.getItem('username');
    
    if (token && userId && username) {
        useGameStore.setState({
            isAuthenticated: true,
            userId: parseInt(userId),
            username,
            accessToken: token,
        });
    }
};

initStore();

export default useGameStore;
