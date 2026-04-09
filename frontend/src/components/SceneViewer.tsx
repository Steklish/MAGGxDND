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
    const dimX = typeof dimensions?.x === 'number' ? dimensions.x : 20;
    const dimY = typeof dimensions?.y === 'number' ? dimensions.y : 20;

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

    // Helper function to generate tooltip content
    const getTooltipContent = (obj: any): TooltipInfo => {
        const lines: string[] = [];
        
        // Name
        lines.push(`<strong>${obj.name || 'Unknown Object'}</strong>`);
        
        // Type
        if (obj.obj_type) {
            lines.push(`<span style="color: ${getObjectTypeColor(obj.obj_type)}">[${obj.obj_type}]</span>`);
        }
        
        // Description
        if (obj.description) {
            lines.push(`<hr style="margin: 4px 0; border-color: #555;">`);
            lines.push(obj.description);
        }
        
        // State
        if (obj.state && obj.state !== 'normal') {
            lines.push(`<span style="color: #FFC107;">State: ${obj.state}</span>`);
        }
        
        // Locked
        if (obj.is_locked) {
            lines.push(`<span style="color: #FF5722;">🔒 Locked</span>`);
        }
        
        // Hidden
        if (obj.is_hidden) {
            lines.push(`<span style="color: #9E9E9E;">👁️ Hidden</span>`);
        }
        
        // Combat properties
        if (obj.damage_dice || obj.damage_type) {
            lines.push(`<hr style="margin: 4px 0; border-color: #555;">`);
            lines.push(`<span style="color: #F44336;">⚔️ ${obj.damage_dice || '?'} ${obj.damage_type || ''}</span>`);
        }
        
        // Container contents
        if (obj.content && obj.content.length > 0) {
            lines.push(`<hr style="margin: 4px 0; border-color: #555;">`);
            lines.push(`<span style="color: #4CAF50;">📦 Contents: ${obj.content.join(', ')}</span>`);
        }
        
        if (obj.contained_objects && obj.contained_objects.length > 0) {
            lines.push(`<hr style="margin: 4px 0; border-color: #555;">`);
            lines.push(`<span style="color: #4CAF50;">📦 Contains: ${obj.contained_objects.map((o: any) => o.name).join(', ')}</span>`);
        }
        
        // Capacity
        if (obj.capacity !== null && obj.capacity !== undefined) {
            const contentCount = (obj.content?.length || 0) + (obj.contained_objects?.length || 0);
            lines.push(`Capacity: ${contentCount}/${obj.capacity}`);
        }
        
        // Quantity
        if (obj.quantity > 1) {
            lines.push(`Quantity: ${obj.quantity}`);
        }
        
        // Equipped
        if (obj.is_equipped) {
            lines.push(`<span style="color: #2196F3;">🎒 Equipped</span>`);
        }
        
        // Tags
        if (obj.tags && obj.tags.length > 0) {
            lines.push(`<hr style="margin: 4px 0; border-color: #555;">`);
            lines.push(`<span style="color: #FFEB3B;">Tags: ${obj.tags.join(', ')}</span>`);
        }
        
        // Position
        if (obj.position) {
            lines.push(`<hr style="margin: 4px 0; border-color: #555;">`);
            lines.push(`Position: (${obj.position.x}, ${obj.position.y}) ${scaleUnit}`);
        }
        
        return {
            x: obj.position?.x || 0,
            y: obj.position?.y || 0,
            content: lines.join('<br>'),
            title: obj.name || 'Unknown Object'
        };
    };

    // Helper function to render character on grid
    const renderCharacter = (x: number, y: number, character: any, type: 'player' | 'npc', idx: number) => {
        const color = type === 'player' ? '#4CAF50' : '#f44336'; // Green for players, red for NPCs
        const name = character?.character_name || character?.name || 'Unknown';
        const race = character?.race || '';
        const charClass = character?.char_class || character?.class || '';

        return (
            <div
                key={`${type}-${name}-${idx}`}
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

    // Helper function to render object on grid
    const renderObject = (obj: any, index: number, x: number, y: number) => {
        const color = getObjectTypeColor(obj.obj_type);
        
        // Determine icon based on type
        let icon = '📦'; // Default container
        if (obj.obj_type === 'interactable') icon = '⚙️';
        else if (obj.obj_type === 'prop') icon = '🎨';
        else if (obj.damage_dice) icon = '⚔️'; // Weapon
        else if (obj.is_locked) icon = '🔒';
        else if (obj.is_hidden) icon = '👁️';
        
        return (
            <div
                key={`object-${index}-${obj.id || obj.name}`}
                className="grid-cell-object"
                onMouseEnter={() => setHoveredObject({ obj, x, y })}
                onMouseLeave={() => setHoveredObject(null)}
                style={{
                    position: 'absolute',
                    left: `${x * (100 / dimX)}%`,
                    top: `${y * (100 / dimY)}%`,
                    width: `${100 / dimX}%`,
                    height: `${100 / dimY}%`,
                    backgroundColor: color,
                    borderRadius: '4px',
                    border: obj.state === 'active' ? '2px solid #FFC107' : '1px solid rgba(255,255,255,0.3)',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '14px',
                    cursor: 'pointer',
                    zIndex: 5,
                    opacity: obj.is_hidden ? 0.6 : 1,
                }}
            >
                {icon}
            </div>
        );
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
                <div className="grid-container">
                    <div className="grid">
                        {Array(dimY).fill(null).map((_, y) => (
                            <div key={`row-${y}`} className="grid-row">
                                {Array(dimX).fill(null).map((_, x) => (
                                    <div key={`cell-${x}-${y}`} className="grid-cell" title={`Cell ${x},${y}`}>·</div>
                                ))}
                            </div>
                        ))}

                        {/* Render objects on the grid - using memoized positions */}
                        {objectPositions.map(({ obj, idx, x, y }) => renderObject(obj, idx, x, y))}

                        {/* Render players on the grid - using memoized positions */}
                        {playerPositions.map(({ character, idx, x, y }) => 
                            renderCharacter(x, y, character, 'player', idx)
                        )}

                        {/* Render NPCs on the grid - using memoized positions */}
                        {npcPositions.map(({ character, idx, x, y }) => 
                            renderCharacter(x, y, character, 'npc', idx)
                        )}
                    </div>
                </div>

                {/* Object Hover Tooltip */}
                {hoveredObject && (
                    <div 
                        className="object-tooltip"
                        dangerouslySetInnerHTML={{ __html: getTooltipContent(hoveredObject.obj).content }}
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
                                    onMouseEnter={() => setHoveredObject({ obj, x: obj.position?.x || 0, y: obj.position?.y || 0 })}
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
