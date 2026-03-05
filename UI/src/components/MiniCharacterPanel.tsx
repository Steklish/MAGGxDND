import React from 'react';
import { useGameStore } from '../store/gameStore';
import { Tooltip } from './common/Tooltip';
import './MiniCharacterPanel.css';

interface CharacterMiniPreviewProps {
    character: any;
}

const CharacterMiniPreview: React.FC<CharacterMiniPreviewProps> = ({ character }) => {
    const hpPercent = (character.current_hp / character.max_hp) * 100;
    const hpColor = hpPercent > 50
        ? 'var(--accent-green)'
        : hpPercent > 25
            ? 'var(--accent-yellow)'
            : 'var(--accent-red)';

    return (
        <div className="character-mini-preview">
            <div className="mini-preview-header">
                <span className="mini-preview-name">{character.name}</span>
                <span className="mini-preview-subtitle">
                    {character.race} {character.char_class} Lvl {character.level}
                </span>
            </div>

            <div className="mini-preview-hp">
                <div className="mini-preview-hp-bar">
                    <div
                        className="mini-preview-hp-fill"
                        style={{ width: `${hpPercent}%`, backgroundColor: hpColor }}
                    />
                </div>
                <span className="mini-preview-hp-text">{character.current_hp}/{character.max_hp}</span>
            </div>

            <div className="mini-preview-stats">
                <span>AC: <strong>{character.armor_class}</strong></span>
                <span>SPD: <strong>{character.speed}</strong></span>
                <span>Init: <strong>+{character.initiative_bonus}</strong></span>
            </div>

            {character.active_conditions && character.active_conditions.trim() && (
                <div className="mini-preview-conditions">
                    <span className="mini-preview-condition-title">Conditions:</span>
                    {character.active_conditions.split('\n')?.map((cond: string, idx: number) => (
                        <span key={idx} className="mini-preview-condition">{cond}</span>
                    ))}
                </div>
            )}
        </div>
    );
};

interface MiniCharacterIconProps {
    character: any;
    isCurrentTurn: boolean;
    isActive: boolean;
    onClick: () => void;
}

const MiniCharacterIcon: React.FC<MiniCharacterIconProps> = ({ 
    character, 
    isCurrentTurn, 
    isActive,
    onClick 
}) => {
    const hpPercent = (character.current_hp / character.max_hp) * 100;
    const hpColor = hpPercent > 50
        ? 'var(--accent-green)'
        : hpPercent > 25
            ? 'var(--accent-yellow)'
            : 'var(--accent-red)';

    return (
        <Tooltip content={<CharacterMiniPreview character={character} />} position="right">
            <div 
                className={`mini-character-icon ${isCurrentTurn ? 'current-turn' : ''} ${isActive ? 'active' : ''}`}
                onClick={onClick}
            >
                <div className="mini-icon-portrait">
                    <span className="mini-icon-initial">{character.name[0].toUpperCase()}</span>
                    <div 
                        className="mini-icon-hp-indicator" 
                        style={{ backgroundColor: hpColor }}
                    />
                </div>
                {isCurrentTurn && <div className="mini-turn-indicator" />}
            </div>
        </Tooltip>
    );
};

export const MiniCharacterPanel: React.FC = () => {
    const { session, activeCharacter, setActiveCharacter } = useGameStore();

    if (!session) {
        return (
            <div className="mini-character-panel">
                <div className="mini-panel-icon">👥</div>
            </div>
        );
    }

    const players = session.players?.map(p => p.character) || [];
    const npcs = session.npcs?.map(n => n.character) || [];

    const getCurrentTurnCharacter = () => {
        if (!session.turn_queue || session.turn_queue.length === 0) return null;
        const sortedQueue = [...session.turn_queue].sort((a, b) => a[2] - b[2]);
        return sortedQueue[0]?.[0];
    };

    const currentTurnChar = getCurrentTurnCharacter();

    const handleSelectCharacter = (char: any) => {
        if (activeCharacter?.name === char.name) {
            setActiveCharacter(null);
        } else {
            setActiveCharacter(char);
        }
    };

    return (
        <div className="mini-character-panel">
            <div className="mini-panel-section">
                <div className="mini-section-icon" title="Players">👤</div>
                <div className="mini-icons-list">
                    {players.filter(Boolean).map(char => (
                        <MiniCharacterIcon
                            key={char?.name || 'unknown'}
                            character={char}
                            isCurrentTurn={currentTurnChar?.name === char?.name}
                            isActive={activeCharacter?.name === char?.name}
                            onClick={() => handleSelectCharacter(char)}
                        />
                    ))}
                </div>
            </div>

            {npcs.length > 0 && (
                <div className="mini-panel-section">
                    <div className="mini-section-icon" title="NPCs">🎭</div>
                    <div className="mini-icons-list">
                        {npcs.filter(Boolean).map(char => (
                            <MiniCharacterIcon
                                key={char?.name || 'unknown'}
                                character={char}
                                isCurrentTurn={currentTurnChar?.name === char?.name}
                                isActive={activeCharacter?.name === char?.name}
                                onClick={() => handleSelectCharacter(char)}
                            />
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};
