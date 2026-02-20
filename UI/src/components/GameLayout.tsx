import React, { useState } from 'react';
import { useGameStore } from '../store/gameStore';
import { ChatPanel } from './ChatPanel';
import { SceneViewer } from './SceneViewer';
import { CharacterPanel } from './CharacterPanel';
import { ActionPanel } from './ActionPanel';
import { TurnQueue } from './TurnQueue';
import './GameLayout.css';

export const GameLayout: React.FC = () => {
    const { session, currentScene, activeCharacter } = useGameStore();
    const [leftPanelCollapsed, setLeftPanelCollapsed] = useState(false);
    const [rightPanelCollapsed, setRightPanelCollapsed] = useState(false);

    if (!session) {
        return <div className="loading">Loading game...</div>;
    }

    return (
        <div className="game-layout">
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
                    className={`left-panel ${leftPanelCollapsed ? 'collapsed' : ''}`}
                >
                    <CharacterPanel 
                        collapsed={leftPanelCollapsed} 
                        onToggle={() => setLeftPanelCollapsed(!leftPanelCollapsed)} 
                    />
                </aside>

                {/* Center - Scene and Action */}
                <main className="center-panel">
                    <SceneViewer />
                    <ActionPanel />
                </main>

                {/* Right Panel - Chat */}
                <aside
                    className={`right-panel ${rightPanelCollapsed ? 'collapsed' : ''}`}
                >
                    <ChatPanel 
                        collapsed={rightPanelCollapsed} 
                        onToggle={() => setRightPanelCollapsed(!rightPanelCollapsed)} 
                    />
                </aside>
            </div>
        </div>
    );
};
