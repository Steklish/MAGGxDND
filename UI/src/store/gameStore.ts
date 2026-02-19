// Zustand store for game state management
import { create } from 'zustand';
import { 
    Session, Character, Message, Event, 
    SceneNode, NPCCharacter, UnifiedObject,
    ServerMessage, ClientMessage, PlayerActionMessage 
} from '../types/game';

// Game mode for UI
export type UIMode = 'connecting' | 'lobby' | 'playing' | 'error';

interface GameState {
    // Connection state
    mode: UIMode;
    websocket: WebSocket | null;
    sessionId: string | null;
    playerId: string | null;
    
    // Game state
    session: Session | null;
    currentScene: SceneNode | null;
    messages: Message[];
    events: Event[];
    turnQueue: Array<{character: string; next_turn: number}>;
    turnTime: number;
    activeCharacter: Character | null;
    
    // UI state
    isActionPending: boolean;
    clarificationText: string | null;
    error: string | null;
    
    // Actions
    connect: (sessionId: string, playerId: string) => void;
    disconnect: () => void;
    sendAction: (requestText: string, character: Character) => void;
    choosePlayer: (playerId: string) => void;
    setActiveCharacter: (character: Character | null) => void;
    clearError: () => void;
}

export const useGameStore = create<GameState>((set, get) => ({
    // Initial state
    mode: 'connecting',
    websocket: null,
    sessionId: null,
    playerId: null,
    session: null,
    currentScene: null,
    messages: [],
    events: [],
    turnQueue: [],
    turnTime: 0,
    activeCharacter: null,
    isActionPending: false,
    clarificationText: null,
    error: null,

    connect: (sessionId: string, playerId: string) => {
        const wsUrl = `ws://localhost:8000/ws/${sessionId}/${playerId}`;
        const websocket = new WebSocket(wsUrl);

        websocket.onopen = () => {
            console.log('WebSocket connected');
            set({ 
                mode: 'playing', 
                sessionId, 
                playerId, 
                websocket,
                error: null 
            });

            // Subscribe to events
            const subscribeMsg: ClientMessage = {
                type: 'SUBSCRIBE_EVENTS',
                payload: { subscriber_id: playerId }
            };
            websocket.send(JSON.stringify(subscribeMsg));
        };

        websocket.onmessage = (event) => {
            try {
                const message: ServerMessage = JSON.parse(event.data);
                get().handleServerMessage(message);
            } catch (e) {
                console.error('Failed to parse message:', e);
            }
        };

        websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            set({ mode: 'error', error: 'Connection error' });
        };

        websocket.onclose = () => {
            console.log('WebSocket closed');
            set({ mode: 'error', error: 'Connection closed' });
        };
    },

    disconnect: () => {
        const { websocket } = get();
        if (websocket) {
            websocket.close();
        }
        set({
            websocket: null,
            mode: 'connecting',
            sessionId: null,
            playerId: null,
            session: null,
            currentScene: null,
            messages: [],
            events: [],
            turnQueue: [],
            turnTime: 0,
            activeCharacter: null,
        });
    },

    sendAction: (requestText: string, character: Character) => {
        const { websocket, playerId } = get();
        if (!websocket || !playerId) {
            set({ error: 'Not connected to server' });
            return;
        }

        const actionMsg: PlayerActionMessage = {
            type: 'PLAYER_ACTION',
            payload: {
                player_id: playerId,
                request_text: requestText,
                character: character,
                timestamp: Date.now() / 1000
            }
        };

        websocket.send(JSON.stringify(actionMsg));
        set({ isActionPending: true, clarificationText: null });
    },

    choosePlayer: (playerId: string) => {
        const { websocket } = get();
        if (!websocket) {
            set({ error: 'Not connected to server' });
            return;
        }

        const chooseMsg: ClientMessage = {
            type: 'CHOOSE_PLAYER',
            payload: { selected_player_id: playerId }
        };

        websocket.send(JSON.stringify(chooseMsg));
    },

    setActiveCharacter: (character: Character | null) => {
        set({ activeCharacter: character });
    },

    clearError: () => {
        set({ error: null });
    },

    // Internal method to handle server messages
    handleServerMessage: (message: ServerMessage) => {
        const state = get();

        switch (message.type) {
            case 'SESSION_UPDATE':
                set({
                    session: message.payload.session,
                    currentScene: message.payload.session.current_scene,
                    messages: message.payload.session.messages,
                    turnQueue: message.payload.session.turn_queue.map(([char, _, nt]) => ({
                        character: char.name,
                        next_turn: nt
                    })),
                    turnTime: message.payload.session.turn_time,
                });
                break;

            case 'MASTER_MESSAGE':
                set({
                    messages: [...state.messages, {
                        sender_name: `DM ${message.payload.tag || ''}`,
                        text: message.payload.text
                    }],
                    isActionPending: message.payload.tag === 'Clarification' || message.payload.tag === 'Illegal' ? false : state.isActionPending,
                    clarificationText: message.payload.tag === 'Clarification' ? message.payload.text : state.clarificationText,
                });
                break;

            case 'GAME_EVENT':
                set({
                    events: [...state.events, message.payload.event]
                });
                break;

            case 'ACTION_REQUEST':
                set({
                    activeCharacter: message.payload.character,
                    isActionPending: false,
                    clarificationText: null,
                });
                break;

            case 'TURN_QUEUE_UPDATE':
                set({
                    turnQueue: message.payload.turn_queue,
                    turnTime: message.payload.turn_time
                });
                break;

            case 'SCENE_UPDATE':
                set({
                    currentScene: message.payload.scene
                });
                break;

            case 'ERROR':
                set({
                    error: message.payload.message,
                    mode: 'error'
                });
                break;
        }
    },
}));
