import React, { useState } from 'react';
import { useGameStore } from '../store/gameStore';
import './ConnectionScreen.css';

export const ConnectionScreen: React.FC = () => {
    const [sessionId, setSessionId] = useState('');
    const [playerId, setPlayerId] = useState('');
    const [playerName, setPlayerName] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    // const connect = useGameStore((state) => state.connect);
    const createSession = useGameStore((state) => state.createSession);
    const joinSession = useGameStore((state) => state.joinSession);

    // const handleConnect = async (e: React.FormEvent) => {
    //     e.preventDefault();
    //     if (!sessionId || !playerId) return;

    //     setIsLoading(true);
    //     setError('');

    //     try {
    //         await connect(sessionId, playerId);
    //     } catch (err) {
    //         setError(err instanceof Error ? err.message : 'Connection failed');
    //         setIsLoading(false);
    //     }
    // };

    const handleCreateSession = async () => {
        setIsLoading(true);
        setError('');

        try {
            // Create a new session
            const session = await createSession({
                session_name: playerName ? `${playerName}'s Session` : 'New Session',
                game_mode: 'STORY',
                max_players: 5,
            });

            const newSessionId = session.session_id;
            setSessionId(newSessionId);

            // Join the session as a player
            await joinSession(newSessionId, playerName || 'Player');
            const newPlayerId = playerId; // Use the playerId from state

            setPlayerId(newPlayerId);

            // Connect to the session
            // await connect(newSessionId, newPlayerId || 'player_1');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create session');
            setIsLoading(false);
        }
    };

    const handleQuickStart = async () => {
        // Quick start with auto-generated IDs
        const newSessionId = `session_${Math.random().toString(36).substring(7)}`;
        const newPlayerId = `player_${Math.random().toString(36).substring(7)}`;
        
        setIsLoading(true);
        setError('');
        
        try {
            // await connect(newSessionId, newPlayerId);
            // Quick start disabled - use create session instead
            setError('Quick start disabled. Please create a session.');
            setIsLoading(false);
            return;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Connection failed');
            setIsLoading(false);
        }
    };

    return (
        <div className="connection-screen">
            <div className="connection-container">
                <div className="logo">
                    <h1>MAGGxDND</h1>
                    <p className="subtitle">AI-Powered D&D Experience</p>
                </div>

                {error && (
                    <div className="error-message">
                        <p>{error}</p>
                        <button onClick={() => setError('')} className="close-error">
                            ×
                        </button>
                    </div>
                )}

                <form onSubmit={(e) => { e.preventDefault(); setError('Connection disabled. Please create a new session.'); }} className="connection-form">
                    <div className="form-group">
                        <label htmlFor="playerName">Your Name (Optional)</label>
                        <input
                            type="text"
                            id="playerName"
                            value={playerName}
                            onChange={(e) => setPlayerName(e.target.value)}
                            placeholder="Enter your name"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="sessionId">Session ID</label>
                        <input
                            type="text"
                            id="sessionId"
                            value={sessionId}
                            onChange={(e) => setSessionId(e.target.value)}
                            placeholder="Enter or create session ID"
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="playerId">Player ID</label>
                        <input
                            type="text"
                            id="playerId"
                            value={playerId}
                            onChange={(e) => setPlayerId(e.target.value)}
                            placeholder="Enter your player ID"
                            required
                        />
                    </div>

                    <button 
                        type="submit" 
                        className="connect-btn"
                        disabled={isLoading}
                    >
                        {isLoading ? 'Connecting...' : 'Connect to Game'}
                    </button>
                </form>

                <div className="divider">
                    <span>OR</span>
                </div>

                <button 
                    onClick={handleCreateSession} 
                    className="create-session-btn"
                    disabled={isLoading || !playerName}
                >
                    Create New Session
                </button>

                <button 
                    onClick={handleQuickStart} 
                    className="quick-start-btn"
                    disabled={isLoading}
                >
                    Quick Start (Development)
                </button>

                <div className="info-panel">
                    <h3>How to Play</h3>
                    <ol>
                        <li>Enter your name (optional)</li>
                        <li>Create a new session or enter an existing session ID</li>
                        <li>Connect and wait for your turn</li>
                        <li>Describe your action in natural language</li>
                        <li>The AI Game Master will adjudicate</li>
                    </ol>
                </div>
            </div>
        </div>
    );
};
