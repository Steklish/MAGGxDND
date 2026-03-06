import React from 'react';
import { useGameStore } from '../store/gameStore';
import './SceneViewer.css';

export const SceneViewer: React.FC = () => {
    const { currentScene, session } = useGameStore();

    if (!currentScene) {
        return (
            <div className="scene-viewer">
                <div className="no-scene">
                    <p>No scene loaded</p>
                    <p className="hint">Waiting for game master to initialize...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="scene-viewer">
            <div className="scene-header">
                <h3>{currentScene.name}</h3>
                {currentScene.description && (
                    <p className="scene-description">{currentScene.description}</p>
                )}
            </div>
            <div className="scene-content">
                <div className="grid-container">
                    <div className="grid">
                        {Array(20).fill(null).map((_, y) => (
                            <div key={y} className="grid-row">
                                {Array(20).fill(null).map((_, x) => (
                                    <div key={x} className="grid-cell" title={`Cell ${x},${y}`}>·</div>
                                ))}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};
