import React, { useState } from 'react';
import { useGameStore } from '../store/gameStore';
import './ActionPanel.css';

export const ActionPanel: React.FC = () => {
    const { activeCharacter, sendAction, isActionPending, clarificationText } = useGameStore();
    const [actionText, setActionText] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (activeCharacter && actionText.trim()) {
            sendAction(actionText.trim(), activeCharacter);
            setActionText('');
        }
    };

    if (!activeCharacter) {
        return (
            <div className="action-panel">
                <div className="no-action">
                    <p>⏳ Waiting for your turn...</p>
                    <p className="hint">The Game Master will prompt you when it's time to act</p>
                </div>
            </div>
        );
    }

    return (
        <div className="action-panel">
            <div className="action-panel-content">
                {clarificationText && (
                    <div className="clarification-box">
                        <span className="clarification-icon">❓</span>
                        <p className="clarification-text">{clarificationText}</p>
                    </div>
                )}

                <form onSubmit={handleSubmit} className="action-form">
                    <div className="form-group">
                        <textarea
                            id="action-input"
                            value={actionText}
                            onChange={(e) => setActionText(e.target.value)}
                            placeholder="Describe your action..."
                            rows={3}
                            disabled={isActionPending}
                        />
                    </div>

                    <div className="action-buttons">
                        <button
                            type="submit"
                            className="submit-btn"
                            disabled={!actionText.trim() || isActionPending}
                        >
                            {isActionPending ? 'Processing...' : 'Submit'}
                        </button>
                        <button
                            type="button"
                            className="clear-btn"
                            onClick={() => setActionText('')}
                            disabled={isActionPending}
                        >
                            Clear
                        </button>
                        <button
                            type="button"
                            className="skip-btn"
                            onClick={() => setActionText('')}
                            disabled={isActionPending}
                        >
                            Skip Turn
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};
