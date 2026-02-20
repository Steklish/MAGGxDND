import React from 'react';
import { useGameStore } from '../store/gameStore';
import { Tooltip } from './common/Tooltip';
import './CharacterPanel.css';

interface CharacterPreviewProps {
    character: any;
}

const CharacterPreview: React.FC<CharacterPreviewProps> = ({ character }) => {
    const hpPercent = (character.current_hp / character.max_hp) * 100;
    const hpColor = hpPercent > 50 
        ? 'var(--accent-green)' 
        : hpPercent > 25 
            ? 'var(--accent-yellow)' 
            : 'var(--accent-red)';

    return (
        <div className="character-preview">
            <div className="character-preview-header">
                <div>
                    <span className="character-preview-name">{character.name}</span>
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
                        <span className="character-preview-stat-value">{character.stats.strength}</span>
                    </div>
                    <div className="character-preview-stat">
                        <span className="character-preview-stat-name">DEX</span>
                        <span className="character-preview-stat-value">{character.stats.dexterity}</span>
                    </div>
                    <div className="character-preview-stat">
                        <span className="character-preview-stat-name">CON</span>
                        <span className="character-preview-stat-value">{character.stats.constitution}</span>
                    </div>
                    <div className="character-preview-stat">
                        <span className="character-preview-stat-name">INT</span>
                        <span className="character-preview-stat-value">{character.stats.intelligence}</span>
                    </div>
                    <div className="character-preview-stat">
                        <span className="character-preview-stat-name">WIS</span>
                        <span className="character-preview-stat-value">{character.stats.wisdom}</span>
                    </div>
                    <div className="character-preview-stat">
                        <span className="character-preview-stat-name">CHA</span>
                        <span className="character-preview-stat-value">{character.stats.charisma}</span>
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
                    <span className="character-preview-hp-text">{character.current_hp}/{character.max_hp} HP</span>
                </div>
                <div className="character-preview-vitals-grid">
                    <span>AC: <strong>{character.armor_class}</strong></span>
                    <span>SPD: <strong>{character.speed}</strong></span>
                    <span>Prof: <strong>+{character.proficiency_bonus}</strong></span>
                    <span>Init: <strong>+{character.initiative_bonus}</strong></span>
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
                        {character.inventory.slice(0, 5).map((item: any, idx: number) => (
                            <div key={idx} className="character-preview-inventory-item">
                                <span>{item.name}</span>
                                {item.is_equipped && <span className="equipped-badge">⚔️</span>}
                            </div>
                        ))}
                        {character.inventory.length > 5 && (
                            <div className="character-preview-more">
                                +{character.inventory.length - 5} more items...
                            </div>
                        )}
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

    const players = session.players.map(p => p.character);
    const npcs = session.npcs.map(n => n.character);

    const handleSelectCharacter = (char: typeof players[0]) => {
        if (activeCharacter?.name === char.name) {
            setActiveCharacter(null);
        } else {
            setActiveCharacter(char);
        }
    };

    return (
        <div className="character-panel">
            <div className="panel-header">
                <h2>👥 Characters</h2>
            </div>

            <div className="characters-list">
                <div className="character-section">
                    <h3>Players ({players.length})</h3>
                    {players.map(char => (
                        <Tooltip 
                            key={char.name} 
                            content={<CharacterPreview character={char} />}
                            position="right"
                        >
                            <div
                                className={`character-card ${activeCharacter?.name === char.name ? 'active' : ''}`}
                                onClick={() => handleSelectCharacter(char)}
                            >
                                <div className="character-header">
                                    <span className="character-name">{char.name}</span>
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
                                        {char.active_conditions.split('\n').map((cond, idx) => (
                                            <span key={idx} className="condition-tag">{cond}</span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </Tooltip>
                    ))}
                </div>

                <div className="character-section">
                    <h3>NPCs ({npcs.length})</h3>
                    {npcs.map(char => (
                        <Tooltip 
                            key={char.name} 
                            content={<CharacterPreview character={char} />}
                            position="right"
                        >
                            <div
                                className={`character-card npc ${activeCharacter?.name === char.name ? 'active' : ''}`}
                                onClick={() => handleSelectCharacter(char)}
                            >
                                <div className="character-header">
                                    <span className="character-name">{char.name}</span>
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
                    ))}
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
                                <span className="ability-value">{activeCharacter.stats.strength}</span>
                            </div>
                            <div className="ability-score">
                                <span className="ability-name">DEX</span>
                                <span className="ability-value">{activeCharacter.stats.dexterity}</span>
                            </div>
                            <div className="ability-score">
                                <span className="ability-name">CON</span>
                                <span className="ability-value">{activeCharacter.stats.constitution}</span>
                            </div>
                            <div className="ability-score">
                                <span className="ability-name">INT</span>
                                <span className="ability-value">{activeCharacter.stats.intelligence}</span>
                            </div>
                            <div className="ability-score">
                                <span className="ability-name">WIS</span>
                                <span className="ability-value">{activeCharacter.stats.wisdom}</span>
                            </div>
                            <div className="ability-score">
                                <span className="ability-name">CHA</span>
                                <span className="ability-value">{activeCharacter.stats.charisma}</span>
                            </div>
                        </div>
                    </div>

                    <div className="details-section">
                        <h4>Abilities & Spells</h4>
                        {activeCharacter.abilities.length > 0 ? (
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
                        {activeCharacter.inventory.length > 0 ? (
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
