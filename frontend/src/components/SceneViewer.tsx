import React from 'react';
import { useGameStore } from '../store/gameStore';
import './SceneViewer.css';

export const SceneViewer: React.FC = () => {
    const { currentScene, session, currentSession } = useGameStore();

    // Use currentSession as primary, session as fallback
    const activeSession = currentSession || session;

    console.log('🏰 SceneViewer render:', { currentScene, activeSession });

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
    const sceneName = currentScene.name || 'Unknown Location';
    const sceneDescription = currentScene.description || 'The scene is shrouded in mystery...';
    const centerPos = currentScene.center_position || { x: 10, y: 10 };
    const dimensions = currentScene.dimensions || { x: 20, y: 20 };

    // Ensure x and y exist
    const centerX = typeof centerPos.x === 'number' ? centerPos.x : 10;
    const centerY = typeof centerPos.y === 'number' ? centerPos.y : 10;
    const dimX = typeof dimensions.x === 'number' ? dimensions.x : 20;
    const dimY = typeof dimensions.y === 'number' ? dimensions.y : 20;

    console.log('🏰 Scene dimensions:', { centerX, centerY, dimX, dimY });
    console.log('🏰 Scene:', { name: sceneName, description: sceneDescription?.substring(0, 100) });

    // Get characters and NPCs from session
    const players = activeSession?.players || [];
    const npcs = activeSession?.npcs || [];

    console.log('🎭 Players:', players);
    console.log('🎭 NPCs:', npcs);

    // Helper function to get character position
    const getCharacterPosition = (character: any) => {
        // Try multiple position formats
        if (character?.position) {
            return {
                x: typeof character.position.x === 'number' ? character.position.x : Math.floor(Math.random() * dimX),
                y: typeof character.position.y === 'number' ? character.position.y : Math.floor(Math.random() * dimY)
            };
        }
        // Random position if not available
        return {
            x: Math.floor(Math.random() * dimX),
            y: Math.floor(Math.random() * dimY)
        };
    };

    // Helper function to render character on grid
    const renderCharacter = (x: number, y: number, character: any, type: 'player' | 'npc') => {
        const color = type === 'player' ? '#4CAF50' : '#f44336'; // Green for players, red for NPCs
        const name = character?.character_name || character?.name || 'Unknown';
        const race = character?.race || '';
        const charClass = character?.char_class || character?.class || '';

        return (
            <div
                key={`${type}-${name}-${x}-${y}`}
                className="grid-cell-character"
                title={`${name} (${race} ${charClass})`}
                style={{
                    position: 'absolute',
                    left: `${x * (100 / dimX)}%`,
                    top: `${y * (100 / dimY)}%`,
                    width: `${100 / dimX}%`,
                    height: `${100 / dimY}%`,
                    backgroundColor: color,
                    borderRadius: '50%',
                    border: '2px solid white',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '12px',
                    color: 'white',
                    fontWeight: 'bold',
                    cursor: 'pointer',
                    zIndex: 10
                }}
            >
                {name.charAt(0).toUpperCase()}
            </div>
        );
    };

    return (
        <div className="scene-viewer">
            {/* Scene Header */}
            <div className="scene-header">
                <h2 className="scene-title">{sceneName}</h2>
            </div>

            {/* Scene Description */}
            <div className="scene-description-container">
                <p className="scene-description">{sceneDescription}</p>
            </div>

            {/* Grid View */}
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

                    {/* Render players on the grid */}
                    <div className="grid-characters-layer">
                        {players.map((player) => {
                            const character = player?.character || player;
                            const pos = getCharacterPosition(character);
                            return renderCharacter(pos.x, pos.y, character, 'player');
                        })}

                        {/* Render NPCs on the grid */}
                        {npcs.map((npc) => {
                            const character = npc?.character || npc;
                            const pos = getCharacterPosition(character);
                            return renderCharacter(pos.x, pos.y, character, 'npc');
                        })}
                    </div>
                </div>
            </div>

            {/* Character Legend */}
            {(players.length > 0 || npcs.length > 0) && (
                <div className="character-legend">
                    <h4>Characters in Scene:</h4>
                    <div className="legend-items">
                        {players.map((player, idx) => {
                            const character = player?.character || player;
                            return (
                                <div key={`player-legend-${idx}`} className="legend-item player">
                                    <span className="legend-color" style={{ backgroundColor: '#4CAF50' }}></span>
                                    <span>{character?.name || player?.character_name || 'Unknown Player'}</span>
                                </div>
                            );
                        })}
                        {npcs.map((npc, idx) => {
                            const character = npc?.character || npc;
                            return (
                                <div key={`npc-legend-${idx}`} className="legend-item npc">
                                    <span className="legend-color" style={{ backgroundColor: '#f44336' }}></span>
                                    <span>{character?.name || npc?.name || 'Unknown NPC'}</span>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
};
