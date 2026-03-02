// API service for REST calls to the MAGGxDND server
import axios from 'axios';

const API_BASE_URL = '/api/v1';

// Create axios instance with default config
const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Session types
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
}

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

export interface PlayerJoinRequest {
    player_name: string;
    character_name?: string;
    character_prompt?: string;
}

export interface PlayerResponse {
    player_id: string;
    player_name: string;
    character_name?: string;
    connected: boolean;
}

export interface SessionStartRequest {
    scene_prompt: string;
    character_prompts: string[];
    npc_prompts: string[];
}

// Session API
export const sessionAPI = {
    /**
     * Create a new game session
     */
    createSession: async (request: SessionCreateRequest): Promise<SessionResponse> => {
        const response = await api.post<SessionResponse>('/sessions', request);
        return response.data;
    },

    /**
     * Get list of all active sessions
     */
    listSessions: async (): Promise<SessionListResponse> => {
        const response = await api.get<SessionListResponse>('/sessions');
        return response.data;
    },

    /**
     * Get session info by ID
     */
    getSession: async (sessionId: string): Promise<SessionResponse> => {
        const response = await api.get<SessionResponse>(`/sessions/${sessionId}`);
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
    startSession: async (
        sessionId: string,
        request: SessionStartRequest
    ): Promise<SessionResponse> => {
        const response = await api.post<SessionResponse>(
            `/sessions/${sessionId}/start`,
            request
        );
        return response.data;
    },

    /**
     * Join a session as a player
     */
    joinSession: async (
        sessionId: string,
        request: PlayerJoinRequest
    ): Promise<PlayerResponse> => {
        const response = await api.post<PlayerResponse>(
            `/sessions/${sessionId}/players`,
            request
        );
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
    getSessionPlayers: async (sessionId: string): Promise<PlayerResponse[]> => {
        const response = await api.get<PlayerResponse[]>(
            `/sessions/${sessionId}/players`
        );
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

// User/Auth API (placeholder for future implementation)
export const userAPI = {
    // TODO: Implement user authentication endpoints
};

export default api;
