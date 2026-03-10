// WebSocket service for real-time communication with the MAGGxDND server
import type {
    ServerMessage,
    ClientMessage,
    PlayerActionMessage,
    Session,
    Character,
    Event,
} from '../types/game';

export type WebSocketMessageHandler = (message: ServerMessage) => void;
export type WebSocketStateHandler = (state: {
    connected: boolean;
    error?: string;
}) => void;

export interface WebSocketConfig {
    maxReconnectAttempts?: number;
    reconnectDelay?: number;
    reconnectBackoffMultiplier?: number;
    heartbeatInterval?: number;
}

export class WebSocketService {
    private ws: WebSocket | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts: number;
    private reconnectDelay: number;
    private reconnectBackoffMultiplier: number;
    private messageHandlers: WebSocketMessageHandler[] = [];
    private stateHandlers: WebSocketStateHandler[] = [];
    private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
    private sessionId: string | null = null;
    private playerId: string | null = null;
    private connectionPromise: Promise<void> | null = null;
    private isManualDisconnect = false;
    private config: WebSocketConfig;

    constructor(config: WebSocketConfig = {}) {
        this.config = {
            maxReconnectAttempts: config.maxReconnectAttempts ?? 5,
            reconnectDelay: config.reconnectDelay ?? 1000,
            reconnectBackoffMultiplier: config.reconnectBackoffMultiplier ?? 2,
            heartbeatInterval: config.heartbeatInterval ?? 30000,
        };
        this.maxReconnectAttempts = this.config.maxReconnectAttempts!;
        this.reconnectDelay = this.config.reconnectDelay!;
        this.reconnectBackoffMultiplier = this.config.reconnectBackoffMultiplier!;
    }

    /**
     * Connect to the game WebSocket
     */
    connect(
        sessionId: string,
        playerId: string,
        onMessage?: WebSocketMessageHandler,
        onStateChange?: WebSocketStateHandler
    ): Promise<void> {
        this.sessionId = sessionId;
        this.playerId = playerId;
        this.reconnectAttempts = 0;
        this.isManualDisconnect = false;

        if (onMessage) {
            this.addMessageHandler(onMessage);
        }
        if (onStateChange) {
            this.addStateHandler(onStateChange);
        }

        this.connectionPromise = new Promise((resolve, reject) => {
            // Determine WebSocket URL based on current location
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/${sessionId}/${playerId}`;
            console.log('[WebSocket] Connecting to:', wsUrl);

            try {
                this.ws = new WebSocket(wsUrl);

                this.ws.onopen = () => {
                    console.log('[WebSocket] ✓ Connected to', wsUrl);
                    this.reconnectAttempts = 0;
                    this.notifyStateChange({ connected: true });
                    this.startHeartbeat();
                    resolve();
                };

                this.ws.onclose = (event) => {
                    console.log('[WebSocket] ✗ Disconnected:', event.code, event.reason || 'No reason');
                    this.stopHeartbeat();
                    this.notifyStateChange({ connected: false });

                    // Only attempt reconnect if not manually disconnected
                    if (!this.isManualDisconnect && this.reconnectAttempts < this.maxReconnectAttempts && this.sessionId) {
                        this.attemptReconnect();
                    } else if (this.isManualDisconnect) {
                        console.log('[WebSocket] Manual disconnect, skipping reconnect');
                    }
                };

                this.ws.onerror = (error) => {
                    console.error('[WebSocket] Error:', error);
                    this.notifyStateChange({ connected: false, error: 'Connection error' });
                    // Don't reject here, let onclose handle reconnect
                };

                this.ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        console.log('[WebSocket] ← Received:', data.type, data);
                        this.handleMessage(data);
                    } catch (err) {
                        console.error('[WebSocket] Failed to parse message:', err);
                    }
                };
            } catch (error) {
                console.error('[WebSocket] Failed to create connection:', error);
                reject(error);
            }
        });

        return this.connectionPromise;
    }

    /**
     * Disconnect from the WebSocket
     */
    disconnect(): void {
        console.log('[WebSocket] Disconnecting...');
        this.isManualDisconnect = true;
        this.maxReconnectAttempts = 0; // Prevent reconnect

        this.stopHeartbeat();

        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        if (this.ws) {
            this.ws.close(1000, 'Client disconnect');
            this.ws = null;
        }

        this.sessionId = null;
        this.playerId = null;
        this.messageHandlers = [];
        this.stateHandlers = [];
    }

    /**
     * Add a message handler
     */
    addMessageHandler(handler: WebSocketMessageHandler): void {
        if (!this.messageHandlers.includes(handler)) {
            this.messageHandlers.push(handler);
        }
    }

    /**
     * Remove a message handler
     */
    removeMessageHandler(handler: WebSocketMessageHandler): void {
        this.messageHandlers = this.messageHandlers.filter(h => h !== handler);
    }

    /**
     * Add a state handler
     */
    addStateHandler(handler: WebSocketStateHandler): void {
        if (!this.stateHandlers.includes(handler)) {
            this.stateHandlers.push(handler);
        }
    }

    /**
     * Remove a state handler
     */
    removeStateHandler(handler: WebSocketStateHandler): void {
        this.stateHandlers = this.stateHandlers.filter(h => h !== handler);
    }

    /**
     * Send a player action to the server
     */
    sendAction(requestText: string, character: Character): void {
        if (!this.ws || !this.playerId) {
            console.error('[WebSocket] Cannot send action: not connected');
            return;
        }

        const actionMsg: PlayerActionMessage = {
            type: 'PLAYER_ACTION',
            payload: {
                player_id: this.playerId,
                request_text: requestText,
                character: character,
                timestamp: Date.now() / 1000,
            },
        };

        this.send(actionMsg);
    }

    /**
     * Send a generic client message
     */
    send(message: ClientMessage): void {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.error('[WebSocket] Cannot send message: not connected or not ready');
            return;
        }

        console.log('[WebSocket] → Sending:', message.type, message);
        this.ws.send(JSON.stringify(message));
    }

    /**
     * Check if connected
     */
    isConnected(): boolean {
        return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
    }

    /**
     * Get current session ID
     */
    getSessionId(): string | null {
        return this.sessionId;
    }

    /**
     * Get current player ID
     */
    getPlayerId(): string | null {
        return this.playerId;
    }

    /**
     * Attempt to reconnect with exponential backoff
     */
    private attemptReconnect(): void {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('[WebSocket] Max reconnect attempts reached');
            this.notifyStateChange({
                connected: false,
                error: 'Connection lost. Please refresh the page.',
            });
            return;
        }

        const delay = this.reconnectDelay * Math.pow(this.reconnectBackoffMultiplier, this.reconnectAttempts);
        console.log(
            `[WebSocket] Attempting reconnect ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts} in ${delay}ms`
        );

        this.reconnectTimer = setTimeout(() => {
            this.reconnectAttempts++;
            if (this.sessionId && this.playerId) {
                this.connect(this.sessionId, this.playerId);
            }
        }, delay);
    }

    /**
     * Start heartbeat to keep connection alive
     */
    private startHeartbeat(): void {
        this.stopHeartbeat(); // Clear existing heartbeat
        this.heartbeatTimer = setInterval(() => {
            if (this.isConnected()) {
                // Send ping message to keep connection alive
                this.send({ type: 'PING', payload: { timestamp: Date.now() } } as unknown as ClientMessage);
            }
        }, this.config.heartbeatInterval);
    }

    /**
     * Stop heartbeat
     */
    private stopHeartbeat(): void {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    /**
     * Handle incoming WebSocket messages
     */
    private handleMessage(data: any): void {
        // Convert server message format to our internal format
        const serverMessage = this.parseServerMessage(data);
        if (serverMessage) {
            this.messageHandlers.forEach((handler) => handler(serverMessage));
        }
    }

    /**
     * Parse server message to our internal format
     */
    private parseServerMessage(data: any): ServerMessage | null {
        console.log('[WebSocket] Parsing message type:', data.type);

        // Handle different message types from the server
        switch (data.type) {
            case 'CONNECTED':
                console.log('[WebSocket] ✓ Connection confirmed');
                return null;

            case 'MASTER_MESSAGE':
                console.log('[WebSocket] Master message received');
                return {
                    type: 'MASTER_MESSAGE',
                    payload: {
                        text: data.payload?.text || data.text || '',
                        tag: data.payload?.tag || data.tag,
                    },
                };

            case 'SESSION_UPDATE':
                console.log('[WebSocket] Session update received');
                return {
                    type: 'SESSION_UPDATE',
                    payload: {
                        session: data.payload?.session || data.data || data.session || {},
                    },
                };

            case 'TURN_QUEUE_UPDATE':
                console.log('[WebSocket] Turn update received');
                return {
                    type: 'TURN_QUEUE_UPDATE',
                    payload: {
                        turn_queue: data.payload?.turn_queue || data.turn_queue || [],
                        turn_time: data.payload?.turn_time || data.turn_time || Date.now() / 1000,
                    },
                };

            case 'ACTION_REQUEST':
                console.log('[WebSocket] Action request received');
                return {
                    type: 'ACTION_REQUEST',
                    payload: {
                        character: data.payload?.character || data.character || { name: 'Unknown' },
                    },
                };

            case 'ACTION_CONFIRMED':
                console.log('[WebSocket] Action confirmed');
                return {
                    type: 'GAME_EVENT',
                    payload: {
                        event: {
                            event_type: 'ACTION_RESULT',
                            event_initiator: data.payload?.player_id || null,
                            event_subject: data.payload?.player_id || null,
                            event_target: null,
                            description: `Action confirmed: ${data.payload?.request_text || 'Action received'}`,
                        } as Event,
                    },
                };

            case 'GAME_EVENT':
                console.log('[WebSocket] Game event received:', data.payload?.event?.event_type);
                return {
                    type: 'GAME_EVENT',
                    payload: {
                        event: data.payload?.event || data.event || {},
                    },
                };

            case 'SCENE_UPDATE':
                console.log('[WebSocket] Scene update received');
                return {
                    type: 'SCENE_UPDATE',
                    payload: {
                        scene: data.payload?.scene || data.scene || {},
                        characters: data.payload?.characters || [],
                        npcs: data.payload?.npcs || [],
                        objects: data.payload?.objects || [],
                    },
                };

            case 'CHARACTER_STATUS_UPDATE':
                console.log('[WebSocket] Character status update received');
                return {
                    type: 'SESSION_UPDATE',
                    payload: {
                        session: {
                            players: [
                                {
                                    character: data.payload || data.character || {},
                                },
                            ],
                        } as Partial<Session> as Session,
                    },
                };

            case 'ERROR':
                console.error('[WebSocket] Error received:', data.payload?.message);
                return {
                    type: 'ERROR',
                    payload: {
                        message: data.payload?.message || data.error || 'Unknown error',
                        details: data.payload?.details,
                    },
                };

            case 'PONG':
                // Heartbeat response, ignore
                return null;

            default:
                // Try to handle as a game event if it has event_type
                if (data.event_type) {
                    console.log('[WebSocket] Treating as game event:', data.event_type);
                    return {
                        type: 'GAME_EVENT',
                        payload: {
                            event: data as Event,
                        },
                    };
                }

                console.log('[WebSocket] Unknown message type:', data.type);
                return null;
        }
    }

    /**
     * Notify state handlers of connection state change
     */
    private notifyStateChange(state: { connected: boolean; error?: string }): void {
        this.stateHandlers.forEach((handler) => handler(state));
    }
}

// Export singleton instance
export const webSocketService = new WebSocketService();
export default webSocketService;
