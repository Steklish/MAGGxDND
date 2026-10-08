import React from 'react';
import { VectorIcon } from './VectorIcon';
import './HoverTips.css';

interface CharacterStatHoverCardProps {
    character: any;
}

export const CharacterStatHoverCard: React.FC<CharacterStatHoverCardProps> = ({ character }) => {
    if (!character) return <div>No character info</div>;

    const name = character.name || character.character_name || 'Adventurer';
    const race = character.race || 'Human';
    const charClass = character.char_class || character.class || 'Fighter';
    const level = character.level || 1;
    const currentHp = character.current_hp ?? 10;
    const maxHp = character.max_hp ?? 10;
    const ac = character.stats?.armor_class || character.stats?.ac || character.armor_class || 14;
    const speed = character.stats?.speed || 30;

    const stats = character.stats || {};
    const str = stats.strength ?? 10;
    const dex = stats.dexterity ?? 10;
    const con = stats.constitution ?? 10;
    const int = stats.intelligence ?? 10;
    const wis = stats.wisdom ?? 10;
    const cha = stats.charisma ?? 10;

    const getMod = (val: number) => {
        const mod = Math.floor((val - 10) / 2);
        return mod >= 0 ? `+${mod}` : `${mod}`;
    };

    const hpPercent = Math.max(0, Math.min(100, Math.round((currentHp / maxHp) * 100)));

    return (
        <div className="hover-tip-card character-hover-tip">
            <div className="hover-tip-header">
                {character.image_url && !character.image_url.endsWith('.svg') ? (
                    <img src={character.image_url} alt={name} className="hover-tip-avatar" />
                ) : (
                    <div className="hover-tip-avatar-placeholder">
                        <VectorIcon name="shield" />
                    </div>
                )}
                <div className="hover-tip-title-box">
                    <h4 className="hover-tip-name">{name}</h4>
                    <span className="hover-tip-sub">Level {level} {race} {charClass}</span>
                </div>
            </div>

            {/* Health & AC row */}
            <div className="hover-tip-vital-row">
                <div className="hover-vital-box hp-box">
                    <div className="hover-vital-label">
                        <span>HP</span>
                        <span>{currentHp}/{maxHp}</span>
                    </div>
                    <div className="hover-hp-track">
                        <div
                            className="hover-hp-fill"
                            style={{
                                width: `${hpPercent}%`,
                                backgroundColor: hpPercent > 50 ? 'var(--color-guave)' : hpPercent > 20 ? 'var(--color-deep-peach)' : 'var(--color-maroon)'
                            }}
                        />
                    </div>
                </div>

                <div className="hover-vital-box badge-box">
                    <span className="vital-badge-val">{ac}</span>
                    <span className="vital-badge-lbl">AC</span>
                </div>

                <div className="hover-vital-box badge-box">
                    <span className="vital-badge-val">{speed}ft</span>
                    <span className="vital-badge-lbl">SPD</span>
                </div>
            </div>

            {/* Ability Scores */}
            <div className="hover-stats-grid">
                <div className="hover-stat-cell">
                    <span className="stat-name">STR</span>
                    <span className="stat-val">{str}</span>
                    <span className="stat-mod">{getMod(str)}</span>
                </div>
                <div className="hover-stat-cell">
                    <span className="stat-name">DEX</span>
                    <span className="stat-val">{dex}</span>
                    <span className="stat-mod">{getMod(dex)}</span>
                </div>
                <div className="hover-stat-cell">
                    <span className="stat-name">CON</span>
                    <span className="stat-val">{con}</span>
                    <span className="stat-mod">{getMod(con)}</span>
                </div>
                <div className="hover-stat-cell">
                    <span className="stat-name">INT</span>
                    <span className="stat-val">{int}</span>
                    <span className="stat-mod">{getMod(int)}</span>
                </div>
                <div className="hover-stat-cell">
                    <span className="stat-name">WIS</span>
                    <span className="stat-val">{wis}</span>
                    <span className="stat-mod">{getMod(wis)}</span>
                </div>
                <div className="hover-stat-cell">
                    <span className="stat-name">CHA</span>
                    <span className="stat-val">{cha}</span>
                    <span className="stat-mod">{getMod(cha)}</span>
                </div>
            </div>
        </div>
    );
};

interface SpellHoverCardProps {
    spell: any;
}

export const SpellHoverCard: React.FC<SpellHoverCardProps> = ({ spell }) => {
    const spellName = typeof spell === 'string' ? spell : spell.name || 'Arcane Incantation';
    const school = spell.school || 'Evocation';
    const level = spell.level === 0 ? 'Cantrip' : `Level ${spell.level || 1}`;
    const range = spell.range || '60 feet';
    const castingTime = spell.casting_time || '1 action';
    const duration = spell.duration || 'Instantaneous';
    const damage = spell.damage || spell.damage_dice || '1d8 radiant';
    const desc = spell.description || 'Channel weave energy toward your chosen target.';

    return (
        <div className="hover-tip-card spell-hover-tip">
            <div className="hover-tip-header">
                <span className="hover-glyph arcane-glyph"><VectorIcon name="rune" /></span>
                <div>
                    <h4 className="hover-tip-name">{spellName}</h4>
                    <span className="hover-tip-sub">{level} • {school}</span>
                </div>
            </div>

            <div className="hover-meta-grid">
                <div className="meta-item"><span className="meta-lbl">Cast Time:</span> {castingTime}</div>
                <div className="meta-item"><span className="meta-lbl">Range:</span> {range}</div>
                <div className="meta-item"><span className="meta-lbl">Duration:</span> {duration}</div>
                <div className="meta-item"><span className="meta-lbl">Damage:</span> <span className="meta-val-accent">{damage}</span></div>
            </div>

            <p className="hover-tip-desc">{desc}</p>
        </div>
    );
};

interface ItemHoverCardProps {
    item: any;
}

export const ItemHoverCard: React.FC<ItemHoverCardProps> = ({ item }) => {
    const itemName = typeof item === 'string' ? item : item.name || 'Relic';
    const itemType = item.item_type || item.type || 'Equipment';
    const quantity = item.quantity || 1;
    const weight = item.weight ? `${item.weight} lbs` : '1 lb';
    const desc = item.description || 'A trusty adventuring possession kept ready in your pack.';

    return (
        <div className="hover-tip-card item-hover-tip">
            <div className="hover-tip-header">
                <span className="hover-glyph item-glyph"><VectorIcon name="sword" /></span>
                <div>
                    <h4 className="hover-tip-name">{itemName}</h4>
                    <span className="hover-tip-sub">{itemType} • Qty: {quantity}</span>
                </div>
            </div>

            <div className="hover-meta-grid">
                <div className="meta-item"><span className="meta-lbl">Weight:</span> {weight}</div>
                <div className="meta-item"><span className="meta-lbl">Status:</span> Carried in Gear</div>
            </div>

            <p className="hover-tip-desc">{desc}</p>
        </div>
    );
};
