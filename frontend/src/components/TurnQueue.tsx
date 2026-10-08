import React from 'react';
import { useGameStore } from '../store/gameStore';
import { VectorIcon } from './common/VectorIcon';
import { Tooltip } from './common/Tooltip';
import { CharacterStatHoverCard } from './common/HoverTips';
import { handleTiltAndHighlight, handleTiltReset } from '../utils/cardTilt';
import './TurnQueue.css';

export const TurnQueue: React.FC = () => {
    const { turnQueue, currentSession, session, language } = useGameStore();

    if (turnQueue.length === 0) {
        return (
            <div className="turn-queue" data-testid="turn-queue">
                <span className="queue-empty">{language === 'ru' ? 'Очередь ходов: Пусто' : 'Turn Queue: Empty'}</span>
            </div>
        );
    }

    const activeSession = currentSession || session;
    const allCharacters = [
        ...(activeSession?.players || []).map((p: any) => p?.character || p),
        ...(activeSession?.npcs || []).map((n: any) => n?.character || n),
    ];

    // Normalize entries defensively to handle both structured objects and legacy array formats
    const normalizedQueue = turnQueue.map((entry: any) => {
        if (Array.isArray(entry)) {
            const charIdentifier = entry[0];
            const charName = typeof charIdentifier === 'object' ? (charIdentifier?.name || 'Hero') : String(charIdentifier || 'Hero');
            return {
                character: charName,
                time_added: typeof entry[1] === 'number' ? entry[1] : 0,
                next_turn: typeof entry[2] === 'number' ? entry[2] : 0,
            };
        }
        return {
            character: entry.character || entry.name || 'Hero',
            time_added: typeof entry.time_added === 'number' ? entry.time_added : 0,
            next_turn: typeof entry.next_turn === 'number' ? entry.next_turn : 0,
            character_type: entry.character_type,
        };
    });

    // Deduplicate by character name (keep earliest turn for each combatant)
    const uniqueQueue: typeof normalizedQueue = [];
    const seen = new Set<string>();
    for (const item of [...normalizedQueue].sort((a, b) => a.next_turn - b.next_turn)) {
        if (!seen.has(item.character)) {
            seen.add(item.character);
            uniqueQueue.push(item);
        }
    }

    const sortedQueue = uniqueQueue;

    return (
        <div className="turn-queue" data-testid="turn-queue">
            {/* Explanatory Initiative Header Badge */}
            <Tooltip
                content={
                    <div className="turn-help-tooltip">
                        <strong className="turn-help-title">⚔️ {language === 'ru' ? 'Тактический Порядок Инициативы' : 'Tactical Initiative Order'}</strong>
                        <p className="turn-help-text">
                            {language === 'ru'
                                ? 'Определяет последовательность действий в бою. Крайний слева боец совершает ход прямо сейчас. Завершение действия передает ход следующему участнику.'
                                : 'Determines sequence of actions in combat. The leftmost hero or adversary is currently taking their turn. Advancing actions moves the banner to the next participant.'}
                        </p>
                    </div>
                }
                position="bottom"
            >
                <div className="turn-queue-label-badge">
                    <span className="queue-badge-icon"><VectorIcon name="sword" /></span>
                    <span className="queue-badge-text">{language === 'ru' ? 'Инициатива' : 'Initiative'}</span>
                    <span className="queue-help-glyph" title="What is Initiative?">ℹ</span>
                </div>
            </Tooltip>

            {/* Turn Queue List */}
            <div className="turn-queue-list">
                {sortedQueue.map((entry, idx) => {
                    const charObj = allCharacters.find((c: any) => c?.name === entry.character);
                    const avatarUrl = charObj?.image_url;

                    return (
                        <Tooltip
                            key={`${entry.character}-${idx}-${entry.next_turn}`}
                            content={
                                charObj ? (
                                    <CharacterStatHoverCard character={charObj} />
                                ) : (
                                    <div className="turn-hover-fallback">
                                        <strong>{entry.character}</strong>
                                        <div>{language === 'ru' ? `Порядок хода #${idx + 1} • ${idx === 0 ? 'Ходит сейчас' : 'Ожидает ход'}` : `Initiative Order #${idx + 1} • ${idx === 0 ? 'Active Combatant' : 'Awaiting Turn'}`}</div>
                                    </div>
                                )
                            }
                            position="bottom"
                        >
                            <div
                                className={`turn-entry reveal-highlight geometric-tilt ${idx === 0 ? 'next' : ''}`}
                                data-testid={idx === 0 ? 'character-portrait-active' : 'character-portrait'}
                                onMouseMove={handleTiltAndHighlight}
                                onMouseLeave={handleTiltReset}
                            >
                                <span className="turn-order-num">#{idx + 1}</span>

                                {avatarUrl ? (
                                    <img
                                        src={avatarUrl}
                                        alt={entry.character}
                                        className="turn-avatar-mini"
                                        onError={(e) => {
                                            (e.currentTarget as HTMLElement).style.display = 'none';
                                        }}
                                    />
                                ) : (
                                    <span className="turn-indicator">
                                        {idx === 0 ? <VectorIcon name="sword" /> : <VectorIcon name="rune" />}
                                    </span>
                                )}

                                <span className="turn-character">{entry.character}</span>

                                <span className={`turn-state-pill ${idx === 0 ? 'state-active' : 'state-waiting'}`}>
                                    {idx === 0 ? (language === 'ru' ? 'ХОДИТ' : 'ACTING') : (language === 'ru' ? 'ЖДЕТ' : 'WAITING')}
                                </span>
                            </div>
                        </Tooltip>
                    );
                })}
            </div>
        </div>
    );
};
