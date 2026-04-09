// API service for REST calls to the MAGGxDND server
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios';
import { 
    getTraceId, 
    setTraceId, 
    logRequest, 
    logResponse, 
    logError, 
    TRACE_STYLES,
    logJourneyStart,
    logJourneyStage,
    logJourneyComplete
} from '../utils/requestLogger';

// Use relative path - API will be served from the same origin
const API_BASE_URL = '/api/v1';

// Request timing map
const requestTimings = new Map<string, number>();

// Journey tracking map
const journeyStartTimes = new Map<string, number>();

// Custom error types
export class APIError extends Error {
    constructor(
        public status: number,
        public message: string,
        public code?: string,
        public details?: any
    ) {
        super(message);
        this.name = 'APIError';
    }
}

export class NetworkError extends Error {
    constructor(message: string) {
        super(message);
        this.name = 'NetworkError';
    }
}

// Create axios instance with default config
const api: AxiosInstance = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 30000, // 30 second timeout
});

// Request interceptor to add auth token and log requests
api.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        const startTime = Date.now();
        const traceId = getTraceId();

        // Add trace ID to headers
        if (config.headers) {
            config.headers['X-Trace-ID'] = traceId;
        }

        // Add auth token
        const token = localStorage.getItem('access_token');
        if (token && config.headers) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        // Store start time for this request
        const requestKey = `${config.method}:${config.url}`;
        requestTimings.set(requestKey, startTime);
        
        // Store journey start time
        journeyStartTimes.set(requestKey, startTime);

        // Log journey start for important actions
        if (config.method === 'POST' || config.method === 'PUT') {
            logJourneyStart(
                `${config.method} ${config.url}`,
                'Initiating request from frontend to backend'
            );
            logJourneyStage(1, 'Frontend → Backend API', 'Request prepared and sending', config.data);
        }

        // Log the request using our logging utility
        logRequest(
            config.method?.toUpperCase() || 'UNKNOWN',
            `${config.baseURL || ''}${config.url}`,
            config.data,
            config.headers as Record<string, string> | undefined
        );

        // Visual separator
        console.log('%c─────────────────────────────────────────────────────', 'color: #3498db;');

        return config;
    },
    (error) => {
        console.error('%c ❌ Request Interceptor Error:', TRACE_STYLES.error, error);
        return Promise.reject(error);
    }
);

// Response interceptor for error handling and logging
api.interceptors.response.use(
    (response: AxiosResponse) => {
        const requestKey = `${response.config.method}:${response.config.url}`;
        const startTime = requestTimings.get(requestKey);
        const duration = startTime ? Date.now() - startTime : 0;
        const traceId = response.headers['x-trace-id'] || getTraceId();
        const journeyStartTime = journeyStartTimes.get(requestKey);
        const totalDuration = journeyStartTime ? Date.now() - journeyStartTime : 0;

        // Log successful response using our logging utility
        logResponse(
            response.config.method?.toUpperCase() || 'UNKNOWN',
            response.config.url || 'unknown',
            response.status,
            response.data,
            response.headers as Record<string, string> | undefined
        );

        // Log journey stage 5 (complete)
        if (response.config.method === 'POST' || response.config.method === 'PUT') {
            logJourneyStage(5, 'Response → Frontend', `Response received (${response.status})`, response.data);
            logJourneyComplete(
                `${response.config.method} ${response.config.url}`,
                totalDuration,
                [
                    'Frontend → Backend API',
                    'Backend API → Core Engine',
                    'Core Engine Processing',
                    'Core Engine → Event Pool → WebSocket',
                    'WebSocket → Frontend'
                ]
            );
        }

        // Clean up timing
        requestTimings.delete(requestKey);
        journeyStartTimes.delete(requestKey);

        return response;
    },
    (error: AxiosError) => {
        const requestKey = error.config ? `${error.config.method}:${error.config.url}` : 'unknown';
        const startTime = requestTimings.get(requestKey);
        const duration = startTime ? Date.now() - startTime : 0;
        const traceId = error.response?.headers?.['x-trace-id'] || getTraceId();
        const journeyStartTime = journeyStartTimes.get(requestKey);
        const totalDuration = journeyStartTime ? Date.now() - journeyStartTime : 0;

        // Handle network errors
        if (!error.response) {
            console.error(`%c ❌ [NETWORK ERROR] ${error.message}`, TRACE_STYLES.error);
            console.error(`%c Trace ID: ${traceId}`, TRACE_STYLES.trace);
            console.error(`%c This usually means the server is unreachable or there's a network issue`, TRACE_STYLES.error);
            // Log journey error
            if (error.config && (error.config.method === 'POST' || error.config.method === 'PUT')) {
                logJourneyStage(1, 'Network Error', 'Failed to reach backend', error.message);
                logJourneyComplete(`${error.config.method} ${error.config.url}`, totalDuration, ['Frontend → Backend API (FAILED)']);
            }
            throw new NetworkError(
                'Unable to connect to server. Please check your connection.'
            );
        }

        // Log error response using our logging utility
        logError(
            error.config?.method?.toUpperCase() || 'UNKNOWN',
            error.config?.url || 'unknown',
            error.response.status,
            error.response.data,
            error.response.headers as Record<string, string> | undefined
        );

        // Log journey error
        if (error.config && (error.config.method === 'POST' || error.config.method === 'PUT')) {
            logJourneyStage(5, 'Error Response', `Error ${error.response.status}`, error.response.data);
            logJourneyComplete(`${error.config.method} ${error.config.url}`, totalDuration, [
                'Frontend → Backend API',
                'Backend API → Core Engine',
                'Core Engine Processing',
                'Core Engine → Event Pool → WebSocket',
                'WebSocket → Frontend (ERROR)'
            ]);
        }

        // Clean up timing
        requestTimings.delete(requestKey);
        journeyStartTimes.delete(requestKey);

        // Handle specific status codes
        const status = error.response.status;
        const data = error.response.data as any;

        let message = 'An unexpected error occurred';
        if (typeof data === 'string') {
            message = data;
        } else if (data?.detail) {
            message = data.detail;
        } else if (data?.message) {
            message = data.message;
        }

        switch (status) {
            case 401:
                console.warn('⚠️ 401 Unauthorized - clearing auth and cookies, redirecting to landing');
                // Clear localStorage
                localStorage.removeItem('access_token');
                localStorage.removeItem('userId');
                localStorage.removeItem('username');
                localStorage.removeItem('is_guest');
                localStorage.removeItem('remember_me');
                localStorage.removeItem('currentSessionId');
                localStorage.removeItem('currentPlayerId');
                localStorage.removeItem('gameStatus');
                localStorage.removeItem('guest_token');
                // Clear auth cookies
                document.cookie = 'access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
                document.cookie = 'guest_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
                message = 'Session expired. Please log in again.';
                // Notify App.tsx to reset state to landing page
                window.dispatchEvent(new CustomEvent('auth:invalid'));
                break;
            case 403:
                message = 'You do not have permission to perform this action.';
                break;
            case 404:
                message = 'The requested resource was not found.';
                break;
            case 429:
                message = 'Too many requests. Please try again later.';
                break;
            case 500:
                message = 'Server error. Please try again later.';
                break;
            case 503:
                message = 'Service unavailable. Please try again later.';
                break;
        }

        throw new APIError(
            status,
            message,
            (data as any)?.error_code,
            data
        );
    }
);

// Re-export from sessionAPI for backward compatibility
export type {
    SessionCreateRequest as SessionCreateRequestType,
    PlayerJoinRequest as PlayerJoinRequestType,
    SessionStartRequest as SessionStartRequestType,
} from './sessionAPI';

export { sessionAPI } from './sessionAPI';

// Session types (legacy - use sessionAPI instead)
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

// Legacy sessionAPI - use sessionAPI from './sessionAPI' instead
// Kept for backward compatibility
export const legacySessionAPI = {
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
