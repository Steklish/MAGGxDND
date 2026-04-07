// Character API service
// 
// UPDATED: Characters are now created through sessions via delivery
// Old endpoints (GET, PUT, DELETE) removed - characters belong to sessions
import api from './api';

export interface CharacterInSession {
    // Character data returned from session
    character_name: string;
    character_class: string;
    character_race: string;
    level: number;
    max_hp: number;
    current_hp: number;
    armor_class: number;
    stats: Record<string, number>;
    abilities: any[];
    inventory: any[];
    success: boolean;
    message: string;
}

export interface CharacterCreateInSessionData {
    session_id: string;
    character_name: string;
    character_prompt: string;  // Description for AI generation
    character_class?: string;
    character_race?: string;
}

// Re-export for backward compatibility (deprecated)
export interface Character {
    id: number;
    user_id: number;
    name: string;
    race: string;
    char_class: string;
    level: number;
    backstory_summary?: string;
    personality_traits?: string;
    max_hp: number;
    current_hp: number;
    armor_class: number;
    speed: number;
    stats: Record<string, number>;
    abilities: any[];
    inventory: any[];
    created_at?: string;
    updated_at?: string;
}

export interface CharacterProfile {
    id: number;
    character_id: number;
    alignment: string;
    deity?: string;
    homeland?: string;
    background?: string;
    appearance_description?: string;
    hit_dice?: string;
    passive_wisdom?: number;
    inspiration?: boolean;
    saving_throws: Record<string, number>;
    skills: Record<string, number>;
    equipment: any[];
    attacks: any[];
    spell_slots: Record<string, number>;
    features_traits: string[];
    notes?: string;
}

export const characterAPI = {
    /**
     * Create a character within a session using delivery
     * 
     * Backend expects:
     * {
     *   session_id: string,
     *   character_name: string,
     *   character_prompt: string,
     *   character_class?: string,
     *   character_race?: string
     * }
     * 
     * Returns:
     * {
     *   success: boolean,
     *   character_name: string,
     *   character_class: string,
     *   character_race: string,
     *   ...
     * }
     */
    createCharacterInSession: async (data: CharacterCreateInSessionData): Promise<CharacterInSession> => {
        const response = await api.post<CharacterInSession>('/characters/', data);
        return response.data;
    },

    /**
     * DEPRECATED: Get character by ID
     * Characters are now retrieved through session game_info endpoint
     * Use: sessionAPI.getGameInfo(sessionId) instead
     */
    getCharacter: async (_characterId: number): Promise<any> => {
        console.warn('getCharacter is deprecated. Use sessionAPI.getGameInfo() instead.');
        throw new Error('Character retrieval not supported. Use session game_info endpoint.');
    },

    /**
     * DEPRECATED: Get all characters for a user
     * Characters belong to sessions, not users directly
     * Use: sessionAPI.listSessions() to get sessions, then getGameInfo() for characters
     */
    getUserCharacters: async (_userId: number): Promise<any[]> => {
        console.warn('getUserCharacters is deprecated. Characters belong to sessions.');
        // Return empty array - will be handled by loading sessions instead
        return [];
    },

    /**
     * DEPRECATED: Update a character
     * Characters are updated through session delivery
     */
    updateCharacter: async (_characterId: number, _data: any): Promise<any> => {
        console.warn('updateCharacter is deprecated. Use session delivery instead.');
        throw new Error('Character update not supported directly. Use session delivery.');
    },

    /**
     * DEPRECATED: Delete a character
     * Characters are managed by session
     */
    deleteCharacter: async (_characterId: number): Promise<void> => {
        console.warn('deleteCharacter is deprecated. Characters managed by session.');
        throw new Error('Character deletion not supported directly. Use session management.');
    },

    /**
     * DEPRECATED: Get character profile
     * Profiles no longer exist as separate entities
     */
    getCharacterProfile: async (_characterId: number): Promise<any> => {
        console.warn('getCharacterProfile is deprecated. Profiles removed from backend.');
        throw new Error('Profile endpoint removed. Character data in session.');
    },

    /**
     * DEPRECATED: Create character profile
     * Profiles no longer exist
     */
    createCharacterProfile: async (_data: any): Promise<any> => {
        console.warn('createCharacterProfile is deprecated. Profiles removed from backend.');
        throw new Error('Profile creation removed. Character data stored in session.');
    },

    /**
     * DEPRECATED: Update character profile
     * Profiles no longer exist
     */
    updateCharacterProfile: async (_characterId: number, _data: any): Promise<any> => {
        console.warn('updateCharacterProfile is deprecated. Profiles removed from backend.');
        throw new Error('Profile update removed. Character data in session.');
    },
};

export default characterAPI;
