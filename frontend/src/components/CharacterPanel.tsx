import React from 'react';
import { useGameStore } from '../store/gameStore';
import { Tooltip } from './common/Tooltip';
import './CharacterPanel.css';

interface CharacterPreviewProps {
    character: any;
    type?: 'player' | 'ally_npc' | 'hostile_npc' | 'neutral_npc';
}

const getCharacterType = (char: any, session: any): 'player' | 'ally_npc' | 'hostile_npc' | 'neutral_npc' => {
    // Check if character is a player
    const players = session?.players || [];
    for (const p of players) {
        if (p.character?.name === char.name) return 'player';
    }

    // Check if character is an NPC
    const npcs = session?.npcs || [];
    for (const n of npcs) {
        if (n.character?.name === char.name) {
            const alignment = n.character.alignment || '';
            if (alignment.includes('Good')) return 'ally_npc';
            if (alignment.includes('Evil') || alignment.includes('Chaotic')) return 'hostile_npc';
            return 'neutral_npc';
        }
    }

    return 'player';
};

const getTypeColor = (type: string) => {
    switch (type) {
        case 'player': return 'var(--accent-purple)';
        case 'ally_npc': return 'var(--accent-green)';
        case 'hostile_npc': return 'var(--accent-red)';
        case 'neutral_npc': return 'var(--accent-yellow)';
        default: return 'var(--accent-yellow)';
    }
};

const getTypeBgGradient = (type: string) => {
    switch (type) {
        case 'player': return 'linear-gradient(135deg, rgba(157, 78, 221, 0.15) 0%, rgba(157, 78, 221, 0.05) 100%)';
        case 'ally_npc': return 'linear-gradient(135deg, rgba(42, 157, 143, 0.15) 0%, rgba(42, 157, 143, 0.05) 100%)';
        case 'hostile_npc': return 'linear-gradient(135deg, rgba(230, 57, 70, 0.15) 0%, rgba(230, 57, 70, 0.05) 100%)';
        case 'neutral_npc': return 'linear-gradient(135deg, rgba(233, 196, 106, 0.15) 0%, rgba(233, 196, 106, 0.05) 100%)';
        default: return 'linear-gradient(135deg, rgba(233, 196, 106, 0.15) 0%, rgba(233, 196, 106, 0.05) 100%)';
    }
};

const CharacterPreview: React.FC<CharacterPreviewProps> = ({ character, type = 'player' }) => {
    const hpPercent = (character.current_hp / character.max_hp) * 100;
    const hpColor = hpPercent > 50
        ? 'var(--accent-green)'
        : hpPercent > 25
            ? 'var(--accent-yellow)'
            : 'var(--accent-red)';
    
    const typeColor = getTypeColor(type);

    return (
        <div className="character-preview">
            <div className="character-preview-header" style={{ borderBottomColor: typeColor }}>
                <div>
                    <span className="character-preview-name" style={{ color: typeColor }}>{character.name}</span>
                    <span className="character-preview-subtitle">
                        {character.race} {character.char_class}, Level {character.level}
                    </span>
                </div>
            </div>

            <div className="character-preview-section">
                <span className="character-preview-section-title">Ability Scores</span>
                <div className="character-preview-stats">
                    <div className="character-preview-stat">
                        <span className="character-preview-stat-name">STR</span>
                        <span className="character-preview-stat-value">{character.stats?.strength || 10}</span>
                    </div>
                    <div className="character-preview-stat">
                        <span className="character-preview-stat-name">DEX</span>
                        <span className="character-preview-stat-value">{character.stats?.dexterity || 10}</span>
                    </div>
                    <div className="character-preview-stat">
                        <span className="character-preview-stat-name">CON</span>
                        <span className="character-preview-stat-value">{character.stats?.constitution || 10}</span>
                    </div>
                    <div className="character-preview-stat">
                        <span className="character-preview-stat-name">INT</span>
                        <span className="character-preview-stat-value">{character.stats?.intelligence || 10}</span>
                    </div>
                    <div className="character-preview-stat">
                        <span className="character-preview-stat-name">WIS</span>
                        <span className="character-preview-stat-value">{character.stats?.wisdom || 10}</span>
                    </div>
                    <div className="character-preview-stat">
                        <span className="character-preview-stat-name">CHA</span>
                        <span className="character-preview-stat-value">{character.stats?.charisma || 10}</span>
                    </div>
                </div>
            </div>

            <div className="character-preview-section">
                <span className="character-preview-section-title">Vitals</span>
                <div className="character-preview-hp">
                    <div className="character-preview-hp-bar">
                        <div
                            className="character-preview-hp-fill"
                            style={{ width: `${hpPercent}%`, backgroundColor: hpColor }}
                        />
                    </div>
                    <span className="character-preview-hp-text">{character.current_hp || 10}/{character.max_hp || 10} HP</span>
                </div>
                <div className="character-preview-vitals-grid">
                    <span>AC: <strong>{character.armor_class || 10}</strong></span>
                    <span>SPD: <strong>{character.speed || 30}</strong></span>
                    <span>Prof: <strong>+{character.proficiency_bonus || 2}</strong></span>
                    <span>Init: <strong>+{character.initiative_bonus || 0}</strong></span>
                </div>
            </div>

            {character.active_conditions && character.active_conditions.trim() && (
                <div className="character-preview-section">
                    <span className="character-preview-section-title">Conditions</span>
                    <div className="character-preview-conditions">
                        {character.active_conditions.split('\n').map((cond: string, idx: number) => (
                            <span key={idx} className="character-preview-condition">{cond}</span>
                        ))}
                    </div>
                </div>
            )}

            {character.abilities && character.abilities.length > 0 && (
                <div className="character-preview-section">
                    <span className="character-preview-section-title">Abilities & Spells</span>
                    <div className="character-preview-abilities">
                        {character.abilities.map((ability: any, idx: number) => (
                            <div key={idx} className="character-preview-ability">
                                <div className="character-preview-ability-name">
                                    {ability.name}
                                    {ability.level > 0 && <span className="spell-level-tag">Lvl {ability.level}</span>}
                                </div>
                                <div className="character-preview-ability-desc">{ability.short_summary}</div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {character.inventory && character.inventory.length > 0 && (
                <div className="character-preview-section">
                    <span className="character-preview-section-title">Inventory ({character.inventory.length})</span>
                    <div className="character-preview-inventory">
                        {character.inventory.map((item: any, idx: number) => (
                            <div key={idx} className="character-preview-inventory-item">
                                <span>{item.name}</span>
                                {item.is_equipped && <span className="equipped-badge">⚔️</span>}
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export const CharacterPanel: React.FC = () => {
    const { session, activeCharacter, setActiveCharacter } = useGameStore();

    if (!session) {
        return (
            <div className="character-panel">
                <div className="no-session">No session</div>
            </div>
        );
    }

    const players = session.players?.map(p => p.character) || [];
    const npcs = session.npcs?.map(n => n.character) || [];

    // Get current turn character
    const getCurrentTurnCharacter = () => {
        if (!session.turn_queue || session.turn_queue.length === 0) return null;
        const sortedQueue = [...session.turn_queue].sort((a, b) => a[2] - b[2]);
        return sortedQueue[0]?.[0];
    };

    const currentTurnChar = getCurrentTurnCharacter();

    const handleSelectCharacter = (char: typeof players[0]) => {
        if (activeCharacter?.name === char.name) {
            setActiveCharacter(null);
        } else {
            setActiveCharacter(char as any);
        }
    };

    return (
        <div className="character-panel">
            <div className="panel-header">
                <h2>👥 Characters</h2>
            </div>

            <div className="characters-list">
                <div className="character-section">
                    <h3 style={{ color: 'var(--accent-yellow)' }}>Players ({players.length})</h3>
                    {players.filter(Boolean).map(char => {
                        if (!char) return null;
                        const charType = getCharacterType(char, session);
                        const typeColor = getTypeColor(charType);
                        const typeBg = getTypeBgGradient(charType);
                        return (
                        <Tooltip
                            key={char.name}
                            content={<CharacterPreview character={char} type={charType} />}
                            position="right"
                            borderColor={typeColor}
                            background={typeBg}
                        >
                            <div
                                className={`character-card ${activeCharacter?.name === char.name ? 'active' : ''} ${currentTurnChar?.name === char.name ? 'current-turn' : ''}`}
                                onClick={() => handleSelectCharacter(char)}
                                style={{
                                    borderColor: activeCharacter?.name === char.name ? typeColor : 'var(--border-color)',
                                    background: typeBg
                                }}
                            >
                                <div className="character-header">
                                    <span className="character-name" style={{ color: typeColor }}>{char.name}</span>
                                    <span className="character-class">{char.char_class}</span>
                                </div>
                                <div className="character-details">
                                    <span className="character-race">{char.race}</span>
                                    <span className="character-level">Lvl {char.level}</span>
                                </div>
                                <div className="character-stats">
                                    <div className="hp-bar">
                                        <div
                                            className="hp-fill"
                                            style={{
                                                width: `${(char.current_hp / char.max_hp) * 100}%`,
                                                backgroundColor: char.current_hp / char.max_hp > 0.5
                                                    ? 'var(--accent-green)'
                                                    : char.current_hp / char.max_hp > 0.25
                                                        ? 'var(--accent-yellow)'
                                                        : 'var(--accent-red)'
                                            }}
                                        />
                                        <span className="hp-text">{char.current_hp}/{char.max_hp} HP</span>
                                    </div>
                                    <div className="ac-stat">
                                        <span>AC: {char.armor_class}</span>
                                        <span>SPD: {char.speed}</span>
                                    </div>
                                </div>
                                {char.active_conditions && char.active_conditions.trim() && (
                                    <div className="character-conditions">
                                        {char.active_conditions.split('\n').map((cond: string, idx: number) => (
                                            <span key={idx} className="condition-tag" style={{ borderColor: typeColor, color: typeColor }}>{cond}</span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </Tooltip>
                    );
                    })}
                </div>

                <div className="character-section">
                    <h3 style={{ color: 'var(--accent-yellow)' }}>NPCs ({npcs.length})</h3>
                    {npcs.filter(Boolean).map(char => {
                        if (!char) return null;
                        const charType = getCharacterType(char, session);
                        const typeColor = getTypeColor(charType);
                        const typeBg = getTypeBgGradient(charType);
                        return (
                        <Tooltip
                            key={char.name}
                            content={<CharacterPreview character={char} type={charType} />}
                            position="right"
                            borderColor={typeColor}
                            background={typeBg}
                        >
                            <div
                                className={`character-card ${activeCharacter?.name === char.name ? 'active' : ''} ${currentTurnChar?.name === char.name ? 'current-turn' : ''}`}
                                onClick={() => handleSelectCharacter(char)}
                                style={{
                                    borderColor: activeCharacter?.name === char.name ? typeColor : 'var(--border-color)',
                                    background: typeBg
                                }}
                            >
                                <div className="character-header">
                                    <span className="character-name" style={{ color: typeColor }}>{char.name}</span>
                                    <span className="character-class">{char.char_class}</span>
                                </div>
                                <div className="character-details">
                                    <span className="character-race">{char.race}</span>
                                    <span className="character-level">Lvl {char.level}</span>
                                </div>
                                <div className="character-stats">
                                    <div className="hp-bar">
                                        <div
                                            className="hp-fill"
                                            style={{
                                                width: `${(char.current_hp / char.max_hp) * 100}%`
                                            }}
                                        />
                                        <span className="hp-text">{char.current_hp}/{char.max_hp} HP</span>
                                    </div>
                                </div>
                            </div>
                        </Tooltip>
                    );
                    })}
                </div>
            </div>

            {activeCharacter && (
                <div className="character-details-panel">
                    <h3>{activeCharacter.name}</h3>

                    <div className="details-section">
                        <h4>Ability Scores</h4>
                        <div className="ability-scores">
                            <div className="ability-score">
                                <span className="ability-name">STR</span>
                                <span className="ability-value">{activeCharacter.stats?.strength || 10}</span>
                            </div>
                            <div className="ability-score">
                                <span className="ability-name">DEX</span>
                                <span className="ability-value">{activeCharacter.stats?.dexterity || 10}</span>
                            </div>
                            <div className="ability-score">
                                <span className="ability-name">CON</span>
                                <span className="ability-value">{activeCharacter.stats?.constitution || 10}</span>
                            </div>
                            <div className="ability-score">
                                <span className="ability-name">INT</span>
                                <span className="ability-value">{activeCharacter.stats?.intelligence || 10}</span>
                            </div>
                            <div className="ability-score">
                                <span className="ability-name">WIS</span>
                                <span className="ability-value">{activeCharacter.stats?.wisdom || 10}</span>
                            </div>
                            <div className="ability-score">
                                <span className="ability-name">CHA</span>
                                <span className="ability-value">{activeCharacter.stats?.charisma || 10}</span>
                            </div>
                        </div>
                    </div>

                    <div className="details-section">
                        <h4>Abilities & Spells</h4>
                        {activeCharacter.abilities?.length > 0 ? (
                            <div className="abilities-list">
                                {activeCharacter.abilities.map((ability, idx) => (
                                    <div key={idx} className="ability-item">
                                        <div className="ability-item-header">
                                            <span className="ability-item-name">{ability.name}</span>
                                            {ability.level > 0 && (
                                                <span className="spell-level">Level {ability.level}</span>
                                            )}
                                        </div>
                                        <p className="ability-item-desc">{ability.short_summary}</p>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="no-abilities">No abilities</p>
                        )}
                    </div>

                    <div className="details-section">
                        <h4>Inventory</h4>
                        {activeCharacter.inventory?.length > 0 ? (
                            <div className="inventory-list">
                                {activeCharacter.inventory.map((item, idx) => (
                                    <div key={idx} className={`inventory-item ${item.is_equipped ? 'equipped' : ''}`}>
                                        <span className="item-name">{item.name}</span>
                                        {item.is_equipped && <span className="equipped-tag">⚔️</span>}
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="no-inventory">Empty inventory</p>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};
