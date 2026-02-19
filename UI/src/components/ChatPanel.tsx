import React, { useState, useRef, useEffect } from 'react';
import { useGameStore } from '../store/gameStore';
import './ChatPanel.css';

export const ChatPanel: React.FC = () => {
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

    return (
        <div className="chat-panel">
            <div className="chat-header">
                <h2>💬 Game Log</h2>
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
