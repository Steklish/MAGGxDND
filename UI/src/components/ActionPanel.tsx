import React, { useState, useRef } from 'react';
import { useGameStore } from '../store/gameStore';
import './ActionPanel.css';

export const ActionPanel: React.FC = () => {
    const { activeCharacter, sendAction, isActionPending, clarificationText, events, messages } = useGameStore();
    const [actionText, setActionText] = useState('');
    const [panelHeight, setPanelHeight] = useState(200);
    const [isResizing, setIsResizing] = useState(false);
    const [startY, setStartY] = useState(0);
    const [startHeight, setStartHeight] = useState(0);
    const panelRef = useRef<HTMLDivElement>(null);

    const handleResizeStart = (e: React.MouseEvent) => {
        e.preventDefault();
        setIsResizing(true);
        setStartY(e.clientY);
        setStartHeight(panelHeight);
    };

    React.useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (!isResizing) return;
            const deltaY = startY - e.clientY;
            const newHeight = Math.max(120, Math.min(400, startHeight + deltaY));
            setPanelHeight(newHeight);
        };

        const handleMouseUp = () => {
            setIsResizing(false);
        };

        if (isResizing) {
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
            return () => {
                document.removeEventListener('mousemove', handleMouseMove);
                document.removeEventListener('mouseup', handleMouseUp);
            };
        }
    }, [isResizing, startY, startHeight]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (activeCharacter && actionText.trim()) {
            sendAction(actionText.trim(), activeCharacter);
            setActionText('');
        }
    };

    const handleSkipTurn = () => {
        // Skip turn action
        console.log('Turn skipped');
    };

    // Get game log entries (combine messages and events)
    const getGameLog = () => {
        const allEntries = [
            ...messages.map(m => ({ type: 'message' as const, data: m, timestamp: Date.now() })),
            ...events.map(e => ({ type: 'event' as const, data: e, timestamp: Date.now() }))
        ];
        return allEntries.slice(-20).reverse();
    };

    const getEventIcon = (eventType: string) => {
        const icons: Record<string, string> = {
            'CHARACTER_MOVEMENT': '👣',
            'CHARACTER_MELEE_ATTACK': '⚔️',
            'CHARACTER_RANGED_ATTACK': '🏹',
            'CHARACTER_DEATH': '💀',
            'CHARACTER_STATUS_CHANGE': '✨',
            'ITEM_PICKUP': '🎒',
            'ITEM_DROP': '📦',
            'ACTION_RESULT': '✓',
            'SYSTEM': '⚙️',
        };
        return icons[eventType] || '📋';
    };

    if (!activeCharacter) {
        return (
            <div className="action-panel" ref={panelRef} style={{ height: `${panelHeight}px` }}>
                <div className="no-action">
                    <p>⏳ Waiting for your turn...</p>
                    <p className="hint lore-font">The Game Master will prompt you when it's time to act</p>
                </div>
                <div
                    className="resize-handle-top"
                    onMouseDown={handleResizeStart}
                />
            </div>
        );
    }

    const gameLog = getGameLog();

    return (
        <div className="action-panel" ref={panelRef} style={{ height: `${panelHeight}px` }}>
            <div className="action-header">
                <div className="active-character">
                    <span className="character-icon">🎯</span>
                    <span className="character-info">
                        <strong>{activeCharacter.name}</strong>
                        <span className="character-position">
                            Position: ({activeCharacter.position.x}, {activeCharacter.position.y})
                        </span>
                    </span>
                </div>
                {isActionPending && (
                    <span className="pending-indicator">⏳ Processing...</span>
                )}
            </div>

            {clarificationText && (
                <div className="clarification-box">
                    <span className="clarification-icon">❓</span>
                    <p className="clarification-text lore-font">{clarificationText}</p>
                </div>
            )}

            <form onSubmit={handleSubmit} className="action-form">
                <div className="form-group">
                    <label htmlFor="action-input">Describe your action:</label>
                    <textarea
                        id="action-input"
                        value={actionText}
                        onChange={(e) => setActionText(e.target.value)}
                        placeholder="I want to investigate the strange markings on the wall..."
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
                        {isActionPending ? 'Processing...' : 'Submit Action'}
                    </button>
                    <button
                        type="button"
                        className="skip-btn"
                        onClick={handleSkipTurn}
                        disabled={isActionPending}
                    >
                        Skip Turn
                    </button>
                    <button
                        type="button"
                        className="clear-btn"
                        onClick={() => setActionText('')}
                        disabled={isActionPending}
                    >
                        Clear
                    </button>
                </div>
            </form>

            {/* Game Log */}
            <div className="game-log-section">
                <h4 className="game-log-title">📜 Recent Events</h4>
                <div className="game-log-list">
                    {gameLog.length === 0 ? (
                        <p className="no-log">No events yet</p>
                    ) : (
                        gameLog.map((entry, idx) => (
                            <div
                                key={idx}
                                className={`log-entry ${entry.type} ${
                                    entry.type === 'message' && entry.data.sender_name.startsWith('DM')
                                        ? 'dm-message'
                                        : ''
                                }`}
                            >
                                {entry.type === 'message' ? (
                                    <div className="log-content">
                                        <span className="log-sender">{entry.data.sender_name}</span>
                                        <span className="log-text">{entry.data.text}</span>
                                    </div>
                                ) : (
                                    <div className="log-content">
                                        <span className="log-icon">
                                            {getEventIcon(entry.data.event_type)}
                                        </span>
                                        <span className="log-text">{entry.data.description}</span>
                                    </div>
                                )}
                            </div>
                        ))
                    )}
                </div>
            </div>

            <div
                className="resize-handle-top"
                onMouseDown={handleResizeStart}
            />
        </div>
    );
};
