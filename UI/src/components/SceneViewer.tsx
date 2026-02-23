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

    const getPlayers = () => {
        if (!session) return [];
        return session.players.map(p => p.character);
    };

    const getNPCs = () => {
        if (!session) return [];
        return session.npcs
            .filter(npc => npc.character.current_scene === session.current_location_name)
            .map(npc => npc.character);
    };

    const getObjects = () => {
        return currentScene.objects || [];
    };

    // Calculate grid positions (simplified 20x20 grid like in delivery.py)
    const gridSize = 20;
    const centerX = currentScene.center_position.x;
    const centerY = currentScene.center_position.y;
    const width = currentScene.dimensions.x;
    const height = currentScene.dimensions.y;

    const minX = centerX - width / 2;
    const maxX = centerX + width / 2;
    const minY = centerY - height / 2;
    const maxY = centerY + height / 2;

    const xScale = gridSize / width;
    const yScale = gridSize / height;

    const positionToGrid = (pos: { x: number; y: number }) => {
        const gridX = Math.floor((pos.x - minX) * xScale);
        const gridY = Math.floor((pos.y - minY) * yScale);
        return {
            x: Math.max(0, Math.min(gridSize - 1, gridX)),
            y: Math.max(0, Math.min(gridSize - 1, gridY))
        };
    };

    // Create grid
    const grid: Array<Array<{ type: 'empty' | 'player' | 'npc' | 'object'; symbol: string; color: string; name: string }>> = 
        Array(gridSize).fill(null).map(() => 
            Array(gridSize).fill(null).map(() => ({
                type: 'empty' as const,
                symbol: '.',
                color: 'var(--text-secondary)',
                name: ''
            }))
        );

    // Place players
    getPlayers().forEach(char => {
        const pos = positionToGrid(char.position);
        grid[pos.y][pos.x] = {
            type: 'player',
            symbol: char.name[0].toUpperCase(),
            color: 'var(--accent-blue)',
            name: char.name
        };
    });

    // Place NPCs
    getNPCs().forEach(char => {
        const pos = positionToGrid(char.position);
        grid[pos.y][pos.x] = {
            type: 'npc',
            symbol: char.name[0].toUpperCase(),
            color: 'var(--accent-red)',
            name: char.name
        };
    });

    // Place objects
    getObjects().forEach(obj => {
        if (obj.position) {
            const pos = positionToGrid(obj.position);
            grid[pos.y][pos.x] = {
                type: 'object',
                symbol: obj.name[0].toUpperCase(),
                color: 'var(--accent-yellow)',
                name: obj.name
            };
        }
    });

    return (
        <div className="scene-viewer">
            <div className="scene-content">
                <div className="grid-container">
                    <div className="grid">
                        {grid.map((row, y) => (
                            <div key={y} className="grid-row">
                                {row.map((cell, x) => (
                                    <div 
                                        key={x} 
                                        className="grid-cell"
                                        style={{ color: cell.color }}
                                        title={cell.name || 'Empty'}
                                    >
                                        {cell.symbol}
                                    </div>
                                ))}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};
