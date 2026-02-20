import React, { useState, useRef, useEffect } from 'react';
import { useGameStore } from '../store/gameStore';
import './ChatPanel.css';

interface ChatPanelProps {
    collapsed: boolean;
    onToggle: () => void;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({ collapsed, onToggle }) => {
    const { messages, events } = useGameStore();
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const [filter, setFilter] = useState<'all' | 'dm' | 'players' | 'events'>('all');

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, events]);

    const getFilteredMessages = () => {
        const allMessages = [
            ...messages.map(m => ({ type: 'message' as const, data: m })),
            ...events.map(e => ({ type: 'event' as const, data: e }))
        ];

        switch (filter) {
            case 'dm':
                return allMessages.filter(m =>
                    m.type === 'message' && m.data.sender_name.startsWith('DM')
                );
            case 'players':
                return allMessages.filter(m =>
                    m.type === 'message' && !m.data.sender_name.startsWith('DM')
                );
            case 'events':
                return allMessages.filter(m => m.type === 'event');
            default:
                return allMessages;
        }
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

    const filteredMessages = getFilteredMessages();

    if (collapsed) {
        return (
            <div className="chat-panel collapsed">
                <div className="collapse-toggle" onClick={onToggle}>
                    <span className="toggle-icon" title="Expand panel">💬←</span>
                </div>
                <nav className="icon-nav">
                    <button 
                        className={`nav-icon ${filter === 'all' ? 'active' : ''}`} 
                        title="All messages"
                        onClick={() => {
                            setFilter('all');
                            onToggle();
                        }}
                    >
                        📋
                    </button>
                    <button 
                        className={`nav-icon ${filter === 'dm' ? 'active' : ''}`} 
                        title="DM messages"
                        onClick={() => {
                            setFilter('dm');
                            onToggle();
                        }}
                    >
                        🎙️
                    </button>
                    <button 
                        className={`nav-icon ${filter === 'players' ? 'active' : ''}`} 
                        title="Player messages"
                        onClick={() => {
                            setFilter('players');
                            onToggle();
                        }}
                    >
                        💬
                    </button>
                    <div className="nav-separator" />
                    <button 
                        className={`nav-icon ${filter === 'events' ? 'active' : ''}`} 
                        title="Events only"
                        onClick={() => {
                            setFilter('events');
                            onToggle();
                        }}
                    >
                        ⚡
                    </button>
                    {events.slice(-5).reverse().map((event, idx) => (
                        <button
                            key={idx}
                            className="nav-icon event-icon"
                            title={event.description}
                            onClick={() => onToggle()}
                        >
                            {getEventIcon(event.event_type)}
                        </button>
                    ))}
                </nav>
            </div>
        );
    }

    return (
        <div className="chat-panel">
            <div className="chat-header">
                <h2>💬 Game Log</h2>
                <button className="collapse-toggle-btn" onClick={onToggle} title="Collapse panel">
                    💬←
                </button>
            </div>
            <div className="filter-buttons">
                <button
                    className={filter === 'all' ? 'active' : ''}
                    onClick={() => setFilter('all')}
                >
                    All
                </button>
                <button
                    className={filter === 'dm' ? 'active' : ''}
                    onClick={() => setFilter('dm')}
                >
                    DM
                </button>
                <button
                    className={filter === 'players' ? 'active' : ''}
                    onClick={() => setFilter('players')}
                >
                    Players
                </button>
                <button
                    className={filter === 'events' ? 'active' : ''}
                    onClick={() => setFilter('events')}
                >
                    Events
                </button>
            </div>

            <div className="chat-messages">
                {filteredMessages.length === 0 ? (
                    <div className="no-messages">
                        <p>No messages yet</p>
                        <p className="hint">Game messages will appear here</p>
                    </div>
                ) : (
                    filteredMessages.map((msg, idx) => (
                        <div
                            key={idx}
                            className={`chat-entry ${msg.type} ${
                                msg.type === 'message' && msg.data.sender_name.startsWith('DM')
                                    ? 'dm-message'
                                    : ''
                            }`}
                        >
                            {msg.type === 'message' ? (
                                <div className="message-content">
                                    <span className="sender">{msg.data.sender_name}</span>
                                    <span className="text">{msg.data.text}</span>
                                </div>
                            ) : (
                                <div className="event-content">
                                    <span className="event-icon">
                                        {getEventIcon(msg.data.event_type)}
                                    </span>
                                    <span className="event-text">{msg.data.description}</span>
                                </div>
                            )}
                        </div>
                    ))
                )}
                <div ref={messagesEndRef} />
            </div>
        </div>
    );
};
