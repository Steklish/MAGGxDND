import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './SessionLobby.css';

interface Player {
    player_id: string;
    player_name: string;
    character_name?: string;
    character?: {
        name: string;
        race: string;
        char_class: string;
        level: number;
        portrait_url?: string;
        initiative_bonus?: number;
    };
    ready: boolean;
    is_host: boolean;
}

interface SessionLobbyProps {
    sessionId: string;
    playerId: string;
    isHost: boolean;
    onGameStart: (gameData: any) => void;
    onLeave: () => void;
}

export const SessionLobby: React.FC<SessionLobbyProps> = ({ 
    sessionId, 
    playerId, 
    isHost,
    onGameStart, 
    onLeave 
}) => {
    const [session, setSession] = useState<any>(null);
    const [players, setPlayers] = useState<Player[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isStarting, setIsStarting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadLobbyData();
        const interval = setInterval(loadLobbyData, 3000); // Refresh every 3 seconds
        return () => clearInterval(interval);
    }, [sessionId]);

    const loadLobbyData = async () => {
        try {
            // Get session info
            const sessionRes = await axios.get('/api/v1/sessions');
            const foundSession = sessionRes.data.sessions.find((s: any) => s.session_id === sessionId);
            
            if (!foundSession) {
                setError('Session not found');
                setIsLoading(false);
                return;
            }

            setSession(foundSession);

            // Get players (mock for now - backend not implemented)
            // TODO: Replace with real endpoint when available
            const mockPlayers: Player[] = [
                {
                    player_id: playerId,
                    player_name: localStorage.getItem('username') || 'Player',
                    character_name: 'Hero',
                    character: {
                        name: 'Hero',
                        race: 'Human',
                        char_class: 'Fighter',
                        level: 1,
                        initiative_bonus: 2
                    },
                    ready: true,
                    is_host: isHost
                }
            ];
            
            setPlayers(mockPlayers);
            setError(null);
        } catch (err: any) {
            console.error('Failed to load lobby data:', err);
            setError('Failed to load lobby data');
        } finally {
            setIsLoading(false);
        }
    };

    const handleStartGame = async () => {
        if (!isHost) return;
        
        setIsStarting(true);
        try {
            // Calculate initiative order
            const initiativeOrder = [...players]
                .filter(p => p.ready && p.character)
                .map(p => ({
                    player_id: p.player_id,
                    player_name: p.player_name,
                    character: p.character!,
                    initiative: Math.floor(Math.random() * 20) + (p.character?.initiative_bonus || 0)
                }))
                .sort((a, b) => b.initiative - a.initiative);

            // Start session via API
            await axios.post(`/api/v1/sessions/${sessionId}/start`, {
                scene_prompt: 'A dark dungeon corridor with flickering torches...',
                character_prompts: players.filter(p => p.ready).map(p => p.character_name || 'Hero'),
                npc_prompts: []
            });

            // Notify game start
            onGameStart({
                sessionId,
                players: initiativeOrder,
                currentTurn: 0,
                scene: {
                    name: 'Dungeon Corridor',
                    description: 'A dark dungeon corridor with flickering torches on the walls. The air is damp and cold.'
                }
            });
        } catch (err: any) {
            console.error('Failed to start game:', err);
            alert('Failed to start game: ' + (err.response?.data?.detail || 'Unknown error'));
        } finally {
            setIsStarting(false);
        }
    };

    const handleReady = async () => {
        // TODO: Implement ready toggle endpoint
        alert('Ready toggle coming soon!');
    };

    const handleKickPlayer = async (playerId: string) => {
        if (!isHost) return;
        if (!confirm(`Kick player?`)) return;
        
        try {
            await axios.delete(`/api/v1/sessions/${sessionId}/players/${playerId}`);
            loadLobbyData();
        } catch (err) {
            console.error('Failed to kick player:', err);
        }
    };

    const handleLeave = async () => {
        try {
            await axios.delete(`/api/v1/sessions/${sessionId}/players/${playerId}`);
        } catch (err) {
            console.error('Failed to leave session:', err);
        }
        onLeave();
    };

    if (isLoading) {
        return (
            <div className="session-lobby loading">
                <div className="loading-spinner">
                    <div className="spinner-ring"></div>
                    <div className="spinner-ring"></div>
                    <div className="spinner-ring"></div>
                </div>
                <p>Loading lobby...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="session-lobby error">
                <h2>Error</h2>
                <p>{error}</p>
                <button className="btn-back" onClick={onLeave}>← Back</button>
            </div>
        );
    }

    return (
        <div className="session-lobby">
            <div className="lobby-header">
                <div className="lobby-title">
                    <h1>{session?.session_name}</h1>
                    <span className="lobby-mode">{session?.game_mode}</span>
                </div>
                <button className="btn-leave" onClick={handleLeave}>
                    🚪 Leave Lobby
                </button>
            </div>

            <div className="lobby-content">
                {/* Players List */}
                <div className="players-section">
                    <h2>👥 Players ({players.length}/{session?.max_players || 5})</h2>
                    <div className="players-list">
                        {players.map(player => (
                            <div key={player.player_id} className={`player-card ${player.ready ? 'ready' : ''}`}>
                                <div className="player-header">
                                    <div className="player-avatar">
                                        {player.character?.portrait_url ? (
                                            <img src={player.character.portrait_url} alt={player.character.name} />
                                        ) : (
                                            <span>{player.player_name.charAt(0).toUpperCase()}</span>
                                        )}
                                    </div>
                                    <div className="player-info">
                                        <span className="player-name">
                                            {player.player_name}
                                            {player.is_host && <span className="host-badge">👑 Host</span>}
                                        </span>
                                        {player.character && (
                                            <span className="character-name">
                                                {player.character.name} - {player.character.race} {player.character.char_class}
                                            </span>
                                        )}
                                    </div>
                                    <div className="player-status">
                                        {player.ready ? (
                                            <span className="ready-status">✅ Ready</span>
                                        ) : (
                                            <span className="not-ready-status">⏳ Not Ready</span>
                                        )}
                                    </div>
                                    {isHost && !player.is_host && (
                                        <button 
                                            className="btn-kick"
                                            onClick={() => handleKickPlayer(player.player_id)}
                                            title="Kick player"
                                        >
                                            👢
                                        </button>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Session Info */}
                <div className="info-section">
                    <h2>📋 Session Information</h2>
                    <div className="info-grid">
                        <div className="info-item">
                            <span className="info-label">Game Mode</span>
                            <span className="info-value">{session?.game_mode}</span>
                        </div>
                        <div className="info-item">
                            <span className="info-label">Max Players</span>
                            <span className="info-value">{session?.max_players}</span>
                        </div>
                        <div className="info-item">
                            <span className="info-label">Status</span>
                            <span className="info-value">{session?.status}</span>
                        </div>
                    </div>
                    {session?.description && (
                        <div className="info-description">
                            <h3>Description</h3>
                            <p>{session.description}</p>
                        </div>
                    )}
                </div>

                {/* Ready Section */}
                <div className="ready-section">
                    {!isHost && (
                        <button 
                            className={`btn-ready ${players.find(p => p.player_id === playerId)?.ready ? 'ready' : ''}`}
                            onClick={handleReady}
                        >
                            {players.find(p => p.player_id === playerId)?.ready ? '✅ Ready' : '⏳ Not Ready'}
                        </button>
                    )}
                    
                    {isHost && (
                        <button 
                            className="btn-start-game"
                            onClick={handleStartGame}
                            disabled={isStarting || players.filter(p => p.ready).length === 0}
                        >
                            {isStarting ? '🎲 Starting...' : '🎲 Start Game'}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};
