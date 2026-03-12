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

export const GameLayout: React.FC<GameLayoutProps> = ({ onCreateSession, onViewSession: _onViewSession, onJoinSession }) => {
    const { session, currentSession, currentScene, activeCharacter, loadSessions, activeSessions, setCurrentSession, setCurrentScene, setActiveCharacter, isGenerating, generationStatus, setIsGenerating, setGenerationStatus, addMessage, isAuthenticated, logout } = useGameStore();

    // Read session info from localStorage directly (not from store) - MUST be before useEffect
    const userId = typeof window !== 'undefined' ? localStorage.getItem('userId') : null;
    const sessionId = typeof window !== 'undefined' ? localStorage.getItem('currentSessionId') : null;
    const playerId = typeof window !== 'undefined' ? localStorage.getItem('currentPlayerId') : null;
    const gameStatus = typeof window !== 'undefined' ? localStorage.getItem('gameStatus') : null;

    // Check if user is authenticated - redirect to landing page if not
    useEffect(() => {
        const token = localStorage.getItem('access_token');
        const isGuest = localStorage.getItem('is_guest') === 'true';
        const hasValidSession = sessionId && playerId;
        
        // If no token AND no active game session - redirect to landing
        if (!token && !hasValidSession) {
            console.log('⚠️ No auth token and no active session - redirecting to landing page');
            // Clear any stale session data
            localStorage.removeItem('currentSessionId');
            localStorage.removeItem('currentPlayerId');
            localStorage.removeItem('gameStatus');
            window.location.href = '/';
            return;
        }
        
        // If guest token expired - redirect to landing
        if (isGuest) {
            try {
                // Guest tokens expire in 24 hours - check if still valid
                const guestToken = localStorage.getItem('guest_token');
                if (!guestToken) {
                    console.log('⚠️ Guest token missing - redirecting to landing page');
                    window.location.href = '/';
                }
            } catch (e) {
                console.warn('⚠️ Error checking guest token:', e);
            }
        }
    }, [sessionId, playerId]);

    // ALL HOOKS MUST BE AT THE TOP - before any conditional returns
    const [showProfile, setShowProfile] = useState(false);
    const [showCreateSession, setShowCreateSession] = useState(false);
    const [sessionNotFound, setSessionNotFound] = useState(false);
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

    // ALL useEffect MUST BE BEFORE ANY CONDITIONAL RETURNS
    useEffect(() => {
        // Check authentication before loading anything
        const token = localStorage.getItem('access_token');
        if (!token && !(sessionId && playerId)) {
            console.log('⚠️ Not authenticated on mount - redirecting to landing page');
            window.location.href = '/';
            return;
        }
        
        loadSessions();
        console.log('🔍 GameLayout mounted:', { sessionId, playerId, currentSession, isGenerating });
        
        // If game is running, try to load game data from server
        if (sessionId && playerId && gameStatus === 'running') {
            console.log('📡 Loading game data for session:', sessionId);
            fetch(`/api/v1/sessions/${sessionId}/game_info`)
                .then(res => res.json())
                .then(data => {
                    console.log('📦 Game info loaded:', data);
                    if (data.detail === 'Session not found') {
                        console.warn('⚠️ Session not found on server - may have been lost');
                        // Clear invalid session
                        localStorage.removeItem('gameStatus');
                        setGenerationStatus('');
                        setIsGenerating(false);
                        setSessionNotFound(true);
                    } else if (data.players && data.players.length > 0) {
                        console.log('🎭 Players loaded:', data.players.length);
                        console.log('🎭 NPCs loaded:', data.npcs?.length || 0);
                        console.log('🏰 Scene:', data.scene?.name);
                        
                        // Update session in store with game data
                        const gameSession = {
                            session_id: data.session_id,
                            session_name: data.session_name,
                            game_mode: data.game_mode,
                            status: data.status,
                            player_count: data.players.length,
                            max_players: 5,
                            description: undefined,
                            players: data.players.map((p: any) => ({
                                character: {
                                    name: p.name,
                                    race: p.race,
                                    char_class: p.char_class,
                                    level: p.level,
                                    current_hp: p.current_hp,
                                    max_hp: p.max_hp,
                                    armor_class: p.armor_class,
                                    initiative_bonus: p.initiative_bonus,
                                    speed: p.speed,
                                    proficiency_bonus: p.proficiency_bonus,
                                    is_alive: p.is_alive,
                                    stats: p.stats,
                                }
                            })),
                            npcs: (data.npcs || []).map((n: any) => ({
                                character: {
                                    name: n.name,
                                    race: n.race,
                                    char_class: n.char_class,
                                    alignment: n.alignment,
                                    current_hp: n.current_hp,
                                    max_hp: n.max_hp,
                                    armor_class: n.armor_class,
                                    initiative_bonus: n.initiative_bonus,
                                    speed: n.speed,
                                    proficiency_bonus: n.proficiency_bonus,
                                    is_alive: n.is_alive,
                                    stats: n.stats,
                                }
                            })),
                        } as any;
                        setCurrentSession(gameSession);
                        
                        // Add welcome message from DM
                        console.log('🏰 Scene loaded:', data.scene.name);
                        
                        // Add initial game messages
                        const dmMessage = {
                            sender_name: 'DM',
                            text: `Welcome to ${data.scene.name}! ${data.scene.description}`,
                            type: 'dm',
                            timestamp: new Date().toISOString(),
                        };
                        const systemMessage = {
                            sender_name: 'System',
                            text: `Game started with ${data.players.length} player(s) and ${data.npcs?.length || 0} NPC(s).`,
                            type: 'environment',
                            timestamp: new Date().toISOString(),
                        };
                        
                        // Add messages to store
                        addMessage(dmMessage);
                        addMessage(systemMessage);
                        
                        // Set current scene
                        if (data.scene) {
                            setCurrentScene({
                                name: data.scene.name,
                                description: data.scene.description,
                                center_position: { x: 10, y: 10 },
                                dimensions: { x: 20, y: 20 },
                                objects: [],
                            });
                            console.log('🏰 Scene loaded:', data.scene.name);
                        }
                        
                        // Set active character (first player)
                        if (data.players && data.players.length > 0) {
                            const firstPlayer = data.players[0];
                            const activeChar = {
                                name: firstPlayer.name,
                                race: firstPlayer.race,
                                char_class: firstPlayer.char_class,
                                level: firstPlayer.level,
                                current_hp: firstPlayer.current_hp,
                                max_hp: firstPlayer.max_hp,
                                armor_class: firstPlayer.armor_class,
                                speed: firstPlayer.speed,
                                proficiency_bonus: firstPlayer.proficiency_bonus,
                                initiative_bonus: firstPlayer.initiative_bonus,
                                is_alive: firstPlayer.is_alive,
                                stats: firstPlayer.stats,
                            } as any;
                            setActiveCharacter(activeChar);
                            console.log('🎭 Active character:', activeChar.name);
                        }
                        
                        console.log('💬 DM Message:', dmMessage.text);
                        console.log('💬 System:', systemMessage.text);
                    }
                })
                .catch(err => console.error('Failed to load game info:', err));
        }
    }, []);

    useEffect(() => {
        console.log('🔍 Initializing turn queue, session:', session);
        console.log('🔍 currentSession:', currentSession);
        if (!session && !currentSession) {
            console.log('⚠️ No session available');
            return;
        }
        const activeSession = session || currentSession;
        if (!activeSession) {
            console.log('⚠️ No active session');
            return;
        }
        console.log('📊 Session players:', activeSession.players?.length || 0);
        console.log('📊 Session npcs:', activeSession.npcs?.length || 0);

        const queue: TurnEntry[] = [];
        activeSession.players?.forEach((p: any) => {
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
        activeSession.npcs?.forEach((n: any) => {
            if (!n?.character) return;
            const char = n.character;
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
        queue.sort((a, b) => b.initiative - a.initiative);
        setTurnQueue(queue);
        setCurrentIndex(0);
        console.log('🎯 Turn queue initialized with', queue.length, 'entries');
        console.log('📋 Turn queue entries:', queue.map(e => ({
            name: e.character?.name,
            type: e.type,
            initiative: e.initiative,
            hasCharacter: !!e.character,
            characterKeys: e.character ? Object.keys(e.character) : 'none'
        })));
    }, [session, currentSession]);

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
                    description: undefined,
                    players: data.players.map((p: any) => ({ player_id: p, player_name: p, character_name: undefined })),
                } as any);
                
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

    // ALL useCallback MUST BE BEFORE ANY CONDITIONAL RETURNS
    const getAliveQueue = useCallback(() => {
        const result = turnQueue.filter(entry => !entry.isDead);
        console.log('🔍 getAliveQueue:', {
            turnQueueLength: turnQueue.length,
            aliveLength: result.length,
            entries: result.map(e => ({ name: e.character?.name, isDead: e.isDead, type: e.type }))
        });
        return result;
    }, [turnQueue]);

    const handleDeathAnimation = useCallback((characterName: string) => {
        setDyingCharacters(prev => [...prev, characterName]);
        setTimeout(() => {
            setDyingCharacters(prev => prev.filter(name => name !== characterName));
        }, 1000);
    }, []);

    const performDeathSave = useCallback((characterName: string) => {
        const roll = Math.floor(Math.random() * 20) + 1;
        console.log(`${characterName} death save roll: ${roll}`);
    }, []);

    const advanceTurn = useCallback(() => {
        const queue = turnQueue.filter(entry => !entry.isDead);
        if (queue.length === 0) return;
        const currentChar = queue[currentIndex % queue.length];
        if (currentChar?.isDying) {
            performDeathSave(currentChar.character.name);
        }
        setCurrentIndex(prev => (prev + 1) % queue.length);
    }, [turnQueue, currentIndex, performDeathSave]);

    const handleMouseMove = useCallback((e: MouseEvent) => {
        if (!isResizingLeft && !isResizingRight && !isResizingHeader && !isResizingActionPanel) return;
        if (!containerRef.current) return;
        const container = containerRef.current;
        const containerRect = container.getBoundingClientRect();
        if (isResizingHeader) {
            const deltaY = e.clientY - startY.current;
            const newHeight = startHeaderHeight.current + deltaY;
            const minHeight = window.innerHeight * 0.05;
            const maxHeight = window.innerHeight * 0.10;
            setHeaderHeight(Math.max(minHeight, Math.min(maxHeight, newHeight)));
        } else if (isResizingActionPanel) {
            const deltaY = e.clientY - startY.current;
            const deltaPercent = (deltaY / containerRect.height) * 100;
            const newHeight = startActionPanelHeight.current + deltaPercent;
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
        if (isResizingHeader) {
            const minHeight = window.innerHeight * 0.05;
            const maxHeight = window.innerHeight * 0.10;
            const midpoint = (minHeight + maxHeight) / 2;
            if (headerHeight > midpoint) {
                setHeaderHeight(maxHeight);
            } else {
                setHeaderHeight(minHeight);
            }
        }
        if (isResizingActionPanel) {
            const collapseThreshold = 10;
            if (actionPanelHeight < collapseThreshold) {
                setIsSceneCollapsed(true);
                setActionPanelHeight(0);
            } else {
                setIsSceneCollapsed(false);
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

    // Variables derived from hooks (must be after ALL hooks)
    const aliveQueue = getAliveQueue();
    const currentTurnChar = aliveQueue[currentIndex % aliveQueue.length];

    // Show session creation overlay
    if (showCreateSession && userId) {
        return <SessionCreation userId={parseInt(userId)} onComplete={handleSessionCreated} onBack={() => setShowCreateSession(false)} />;
    }

    // Show profile page
    if (showProfile && userId) {
        return (
            <ProfilePage 
                userId={parseInt(userId)} 
                onBack={() => setShowProfile(false)} 
                onGoHome={() => {
                    setShowProfile(false);
                    // Navigate to home page
                }}
                onJoinSession={onJoinSession} 
            />
        );
    }

    // Check if user has active session (from localStorage)
    const hasActiveSession = sessionId && playerId;

    // Check if game was started (session is running)
    // Only consider game started if we have both sessionId AND playerId
    const isGameStarted = hasActiveSession && gameStatus === 'running';
    
    // Show message if session was lost
    if (sessionNotFound) {
        return (
            <div className="game-layout">
                <div className="no-session-screen">
                    <div className="no-session-content">
                        <h1>⚠️ Session Not Found</h1>
                        <p>The game session could not be loaded from the server.</p>
                        <p className="hint">This may happen if the server was restarted or the session expired.</p>
                        <div className="no-session-actions">
                            <button className="btn-create-session" onClick={() => {
                                localStorage.removeItem('currentSessionId');
                                localStorage.removeItem('currentPlayerId');
                                localStorage.removeItem('gameStatus');
                                setSessionNotFound(false);
                                window.location.reload();
                            }}>
                                🔄 Clear & Start Fresh
                            </button>
                            <button className="btn-join-session" onClick={onCreateSession}>
                                ✨ Create New Session
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

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
                    {aliveQueue && aliveQueue.length > 0 ? (
                        aliveQueue.map((entry, idx) => {
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
                        })
                    ) : (
                        <div className="no-turn-queue">
                            <p>⏳ Waiting for game data...</p>
                            <p className="hint">Turn queue: {turnQueue?.length || 0} | Alive: {aliveQueue?.length || 0}</p>
                            <p className="hint">Session players: {session?.players?.length || 0} | NPCs: {session?.npcs?.length || 0}</p>
                        </div>
                    )}
                </div>

                <div className="header-right">
                    <button className="profile-btn" title="Profile" onClick={() => setShowProfile(true)}>
                        <span className="profile-icon">👤</span>
                    </button>
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
                    onGoHome={() => {
                        setShowProfile(false);
                        // Navigate to home page
                    }}
                />
            )}
        </div>
    );
};
