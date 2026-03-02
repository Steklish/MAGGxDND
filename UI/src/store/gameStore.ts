// Zustand store for game state management
import { create } from 'zustand';
import { 
    Session, Character, Message, Event, 
    SceneNode, NPCCharacter, UnifiedObject,
    ServerMessage, ClientMessage, PlayerActionMessage 
} from '../types/game';

// Game mode for UI
export type UIMode = 'connecting' | 'lobby' | 'playing' | 'error';

// Mock data for demo mode (no server)
const mockCharacters: Character[] = [
    {
        name: "Ogorek",
        race: "Human",
        char_class: "Wizard",
        level: 5,
        backstory_summary: "A powerful wizard seeking ancient knowledge",
        personality_traits: ["Curious", "Brave", "Arcane"],
        max_hp: 30,
        current_hp: 24,
        temp_hp: 0,
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
        inventory: [
            { name: "Staff of Power", short_summary: "Staff | Equipped", is_equipped: true, quantity: 1 },
            { name: "Robes of Protection", short_summary: "Armor | Equipped", is_equipped: true, quantity: 1 },
            { name: "Health Potion", short_summary: "Consumable", is_equipped: false, quantity: 3 }
        ],
        active_conditions_list: [],
        resources: { spell_slots_lvl1: 3, spell_slots_lvl2: 2, spell_slots_lvl3: 1 },
        position: { x: 5, y: 8 },
        abilities: [
            { name: "Fireball", level: 3, description: "Explosion of fire", duration: "Instantaneous", damage_dice: "8d6", damage_type: "Fire", tags: ["aoe"], short_summary: "Fireball: 8d6 Fire" },
            { name: "Magic Missile", level: 1, description: "Magical darts", duration: "Instantaneous", damage_dice: "3d4", damage_type: "Force", tags: [], short_summary: "Magic Missile: 3d4 Force" },
            { name: "Shield", level: 1, description: "Invisible barrier", duration: "1 round", tags: ["defense"], short_summary: "Shield: +5 AC" }
        ],
        active_conditions: "",
        proficiency_bonus: 3,
        is_alive: true,
        initiative_bonus: 19,
        short_summary: "Ogorek the Human Wizard (Lvl 5)"
    },
    {
        name: "Notman",
        race: "Dwarf",
        char_class: "Fighter",
        level: 5,
        backstory_summary: "A seasoned warrior with a mysterious past",
        personality_traits: ["Stoic", "Loyal", "Determined"],
        max_hp: 45,
        current_hp: 38,
        temp_hp: 0,
        armor_class: 18,
        speed: 25,
        stats: {
            strength: 18,
            dexterity: 14,
            constitution: 16,
            intelligence: 10,
            wisdom: 12,
            charisma: 8
        },
        inventory: [
            { name: "Longsword +1", short_summary: "1d8 Slashing | Weapon | Equipped", is_equipped: true, quantity: 1 },
            { name: "Shield", short_summary: "Armor | Equipped", is_equipped: true, quantity: 1 },
            { name: "Chain Mail", short_summary: "Armor | Equipped", is_equipped: true, quantity: 1 }
        ],
        active_conditions_list: [
            { name: "Blessed", rounds_remaining: 5, trigger: "Passive", periodic_effect_description: "Add d4 to attack rolls", short_summary: "[Blessed] 5 rds | Passive: Add d4 to attacks" }
        ],
        resources: { action_surges: 1, second_wind: 1 },
        position: { x: 8, y: 6 },
        abilities: [
            { name: "Action Surge", level: 0, description: "Extra action", duration: "Instantaneous", tags: [], short_summary: "Action Surge: Extra action" },
            { name: "Second Wind", level: 0, description: "Heal yourself", duration: "Instantaneous", healing_dice: "1d10+5", tags: [], short_summary: "Second Wind: Heals 1d10+5" }
        ],
        active_conditions: "[Blessed] 5 rds | Passive: Add d4 to attacks",
        proficiency_bonus: 3,
        is_alive: true,
        initiative_bonus: 19,
        short_summary: "Notman the Dwarf Fighter (Lvl 5)"
    }
];

const mockNPCs: NPCCharacter[] = [
    {
        name: "Worm",
        race: "Aberration",
        char_class: "Peasant",
        level: 2,
        backstory_summary: "An evil worm lurking in the darkness",
        personality_traits: ["Evil", "Cunning"],
        max_hp: 15,
        current_hp: 12,
        temp_hp: 0,
        armor_class: 11,
        speed: 20,
        stats: {
            strength: 6,
            dexterity: 12,
            constitution: 10,
            intelligence: 8,
            wisdom: 10,
            charisma: 4
        },
        inventory: [],
        active_conditions_list: [],
        resources: {},
        position: { x: 12, y: 10 },
        abilities: [],
        active_conditions: "",
        proficiency_bonus: 2,
        is_alive: true,
        initiative_bonus: 16,
        short_summary: "Worm the Aberration Peasant (Lvl 2)",
        motivation: "Spread corruption",
        alignment: "Chaotic Evil",
        memory: "",
        current_scene: "Slime Cave"
    }
];

const mockScene: SceneNode = {
    name: "Slime Cave",
    description: "A dark and eerie cavern where dark slimy worms live. The air is thick with moisture and the sound of dripping water echoes through the tunnels. Bioluminescent fungi provide dim blue lighting.",
    objects: [
        { name: "Stone Altar", short_summary: "Prop", obj_type: "Prop", quantity: 1, is_equipped: false, position: { x: 10, y: 5 }, tags: ["ancient", "mysterious"] },
        { name: "Treasure Chest", short_summary: "Container | Locked", obj_type: "Container", quantity: 1, is_equipped: false, is_locked: true, position: { x: 15, y: 12 }, tags: ["treasure"] },
        { name: "Torch", short_summary: "Prop", obj_type: "Prop", quantity: 1, is_equipped: false, position: { x: 3, y: 3 }, tags: ["light"] }
    ],
    center_position: { x: 10, y: 10 },
    dimensions: { x: 20, y: 20 },
    scale_unit: "feet"
};

const mockMessages: Message[] = [
    { sender_name: "DM", text: "Welcome to the Slime Cave! The air is thick and you can hear strange sounds echoing from the depths.", type: 'dm' },
    { sender_name: "Ogorek", text: "I cast Detect Magic to sense any magical auras in this cave.", type: 'player' },
    { sender_name: "DM", text: "You sense a faint magical aura emanating from the stone altar in the center of the cave.", type: 'dm' },
    { sender_name: "Notman", text: "I approach the altar cautiously, shield raised.", type: 'player' },
    { sender_name: "Worm", text: "*hisses menacingly from the darkness*", type: 'hostile_npc' },
];

const mockEvents: Event[] = [
    { event_type: "CHARACTER_MOVEMENT", event_initiator: "Ogorek", event_subject: "Ogorek", event_target: "Slime Cave", description: "Ogorek enters the Slime Cave" },
    { event_type: "CHARACTER_MOVEMENT", event_initiator: "Notman", event_subject: "Notman", event_target: "Slime Cave", description: "Notman enters the Slime Cave" },
    { event_type: "ACTION_RESULT", event_initiator: "Ogorek", event_subject: "Ogorek", description: "Ogorek casts Detect Magic" },
];

const mockSession: Session = {
    session_name: "demo_session",
    current_scene: mockScene,
    game_mode: "STORY",
    players: mockCharacters.map(c => ({ character: c })),
    npcs: mockNPCs.map(n => ({ character: n })),
    messages: mockMessages,
    turn_queue: mockCharacters.map((c, i) => [c as any, Date.now() / 1000, Date.now() / 1000 + i * 10]),
    turn_time: 0,
    current_location_name: "Slime Cave",
    spatial_enabled: true
};

interface GameState {
    // Connection state
    mode: UIMode;
    websocket: WebSocket | null;
    sessionId: string | null;
    playerId: string | null;

    // Authentication state
    isAuthenticated: boolean;

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
    getMessageType: (senderName: string) => Message['type'];
    setAuthenticated: (authenticated: boolean) => void;
}

// Helper function to determine message type based on sender
function getMessageType(senderName: string, state: any): Message['type'] {
    if (!senderName) return 'environment';
    
    // DM messages
    if (senderName.startsWith('DM') || senderName === 'Game Master') return 'dm';
    
    // Check if sender is a player character
    const players = state.session?.players || [];
    for (const p of players) {
        if (p.character.name === senderName) return 'player';
    }
    
    // Check if sender is an NPC
    const npcs = state.session?.npcs || [];
    for (const n of npcs) {
        if (n.character.name === senderName) {
            const alignment = n.character.alignment || '';
            if (alignment.includes('Good')) return 'ally_npc';
            if (alignment.includes('Evil') || alignment.includes('Chaotic')) return 'hostile_npc';
            return 'neutral_npc';
        }
    }
    
    // Default to environment for unknown senders
    return 'environment';
}

export const useGameStore = create<GameState>((set, get) => ({
    // Initial state - use mock data for demo
    mode: 'playing',  // Start in playing mode for demo
    websocket: null,
    sessionId: 'demo_session',
    playerId: 'Ogorek',
    isAuthenticated: false,  // Start unauthenticated
    session: mockSession,
    currentScene: mockScene,
    messages: mockMessages,
    events: mockEvents,
    turnQueue: mockSession.turn_queue.map(([char, _, nt]) => ({
        character: (char as any).name,
        next_turn: nt
    })),
    turnTime: 0,
    activeCharacter: mockCharacters[0],  // Start with first character selected
    isActionPending: false,
    clarificationText: null,
    error: null,

    connect: (sessionId: string, playerId: string) => {
        // Demo mode - just load mock data
        console.log('Demo mode: connecting with mock data');
        set({ 
            mode: 'playing', 
            sessionId, 
            playerId,
            session: mockSession,
            currentScene: mockScene,
            messages: mockMessages,
            events: mockEvents,
            turnQueue: mockSession.turn_queue.map(([char, _, nt]) => ({
                character: (char as any).name,
                next_turn: nt
            })),
            activeCharacter: mockCharacters.find(c => c.name === playerId) || mockCharacters[0],
            error: null 
        });

        /* WebSocket code commented out for demo
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
        */
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
        // Demo mode - simulate action
        console.log('Demo action:', requestText);
        set({ isActionPending: true });

        // Simulate GM response after delay
        setTimeout(() => {
            const newMessage: Message = {
                sender_name: `DM`,
                text: `You attempt to ${requestText.toLowerCase()}... (demo response)`
            };
            const newEvent: Event = {
                event_type: "ACTION_RESULT",
                event_initiator: character.name,
                event_subject: character.name,
                description: `${character.name} attempts to ${requestText.toLowerCase()}`
            };
            set(state => ({
                messages: [...state.messages, newMessage],
                events: [...state.events, newEvent],
                isActionPending: false
            }));
        }, 1000);

        /* WebSocket code for later
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
        */
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

    getMessageType: (senderName: string) => {
        return getMessageType(senderName, get());
    },

    setAuthenticated: (authenticated: boolean) => {
        set({ isAuthenticated: authenticated });
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
                        text: message.payload.text,
                        type: 'dm'
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
