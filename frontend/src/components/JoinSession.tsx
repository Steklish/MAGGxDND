import React, { useState, useEffect } from 'react';
import { useGameStore } from '../store/gameStore';
import { sessionAPI, PlayerInfo } from '../services/sessionAPI';
import './JoinSession.css';

type JoinMode = 'select' | 'profile' | 'ai' | 'joining' | 'done';

export const JoinSession: React.FC<{ sessionId: string; onJoined: () => void; onBack: () => void }> = ({ sessionId, onJoined, onBack }) => {
    const { username } = useGameStore();
    const [mode, setMode] = useState<JoinMode>('select');
    const [error, setError] = useState<string | null>(null);
    const [playerInfo, setPlayerInfo] = useState<PlayerInfo | null>(null);
    const [profiles, setProfiles] = useState<any[]>([]);
    const [selectedProfileId, setSelectedProfileId] = useState<number | null>(null);
    const [aiDescription, setAiDescription] = useState('');
    const [checkingRejoin, setCheckingRejoin] = useState(true);

    useEffect(() => {
        loadProfiles();
        checkRejoin();
    }, []);

    // Check if user already joined this session (rejoin case)
    const checkRejoin = async () => {
        try {
            const token = localStorage.getItem('access_token');

            // First check: does the backend already know us as a participant?
            const resp = await fetch(`/api/v1/sessions/${sessionId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (resp.ok) {
                const data = await resp.json();
                // The backend returns `is_owner` and a players list.
                // For rejoin: check if any player entry matches our session participant record.
                // We use the player_name as the match key since that's what the user typed originally.
                const ourPlayer = data.players?.find(
                    (p: any) => p.player_name === username
                );

                if (ourPlayer?.player_id && ourPlayer.character_name) {
                    // User already has a character in this session — auto-rejoin
                    localStorage.setItem(`playerId_${sessionId}`, ourPlayer.player_id);
                    localStorage.setItem('currentPlayerId', ourPlayer.player_id);
                    localStorage.setItem('currentSessionId', sessionId);
                    localStorage.setItem('gameStatus', 'running');

                    // Load game info
                    const gameResp = await fetch(`/api/v1/sessions/${sessionId}/game_info`, {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    if (gameResp.ok) {
                        const gameInfo = await gameResp.json();
                        useGameStore.getState().setCurrentSession(gameInfo);
                        if (gameInfo.current_scene) {
                            useGameStore.getState().setCurrentScene(gameInfo.current_scene);
                        }
                    }

                    // Connect WebSocket and go to game
                    useGameStore.getState().connectWebSocket(sessionId, ourPlayer.player_id);
                    onJoined();
                    return;
                }
            }
        } catch {
            // Failed to check — just proceed to join UI
        }
        setCheckingRejoin(false);
    };

    const loadProfiles = async () => {
        try {
            const userId = useGameStore.getState().userId;
            if (userId) {
                await useGameStore.getState().loadCharacterProfiles(userId);
                setProfiles(Array.from(useGameStore.getState().characterProfiles.values()));
            }
        } catch {
            // Profiles not available
        }
    };

    const handleJoin = async (joinFn: () => Promise<PlayerInfo>) => {
        setMode('joining');
        setError(null);
        try {
            const player = await joinFn();
            setPlayerInfo(player);
            // Write BOTH keys so GameLayout can find it on reload
            localStorage.setItem(`playerId_${sessionId}`, player.player_id);
            localStorage.setItem('currentPlayerId', player.player_id);
            localStorage.setItem('currentSessionId', sessionId);
            localStorage.setItem('gameStatus', 'running');

            // Load game info and navigate
            const token = localStorage.getItem('access_token');
            const gameResp = await fetch(`/api/v1/sessions/${sessionId}/game_info`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (gameResp.ok) {
                const gameInfo = await gameResp.json();
                useGameStore.getState().setCurrentSession(gameInfo);
                if (gameInfo.current_scene) {
                    useGameStore.getState().setCurrentScene(gameInfo.current_scene);
                }
            }

            useGameStore.getState().connectWebSocket(sessionId, player.player_id);
            setMode('done');
            onJoined();
        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || 'Failed to join');
            setMode('select');
        }
    };

    if (checkingRejoin) {
        return (
            <div className="join-session-page">
                <div className="join-session-container">
                    <div className="join-session-title-card">
                        <h2>Checking session...</h2>
                        <div className="dice-loader" />
                    </div>
                </div>
            </div>
        );
    }

    if (mode === 'joining') {
        return (
            <div className="join-session-page">
                <div className="join-session-container">
                    <div className="join-session-title-card">
                        <h2>Joining session...</h2>
                        <div className="dice-loader" />
                    </div>
                </div>
            </div>
        );
    }

    if (mode === 'done' && playerInfo) {
        return (
            <div className="join-session-page">
                <div className="join-session-container">
                    <div className="join-session-title-card">
                        <h2>✓ Joined as {playerInfo.character_name}!</h2>
                        <p>Connecting to the game...</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="join-session-page">
            <div className="join-session-bg"></div>
            <div className="join-session-content">
                <header className="join-session-header">
                    <button className="btn-back" onClick={onBack}>← Back</button>
                    <h1>Join Session</h1>
                </header>

                <div className="join-session-container">
                    <div className="join-session-title-card">
                        <h2>Choose how to join</h2>
                    </div>

                    {error && <div className="error-message">{error}</div>}

                    <div className="join-options-grid">
                        <div className="join-option" onClick={() => setMode('profile')}>
                            <div className="join-option-icon">📋</div>
                            <div className="join-option-text">
                                <h3>From My Templates</h3>
                                <p>
                                    {profiles.length > 0
                                        ? `Choose from ${profiles.length} saved character${profiles.length > 1 ? 's' : ''}`
                                        : 'Choose from your saved character profiles'}
                                </p>
                            </div>
                        </div>

                        <div className="join-option" onClick={() => setMode('ai')}>
                            <div className="join-option-icon">✨</div>
                            <div className="join-option-text">
                                <h3>AI Generated</h3>
                                <p>Describe your character and AI will create it</p>
                            </div>
                        </div>
                    </div>

                    {mode === 'profile' && (
                        <div className="join-form">
                            <h3>Select Character Profile</h3>
                            <select
                                value={selectedProfileId || ''}
                                onChange={e => setSelectedProfileId(Number(e.target.value))}
                            >
                                <option value="">— Choose a profile —</option>
                                {profiles.map(p => (
                                    <option key={p.id} value={p.id}>{p.name}</option>
                                ))}
                            </select>
                            <div className="join-form-actions">
                                <button
                                    className="btn-join"
                                    disabled={!selectedProfileId}
                                    onClick={() => handleJoin(() =>
                                        sessionAPI.joinSessionWithProfile(sessionId, {
                                            player_name: username || 'Adventurer',
                                            profile_id: selectedProfileId!
                                        })
                                    )}
                                >
                                    Join with this character
                                </button>
                                <button className="btn-cancel" onClick={() => setMode('select')}>Cancel</button>
                            </div>
                        </div>
                    )}

                    {mode === 'ai' && (
                        <div className="join-form">
                            <h3>Describe Your Character</h3>
                            <textarea
                                value={aiDescription}
                                onChange={e => setAiDescription(e.target.value)}
                                placeholder="E.g., A grumpy dwarven blacksmith who lost his forge and seeks revenge against the dragon that destroyed it..."
                                rows={4}
                            />
                            <div className="join-form-actions">
                                <button
                                    className="btn-join"
                                    disabled={aiDescription.length < 10}
                                    onClick={() => handleJoin(() =>
                                        sessionAPI.joinSessionAIGenerate(sessionId, {
                                            player_name: username || 'Adventurer',
                                            character_description: aiDescription
                                        })
                                    )}
                                >
                                    Generate & Join
                                </button>
                                <button className="btn-cancel" onClick={() => setMode('select')}>Cancel</button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
