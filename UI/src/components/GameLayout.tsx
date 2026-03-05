import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useGameStore } from '../store/gameStore';
import { ChatPanel } from './ChatPanel';
import { SceneViewer } from './SceneViewer';
import { CharacterPanel } from './CharacterPanel';
import { ActionPanel } from './ActionPanel';
import { Footer } from './Footer';
import { MiniCharacterPanel } from './MiniCharacterPanel';
import { MiniChatPanel } from './MiniChatPanel';
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

export const GameLayout: React.FC<GameLayoutProps> = ({ onCreateSession, onViewSession, onJoinSession }) => {
    const { session, currentSession, currentScene, activeCharacter, loadSessions, activeSessions, setCurrentSession, isGenerating, generationStatus, setIsGenerating, setGenerationStatus } = useGameStore();
    const [showProfile, setShowProfile] = useState(false);
    const [showCreateSession, setShowCreateSession] = useState(false);
    
    // Read session info from localStorage directly (not from store)
    const userId = typeof window !== 'undefined' ? localStorage.getItem('userId') : null;
    const sessionId = typeof window !== 'undefined' ? localStorage.getItem('currentSessionId') : null;
    const playerId = typeof window !== 'undefined' ? localStorage.getItem('currentPlayerId') : null;
    const gameStatus = typeof window !== 'undefined' ? localStorage.getItem('gameStatus') : null;

    const handleSessionCreated = (newSessionId: string) => {
        setShowCreateSession(false);
        // Auto-join the created session
        const username = localStorage.getItem('username') || 'Player';
        fetch(`/api/v1/sessions/${newSessionId}/players`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ player_name: username }),
        }).then(res => res.json()).then(data => {
            localStorage.setItem('currentSessionId', newSessionId);
            localStorage.setItem('currentPlayerId', data.player_id);
            alert(`Session created and joined!\nPlayer ID: ${data.player_id}`);
            window.location.reload();
        }).catch(err => {
            console.error('Failed to auto-join:', err);
            localStorage.setItem('currentSessionId', newSessionId);
        });
    };

    const handleStartGame = async () => {
        if (!sessionId) return;
        try {
            // Set generating state
            setIsGenerating(true);
            setGenerationStatus('🎲 Инициализация игрового мира...');
            
            const response = await fetch(`/api/v1/sessions/start_real_game`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_name: 'Active Session',
                    game_mode: 'STORY',
                    scene_prompt: 'A medieval tavern with adventurers',
                    character_prompts: ['A brave hero'],
                    npc_prompts: ['A mysterious stranger']
                }),
            });
            const data = await response.json();
            
            if (response.ok) {
                setGenerationStatus('✨ Генерация персонажа...');
                await new Promise(resolve => setTimeout(resolve, 500));
                
                setGenerationStatus('🧙 Создание NPC...');
                await new Promise(resolve => setTimeout(resolve, 500));
                
                // Update localStorage with new session ID and mark as running
                localStorage.setItem('currentSessionId', data.session_id);
                localStorage.setItem('currentPlayerId', data.players[0]);
                localStorage.setItem('gameStatus', 'running');
                console.log('🎮 Game started:', data);
                
                setGenerationStatus('🌍 Загрузка мира...');
                await new Promise(resolve => setTimeout(resolve, 800));
                
                // Update store
                setCurrentSession({
                    session_id: data.session_id,
                    session_name: data.session_name,
                    game_mode: data.game_mode,
                    status: 'running',
                    player_count: data.players.length,
                    max_players: 5,
                    description: null,
                    players: data.players.map(p => ({ player_id: p, player_name: p, character_name: null })),
                });
                
                // Reset generating state
                setIsGenerating(false);
                setGenerationStatus('');
                
                // Reload to show game interface
                window.location.reload();
            } else {
                console.error('Failed to start game:', data.detail);
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
        // Update store to clear session
        setCurrentSession(null);
        // Force re-render by updating local state
        window.location.reload();
    };

    // Show session creation overlay
    if (showCreateSession && userId) {
        return <SessionCreation userId={parseInt(userId)} onComplete={handleSessionCreated} onBack={() => setShowCreateSession(false)} />;
    }

    // Show profile page
    if (showProfile && userId) {
        return <ProfilePage userId={parseInt(userId)} onBack={() => setShowProfile(false)} onJoinSession={onJoinSession} />;
    }
    const [leftPanelWidth, setLeftPanelWidth] = useState(25);
    const [rightPanelWidth, setRightPanelWidth] = useState(25);
    const [headerHeight, setHeaderHeight] = useState(() => Math.round(window.innerHeight * 0.07));
    const [actionPanelHeight, setActionPanelHeight] = useState(() => Math.round(window.innerHeight * 0.07));
    const [isSceneCollapsed, setIsSceneCollapsed] = useState(false);
    const [isCollapsing, setIsCollapsing] = useState(false);
    const [isResizingLeft, setIsResizingLeft] = useState(false);
    const [isResizingRight, setIsResizingRight] = useState(false);
    const [isResizingHeader, setIsResizingHeader] = useState(false);
    const [isResizingActionPanel, setIsResizingActionPanel] = useState(false);
    const [turnQueue, setTurnQueue] = useState<TurnEntry[]>([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [dyingCharacters, setDyingCharacters] = useState<string[]>([]);
    const containerRef = useRef<HTMLDivElement>(null);
    const startX = useRef(0);
    const startY = useRef(0);
    const startLeftWidth = useRef(0);
    const startRightWidth = useRef(0);
    const startHeaderHeight = useRef(0);
    const startActionPanelHeight = useRef(0);
    const prevActionPanelHeight = useRef(70);
    const containerWidth = useRef(0);
    const containerHeight = useRef(0);

    // Load sessions on mount
    useEffect(() => {
        loadSessions();
        console.log('🔍 GameLayout mounted:', { sessionId, playerId, currentSession, isGenerating });
    }, []);

    // Initialize turn queue from session - MUST be before any early returns
    useEffect(() => {
        if (!session) return;

        const queue: TurnEntry[] = [];

        // Add players
        session.players?.forEach(p => {
            if (!p?.character) return;
            const char = p.character;
            queue.push({
                character: char,
                type: 'player',
                initiative: char.initiative_bonus || 10,
                isDead: char.current_hp <= 0 && char.is_alive === false,
                isDying: char.current_hp <= 0 && char.is_alive !== false,
                deathSaveSuccesses: 0,
                deathSaveFailures: 0
            });
        });

        // Add NPCs
        session.npcs?.forEach(n => {
            if (!n?.character) return;
            const char = n.character;
            // Determine NPC attitude based on context (for now, default to hostile)
            let type: 'hostile' | 'neutral' | 'ally' = 'hostile';
            if (char.alignment?.includes('Good')) type = 'ally';
            else if (char.alignment?.includes('Neutral')) type = 'neutral';

            queue.push({
                character: char,
                type,
                initiative: char.initiative_bonus || 10,
                isDead: char.current_hp <= 0 && char.is_alive === false,
                isDying: char.current_hp <= 0 && char.is_alive !== false,
                deathSaveSuccesses: 0,
                deathSaveFailures: 0
            });
        });

        // Sort by initiative (descending)
        queue.sort((a, b) => b.initiative - a.initiative);
        setTurnQueue(queue);
        setCurrentIndex(0);
    }, [session]);

    // Check if user has active session (from localStorage)
    const hasActiveSession = sessionId && playerId;

    // Check if game was started (session is running)
    // Only consider game started if we have both sessionId AND playerId
    const isGameStarted = hasActiveSession && gameStatus === 'running';
    
    console.log('🔍 GameLayout render:', { hasActiveSession, isGameStarted, sessionId, playerId, gameStatus });

    // Show loading screen during game generation
    if (isGenerating) {
        return (
            <div className="game-layout">
                <div className="loading-screen">
                    <div className="loading-content">
                        <div className="loading-animation">
                            <div className="loading-spinner"></div>
                            <div className="loading-spinner-delay"></div>
                            <div className="loading-spinner-delay-2"></div>
                        </div>
                        <h2>🎮 Создание игры...</h2>
                        <p className="loading-status">{generationStatus}</p>
                        <p className="loading-hint">Пожалуйста, подождите. Это может занять несколько секунд.</p>
                    </div>
                </div>
            </div>
        );
    }

    // Show game interface when game is started (even without currentScene from WebSocket)
    if (hasActiveSession && isGameStarted) {
        // Game is running - show the full game interface
        // currentScene will be populated when WebSocket connects
        console.log('🎮 Showing game interface for running session');
        // Continue to render the game interface below
    } else if (hasActiveSession && !isGameStarted) {
        return (
            <div className="game-layout">
                <div className="no-session-screen">
                    <div className="no-session-content">
                        <h1>🎮 Connected to Session</h1>
                        <p>You are connected to session: <strong>{sessionId}</strong></p>
                        <p>Player ID: <strong>{playerId}</strong></p>
                        <div className="no-session-actions">
                            <button className="btn-create-session" onClick={handleStartGame}>
                                ▶️ Start Game
                            </button>
                            <button className="btn-join-session" onClick={handleLeaveSession}>
                                🚪 Leave Session
                            </button>
                        </div>
                        <p className="text-muted">Note: Full game integration requires backend to initialize scene data.</p>
                    </div>
                </div>
            </div>
        );
    }

    // Show "no session" state when not in active game AND game not started
    if ((!hasActiveSession || !isGameStarted) && (!session || !currentScene)) {
        return (
            <div className="game-layout">
                <div className="no-session-screen">
                    <div className="no-session-content">
                        <h1>🎲 No Active Game Session</h1>
                        <p>You are not currently in an active game session.</p>
                        <div className="no-session-actions">
                            <button
                                className="btn-create-session"
                                onClick={onCreateSession}
                            >
                                ✨ Create New Session
                            </button>
                            <button
                                className="btn-join-session"
                                onClick={() => {/* TODO: Join session */}}
                            >
                                🚪 Join Existing Session
                            </button>
                            <button
                                className="btn-back-landing"
                                onClick={() => {
                                    // Redirect to profile page
                                    const event = new CustomEvent('show-profile');
                                    window.dispatchEvent(event);
                                }}
                            >
                                ← Back to Profile
                            </button>
                        </div>
                        {activeSessions && activeSessions.length > 0 && (
                            <div className="available-sessions">
                                <h3>Available Sessions:</h3>
                                <div className="sessions-list">
                                    {activeSessions.map(sess => (
                                        <div key={sess.session_id} className="session-item">
                                            <div className="session-item-info">
                                                <span className="session-name">{sess.session_name}</span>
                                                <span className="session-players">{sess.player_count}/{sess.max_players} players</span>
                                            </div>
                                            <button
                                                className="btn-join-session"
                                                onClick={() => onJoinSession && onJoinSession(sess.session_id)}
                                            >
                                                🚪 Join
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        );
    }

    // Get alive queue (filter out dead, keep dying for death saves)
    const getAliveQueue = useCallback(() => {
        return turnQueue.filter(entry => !entry.isDead);
    }, [turnQueue]);

    const aliveQueue = getAliveQueue();
    const currentTurnChar = aliveQueue[currentIndex % aliveQueue.length];

    // Handle character death animation
    const handleDeathAnimation = useCallback((characterName: string) => {
        setDyingCharacters(prev => [...prev, characterName]);
        setTimeout(() => {
            setDyingCharacters(prev => prev.filter(name => name !== characterName));
        }, 1000);
    }, []);

    // Handle death save for dying characters
    const performDeathSave = useCallback((characterName: string) => {
        // In a real implementation, this would roll a d20
        const roll = Math.floor(Math.random() * 20) + 1;
        console.log(`${characterName} death save roll: ${roll}`);
        // Update death save counters based on roll
        // 10+ = success, <10 = failure
        // 1 = 2 failures, 20 = automatic success
    }, []);

    // Advance turn
    const advanceTurn = useCallback(() => {
        if (aliveQueue.length === 0) return;

        const currentChar = aliveQueue[currentIndex % aliveQueue.length];

        // Check if current character is dying - perform death save
        if (currentChar?.isDying) {
            performDeathSave(currentChar.character.name);
        }

        // Move to next character
        setCurrentIndex(prev => (prev + 1) % aliveQueue.length);
    }, [aliveQueue, currentIndex, performDeathSave]);

    const handleMouseMove = useCallback((e: MouseEvent) => {
        if (!isResizingLeft && !isResizingRight && !isResizingHeader && !isResizingActionPanel) return;
        if (!containerRef.current) return;

        const container = containerRef.current;
        const containerRect = container.getBoundingClientRect();

        if (isResizingHeader) {
            const deltaY = e.clientY - startY.current;
            const newHeight = startHeaderHeight.current + deltaY;
            // Allow dragging between min and max, will snap on release
            const minHeight = window.innerHeight * 0.05;
            const maxHeight = window.innerHeight * 0.10;
            setHeaderHeight(Math.max(minHeight, Math.min(maxHeight, newHeight)));
        } else if (isResizingActionPanel) {
            const deltaY = e.clientY - startY.current;
            const deltaPercent = (deltaY / containerRect.height) * 100;
            const newHeight = startActionPanelHeight.current + deltaPercent;
            
            // If dragging below threshold, collapse scene
            if (newHeight < 10) {
                setIsSceneCollapsed(true);
                prevActionPanelHeight.current = actionPanelHeight;
                setActionPanelHeight(0);
            } else {
                setIsSceneCollapsed(false);
                setActionPanelHeight(Math.max(10, Math.min(60, newHeight)));
            }
        } else {
            const deltaX = e.clientX - startX.current;
            const deltaPercent = (deltaX / containerWidth.current) * 100;

            if (isResizingLeft) {
                const newWidth = startLeftWidth.current + deltaPercent;
                setLeftPanelWidth(Math.max(5, Math.min(25, newWidth)));
            }

            if (isResizingRight) {
                const newWidth = startRightWidth.current - deltaPercent;
                setRightPanelWidth(Math.max(5, Math.min(25, newWidth)));
            }
        }
    }, [isResizingLeft, isResizingRight, isResizingHeader, isResizingActionPanel]);

    const handleMouseUp = useCallback(() => {
        // Snap header to min or max height
        if (isResizingHeader) {
            const minHeight = window.innerHeight * 0.05;
            const maxHeight = window.innerHeight * 0.10;
            const midpoint = (minHeight + maxHeight) / 2;
            
            // Snap to max if above midpoint, otherwise snap to min
            if (headerHeight > midpoint) {
                setHeaderHeight(maxHeight);
            } else {
                setHeaderHeight(minHeight);
            }
        }
        
        // Snap action panel to collapsed or expanded
        if (isResizingActionPanel) {
            const collapseThreshold = 10;
            if (actionPanelHeight < collapseThreshold) {
                setIsSceneCollapsed(true);
                setActionPanelHeight(0);
            } else {
                setIsSceneCollapsed(false);
                // Snap to default expanded height
                setActionPanelHeight(70);
            }
        }
        
        setIsResizingLeft(false);
        setIsResizingRight(false);
        setIsResizingHeader(false);
        setIsResizingActionPanel(false);
    }, [isResizingHeader, isResizingActionPanel, headerHeight, actionPanelHeight]);

    useEffect(() => {
        if (isResizingLeft || isResizingRight || isResizingHeader || isResizingActionPanel) {
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
            return () => {
                document.removeEventListener('mousemove', handleMouseMove);
                document.removeEventListener('mouseup', handleMouseUp);
            };
        }
    }, [isResizingLeft, isResizingRight, isResizingHeader, isResizingActionPanel, handleMouseMove, handleMouseUp]);

    const startLeftResize = (e: React.MouseEvent) => {
        e.preventDefault();
        setIsResizingLeft(true);
        startX.current = e.clientX;
        startLeftWidth.current = leftPanelWidth;
        if (containerRef.current) {
            containerWidth.current = containerRef.current.getBoundingClientRect().width;
        }
    };

    const startRightResize = (e: React.MouseEvent) => {
        e.preventDefault();
        setIsResizingRight(true);
        startX.current = e.clientX;
        startRightWidth.current = rightPanelWidth;
        if (containerRef.current) {
            containerWidth.current = containerRef.current.getBoundingClientRect().width;
        }
    };

    const startHeaderResize = (e: React.MouseEvent) => {
        e.preventDefault();
        setIsResizingHeader(true);
        startY.current = e.clientY;
        startHeaderHeight.current = headerHeight;
    };

    const startActionPanelResize = (e: React.MouseEvent) => {
        e.preventDefault();
        setIsResizingActionPanel(true);
        startY.current = e.clientY;
        startActionPanelHeight.current = isSceneCollapsed ? (prevActionPanelHeight.current || 50) : actionPanelHeight;
        if (containerRef.current) {
            containerHeight.current = containerRef.current.getBoundingClientRect().height;
        }
    };

    const toggleScene = () => {
        if (isSceneCollapsed) {
            // Expand scene with animation
            setIsCollapsing(true);
            setActionPanelHeight(70);
            setIsSceneCollapsed(false);
            setTimeout(() => setIsCollapsing(false), 300);
        } else {
            // Collapse scene with animation
            setIsCollapsing(true);
            prevActionPanelHeight.current = actionPanelHeight;
            setActionPanelHeight(0);
            setIsSceneCollapsed(true);
            setTimeout(() => setIsCollapsing(false), 300);
        }
    };

    if (!session) {
        return <div className="loading">Loading game...</div>;
    }

    const getAttitudeColor = (type: string) => {
        switch (type) {
            case 'player': return 'var(--accent-purple)';
            case 'ally': return 'var(--accent-green)';
            case 'neutral': return 'var(--accent-yellow)';
            case 'hostile': return 'var(--accent-red)';
            default: return 'var(--text-muted)';
        }
    };

    const getAttitudeBgGradient = (type: string) => {
        switch (type) {
            case 'player': return 'linear-gradient(135deg, rgba(157, 78, 221, 0.3) 0%, rgba(157, 78, 221, 0.1) 100%)';
            case 'ally': return 'linear-gradient(135deg, rgba(42, 157, 143, 0.3) 0%, rgba(42, 157, 143, 0.1) 100%)';
            case 'neutral': return 'linear-gradient(135deg, rgba(233, 196, 106, 0.3) 0%, rgba(233, 196, 106, 0.1) 100%)';
            case 'hostile': return 'linear-gradient(135deg, rgba(230, 57, 70, 0.3) 0%, rgba(230, 57, 70, 0.1) 100%)';
            default: return 'linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%)';
        }
    };

    return (
        <div className="game-layout" ref={containerRef} style={{ '--header-height': `${headerHeight}px` } as React.CSSProperties}>
            {/* Header */}
            <header
                className="game-header"
                style={{
                    height: `${headerHeight}px`,
                    '--header-height': `${headerHeight}px`
                } as React.CSSProperties}
            >
                <div className="header-left">
                    <h1 className="game-title">
                        <span className="title-magg">MAGG</span>
                        <span className="title-x">x</span>
                        <span className="title-dnd">DND</span>
                    </h1>
                </div>

                {/* Turn Queue with Portraits */}
                <div className="header-center turn-queue-container">
                    {aliveQueue.map((entry, idx) => {
                        const isCurrentTurn = idx === (currentIndex % aliveQueue.length);
                        const isDying = entry.isDying;
                        const color = getAttitudeColor(entry.type);
                        const bgGradient = getAttitudeBgGradient(entry.type);

                        return (
                            <React.Fragment key={`${entry.character.name}-${entry.initiative}`}>
                                {/* Full Portrait - 16:9 horizontal rectangle */}
                                <div
                                    className={`turn-portrait ${isCurrentTurn ? 'active' : ''} ${isDying ? 'dying' : ''} ${dyingCharacters.includes(entry.character.name) ? 'death-animation' : ''}`}
                                    style={{
                                        borderColor: color,
                                        opacity: isCurrentTurn ? 1 : 0.4,
                                        background: bgGradient
                                    } as React.CSSProperties}
                                >
                                    <div className="portrait-frame">
                                        {/* Character name overlay */}
                                        <div className="portrait-name-overlay">
                                            {entry.character.name}
                                        </div>
                                        {/* Attitude indicator bar */}
                                        <div
                                            className="attitude-indicator"
                                            style={{ backgroundColor: color }}
                                        />
                                    </div>

                                    {/* Death save counters */}
                                    {isDying && (
                                        <div className="death-saves">
                                            <div className="death-save-successes">
                                                {'✓'.repeat(entry.deathSaveSuccesses)}
                                            </div>
                                            <div className="death-save-failures">
                                                {'✗'.repeat(entry.deathSaveFailures)}
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Mini Portrait - for small headers */}
                                <div
                                    className={`mini-portrait ${isCurrentTurn ? 'active' : ''}`}
                                    style={{
                                        borderColor: color,
                                        opacity: isCurrentTurn ? 1 : 0.5
                                    } as React.CSSProperties}
                                >
                                    <div
                                        className="mini-portrait-indicator"
                                        style={{ backgroundColor: color }}
                                    />
                                    <span className="mini-portrait-name">{entry.character.name}</span>
                                </div>
                            </React.Fragment>
                        );
                    })}
                </div>

                <div className="header-right">
                    <button className="btn-create-session-header" onClick={() => setShowCreateSession(true)}>
                        ➕ Create Session
                    </button>
                    <button className="profile-btn" title="Profile" onClick={() => setShowProfile(true)}>
                        <span className="profile-icon">👤</span>
                    </button>
                    {sessionId && playerId && (
                        <div className="session-status">
                            <span className="status-dot">🟢</span>
                            <span className="session-id" title={sessionId}>{sessionId.substring(0, 8)}...</span>
                        </div>
                    )}
                </div>

                {/* Header resize handle */}
                <div
                    className="header-resize-handle"
                    onMouseDown={startHeaderResize}
                />
            </header>

            {/* Main content */}
            <div className="game-content">
                {/* Left Panel - Characters */}
                <aside
                    className="left-panel"
                    style={{ width: `${leftPanelWidth}%` }}
                >
                    {leftPanelWidth <= 5 ? <MiniCharacterPanel /> : <CharacterPanel />}
                </aside>

                {/* Session Info Panel - Shows when connected to session */}
                {sessionId && playerId && (
                    <div className="session-info-panel" style={{ border: '2px solid red' }}>
                        <div className="session-info-header">
                            <h3>🎮 Active Session</h3>
                            <button className="btn-leave-session" onClick={handleLeaveSession}>
                                🚪 Leave
                            </button>
                        </div>
                        <div className="session-info-content">
                            <div className="session-detail">
                                <span className="detail-label">Session ID:</span>
                                <span className="detail-value mono">{sessionId}</span>
                            </div>
                            <div className="session-detail">
                                <span className="detail-label">Player ID:</span>
                                <span className="detail-value mono">{playerId}</span>
                            </div>
                            <div className="session-detail">
                                <span className="detail-label">Status:</span>
                                <span className="detail-value status-connected">🟢 Connected</span>
                            </div>
                            <button className="btn-start-game" onClick={handleStartGame}>
                                🎲 Start Game
                            </button>
                        </div>
                    </div>
                )}

                {/* Left resize handle */}
                <div
                    className={`resize-handle left-resize ${isResizingLeft ? 'resizing' : ''}`}
                    onMouseDown={startLeftResize}
                />

                {/* Center - Action and Scene */}
                <main className="center-panel">
                    <div className={`action-panel-container ${isCollapsing ? 'collapsing' : ''}`} style={{ flex: `1 1 ${isSceneCollapsed ? 100 : 100 - actionPanelHeight}%` }}>
                        <ActionPanel />
                    </div>
                    <div
                        className={`resize-handle action-panel-resize ${isResizingActionPanel ? 'resizing' : ''} ${isSceneCollapsed ? 'hidden-handle' : ''}`}
                        onMouseDown={startActionPanelResize}
                    />
                    <div className={`scene-container ${isCollapsing ? 'collapsing' : ''} ${isSceneCollapsed ? 'hidden-scene' : ''}`} style={{ flex: `0 0 ${isSceneCollapsed ? 0 : actionPanelHeight}%` }}>
                        <SceneViewer />
                    </div>
                    <div className={`action-panel-collapsed-handle ${isSceneCollapsed ? 'show' : ''}`} onClick={toggleScene}>
                        <div className="handle-bar" />
                    </div>
                </main>

                {/* Right resize handle */}
                <div
                    className={`resize-handle right-resize ${isResizingRight ? 'resizing' : ''}`}
                    onMouseDown={startRightResize}
                />

                {/* Right Panel - Chat */}
                <aside
                    className="right-panel"
                    style={{ width: `${rightPanelWidth}%` }}
                >
                    {rightPanelWidth <= 5 ? <MiniChatPanel /> : <ChatPanel />}
                </aside>
            </div>

            {/* Footer */}
            <Footer />

            {/* Profile Page Modal */}
            {showProfile && userId && (
                <ProfilePage
                    userId={parseInt(userId)}
                    onBack={() => setShowProfile(false)}
                />
            )}
        </div>
    );
};
