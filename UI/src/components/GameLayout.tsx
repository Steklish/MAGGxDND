import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useGameStore } from '../store/gameStore';
import { ChatPanel } from './ChatPanel';
import { SceneViewer } from './SceneViewer';
import { CharacterPanel } from './CharacterPanel';
import { ActionPanel } from './ActionPanel';
import { TurnQueue } from './TurnQueue';
import './GameLayout.css';

export const GameLayout: React.FC = () => {
    const { session, currentScene, activeCharacter } = useGameStore();
    const [leftPanelWidth, setLeftPanelWidth] = useState(25);
    const [rightPanelWidth, setRightPanelWidth] = useState(25);
    const [isResizingLeft, setIsResizingLeft] = useState(false);
    const [isResizingRight, setIsResizingRight] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);
    const startX = useRef(0);
    const startLeftWidth = useRef(0);
    const startRightWidth = useRef(0);
    const containerWidth = useRef(0);

    const handleMouseMove = useCallback((e: MouseEvent) => {
        if (!isResizingLeft && !isResizingRight) return;
        if (!containerRef.current) return;

        const container = containerRef.current;
        const containerRect = container.getBoundingClientRect();
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
    }, [isResizingLeft, isResizingRight]);

    const handleMouseUp = useCallback(() => {
        setIsResizingLeft(false);
        setIsResizingRight(false);
    }, []);

    useEffect(() => {
        if (isResizingLeft || isResizingRight) {
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
            return () => {
                document.removeEventListener('mousemove', handleMouseMove);
                document.removeEventListener('mouseup', handleMouseUp);
            };
        }
    }, [isResizingLeft, isResizingRight, handleMouseMove, handleMouseUp]);

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

    if (!session) {
        return <div className="loading">Loading game...</div>;
    }

    return (
        <div className="game-layout" ref={containerRef}>
            {/* Header */}
            <header className="game-header">
                <div className="header-left">
                    <h1 className="game-title">MAGGxDND</h1>
                    {session.current_scene && (
                        <span className="scene-indicator">
                            📍 {session.current_scene.name}
                        </span>
                    )}
                </div>
                <div className="header-center">
                    <TurnQueue />
                </div>
                <div className="header-right">
                    <span className={`game-mode ${session.game_mode.toLowerCase()}`}>
                        {session.game_mode === 'COMBAT' ? '⚔️ COMBAT' : '📖 STORY'}
                    </span>
                </div>
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

                {/* Center - Scene and Action */}
                <main className="center-panel">
                    <SceneViewer />
                    <ActionPanel />
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
        </div>
    );
};
