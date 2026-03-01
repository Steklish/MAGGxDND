import React from 'react';
import { useGameStore } from '../store/gameStore';
import './TurnQueue.css';

export const TurnQueue: React.FC = () => {
    const { turnQueue } = useGameStore();

    if (turnQueue.length === 0) {
        return (
            <div className="turn-queue">
                <span className="queue-empty">Turn Queue: Empty</span>
            </div>
        );
    }

    // Sort by next_turn to show order
    const sortedQueue = [...turnQueue].sort((a, b) => a.next_turn - b.next_turn);

    return (
        <div className="turn-queue">
            <div className="turn-queue-list">
                {sortedQueue.map((entry, idx) => (
                    <div
                        key={`${entry.character}-${entry.next_turn}`}
                        className={`turn-entry ${idx === 0 ? 'next' : ''}`}
                    >
                        <span className="turn-indicator">
                            {idx === 0 ? '🎯' : '⏳'}
                        </span>
                        <span className="turn-character">{entry.character}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};
