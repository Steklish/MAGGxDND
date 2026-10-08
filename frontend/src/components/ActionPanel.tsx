import React, { useState } from 'react';
import { useGameStore } from '../store/gameStore';
import { VectorIcon, IconName } from './common/VectorIcon';
import './ActionPanel.css';

interface ActionPreset {
    id: string;
    label: string;
    icon: IconName;
    actionText: string;
    type: 'action' | 'bonus' | 'movement' | 'utility';
    description: string;
}

const DEFAULT_PRESETS: ActionPreset[] = [
    {
        id: 'attack',
        label: 'Attack',
        icon: 'sword',
        actionText: 'I make a weapon attack against the nearest hostile target.',
        type: 'action',
        description: 'Make a melee or ranged attack against an enemy',
    },
    {
        id: 'dash',
        label: 'Dash',
        icon: 'horse',
        actionText: 'I take the Dash action to gain extra movement for this turn.',
        type: 'movement',
        description: 'Double your movement speed for the current turn',
    },
    {
        id: 'dodge',
        label: 'Dodge',
        icon: 'shield',
        actionText: 'I take the Dodge action, focusing entirely on evading incoming attacks.',
        type: 'action',
        description: 'Attack rolls against you have disadvantage until your next turn',
    },
    {
        id: 'hide',
        label: 'Hide',
        icon: 'helm',
        actionText: 'I attempt to hide behind available cover with a Dexterity (Stealth) check.',
        type: 'action',
        description: 'Make a Stealth check to become hidden from view',
    },
    {
        id: 'search',
        label: 'Search',
        icon: 'rune',
        actionText: 'I carefully search my surroundings with an Investigation / Perception check.',
        type: 'utility',
        description: 'Inspect the environment, find hidden doors or traps',
    },
    {
        id: 'help',
        label: 'Help Ally',
        icon: 'knight',
        actionText: 'I use the Help action to give advantage to my ally on their next check or attack.',
        type: 'action',
        description: 'Aid a friendly creature to grant them advantage',
    },
    {
        id: 'interact',
        label: 'Use Object',
        icon: 'gate',
        actionText: 'I interact with the nearest object or mechanism in the scene.',
        type: 'utility',
        description: 'Open a door, pull a lever, or interact with scene props',
    },
    {
        id: 'speak',
        label: 'Dialogue',
        icon: 'banner',
        actionText: 'I speak aloud: "',
        type: 'utility',
        description: 'Communicate with party members or NPCs',
    },
];

export const ActionPanel: React.FC = () => {
    const { activeCharacter, sendAction, isActionPending, clarificationText, isDMThinking } = useGameStore();
    const isResolving = isActionPending || isDMThinking;
    const [actionText, setActionText] = useState('');
    const [selectedCategory, setSelectedCategory] = useState<'all' | 'spells' | 'inventory'>('all');

    const handleSubmit = (e?: React.FormEvent) => {
        if (e) e.preventDefault();
        if (activeCharacter && actionText.trim() && !isResolving) {
            sendAction(actionText.trim(), activeCharacter);
            setActionText('');
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    const handlePresetClick = (preset: ActionPreset) => {
        if (preset.id === 'speak') {
            setActionText('I speak aloud: "');
        } else {
            setActionText(preset.actionText);
        }
    };

    const handleSpellClick = (spell: any) => {
        const spellName = spell.name || spell;
        setActionText(`I cast ${spellName} on the target.`);
    };

    const handleItemClick = (item: any) => {
        const itemName = item.name || item;
        setActionText(`I use ${itemName} from my inventory.`);
    };

    if (!activeCharacter) {
        return (
            <div className="action-deck-panel waiting-state">
                <div className="waiting-pill">
                    <span className="waiting-spinner-mini" />
                    <span>Awaiting player turn... The DM will signal when you may act.</span>
                </div>
            </div>
        );
    }

    const characterSpells = activeCharacter.abilities || [];
    const characterInventory = (activeCharacter.inventory || []).filter((i: any) => !i.is_equipped);

    return (
        <div className="action-deck-panel">
            {/* Top Bar: Action Categories & Dice Tray Toggle */}
            <div className="deck-header-bar">
                <div className="deck-tabs">
                    <button
                        type="button"
                        className={`deck-tab-btn ${selectedCategory === 'all' ? 'active' : ''}`}
                        onClick={() => setSelectedCategory('all')}
                    >
                        <VectorIcon name="sword" /> Standard Actions
                    </button>
                    {characterSpells.length > 0 && (
                        <button
                            type="button"
                            className={`deck-tab-btn ${selectedCategory === 'spells' ? 'active' : ''}`}
                            onClick={() => setSelectedCategory('spells')}
                        >
                            <VectorIcon name="magic" /> Spells & Abilities ({characterSpells.length})
                        </button>
                    )}
                    {characterInventory.length > 0 && (
                        <button
                            type="button"
                            className={`deck-tab-btn ${selectedCategory === 'inventory' ? 'active' : ''}`}
                            onClick={() => setSelectedCategory('inventory')}
                        >
                            <VectorIcon name="potion" /> Use Item ({characterInventory.length})
                        </button>
                    )}
                </div>
            </div>

            {/* Quick Action Dock */}
            {selectedCategory === 'all' && (
                <div className="action-hotbar-dock">
                    {DEFAULT_PRESETS.map(preset => (
                        <button
                            key={preset.id}
                            type="button"
                            className={`hotbar-action-chip ${preset.type}`}
                            onClick={() => handlePresetClick(preset)}
                            title={preset.description}
                            disabled={isActionPending}
                        >
                            <span className="chip-icon"><VectorIcon name={preset.icon} /></span>
                            <span className="chip-label">{preset.label}</span>
                        </button>
                    ))}
                </div>
            )}

            {/* Spells Quick Dock */}
            {selectedCategory === 'spells' && (
                <div className="action-hotbar-dock spells-dock">
                    {characterSpells.map((spell: any, idx: number) => {
                        const name = typeof spell === 'string' ? spell : spell.name;
                        return (
                            <button
                                key={`spell-${idx}`}
                                type="button"
                                className="hotbar-action-chip spell-chip"
                                onClick={() => handleSpellClick(spell)}
                                title={typeof spell === 'object' ? spell.short_summary || spell.description : `Cast ${name}`}
                                disabled={isResolving}
                            >
                                <span className="chip-icon"><VectorIcon name="magic" /></span>
                                <span className="chip-label">{name}</span>
                            </button>
                        );
                    })}
                </div>
            )}

            {/* Inventory Quick Dock */}
            {selectedCategory === 'inventory' && (
                <div className="action-hotbar-dock items-dock">
                    {characterInventory.map((item: any, idx: number) => {
                        const name = typeof item === 'string' ? item : item.name;
                        const iconUrl = typeof item === 'object' ? item.image_url : null;
                        return (
                            <button
                                key={`item-${idx}`}
                                type="button"
                                className="hotbar-action-chip item-chip"
                                onClick={() => handleItemClick(item)}
                                title={`Use ${name}`}
                                disabled={isResolving}
                            >
                                {iconUrl ? (
                                    <img
                                        src={iconUrl}
                                        alt={name}
                                        className="chip-icon-img"
                                        onError={(e) => {
                                            (e.currentTarget as HTMLElement).style.display = 'none';
                                        }}
                                    />
                                ) : (
                                    <span className="chip-icon"><VectorIcon name="potion" /></span>
                                )}
                                <span className="chip-label">{name}</span>
                            </button>
                        );
                    })}
                </div>
            )}

            {/* Clarification Box if Master requested clarification */}
            {clarificationText && (
                <div className="deck-clarification-banner">
                    <span className="banner-icon"><VectorIcon name="rune" /></span>
                    <div className="banner-body">
                        <strong>DM Clarification:</strong> {clarificationText}
                    </div>
                </div>
            )}

            {/* Input Form */}
            <form onSubmit={handleSubmit} className="deck-action-form">
                <div className="deck-input-container">
                    <textarea
                        className="deck-action-input"
                        value={actionText}
                        onChange={(e) => setActionText(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={`Describe what ${activeCharacter.name} does... (Enter to send, Shift+Enter for new line)`}
                        rows={2}
                        disabled={isResolving}
                    />

                    {isDMThinking && (
                        <div className="deck-dm-thinking-pill">
                            <span className="thinking-pulse" />
                            <span>Dungeon Master is calculating outcome...</span>
                        </div>
                    )}
                </div>

                <div className="deck-action-buttons">
                    <button
                        type="submit"
                        className="deck-submit-btn"
                        disabled={!actionText.trim() || isResolving}
                    >
                        {isResolving ? 'Resolving...' : <><VectorIcon name="sword" /> Act</>}
                    </button>

                    <button
                        type="button"
                        className="deck-skip-btn"
                        onClick={() => {
                            sendAction('I pass my turn.', activeCharacter);
                            setActionText('');
                        }}
                        disabled={isResolving}
                        title="Pass turn without taking an action"
                    >
                        Skip Turn
                    </button>
                </div>
            </form>
        </div>
    );
};
