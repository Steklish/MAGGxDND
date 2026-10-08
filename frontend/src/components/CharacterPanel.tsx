import React, { useState } from 'react';
import { useGameStore } from '../store/gameStore';
import { VectorIcon } from './common/VectorIcon';
import { resolveItemDetails, resolveSpellDetails, EnrichedItem, EnrichedSpell } from '../utils/dndCatalog';
import { useTranslation } from '../i18n/useTranslation';
import './CharacterPanel.css';

export const CharacterPanel: React.FC = () => {
    const { activeCharacter, session, currentSession, setActiveCharacter, sendAction } = useGameStore();
    const { t, language } = useTranslation();
    const [activeTab, setActiveTab] = useState<'sheet' | 'party' | 'inventory' | 'spells'>('sheet');
    const [transferTarget, setTransferTarget] = useState<string>('');
    const [selectedItemForTransfer, setSelectedItemForTransfer] = useState<any | null>(null);

    // Filtering and expansion state
    const [itemFilter, setItemFilter] = useState<'all' | 'weapon' | 'armor' | 'potion' | 'gear'>('all');
    const [spellFilter, setSpellFilter] = useState<'all' | 'cantrip' | 'leveled' | 'feat'>('all');
    const [expandedItemKey, setExpandedItemKey] = useState<string | null>(null);
    const [expandedSpellKey, setExpandedSpellKey] = useState<string | null>(null);
    const [actionFeedback, setActionFeedback] = useState<string | null>(null);

    const activeSession = currentSession || session;
    const players = activeSession?.players || [];
    const npcs = activeSession?.npcs || [];

    const stats = activeCharacter?.stats || {
        strength: 10,
        dexterity: 10,
        constitution: 10,
        intelligence: 10,
        wisdom: 10,
        charisma: 10,
    };

    const getModifier = (score: number) => {
        const mod = Math.floor((score - 10) / 2);
        return mod >= 0 ? `+${mod}` : `${mod}`;
    };

    const showFeedback = (msg: string) => {
        setActionFeedback(msg);
        setTimeout(() => setActionFeedback(null), 3000);
    };

    const handleAbilityRoll = (statName: string, score: number) => {
        if (!activeCharacter) return;
        const mod = getModifier(score);
        sendAction(`I roll a ${statName} check (${mod}).`, activeCharacter);
        showFeedback(`Rolled ${statName} check (${mod})`);
    };

    const handleEquipItem = (_item: any, enriched: EnrichedItem) => {
        if (!activeCharacter) return;
        const itemName = enriched.name;
        const actionVerb = enriched.isEquipped ? 'unequip' : 'equip';
        sendAction(`I ${actionVerb} ${itemName}.`, activeCharacter);
        showFeedback(`${actionVerb === 'equip' ? 'Equipped' : 'Unequipped'} ${itemName}`);
    };

    const handleUseItem = (_item: any, enriched: EnrichedItem) => {
        if (!activeCharacter) return;
        const itemName = enriched.name;
        if (enriched.category === 'potion') {
            sendAction(`I drink ${itemName} and regain vitality! (${enriched.usageEffect || 'restores HP'})`, activeCharacter);
            showFeedback(`Drank ${itemName}!`);
        } else if (enriched.category === 'gear') {
            sendAction(`I unpack and use my ${itemName}.`, activeCharacter);
            showFeedback(`Used ${itemName}!`);
        } else {
            sendAction(`I use ${itemName}.`, activeCharacter);
            showFeedback(`Used ${itemName}!`);
        }
    };

    const handleAttackWithItem = (_item: any, enriched: EnrichedItem) => {
        if (!activeCharacter) return;
        const itemName = enriched.name;
        const dmg = enriched.damageDice ? ` (${enriched.damageDice} ${enriched.damageType || ''})` : '';
        sendAction(`I make an attack with my ${itemName}${dmg}!`, activeCharacter);
        showFeedback(`Attacked with ${itemName}!`);
    };

    const handleInspectItem = (_item: any, enriched: EnrichedItem) => {
        if (!activeCharacter) return;
        sendAction(`I examine ${enriched.name} to check its craftsmanship and state.`, activeCharacter);
        showFeedback(`Inspected ${enriched.name}`);
    };

    const handleDropItem = (_item: any, enriched: EnrichedItem) => {
        if (!activeCharacter) return;
        const itemName = enriched.name;
        sendAction(`I drop ${itemName} onto the ground.`, activeCharacter);
        showFeedback(`Dropped ${itemName} to ground`);
    };

    const handleTransferItem = () => {
        if (!activeCharacter || !selectedItemForTransfer || !transferTarget) return;
        const itemName = selectedItemForTransfer.name || selectedItemForTransfer;
        sendAction(`I transfer ${itemName} to ${transferTarget}.`, activeCharacter);
        showFeedback(`Transferred ${itemName} to ${transferTarget}`);
        setSelectedItemForTransfer(null);
        setTransferTarget('');
    };

    const handleCastSpell = (_ability: any, enriched: EnrichedSpell) => {
        if (!activeCharacter) return;
        const spellName = enriched.name;
        sendAction(`I cast ${spellName}!`, activeCharacter);
        showFeedback(`Cast ${spellName}!`);
    };

    const handleRollSpellEffect = (_ability: any, enriched: EnrichedSpell) => {
        if (!activeCharacter) return;
        const spellName = enriched.name;
        const dice = enriched.damageDice || enriched.healingDice || 'd20';
        sendAction(`I roll the spell effect for ${spellName} (${dice})!`, activeCharacter);
        showFeedback(`Rolled ${dice} for ${spellName}!`);
    };

    if (!activeCharacter) {
        return (
            <div className="ergonomic-character-panel empty">
                <div className="char-empty-box">
                    <span className="empty-avatar"><VectorIcon name="shield" size="3rem" /></span>
                    <h3>{language === 'ru' ? 'Герой не выбран' : 'No Active Hero Selected'}</h3>
                    <p>{t.character.selectHeroPrompt}</p>
                </div>
            </div>
        );
    }

    const currentHP = activeCharacter.current_hp ?? 10;
    const maxHP = activeCharacter.max_hp ?? 10;
    const hpRatio = Math.max(0, Math.min(1, currentHP / maxHP));
    const hpPercent = Math.round(hpRatio * 100);

    const inventoryList = activeCharacter.inventory || [];
    const abilitiesList = activeCharacter.abilities || [];

    // Filter items
    const filteredItems = inventoryList.filter((item: any) => {
        if (itemFilter === 'all') return true;
        const details = resolveItemDetails(item);
        if (itemFilter === 'weapon') return details.category === 'weapon';
        if (itemFilter === 'armor') return details.category === 'armor' || details.category === 'shield';
        if (itemFilter === 'potion') return details.category === 'potion';
        if (itemFilter === 'gear') return details.category === 'gear' || details.category === 'container' || details.category === 'misc';
        return true;
    });

    // Filter spells
    const filteredSpells = abilitiesList.filter((ab: any) => {
        if (spellFilter === 'all') return true;
        const details = resolveSpellDetails(ab);
        if (spellFilter === 'cantrip') return details.level === 0 && details.actionType !== 'Special';
        if (spellFilter === 'leveled') return details.level > 0;
        if (spellFilter === 'feat') return details.actionType === 'Special' || details.actionType === 'Passive' || details.level === 0;
        return true;
    });

    return (
        <div className="ergonomic-character-panel">
            {/* Action Feedback Banner */}
            {actionFeedback && (
                <div className="action-feedback-toast" role="status">
                    <span className="feedback-sparkle">✨</span> {actionFeedback}
                </div>
            )}

            {/* Sheet Tabs */}
            <div className="char-tabs-bar">
                <button
                    type="button"
                    className={`char-tab-btn ${activeTab === 'sheet' ? 'active' : ''}`}
                    onClick={() => setActiveTab('sheet')}
                >
                    <VectorIcon name="knight" /> {t.character.heroTab}
                </button>
                <button
                    type="button"
                    className={`char-tab-btn ${activeTab === 'inventory' ? 'active' : ''}`}
                    onClick={() => setActiveTab('inventory')}
                >
                    <VectorIcon name="potion" /> {t.character.itemsTab} ({inventoryList.length})
                </button>
                <button
                    type="button"
                    className={`char-tab-btn ${activeTab === 'spells' ? 'active' : ''}`}
                    onClick={() => setActiveTab('spells')}
                >
                    <VectorIcon name="magic" /> {t.character.abilitiesTab} ({abilitiesList.length})
                </button>
                <button
                    type="button"
                    className={`char-tab-btn ${activeTab === 'party' ? 'active' : ''}`}
                    onClick={() => setActiveTab('party')}
                >
                    <VectorIcon name="knight" /> {t.character.partyTab} ({players.length + npcs.length})
                </button>
            </div>

            {/* TAB: Hero Sheet Overview */}
            {activeTab === 'sheet' && (
                <div className="char-tab-content">
                    {/* Hero Header */}
                    <div className="hero-identity-card">
                        <div className="hero-avatar">
                            {activeCharacter.image_url ? (
                                <img
                                    src={activeCharacter.image_url}
                                    alt={activeCharacter.name}
                                    className="hero-avatar-img"
                                    onError={(e) => {
                                        (e.currentTarget as HTMLElement).style.display = 'none';
                                    }}
                                />
                            ) : (
                                <span>{activeCharacter.name?.charAt(0).toUpperCase()}</span>
                            )}
                        </div>
                        <div className="hero-meta">
                            <h3 className="hero-name">{activeCharacter.name}</h3>
                            <span className="hero-subtext">
                                Level {activeCharacter.level || 1} {activeCharacter.race || 'Human'} {activeCharacter.char_class || 'Adventurer'}
                            </span>
                            {(activeCharacter as any).alignment && (
                                <span className="hero-alignment-tag">{(activeCharacter as any).alignment}</span>
                            )}
                        </div>
                    </div>

                    {/* Vitals Bar */}
                    <div className="hero-vitals-strip">
                        <div className="vital-box hp-vital-box">
                            <div className="hp-header">
                                <span className="vital-label">Hit Points</span>
                                <span className="hp-numbers">{currentHP} / {maxHP}</span>
                            </div>
                            <div className="vital-bar-track">
                                <div
                                    className="vital-bar-fill"
                                    style={{
                                        width: `${hpPercent}%`,
                                        background: hpPercent > 50 ? '#10b981' : hpPercent > 20 ? '#f59e0b' : '#ef4444'
                                    }}
                                />
                            </div>
                        </div>

                        <div className="stat-badges-row">
                            <div className="stat-badge ac-badge" title="Armor Class">
                                <span className="badge-icon"><VectorIcon name="shield" /></span>
                                <span className="badge-value">{activeCharacter.armor_class ?? 10}</span>
                                <span className="badge-label">AC</span>
                            </div>
                            <div className="stat-badge spd-badge" title="Movement Speed">
                                <span className="badge-icon"><VectorIcon name="horse" /></span>
                                <span className="badge-value">{activeCharacter.speed ?? 30}ft</span>
                                <span className="badge-label">Speed</span>
                            </div>
                            <div className="stat-badge prof-badge" title="Proficiency Bonus">
                                <span className="badge-icon">★</span>
                                <span className="badge-value">+{(activeCharacter as any).proficiency_bonus ?? 2}</span>
                                <span className="badge-label">Prof</span>
                            </div>
                        </div>
                    </div>

                    {/* Ability Scores Grid */}
                    <div className="abilities-section">
                        <div className="section-title-row">
                            <span className="section-title">Ability Scores</span>
                            <span className="section-hint">Click modifier to roll check</span>
                        </div>

                        <div className="abilities-grid">
                            {[
                                { key: 'STR', name: 'Strength', val: stats.strength },
                                { key: 'DEX', name: 'Dexterity', val: stats.dexterity },
                                { key: 'CON', name: 'Constitution', val: stats.constitution },
                                { key: 'INT', name: 'Intelligence', val: stats.intelligence },
                                { key: 'WIS', name: 'Wisdom', val: stats.wisdom },
                                { key: 'CHA', name: 'Charisma', val: stats.charisma },
                            ].map(stat => {
                                const mod = getModifier(stat.val);
                                return (
                                    <div
                                        key={stat.key}
                                        className="ability-card"
                                        onClick={() => handleAbilityRoll(stat.name, stat.val)}
                                        title={`Roll ${stat.name} Check (${mod})`}
                                    >
                                        <span className="ability-key">{stat.key}</span>
                                        <span className="ability-modifier">{mod}</span>
                                        <span className="ability-score">{stat.val}</span>
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                    {/* Conditions */}
                    {(activeCharacter as any).active_conditions_list && (activeCharacter as any).active_conditions_list.length > 0 && (
                        <div className="conditions-section">
                            <span className="section-title">Active Conditions</span>
                            <div className="conditions-tags">
                                {(activeCharacter as any).active_conditions_list.map((cond: string, idx: number) => (
                                    <span key={idx} className="condition-pill"><VectorIcon name="horse" /> {cond}</span>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* TAB: Inventory */}
            {activeTab === 'inventory' && (
                <div className="char-tab-content">
                    {/* Filter Pills Bar */}
                    <div className="codex-filter-pills-bar">
                        <button
                            type="button"
                            className={`codex-filter-pill ${itemFilter === 'all' ? 'active' : ''}`}
                            onClick={() => setItemFilter('all')}
                        >
                            All ({inventoryList.length})
                        </button>
                        <button
                            type="button"
                            className={`codex-filter-pill ${itemFilter === 'weapon' ? 'active' : ''}`}
                            onClick={() => setItemFilter('weapon')}
                        >
                            ⚔️ Weapons
                        </button>
                        <button
                            type="button"
                            className={`codex-filter-pill ${itemFilter === 'armor' ? 'active' : ''}`}
                            onClick={() => setItemFilter('armor')}
                        >
                            🛡️ Armor
                        </button>
                        <button
                            type="button"
                            className={`codex-filter-pill ${itemFilter === 'potion' ? 'active' : ''}`}
                            onClick={() => setItemFilter('potion')}
                        >
                            🧪 Potions
                        </button>
                        <button
                            type="button"
                            className={`codex-filter-pill ${itemFilter === 'gear' ? 'active' : ''}`}
                            onClick={() => setItemFilter('gear')}
                        >
                            🎒 Gear
                        </button>
                    </div>

                    {filteredItems.length === 0 ? (
                        <div className="tab-empty-msg">
                            <p>No items found in this category.</p>
                        </div>
                    ) : (
                        <div className="inventory-cards-list">
                            {filteredItems.map((item: any, idx: number) => {
                                const enriched = resolveItemDetails(item);
                                const isExpanded = expandedItemKey === `${enriched.name}-${idx}`;

                                return (
                                    <div
                                        key={`item-${idx}`}
                                        className={`inventory-item-card ${enriched.isEquipped ? 'equipped' : ''} category-${enriched.category}`}
                                    >
                                        {/* Main Card Header / Summary Row */}
                                        <div className="item-card-main-row">
                                            {/* Item Icon Box */}
                                            <div
                                                className={`item-icon-box category-${enriched.category}`}
                                                onClick={() => setExpandedItemKey(isExpanded ? null : `${enriched.name}-${idx}`)}
                                                title="Click to view full item lore and details"
                                            >
                                                {typeof item === 'object' && item.image_url ? (
                                                    <img
                                                        src={item.image_url}
                                                        alt={enriched.name}
                                                        className="item-card-img"
                                                        onError={(e) => {
                                                            (e.currentTarget as HTMLElement).style.display = 'none';
                                                        }}
                                                    />
                                                ) : (
                                                    <VectorIcon name={enriched.iconName} />
                                                )}
                                            </div>

                                            {/* Item Info Body */}
                                            <div
                                                className="item-info-col"
                                                onClick={() => setExpandedItemKey(isExpanded ? null : `${enriched.name}-${idx}`)}
                                                style={{ cursor: 'pointer' }}
                                                title="Click to toggle item dossier"
                                            >
                                                <div className="item-name-row">
                                                    <span className="item-name">{enriched.name}</span>
                                                    {enriched.quantity > 1 && (
                                                        <span className="item-qty-badge">×{enriched.quantity}</span>
                                                    )}
                                                    {enriched.isEquipped && (
                                                        <span className="equipped-chip">EQUIPPED</span>
                                                    )}
                                                </div>

                                                <div className="item-category-subrow">
                                                    <span className={`item-category-tag tag-${enriched.category}`}>
                                                        {enriched.categoryLabel}
                                                    </span>
                                                    {enriched.rarity && enriched.rarity !== 'common' && (
                                                        <span className={`item-rarity-tag rarity-${enriched.rarity}`}>
                                                            {enriched.rarityLabel}
                                                        </span>
                                                    )}
                                                </div>

                                                {/* Combat Badges Row */}
                                                <div className="item-combat-stats-row">
                                                    {enriched.damageDice && (
                                                        <span className="combat-stat-chip chip-damage">
                                                            ⚔️ {enriched.damageDice} {enriched.damageType || ''}
                                                        </span>
                                                    )}
                                                    {enriched.acBonus && (
                                                        <span className="combat-stat-chip chip-defense">
                                                            🛡️ {enriched.acBonus}
                                                        </span>
                                                    )}
                                                    {enriched.usageEffect && (
                                                        <span className="combat-stat-chip chip-effect">
                                                            ✨ {enriched.usageEffect}
                                                        </span>
                                                    )}
                                                    {enriched.weight && (
                                                        <span className="combat-stat-chip chip-weight">
                                                            ⚖️ {enriched.weight}
                                                        </span>
                                                    )}
                                                    {enriched.cost && (
                                                        <span className="combat-stat-chip chip-cost">
                                                            🪙 {enriched.cost}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>

                                            {/* Interactive Action Buttons */}
                                            <div className="item-actions-col">
                                                {/* Primary Contextual Action */}
                                                {enriched.canUse && (
                                                    <button
                                                        type="button"
                                                        className="item-btn primary-use-btn"
                                                        onClick={() => handleUseItem(item, enriched)}
                                                        title={`Use ${enriched.name}`}
                                                    >
                                                        {enriched.category === 'potion' ? '🧪 Drink' : 'Use'}
                                                    </button>
                                                )}

                                                {enriched.canAttack && enriched.isEquipped && (
                                                    <button
                                                        type="button"
                                                        className="item-btn attack-btn"
                                                        onClick={() => handleAttackWithItem(item, enriched)}
                                                        title={`Attack with ${enriched.name}`}
                                                    >
                                                        ⚔️ Attack
                                                    </button>
                                                )}

                                                {enriched.canEquip && (
                                                    <button
                                                        type="button"
                                                        className={`item-btn equip-btn ${enriched.isEquipped ? 'active-equip' : ''}`}
                                                        onClick={() => handleEquipItem(item, enriched)}
                                                        title={enriched.isEquipped ? 'Unequip' : 'Equip'}
                                                    >
                                                        {enriched.isEquipped ? 'Unequip' : 'Equip'}
                                                    </button>
                                                )}

                                                {/* Dossier Toggle Button */}
                                                <button
                                                    type="button"
                                                    className={`item-btn info-btn ${isExpanded ? 'active' : ''}`}
                                                    onClick={() => setExpandedItemKey(isExpanded ? null : `${enriched.name}-${idx}`)}
                                                    title={isExpanded ? 'Collapse info' : 'View full details'}
                                                >
                                                    {isExpanded ? '▲ Info' : '📜 Info'}
                                                </button>

                                                {/* Drop to Ground */}
                                                <button
                                                    type="button"
                                                    className="item-btn drop-btn"
                                                    onClick={() => handleDropItem(item, enriched)}
                                                    title="Drop onto the ground"
                                                >
                                                    Drop
                                                </button>

                                                {/* Transfer to Ally */}
                                                <button
                                                    type="button"
                                                    className="item-btn transfer-btn"
                                                    onClick={() => setSelectedItemForTransfer(item)}
                                                    title="Transfer to ally"
                                                >
                                                    Give
                                                </button>
                                            </div>
                                        </div>

                                        {/* Expandable Item Lore & Rules Dossier */}
                                        {isExpanded && (
                                            <div className="item-expanded-dossier">
                                                <div className="dossier-divider" />
                                                <p className="item-dossier-desc">{enriched.description}</p>

                                                {enriched.properties && enriched.properties.length > 0 && (
                                                    <div className="item-dossier-properties">
                                                        <span className="properties-label">Properties:</span>
                                                        <div className="properties-tags-list">
                                                            {enriched.properties.map((prop, pIdx) => (
                                                                <span key={pIdx} className="property-tag">{prop}</span>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}

                                                <div className="item-dossier-quick-bar">
                                                    <button
                                                        type="button"
                                                        className="dossier-action-btn inspect-btn"
                                                        onClick={() => handleInspectItem(item, enriched)}
                                                    >
                                                        🔍 Inspect with Perception
                                                    </button>
                                                    {enriched.canAttack && (
                                                        <button
                                                            type="button"
                                                            className="dossier-action-btn attack-shortcut-btn"
                                                            onClick={() => handleAttackWithItem(item, enriched)}
                                                        >
                                                            ⚔️ Attack Roll
                                                        </button>
                                                    )}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    {/* Transfer Modal / Banner */}
                    {selectedItemForTransfer && (
                        <div className="transfer-box-banner">
                            <span className="transfer-title">
                                Give <strong>{selectedItemForTransfer.name || selectedItemForTransfer}</strong> to:
                            </span>
                            <div className="transfer-inputs">
                                <select
                                    value={transferTarget}
                                    onChange={(e) => setTransferTarget(e.target.value)}
                                    className="transfer-select"
                                >
                                    <option value="">Select party member...</option>
                                    {players
                                        .map(p => p.character?.name || p.name)
                                        .filter(n => n && n !== activeCharacter.name)
                                        .map((name, i) => (
                                            <option key={i} value={name}>{name}</option>
                                        ))
                                    }
                                </select>
                                <button
                                    type="button"
                                    className="confirm-transfer-btn"
                                    onClick={handleTransferItem}
                                    disabled={!transferTarget}
                                >
                                    Transfer
                                </button>
                                <button
                                    type="button"
                                    className="cancel-transfer-btn"
                                    onClick={() => setSelectedItemForTransfer(null)}
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* TAB: Spells & Abilities */}
            {activeTab === 'spells' && (
                <div className="char-tab-content">
                    {/* Spell Filter Pills */}
                    <div className="codex-filter-pills-bar">
                        <button
                            type="button"
                            className={`codex-filter-pill ${spellFilter === 'all' ? 'active' : ''}`}
                            onClick={() => setSpellFilter('all')}
                        >
                            All ({abilitiesList.length})
                        </button>
                        <button
                            type="button"
                            className={`codex-filter-pill ${spellFilter === 'cantrip' ? 'active' : ''}`}
                            onClick={() => setSpellFilter('cantrip')}
                        >
                            ✨ Cantrips
                        </button>
                        <button
                            type="button"
                            className={`codex-filter-pill ${spellFilter === 'leveled' ? 'active' : ''}`}
                            onClick={() => setSpellFilter('leveled')}
                        >
                            🔮 Spells
                        </button>
                        <button
                            type="button"
                            className={`codex-filter-pill ${spellFilter === 'feat' ? 'active' : ''}`}
                            onClick={() => setSpellFilter('feat')}
                        >
                            ⚡ Feats
                        </button>
                    </div>

                    {filteredSpells.length === 0 ? (
                        <div className="tab-empty-msg">
                            <p>No spells or special abilities registered in this category.</p>
                        </div>
                    ) : (
                        <div className="spells-cards-list">
                            {filteredSpells.map((ab: any, idx: number) => {
                                const enriched = resolveSpellDetails(ab);
                                const isExpanded = expandedSpellKey === `${enriched.name}-${idx}`;

                                return (
                                    <div key={`spell-${idx}`} className="spell-item-card">
                                        {/* Spell Top Header */}
                                        <div className="spell-card-main-row">
                                            <div
                                                className="spell-icon-box"
                                                onClick={() => setExpandedSpellKey(isExpanded ? null : `${enriched.name}-${idx}`)}
                                                title="Toggle Spell Dossier"
                                            >
                                                <VectorIcon name="magic" />
                                                <span className="spell-level-corner">{enriched.level}</span>
                                            </div>

                                            <div
                                                className="spell-info-col"
                                                onClick={() => setExpandedSpellKey(isExpanded ? null : `${enriched.name}-${idx}`)}
                                                style={{ cursor: 'pointer' }}
                                                title="Click to view full spell mechanics"
                                            >
                                                <div className="spell-title-row">
                                                    <span className="spell-name">{enriched.name}</span>
                                                    <span className="spell-level-badge">{enriched.levelLabel}</span>
                                                    <span className="spell-school-tag">{enriched.school}</span>
                                                </div>

                                                {/* Parameters Row */}
                                                <div className="spell-parameters-strip">
                                                    <span className="spell-param-chip chip-action">
                                                        ⚡ {enriched.castingTime}
                                                    </span>
                                                    <span className="spell-param-chip chip-range">
                                                        📏 {enriched.range}
                                                    </span>
                                                    <span className="spell-param-chip chip-duration">
                                                        ⏱️ {enriched.duration}
                                                    </span>
                                                    {enriched.components && (
                                                        <span className="spell-param-chip chip-comp">
                                                            🗣️ {enriched.components}
                                                        </span>
                                                    )}
                                                    {enriched.damageDice && (
                                                        <span className="spell-param-chip chip-dmg">
                                                            💥 {enriched.damageDice} {enriched.damageType || ''}
                                                        </span>
                                                    )}
                                                    {enriched.healingDice && (
                                                        <span className="spell-param-chip chip-heal">
                                                            💚 {enriched.healingDice}
                                                        </span>
                                                    )}
                                                    {enriched.saveDC && (
                                                        <span className="spell-param-chip chip-save">
                                                            🎯 {enriched.saveDC}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>

                                            {/* Spell Interactive Actions */}
                                            <div className="spell-actions-col">
                                                <button
                                                    type="button"
                                                    className="cast-ability-btn"
                                                    onClick={() => handleCastSpell(ab, enriched)}
                                                    title={`Cast ${enriched.name}`}
                                                >
                                                    ✨ Cast
                                                </button>

                                                {(enriched.damageDice || enriched.healingDice) && (
                                                    <button
                                                        type="button"
                                                        className="roll-spell-effect-btn"
                                                        onClick={() => handleRollSpellEffect(ab, enriched)}
                                                        title="Roll damage or healing dice"
                                                    >
                                                        🎲 Roll
                                                    </button>
                                                )}

                                                <button
                                                    type="button"
                                                    className={`spell-info-toggle-btn ${isExpanded ? 'active' : ''}`}
                                                    onClick={() => setExpandedSpellKey(isExpanded ? null : `${enriched.name}-${idx}`)}
                                                    title="Toggle full spell details"
                                                >
                                                    {isExpanded ? '▲' : '📜'}
                                                </button>
                                            </div>
                                        </div>

                                        {/* Expandable Spell Description & Rules Drawer */}
                                        {isExpanded && (
                                            <div className="spell-expanded-dossier">
                                                <div className="dossier-divider" />
                                                <p className="spell-full-desc">{enriched.description}</p>

                                                {enriched.tags && enriched.tags.length > 0 && (
                                                    <div className="spell-tags-row">
                                                        {enriched.tags.map((tag, tIdx) => (
                                                            <span key={tIdx} className="spell-keyword-tag">#{tag}</span>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            )}

            {/* TAB: Party Overview */}
            {activeTab === 'party' && (
                <div className="char-tab-content">
                    <span className="section-title">Party & Allies ({players.length + npcs.length})</span>
                    <div className="party-cards-list">
                        {players.map((p, idx) => {
                            const char = p.character || p;
                            const isMe = char.name === activeCharacter.name;
                            return (
                                <div
                                    key={`party-${idx}`}
                                    className={`party-char-card ${isMe ? 'selected-me' : ''}`}
                                    onClick={() => setActiveCharacter(char)}
                                >
                                    <div className="party-avatar">
                                        {char.image_url ? (
                                            <img
                                                src={char.image_url}
                                                alt={char.name}
                                                className="party-avatar-img"
                                                onError={(e) => {
                                                    (e.currentTarget as HTMLElement).style.display = 'none';
                                                }}
                                            />
                                        ) : (
                                            <span>{char.name?.charAt(0).toUpperCase()}</span>
                                        )}
                                    </div>
                                    <div className="party-info">
                                        <div className="party-name-row">
                                            <span className="party-char-name">{char.name}</span>
                                            {isMe && <span className="you-chip">YOU</span>}
                                        </div>
                                        <span className="party-class">{char.race || ''} {char.char_class || 'Player'}</span>
                                        <div className="party-hp-mini">
                                            HP: {char.current_hp ?? 10} / {char.max_hp ?? 10}
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                        {npcs.map((npc, idx) => {
                            const char = npc.character || npc;
                            return (
                                <div
                                    key={`npc-${idx}`}
                                    className="party-char-card npc-card"
                                >
                                    <div className="party-avatar npc-avatar">
                                        {char.image_url ? (
                                            <img
                                                src={char.image_url}
                                                alt={char.name}
                                                className="party-avatar-img"
                                                onError={(e) => {
                                                    (e.currentTarget as HTMLElement).style.display = 'none';
                                                }}
                                            />
                                        ) : (
                                            <span>{char.name?.charAt(0).toUpperCase()}</span>
                                        )}
                                    </div>
                                    <div className="party-info">
                                        <div className="party-name-row">
                                            <span className="party-char-name">{char.name}</span>
                                            <span className="npc-chip">NPC</span>
                                        </div>
                                        <span className="party-class">{char.race || ''} {char.char_class || 'Peasant'}</span>
                                        <div className="party-hp-mini">
                                            HP: {char.current_hp ?? 10} / {char.max_hp ?? 10}
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
};
