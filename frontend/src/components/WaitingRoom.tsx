import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGameStore } from '../store/gameStore';
import { ErrorBoundary } from './common/ErrorBoundary';
import './WaitingRoom.css';

interface Player {
    player_id: string;
    player_name: string;
    character_name?: string;
    connected: boolean;
    is_ready: boolean;
    role: string;
}

interface SessionInfo {
    session_id: string;
    session_name: string;
    game_mode: string;
    player_count: number;
    max_players: number;
    status: string;
    description?: string;
    owner_id: number;
    owner_name: string;
    is_owner: boolean;
    players: Player[];
}

interface WaitingRoomProps {
    sessionId: string;
    onGameStart: (sessionId: string) => void;
    onBack: () => void;
}

export const WaitingRoom: React.FC<WaitingRoomProps> = ({ sessionId, onGameStart, onBack }) => {
    const navigate = useNavigate();
    const { username, logout, setCurrentSession } = useGameStore();
    const [session, setSession] = useState<SessionInfo | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [scrolled, setScrolled] = useState(false);
    const [playerId, setPlayerId] = useState<string | null>(null);
    const [isReady, setIsReady] = useState(false);
    const [isOwner, setIsOwner] = useState(false);
    const [waitingForPlayers, setWaitingForPlayers] = useState(false);

    // Check if we can start (ALL connected players must be ready)
    const canStartGame = session && session.players
        .filter(p => p.connected)
        .every(p => p.is_ready);
    
    // Get list of not ready connected players
    const notReadyPlayers = session?.players
        .filter(p => p.connected && !p.is_ready)
        .map(p => p.player_name) || [];

    useEffect(() => {
        // Check if we already have a player ID for this session
        const storedPlayerId = localStorage.getItem(`playerId_${sessionId}`);
        if (storedPlayerId) {
            setPlayerId(storedPlayerId);
        }

        // Auto-join session if not already joined
        const joinSession = async () => {
            try {
                const username = localStorage.getItem('username') || 'Player';
                const response = await fetch(`/api/v1/sessions/${sessionId}/players`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ player_name: username })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    setPlayerId(data.player_id);
                    localStorage.setItem(`playerId_${sessionId}`, data.player_id);
                    console.log('✓ Auto-joined session:', sessionId, 'player_id:', data.player_id);
                } else {
                    const errorData = await response.json();
                    if (errorData.detail && !errorData.detail.includes('already')) {
                        console.warn('Failed to auto-join:', errorData.detail);
                    }
                }
            } catch (err) {
                console.error('Failed to auto-join session:', err);
            }
        };
        
        joinSession();
        loadSessionInfo();

        // Poll for updates every 3 seconds
        const interval = setInterval(loadSessionInfo, 3000);

        // Scroll handler
        const handleScroll = () => {
            setScrolled(window.scrollY > 50);
        };
        window.addEventListener('scroll', handleScroll);

        return () => {
            clearInterval(interval);
            window.removeEventListener('scroll', handleScroll);
        };
    }, [sessionId]);

    const loadSessionInfo = async () => {
        try {
            const response = await fetch(`/api/v1/sessions/${sessionId}/waiting-room`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                console.log('[WaitingRoom] Session data loaded:', data);
                console.log('[WaitingRoom] is_owner:', data.is_owner, 'username:', username);
                setSession(data);
                setIsOwner(data.is_owner);
                
                // Check if current user is already ready
                const currentPlayer = data.players.find((p: Player) => p.player_name === username);
                if (currentPlayer) {
                    setIsReady(currentPlayer.is_ready);
                    console.log('[WaitingRoom] Player ready status:', currentPlayer.is_ready);
                }
                
                setError(null);
            } else {
                const errorData = await response.json();
                setError(errorData.detail || 'Failed to load session info');
            }
        } catch (err: any) {
            console.error('Failed to load session info:', err);
            setError('Network error. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleToggleReady = async () => {
        try {
            const response = await fetch(`/api/v1/sessions/${sessionId}/ready`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify({
                    is_ready: !isReady
                })
            });

            if (response.ok) {
                setIsReady(!isReady);
                await loadSessionInfo();
            } else {
                const errorData = await response.json();
                alert(`Failed to update ready status: ${errorData.detail || 'Unknown error'}`);
            }
        } catch (err: any) {
            console.error('Failed to toggle ready status:', err);
            alert('Network error. Please try again.');
        }
    };

    const handleStartGame = async () => {
        if (!canStartGame) {
            if (notReadyPlayers.length > 0) {
                alert(`Waiting for players to ready: ${notReadyPlayers.join(', ')}`);
            } else {
                alert('Wait for players to connect!');
            }
            return;
        }

        setWaitingForPlayers(true);

        try {
            const response = await fetch(`/api/v1/sessions/${sessionId}/start-game`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                // Update session status
                localStorage.setItem('gameStatus', 'running');
                localStorage.setItem('currentSessionId', sessionId);
                
                // Navigate to game page
                onGameStart(sessionId);
            } else {
                const errorData = await response.json();
                alert(`Failed to start game: ${errorData.detail || 'Unknown error'}`);
                setWaitingForPlayers(false);
            }
        } catch (err: any) {
            console.error('Failed to start game:', err);
            alert('Network error. Please try again.');
            setWaitingForPlayers(false);
        }
    };

    const handleLogout = () => {
        logout();
        navigate('/');
    };

    const handleCopySessionId = () => {
        if (session?.session_id) {
            navigator.clipboard.writeText(session.session_id);
            alert('Session ID copied to clipboard!');
        }
    };

    if (isLoading) {
        return (
            <div className="waiting-room loading">
                <div className="loading-spinner">
                    <div className="spinner-ring"></div>
                    <div className="spinner-ring"></div>
                    <div className="spinner-ring"></div>
                </div>
                <p>Loading waiting room...</p>
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
        <div className="waiting-room-page">
            {/* Background */}
            <div className="waiting-room-bg"></div>

            {/* Navigation Header */}
            <header className={`waiting-room-header ${scrolled ? 'scrolled' : ''}`}>
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
                        <button onClick={() => navigate('/profile')}>Characters</button>
                        <button>Sessions</button>
                    </nav>

                    <div className="header-actions">
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

            {/* Waiting Room Content */}
            <div className="waiting-room-content">
                <div className="waiting-room-container">
                    {/* Session Title Card */}
                    <div className="waiting-room-title-card">
                        <div className="waiting-room-title-header">
                            <div className="session-icon-large">🎲</div>
                            <div className="waiting-room-title-info">
                                <h1>{session.session_name}</h1>
                                <span className={`session-status status-${session.status.toLowerCase()}`}>
                                    {session.status}
                                </span>
                            </div>
                            <div className="session-title-actions">
                                {isOwner ? (
                                    <button 
                                        className={`btn-start-game ${!canStartGame ? 'disabled' : ''}`} 
                                        onClick={handleStartGame}
                                        disabled={!canStartGame || waitingForPlayers}
                                    >
                                        {waitingForPlayers ? (
                                            <>
                                                <span className="loading-spinner-small"></span>
                                                Starting...
                                            </>
                                        ) : (
                                            <>
                                                🚀 Start Game
                                            </>
                                        )}
                                    </button>
                                ) : (
                                    <button 
                                        className={`btn-ready ${isReady ? 'ready' : ''}`} 
                                        onClick={handleToggleReady}
                                    >
                                        {isReady ? '✅ Ready!' : '🎯 Get Ready'}
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Main Info Grid */}
                    <div className="waiting-room-grid">
                        {/* Session Info */}
                        <div className="waiting-room-info-card">
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
                                <div className="info-item">
                                    <span className="info-label">Session Owner</span>
                                    <span className="info-value">{session.owner_name}</span>
                                </div>
                            </div>
                            {session.description && (
                                <div className="info-description">
                                    <h3>Description</h3>
                                    <p>{session.description}</p>
                                </div>
                            )}

                            {/* Ready Status Notice */}
                            <div className="ready-notice">
                                <div className="notice-icon">ℹ️</div>
                                <div className="notice-content">
                                    <strong>Waiting for Players</strong>
                                    <p>
                                        {isOwner 
                                            ? notReadyPlayers.length > 0
                                                ? `Waiting for: ${notReadyPlayers.join(', ')}`
                                                : "All players are ready! You can start the game."
                                            : "Click 'Get Ready' to let the owner know you're ready to start."
                                        }
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Players List */}
                        <div className="players-ready-card">
                            <div className="players-card-header">
                                <h2>👥 Players ({session.players.length})</h2>
                                {!playerId && (
                                    <span className="hint-text">Join to participate</span>
                                )}
                            </div>
                            {session.players && session.players.length > 0 ? (
                                <div className="players-ready-list">
                                    {session.players.map((player) => (
                                        <div key={player.player_id} className="player-ready-item">
                                            <div className="player-ready-info">
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
                                                        {player.connected ? '🟢' : '🔴'}
                                                    </span>
                                                    <span className={`player-ready-badge ${player.is_ready ? 'ready' : ''}`}>
                                                        {player.is_ready ? '✅ Ready' : '⏳ Not Ready'}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="empty-players">
                                    <div className="empty-icon">👥</div>
                                    <p>No players connected yet</p>
                                    <p className="empty-hint">Share the session ID to invite players!</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Back Button at Bottom */}
                    <div className="waiting-room-back-container">
                        <button className="btn-back-large" onClick={onBack}>
                            ← Back to Home
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
