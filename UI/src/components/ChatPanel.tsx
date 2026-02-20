import React, { useState, useRef, useEffect } from 'react';
import { useGameStore } from '../store/gameStore';
import { Tooltip } from './common/Tooltip';
import './ChatPanel.css';

interface ChatPanelProps {
    collapsed: boolean;
    onToggle: () => void;
}

interface FilterTooltipContentProps {
    filter: 'all' | 'dm' | 'players' | 'events';
}

const FilterTooltipContent: React.FC<FilterTooltipContentProps> = ({ filter }) => {
    const filterInfo: Record<string, { title: string; description: string; icon: string }> = {
        'all': {
            title: 'All Messages',
            description: 'Show all messages including DM narration, player actions, and game events.',
            icon: '📋'
        },
        'dm': {
            title: 'DM Messages',
            description: 'Show only messages from the Dungeon Master (narration, rulings, clarifications).',
            icon: '🎙️'
        },
        'players': {
            title: 'Player Messages',
            description: 'Show only messages from players (character dialogue, actions, meta comments).',
            icon: '💬'
        },
        'events': {
            title: 'Game Events',
            description: 'Show only game events (movement, attacks, item pickups, status changes).',
            icon: '⚡'
        }
    };

    const info = filterInfo[filter];

    return (
        <div className="filter-tooltip">
            <div className="filter-tooltip-title">
                <div className="filter-tooltip-icon">
                    <span>{info.icon}</span>
                    <span>{info.title}</span>
                </div>
            </div>
            <p className="filter-tooltip-description">{info.description}</p>
        </div>
    );
};

interface EventTooltipContentProps {
    event: any;
}

const EventTooltipContent: React.FC<EventTooltipContentProps> = ({ event }) => {
    const eventInfo: Record<string, { title: string; description: string; icon: string }> = {
        'CHARACTER_MOVEMENT': { title: 'Movement', description: 'A character moved to a new location', icon: '👣' },
        'CHARACTER_MELEE_ATTACK': { title: 'Melee Attack', description: 'A character made a melee attack', icon: '⚔️' },
        'CHARACTER_RANGED_ATTACK': { title: 'Ranged Attack', description: 'A character made a ranged attack', icon: '🏹' },
        'CHARACTER_DEATH': { title: 'Death', description: 'A character has died', icon: '💀' },
        'CHARACTER_STATUS_CHANGE': { title: 'Status Change', description: 'A character\'s status has changed', icon: '✨' },
        'ITEM_PICKUP': { title: 'Item Pickup', description: 'An item was picked up', icon: '🎒' },
        'ITEM_DROP': { title: 'Item Drop', description: 'An item was dropped', icon: '📦' },
        'ACTION_RESULT': { title: 'Action Result', description: 'Result of a character action', icon: '✓' },
        'SYSTEM': { title: 'System', description: 'System message', icon: '⚙️' },
    };

    const info = eventInfo[event.event_type] || { title: 'Event', description: 'A game event occurred', icon: '📋' };

    return (
        <div className="filter-tooltip">
            <div className="filter-tooltip-title">
                <div className="filter-tooltip-icon">
                    <span>{info.icon}</span>
                    <span>{info.title}</span>
                </div>
            </div>
            <p className="filter-tooltip-description" style={{ marginTop: '8px', fontWeight: '600' }}>
                {event.description}
            </p>
            {event.event_initiator && (
                <p className="filter-tooltip-description" style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                    Initiator: {event.event_initiator}
                </p>
            )}
        </div>
    );
};

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
                <nav className="icon-nav">
                    <Tooltip 
                        content={<FilterTooltipContent filter="all" />}
                        position="right"
                    >
                        <button
                            className={`nav-icon ${filter === 'all' ? 'active' : ''}`}
                            onClick={() => {
                                setFilter('all');
                                onToggle();
                            }}
                        >
                            📋
                        </button>
                    </Tooltip>
                    <Tooltip 
                        content={<FilterTooltipContent filter="dm" />}
                        position="right"
                    >
                        <button
                            className={`nav-icon ${filter === 'dm' ? 'active' : ''}`}
                            onClick={() => {
                                setFilter('dm');
                                onToggle();
                            }}
                        >
                            🎙️
                        </button>
                    </Tooltip>
                    <Tooltip 
                        content={<FilterTooltipContent filter="players" />}
                        position="right"
                    >
                        <button
                            className={`nav-icon ${filter === 'players' ? 'active' : ''}`}
                            onClick={() => {
                                setFilter('players');
                                onToggle();
                            }}
                        >
                            💬
                        </button>
                    </Tooltip>
                    <div className="nav-separator" />
                    <Tooltip 
                        content={<FilterTooltipContent filter="events" />}
                        position="right"
                    >
                        <button
                            className={`nav-icon ${filter === 'events' ? 'active' : ''}`}
                            onClick={() => {
                                setFilter('events');
                                onToggle();
                            }}
                        >
                            ⚡
                        </button>
                    </Tooltip>
                    {events.slice(-5).reverse().map((event, idx) => (
                        <Tooltip 
                            key={idx}
                            content={<EventTooltipContent event={event} />}
                            position="right"
                        >
                            <button
                                className="nav-icon event-icon"
                                onClick={() => onToggle()}
                            >
                                {getEventIcon(event.event_type)}
                            </button>
                        </Tooltip>
                    ))}
                </nav>
            </div>
        );
    }

    return (
        <div className="chat-panel">
            <div className="chat-header">
                <h2>💬 Game Log</h2>
            </div>
            <div className="filter-buttons">
                <Tooltip content={<FilterTooltipContent filter="all" />} position="bottom">
                    <button
                        className={filter === 'all' ? 'active' : ''}
                        onClick={() => setFilter('all')}
                    >
                        📋 All
                    </button>
                </Tooltip>
                <Tooltip content={<FilterTooltipContent filter="dm" />} position="bottom">
                    <button
                        className={filter === 'dm' ? 'active' : ''}
                        onClick={() => setFilter('dm')}
                    >
                        🎙️ DM
                    </button>
                </Tooltip>
                <Tooltip content={<FilterTooltipContent filter="players" />} position="bottom">
                    <button
                        className={filter === 'players' ? 'active' : ''}
                        onClick={() => setFilter('players')}
                    >
                        💬 Players
                    </button>
                </Tooltip>
                <Tooltip content={<FilterTooltipContent filter="events" />} position="bottom">
                    <button
                        className={filter === 'events' ? 'active' : ''}
                        onClick={() => setFilter('events')}
                    >
                        ⚡ Events
                    </button>
                </Tooltip>
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
                                <Tooltip 
                                    content={<EventTooltipContent event={msg.data} />}
                                    position="right"
                                >
                                    <div className="event-content-with-tooltip">
                                        <div className="event-content">
                                            <span className="event-icon">
                                                {getEventIcon(msg.data.event_type)}
                                            </span>
                                            <span className="event-text">{msg.data.description}</span>
                                        </div>
                                    </div>
                                </Tooltip>
                            )}
                        </div>
                    ))
                )}
                <div ref={messagesEndRef} />
            </div>
        </div>
    );
};
