import React, { useState, useRef, useEffect } from 'react';
import { useGameStore } from '../store/gameStore';
import { Tooltip } from './common/Tooltip';
import './ChatPanel.css';

interface FilterTooltipContentProps {
    filter: 'all' | 'dm' | 'players' | 'events' | 'rolls';
}

const FilterTooltipContent: React.FC<FilterTooltipContentProps> = ({ filter }) => {
    const filterInfo: Record<string, { title: string; description: string; icon: string }> = {
        'all': {
            title: 'All Logs',
            description: 'Show complete chronicle including DM narration, player speech, rolls, and events.',
            icon: '📜'
        },
        'dm': {
            title: 'DM Narration',
            description: 'Filter only storytelling, scene descriptions, and Dungeon Master rulings.',
            icon: '🎭'
        },
        'players': {
            title: 'Party & NPCs',
            description: 'Filter dialogue and actions from player characters and non-player entities.',
            icon: '💬'
        },
        'events': {
            title: 'Game Events',
            description: 'Tactical mechanics (movement, damage, conditions, item manipulation).',
            icon: '⚡'
        },
        'rolls': {
            title: 'Dice Rolls',
            description: 'Check roll outcomes, attack checks, damage calculations, and saving throws.',
            icon: '🎲'
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

export const ChatPanel: React.FC = () => {
    const { messages, events, currentScene } = useGameStore();
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const scrollContainerRef = useRef<HTMLDivElement>(null);
    const [filter, setFilter] = useState<'all' | 'dm' | 'players' | 'events' | 'rolls'>('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [isAtBottom, setIsAtBottom] = useState(true);

    const safeMessages = messages || [];
    const safeEvents = events || [];

    const handleScroll = () => {
        if (!scrollContainerRef.current) return;
        const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
        const atBottom = scrollHeight - scrollTop - clientHeight < 50;
        setIsAtBottom(atBottom);
    };

    const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
        messagesEndRef.current?.scrollIntoView({ behavior });
        setIsAtBottom(true);
    };

    useEffect(() => {
        if (isAtBottom) {
            scrollToBottom('smooth');
        }
    }, [safeMessages, safeEvents]);

    const isDM = (sender: string) => {
        const lower = sender.toLowerCase();
        return lower.startsWith('dm') || lower.includes('dungeon master') || lower.includes('game master') || lower.includes('magg') || lower === 'master';
    };

    const isRollText = (text: string) => {
        return text.includes('Rolled') || text.includes('d20') || text.includes('NATURAL 20') || text.includes('NATURAL 1') || text.includes('[Initiative]') || text.includes('[Attack');
    };

    const getFilteredEntries = () => {
        const combined = [
            ...(safeMessages.map((m, idx) => ({
                id: `msg-${idx}`,
                kind: 'message' as const,
                sender: m.sender_name || 'Adventurer',
                text: m.text || '',
                type: m.type,
                timestamp: (m as any).timestamp || '',
            }))),
            ...(safeEvents.map((e, idx) => ({
                id: `evt-${idx}`,
                kind: 'event' as const,
                sender: e.event_initiator || 'System',
                text: e.description || '',
                type: e.event_type,
                timestamp: (e as any).timestamp || '',
            }))),
        ];

        return combined.filter(entry => {
            // Apply search query
            if (searchQuery.trim()) {
                const query = searchQuery.toLowerCase();
                const matchesText = entry.text.toLowerCase().includes(query);
                const matchesSender = entry.sender.toLowerCase().includes(query);
                if (!matchesText && !matchesSender) return false;
            }

            // Apply category filter
            switch (filter) {
                case 'dm':
                    return entry.kind === 'message' && isDM(entry.sender);
                case 'players':
                    return entry.kind === 'message' && !isDM(entry.sender);
                case 'events':
                    return entry.kind === 'event';
                case 'rolls':
                    return entry.kind === 'message' && isRollText(entry.text);
                default:
                    return true;
            }
        });
    };

    const entries = getFilteredEntries();

    return (
        <div className="ergonomic-chat-panel">
            {/* Header with Title and Search */}
            <div className="chronicle-header">
                <div className="chronicle-title-group">
                    <span className="chronicle-icon">📜</span>
                    <h3>Chronicle & Narrative</h3>
                    <span className="chronicle-badge">{entries.length}</span>
                </div>

                <div className="chronicle-search-wrapper">
                    <input
                        type="text"
                        className="chronicle-search-input"
                        placeholder="Search logs..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    {searchQuery && (
                        <button
                            type="button"
                            className="clear-search-btn"
                            onClick={() => setSearchQuery('')}
                        >
                            ✕
                        </button>
                    )}
                </div>
            </div>

            {/* Filter Tabs */}
            <div className="chronicle-filters">
                <Tooltip content={<FilterTooltipContent filter="all" />} position="bottom">
                    <button
                        className={`chronicle-filter-chip ${filter === 'all' ? 'active' : ''}`}
                        onClick={() => setFilter('all')}
                    >
                        📜 All
                    </button>
                </Tooltip>
                <Tooltip content={<FilterTooltipContent filter="dm" />} position="bottom">
                    <button
                        className={`chronicle-filter-chip dm-chip ${filter === 'dm' ? 'active' : ''}`}
                        onClick={() => setFilter('dm')}
                    >
                        🎭 DM
                    </button>
                </Tooltip>
                <Tooltip content={<FilterTooltipContent filter="players" />} position="bottom">
                    <button
                        className={`chronicle-filter-chip party-chip ${filter === 'players' ? 'active' : ''}`}
                        onClick={() => setFilter('players')}
                    >
                        💬 Party
                    </button>
                </Tooltip>
                <Tooltip content={<FilterTooltipContent filter="rolls" />} position="bottom">
                    <button
                        className={`chronicle-filter-chip rolls-chip ${filter === 'rolls' ? 'active' : ''}`}
                        onClick={() => setFilter('rolls')}
                    >
                        🎲 Rolls
                    </button>
                </Tooltip>
                <Tooltip content={<FilterTooltipContent filter="events" />} position="bottom">
                    <button
                        className={`chronicle-filter-chip events-chip ${filter === 'events' ? 'active' : ''}`}
                        onClick={() => setFilter('events')}
                    >
                        ⚡ Events
                    </button>
                </Tooltip>
            </div>
            {/* Atmospheric Scene Banner (persisted scene visual) */}
            {currentScene && (currentScene.name || currentScene.image_url) && (
                <div className="scene-atmosphere-banner" data-testid="scene-atmosphere-banner">
                    {currentScene.image_url && (
                        <div className="scene-banner-img-wrapper">
                            <img
                                src={currentScene.image_url}
                                alt={currentScene.name || 'Current Scene'}
                                className="scene-banner-img"
                                onError={(e) => {
                                    (e.currentTarget as HTMLElement).style.display = 'none';
                                }}
                            />
                        </div>
                    )}
                    <div className="scene-banner-info">
                        <div className="scene-banner-tag">📍 CURRENT ENVIRONMENT</div>
                        <h4 className="scene-banner-title">{currentScene.name || 'Unnamed Chamber'}</h4>
                        {currentScene.description && (
                            <p className="scene-banner-desc">
                                {currentScene.description.length > 130
                                    ? currentScene.description.slice(0, 130) + '...'
                                    : currentScene.description}
                            </p>
                        )}
                    </div>
                </div>
            )}

            {/* Scrollable Message Feed */}
            <div
                className="chronicle-feed"
                ref={scrollContainerRef}
                onScroll={handleScroll}
            >
                {entries.length === 0 ? (
                    <div className="chronicle-empty">
                        <span className="empty-glyph">🔮</span>
                        <p>No entries found</p>
                        <span className="empty-hint">The chronicle is silent for this filter.</span>
                    </div>
                ) : (
                    entries.map((entry) => {
                        const dm = isDM(entry.sender);
                        const isRoll = isRollText(entry.text);

                        if (entry.kind === 'event') {
                            return (
                                <div key={entry.id} className="chronicle-entry event-entry">
                                    <span className="entry-tag event-tag">⚡ EVENT</span>
                                    <div className="entry-body">
                                        <span className="event-desc">{entry.text}</span>
                                    </div>
                                </div>
                            );
                        }

                        if (dm) {
                            return (
                                <div key={entry.id} className="chronicle-entry dm-entry">
                                    <div className="entry-sender-bar">
                                        <span className="entry-tag dm-tag">🎭 {entry.sender}</span>
                                    </div>
                                    <div className="entry-narrative-prose">
                                        {entry.text}
                                    </div>
                                </div>
                            );
                        }

                        if (isRoll) {
                            return (
                                <div key={entry.id} className="chronicle-entry roll-entry">
                                    <div className="entry-sender-bar">
                                        <span className="player-name">{entry.sender}</span>
                                        <span className="entry-tag roll-tag">🎲 ROLL</span>
                                    </div>
                                    <div className="roll-result-text">
                                        {entry.text}
                                    </div>
                                </div>
                            );
                        }

                        return (
                            <div key={entry.id} className="chronicle-entry player-entry">
                                <div className="entry-sender-bar">
                                    <span className="player-name">{entry.sender}</span>
                                </div>
                                <div className="entry-text">
                                    {entry.text}
                                </div>
                            </div>
                        );
                    })
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Jump to bottom button when scrolled up */}
            {!isAtBottom && (
                <button
                    type="button"
                    className="jump-bottom-btn"
                    onClick={() => scrollToBottom('smooth')}
                    title="Jump to latest"
                >
                    ↓ Latest
                </button>
            )}
        </div>
    );
};
