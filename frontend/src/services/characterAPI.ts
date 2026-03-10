// Character API service
import api from './api';

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

export interface CharacterCreateData {
    user_id: number;
    name: string;
    race: string;
    char_class: string;
    level?: number;
    backstory_summary?: string;
    personality_traits?: string;
    max_hp: number;
    current_hp: number;
    armor_class: number;
    speed: number;
    stats: Record<string, number>;
    abilities?: any[];
    inventory?: any[];
}

export interface CharacterProfileCreateData {
    character_id: number;
    alignment?: string;
    deity?: string;
    homeland?: string;
    background?: string;
    appearance_description?: string;
    hit_dice?: string;
    passive_wisdom?: number;
    inspiration?: boolean;
    saving_throws?: Record<string, number>;
    skills?: Record<string, number>;
    equipment?: any[];
    attacks?: any[];
    spell_slots?: Record<string, number>;
    features_traits?: string[];
    notes?: string;
}

export const characterAPI = {
    /**
     * Create a new character
     */
    createCharacter: async (data: CharacterCreateData): Promise<Character> => {
        const response = await api.post<Character>('/characters/', data);
        return response.data;
    },

    /**
     * Get character by ID
     */
    getCharacter: async (characterId: number): Promise<Character> => {
        const response = await api.get<Character>(`/characters/${characterId}`);
        return response.data;
    },

    /**
     * Get all characters for a user
     */
    getUserCharacters: async (userId: number): Promise<Character[]> => {
        const response = await api.get<Character[]>(`/characters/user/${userId}`);
        return response.data;
    },

    /**
     * Update a character
     */
    updateCharacter: async (characterId: number, data: Partial<Character>): Promise<Character> => {
        const response = await api.put<Character>(`/characters/${characterId}`, data);
        return response.data;
    },

    /**
     * Delete a character
     */
    deleteCharacter: async (characterId: number): Promise<void> => {
        await api.delete(`/characters/${characterId}`);
    },

    /**
     * Get character profile
     */
    getCharacterProfile: async (characterId: number): Promise<CharacterProfile> => {
        const response = await api.get<CharacterProfile>(`/profiles/character/${characterId}`);
        return response.data;
    },

    /**
     * Create character profile
     */
    createCharacterProfile: async (data: CharacterProfileCreateData): Promise<CharacterProfile> => {
        const response = await api.post<CharacterProfile>('/profiles/', data);
        return response.data;
    },

    /**
     * Update character profile by character ID
     */
    updateCharacterProfile: async (characterId: number, data: Partial<CharacterProfile>): Promise<CharacterProfile> => {
        const response = await api.put<CharacterProfile>(`/profiles/character/${characterId}`, data);
        return response.data;
    },
};

export default characterAPI;
