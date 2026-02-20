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
    const [headerHeight, setHeaderHeight] = useState(80);
    const [isResizingLeft, setIsResizingLeft] = useState(false);
    const [isResizingRight, setIsResizingRight] = useState(false);
    const [isResizingHeader, setIsResizingHeader] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);
    const startX = useRef(0);
    const startY = useRef(0);
    const startLeftWidth = useRef(0);
    const startRightWidth = useRef(0);
    const startHeaderHeight = useRef(0);
    const containerWidth = useRef(0);

    const handleMouseMove = useCallback((e: MouseEvent) => {
        if (!isResizingLeft && !isResizingRight && !isResizingHeader) return;
        if (!containerRef.current) return;

        const container = containerRef.current;
        const containerRect = container.getBoundingClientRect();

        if (isResizingHeader) {
            const deltaY = e.clientY - startY.current;
            const newHeight = startHeaderHeight.current + deltaY;
            setHeaderHeight(Math.max(60, Math.min(200, newHeight)));
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
    }, [isResizingLeft, isResizingRight, isResizingHeader]);

    const handleMouseUp = useCallback(() => {
        setIsResizingLeft(false);
        setIsResizingRight(false);
        setIsResizingHeader(false);
    }, []);

    useEffect(() => {
        if (isResizingLeft || isResizingRight || isResizingHeader) {
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
            return () => {
                document.removeEventListener('mousemove', handleMouseMove);
                document.removeEventListener('mouseup', handleMouseUp);
            };
        }
    }, [isResizingLeft, isResizingRight, isResizingHeader, handleMouseMove, handleMouseUp]);

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

    if (!session) {
        return <div className="loading">Loading game...</div>;
    }

    // Get current turn character
    const getCurrentTurnCharacter = () => {
        if (!session.turn_queue || session.turn_queue.length === 0) return null;
        const sortedQueue = [...session.turn_queue].sort((a, b) => a[2] - b[2]);
        return sortedQueue[0]?.[0];
    };

    const currentTurnChar = getCurrentTurnCharacter();

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
                <div className="header-center">
                    {currentTurnChar && (
                        <div className="current-turn-indicator">
                            <span className="turn-label">Current Turn:</span>
                            <span className="turn-character">{currentTurnChar.name}</span>
                        </div>
                    )}
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
