import React, { useState, useRef, useEffect } from 'react';
import { useGameStore } from '../store/gameStore';
import './ActionPanel.css';

export const ActionPanel: React.FC = () => {
    const { activeCharacter, sendAction, isActionPending, clarificationText, messages, getMessageType, isDMThinking } = useGameStore();
    const [actionText, setActionText] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const dialogueContainerRef = useRef<HTMLDivElement>(null);

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

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        // Submit on Enter (without Shift)
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
        // Shift+Enter adds a newline (default behavior)
    };

    const getMessageClassName = (type: string, isPlayer: boolean) => {
        const baseClass = 'dialogue-message';
        const alignClass = isPlayer ? 'player-align' : 'npc-align';
        
        switch (type) {
            case 'dm': return `${baseClass} ${alignClass} dm-message`;
            case 'player': return `${baseClass} ${alignClass} player-message`;
            case 'ally_npc': return `${baseClass} ${alignClass} ally-npc-message`;
            case 'hostile_npc': return `${baseClass} ${alignClass} hostile-npc-message`;
            case 'neutral_npc': return `${baseClass} ${alignClass} neutral-npc-message`;
            case 'environment': return `${baseClass} ${alignClass} environment-message`;
            default: return `${baseClass} ${alignClass}`;
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

    const isPlayerMessage = (type: string) => {
        return type === 'player';
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
                {/* Dialogue messages area - oldest at top, newest at bottom */}
                <div className="dialogue-messages" ref={dialogueContainerRef}>
                    {messages.length === 0 ? (
                        <p className="no-dialogue">No dialogue yet</p>
                    ) : (
                        messages.map((msg, idx) => {
                            const msgType = (msg.type || getMessageType(msg.sender_name || '')) as string;
                            const isPlayer = isPlayerMessage(msgType);
                            const senderName = msg.sender_name || 'Unknown';
                            const messageText = msg.text || '';
                            return (
                                <div
                                    key={idx}
                                    className={getMessageClassName(msgType, isPlayer)}
                                    style={{ borderLeftColor: isPlayer ? 'transparent' : getMessageColor(msgType), borderRightColor: isPlayer ? getMessageColor(msgType) : 'transparent' }}
                                >
                                    <span className="dialogue-sender" style={{ color: getMessageColor(msgType) }}>
                                        {senderName}
                                    </span>
                                    <span className="dialogue-text">{messageText}</span>
                                </div>
                            );
                        })
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* DM Thinking Animation */}
                {isDMThinking && (
                    <div className="dm-thinking">
                        <div className="thinking-dots">
                            <span className="dot">•</span>
                            <span className="dot">•</span>
                            <span className="dot">•</span>
                            <span className="dot">•</span>
                        </div>
                        <span className="thinking-text">DM is thinking...</span>
                    </div>
                )}

                {clarificationText && (
                    <div className="clarification-box">
                        <span className="clarification-icon">❓</span>
                        <p className="clarification-text">{clarificationText}</p>
                    </div>
                )}

                {/* Action form at the bottom */}
                <form onSubmit={handleSubmit} className="action-form">
                    <div className="form-group">
                        <textarea
                            id="action-input"
                            value={actionText}
                            onChange={(e) => setActionText(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Describe your action... (Enter to send, Shift+Enter for new line)"
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
