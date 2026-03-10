import React, { useState } from 'react';
import { useGameStore } from '../store/gameStore';
import { Tooltip } from './common/Tooltip';
import './MiniChatPanel.css';

interface EventMiniTooltipProps {
    event: any;
}

const EventMiniTooltip: React.FC<EventMiniTooltipProps> = ({ event }) => {
    const eventInfo: Record<string, { title: string; icon: string }> = {
        'CHARACTER_MOVEMENT': { title: 'Movement', icon: '👣' },
        'CHARACTER_MELEE_ATTACK': { title: 'Melee Attack', icon: '⚔️' },
        'CHARACTER_RANGED_ATTACK': { title: 'Ranged Attack', icon: '🏹' },
        'CHARACTER_DEATH': { title: 'Death', icon: '💀' },
        'CHARACTER_STATUS_CHANGE': { title: 'Status Change', icon: '✨' },
        'ITEM_PICKUP': { title: 'Item Pickup', icon: '🎒' },
        'ITEM_DROP': { title: 'Item Drop', icon: '📦' },
        'ACTION_RESULT': { title: 'Action Result', icon: '✓' },
        'SYSTEM': { title: 'System', icon: '⚙️' },
    };

    const info = eventInfo[event.event_type] || { title: 'Event', icon: '📋' };

    return (
        <div className="mini-event-tooltip">
            <div className="mini-event-tooltip-header">
                <span className="mini-event-tooltip-icon">{info.icon}</span>
                <span className="mini-event-tooltip-title">{info.title}</span>
            </div>
            <p className="mini-event-tooltip-description">{event.description}</p>
        </div>
    );
};

interface MessageMiniIconProps {
    message: any;
    onClick: () => void;
}

const MessageMiniIcon: React.FC<MessageMiniIconProps> = ({ message, onClick }) => {
    const isDM = message.sender_name?.startsWith('DM');
    
    return (
        <Tooltip 
            content={
                <div className="mini-message-tooltip">
                    <span className="mini-message-sender">{message.sender_name}</span>
                    <span className="mini-message-text">{message.text}</span>
                </div>
            } 
            position="left"
        >
            <div 
                className={`mini-message-icon ${isDM ? 'dm-message' : 'player-message'}`}
                onClick={onClick}
            >
                <span className="mini-message-indicator">{isDM ? '🎙️' : '💬'}</span>
            </div>
        </Tooltip>
    );
};

interface EventMiniIconProps {
    event: any;
    onClick: () => void;
}

const EventMiniIcon: React.FC<EventMiniIconProps> = ({ event, onClick }) => {
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

    return (
        <Tooltip content={<EventMiniTooltip event={event} />} position="left">
            <div className="mini-event-icon" onClick={onClick}>
                <span className="mini-event-icon-symbol">{getEventIcon(event.event_type)}</span>
            </div>
        </Tooltip>
    );
};

export const MiniChatPanel: React.FC = () => {
    const { messages, events } = useGameStore();
    const [selectedFilter, setSelectedFilter] = useState<'all' | 'dm' | 'players' | 'events'>('all');

    const getFilteredItems = () => {
        const allItems = [
            ...messages.map(m => ({ type: 'message' as const, data: m })),
            ...events.map(e => ({ type: 'event' as const, data: e }))
        ];

        switch (selectedFilter) {
            case 'dm':
                return allItems.filter(m => m.type === 'message' && m.data.sender_name?.startsWith('DM'));
            case 'players':
                return allItems.filter(m => m.type === 'message' && !m.data.sender_name?.startsWith('DM'));
            case 'events':
                return allItems.filter(m => m.type === 'event');
            default:
                return allItems.slice(-20); // Last 20 items
        }
    };

    const filteredItems = getFilteredItems();

    const handleItemClick = (item: any) => {
        // Could expand panel or show details
        console.log('Clicked:', item);
    };

    return (
        <div className="mini-chat-panel">
            <div className="mini-chat-filters">
                <Tooltip content={<span>📋 All Messages</span>} position="left">
                    <button
                        className={`mini-filter-btn ${selectedFilter === 'all' ? 'active' : ''}`}
                        onClick={() => setSelectedFilter('all')}
                    >
                        📋
                    </button>
                </Tooltip>
                <Tooltip content={<span>🎙️ DM Messages</span>} position="left">
                    <button
                        className={`mini-filter-btn ${selectedFilter === 'dm' ? 'active' : ''}`}
                        onClick={() => setSelectedFilter('dm')}
                    >
                        🎙️
                    </button>
                </Tooltip>
                <Tooltip content={<span>💬 Player Messages</span>} position="left">
                    <button
                        className={`mini-filter-btn ${selectedFilter === 'players' ? 'active' : ''}`}
                        onClick={() => setSelectedFilter('players')}
                    >
                        💬
                    </button>
                </Tooltip>
                <Tooltip content={<span>⚡ Events</span>} position="left">
                    <button
                        className={`mini-filter-btn ${selectedFilter === 'events' ? 'active' : ''}`}
                        onClick={() => setSelectedFilter('events')}
                    >
                        ⚡
                    </button>
                </Tooltip>
            </div>

            <div className="mini-chat-items">
                {filteredItems.slice(-10).map((item, idx) => (
                    item.type === 'message' ? (
                        <MessageMiniIcon
                            key={`msg-${idx}`}
                            message={item.data}
                            onClick={() => handleItemClick(item)}
                        />
                    ) : (
                        <EventMiniIcon
                            key={`evt-${idx}`}
                            event={item.data}
                            onClick={() => handleItemClick(item)}
                        />
                    )
                ))}
            </div>
        </div>
    );
};
