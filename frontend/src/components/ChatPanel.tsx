import React, { useState, useRef, useEffect, useMemo } from 'react';
import { useGameStore } from '../store/gameStore';
import { Tooltip } from './common/Tooltip';
import { VectorIcon, IconName } from './common/VectorIcon';
import { CharacterStatHoverCard, SpellHoverCard, ItemHoverCard } from './common/HoverTips';
import { highlightNarrativeKeywords } from '../utils/keywordHighlighter';
import { handleTiltAndHighlight, handleTiltReset } from '../utils/cardTilt';
import { useTranslation } from '../i18n/useTranslation';
import './ChatPanel.css';

interface FilterTooltipContentProps {
    filter: 'story' | 'story-events' | 'all' | 'rolls' | 'dm';
}

const FilterTooltipContent: React.FC<FilterTooltipContentProps> = ({ filter }) => {
    const { language } = useTranslation();

    const filterInfoRu: Record<string, { title: string; description: string; icon: IconName }> = {
        'story': {
            title: 'Сюжет & Диалоги',
            description: 'Только повествование: ответы Мастера подземелий и речь/действия персонажей.',
            icon: 'woman'
        },
        'story-events': {
            title: 'Сюжет + События системы',
            description: 'Летопись сюжета плюс тактическое передвижение, урон, состояния и изменения окружения.',
            icon: 'sword'
        },
        'all': {
            title: 'Полная Летопись (Все логи)',
            description: 'Полный поток: повествование DM, речь игроков, тактические события и броски кубиков.',
            icon: 'banner'
        },
        'rolls': {
            title: 'Только Броски Кубиков',
            description: 'Результаты проверок, атаки, броски урона и спасброски.',
            icon: 'dice'
        },
        'dm': {
            title: 'Только Решения Мастера',
            description: 'Фильтр повествования, описаний локаций и решений Dungeon Master.',
            icon: 'crown'
        }
    };

    const filterInfoEn: Record<string, { title: string; description: string; icon: IconName }> = {
        'story': {
            title: 'Story & Dialogue',
            description: 'Pure narrative: Shows only Dungeon Master replies and Character speech/actions.',
            icon: 'woman'
        },
        'story-events': {
            title: 'Story + System Events',
            description: 'Narrative chronicle plus tactical movement, damage, conditions, and environment changes.',
            icon: 'sword'
        },
        'all': {
            title: 'Full Chronicle (All Logs)',
            description: 'Complete feed including DM narration, player speech, tactical events, and dice rolls.',
            icon: 'banner'
        },
        'rolls': {
            title: 'Dice Rolls Only',
            description: 'Check roll outcomes, attack checks, damage calculations, and saving throws.',
            icon: 'dice'
        },
        'dm': {
            title: 'DM Rulings Only',
            description: 'Filter only storytelling, scene descriptions, and Dungeon Master rulings.',
            icon: 'crown'
        }
    };

    const map = language === 'ru' ? filterInfoRu : filterInfoEn;
    const info = map[filter] || map['all'];

    return (
        <div className="filter-tooltip">
            <div className="filter-tooltip-title">
                <div className="filter-tooltip-icon">
                    <VectorIcon name={info.icon} />
                    <span>{info.title}</span>
                </div>
            </div>
            <p className="filter-tooltip-description">{info.description}</p>
        </div>
    );
};

interface FastCommand {
    id: string;
    label: string;
    icon: IconName;
    text: string;
    description: string;
}

const FAST_COMMANDS: FastCommand[] = [
    { id: 'attack', label: 'Attack', icon: 'sword', text: 'I make a weapon attack against the nearest hostile target.', description: 'Strike an enemy' },
    { id: 'dash', label: 'Dash', icon: 'horse', text: 'I take the Dash action to gain extra movement for this turn.', description: 'Double movement speed' },
    { id: 'dodge', label: 'Dodge', icon: 'shield', text: 'I take the Dodge action, focusing entirely on evading incoming attacks.', description: 'Disadvantage on attacks against you' },
    { id: 'hide', label: 'Hide', icon: 'helm', text: 'I attempt to hide behind available cover with a Dexterity (Stealth) check.', description: 'Stealth check for cover' },
    { id: 'search', label: 'Search', icon: 'rune', text: 'I carefully search my surroundings with an Investigation / Perception check.', description: 'Inspect surroundings' },
    { id: 'help', label: 'Help Ally', icon: 'knight', text: 'I use the Help action to give advantage to my ally on their next check or attack.', description: 'Aid a friendly creature' },
    { id: 'interact', label: 'Use Object', icon: 'gate', text: 'I interact with the nearest object or mechanism in the scene.', description: 'Operate mechanism or object' },
    { id: 'speak', label: 'Dialogue', icon: 'banner', text: 'I speak aloud: "', description: 'Converse with party or NPCs' },
];

export const ChatPanel: React.FC = () => {
    const { t, language } = useTranslation();

    const {
        messages,
        events,
        currentScene,
        activeCharacter,
        currentSession,
        session,
        sendAction,
        isActionPending,
        clarificationText,
        isDMThinking,
        turnQueue,
    } = useGameStore();

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const scrollContainerRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    const [filter, setFilter] = useState<'story' | 'story-events' | 'all' | 'rolls' | 'dm'>('story');
    const [isAtBottom, setIsAtBottom] = useState(true);

    const fastCommands: FastCommand[] = useMemo(() => [
        { id: 'attack', label: t.chat.actions.attack, icon: 'sword', text: t.chat.actions.attackPrompt, description: t.chat.actions.attackDesc },
        { id: 'dash', label: t.chat.actions.dash, icon: 'horse', text: t.chat.actions.dashPrompt, description: t.chat.actions.dashDesc },
        { id: 'dodge', label: t.chat.actions.dodge, icon: 'shield', text: t.chat.actions.dodgePrompt, description: t.chat.actions.dodgeDesc },
        { id: 'hide', label: t.chat.actions.hide, icon: 'helm', text: t.chat.actions.hidePrompt, description: t.chat.actions.hideDesc },
        { id: 'search', label: t.chat.actions.search, icon: 'rune', text: t.chat.actions.searchPrompt, description: t.chat.actions.searchDesc },
        { id: 'help', label: t.chat.actions.help, icon: 'knight', text: t.chat.actions.helpPrompt, description: t.chat.actions.helpDesc },
        { id: 'interact', label: t.chat.actions.interact, icon: 'gate', text: t.chat.actions.interactPrompt, description: t.chat.actions.interactDesc },
        { id: 'speak', label: t.chat.actions.speak, icon: 'banner', text: t.chat.actions.speakPrompt, description: t.chat.actions.speakDesc },
    ], [t]);

    // Integrated Action State
    const [actionText, setActionText] = useState('');
    const [showFastCommands, setShowFastCommands] = useState(false);
    const [commandCategory, setCommandCategory] = useState<'actions' | 'spells' | 'items'>('actions');
    const [showSceneLore, setShowSceneLore] = useState(false);

    const isResolving = isActionPending || isDMThinking;
    const activeSession = currentSession || session;

    // Tactical Combat Turn Order Validation
    const isCombatMode = useMemo(() => {
        const mode = activeSession?.game_mode || (activeSession as any)?.mode;
        const modeStr = typeof mode === 'string' ? mode : (mode?.value || '');
        return modeStr.toUpperCase() === 'COMBAT';
    }, [activeSession]);

    const activeCombatant = useMemo(() => {
        if (!isCombatMode || !turnQueue || turnQueue.length === 0) return null;
        const first = turnQueue[0];
        if (Array.isArray(first)) {
            const c = first[0];
            return typeof c === 'object' ? (c?.name || 'Hero') : String(c || 'Hero');
        }
        return first.character || first.name || null;
    }, [isCombatMode, turnQueue]);

    const isMyTurnInCombat = useMemo(() => {
        if (!isCombatMode) return true; // In story mode, any player can contribute actions
        if (!activeCombatant || !activeCharacter) return true;
        return activeCharacter.name.toLowerCase() === activeCombatant.toLowerCase();
    }, [isCombatMode, activeCombatant, activeCharacter]);

    const isInputDisabled = isResolving || (!isMyTurnInCombat);
    const safeMessages = messages || [];
    const safeEvents = events || [];

    const characterSpells = activeCharacter?.abilities || [];
    const characterInventory = (activeCharacter?.inventory || []).filter((i: any) => !i.is_equipped);

    const handleScroll = () => {
        if (!scrollContainerRef.current) return;
        const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
        const atBottom = scrollHeight - scrollTop - clientHeight < 60;
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
        if (!sender) return false;
        const lower = sender.toLowerCase().trim();
        return (
            lower.startsWith('dm') ||
            lower.includes('dungeon master') ||
            lower.includes('game master') ||
            lower.includes('magg') ||
            lower === 'master' ||
            lower === 'dm/narrator' ||
            lower === 'narrator'
        );
    };

    const isRollText = (text: string) => {
        if (!text) return false;
        return (
            text.includes('Rolled') ||
            text.includes('d20') ||
            text.includes('NATURAL 20') ||
            text.includes('NATURAL 1') ||
            text.includes('[Initiative]') ||
            text.includes('[Attack') ||
            text.includes('[Damage')
        );
    };

    const getFallbackPortrait = (charClass?: string, role?: string): string => {
        if (role === 'dm') return '/assets/placeholders/dm_emblem.svg';
        const cls = (charClass || '').toLowerCase();
        if (cls.includes('wizard') || cls.includes('mage') || cls.includes('sorcerer') || cls.includes('warlock')) {
            return '/assets/placeholders/character_wizard.svg';
        }
        if (cls.includes('rogue') || cls.includes('thief') || cls.includes('assassin') || cls.includes('ranger')) {
            return '/assets/placeholders/character_rogue.svg';
        }
        if (cls.includes('cleric') || cls.includes('paladin') || cls.includes('priest')) {
            return '/assets/placeholders/character_cleric.svg';
        }
        if (cls.includes('fighter') || cls.includes('warrior') || cls.includes('barbarian')) {
            return '/assets/placeholders/character_warrior.svg';
        }
        return '/assets/placeholders/character_default.svg';
    };

    const resolveAvatar = (sender: string) => {
        if (isDM(sender)) {
            return {
                url: '/assets/placeholders/dm_emblem.svg',
                fallback: '/assets/placeholders/dm_emblem.svg',
                name: 'Dungeon Master',
                role: 'dm',
                isMe: false,
                isHostile: false,
                character: null,
            };
        }

        const isMe = Boolean(
            activeCharacter &&
            (sender.toLowerCase() === activeCharacter.name?.toLowerCase() ||
             sender.toLowerCase() === (activeCharacter as any).character_name?.toLowerCase())
        );

        if (isMe && activeCharacter) {
            const fallback = getFallbackPortrait(activeCharacter.char_class, 'player');
            return {
                url: activeCharacter.image_url || fallback,
                fallback,
                name: activeCharacter.name || 'Hero',
                role: 'player',
                isMe: true,
                isHostile: false,
                character: activeCharacter,
            };
        }

        const partyMember = activeSession?.players?.find((p: any) => {
            const char = p.character || p;
            return char?.name?.toLowerCase() === sender.toLowerCase();
        });
        if (partyMember) {
            const char = partyMember.character || partyMember;
            const fallback = getFallbackPortrait(char.char_class, 'ally');
            return {
                url: char.image_url || fallback,
                fallback,
                name: char.name || sender,
                role: 'ally',
                isMe: false,
                isHostile: false,
                character: char,
            };
        }

        const npcMember = activeSession?.npcs?.find((n: any) => {
            const char = n.character || n;
            return char?.name?.toLowerCase() === sender.toLowerCase();
        });
        if (npcMember) {
            const char = npcMember.character || npcMember;
            const isHostile = Boolean(
                (char.alignment || '').toLowerCase().includes('evil') ||
                (char.alignment || '').toLowerCase().includes('hostile') ||
                (char.alignment || '').toLowerCase().includes('chaotic')
            );
            const fallback = getFallbackPortrait(char.char_class, isHostile ? 'hostile' : 'npc');
            return {
                url: char.image_url || fallback,
                fallback,
                name: char.name || sender,
                role: isHostile ? 'hostile' : 'npc',
                isMe: false,
                isHostile,
                character: char,
            };
        }

        const fallback = getFallbackPortrait('warrior', 'adventurer');
        return {
            url: fallback,
            fallback,
            name: sender,
            role: 'adventurer',
            isMe: false,
            isHostile: false,
            character: null,
        };
    };

    // Combine messages and events with deduplication
    const combinedEntries = useMemo(() => {
        const seenKeys = new Set<string>();
        const list: Array<{
            id: string;
            kind: 'message' | 'event';
            sender: string;
            text: string;
            type?: string;
            timestamp: string;
        }> = [];

        // 1. Messages
        safeMessages.forEach((m, idx) => {
            const sender = m.sender_name || 'Adventurer';
            const text = (m.text || '').trim();
            if (!text) return;

            // System events sent via messages are marked as kind: event to render as round tiles
            const isSysEvent = m.type === 'event' ||
                               sender.toLowerCase() === 'game' ||
                               sender.toLowerCase() === 'system';

            const kind: 'message' | 'event' = isSysEvent ? 'event' : 'message';
            const key = `${kind}:${sender}:${text}`;
            if (seenKeys.has(key)) return;
            seenKeys.add(key);

            list.push({
                id: `msg-${idx}`,
                kind,
                sender,
                text: m.text,
                type: m.type,
                timestamp: (m as any).timestamp || '',
            });
        });

        // 2. Events
        safeEvents.forEach((e, idx) => {
            const text = (e.description || '').trim();
            if (!text) return;
            const sender = e.event_initiator || 'System';

            const eventKey = `event:${sender}:${text}`;
            const altKey = `message:${sender}:${text}`;
            if (seenKeys.has(eventKey) || seenKeys.has(altKey)) return;
            seenKeys.add(eventKey);

            list.push({
                id: `evt-${idx}`,
                kind: 'event',
                sender,
                text: e.description,
                type: e.event_type,
                timestamp: (e as any).timestamp || '',
            });
        });

        // 3. Sort chronologically so tactical events and pills interleave directly in true chronological order
        list.sort((a, b) => {
            const timeA = a.timestamp ? new Date(a.timestamp).getTime() : 0;
            const timeB = b.timestamp ? new Date(b.timestamp).getTime() : 0;
            if (timeA && timeB && timeA !== timeB) {
                return timeA - timeB;
            }
            return 0;
        });

        return list;
    }, [safeMessages, safeEvents]);

    const filteredEntries = useMemo(() => {
        return combinedEntries.filter(entry => {
            switch (filter) {
                case 'story':
                    return entry.kind === 'message' && !isRollText(entry.text);
                case 'story-events':
                    return (entry.kind === 'message' && !isRollText(entry.text)) || entry.kind === 'event';
                case 'dm':
                    return entry.kind === 'message' && isDM(entry.sender);
                case 'rolls':
                    return entry.kind === 'message' && isRollText(entry.text);
                case 'all':
                default:
                    return true;
            }
        });
    }, [combinedEntries, filter]);

    const formatTimestamp = (ts: string | number) => {
        if (!ts) return '';
        try {
            const date = typeof ts === 'number' ? new Date(ts) : new Date(ts);
            if (isNaN(date.getTime())) return '';
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } catch {
            return '';
        }
    };

    const knownEntityNames = useMemo(() => {
        return [
            ...(activeSession?.players || []).map((p: any) => p?.character?.name || p?.name),
            ...(activeSession?.npcs || []).map((n: any) => n?.character?.name || n?.name),
            activeCharacter?.name,
        ].filter(Boolean);
    }, [activeSession, activeCharacter]);

    // Action Form Handlers
    const handleActionSubmit = (e?: React.FormEvent) => {
        if (e) e.preventDefault();
        if (activeCharacter && actionText.trim() && !isInputDisabled) {
            sendAction(actionText.trim(), activeCharacter);
            setActionText('');
            if (inputRef.current) {
                inputRef.current.style.height = 'auto';
            }
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleActionSubmit();
        }
    };

    const handlePresetClick = (preset: FastCommand) => {
        setActionText(preset.text);
        inputRef.current?.focus();
    };

    const handleSpellClick = (spell: any) => {
        const spellName = typeof spell === 'string' ? spell : spell.name;
        setActionText(`I cast ${spellName} on the target.`);
        inputRef.current?.focus();
    };

    const handleItemClick = (item: any) => {
        const itemName = typeof item === 'string' ? item : item.name;
        setActionText(`I use ${itemName} from my inventory.`);
        inputRef.current?.focus();
    };

    return (
        <div className="ergonomic-chat-panel">
            {/* Header with Title */}
            <div className="chronicle-header">
                <div className="chronicle-title-group">
                    <span className="chronicle-icon"><VectorIcon name="banner" /></span>
                    <h3>{language === 'ru' ? 'Летопись & Диалог' : 'Chronicle & Chat'}</h3>
                    <span className="chronicle-badge">{filteredEntries.length}</span>
                </div>
            </div>

            {/* Filter Tabs */}
            <div className="chronicle-filters">
                <Tooltip content={<FilterTooltipContent filter="story" />} position="bottom">
                    <button
                        className={`chronicle-filter-chip story-chip ${filter === 'story' ? 'active' : ''}`}
                        onClick={() => setFilter('story')}
                    >
                        <VectorIcon name="woman" /> {t.chat.storyFilter}
                    </button>
                </Tooltip>
                <Tooltip content={<FilterTooltipContent filter="story-events" />} position="bottom">
                    <button
                        className={`chronicle-filter-chip story-events-chip ${filter === 'story-events' ? 'active' : ''}`}
                        onClick={() => setFilter('story-events')}
                    >
                        <VectorIcon name="sword" /> {t.chat.storyEventsFilter}
                    </button>
                </Tooltip>
                <Tooltip content={<FilterTooltipContent filter="all" />} position="bottom">
                    <button
                        className={`chronicle-filter-chip ${filter === 'all' ? 'active' : ''}`}
                        onClick={() => setFilter('all')}
                    >
                        <VectorIcon name="banner" /> {t.chat.allFilter}
                    </button>
                </Tooltip>
                <Tooltip content={<FilterTooltipContent filter="rolls" />} position="bottom">
                    <button
                        className={`chronicle-filter-chip rolls-chip ${filter === 'rolls' ? 'active' : ''}`}
                        onClick={() => setFilter('rolls')}
                    >
                        <VectorIcon name="dice" /> {t.chat.rollsFilter}
                    </button>
                </Tooltip>
                <Tooltip content={<FilterTooltipContent filter="dm" />} position="bottom">
                    <button
                        className={`chronicle-filter-chip dm-chip ${filter === 'dm' ? 'active' : ''}`}
                        onClick={() => setFilter('dm')}
                    >
                        <VectorIcon name="crown" /> {t.chat.dmFilter}
                    </button>
                </Tooltip>
            </div>

            {/* Compact Foldable Scene Lore Bar (Separate Place to Hide and Not Waste Space) */}
            {currentScene && (currentScene.name || currentScene.description) && (
                <div className="chronicle-scene-lore-strip">
                    <button
                        type="button"
                        className="lore-strip-toggle-btn"
                        onClick={() => setShowSceneLore(!showSceneLore)}
                        title="Toggle Scene Description"
                    >
                        <span className="lore-strip-icon">📜</span>
                        <span className="lore-strip-title">{currentScene.name || 'Current Scene'}</span>
                        <span className="lore-strip-indicator">{showSceneLore ? 'Hide Lore ▲' : 'Show Lore ▼'}</span>
                    </button>
                    {showSceneLore && (
                        <div className="lore-strip-body">
                            {currentScene.description && <p className="lore-strip-text">{currentScene.description}</p>}
                        </div>
                    )}
                </div>
            )}

            {/* Scrollable Message Feed with DM Thinking Overlay */}
            <div className="chronicle-feed-container">
                <div
                    className="chronicle-feed"
                    ref={scrollContainerRef}
                    onScroll={handleScroll}
                >
                {filteredEntries.length === 0 ? (
                    <div className="chronicle-empty">
                        <span className="empty-glyph"><VectorIcon name="swirl" size="2rem" /></span>
                        <p>No entries found</p>
                        <span className="empty-hint">The chronicle is silent for this filter.</span>
                    </div>
                ) : (
                    filteredEntries.map((entry) => {
                        const avatar = resolveAvatar(entry.sender);
                        const isRoll = isRollText(entry.text);
                        const timeStr = formatTimestamp(entry.timestamp);

                        const isQuestFanfare = entry.text.includes('🏆 **Objective Completed') ||
                                              entry.text.includes('🌟 **CHAPTER COMPLETED') ||
                                              entry.text.includes('👑 **GRAND VICTORY') ||
                                              (entry as any).tag === 'quest_update' ||
                                              (entry as any).tag === 'chapter_advance';

                        // 0. Campaign Quest & Chapter Milestone Fanfare
                        if (isQuestFanfare) {
                            return (
                                <div key={entry.id} className="chat-row center-row quest-fanfare-row" data-testid="chat-msg-quest">
                                    <div className="quest-fanfare-card">
                                        <div className="quest-fanfare-header">
                                            <span className="quest-fanfare-icon">📜</span>
                                            <span className="quest-fanfare-tag">CAMPAIGN MILESTONE</span>
                                        </div>
                                        <div className="quest-fanfare-text">{entry.text}</div>
                                        {timeStr && <span className="event-time">{timeStr}</span>}
                                    </div>
                                </div>
                            );
                        }

                        // 1. Tactical or System Events: Round Tile Pill (Centred, NOT a chat message bubble)
                        if (entry.kind === 'event') {
                            return (
                                <div key={entry.id} className="chat-row center-row" data-testid="chat-msg-event">
                                    <div className="event-tactical-pill">
                                        <span className="event-icon"><VectorIcon name="horse" /></span>
                                        <span className="event-text">{entry.text}</span>
                                        {timeStr && <span className="event-time">{timeStr}</span>}
                                    </div>
                                </div>
                            );
                        }

                        // 2. Dice Rolls (Centered Tactical Badge)
                        if (isRoll) {
                            return (
                                <div key={entry.id} className="chat-row center-row" data-testid="chat-msg-roll">
                                    <div className="roll-tactical-pill">
                                        <span className="roll-icon"><VectorIcon name="dice" /></span>
                                        <div className="roll-content">
                                            <span className="roll-sender">{entry.sender}</span>
                                            <span className="roll-text">{entry.text}</span>
                                        </div>
                                        {timeStr && <span className="roll-time">{timeStr}</span>}
                                    </div>
                                </div>
                            );
                        }

                        // 3. Dungeon Master Narrative Card (Distinguished layout with DM Crest)
                        if (avatar.role === 'dm') {
                            return (
                                <div key={entry.id} className="chat-row dm-row" data-testid="chat-msg-dm">
                                    <Tooltip
                                        content={
                                            <div className="hover-tip-card">
                                                <h4 className="hover-tip-name" style={{ color: 'var(--color-creme)' }}>Dungeon Master</h4>
                                                <span className="hover-tip-sub">Narrator & Arbiter of Rules</span>
                                                <p className="hover-tip-desc" style={{ marginTop: '6px' }}>
                                                    Weaves the fate, environment, encounters, and challenges of the realm.
                                                </p>
                                            </div>
                                        }
                                        position="right"
                                    >
                                        <div
                                            className="chat-avatar-wrapper avatar-dm reveal-highlight geometric-tilt"
                                            title="Dungeon Master"
                                            onMouseMove={handleTiltAndHighlight}
                                            onMouseLeave={handleTiltReset}
                                        >
                                            <img
                                                src={avatar.url}
                                                alt="DM"
                                                className="chat-avatar-img dm-crest-img"
                                                onError={(e) => {
                                                    (e.currentTarget as HTMLImageElement).src = avatar.fallback;
                                                }}
                                            />
                                            <span className="avatar-status-badge dm-badge"><VectorIcon name="crown" /></span>
                                        </div>
                                    </Tooltip>

                                    <div
                                        className="dm-narrative-card reveal-highlight geometric-tilt"
                                        onMouseMove={handleTiltAndHighlight}
                                        onMouseLeave={handleTiltReset}
                                    >
                                        <div className="dm-card-header">
                                            <div className="dm-title-badge">
                                                <span className="dm-crown"><VectorIcon name="crown" /></span>
                                                <span className="dm-title">{entry.sender || 'DUNGEON MASTER'}</span>
                                            </div>
                                            {timeStr && <span className="chat-timestamp">{timeStr}</span>}
                                        </div>
                                        <div className="dm-narrative-prose">
                                            {highlightNarrativeKeywords(entry.text, knownEntityNames)}
                                        </div>
                                    </div>
                                </div>
                            );
                        }

                        // 4. Current Player's Actions/Speech (Right-Aligned Bubble with Player Portrait on Right)
                        if (avatar.isMe) {
                            return (
                                <div key={entry.id} className="chat-row player-row" data-testid="chat-msg-player">
                                    <div className="chat-bubble-group group-right">
                                        <div className="chat-sender-meta meta-right">
                                            {timeStr && <span className="chat-timestamp">{timeStr}</span>}
                                            <span className="chat-sender-name player-name-me">
                                                You ({activeCharacter?.name || entry.sender})
                                            </span>
                                        </div>
                                        <div
                                            className="chat-bubble player-bubble reveal-highlight geometric-tilt"
                                            onMouseMove={handleTiltAndHighlight}
                                            onMouseLeave={handleTiltReset}
                                        >
                                            <div className="bubble-text">{entry.text}</div>
                                        </div>
                                    </div>
                                    <Tooltip
                                        content={<CharacterStatHoverCard character={avatar.character || activeCharacter} />}
                                        position="left"
                                    >
                                        <div
                                            className="chat-avatar-wrapper avatar-player reveal-highlight geometric-tilt"
                                            title={avatar.name}
                                            onMouseMove={handleTiltAndHighlight}
                                            onMouseLeave={handleTiltReset}
                                        >
                                            <img
                                                src={avatar.url}
                                                alt={avatar.name}
                                                className="chat-avatar-img player-avatar-img"
                                                onError={(e) => {
                                                    (e.currentTarget as HTMLImageElement).src = avatar.fallback;
                                                }}
                                            />
                                            <span className="avatar-status-badge player-badge"><VectorIcon name="sword" /></span>
                                        </div>
                                    </Tooltip>
                                </div>
                            );
                        }

                        // 5. Party Members & NPCs (Left-Aligned Bubble with Portrait on Left)
                        return (
                            <div
                                key={entry.id}
                                className={`chat-row incoming-row ${avatar.isHostile ? 'hostile-row' : ''}`}
                                data-testid="chat-msg-incoming"
                            >
                                <Tooltip
                                    content={
                                        avatar.character ? (
                                            <CharacterStatHoverCard character={avatar.character} />
                                        ) : (
                                            <div className="hover-tip-card">
                                                <h4 className="hover-tip-name" style={{ color: 'var(--color-creme)' }}>{avatar.name}</h4>
                                                <span className="hover-tip-sub">{avatar.isHostile ? 'Hostile Foe' : 'Party Member'}</span>
                                            </div>
                                        )
                                    }
                                    position="right"
                                >
                                    <div
                                        className={`chat-avatar-wrapper ${avatar.isHostile ? 'avatar-hostile' : 'avatar-ally'} reveal-highlight geometric-tilt`}
                                        title={avatar.name}
                                        onMouseMove={handleTiltAndHighlight}
                                        onMouseLeave={handleTiltReset}
                                    >
                                        <img
                                            src={avatar.url}
                                            alt={avatar.name}
                                            className="chat-avatar-img incoming-avatar-img"
                                            onError={(e) => {
                                                (e.currentTarget as HTMLImageElement).src = avatar.fallback;
                                            }}
                                        />
                                        <span className={`avatar-status-badge ${avatar.isHostile ? 'hostile-badge' : 'ally-badge'}`}>
                                            {avatar.isHostile ? <VectorIcon name="helm" /> : <VectorIcon name="shield" />}
                                        </span>
                                    </div>
                                </Tooltip>
                                <div className="chat-bubble-group group-left">
                                    <div className="chat-sender-meta meta-left">
                                        <span className={`chat-sender-name ${avatar.isHostile ? 'sender-hostile' : 'sender-ally'}`}>
                                            {entry.sender}
                                        </span>
                                        <span className={`chat-role-pill ${avatar.isHostile ? 'role-hostile' : 'role-ally'}`}>
                                            {avatar.isHostile ? 'Enemy' : avatar.role === 'ally' ? 'Party' : 'NPC'}
                                        </span>
                                        {timeStr && <span className="chat-timestamp">{timeStr}</span>}
                                    </div>
                                    <div
                                        className={`chat-bubble incoming-bubble ${avatar.isHostile ? 'hostile-bubble' : ''} reveal-highlight geometric-tilt`}
                                        onMouseMove={handleTiltAndHighlight}
                                        onMouseLeave={handleTiltReset}
                                    >
                                        <div className="bubble-text">{highlightNarrativeKeywords(entry.text, knownEntityNames)}</div>
                                    </div>
                                </div>
                            </div>
                        );
                    })
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Fancy DM Thinking Arcane Overlay */}
            {isResolving && (
                <div className="dm-thinking-overlay" data-testid="dm-thinking-overlay">
                    <div className="dm-thinking-card">
                        <div className="dm-arcane-runes-spinner">
                            <span className="rune-glyph">ᚱ</span>
                            <span className="rune-ring ring-outer" />
                            <span className="rune-ring ring-inner" />
                        </div>
                        <div className="dm-thinking-text-group">
                            <h4 className="dm-thinking-title">
                                <VectorIcon name="crown" />
                                <span>{language === 'ru' ? 'Мастер Подземелий формулирует исход...' : 'Dungeon Master is Weaving the Story...'}</span>
                            </h4>
                            <p className="dm-thinking-subtitle">
                                {language === 'ru'
                                    ? 'Нити судеб сплетаются в единое сказание. Прием действий заблокирован до завершения описания.'
                                    : 'The threads of fate intertwine. Action submission locked until narration concludes.'}
                            </p>
                            <div className="dm-thinking-progress-bar">
                                <div className="dm-thinking-progress-shimmer" />
                            </div>
                        </div>
                    </div>
                </div>
            )}
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

            {/* Integrated Foldable Fast Commands Bar */}
            <div className="chat-fast-commands-container">
                <div className="fast-commands-header">
                    <button
                        type="button"
                        className="fast-commands-toggle-btn"
                        onClick={() => setShowFastCommands(!showFastCommands)}
                        title="Toggle Fast Commands Bar"
                    >
                        <span className="commands-icon">⚡</span>
                        <span className="commands-title">{t.chat.fastCommands}</span>
                        <span className="commands-chevron">{showFastCommands ? (language === 'ru' ? '▲ Свернуть' : '▲ Fold') : (language === 'ru' ? '▼ Развернуть' : '▼ Expand')}</span>
                    </button>

                    {showFastCommands && (characterSpells.length > 0 || characterInventory.length > 0) && (
                        <div className="fast-commands-category-tabs">
                            <button
                                type="button"
                                className={`category-tab ${commandCategory === 'actions' ? 'active' : ''}`}
                                onClick={() => setCommandCategory('actions')}
                            >
                                {language === 'ru' ? 'Действия' : 'Actions'}
                            </button>
                            {characterSpells.length > 0 && (
                                <button
                                    type="button"
                                    className={`category-tab ${commandCategory === 'spells' ? 'active' : ''}`}
                                    onClick={() => setCommandCategory('spells')}
                                >
                                    {language === 'ru' ? `Заклинания (${characterSpells.length})` : `Spells (${characterSpells.length})`}
                                </button>
                            )}
                            {characterInventory.length > 0 && (
                                <button
                                    type="button"
                                    className={`category-tab ${commandCategory === 'items' ? 'active' : ''}`}
                                    onClick={() => setCommandCategory('items')}
                                >
                                    {language === 'ru' ? `Предметы (${characterInventory.length})` : `Items (${characterInventory.length})`}
                                </button>
                            )}
                        </div>
                    )}
                </div>

                {showFastCommands && (
                    <div className="fast-commands-body">
                        {commandCategory === 'actions' && (
                            <div className="fast-chips-row">
                                {fastCommands.map(cmd => (
                                    <Tooltip
                                        key={cmd.id}
                                        content={
                                            <div className="hover-tip-card">
                                                <h4 className="hover-tip-name" style={{ color: 'var(--color-creme)' }}>{cmd.label}</h4>
                                                <p className="hover-tip-desc" style={{ marginTop: '4px' }}>{cmd.description}</p>
                                            </div>
                                        }
                                        position="top"
                                    >
                                        <button
                                            type="button"
                                            className="fast-chip-btn reveal-highlight geometric-tilt"
                                            onClick={() => handlePresetClick(cmd)}
                                            disabled={isInputDisabled}
                                            onMouseMove={handleTiltAndHighlight}
                                            onMouseLeave={handleTiltReset}
                                        >
                                            <VectorIcon name={cmd.icon} />
                                            <span>{cmd.label}</span>
                                        </button>
                                    </Tooltip>
                                ))}
                            </div>
                        )}
                        {commandCategory === 'spells' && (
                            <div className="fast-chips-row">
                                {characterSpells.map((spell: any, idx: number) => {
                                    const name = typeof spell === 'string' ? spell : spell.name;
                                    return (
                                        <Tooltip
                                            key={`spell-${idx}`}
                                            content={<SpellHoverCard spell={spell} />}
                                            position="top"
                                        >
                                            <button
                                                type="button"
                                                className="fast-chip-btn spell-chip reveal-highlight geometric-tilt"
                                                onClick={() => handleSpellClick(spell)}
                                                disabled={isInputDisabled}
                                                onMouseMove={handleTiltAndHighlight}
                                                onMouseLeave={handleTiltReset}
                                            >
                                                <VectorIcon name="magic" />
                                                <span>{name}</span>
                                            </button>
                                        </Tooltip>
                                    );
                                })}
                            </div>
                        )}
                        {commandCategory === 'items' && (
                            <div className="fast-chips-row">
                                {characterInventory.map((item: any, idx: number) => {
                                    const name = typeof item === 'string' ? item : item.name;
                                    return (
                                        <Tooltip
                                            key={`item-${idx}`}
                                            content={<ItemHoverCard item={item} />}
                                            position="top"
                                        >
                                            <button
                                                type="button"
                                                className="fast-chip-btn item-chip reveal-highlight geometric-tilt"
                                                onClick={() => handleItemClick(item)}
                                                disabled={isInputDisabled}
                                                onMouseMove={handleTiltAndHighlight}
                                                onMouseLeave={handleTiltReset}
                                            >
                                                <VectorIcon name="potion" />
                                                <span>{name}</span>
                                            </button>
                                        </Tooltip>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Integrated Action Input Area (United with Chat) */}
            <div className="chat-input-area">
                {clarificationText && (
                    <div className="chat-clarification-banner">
                        <span className="banner-icon"><VectorIcon name="rune" /></span>
                        <div className="banner-body">
                            <strong>{language === 'ru' ? 'Уточнение Мастера:' : 'DM Clarification:'}</strong> {clarificationText}
                        </div>
                    </div>
                )}

                {isDMThinking && (
                    <div className="chat-dm-thinking-pill">
                        <span className="thinking-pulse" />
                        <span>{language === 'ru' ? 'Мастер подземелий описывает исход...' : 'The Dungeon Master is chronicling the outcome...'}</span>
                    </div>
                )}

                {isCombatMode && !isMyTurnInCombat && activeCombatant && (
                    <div className="chat-turn-lock-banner" data-testid="combat-turn-lock-banner">
                        <span className="turn-lock-icon">⏳</span>
                        <span>
                            {language === 'ru'
                                ? `Сейчас ход бойца: «${activeCombatant}». Дождитесь своей очереди в тактическом порядке инициативы.`
                                : `Currently taking turn: «${activeCombatant}». Please await your turn in initiative order.`}
                        </span>
                    </div>
                )}

                <form onSubmit={handleActionSubmit} className="chat-action-form">
                    <textarea
                        ref={inputRef}
                        className="chat-action-textarea"
                        value={actionText}
                        onChange={(e) => setActionText(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={
                            !isMyTurnInCombat && activeCombatant
                                ? (language === 'ru' ? `Ожидание хода ${activeCombatant}...` : `Waiting for ${activeCombatant}'s turn...`)
                                : activeCharacter
                                    ? (language === 'ru'
                                        ? `Что делает ${activeCharacter.name}? (Enter — действие, Shift+Enter — перенос строки)`
                                        : `What does ${activeCharacter.name} do? (Enter to act, Shift+Enter for newline)`)
                                    : (language === 'ru'
                                        ? 'Что делает ваш герой? (Enter — действие, Shift+Enter — перенос строки)'
                                        : 'What does your hero do? (Enter to act, Shift+Enter for newline)')
                        }
                        rows={1}
                        disabled={isInputDisabled}
                    />

                    <div className="chat-form-buttons">
                        <button
                            type="submit"
                            className="chat-act-btn"
                            disabled={!actionText.trim() || isInputDisabled}
                            title={t.chat.actButton}
                        >
                            {isResolving ? t.chat.resolving : <><VectorIcon name="sword" /> {t.chat.actButton}</>}
                        </button>

                        <button
                            type="button"
                            className="chat-pass-btn"
                            onClick={() => {
                                if (activeCharacter && !isInputDisabled) {
                                    sendAction(language === 'ru' ? 'Я пропускаю ход.' : 'I pass my turn.', activeCharacter);
                                    setActionText('');
                                }
                            }}
                            disabled={isInputDisabled}
                            title={language === 'ru' ? 'Пропустить ход' : 'Pass turn without taking an action'}
                        >
                            {language === 'ru' ? 'Пас' : 'Pass'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};
