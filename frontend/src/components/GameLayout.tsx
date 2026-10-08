import React, { useState, useRef, useEffect } from 'react';
import { useGameStore } from '../store/gameStore';
import { ChatPanel } from './ChatPanel';
import { SceneViewer } from './SceneViewer';
import { CharacterPanel } from './CharacterPanel';
import { Footer } from './Footer';
import { ProfilePage } from './ProfilePage';
import { SessionCreation } from './SessionCreation';
import './GameLayout.css';

interface TurnEntry {
    character: any;
    type: 'player' | 'npc' | 'ally' | 'hostile' | 'neutral';
    initiative: number;
    isDead: boolean;
    isDying: boolean;
    deathSaveSuccesses: number;
    deathSaveFailures: number;
}

interface GameLayoutProps {
    onCreateSession?: () => void;
    onViewSession?: (sessionId: string) => void;
    onJoinSession?: (sessionId: string) => void;
}

export const GameLayout: React.FC<GameLayoutProps> = ({ onCreateSession, onViewSession: _onViewSession, onJoinSession: _onJoinSession }) => {
    const {
        session,
        currentSession,
        currentScene,
        activeCharacter,
        loadSessions,
        activeSessions,
        setCurrentSession,
        setActiveCharacter,
        isGenerating,
        generationStatus,
        setIsGenerating,
        setGenerationStatus,
        sendAction
    } = useGameStore();

    // Read session info from localStorage directly
    const userId = typeof window !== 'undefined' ? localStorage.getItem('userId') : null;
    const sessionId = typeof window !== 'undefined' ? localStorage.getItem('currentSessionId') : null;
    const playerId = typeof window !== 'undefined' ? localStorage.getItem('currentPlayerId') : null;
    const gameStatus = typeof window !== 'undefined' ? localStorage.getItem('gameStatus') : null;

    // Check if user is authenticated
    useEffect(() => {
        const token = localStorage.getItem('access_token');
        const isGuest = localStorage.getItem('is_guest') === 'true';
        const hasValidSession = sessionId && playerId;

        if (!token && !hasValidSession) {
            console.log('⚠️ No auth token and no active session - redirecting to landing page');
            localStorage.removeItem('currentSessionId');
            localStorage.removeItem('currentPlayerId');
            localStorage.removeItem('gameStatus');
            window.location.href = '/';
            return;
        }

        if (isGuest) {
            try {
                const guestToken = localStorage.getItem('guest_token') || localStorage.getItem('access_token');
                if (!guestToken) {
                    window.location.href = '/';
                }
            } catch (e) {
                console.warn('⚠️ Error checking guest token:', e);
            }
        }
    }, [sessionId, playerId]);

    // UI state
    const [showProfile, setShowProfile] = useState(false);
    const [showCreateSession, setShowCreateSession] = useState(false);
    const [sessionNotFound, setSessionNotFound] = useState(false);
    const [copiedSessionId, setCopiedSessionId] = useState(false);
    const [layoutMode, setLayoutMode] = useState<'split' | 'map' | 'story'>('split');
    const [showCharacterDrawer, setShowCharacterDrawer] = useState(false);
    const [turnQueue, setTurnQueue] = useState<TurnEntry[]>([]);
    const [currentIndex, setCurrentIndex] = useState(0);

    // Initial load
    useEffect(() => {
        const token = localStorage.getItem('access_token');
        if (!token && !(sessionId && playerId)) {
            window.location.href = '/';
            return;
        }

        loadSessions();

        if (sessionId && playerId && gameStatus === 'running') {
            fetch(`/api/v1/sessions/${sessionId}/game_info`)
                .then(res => res.json())
                .then(data => {
                    if (data.detail === 'Session not found') {
                        localStorage.removeItem('gameStatus');
                        setGenerationStatus('');
                        setIsGenerating(false);
                        setSessionNotFound(true);
                    } else {
                        const gameSession = {
                            session_id: data.session_id,
                            session_name: data.session_name,
                            game_mode: data.game_mode,
                            status: data.status,
                            player_count: data.player_count,
                            max_players: data.max_players,
                            description: data.description,
                            players: data.players || [],
                            npcs: data.npcs || [],
                        };
                        setCurrentSession(gameSession as any);

                        // Set active character if not set
                        const currentUser = localStorage.getItem('username');
                        const myPlayer = (data.players || []).find((p: any) =>
                            p.player_name === currentUser || p.character?.name === currentUser
                        );
                        if (myPlayer && myPlayer.character) {
                            setActiveCharacter(myPlayer.character);
                        } else if (data.players && data.players[0] && data.players[0].character) {
                            setActiveCharacter(data.players[0].character);
                        }
                    }
                })
                .catch(err => {
                    console.warn('Could not load game_info:', err);
                });
        }
    }, [sessionId, playerId, gameStatus]);

    // Initialize turn queue from session players & NPCs
    useEffect(() => {
        const activeSession = currentSession || session;
        if (!activeSession) return;

        const queue: TurnEntry[] = [];
        activeSession.players?.forEach((p: any) => {
            const char = p.character || p;
            if (!char || !char.name) return;
            queue.push({
                character: char,
                type: 'player',
                initiative: char.stats?.dexterity || 10,
                isDead: (char.current_hp ?? 10) <= 0 && char.is_alive === false,
                isDying: (char.current_hp ?? 10) <= 0 && char.is_alive !== false,
                deathSaveSuccesses: 0,
                deathSaveFailures: 0,
            });
        });

        activeSession.npcs?.forEach((n: any) => {
            const char = n.character || n;
            if (!char || !char.name) return;
            const isGood = (char.alignment || '').includes('Good');
            queue.push({
                character: char,
                type: isGood ? 'ally' : 'hostile',
                initiative: char.stats?.dexterity || 10,
                isDead: (char.current_hp ?? 10) <= 0 && char.is_alive === false,
                isDying: (char.current_hp ?? 10) <= 0 && char.is_alive !== false,
                deathSaveSuccesses: 0,
                deathSaveFailures: 0,
            });
        });

        queue.sort((a, b) => b.initiative - a.initiative);
        setTurnQueue(queue);
    }, [session, currentSession]);

    const handleCopySessionId = async () => {
        if (sessionId) {
            try {
                await navigator.clipboard.writeText(sessionId);
                setCopiedSessionId(true);
                setTimeout(() => setCopiedSessionId(false), 2000);
            } catch (err) {
                setCopiedSessionId(true);
                setTimeout(() => setCopiedSessionId(false), 2000);
            }
        }
    };

    const handleStartGame = async () => {
        if (!sessionId) return;
        try {
            setIsGenerating(true);
            setGenerationStatus('🎲 Инициализация игрового мира...');
            const username = localStorage.getItem('username') || 'Adventurer';

            const response = await fetch(`/api/v1/sessions/${sessionId}/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify({
                    wishes: 'A medieval fantasy dungeon quest with mysteries and encounters',
                    scene_prompt: 'A ruined underground temple chamber bathed in eerie blue torchlight',
                    character_prompts: [`A brave ${username}, level 1 adventurer ready for quests`],
                    npc_prompts: ['A cunning goblin scout hiding in the shadows'],
                }),
            });

            const data = await response.json();
            if (response.ok) {
                localStorage.setItem('currentSessionId', sessionId);
                localStorage.setItem('gameStatus', 'running');
                setIsGenerating(false);
                setGenerationStatus('');
                if (onCreateSession) {
                    onCreateSession();
                } else {
                    window.location.reload();
                }
            } else {
                setIsGenerating(false);
                setGenerationStatus('');
            }
        } catch (error) {
            console.error('Failed to start game:', error);
            setIsGenerating(false);
            setGenerationStatus('');
        }
    };

    const handleLeaveSession = () => {
        localStorage.removeItem('currentSessionId');
        localStorage.removeItem('currentPlayerId');
        localStorage.removeItem('gameStatus');
        setCurrentSession(null);
        window.location.reload();
    };

    const handleNextTurn = () => {
        if (turnQueue.length === 0) return;
        const nextIdx = (currentIndex + 1) % turnQueue.length;
        setCurrentIndex(nextIdx);
        const nextActor = turnQueue[nextIdx];
        if (nextActor?.character && nextActor.type === 'player') {
            setActiveCharacter(nextActor.character);
        }
    };

    // Overlay for session creation
    if (showCreateSession && userId) {
        return <SessionCreation userId={parseInt(userId)} onComplete={() => setShowCreateSession(false)} onBack={() => setShowCreateSession(false)} />;
    }

    // Overlay for profile
    if (showProfile && userId) {
        return <ProfilePage userId={parseInt(userId)} onBack={() => setShowProfile(false)} onGoHome={() => setShowProfile(false)} />;
    }

    const hasActiveSession = sessionId && playerId;
    const isGameStarted = hasActiveSession && gameStatus === 'running';

    // Session not found fallback
    if (sessionNotFound) {
        return (
            <div className="ergonomic-game-layout error-state">
                <div className="status-modal-card">
                    <h2>⚠️ Session Not Found</h2>
                    <p>The game session was not found on the server.</p>
                    <div className="modal-actions-row">
                        <button className="primary-btn" onClick={handleLeaveSession}>Start Fresh</button>
                        <button className="secondary-btn" onClick={onCreateSession}>Create New</button>
                    </div>
                </div>
            </div>
        );
    }

    // Loading overlay
    if (isGenerating) {
        return (
            <div className="ergonomic-game-layout loading-state">
                <div className="status-modal-card">
                    <div className="pulse-spinner" />
                    <h2>🎮 Initializing Adventure...</h2>
                    <p className="status-text">{generationStatus || 'Summoning world and entities...'}</p>
                </div>
            </div>
        );
    }

    // Lobby state
    if (hasActiveSession && !isGameStarted) {
        return (
            <div className="ergonomic-game-layout lobby-state">
                <div className="status-modal-card lobby-card">
                    <span className="lobby-icon">🎲</span>
                    <h2>Adventure Ready to Begin</h2>
                    <p>Connected to Session: <strong>{sessionId?.slice(0, 8)}...</strong></p>
                    <p className="lobby-hint">Click below when your party is ready to step into the world.</p>
                    <div className="modal-actions-row">
                        <button className="primary-btn glow" onClick={handleStartGame}>▶️ Launch Game Session</button>
                        <button className="secondary-btn" onClick={handleLeaveSession}>🚪 Leave Lobby</button>
                    </div>
                </div>
            </div>
        );
    }

    // No session state
    if ((!hasActiveSession || !isGameStarted) && (!session || !currentScene)) {
        return (
            <div className="ergonomic-game-layout empty-state">
                <div className="status-modal-card">
                    <span className="lobby-icon">⚔️</span>
                    <h2>No Active Session</h2>
                    <p>Create or join an adventure session to begin playing.</p>
                    <div className="modal-actions-row">
                        <button className="primary-btn glow" onClick={onCreateSession}>✨ Create Session</button>
                        <button className="secondary-btn" onClick={() => window.location.href = '/'}>← Back to Home</button>
                    </div>
                </div>
            </div>
        );
    }

    const currentActor = turnQueue[currentIndex % Math.max(1, turnQueue.length)];
    const activeGameMode = (currentSession as any)?.game_mode || 'STORY';

    return (
        <div className="ergonomic-game-layout">
            {/* Top Navigation & Initiative HUD */}
            <header className="ergonomic-game-header">
                {/* Brand & Session */}
                <div className="header-brand-section">
                    <h1 className="brand-logo">
                        <span className="logo-gold">MAGG</span>
                        <span className="logo-dim">×</span>
                        <span className="logo-white">DND</span>
                    </h1>

                    {sessionId && (
                        <div
                            className="session-id-pill"
                            onClick={handleCopySessionId}
                            title="Click to copy full Session ID"
                        >
                            <span className="pill-dot" />
                            <span className="pill-text">{copiedSessionId ? '✓ Copied' : `Session: ${sessionId.slice(0, 8)}`}</span>
                        </div>
                    )}

                    <div className={`mode-badge ${activeGameMode.toLowerCase()}`}>
                        {activeGameMode === 'COMBAT' ? '⚔️ COMBAT' : '📜 STORY'}
                    </div>
                </div>

                {/* Center: Dynamic Initiative Strip */}
                <div className="header-initiative-strip">
                    {turnQueue.length > 0 ? (
                        <div className="initiative-tokens-list">
                            {turnQueue.map((entry, idx) => {
                                const isCurrent = idx === (currentIndex % turnQueue.length);
                                const isAlly = entry.type === 'player' || entry.type === 'ally';
                                return (
                                    <div
                                        key={`turn-${idx}-${entry.character.name}`}
                                        className={`turn-token-pill ${isCurrent ? 'active' : ''} ${isAlly ? 'ally' : 'hostile'}`}
                                        title={`${entry.character.name} (Initiative: ${entry.initiative})`}
                                    >
                                        <span className="turn-rank">{idx + 1}</span>
                                        <span className="turn-name">{entry.character.name}</span>
                                        {isCurrent && <span className="turn-active-indicator">NOW</span>}
                                    </div>
                                );
                            })}
                        </div>
                    ) : (
                        <span className="free-exploration-text">🕊️ Free Party Exploration</span>
                    )}

                    {turnQueue.length > 0 && (
                        <button
                            type="button"
                            className="next-turn-btn"
                            onClick={handleNextTurn}
                            title="Advance to next turn"
                        >
                            Next Turn ❯
                        </button>
                    )}
                </div>

                {/* Right: Layout Switchers & Quick Tools */}
                <div className="header-tools-section">
                    {/* View mode toggle */}
                    <div className="layout-mode-group">
                        <button
                            type="button"
                            className={`layout-btn ${layoutMode === 'map' ? 'active' : ''}`}
                            onClick={() => setLayoutMode('map')}
                            title="Tactical Map Focus"
                        >
                            🗺️
                        </button>
                        <button
                            type="button"
                            className={`layout-btn ${layoutMode === 'split' ? 'active' : ''}`}
                            onClick={() => setLayoutMode('split')}
                            title="Split Map & Chronicle"
                        >
                            ⚖️
                        </button>
                        <button
                            type="button"
                            className={`layout-btn ${layoutMode === 'story' ? 'active' : ''}`}
                            onClick={() => setLayoutMode('story')}
                            title="Chronicle Story Focus"
                        >
                            📜
                        </button>
                    </div>

                    {/* Quick Tools */}
                    <button
                        type="button"
                        className={`tool-icon-btn ${showCharacterDrawer ? 'active' : ''}`}
                        onClick={() => setShowCharacterDrawer(!showCharacterDrawer)}
                        title="Toggle Hero Sheet Drawer"
                    >
                        👤
                    </button>

                    <button
                        type="button"
                        className="tool-icon-btn"
                        onClick={() => setShowProfile(true)}
                        title="User Profile"
                    >
                        ⚙️
                    </button>
                </div>
            </header>

            {/* Main Interactive Arena */}
            <div className={`ergonomic-workspace ${layoutMode}`}>
                {/* Tactical Scene Viewer */}
                {(layoutMode === 'split' || layoutMode === 'map') && (
                    <div className={`workspace-pane map-pane ${layoutMode === 'map' ? 'fullscreen' : ''}`}>
                        <SceneViewer />
                    </div>
                )}

                {/* Narrative Chronicle Log with Integrated Input */}
                {(layoutMode === 'split' || layoutMode === 'story') && (
                    <div className={`workspace-pane chronicle-pane ${layoutMode === 'story' ? 'fullscreen' : ''}`}>
                        <ChatPanel />
                    </div>
                )}

                {/* Slide-out Character Sheet Drawer */}
                {showCharacterDrawer && (
                    <aside className="character-sheet-drawer">
                        <div className="drawer-header-bar">
                            <h3>Hero Details</h3>
                            <button
                                type="button"
                                className="close-drawer-btn"
                                onClick={() => setShowCharacterDrawer(false)}
                            >
                                ✕
                            </button>
                        </div>
                        <div className="drawer-body">
                            <CharacterPanel />
                        </div>
                    </aside>
                )}
            </div>
        </div>
    );
};
