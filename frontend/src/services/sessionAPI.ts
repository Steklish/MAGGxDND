// Session/Game API service
import api from './api';

export interface GameSession {
    session_id: string;
    session_name: string;
    game_mode: string;
    status: string;
    description?: string;
    player_count: number;
    max_players: number;
    created_at?: string;
    updated_at?: string;
    owner_id?: number;
    owner_name?: string;
    // Extended fields for game state
    players?: any[];
    npcs?: any[];
    turn_queue?: any[];
}

// Legacy types for backward compatibility
export interface SessionResponse {
    session_id: string;
    session_name: string;
    game_mode: string;
    player_count: number;
    status: string;
    description?: string;
}

export interface SessionListResponse {
    sessions: SessionResponse[];
    total: number;
}

export interface PlayerResponse {
    player_id: string;
    player_name: string;
    character_name?: string;
    connected: boolean;
}

export interface PlayerInfo {
    player_id: string;
    player_name: string;
    character_name?: string;
    connected: boolean;
}

export interface SessionCreateRequest {
    session_name: string;
    game_mode?: string;
    max_players?: number;
    description?: string;
    guide?: string;
    scene_prompt?: string;
    character_prompts?: string[];
    npc_prompts?: string[];
    gemini_api_key?: string;
    gemini_model?: string;
    owner_id?: number;
    owner_name?: string;
}

export interface SessionStartRequest {
    scene_prompt: string;
    character_prompts: string[];
    npc_prompts: string[];
}

export interface PlayerJoinRequest {
    player_name: string;
    character_name?: string;
    character_prompt?: string;
}

export const sessionAPI = {
    /**
     * Create a new game session
     */
    createSession: async (request: SessionCreateRequest): Promise<GameSession> => {
        const response = await api.post<GameSession>('/sessions', request);
        return response.data;
    },

    /**
     * Get list of all active sessions
     */
    listSessions: async (userId?: number): Promise<{ sessions: GameSession[]; total: number }> => {
        const params = userId ? `?user_id=${userId}` : '';
        const response = await api.get<{ sessions: GameSession[]; total: number }>(`/sessions${params}`);
        return response.data;
    },

    /**
     * Get session info by ID
     */
    getSession: async (sessionId: string): Promise<GameSession> => {
        const response = await api.get<GameSession>(`/sessions/${sessionId}`);
        return response.data;
    },

    /**
     * Delete a session
     */
    deleteSession: async (sessionId: string): Promise<void> => {
        await api.delete(`/sessions/${sessionId}`);
    },

    /**
     * Start a session with initial scene and characters
     */
    startSession: async (sessionId: string, request: SessionStartRequest): Promise<GameSession> => {
        const response = await api.post<GameSession>(`/sessions/${sessionId}/start`, request);
        return response.data;
    },

    /**
     * Join a session as a player
     */
    joinSession: async (sessionId: string, request: PlayerJoinRequest): Promise<PlayerInfo> => {
        const response = await api.post<PlayerInfo>(`/sessions/${sessionId}/players`, request);
        return response.data;
    },

    /**
     * Leave a session
     */
    leaveSession: async (sessionId: string, playerId: string): Promise<void> => {
        await api.delete(`/sessions/${sessionId}/players/${playerId}`);
    },

    /**
     * Get all players in a session
     */
    getSessionPlayers: async (sessionId: string): Promise<PlayerInfo[]> => {
        const response = await api.get<PlayerInfo[]>(`/sessions/${sessionId}/players`);
        return response.data;
    },

    /**
     * Get session info including connected players
     */
    getSessionInfo: async (sessionId: string): Promise<any> => {
        const response = await api.get(`/sessions/${sessionId}/info`);
        return response.data;
    },
};

export default sessionAPI;
