import React, { useState } from 'react';
import './DiceRoller.css';

export interface DiceRollResult {
    id: string;
    diceType: string;
    count: number;
    modifier: number;
    rolls: number[];
    total: number;
    advantageType?: 'normal' | 'advantage' | 'disadvantage';
    droppedRoll?: number;
    label?: string;
    timestamp: string;
}

interface DiceRollerProps {
    onRollResult?: (result: DiceRollResult) => void;
    onInsertToAction?: (text: string) => void;
    onClose?: () => void;
}

const STANDARD_DICE = [
    { type: 'd4', sides: 4, icon: '▲', color: '#f59e0b' },
    { type: 'd6', sides: 6, icon: '⚅', color: '#10b981' },
    { type: 'd8', sides: 8, icon: '◆', color: '#3b82f6' },
    { type: 'd10', sides: 10, icon: '✦', color: '#8b5cf6' },
    { type: 'd12', sides: 12, icon: '⬡', color: '#ec4899' },
    { type: 'd20', sides: 20, icon: '🎲', color: '#ef4444' },
    { type: 'd100', sides: 100, icon: '💯', color: '#06b6d4' },
];

export const DiceRoller: React.FC<DiceRollerProps> = ({ onRollResult, onInsertToAction, onClose }) => {
    const [selectedDice, setSelectedDice] = useState<number>(20); // d20 default
    const [diceCount, setDiceCount] = useState<number>(1);
    const [modifier, setModifier] = useState<number>(0);
    const [advantageType, setAdvantageType] = useState<'normal' | 'advantage' | 'disadvantage'>('normal');
    const [rollLabel, setRollLabel] = useState<string>('');
    const [lastResult, setLastResult] = useState<DiceRollResult | null>(null);
    const [rollHistory, setRollHistory] = useState<DiceRollResult[]>([]);
    const [isRolling, setIsRolling] = useState<boolean>(false);

    const rollSingleDie = (sides: number) => {
        return Math.floor(Math.random() * sides) + 1;
    };

    const handleRoll = (customSides?: number, customCount?: number, customMod?: number, customAdv?: 'normal' | 'advantage' | 'disadvantage', customLabel?: string) => {
        setIsRolling(true);
        const sides = customSides ?? selectedDice;
        const count = customCount ?? diceCount;
        const mod = customMod ?? modifier;
        const adv = customAdv ?? advantageType;
        const label = customLabel ?? rollLabel;

        setTimeout(() => {
            let rolls: number[] = [];
            let total = 0;
            let droppedRoll: number | undefined = undefined;

            if (sides === 20 && adv !== 'normal') {
                const r1 = rollSingleDie(20);
                const r2 = rollSingleDie(20);
                if (adv === 'advantage') {
                    rolls = [Math.max(r1, r2)];
                    droppedRoll = Math.min(r1, r2);
                } else {
                    rolls = [Math.min(r1, r2)];
                    droppedRoll = Math.max(r1, r2);
                }
                total = rolls[0] + mod;
            } else {
                for (let i = 0; i < count; i++) {
                    const r = rollSingleDie(sides);
                    rolls.push(r);
                }
                total = rolls.reduce((sum, val) => sum + val, 0) + mod;
            }

            const now = new Date();
            const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;

            const result: DiceRollResult = {
                id: `roll-${Date.now()}`,
                diceType: `d${sides}`,
                count: sides === 20 && adv !== 'normal' ? 2 : count,
                modifier: mod,
                rolls,
                total,
                advantageType: sides === 20 ? adv : 'normal',
                droppedRoll,
                label: label.trim() || undefined,
                timestamp: timeStr,
            };

            setLastResult(result);
            setRollHistory(prev => [result, ...prev.slice(0, 9)]);
            setIsRolling(false);

            if (onRollResult) {
                onRollResult(result);
            }
        }, 300);
    };

    const handleQuickPreset = (presetName: string, sides: number, count: number, mod: number, adv: 'normal' | 'advantage' | 'disadvantage' = 'normal') => {
        setRollLabel(presetName);
        handleRoll(sides, count, mod, adv, presetName);
    };

    const formatRollForAction = (res: DiceRollResult) => {
        const modStr = res.modifier !== 0 ? (res.modifier > 0 ? `+${res.modifier}` : `${res.modifier}`) : '';
        const advStr = res.advantageType && res.advantageType !== 'normal' ? ` (${res.advantageType})` : '';
        const labelStr = res.label ? `[${res.label}] ` : '';
        return `${labelStr}Rolled ${res.diceType}${advStr}${modStr}: Total ${res.total} (rolls: [${res.rolls.join(', ')}]${res.droppedRoll !== undefined ? `, dropped: ${res.droppedRoll}` : ''})`;
    };

    return (
        <div className="dice-roller-panel">
            <div className="dice-roller-header">
                <div className="dice-header-title">
                    <span className="dice-icon">🎲</span>
                    <h3>Interactive Dice Tray</h3>
                </div>
                {onClose && (
                    <button className="dice-close-btn" onClick={onClose} title="Close Dice Tray">
                        ✕
                    </button>
                )}
            </div>

            {/* Quick Preset Buttons */}
            <div className="dice-presets-bar">
                <span className="preset-label">Presets:</span>
                <button
                    className="preset-btn"
                    onClick={() => handleQuickPreset('Initiative', 20, 1, 0)}
                    title="Roll Initiative (d20)"
                >
                    ⚡ Initiative
                </button>
                <button
                    className="preset-btn"
                    onClick={() => handleQuickPreset('Attack (Adv)', 20, 1, 0, 'advantage')}
                    title="Attack with Advantage"
                >
                    ⚔️ Adv Attack
                </button>
                <button
                    className="preset-btn"
                    onClick={() => handleQuickPreset('Death Save', 20, 1, 0)}
                    title="Death Saving Throw"
                >
                    💀 Death Save
                </button>
                <button
                    className="preset-btn"
                    onClick={() => handleQuickPreset('Perception', 20, 1, 0)}
                    title="Perception Check"
                >
                    👁️ Perception
                </button>
            </div>

            {/* Dice Selector Chips */}
            <div className="dice-types-selector">
                {STANDARD_DICE.map(dice => (
                    <button
                        key={dice.type}
                        className={`dice-chip ${selectedDice === dice.sides ? 'selected' : ''}`}
                        onClick={() => setSelectedDice(dice.sides)}
                        style={{ '--dice-color': dice.color } as React.CSSProperties}
                    >
                        <span className="dice-glyph">{dice.icon}</span>
                        <span className="dice-type-name">{dice.type}</span>
                    </button>
                ))}
            </div>

            {/* Dice Controls */}
            <div className="dice-controls-grid">
                <div className="control-group">
                    <label>Count</label>
                    <div className="counter-controls">
                        <button
                            type="button"
                            onClick={() => setDiceCount(Math.max(1, diceCount - 1))}
                            disabled={diceCount <= 1}
                        >
                            -
                        </button>
                        <span>{diceCount}</span>
                        <button
                            type="button"
                            onClick={() => setDiceCount(Math.min(20, diceCount + 1))}
                            disabled={diceCount >= 20}
                        >
                            +
                        </button>
                    </div>
                </div>

                <div className="control-group">
                    <label>Modifier</label>
                    <div className="counter-controls">
                        <button
                            type="button"
                            onClick={() => setModifier(modifier - 1)}
                        >
                            -
                        </button>
                        <span>{modifier >= 0 ? `+${modifier}` : modifier}</span>
                        <button
                            type="button"
                            onClick={() => setModifier(modifier + 1)}
                        >
                            +
                        </button>
                    </div>
                </div>

                {selectedDice === 20 && (
                    <div className="control-group advantage-group">
                        <label>Roll Mode</label>
                        <div className="advantage-toggle">
                            <button
                                type="button"
                                className={`adv-btn ${advantageType === 'disadvantage' ? 'active disadv' : ''}`}
                                onClick={() => setAdvantageType(advantageType === 'disadvantage' ? 'normal' : 'disadvantage')}
                                title="Disadvantage (take lower roll)"
                            >
                                Disadv
                            </button>
                            <button
                                type="button"
                                className={`adv-btn ${advantageType === 'normal' ? 'active' : ''}`}
                                onClick={() => setAdvantageType('normal')}
                            >
                                Norm
                            </button>
                            <button
                                type="button"
                                className={`adv-btn ${advantageType === 'advantage' ? 'active adv' : ''}`}
                                onClick={() => setAdvantageType(advantageType === 'advantage' ? 'normal' : 'advantage')}
                                title="Advantage (take higher roll)"
                            >
                                Adv
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Roll Purpose Label */}
            <div className="roll-label-input-container">
                <input
                    type="text"
                    className="roll-label-input"
                    placeholder="Purpose / Reason (e.g. Longsword Attack, Fireball, Stealth)..."
                    value={rollLabel}
                    onChange={(e) => setRollLabel(e.target.value)}
                />
            </div>

            {/* Main Action Roll Button */}
            <button
                type="button"
                className={`main-roll-btn ${isRolling ? 'rolling' : ''}`}
                onClick={() => handleRoll()}
                disabled={isRolling}
            >
                {isRolling ? 'Rolling...' : `Roll ${diceCount}d${selectedDice}${modifier !== 0 ? (modifier > 0 ? `+${modifier}` : modifier) : ''}`}
            </button>

            {/* Result Display */}
            {lastResult && (
                <div className="dice-result-card">
                    <div className="result-header">
                        <span className="result-tag">{lastResult.label || lastResult.diceType}</span>
                        <span className="result-timestamp">{lastResult.timestamp}</span>
                    </div>

                    <div className="result-big-display">
                        <span className="result-total">{lastResult.total}</span>
                        <div className="result-breakdown">
                            <span className="breakdown-formula">
                                [{lastResult.rolls.join(', ')}]
                                {lastResult.droppedRoll !== undefined && (
                                    <span className="dropped-roll" title="Dropped roll">
                                        {' '}(dropped {lastResult.droppedRoll})
                                    </span>
                                )}
                                {lastResult.modifier !== 0 && (
                                    <span> {lastResult.modifier > 0 ? `+ ${lastResult.modifier}` : `- ${Math.abs(lastResult.modifier)}`}</span>
                                )}
                            </span>
                            {lastResult.diceType === 'd20' && lastResult.rolls[0] === 20 && (
                                <span className="crit-badge success">NATURAL 20!</span>
                            )}
                            {lastResult.diceType === 'd20' && lastResult.rolls[0] === 1 && (
                                <span className="crit-badge fail">NATURAL 1!</span>
                            )}
                        </div>
                    </div>

                    {onInsertToAction && (
                        <div className="result-actions">
                            <button
                                type="button"
                                className="insert-action-btn"
                                onClick={() => onInsertToAction(formatRollForAction(lastResult))}
                            >
                                📋 Insert into Action Input
                            </button>
                        </div>
                    )}
                </div>
            )}

            {/* Recent Roll History */}
            {rollHistory.length > 1 && (
                <div className="roll-history-section">
                    <span className="history-title">Recent Rolls</span>
                    <div className="history-list">
                        {rollHistory.slice(1, 4).map(item => (
                            <div key={item.id} className="history-item">
                                <span className="history-label">{item.label || item.diceType}</span>
                                <span className="history-total">{item.total}</span>
                                <span className="history-rolls">[{item.rolls.join(',')}]</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};
