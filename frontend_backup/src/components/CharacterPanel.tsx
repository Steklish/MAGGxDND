import React, { useState } from 'react';
import { useGameStore } from '../store/gameStore';
import './CharacterPanel.css';

export const CharacterPanel: React.FC = () => {
    const { activeCharacter, session, currentSession, setActiveCharacter, sendAction } = useGameStore();
    const [activeTab, setActiveTab] = useState<'sheet' | 'party' | 'inventory' | 'spells'>('sheet');
    const [transferTarget, setTransferTarget] = useState<string>('');
    const [selectedItemForTransfer, setSelectedItemForTransfer] = useState<any | null>(null);

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

    const handleAbilityRoll = (statName: string, score: number) => {
        if (!activeCharacter) return;
        const mod = getModifier(score);
        sendAction(`I roll a ${statName} check (${mod}).`, activeCharacter);
    };

    const handleEquipItem = (item: any) => {
        if (!activeCharacter) return;
        const itemName = item.name || item;
        const actionVerb = item.is_equipped ? 'unequip' : 'equip';
        sendAction(`I ${actionVerb} ${itemName}.`, activeCharacter);
    };

    const handleDropItem = (item: any) => {
        if (!activeCharacter) return;
        const itemName = item.name || item;
        sendAction(`I drop ${itemName} onto the ground.`, activeCharacter);
    };

    const handleTransferItem = () => {
        if (!activeCharacter || !selectedItemForTransfer || !transferTarget) return;
        const itemName = selectedItemForTransfer.name || selectedItemForTransfer;
        sendAction(`I transfer ${itemName} to ${transferTarget}.`, activeCharacter);
        setSelectedItemForTransfer(null);
        setTransferTarget('');
    };

    const handleCastAbility = (ability: any) => {
        if (!activeCharacter) return;
        const name = ability.name || ability;
        sendAction(`I use ${name}.`, activeCharacter);
    };

    if (!activeCharacter) {
        return (
            <div className="ergonomic-character-panel empty">
                <div className="char-empty-box">
                    <span className="empty-avatar">🛡️</span>
                    <h3>No Active Hero Selected</h3>
                    <p>Select a character from the party list to view their character sheet.</p>
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

    return (
        <div className="ergonomic-character-panel">
            {/* Sheet Tabs */}
            <div className="char-tabs-bar">
                <button
                    type="button"
                    className={`char-tab-btn ${activeTab === 'sheet' ? 'active' : ''}`}
                    onClick={() => setActiveTab('sheet')}
                >
                    👤 Hero
                </button>
                <button
                    type="button"
                    className={`char-tab-btn ${activeTab === 'inventory' ? 'active' : ''}`}
                    onClick={() => setActiveTab('inventory')}
                >
                    🎒 Items ({inventoryList.length})
                </button>
                <button
                    type="button"
                    className={`char-tab-btn ${activeTab === 'spells' ? 'active' : ''}`}
                    onClick={() => setActiveTab('spells')}
                >
                    ✨ Spells ({abilitiesList.length})
                </button>
                <button
                    type="button"
                    className={`char-tab-btn ${activeTab === 'party' ? 'active' : ''}`}
                    onClick={() => setActiveTab('party')}
                >
                    👥 Party ({players.length + npcs.length})
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
                                <span className="badge-icon">🛡️</span>
                                <span className="badge-value">{activeCharacter.armor_class ?? 10}</span>
                                <span className="badge-label">AC</span>
                            </div>
                            <div className="stat-badge spd-badge" title="Movement Speed">
                                <span className="badge-icon">👟</span>
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
                                    <span key={idx} className="condition-pill">⚡ {cond}</span>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* TAB: Inventory */}
            {activeTab === 'inventory' && (
                <div className="char-tab-content">
                    <div className="inventory-header-row">
                        <span className="section-title">Carried Items ({inventoryList.length})</span>
                    </div>

                    {inventoryList.length === 0 ? (
                        <div className="tab-empty-msg">
                            <p>Inventory is currently empty.</p>
                        </div>
                    ) : (
                        <div className="inventory-cards-list">
                            {inventoryList.map((item: any, idx: number) => {
                                const name = typeof item === 'string' ? item : item.name;
                                const isEquipped = typeof item === 'object' && item.is_equipped;
                                const itemType = typeof item === 'object' ? item.type || 'item' : 'item';
                                return (
                                    <div key={idx} className={`inventory-item-card ${isEquipped ? 'equipped' : ''}`}>
                                        <div className="item-icon-col">
                                            {typeof item === 'object' && item.image_url ? (
                                                <img
                                                    src={item.image_url}
                                                    alt={name}
                                                    className="item-card-img"
                                                    onError={(e) => {
                                                        (e.currentTarget as HTMLElement).style.display = 'none';
                                                    }}
                                                />
                                            ) : (
                                                <span>{isEquipped ? '⚔️' : '📦'}</span>
                                            )}
                                        </div>
                                        <div className="item-info-col">
                                            <div className="item-name-row">
                                                <span className="item-name">{name}</span>
                                                {isEquipped && <span className="equipped-chip">EQUIPPED</span>}
                                            </div>
                                            <span className="item-type-text">{itemType}</span>
                                        </div>
                                        <div className="item-actions-col">
                                            <button
                                                type="button"
                                                className="item-btn equip-btn"
                                                onClick={() => handleEquipItem(item)}
                                                title={isEquipped ? 'Unequip' : 'Equip'}
                                            >
                                                {isEquipped ? 'Unequip' : 'Equip'}
                                            </button>
                                            <button
                                                type="button"
                                                className="item-btn drop-btn"
                                                onClick={() => handleDropItem(item)}
                                                title="Drop to scene"
                                            >
                                                Drop
                                            </button>
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
                    <span className="section-title">Spells & Feats ({abilitiesList.length})</span>
                    {abilitiesList.length === 0 ? (
                        <div className="tab-empty-msg">
                            <p>No active spells or special abilities registered.</p>
                        </div>
                    ) : (
                        <div className="spells-cards-list">
                            {abilitiesList.map((ab: any, idx: number) => {
                                const name = typeof ab === 'string' ? ab : ab.name;
                                const desc = typeof ab === 'object' ? ab.short_summary || ab.description || '' : '';
                                const type = typeof ab === 'object' ? ab.type || 'action' : 'action';
                                return (
                                    <div key={idx} className="spell-item-card">
                                        <div className="spell-header-row">
                                            <span className="spell-name">✨ {name}</span>
                                            <span className="spell-type-tag">{type}</span>
                                        </div>
                                        {desc && <p className="spell-desc">{desc}</p>}
                                        <button
                                            type="button"
                                            className="cast-ability-btn"
                                            onClick={() => handleCastAbility(ab)}
                                        >
                                            ⚡ Cast / Trigger
                                        </button>
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
