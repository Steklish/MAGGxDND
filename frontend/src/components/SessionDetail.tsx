import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { useGameStore } from '../store/gameStore';
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
    const [joinSessionId, setJoinSessionId] = useState('');
    const [joinError, setJoinError] = useState<string | null>(null);

    useEffect(() => {
        loadSessionDetail();
        // Refresh every 5 seconds
        const interval = setInterval(loadSessionDetail, 5000);
        
        // Scroll handler for header
        const handleScroll = () => {
            setScrolled(window.scrollY > 50);
        };
        window.addEventListener('scroll', handleScroll);
        
        return () => {
            clearInterval(interval);
            window.removeEventListener('scroll', handleScroll);
        };
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

    const handleJoinSession = async () => {
        if (!joinSessionId.trim()) {
            setJoinError('Please enter a session ID');
            return;
        }

        setIsJoining(true);
        setJoinError(null);

        try {
            const playerName = username || localStorage.getItem('username') || 'Player';
            const response = await fetch(`/api/v1/sessions/${joinSessionId}/players`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ player_name: playerName }),
            });

            if (response.ok) {
                const data = await response.json();
                alert(`Successfully joined session! Player ID: ${data.player_id}`);
                setJoinSessionId('');
                // Reload sessions list
                loadSessions();
                // Navigate to the joined session
                navigate(`/session/${joinSessionId}`);
                window.location.reload();
            } else {
                const errorData = await response.json();
                setJoinError(errorData.detail || 'Failed to join session');
            }
        } catch (err: any) {
            console.error('Failed to join session:', err);
            setJoinError('Network error. Please try again.');
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
            <div className="session-detail error">
                <h2>Error Loading Session</h2>
                <p>{error || 'Session not found'}</p>
                <button className="btn-back" onClick={onBack}>← Back</button>
            </div>
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

                        {/* Join Session Card */}
                        <div className="join-session-card">
                            <h2>🔗 Join Another Session</h2>
                            <p className="join-description">
                                Enter a session ID to connect to another player's game
                            </p>
                            <div className="join-form">
                                <input
                                    type="text"
                                    className="join-input"
                                    placeholder="Paste session ID here..."
                                    value={joinSessionId}
                                    onChange={(e) => setJoinSessionId(e.target.value)}
                                    disabled={isJoining}
                                />
                                <button
                                    className="btn-join"
                                    onClick={handleJoinSession}
                                    disabled={isJoining || !joinSessionId.trim()}
                                >
                                    {isJoining ? '⏳ Joining...' : '🚀 Join Session'}
                                </button>
                            </div>
                            {joinError && (
                                <div className="join-error">
                                    ⚠️ {joinError}
                                </div>
                            )}
                            <div className="join-hint">
                                💡 Share your session ID with friends so they can join!
                            </div>
                        </div>

                        {/* Players List */}
                        <div className="players-card full-width">
                            <h2>👥 Connected Players ({session.players?.length || 0})</h2>
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
                                    <p className="empty-hint">Share your session ID or use the join form to connect!</p>
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
