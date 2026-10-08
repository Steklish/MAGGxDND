import React from 'react';
import { useGameStore } from '../store/gameStore';
import './TurnQueue.css';

export const TurnQueue: React.FC = () => {
    const { turnQueue, currentSession, session } = useGameStore();

    if (turnQueue.length === 0) {
        return (
            <div className="turn-queue" data-testid="turn-queue">
                <span className="queue-empty">Turn Queue: Empty</span>
            </div>
        );
    }

    const activeSession = currentSession || session;
    const allCharacters = [
        ...(activeSession?.players || []).map((p: any) => p?.character || p),
        ...(activeSession?.npcs || []).map((n: any) => n?.character || n),
    ];

    // Sort by next_turn to show order
    const sortedQueue = [...turnQueue].sort((a, b) => a.next_turn - b.next_turn);

    return (
        <div className="turn-queue" data-testid="turn-queue">
            <div className="turn-queue-list">
                {sortedQueue.map((entry, idx) => {
                    const charObj = allCharacters.find((c: any) => c?.name === entry.character);
                    const avatarUrl = charObj?.image_url;
                    return (
                        <div
                            key={`${entry.character}-${entry.next_turn}`}
                            className={`turn-entry ${idx === 0 ? 'next' : ''}`}
                            data-testid={idx === 0 ? 'character-portrait-active' : 'character-portrait'}
                        >
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
                                    {idx === 0 ? '🎯' : '⏳'}
                                </span>
                            )}
                            <span className="turn-character">{entry.character}</span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};
