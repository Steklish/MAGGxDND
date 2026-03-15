import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { useGameStore } from '../store/gameStore';
import { ErrorBoundary } from './common/ErrorBoundary';
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
    onStartGame?: (sessionId: string) => void;
}

export const SessionDetail: React.FC<SessionDetailProps> = ({ sessionId, onBack, onLeave, onStartGame }) => {
    const navigate = useNavigate();
    const { username, logout, activeSessions, loadSessions } = useGameStore();
    const [session, setSession] = useState<any | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [scrolled, setScrolled] = useState(false);
    const [isJoining, setIsJoining] = useState(false);
    const [playerId, setPlayerId] = useState<string | null>(null);
    const [hasJoinedSession, setHasJoinedSession] = useState(false);

    useEffect(() => {
        // Check if we already have a player ID for this session in localStorage
        const storedPlayerId = localStorage.getItem(`playerId_${sessionId}`);
        if (storedPlayerId) {
            setPlayerId(storedPlayerId);
            setHasJoinedSession(true);
        }
        
        loadSessionDetail();
        loadPlayers();
        
        // Refresh session data every 5 seconds
        const sessionInterval = setInterval(loadSessionDetail, 5000);
        // Refresh players every 2 seconds for real-time updates
        const playersInterval = setInterval(loadPlayers, 2000);

        // Scroll handler for header
        const handleScroll = () => {
            setScrolled(window.scrollY > 50);
        };
        window.addEventListener('scroll', handleScroll);

        return () => {
            clearInterval(sessionInterval);
            clearInterval(playersInterval);
            window.removeEventListener('scroll', handleScroll);
        };
    }, [sessionId]);

    const loadSessionDetail = async () => {
        try {
            // Get session list and find our session
            const response = await axios.get('/api/v1/sessions');
            const foundSession = response.data.sessions.find((s: any) => s.session_id === sessionId);

            if (foundSession) {
                setSession({
                    ...foundSession,
                    players: [] // Will be populated by loadPlayers
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

    const loadPlayers = async () => {
        try {
            const response = await axios.get(`/api/v1/sessions/${sessionId}/players`);
            if (response.data && Array.isArray(response.data)) {
                setSession((prev: any) => ({
                    ...prev,
                    players: response.data,
                    player_count: response.data.length
                }));
            }
        } catch (err: any) {
            console.warn('Failed to load players:', err.message);
        }
    };

    const handleLeaveSession = async () => {
        // TODO: Implement leave session endpoint
        alert('Leave session feature coming soon!');
        onLeave();
    };

    const handleStartSession = async () => {
        if (onStartGame) {
            onStartGame(sessionId);
        } else {
            alert('Start session feature coming soon! This requires backend implementation.');
        }
    };

    const handleLogout = () => {
        logout();
        navigate('/');
    };

    const handleJoinThisSession = async () => {
        if (hasJoinedSession || playerId) {
            alert('You are already connected to this session!');
            return;
        }
        
        setIsJoining(true);

        try {
            const playerName = username || localStorage.getItem('username') || 'Player';
            const response = await fetch(`/api/v1/sessions/${sessionId}/players`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ player_name: playerName }),
            });

            if (response.ok) {
                const data = await response.json();
                setPlayerId(data.player_id);
                setHasJoinedSession(true);
                // Store player ID in localStorage to persist across page reloads
                localStorage.setItem(`playerId_${sessionId}`, data.player_id);
                // Reload session data to show updated player list
                await loadSessionDetail();
                await loadPlayers();
            } else {
                const errorData = await response.json();
                alert(`Failed to join: ${errorData.detail || 'Unknown error'}`);
            }
        } catch (err: any) {
            console.error('Failed to join session:', err);
            alert('Network error. Please try again.');
        } finally {
            setIsJoining(false);
        }
    };

    const handleCopySessionId = () => {
        if (session?.session_id) {
            navigator.clipboard.writeText(session.session_id);
            alert('Session ID copied to clipboard!');
        }
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
            <ErrorBoundary errorType="no-session">
                <div className="error-content">
                    <div className="error-code">SESSION NOT FOUND</div>
                    <div className="error-description">
                        {error || 'The session you are looking for does not exist or has been closed.'}
                    </div>
                    <div className="error-actions">
                        <button className="error-retry-btn" onClick={() => window.location.reload()}>
                            🔄 Retry
                        </button>
                        <button className="error-home-btn" onClick={onBack}>
                            🏠 Back to Home
                        </button>
                    </div>
                </div>
            </ErrorBoundary>
        );
    }

    return (
        <div className="session-detail-page">
            {/* Background */}
            <div className="session-detail-bg"></div>
            
            {/* Navigation Header */}
            <header className={`session-detail-header ${scrolled ? 'scrolled' : ''}`}>
                <div className="header-content">
                    <div className="logo" onClick={() => navigate('/home')}>
                        <span className="logo-icon">🐉</span>
                        <span className="logo-text">
                            <span className="logo-magg">MAGG</span>
                            <span className="logo-x">x</span>
                            <span className="logo-dnd">DND</span>
                        </span>
                    </div>

                    <nav className="header-nav">
                        <button onClick={() => navigate('/home')}>Overview</button>
                        <button onClick={() => { navigate('/profile'); }}>Characters</button>
                        <button>Sessions</button>
                    </nav>

                    <div className="header-actions">
                        <button
                            className="btn-create-session"
                            onClick={() => navigate('/home')}
                        >
                            <span>⚔️</span>
                            <span>Create Session</span>
                        </button>

                        <button
                            className="btn-profile"
                            onClick={() => navigate('/profile')}
                        >
                            <span className="profile-avatar">👤</span>
                            <span className="profile-name">{username || 'Adventurer'}</span>
                        </button>

                        <button
                            className="btn-logout"
                            onClick={handleLogout}
                            title="Logout"
                        >
                            <span>🚪</span>
                        </button>
                    </div>
                </div>
            </header>

            {/* Session Content */}
            <div className="session-detail-content">
                <div className="session-detail-container">
                    {/* Session Title Card */}
                    <div className="session-title-card">
                        <div className="session-title-header">
                            <div className="session-icon-large">🎲</div>
                            <div className="session-title-info">
                                <h1>{session.session_name}</h1>
                                <span className={`session-status status-${session.status.toLowerCase()}`}>
                                    {session.status}
                                </span>
                            </div>
                            <div className="session-title-actions">
                                {session.status === 'created' && (
                                    <button className="btn-start" onClick={handleStartSession}>
                                        🚀 Start Session
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Main Info Grid */}
                    <div className="session-main-grid">
                        {/* Session Info */}
                        <div className="session-info-card">
                            <h2>📋 Session Information</h2>
                            <div className="info-grid">
                                <div className="info-item full-width">
                                    <span className="info-label">Session ID</span>
                                    <div className="session-id-container">
                                        <span className="info-value mono">{session.session_id}</span>
                                        <button className="btn-copy" onClick={handleCopySessionId} title="Copy Session ID">
                                            📋 Copy
                                        </button>
                                    </div>
                                </div>
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
                            <div className="players-card-header">
                                <h2>👥 Connected Players ({session.players?.length || 0})</h2>
                                {!hasJoinedSession && !playerId && (
                                    <button
                                        className="btn-join-this"
                                        onClick={handleJoinThisSession}
                                        disabled={isJoining}
                                    >
                                        {isJoining ? '⏳ Connecting...' : '🔗 Connect'}
                                    </button>
                                )}
                            </div>
                            {playerId && (
                                <div className="connected-notice">
                                    ✅ Connected: <strong>{playerId}</strong>
                                </div>
                            )}
                            {session.players && session.players.length > 0 ? (
                                <div className="players-list">
                                    {session.players.map((player: any) => (
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
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="empty-players">
                                    <div className="empty-icon">👥</div>
                                    <p>No players connected yet</p>
                                    {!playerId && (
                                        <p className="empty-hint">Click "Connect" to join this session!</p>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Back Button at Bottom */}
                    <div className="session-back-container">
                        <button className="btn-back-large" onClick={onBack}>
                            ← Back to Home
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
