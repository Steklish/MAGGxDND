import React from 'react';
import { useGameStore } from '../store/gameStore';
import './SceneViewer.css';

export const SceneViewer: React.FC = () => {
    const { currentScene, session } = useGameStore();

    console.log('🏰 SceneViewer render:', { currentScene });

    // Check for null, undefined, or invalid scene
    if (!currentScene || typeof currentScene !== 'object') {
        return (
            <div className="scene-viewer">
                <div className="no-scene">
                    <p>No scene loaded</p>
                    <p className="hint">Waiting for game master to initialize...</p>
                </div>
            </div>
        );
    }

    // Safely access nested properties with defaults
    const centerPos = currentScene.center_position || { x: 10, y: 10 };
    const dimensions = currentScene.dimensions || { x: 20, y: 20 };
    
    // Ensure x and y exist
    const centerX = typeof centerPos.x === 'number' ? centerPos.x : 10;
    const centerY = typeof centerPos.y === 'number' ? centerPos.y : 10;
    const dimX = typeof dimensions.x === 'number' ? dimensions.x : 20;
    const dimY = typeof dimensions.y === 'number' ? dimensions.y : 20;

    console.log('🏰 Scene dimensions:', { centerX, centerY, dimX, dimY });

    return (
        <div className="scene-viewer">
            <div className="scene-content">
                <div className="grid-container">
                    <div className="grid">
                        {Array(dimY).fill(null).map((_, y) => (
                            <div key={y} className="grid-row">
                                {Array(dimX).fill(null).map((_, x) => (
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
