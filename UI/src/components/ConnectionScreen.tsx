import React, { useState } from 'react';
import { useGameStore } from '../store/gameStore';
import './ConnectionScreen.css';

export const ConnectionScreen: React.FC = () => {
    const [sessionId, setSessionId] = useState('');
    const [playerId, setPlayerId] = useState('');
    const connect = useGameStore((state) => state.connect);

    const handleConnect = (e: React.FormEvent) => {
        e.preventDefault();
        if (sessionId && playerId) {
            connect(sessionId, playerId);
        }
    };

    const handleQuickStart = () => {
        // For development - auto-generate IDs
        const newSessionId = `session_${Math.random().toString(36).substring(7)}`;
        const newPlayerId = `player_${Math.random().toString(36).substring(7)}`;
        setSessionId(newSessionId);
        setPlayerId(newPlayerId);
        connect(newSessionId, newPlayerId);
    };

    return (
        <div className="connection-screen">
            <div className="connection-container">
                <div className="logo">
                    <h1>MAGGxDND</h1>
                    <p className="subtitle">AI-Powered D&D Experience</p>
                </div>

                <form onSubmit={handleConnect} className="connection-form">
                    <div className="form-group">
                        <label htmlFor="sessionId">Session ID</label>
                        <input
                            type="text"
                            id="sessionId"
                            value={sessionId}
                            onChange={(e) => setSessionId(e.target.value)}
                            placeholder="Enter session ID"
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

                    <button type="submit" className="connect-btn">
                        Connect to Game
                    </button>
                </form>

                <div className="divider">
                    <span>OR</span>
                </div>

                <button onClick={handleQuickStart} className="quick-start-btn">
                    Quick Start (Development)
                </button>

                <div className="info-panel">
                    <h3>How to Play</h3>
                    <ol>
                        <li>Enter or create a session ID</li>
                        <li>Enter your player name/ID</li>
                        <li>Connect and wait for your turn</li>
                        <li>Describe your action in natural language</li>
                        <li>The AI Game Master will adjudicate</li>
                    </ol>
                </div>
            </div>
        </div>
    );
};
