import React, { useRef, useEffect } from 'react';
import { useGameStore } from '../store/gameStore';
import { Tooltip } from './common/Tooltip';
import './EventsPanel.css';

interface EventTooltipContentProps {
    event: any;
}

const EventTooltipContent: React.FC<EventTooltipContentProps> = ({ event }) => {
    const eventInfo: Record<string, { title: string; description: string; icon: string }> = {
        'CHARACTER_MOVEMENT': { title: 'Movement', description: 'A character moved to a new location', icon: '👣' },
        'CHARACTER_MELEE_ATTACK': { title: 'Melee Attack', description: 'A character made a melee attack', icon: '⚔️' },
        'CHARACTER_RANGED_ATTACK': { title: 'Ranged Attack', description: 'A character made a ranged attack', icon: '🏹' },
        'CHARACTER_DEATH': { title: 'Death', description: 'A character has died', icon: '💀' },
        'CHARACTER_STATUS_CHANGE': { title: 'Status Change', description: "A character's status has changed", icon: '✨' },
        'ITEM_PICKUP': { title: 'Item Pickup', description: 'An item was picked up', icon: '🎒' },
        'ITEM_DROP': { title: 'Item Drop', description: 'An item was dropped', icon: '📦' },
        'ACTION_RESULT': { title: 'Action Result', description: 'Result of a character action', icon: '✓' },
        'SYSTEM': { title: 'System', description: 'System message', icon: '⚙️' },
    };

    const info = eventInfo[event.event_type] || { title: 'Event', description: 'A game event occurred', icon: '📋' };

    return (
        <div className="event-tooltip">
            <div className="event-tooltip-header">
                <span className="event-tooltip-icon">{info.icon}</span>
                <span className="event-tooltip-title">{info.title}</span>
            </div>
            <p className="event-tooltip-description">{event.description}</p>
            {event.event_initiator && (
                <p className="event-tooltip-meta">
                    Initiator: {event.event_initiator}
                </p>
            )}
        </div>
    );
};

export const EventsPanel: React.FC = () => {
    const { events } = useGameStore();
    const eventsEndRef = useRef<HTMLDivElement>(null);

    const safeEvents = events || [];

    const scrollToBottom = () => {
        eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [safeEvents]);

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

    const getEventColor = (eventType: string) => {
        switch (eventType) {
            case 'CHARACTER_MELEE_ATTACK':
            case 'CHARACTER_RANGED_ATTACK':
                return 'var(--accent-red)';
            case 'CHARACTER_DEATH':
                return 'var(--text-muted)';
            case 'CHARACTER_MOVEMENT':
                return 'var(--accent-blue)';
            case 'ITEM_PICKUP':
            case 'ITEM_DROP':
                return 'var(--accent-green)';
            case 'SYSTEM':
                return 'var(--text-muted)';
            default:
                return 'var(--accent-yellow)';
        }
    };

    return (
        <div className="events-panel">
            <div className="events-header">
                <h2>⚡ Game Events</h2>
                <span className="events-count">{safeEvents.length}</span>
            </div>

            <div className="events-list">
                {!safeEvents || safeEvents.length === 0 ? (
                    <div className="no-events">
                        <p>No events yet</p>
                        <p className="hint">Game events will appear here</p>
                    </div>
                ) : (
                    safeEvents.map((event, idx) => (
                        <Tooltip key={`event-${idx}`} content={<EventTooltipContent event={event} />} position="left">
                            <div
                                className="event-entry"
                                style={{ borderLeftColor: getEventColor(event.event_type) }}
                            >
                                <span className="event-icon">{getEventIcon(event.event_type)}</span>
                                <div className="event-content">
                                    <span className="event-description">{event.description}</span>
                                    <span className="event-type">{event.event_type}</span>
                                </div>
                            </div>
                        </Tooltip>
                    ))
                )}
                <div ref={eventsEndRef} />
            </div>
        </div>
    );
};
