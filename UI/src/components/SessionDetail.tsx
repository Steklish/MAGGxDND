import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './SessionDetail.css';

interface Player {
    player_id: string;
    player_name: string;
    character_name?: string;
    connected: boolean;
}

interface SessionDetail {
    session_id: string;
    session_name: string;
    game_mode: string;
    player_count: number;
    max_players: number;
    status: string;
    description?: string;
    players: Player[];
}

interface SessionDetailProps {
    sessionId: string;
    onBack: () => void;
    onLeave: () => void;
}

export const SessionDetail: React.FC<SessionDetailProps> = ({ sessionId, onBack, onLeave }) => {
    const [session, setSession] = useState<any | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadSessionDetail();
        // Refresh every 5 seconds
        const interval = setInterval(loadSessionDetail, 5000);
        return () => clearInterval(interval);
    }, [sessionId]);

    const loadSessionDetail = async () => {
        try {
            // Get session list and find our session
            const response = await axios.get('/api/v1/sessions');
            const foundSession = response.data.sessions.find((s: any) => s.session_id === sessionId);
            
            if (foundSession) {
                // Mock players data since endpoint not implemented
                setSession({
                    ...foundSession,
                    players: [] // TODO: Implement players endpoint
                });
            } else {
                setError('Session not found');
            }
            setError(null);
        } catch (err: any) {
            console.error('Failed to load session detail:', err);
            setError('Failed to load session information');
        } finally {
            setIsLoading(false);
        }
    };

    const handleLeaveSession = async () => {
        // TODO: Implement leave session endpoint
        alert('Leave session feature coming soon!');
        onLeave();
    };

    const handleStartSession = async () => {
        // TODO: Implement start session endpoint
        alert('Start session feature coming soon! This requires backend implementation.');
    };

    if (isLoading) {
        return (
            <div className="session-detail loading">
                <div className="loading-spinner">
                    <div className="spinner-ring"></div>
                    <div className="spinner-ring"></div>
                    <div className="spinner-ring"></div>
                </div>
                <p>Loading session...</p>
            </div>
        );
    }

    if (error || !session) {
        return (
            <div className="session-detail error">
                <h2>Error Loading Session</h2>
                <p>{error || 'Session not found'}</p>
                <button className="btn-back" onClick={onBack}>← Back</button>
            </div>
        );
    }

    return (
        <div className="session-detail">
            <div className="session-header">
                <button className="btn-back" onClick={onBack}>← Back</button>
                <div className="session-title">
                    <h1>{session.session_name}</h1>
                    <span className={`session-status status-${session.status.toLowerCase()}`}>
                        {session.status}
                    </span>
                </div>
                <div className="session-actions">
                    {session.status === 'created' && (
                        <button className="btn-start" onClick={handleStartSession}>
                            🚀 Start Session
                        </button>
                    )}
                    <button className="btn-leave" onClick={onLeave}>
                        ← Back
                    </button>
                </div>
            </div>

            <div className="session-content">
                {/* Session Info */}
                <div className="session-info-card">
                    <h2>📋 Session Information</h2>
                    <div className="info-grid">
                        <div className="info-item">
                            <span className="info-label">Game Mode</span>
                            <span className="info-value">{session.game_mode}</span>
                        </div>
                        <div className="info-item">
                            <span className="info-label">Players</span>
                            <span className="info-value">{session.player_count} / {session.max_players}</span>
                        </div>
                        <div className="info-item">
                            <span className="info-label">Status</span>
                            <span className="info-value">{session.status}</span>
                        </div>
                        <div className="info-item">
                            <span className="info-label">Session ID</span>
                            <span className="info-value mono">{session.session_id}</span>
                        </div>
                    </div>
                    {session.description && (
                        <div className="info-description">
                            <h3>Description</h3>
                            <p>{session.description}</p>
                        </div>
                    )}
                </div>

                {/* Players List */}
                <div className="players-card">
                    <h2>👥 Connected Players ({session.players?.length || 0})</h2>
                    {session.players && session.players.length > 0 ? (
                        <div className="players-list">
                            {session.players.map(player => (
                                <div key={player.player_id} className="player-item">
                                    <div className="player-info">
                                        <div className="player-avatar">
                                            {player.player_name.charAt(0).toUpperCase()}
                                        </div>
                                        <div className="player-details">
                                            <span className="player-name">{player.player_name}</span>
                                            {player.character_name && (
                                                <span className="player-character">{player.character_name}</span>
                                            )}
                                        </div>
                                        <span className={`player-status ${player.connected ? 'connected' : 'disconnected'}`}>
                                            {player.connected ? '🟢 Connected' : '🔴 Disconnected'}
                                        </span>
                                    </div>
                                    {/* Kick button removed - endpoint not implemented */}
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="empty-message">No players connected yet</p>
                    )}
                </div>

                {/* Session Settings */}
                <div className="settings-card">
                    <h2>⚙️ Session Settings</h2>
                    <div className="settings-grid">
                        <div className="setting-item">
                            <span className="setting-label">Max Players</span>
                            <span className="setting-value">{session.max_players}</span>
                        </div>
                        <div className="setting-item">
                            <span className="setting-label">Current Players</span>
                            <span className="setting-value">{session.player_count}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
