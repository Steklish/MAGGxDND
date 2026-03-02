// TypeScript types based on schemas/in_game.py and schemas/orchestration.py

// Coordinate2D
export interface Coordinate2D {
    x: number;
    y: number;
}

// Character stats
export interface AbilityScores {
    strength: number;
    dexterity: number;
    constitution: number;
    intelligence: number;
    wisdom: number;
    charisma: number;
}

// Character class enum
export type CharacterClass = 
    | "Peasant" | "Fighter" | "Wizard" | "Rogue" 
    | "Cleric" | "Ranger" | "Paladin" | "Barbarian" | "Bard";

// Damage type
export type DamageType =
    | "Slashing" | "Piercing" | "Bludgeoning"
    | "Fire" | "Cold" | "Lightning" | "Force";

// Condition trigger
export type ConditionTrigger = "End of Round" | "Passive" | "On Action";

// Condition
export interface Condition {
    name: string;
    rounds_remaining: number | null;
    trigger: ConditionTrigger;
    periodic_effect_description: string;
    short_summary: string;
}

// Object type
export type ObjectType = "Prop" | "Container" | "Interactable";

// UnifiedObject (Item)
export interface UnifiedObject {
    id?: string;
    name: string;
    description?: string;
    obj_type?: ObjectType;
    state?: string;
    quantity: number;
    is_equipped: boolean;
    damage_dice?: string;
    damage_type?: DamageType;
    is_locked?: boolean;
    is_hidden?: boolean;
    content?: string[];
    capacity?: number;
    contained_objects?: UnifiedObject[];
    position?: Coordinate2D;
    tags?: string[];
    item_description?: string;
    short_summary: string;
}

// SpellAbility
export interface SpellAbility {
    name: string;
    level: number;
    description: string;
    duration: string;
    damage_dice?: string;
    damage_type?: DamageType;
    healing_dice?: string;
    tags: string[];
    short_summary: string;
}

// Character
export interface Character {
    // Identity
    name: string;
    race: string;
    char_class: CharacterClass;
    level: number;
    backstory_summary: string;
    personality_traits: string[];
    
    // Vitals
    max_hp: number;
    current_hp: number;
    temp_hp: number;
    armor_class: number;
    speed: number;
    
    // Stats
    stats: AbilityScores;
    
    // State
    inventory: UnifiedObject[];
    active_conditions_list: Condition[];
    resources: Record<string, number>;
    position: Coordinate2D;
    abilities: SpellAbility[];
    
    // Computed
    active_conditions: string;
    proficiency_bonus: number;
    is_alive: boolean;
    initiative_bonus: number;
    short_summary: string;
}

// NPCCharacter
export interface NPCCharacter extends Character {
    motivation?: string;
    alignment?: string;
    memory: string;
    current_scene: string;
}

// SceneNode
export interface SceneNode {
    name: string;
    description: string;
    objects: UnifiedObject[];
    center_position: Coordinate2D;
    dimensions: Coordinate2D;
    scale_unit: string;
}

// Event types
export type EventType = 
    | "LOCATION_CHANGE" | "LOCATION_MUTATION" | "LOCATION_STATUS_CHANGE"
    | "OBJECT_TRANSFER" | "ITEM_TRANSFER" | "ITEM_MOVEMENT" | "ITEM_MUTATION"
    | "ITEM_INTERACTION" | "ITEM_PICKUP" | "ITEM_DROP" | "CONTAINER_ACCESS"
    | "CONTAINER_TRANSFER" | "CHARACTER_STATUS_CHANGE" | "CHARACTER_DEATH"
    | "CHARACTER_STATS_UPDATE" | "CHARACTER_MOVEMENT" | "CHARACTER_TRANSFER"
    | "CHARACTER_POSITION_UPDATE" | "ACTION_RESULT" | "CHARACTER_MELEE_ATTACK"
    | "CHARACTER_RANGED_ATTACK" | "SYSTEM";

// Event
export interface Event {
    event_type: EventType;
    event_initiator: string | null;
    event_subject: string | null;
    event_target: string | null;
    description: string;
}

// Message
export interface Message {
    sender_name: string;
    text: string;
    type?: 'dm' | 'player' | 'ally_npc' | 'hostile_npc' | 'neutral_npc' | 'environment';
}

// Game mode
export type GameMode = "STORY" | "COMBAT";

// Turn queue entry
export type TurnQueueEntry = [Character, number, number];

// Session
export interface Session {
    session_name: string;
    current_scene: SceneNode | null;
    game_mode: GameMode;
    players: PlayerEntity[];
    npcs: NPC[];
    messages: Message[];
    turn_queue: TurnQueueEntry[];
    turn_time: number;
    current_location_name: string | null;
    spatial_enabled: boolean;
}

// Player entity (wrapper)
export interface PlayerEntity {
    character: Character;
}

// NPC entity (wrapper)
export interface NPC {
    character: NPCCharacter;
}

// WebSocket message types (Client -> Server)
export interface PlayerActionMessage {
    type: "PLAYER_ACTION";
    payload: {
        player_id: string;
        request_text: string;
        character: Character;
        timestamp: number;
    };
}

export interface ChoosePlayerMessage {
    type: "CHOOSE_PLAYER";
    payload: {
        selected_player_id: string;
    };
}

export interface SubscribeEventsMessage {
    type: "SUBSCRIBE_EVENTS";
    payload: {
        subscriber_id: string;
    };
}

// WebSocket message types (Server -> Client)
export interface MasterMessagePayload {
    type: "MASTER_MESSAGE";
    payload: {
        text: string;
        tag?: string;
    };
}

export interface SessionUpdateMessage {
    type: "SESSION_UPDATE";
    payload: {
        session: Session;
    };
}

export interface GameEventMessage {
    type: "GAME_EVENT";
    payload: {
        event: Event;
    };
}

export interface ActionRequestMessage {
    type: "ACTION_REQUEST";
    payload: {
        character: Character;
    };
}

export interface TurnQueueUpdateMessage {
    type: "TURN_QUEUE_UPDATE";
    payload: {
        turn_queue: Array<{character: string; next_turn: number}>;
        turn_time: number;
    };
}

export interface SceneUpdateMessage {
    type: "SCENE_UPDATE";
    payload: {
        scene: SceneNode;
        characters: Character[];
        npcs: NPCCharacter[];
        objects: UnifiedObject[];
    };
}

export interface ErrorMessage {
    type: "ERROR";
    payload: {
        message: string;
        details?: any;
    };
}

// Union types
export type ClientMessage = PlayerActionMessage | ChoosePlayerMessage | SubscribeEventsMessage;
export type ServerMessage = 
    | MasterMessagePayload 
    | SessionUpdateMessage 
    | GameEventMessage 
    | ActionRequestMessage 
    | TurnQueueUpdateMessage 
    | SceneUpdateMessage 
    | ErrorMessage;
