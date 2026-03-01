import React, { useState, useRef, useEffect } from 'react';
import { useGameStore } from '../store/gameStore';
import './ActionPanel.css';

export const ActionPanel: React.FC = () => {
    const { activeCharacter, sendAction, isActionPending, clarificationText, messages, getMessageType } = useGameStore();
    const [actionText, setActionText] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (activeCharacter && actionText.trim()) {
            sendAction(actionText.trim(), activeCharacter);
            setActionText('');
        }
    };

    const getMessageClassName = (type: string) => {
        switch (type) {
            case 'dm': return 'dialogue-message dm-message';
            case 'player': return 'dialogue-message player-message';
            case 'ally_npc': return 'dialogue-message ally-npc-message';
            case 'hostile_npc': return 'dialogue-message hostile-npc-message';
            case 'neutral_npc': return 'dialogue-message neutral-npc-message';
            case 'environment': return 'dialogue-message environment-message';
            default: return 'dialogue-message';
        }
    };

    const getMessageColor = (type: string) => {
        switch (type) {
            case 'dm': return 'var(--accent-orange)';
            case 'player': return 'var(--accent-purple)';
            case 'ally_npc': return 'var(--accent-green)';
            case 'hostile_npc': return 'var(--accent-red)';
            case 'neutral_npc': return 'var(--accent-yellow)';
            case 'environment': return 'var(--text-primary)';
            default: return 'var(--text-secondary)';
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
                {/* Dialogue messages area */}
                <div className="dialogue-messages">
                    {messages.length === 0 ? (
                        <p className="no-dialogue">No dialogue yet</p>
                    ) : (
                        messages.map((msg, idx) => {
                            const msgType = msg.type || getMessageType(msg.sender_name);
                            return (
                                <div
                                    key={idx}
                                    className={getMessageClassName(msgType)}
                                    style={{ borderLeftColor: getMessageColor(msgType) }}
                                >
                                    <span className="dialogue-sender" style={{ color: getMessageColor(msgType) }}>
                                        {msg.sender_name}
                                    </span>
                                    <span className="dialogue-text">{msg.text}</span>
                                </div>
                            );
                        })
                    )}
                    <div ref={messagesEndRef} />
                </div>

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
