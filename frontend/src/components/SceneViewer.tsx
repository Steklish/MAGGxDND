import React, { useState, useMemo } from 'react';
import { useGameStore } from '../store/gameStore';
import './SceneViewer.css';

interface TooltipInfo {
    x: number;
    y: number;
    content: string;
    title: string;
}

export const SceneViewer: React.FC = () => {
    const { currentScene, session, currentSession } = useGameStore();
    const [hoveredObject, setHoveredObject] = useState<{ obj: any; x: number; y: number } | null>(null);
    const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

    // Use currentSession as primary, session as fallback
    const activeSession = currentSession || session;

    // Safely access nested properties with defaults (BEFORE early return)
    const sceneName = currentScene?.name || 'Unknown Location';
    const sceneDescription = currentScene?.description || 'The scene is shrouded in mystery...';
    const centerPos = currentScene?.center_position || { x: 10, y: 10 };
    const dimensions = currentScene?.dimensions || { x: 20, y: 20 };
    const scaleUnit = currentScene?.scale_unit || 'feet';
    const sceneObjects = currentScene?.objects || [];

    // Ensure x and y exist
    const centerX = typeof centerPos?.x === 'number' ? centerPos.x : 10;
    const centerY = typeof centerPos?.y === 'number' ? centerPos.y : 10;
    const dimX = typeof dimensions?.x === 'number' && dimensions.x > 0 ? dimensions.x : 20;
    const dimY = typeof dimensions?.y === 'number' && dimensions.y > 0 ? dimensions.y : 20;

    // Safety check: prevent rendering with invalid dimensions
    if (dimX <= 0 || dimY <= 0 || dimX > 100 || dimY > 100) {
        return (
            <div className="scene-viewer">
                <div className="no-scene">
                    <p>Invalid scene dimensions</p>
                    <p className="hint">Grid size must be between 1 and 100</p>
                </div>
            </div>
        );
    }

    // Get characters and NPCs from session
    const players = activeSession?.players || [];
    const npcs = activeSession?.npcs || [];

    // Helper function to get character position
    const getCharacterPosition = (character: any) => {
        if (character?.position) {
            // Clamp to grid bounds and round to avoid sub-pixel flickering
            const x = Math.max(0, Math.min(dimX - 1, Math.floor(character.position.x)));
            const y = Math.max(0, Math.min(dimY - 1, Math.floor(character.position.y)));
            return { x, y };
        }
        // Random position if not available
        return {
            x: Math.floor(Math.random() * dimX),
            y: Math.floor(Math.random() * dimY)
        };
    };

    // Helper function to get object position
    const getObjectPosition = (obj: any) => {
        if (obj?.position) {
            // Clamp to grid bounds and round to avoid sub-pixel flickering
            const x = Math.max(0, Math.min(dimX - 1, Math.floor(obj.position.x)));
            const y = Math.max(0, Math.min(dimY - 1, Math.floor(obj.position.y)));
            return { x, y };
        }
        // Random position if not available
        return {
            x: Math.floor(Math.random() * dimX),
            y: Math.floor(Math.random() * dimY)
        };
    };

    // Memoize positions to prevent unnecessary recalculations (MUST be before early return)
    const playerPositions = useMemo(() => 
        players.map((player, idx) => {
            const character = player?.character || player;
            return { character, idx, ...getCharacterPosition(character) };
        }),
        [players, dimX, dimY]
    );

    const npcPositions = useMemo(() => 
        npcs.map((npc, idx) => {
            const character = npc?.character || npc;
            return { character, idx, ...getCharacterPosition(character) };
        }),
        [npcs, dimX, dimY]
    );

    const objectPositions = useMemo(() => 
        sceneObjects.map((obj, idx) => ({
            obj,
            idx,
            ...getObjectPosition(obj)
        })),
        [sceneObjects, dimX, dimY]
    );

    // Check for null, undefined, or invalid scene (AFTER all hooks)
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

    // Helper function to get object type color
    const getObjectTypeColor = (objType: string) => {
        switch (objType?.toLowerCase()) {
            case 'container': return '#9C27B0'; // Purple
            case 'interactable': return '#FF9800'; // Orange
            case 'prop': return '#607D8B'; // Blue Grey
            default: return '#795548'; // Brown
        }
    };

    // Simple tooltip content generator
    const getTooltipContent = (obj: any) => {
        const lines: string[] = [];
        lines.push(`<strong>${obj.name || 'Unknown Object'}</strong>`);
        if (obj.obj_type) lines.push(`<span style="color: ${getObjectTypeColor(obj.obj_type)}">[${obj.obj_type}]</span>`);
        if (obj.description) lines.push(obj.description);
        if (obj.state && obj.state !== 'normal') lines.push(`<span style="color: #FFC107;">State: ${obj.state}</span>`);
        if (obj.is_locked) lines.push('🔒 Locked');
        if (obj.is_hidden) lines.push('👁️ Hidden');
        if (obj.damage_dice) lines.push(`⚔️ ${obj.damage_dice} ${obj.damage_type || ''}`);
        return lines.join('<br>');
    };

    return (
        <div className="scene-viewer">
            {/* Scene Header */}
            <div className="scene-header">
                <h2 className="scene-title">{sceneName}</h2>
                {scaleUnit && <span className="scene-scale">({dimX}x{dimY} {scaleUnit})</span>}
            </div>

            {/* Scene Description */}
            <div className="scene-description-container">
                <p className="scene-description">{sceneDescription}</p>
            </div>

            {/* Grid View */}
            <div className="scene-content">
                <div className="grid-wrapper">
                    <div className="grid" style={{
                        gridTemplateColumns: `repeat(${dimX}, 1fr)`,
                        gridTemplateRows: `repeat(${dimY}, 1fr)`
                    }}>
                        {/* Render grid cells */}
                        {Array.from({ length: dimY * dimX }).map((_, i) => {
                            const x = i % dimX;
                            const y = Math.floor(i / dimX);
                            return (
                                <div 
                                    key={`cell-${x}-${y}`} 
                                    className="grid-cell"
                                    data-x={x}
                                    data-y={y}
                                />
                            );
                        })}

                        {/* Render objects on the grid */}
                        {objectPositions.map(({ obj, idx, x, y }) => (
                            <div
                                key={`object-${idx}-${obj.id || obj.name}`}
                                className="grid-marker grid-marker-object"
                                style={{
                                    gridColumnStart: x + 1,
                                    gridRowStart: y + 1,
                                    backgroundColor: getObjectTypeColor(obj.obj_type),
                                    opacity: obj.is_hidden ? 0.5 : 1,
                                    borderColor: obj.state === 'active' ? '#FFC107' : 'rgba(255,255,255,0.3)',
                                }}
                                onMouseEnter={(e) => {
                                    setHoveredObject({ obj, x, y });
                                    setTooltipPos({ x: e.clientX, y: e.clientY });
                                }}
                                onMouseMove={(e) => {
                                    setTooltipPos({ x: e.clientX, y: e.clientY });
                                }}
                                onMouseLeave={() => setHoveredObject(null)}
                            >
                                {obj.obj_type === 'interactable' ? '⚙️' :
                                 obj.obj_type === 'prop' ? '🎨' :
                                 obj.damage_dice ? '⚔️' :
                                 obj.is_locked ? '🔒' :
                                 obj.is_hidden ? '👁️' : '📦'}
                            </div>
                        ))}

                        {/* Render players on the grid */}
                        {playerPositions.map(({ character, idx, x, y }) => {
                            const name = character?.character_name || character?.name || 'Unknown';
                            return (
                                <div
                                    key={`player-${idx}-${name}`}
                                    className="grid-marker grid-marker-character grid-marker-player"
                                    style={{
                                        gridColumnStart: x + 1,
                                        gridRowStart: y + 1,
                                    }}
                                    title={`${name} (${character?.race || ''} ${character?.char_class || ''})`}
                                >
                                    {name.charAt(0).toUpperCase()}
                                </div>
                            );
                        })}

                        {/* Render NPCs on the grid */}
                        {npcPositions.map(({ character, idx, x, y }) => {
                            const name = character?.character_name || character?.name || 'Unknown';
                            return (
                                <div
                                    key={`npc-${idx}-${name}`}
                                    className="grid-marker grid-marker-character grid-marker-npc"
                                    style={{
                                        gridColumnStart: x + 1,
                                        gridRowStart: y + 1,
                                    }}
                                    title={`${name} (${character?.race || ''} ${character?.char_class || ''})`}
                                >
                                    {name.charAt(0).toUpperCase()}
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Object Hover Tooltip - follows mouse */}
                {hoveredObject && (
                    <div
                        className="object-tooltip"
                        style={{
                            left: tooltipPos.x + 15,
                            top: tooltipPos.y - 10,
                        }}
                        dangerouslySetInnerHTML={{ __html: getTooltipContent(hoveredObject.obj) }}
                    />
                )}
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

            {/* Objects Legend */}
            {sceneObjects.length > 0 && (
                <div className="objects-legend">
                    <h4>Objects in Scene ({sceneObjects.length}):</h4>
                    <div className="legend-items">
                        {sceneObjects.map((obj: any, idx: number) => {
                            const color = getObjectTypeColor(obj.obj_type);
                            return (
                                <div
                                    key={`object-legend-${idx}`}
                                    className="legend-item object"
                                    onMouseEnter={(e) => {
                                        setHoveredObject({ obj, x: obj.position?.x || 0, y: obj.position?.y || 0 });
                                        setTooltipPos({ x: e.clientX, y: e.clientY });
                                    }}
                                    onMouseMove={(e) => {
                                        setTooltipPos({ x: e.clientX, y: e.clientY });
                                    }}
                                    onMouseLeave={() => setHoveredObject(null)}
                                >
                                    <span className="legend-color" style={{ backgroundColor: color }}></span>
                                    <span>{obj.name || 'Unknown Object'}</span>
                                    {obj.obj_type && <span className="object-type-badge">{obj.obj_type}</span>}
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
};
