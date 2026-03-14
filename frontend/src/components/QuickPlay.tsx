import React, { useState } from 'react';
import './QuickPlay.css';

interface QuickPlayProps {
    onJoinGame: (sessionId: string) => void;
    onCreateGame: () => void;
    onClose: () => void;
}

export const QuickPlay: React.FC<QuickPlayProps> = ({ onJoinGame, onCreateGame, onClose }) => {
    const [mode, setMode] = useState<'join' | 'create'>('join');
    const [sessionId, setSessionId] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    const quickSessions = [
        { id: 'qs1', name: 'Dragon\'s Lair', players: '2/5', mode: 'Combat', level: '5-10' },
        { id: 'qs2', name: 'Mystery Manor', players: '1/4', mode: 'Mystery', level: '1-5' },
        { id: 'qs3', name: 'Epic Quest', players: '3/6', mode: 'Story', level: '10-15' },
    ];

    const handleQuickJoin = async (sessionId: string) => {
        setIsLoading(true);
        try {
            await onJoinGame(sessionId);
        } catch (err) {
            setError('Failed to join session');
        } finally {
            setIsLoading(false);
        }
    };

    const handleQuickCreate = () => {
        setMode('create');
    };

    return (
        <div className="quick-play-overlay" onClick={onClose}>
            <div className="quick-play-modal" onClick={(e) => e.stopPropagation()}>
                <div className="quick-play-header">
                    <h2>⚡ Quick Play</h2>
                    <button className="qp-close" onClick={onClose}>✕</button>
                </div>

                <div className="qp-mode-selector">
                    <button 
                        className={`qp-mode-btn ${mode === 'join' ? 'active' : ''}`}
                        onClick={() => setMode('join')}
                    >
                        🚪 Join Game
                    </button>
                    <button 
                        className={`qp-mode-btn ${mode === 'create' ? 'active' : ''}`}
                        onClick={handleQuickCreate}
                    >
                        ⚔️ Create Game
                    </button>
                </div>

                {mode === 'join' ? (
                    <div className="qp-content">
                        <div className="qp-section">
                            <h3>🔗 Join by Session ID</h3>
                            <div className="qp-input-group">
                                <input
                                    type="text"
                                    className="qp-input"
                                    placeholder="Enter Session ID"
                                    value={sessionId}
                                    onChange={(e) => setSessionId(e.target.value)}
                                />
                                <button 
                                    className="qp-btn-primary"
                                    onClick={() => handleQuickJoin(sessionId)}
                                    disabled={!sessionId || isLoading}
                                >
                                    {isLoading ? 'Joining...' : 'Join'}
                                </button>
                            </div>
                        </div>

                        <div className="qp-divider">
                            <span>OR</span>
                        </div>

                        <div className="qp-section">
                            <h3>🎮 Quick Join Sessions</h3>
                            <div className="qp-sessions-list">
                                {quickSessions.map((session) => (
                                    <div key={session.id} className="qp-session-card">
                                        <div className="qp-session-info">
                                            <h4>{session.name}</h4>
                                            <div className="qp-session-tags">
                                                <span className="qp-tag">{session.mode}</span>
                                                <span className="qp-tag">Lvl {session.level}</span>
                                                <span className="qp-tag">{session.players}</span>
                                            </div>
                                        </div>
                                        <button 
                                            className="qp-btn-join"
                                            onClick={() => handleQuickJoin(session.id)}
                                            disabled={isLoading}
                                        >
                                            Join
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="qp-content">
                        <div className="qp-create-options">
                            <div 
                                className="qp-create-card"
                                onClick={() => {
                                    onCreateGame();
                                    onClose();
                                }}
                            >
                                <div className="qp-create-icon">🏰</div>
                                <h4>Custom Session</h4>
                                <p>Create a fully customized session with your own settings</p>
                            </div>

                            <div 
                                className="qp-create-card featured"
                                onClick={() => handleQuickJoin('quick-adventure')}
                            >
                                <div className="qp-create-icon">⚡</div>
                                <h4>Quick Adventure</h4>
                                <p>AI-generated one-shot adventure (1-2 hours)</p>
                                <span className="qp-featured-badge">Recommended</span>
                            </div>

                            <div 
                                className="qp-create-card"
                                onClick={() => handleQuickJoin('quick-campaign')}
                            >
                                <div className="qp-create-icon">📖</div>
                                <h4>Quick Campaign</h4>
                                <p>Start an ongoing campaign with AI dungeon master</p>
                            </div>
                        </div>
                    </div>
                )}

                {error && (
                    <div className="qp-error">
                        ⚠️ {error}
                    </div>
                )}
            </div>
        </div>
    );
};
