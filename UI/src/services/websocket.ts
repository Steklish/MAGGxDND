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

export class WebSocketService {
    private ws: WebSocket | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 1000;
    private messageHandlers: WebSocketMessageHandler[] = [];
    private stateHandlers: WebSocketStateHandler[] = [];
    private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    private sessionId: string | null = null;
    private playerId: string | null = null;

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

        if (onMessage) {
            this.messageHandlers.push(onMessage);
        }
        if (onStateChange) {
            this.stateHandlers.push(onStateChange);
        }

        return new Promise((resolve, reject) => {
            // Determine WebSocket URL based on current location
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/${sessionId}/${playerId}`;
            console.log('[WebSocket] Connecting to:', wsUrl);

            try {
                this.ws = new WebSocket(wsUrl);

                this.ws.onopen = () => {
                    console.log('[WebSocket] Connected');
                    this.reconnectAttempts = 0;
                    this.notifyStateChange({ connected: true });
                    resolve();
                };

                this.ws.onclose = (event) => {
                    console.log('[WebSocket] Disconnected:', event.code, event.reason);
                    this.notifyStateChange({ connected: false });
                    this.attemptReconnect();
                };

                this.ws.onerror = (error) => {
                    console.error('[WebSocket] Error:', error);
                    this.notifyStateChange({ connected: false, error: 'Connection error' });
                    reject(new Error('WebSocket connection error'));
                };

                this.ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        console.log('[WebSocket] Received:', data);
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
    }

    /**
     * Disconnect from the WebSocket
     */
    disconnect(): void {
        console.log('[WebSocket] Disconnecting...');
        this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnect

        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        this.sessionId = null;
        this.playerId = null;
        this.messageHandlers = [];
        this.stateHandlers = [];
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
            console.error('[WebSocket] Cannot send message: not connected');
            return;
        }

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
     * Attempt to reconnect
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

        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
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
        // Handle different message types from the server
        switch (data.type) {
            case 'CONNECTED':
                // Connection confirmation - not a game message
                return null;

            case 'MASTER_MESSAGE':
                return {
                    type: 'MASTER_MESSAGE',
                    payload: {
                        text: data.text,
                        tag: data.tag,
                    },
                };

            case 'SESSION_UPDATE':
                return {
                    type: 'SESSION_UPDATE',
                    payload: {
                        session: data.data as Session,
                    },
                };

            case 'TURN_UPDATE':
                return {
                    type: 'TURN_QUEUE_UPDATE',
                    payload: {
                        turn_queue: [
                            {
                                character: data.active_player_name,
                                next_turn: Date.now() / 1000,
                            },
                        ],
                        turn_time: Date.now() / 1000,
                    },
                };

            case 'PLAYER_REQUEST':
                return {
                    type: 'ACTION_REQUEST',
                    payload: {
                        character: { name: data.character_name } as Character,
                    },
                };

            case 'ACTION_CONFIRMED':
                // Convert to game event
                return {
                    type: 'GAME_EVENT',
                    payload: {
                        event: {
                            event_type: 'ACTION_RESULT',
                            event_initiator: data.event?.data?.character_name || null,
                            event_subject: data.event?.data?.character_name || null,
                            event_target: null,
                            description: `Action confirmed: ${JSON.stringify(data.event?.data)}`,
                        } as Event,
                    },
                };

            case 'CHARACTER_UPDATE':
                // Handle character state updates
                return {
                    type: 'SESSION_UPDATE',
                    payload: {
                        session: {
                            players: [
                                {
                                    character: {
                                        name: data.character_id,
                                        ...data.updates,
                                    } as Character,
                                },
                            ],
                        } as Partial<Session> as Session,
                    },
                };

            case 'SCENE_UPDATE':
                return {
                    type: 'SCENE_UPDATE',
                    payload: {
                        scene: data.scene,
                        characters: [],
                        npcs: [],
                        objects: [],
                    },
                };

            case 'COMBAT_EVENT':
                return {
                    type: 'GAME_EVENT',
                    payload: {
                        event: {
                            event_type: 'ACTION_RESULT',
                            event_initiator: null,
                            event_subject: null,
                            event_target: null,
                            description: JSON.stringify(data.data),
                        } as Event,
                    },
                };

            case 'error':
                return {
                    type: 'ERROR',
                    payload: {
                        message: data.error || 'Unknown error',
                    },
                };

            default:
                // Try to handle as a game event
                if (data.event_type) {
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
