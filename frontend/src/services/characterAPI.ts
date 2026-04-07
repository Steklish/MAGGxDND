// Character API service
//
// Supports two types of character operations:
// 1. Character Profiles - User's saved character templates (reusable across sessions)
// 2. In-Session Characters - Characters created for specific game sessions

import api from './api';

// ===================================================================
// CHARACTER PROFILES (Saved Templates)
// ===================================================================

export interface CharacterProfile {
    id: number;
    user_id: number;
    name: string;
    race: string;
    char_class: string;
    level: number;
    backstory_summary?: string;
    personality_traits?: string[];
    appearance_description?: string;
    background?: string;
    alignment?: string;
    max_hp: number;
    armor_class: number;
    speed: number;
    is_favorite: boolean;
    character_data?: Record<string, any>;
    created_at: string;
    updated_at: string;
}

export interface CharacterProfileCreate {
    name: string;
    race?: string;
    char_class: string;
    level?: number;
    character_data?: Record<string, any>;
    backstory_summary?: string;
    personality_traits?: string[];
    appearance_description?: string;
    background?: string;
    alignment?: string;
    max_hp?: number;
    armor_class?: number;
    speed?: number;
    is_favorite?: boolean;
}

export interface CharacterProfileUpdate {
    name?: string;
    backstory_summary?: string;
    appearance_description?: string;
    is_favorite?: boolean;
    character_data?: Record<string, any>;
}

export interface CharacterProfileListResponse {
    profiles: CharacterProfile[];
    total: number;
}

// Character Profile Endpoints
export const characterProfileAPI = {
    /**
     * Save a character profile for future use
     */
    async createProfile(data: CharacterProfileCreate): Promise<CharacterProfile> {
        const response = await api.post('/characters/', data);
        return response.data;
    },

    /**
     * List all saved character profiles for the current user
     */
    async listProfiles(skip = 0, limit = 50): Promise<CharacterProfileListResponse> {
        const response = await api.get('/characters/', { params: { skip, limit } });
        return response.data;
    },

    /**
     * Get a specific character profile
     */
    async getProfile(profileId: number): Promise<CharacterProfile> {
        const response = await api.get(`/characters/${profileId}`);
        return response.data;
    },

    /**
     * Update a character profile
     */
    async updateProfile(profileId: number, data: CharacterProfileUpdate): Promise<CharacterProfile> {
        const response = await api.put(`/characters/${profileId}`, data);
        return response.data;
    },

    /**
     * Delete a character profile
     */
    async deleteProfile(profileId: number): Promise<void> {
        await api.delete(`/characters/${profileId}`);
    }
};

// ===================================================================
// IN-SESSION CHARACTERS (Game Session Characters)
// ===================================================================

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
     * Use characterProfileAPI.getProfile() instead
     */
    getCharacterProfile: async (profileId: number): Promise<CharacterProfile> => {
        console.warn('getCharacterProfile is deprecated. Use characterProfileAPI.getProfile() instead.');
        return characterProfileAPI.getProfile(profileId);
    },

    /**
     * DEPRECATED: Create character profile
     * Use characterProfileAPI.createProfile() instead
     */
    createCharacterProfile: async (data: CharacterProfileCreate): Promise<CharacterProfile> => {
        console.warn('createCharacterProfile is deprecated. Use characterProfileAPI.createProfile() instead.');
        return characterProfileAPI.createProfile(data);
    },

    /**
     * DEPRECATED: Update character profile
     * Use characterProfileAPI.updateProfile() instead
     */
    updateCharacterProfile: async (profileId: number, data: CharacterProfileUpdate): Promise<CharacterProfile> => {
        console.warn('updateCharacterProfile is deprecated. Use characterProfileAPI.updateProfile() instead.');
        return characterProfileAPI.updateProfile(profileId, data);
    },
};

export default characterAPI;
