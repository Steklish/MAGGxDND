import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { useGameStore } from '../store/gameStore';
import { ErrorBoundary } from './common/ErrorBoundary';
import { CharacterProfileSelector } from './CharacterProfileSelector';
import './SessionDetail.css';

interface Player {
    player_id: string;
    player_name: string;
    character_name?: string;
    connected: boolean;
    is_ready?: boolean;
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
    const [isOwner, setIsOwner] = useState(false);
    const [showProfileSelector, setShowProfileSelector] = useState(false);

    // Check if session is already running (from active sessions in memory)
    const activeSession = activeSessions.find(s => s.session_id === sessionId);
    const isRunning = session?.status === 'running' || activeSession !== undefined;
    const isInMemory = activeSession !== undefined;

    // Navigate to game directly if session is running
    const handleEnterGame = () => {
        if (onStartGame) {
            onStartGame(sessionId);
        }
    };

    // Navigate to waiting room for game setup
    const handleGoToWaitingRoom = () => {
        if (onStartGame) {
            onStartGame(sessionId);
        }
    };

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
        // Refresh players every 3 seconds for real-time updates (reduced frequency)
        const playersInterval = setInterval(loadPlayers, 3000);

        // Scroll handler for header + dynamic scrollbar color
        const handleScroll = () => {
            setScrolled(window.scrollY > 50);

            const scrollTop = window.scrollY;
            const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
            const progress = maxScroll > 0 ? scrollTop / maxScroll : 0;

            let color: string;
            if (progress < 0.25) {
                const t = progress / 0.25;
                color = `rgb(${42 + t * (233 - 42)}, ${157 + t * (196 - 157)}, ${143 + t * (106 - 143)})`;
            } else if (progress < 0.5) {
                const t = (progress - 0.25) / 0.25;
                color = `rgb(${233 + t * (255 - 233)}, ${196 + t * (107 - 196)}, ${106 + t * (53 - 106)})`;
            } else if (progress < 0.75) {
                const t = (progress - 0.5) / 0.25;
                color = `rgb(${255 + t * (230 - 255)}, ${107 + t * (57 - 107)}, ${53 + t * (70 - 53)})`;
            } else {
                const t = (progress - 0.75) / 0.25;
                color = `rgb(${230 + t * (157 - 230)}, ${57 + t * (78 - 57)}, ${70 + t * (221 - 70)})`;
            }

            document.documentElement.style.setProperty('--scrollbar-color', color);
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
            // Get session detail from the specific endpoint
            const response = await axios.get(`/api/v1/sessions/${sessionId}`);
            const foundSession = response.data;

            if (foundSession) {
                setSession({
                    ...foundSession,
                    players: session?.players || [] // Keep existing players until loaded
                });
                // Check if current user is the owner
                const ownerStatus = foundSession.is_owner || false;
                setIsOwner(ownerStatus);
                console.log('[SessionDetail] is_owner:', ownerStatus, 'session:', foundSession);
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
                // Only update player_count from the session detail, not from players array length
                // This prevents jumping because player_count comes from DB with proper filtering
                setSession((prev: any) => ({
                    ...prev,
                    players: response.data
                    // Keep player_count from session detail endpoint
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

    const handleLogout = () => {
        logout();
        navigate('/');
    };

    const handleJoinThisSession = async () => {
        if (hasJoinedSession || playerId) {
            alert('You are already connected to this session!');
            return;
        }

        // Show profile selector instead of direct join
        setShowProfileSelector(true);
    };

    const handleProfileSelected = async (profileId: number) => {
        setShowProfileSelector(false);
        setIsJoining(true);

        try {
            const playerName = username || localStorage.getItem('username') || 'Player';
            const response = await fetch(`/api/v1/sessions/${sessionId}/players/with-profile`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ player_name: playerName, profile_id: profileId }),
            });

            if (response.ok) {
                const data = await response.json();
                setPlayerId(data.player_id);
                setHasJoinedSession(true);
                localStorage.setItem(`playerId_${sessionId}`, data.player_id);
                await loadSessionDetail();
                await loadPlayers();
            } else {
                const errorData = await response.json();
                alert(`Failed to join: ${errorData.detail || 'Unknown error'}`);
            }
        } catch (err: any) {
            console.error('Failed to join session with profile:', err);
            alert('Network error. Please try again.');
        } finally {
            setIsJoining(false);
        }
    };

    const handleProfileSelectorCancel = () => {
        setShowProfileSelector(false);
    };

    const handleCopySessionId = () => {
        if (session?.session_id) {
            navigator.clipboard.writeText(session.session_id);
            alert('Session ID copied to clipboard!');
        }
    };

    const handleKickPlayer = async (playerIdToKick: string, playerName: string) => {
        if (!isOwner) {
            alert('Only the session owner can kick players');
            return;
        }

        if (!confirm(`Are you sure you want to kick ${playerName} from the session?`)) {
            return;
        }

        try {
            const response = await fetch(`/api/v1/sessions/${sessionId}/players/${playerIdToKick}/kick`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
            });

            if (response.ok) {
                // Reload players list
                await loadPlayers();
                await loadSessionDetail();
            } else {
                const errorData = await response.json();
                alert(`Failed to kick player: ${errorData.detail || 'Unknown error'}`);
            }
        } catch (err: any) {
            console.error('Failed to kick player:', err);
            alert('Network error. Please try again.');
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
                                {isRunning ? (
                                    <button
                                        className="btn-enter-game"
                                        onClick={handleEnterGame}
                                    >
                                        🎮 Enter Game
                                    </button>
                                ) : (
                                    <button
                                        className="btn-waiting-room"
                                        onClick={handleGoToWaitingRoom}
                                    >
                                        🎲 Go to Waiting Room
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
                                <h2>👥 Players ({session.player_count || session.players?.length || 0})</h2>
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
                                                    {player.role === 'owner' && (
                                                        <span className="player-role-badge">👑 Owner</span>
                                                    )}
                                                </div>
                                                <div className="player-status-section">
                                                    <span className={`player-status ${player.connected ? 'connected' : 'disconnected'}`}>
                                                        {player.connected ? '🟢 Connected' : '🔴 Disconnected'}
                                                    </span>
                                                    <span className={`player-ready-badge ${player.is_ready ? 'ready' : ''}`}>
                                                        {player.is_ready ? '✅ Ready' : '⏳ Not Ready'}
                                                    </span>
                                                </div>
                                                {/* Kick button - only for owner and not for other owners */}
                                                {isOwner && player.role !== 'owner' && (
                                                    <button
                                                        className="btn-kick"
                                                        onClick={() => handleKickPlayer(player.player_id, player.player_name)}
                                                        title="Kick player"
                                                    >
                                                        ❌ Kick
                                                    </button>
                                                )}
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

            {/* Character Profile Selector Modal */}
            {showProfileSelector && (
                <CharacterProfileSelector
                    sessionId={sessionId}
                    playerName={username || localStorage.getItem('username') || 'Player'}
                    onSelect={handleProfileSelected}
                    onCancel={handleProfileSelectorCancel}
                    isLoading={false}
                />
            )}
        </div>
    );
};
