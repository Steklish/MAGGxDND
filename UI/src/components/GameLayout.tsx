import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useGameStore } from '../store/gameStore';
import { ChatPanel } from './ChatPanel';
import { SceneViewer } from './SceneViewer';
import { CharacterPanel } from './CharacterPanel';
import { ActionPanel } from './ActionPanel';
import { Footer } from './Footer';
import './GameLayout.css';

interface TurnEntry {
    character: any;
    type: 'player' | 'npc' | 'ally' | 'hostile' | 'neutral';
    initiative: number;
    isDead: boolean;
    isDying: boolean;
    deathSaveSuccesses: number;
    deathSaveFailures: number;
}

export const GameLayout: React.FC = () => {
    const { session, currentScene, activeCharacter } = useGameStore();
    const [leftPanelWidth, setLeftPanelWidth] = useState(25);
    const [rightPanelWidth, setRightPanelWidth] = useState(25);
    const [headerHeight, setHeaderHeight] = useState(140);
    const [actionPanelHeight, setActionPanelHeight] = useState(30);
    const [isActionPanelCollapsed, setIsActionPanelCollapsed] = useState(false);
    const [isCollapsing, setIsCollapsing] = useState(false);
    const [isResizingLeft, setIsResizingLeft] = useState(false);
    const [isResizingRight, setIsResizingRight] = useState(false);
    const [isResizingHeader, setIsResizingHeader] = useState(false);
    const [isResizingActionPanel, setIsResizingActionPanel] = useState(false);
    const [turnQueue, setTurnQueue] = useState<TurnEntry[]>([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [dyingCharacters, setDyingCharacters] = useState<string[]>([]);
    const containerRef = useRef<HTMLDivElement>(null);
    const startX = useRef(0);
    const startY = useRef(0);
    const startLeftWidth = useRef(0);
    const startRightWidth = useRef(0);
    const startHeaderHeight = useRef(0);
    const startActionPanelHeight = useRef(0);
    const prevActionPanelHeight = useRef(30);
    const containerWidth = useRef(0);
    const containerHeight = useRef(0);

    // Initialize turn queue from session
    useEffect(() => {
        if (!session) return;

        const queue: TurnEntry[] = [];

        // Add players
        session.players.forEach(p => {
            const char = p.character;
            queue.push({
                character: char,
                type: 'player',
                initiative: char.initiative_bonus || 10,
                isDead: char.current_hp <= 0 && char.is_alive === false,
                isDying: char.current_hp <= 0 && char.is_alive !== false,
                deathSaveSuccesses: 0,
                deathSaveFailures: 0
            });
        });

        // Add NPCs
        session.npcs.forEach(n => {
            const char = n.character;
            // Determine NPC attitude based on context (for now, default to hostile)
            let type: 'hostile' | 'neutral' | 'ally' = 'hostile';
            if (char.alignment?.includes('Good')) type = 'ally';
            else if (char.alignment?.includes('Neutral')) type = 'neutral';

            queue.push({
                character: char,
                type,
                initiative: char.initiative_bonus || 10,
                isDead: char.current_hp <= 0 && char.is_alive === false,
                isDying: char.current_hp <= 0 && char.is_alive !== false,
                deathSaveSuccesses: 0,
                deathSaveFailures: 0
            });
        });

        // Sort by initiative (descending)
        queue.sort((a, b) => b.initiative - a.initiative);
        setTurnQueue(queue);
        setCurrentIndex(0);
    }, [session]);

    // Get alive queue (filter out dead, keep dying for death saves)
    const getAliveQueue = useCallback(() => {
        return turnQueue.filter(entry => !entry.isDead);
    }, [turnQueue]);

    const aliveQueue = getAliveQueue();
    const currentTurnChar = aliveQueue[currentIndex % aliveQueue.length];

    // Handle character death animation
    const handleDeathAnimation = useCallback((characterName: string) => {
        setDyingCharacters(prev => [...prev, characterName]);
        setTimeout(() => {
            setDyingCharacters(prev => prev.filter(name => name !== characterName));
        }, 1000);
    }, []);

    // Handle death save for dying characters
    const performDeathSave = useCallback((characterName: string) => {
        // In a real implementation, this would roll a d20
        const roll = Math.floor(Math.random() * 20) + 1;
        console.log(`${characterName} death save roll: ${roll}`);
        // Update death save counters based on roll
        // 10+ = success, <10 = failure
        // 1 = 2 failures, 20 = automatic success
    }, []);

    // Advance turn
    const advanceTurn = useCallback(() => {
        if (aliveQueue.length === 0) return;

        const currentChar = aliveQueue[currentIndex % aliveQueue.length];

        // Check if current character is dying - perform death save
        if (currentChar?.isDying) {
            performDeathSave(currentChar.character.name);
        }

        // Move to next character
        setCurrentIndex(prev => (prev + 1) % aliveQueue.length);
    }, [aliveQueue, currentIndex, performDeathSave]);

    const handleMouseMove = useCallback((e: MouseEvent) => {
        if (!isResizingLeft && !isResizingRight && !isResizingHeader && !isResizingActionPanel) return;
        if (!containerRef.current) return;

        const container = containerRef.current;
        const containerRect = container.getBoundingClientRect();

        if (isResizingHeader) {
            const deltaY = e.clientY - startY.current;
            const newHeight = startHeaderHeight.current + deltaY;
            // Min height 70px for mini mode, max = portrait + name + death saves + padding
            setHeaderHeight(Math.max(70, Math.min(240, newHeight)));
        } else if (isResizingActionPanel) {
            const deltaY = e.clientY - startY.current;
            const deltaPercent = (deltaY / containerRect.height) * 100;
            const newHeight = startActionPanelHeight.current + deltaPercent;
            const clampedHeight = Math.max(15, Math.min(60, newHeight));
            setActionPanelHeight(clampedHeight);
            if (clampedHeight > 15) {
                setIsActionPanelCollapsed(false);
            }
        } else {
            const deltaX = e.clientX - startX.current;
            const deltaPercent = (deltaX / containerWidth.current) * 100;

            if (isResizingLeft) {
                const newWidth = startLeftWidth.current + deltaPercent;
                setLeftPanelWidth(Math.max(15, Math.min(50, newWidth)));
            }

            if (isResizingRight) {
                const newWidth = startRightWidth.current - deltaPercent;
                setRightPanelWidth(Math.max(15, Math.min(50, newWidth)));
            }
        }
    }, [isResizingLeft, isResizingRight, isResizingHeader, isResizingActionPanel]);

    const handleMouseUp = useCallback(() => {
        setIsResizingLeft(false);
        setIsResizingRight(false);
        setIsResizingHeader(false);
        setIsResizingActionPanel(false);
    }, []);

    useEffect(() => {
        if (isResizingLeft || isResizingRight || isResizingHeader || isResizingActionPanel) {
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
            return () => {
                document.removeEventListener('mousemove', handleMouseMove);
                document.removeEventListener('mouseup', handleMouseUp);
            };
        }
    }, [isResizingLeft, isResizingRight, isResizingHeader, isResizingActionPanel, handleMouseMove, handleMouseUp]);

    const startLeftResize = (e: React.MouseEvent) => {
        e.preventDefault();
        setIsResizingLeft(true);
        startX.current = e.clientX;
        startLeftWidth.current = leftPanelWidth;
        if (containerRef.current) {
            containerWidth.current = containerRef.current.getBoundingClientRect().width;
        }
    };

    const startRightResize = (e: React.MouseEvent) => {
        e.preventDefault();
        setIsResizingRight(true);
        startX.current = e.clientX;
        startRightWidth.current = rightPanelWidth;
        if (containerRef.current) {
            containerWidth.current = containerRef.current.getBoundingClientRect().width;
        }
    };

    const startHeaderResize = (e: React.MouseEvent) => {
        e.preventDefault();
        setIsResizingHeader(true);
        startY.current = e.clientY;
        startHeaderHeight.current = headerHeight;
    };

    const startActionPanelResize = (e: React.MouseEvent) => {
        e.preventDefault();
        setIsResizingActionPanel(true);
        startY.current = e.clientY;
        startActionPanelHeight.current = isActionPanelCollapsed ? prevActionPanelHeight.current : actionPanelHeight;
        if (containerRef.current) {
            containerHeight.current = containerRef.current.getBoundingClientRect().height;
        }
    };

    const toggleActionPanel = () => {
        setIsCollapsing(true);
        if (isActionPanelCollapsed) {
            setActionPanelHeight(prevActionPanelHeight.current);
            setIsActionPanelCollapsed(false);
            setTimeout(() => setIsCollapsing(false), 300);
        } else {
            prevActionPanelHeight.current = actionPanelHeight;
            setActionPanelHeight(0);
            setIsActionPanelCollapsed(true);
            setTimeout(() => setIsCollapsing(false), 300);
        }
    };

    if (!session) {
        return <div className="loading">Loading game...</div>;
    }

    const getAttitudeColor = (type: string) => {
        switch (type) {
            case 'player': return 'var(--accent-purple)';
            case 'ally': return 'var(--accent-green)';
            case 'neutral': return 'var(--accent-yellow)';
            case 'hostile': return 'var(--accent-orange)';
            default: return 'var(--text-muted)';
        }
    };

    return (
        <div className="game-layout" ref={containerRef}>
            {/* Header */}
            <header className="game-header" style={{ height: `${headerHeight}px` }}>
                <div className="header-left">
                    <h1 className="game-title">
                        <span className="title-magg">MAGG</span>
                        <span className="title-x">x</span>
                        <span className="title-dnd">DND</span>
                    </h1>
                </div>

                {/* Turn Queue with Portraits */}
                <div className="header-center turn-queue-container">
                    {aliveQueue.map((entry, idx) => {
                        const isCurrentTurn = idx === (currentIndex % aliveQueue.length);
                        const isDying = entry.isDying;

                        return (
                            <div
                                key={`${entry.character.name}-${entry.initiative}`}
                                className={`turn-portrait ${isCurrentTurn ? 'active' : ''} ${isDying ? 'dying' : ''} ${dyingCharacters.includes(entry.character.name) ? 'death-animation' : ''}`}
                                style={{
                                    borderColor: getAttitudeColor(entry.type),
                                    opacity: isCurrentTurn ? 1 : 0.4
                                }}
                            >
                                <div className="portrait-frame">
                                    {/* Portrait placeholder - will be loaded later */}
                                    <div className="portrait-placeholder">
                                        <span className="portrait-initial">
                                            {entry.character.name?.[0] || '?'}
                                        </span>
                                    </div>
                                    {/* Attitude indicator */}
                                    <div
                                        className="attitude-indicator"
                                        style={{ backgroundColor: getAttitudeColor(entry.type) }}
                                    />
                                </div>

                                {/* Character name below portrait */}
                                <div className="portrait-name">
                                    {entry.character.name}
                                </div>

                                {/* Death save counters */}
                                {isDying && (
                                    <div className="death-saves">
                                        <div className="death-save-successes">
                                            {'✓'.repeat(entry.deathSaveSuccesses)}
                                        </div>
                                        <div className="death-save-failures">
                                            {'✗'.repeat(entry.deathSaveFailures)}
                                        </div>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>

                <div className="header-right">
                    <button className="profile-btn" title="Profile">
                        <span className="profile-icon">👤</span>
                    </button>
                </div>

                {/* Header resize handle */}
                <div
                    className="header-resize-handle"
                    onMouseDown={startHeaderResize}
                />
            </header>

            {/* Main content */}
            <div className="game-content">
                {/* Left Panel - Characters */}
                <aside
                    className="left-panel"
                    style={{ width: `${leftPanelWidth}%` }}
                >
                    <CharacterPanel />
                </aside>

                {/* Left resize handle */}
                <div
                    className={`resize-handle left-resize ${isResizingLeft ? 'resizing' : ''}`}
                    onMouseDown={startLeftResize}
                />

                {/* Center - Action and Scene */}
                <main className="center-panel">
                    <div className={`action-panel-container ${isCollapsing ? 'collapsing' : ''}`} style={{ flex: `1 1 ${isActionPanelCollapsed ? 100 : 100 - actionPanelHeight}%` }}>
                        <ActionPanel />
                    </div>
                    {!isActionPanelCollapsed && (
                        <>
                            <div
                                className={`resize-handle action-panel-resize ${isResizingActionPanel ? 'resizing' : ''}`}
                                onMouseDown={startActionPanelResize}
                            >
                                <button
                                    className="action-panel-toggle-btn"
                                    onClick={toggleActionPanel}
                                    title="Collapse scene view"
                                />
                            </div>
                            <div className={`scene-container ${isCollapsing ? 'collapsing' : ''}`} style={{ flex: `0 0 ${actionPanelHeight}%` }}>
                                <SceneViewer />
                            </div>
                        </>
                    )}
                    {isActionPanelCollapsed && (
                        <div className="action-panel-collapsed-handle" style={{ display: 'flex' }} onClick={toggleActionPanel} />
                    )}
                </main>

                {/* Right resize handle */}
                <div
                    className={`resize-handle right-resize ${isResizingRight ? 'resizing' : ''}`}
                    onMouseDown={startRightResize}
                />

                {/* Right Panel - Chat */}
                <aside
                    className="right-panel"
                    style={{ width: `${rightPanelWidth}%` }}
                >
                    <ChatPanel />
                </aside>
            </div>

            {/* Footer */}
            <Footer />
        </div>
    );
};
