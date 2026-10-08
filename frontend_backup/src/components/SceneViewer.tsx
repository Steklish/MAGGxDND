import React, { useState, useMemo } from 'react';
import { useGameStore } from '../store/gameStore';
import './SceneViewer.css';

interface SelectedEntity {
    type: 'player' | 'npc' | 'object';
    data: any;
    x: number;
    y: number;
}

export const SceneViewer: React.FC = () => {
    const { currentScene, session, currentSession, sendAction, activeCharacter, setCurrentScene } = useGameStore();
    const [selectedEntity, setSelectedEntity] = useState<SelectedEntity | null>(null);
    const [zoom, setZoom] = useState<number>(1.0);
    const [showGrid, setShowGrid] = useState<boolean>(true);
    const [hoveredInfo, setHoveredInfo] = useState<{ title: string; subtitle: string; x: number; y: number } | null>(null);
    const [isRegenerating, setIsRegenerating] = useState<boolean>(false);

    // Use currentSession as primary, session as fallback
    const activeSession = currentSession || session;

    // Tactical battle map background URL (preserves across token movements/turns)
    const mapImageUrl = useMemo(() => {
        return (
            currentScene?.battlemap_image_url ||
            currentScene?.background_image_url ||
            '/assets/placeholders/battlemap_stone.svg'
        );
    }, [currentScene?.battlemap_image_url, currentScene?.background_image_url]);

    // Safely access nested properties with defaults
    const sceneName = currentScene?.name || 'Tactical Arena';
    const sceneDescription = currentScene?.description || 'The environment lies in eerie stillness, waiting for action...';
    const centerPos = currentScene?.center_position || { x: 10, y: 10 };
    const dimensions = currentScene?.dimensions || { x: 20, y: 20 };
    const scaleUnit = currentScene?.scale_unit || 'feet';
    const sceneObjects = currentScene?.objects || [];

    const dimX = typeof dimensions?.x === 'number' && dimensions.x > 0 ? dimensions.x : 20;
    const dimY = typeof dimensions?.y === 'number' && dimensions.y > 0 ? dimensions.y : 20;

    // Get characters and NPCs from session
    const players = activeSession?.players || [];
    const npcs = activeSession?.npcs || [];

    const getCharacterPosition = (character: any) => {
        if (character?.position) {
            const x = Math.max(0, Math.min(dimX - 1, Math.floor(character.position.x)));
            const y = Math.max(0, Math.min(dimY - 1, Math.floor(character.position.y)));
            return { x, y };
        }
        return {
            x: Math.floor(Math.random() * dimX),
            y: Math.floor(Math.random() * dimY)
        };
    };

    const getObjectPosition = (obj: any) => {
        if (obj?.position) {
            const x = Math.max(0, Math.min(dimX - 1, Math.floor(obj.position.x)));
            const y = Math.max(0, Math.min(dimY - 1, Math.floor(obj.position.y)));
            return { x, y };
        }
        return {
            x: Math.floor(Math.random() * dimX),
            y: Math.floor(Math.random() * dimY)
        };
    };

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
        sceneObjects.map((obj: any, idx: number) => ({
            obj,
            idx,
            ...getObjectPosition(obj)
        })),
        [sceneObjects, dimX, dimY]
    );

    if (!currentScene || typeof currentScene !== 'object') {
        return (
            <div className="ergonomic-scene-viewer empty-state">
                <div className="scene-placeholder">
                    <span className="placeholder-icon">🗺️</span>
                    <h3>Tactical Battle Grid</h3>
                    <p>No active battle scene is loaded. Once the DM sets the scene, spatial tokens will appear here.</p>
                </div>
            </div>
        );
    }

    const getObjectTypeColor = (objType: string) => {
        switch (objType?.toLowerCase()) {
            case 'container': return '#a855f7';
            case 'interactable': return '#f59e0b';
            case 'prop': return '#64748b';
            default: return '#78716c';
        }
    };

    const handleTargetAction = () => {
        if (!selectedEntity || !activeCharacter) return;
        const name = selectedEntity.data.name || selectedEntity.data.character_name || 'the target';
        if (selectedEntity.type === 'object') {
            sendAction(`I interact with ${name} at coordinate (${selectedEntity.x}, ${selectedEntity.y}).`, activeCharacter);
        } else {
            sendAction(`I target ${name} with my action.`, activeCharacter);
        }
    };

    const handleRegenerateMap = async () => {
        const sessionId = (activeSession as any)?.session_id || (activeSession as any)?.session_uuid || (session as any)?.session_id || (session as any)?.session_uuid;
        if (!sessionId || isRegenerating) return;

        setIsRegenerating(true);
        try {
            const response = await fetch(`/api/v1/sessions/${sessionId}/scene/regenerate-map`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (response.ok) {
                const data = await response.json();
                if (data.battlemap_image_url && currentScene) {
                    const updated = {
                        ...currentScene,
                        battlemap_image_url: data.battlemap_image_url,
                        background_image_url: data.battlemap_image_url,
                    };
                    if (setCurrentScene) {
                        setCurrentScene(updated);
                    }
                }
            } else {
                console.warn('Map regeneration returned status', response.status);
            }
        } catch (error) {
            console.error('Failed to regenerate battle map:', error);
        } finally {
            setIsRegenerating(false);
        }
    };

    return (
        <div className="ergonomic-scene-viewer">
            {/* Top Toolbar */}
            <div className="scene-toolbar">
                <div className="scene-meta">
                    <span className="location-icon">📍</span>
                    <span className="location-name">{sceneName}</span>
                    <span className="location-dim">{dimX}×{dimY} {scaleUnit}</span>
                </div>

                <div className="scene-controls">
                    <button
                        type="button"
                        className={`tool-btn ${showGrid ? 'active' : ''}`}
                        onClick={() => setShowGrid(!showGrid)}
                        title="Toggle Grid Lines"
                    >
                        ⊞ Grid
                    </button>
                    <button
                        type="button"
                        className={`tool-btn regenerate-btn ${isRegenerating ? 'loading' : ''}`}
                        onClick={handleRegenerateMap}
                        disabled={isRegenerating}
                        title="Regenerate Tactical Battle Map"
                        data-testid="regenerate-map-btn"
                    >
                        {isRegenerating ? '⏳ Generating...' : '🎨 Gen Map'}
                    </button>
                    <button
                        type="button"
                        className="tool-btn"
                        onClick={() => setZoom(prev => Math.max(0.6, prev - 0.15))}
                        title="Zoom Out"
                    >
                        -
                    </button>
                    <span className="zoom-label">{Math.round(zoom * 100)}%</span>
                    <button
                        type="button"
                        className="tool-btn"
                        onClick={() => setZoom(prev => Math.min(2.0, prev + 0.15))}
                        title="Zoom In"
                    >
                        +
                    </button>
                    <button
                        type="button"
                        className="tool-btn"
                        onClick={() => setZoom(1.0)}
                        title="Reset Zoom"
                    >
                        ↺
                    </button>
                </div>
            </div>

            {/* Tactical Grid Viewport */}
            <div className="scene-viewport">
                <div
                    className="grid-zoom-container"
                    style={{ transform: `scale(${zoom})`, transformOrigin: 'top left' }}
                >
                    {mapImageUrl && (
                        <img
                            src={mapImageUrl}
                            alt={sceneName || 'Tactical Battle Map'}
                            className="tactical-map-background"
                            data-testid="tactical-map-background"
                            loading="eager"
                        />
                    )}
                    <div
                        className={`tactical-grid ${showGrid ? 'grid-visible' : ''}`}
                        style={{
                            gridTemplateColumns: `repeat(${dimX}, 1fr)`,
                            gridTemplateRows: `repeat(${dimY}, 1fr)`,
                        }}
                    >
                        {/* Grid cells */}
                        {Array.from({ length: dimY * dimX }).map((_, i) => {
                            const x = i % dimX;
                            const y = Math.floor(i / dimX);
                            return (
                                <div
                                    key={`cell-${x}-${y}`}
                                    className="tactical-cell"
                                    data-x={x}
                                    data-y={y}
                                />
                            );
                        })}

                        {/* Interactive Objects */}
                        {objectPositions.map(({ obj, idx, x, y }: { obj: any; idx: number; x: number; y: number }) => {
                            const isSelected = selectedEntity?.type === 'object' && selectedEntity?.data === obj;
                            return (
                                <div
                                    key={`obj-${idx}-${obj.name || idx}`}
                                    className={`tactical-token object-token ${isSelected ? 'selected' : ''}`}
                                    style={{
                                        gridColumnStart: x + 1,
                                        gridRowStart: y + 1,
                                        backgroundColor: getObjectTypeColor(obj.obj_type),
                                    }}
                                    onClick={() => setSelectedEntity({ type: 'object', data: obj, x, y })}
                                    onMouseEnter={() => setHoveredInfo({ title: obj.name || 'Object', subtitle: `[${obj.obj_type || 'prop'}] (${x}, ${y})`, x, y })}
                                    onMouseLeave={() => setHoveredInfo(null)}
                                >
                                    {obj.obj_type === 'container' ? '📦' :
                                     obj.obj_type === 'interactable' ? '⚙️' :
                                     obj.damage_dice ? '⚔️' : '🗿'}
                                </div>
                            );
                        })}

                        {/* Player Tokens */}
                        {playerPositions.map(({ character, idx, x, y }) => {
                            const name = character?.name || character?.character_name || 'Hero';
                            const isSelected = selectedEntity?.type === 'player' && selectedEntity?.data === character;
                            const isSelf = activeCharacter?.name === name;
                            return (
                                <div
                                    key={`pl-${idx}-${name}`}
                                    className={`tactical-token player-token ${isSelected ? 'selected' : ''} ${isSelf ? 'self-token' : ''}`}
                                    style={{
                                        gridColumnStart: x + 1,
                                        gridRowStart: y + 1,
                                    }}
                                    onClick={() => setSelectedEntity({ type: 'player', data: character, x, y })}
                                    onMouseEnter={() => setHoveredInfo({ title: name, subtitle: `${character.race || ''} ${character.char_class || 'Player'} (${x}, ${y})`, x, y })}
                                    onMouseLeave={() => setHoveredInfo(null)}
                                >
                                    <span className="token-initial">{name.charAt(0).toUpperCase()}</span>
                                </div>
                            );
                        })}

                        {/* NPC Tokens */}
                        {npcPositions.map(({ character, idx, x, y }) => {
                            const name = character?.name || character?.character_name || 'NPC';
                            const isSelected = selectedEntity?.type === 'npc' && selectedEntity?.data === character;
                            const isHostile = (character.alignment || '').includes('Evil') || (character.alignment || '').includes('Chaotic');
                            return (
                                <div
                                    key={`npc-${idx}-${name}`}
                                    className={`tactical-token npc-token ${isHostile ? 'hostile' : 'ally'} ${isSelected ? 'selected' : ''}`}
                                    style={{
                                        gridColumnStart: x + 1,
                                        gridRowStart: y + 1,
                                    }}
                                    onClick={() => setSelectedEntity({ type: 'npc', data: character, x, y })}
                                    onMouseEnter={() => setHoveredInfo({ title: name, subtitle: `${character.char_class || 'NPC'} (${x}, ${y})`, x, y })}
                                    onMouseLeave={() => setHoveredInfo(null)}
                                >
                                    <span className="token-initial">{name.charAt(0).toUpperCase()}</span>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Floating Hover Badge */}
                {hoveredInfo && (
                    <div className="hover-coordinate-badge">
                        <strong>{hoveredInfo.title}</strong> — {hoveredInfo.subtitle}
                    </div>
                )}
            </div>

            {/* Tactical Entity Inspector Drawer */}
            {selectedEntity ? (
                <div className="tactical-inspector-drawer">
                    <div className="inspector-avatar">
                        <span className="inspector-token-glyph">
                            {selectedEntity.type === 'object' ? '📦' : selectedEntity.data.name?.charAt(0).toUpperCase() || 'E'}
                        </span>
                    </div>

                    <div className="inspector-details">
                        <div className="inspector-title-row">
                            <h4 className="inspector-name">{selectedEntity.data.name || selectedEntity.data.character_name}</h4>
                            <span className="inspector-tag">{selectedEntity.type.toUpperCase()}</span>
                            <span className="inspector-coords">Coord: ({selectedEntity.x}, {selectedEntity.y})</span>
                        </div>

                        {selectedEntity.type !== 'object' ? (
                            <div className="inspector-vitals">
                                <span className="vital-item">HP: <strong>{selectedEntity.data.current_hp ?? 10}/{selectedEntity.data.max_hp ?? 10}</strong></span>
                                <span className="vital-item">AC: <strong>{selectedEntity.data.armor_class ?? 10}</strong></span>
                                <span className="vital-item">Speed: <strong>{selectedEntity.data.speed ?? 30}ft</strong></span>
                            </div>
                        ) : (
                            <p className="inspector-desc">{selectedEntity.data.description || 'An interactive item or prop in the scene.'}</p>
                        )}
                    </div>

                    <div className="inspector-actions">
                        <button
                            type="button"
                            className="target-btn"
                            onClick={handleTargetAction}
                        >
                            🎯 Target in Action
                        </button>
                        <button
                            type="button"
                            className="close-inspector-btn"
                            onClick={() => setSelectedEntity(null)}
                        >
                            ✕
                        </button>
                    </div>
                </div>
            ) : (
                <div className="tactical-footer-hint">
                    <span>💡 Click any token on the battle map to inspect stats or select as action target</span>
                </div>
            )}
        </div>
    );
};
