import React, { useState } from 'react';
import { useGameStore } from '../store/gameStore';
import { VectorIcon } from './common/VectorIcon';
import { highlightNarrativeKeywords } from '../utils/keywordHighlighter';
import { handleTiltAndHighlight, handleTiltReset } from '../utils/cardTilt';
import { useTranslation } from '../i18n/useTranslation';
import './SceneMenu.css';

interface SceneMenuProps {
    onClose?: () => void;
}

export const SceneMenu: React.FC<SceneMenuProps> = ({ onClose }) => {
    const { currentScene, activeCharacter, sendAction, currentSession, session } = useGameStore();
    const { t, language } = useTranslation();
    const [selectedObj, setSelectedObj] = useState<any | null>(null);

    const activeSession = currentSession || session;
    const sceneName = currentScene?.name || (language === 'ru' ? 'Тактическая Комната' : 'Tactical Chamber');
    const description = currentScene?.description || (language === 'ru'
        ? 'Воздух неподвижен в этой каменной зале. Тени пляшут на каменной кладке, пока отряд осматривает окружение.'
        : 'The air is still in this stone-hewn chamber. Shadows dance across chiseled masonry as your party observes the surroundings.');
    const dimensions = currentScene?.dimensions || { x: 20, y: 20 };
    const dimX = typeof dimensions.x === 'number' ? dimensions.x : 20;
    const dimY = typeof dimensions.y === 'number' ? dimensions.y : 20;
    const objects = currentScene?.objects || [];

    const locationGraph = (activeSession as any)?.location_graph || {};
    const allLocations = (activeSession as any)?.all_locations || {};
    const connectedLocations: string[] = locationGraph[sceneName] || [];
    const otherKnownLocations: string[] = Object.keys(allLocations).filter(
        (loc) => loc !== sceneName && !connectedLocations.includes(loc)
    );

    const knownEntityNames = [
        ...(activeSession?.players || []).map((p: any) => p?.character?.name || p?.name),
        ...(activeSession?.npcs || []).map((n: any) => n?.character?.name || n?.name),
    ].filter(Boolean);

    const handleInteract = (obj: any) => {
        if (!activeCharacter) return;
        const objName = obj.name || (language === 'ru' ? 'механизм' : 'the mechanism');
        const posX = obj.position?.x ?? '?';
        const posY = obj.position?.y ?? '?';
        const msg = language === 'ru'
            ? `Я взаимодействую с объектом "${objName}" по координатам (${posX}, ${posY}).`
            : `I interact with ${objName} at coordinate (${posX}, ${posY}).`;
        sendAction(msg, activeCharacter);
    };

    const handleInspect = (obj: any) => {
        if (!activeCharacter) return;
        const objName = obj.name || (language === 'ru' ? 'объект' : 'the object');
        const msg = language === 'ru'
            ? `Я внимательно осматриваю объект "${objName}" на наличие деталей или ловушек.`
            : `I examine and inspect ${objName} closely for details or traps.`;
        sendAction(msg, activeCharacter);
    };

    const handleSearchRoom = () => {
        if (!activeCharacter) return;
        const msg = language === 'ru'
            ? `Я тщательно осматриваю комнату "${sceneName}" в поисках скрытых дверей, сокровищ или ловушек.`
            : `I search the entire ${sceneName} for hidden doors, concealed treasure, or secret passages.`;
        sendAction(msg, activeCharacter);
    };

    const handleTravelToLocation = (targetLocation: string) => {
        if (!activeCharacter) return;
        const msg = language === 'ru'
            ? `Я веду отряд и перехожу через проход в ${targetLocation}.`
            : `I lead the party and travel through the exit into ${targetLocation}.`;
        sendAction(msg, activeCharacter);
    };

    return (
        <div className="scene-menu-container">
            {/* Header */}
            <div className="scene-menu-header">
                <div className="scene-menu-title-group">
                    <span className="scene-menu-crest"><VectorIcon name="tower" /></span>
                    <div>
                        <h3 className="scene-menu-heading">{sceneName}</h3>
                        <span className="scene-menu-sub">Tactical Dossier • {dimX}×{dimY} ft Arena</span>
                    </div>
                </div>
                {onClose && (
                    <button
                        type="button"
                        className="scene-menu-close-btn"
                        onClick={onClose}
                        title="Close Scene Dossier"
                    >
                        ✕
                    </button>
                )}
            </div>

            <div className="scene-menu-scroll-body">
                {/* Visual Snapshot & Environment */}
                <div className="scene-menu-section">
                    <div className="scene-section-title">
                        <VectorIcon name="gate" />
                        <span>{language === 'ru' ? 'Окружение & Описание' : 'Environment & Narrative'}</span>
                    </div>
                    <div
                        className="scene-narrative-card reveal-highlight geometric-tilt"
                        onMouseMove={handleTiltAndHighlight}
                        onMouseLeave={handleTiltReset}
                    >
                        <div className="scene-narrative-text">
                            {highlightNarrativeKeywords(description, knownEntityNames)}
                        </div>
                    </div>
                </div>

                {/* Scene Exploration Fast Actions */}
                <div className="scene-menu-section">
                    <div className="scene-section-title">
                        <VectorIcon name="rune" />
                        <span>{language === 'ru' ? 'Быстрые Исследования' : 'Spatial Inquiries'}</span>
                    </div>
                    <div className="scene-quick-actions">
                        <button
                            type="button"
                            className="scene-action-chip reveal-highlight"
                            onClick={handleSearchRoom}
                            onMouseMove={handleTiltAndHighlight}
                            onMouseLeave={handleTiltReset}
                        >
                            <span>🔍 {language === 'ru' ? 'Обыскать комнату' : 'Search Chamber'}</span>
                        </button>
                        <button
                            type="button"
                            className="scene-action-chip reveal-highlight"
                            onClick={() => {
                                if (activeCharacter) {
                                    const msg = language === 'ru'
                                        ? 'Я проверяю комнату на наличие нажимных плит, растяжек и магических ловушек.'
                                        : 'I check the room for pressure plates, tripwires, and magical wards.';
                                    sendAction(msg, activeCharacter);
                                }
                            }}
                            onMouseMove={handleTiltAndHighlight}
                            onMouseLeave={handleTiltReset}
                        >
                            <span>⚠️ {language === 'ru' ? 'Поиск ловушек' : 'Detect Traps'}</span>
                        </button>
                        <button
                            type="button"
                            className="scene-action-chip reveal-highlight"
                            onClick={() => {
                                if (activeCharacter) {
                                    const msg = language === 'ru'
                                        ? 'Я осторожно прислушиваюсь у дверного проема к приближающимся звукам.'
                                        : 'I listen closely at the chamber doorway for approaching sounds.';
                                    sendAction(msg, activeCharacter);
                                }
                            }}
                            onMouseMove={handleTiltAndHighlight}
                            onMouseLeave={handleTiltReset}
                        >
                            <span>👂 {language === 'ru' ? 'Слушать у дверей' : 'Listen at Doors'}</span>
                        </button>
                    </div>
                </div>

                {/* Connected Exits & Scene Navigation */}
                <div className="scene-menu-section">
                    <div className="scene-section-title">
                        <VectorIcon name="tower" />
                        <span>{language === 'ru' ? 'Переходы & Выходы' : 'Connected Exits & Travel'} ({connectedLocations.length + otherKnownLocations.length})</span>
                    </div>
                    {connectedLocations.length === 0 && otherKnownLocations.length === 0 ? (
                        <div className="scene-empty-objects">
                            <span className="empty-glyph"><VectorIcon name="gate" /></span>
                            <p>{language === 'ru' ? 'Смежные проходы пока не обнаружены.' : 'No adjacent passageways mapped yet.'}</p>
                            <span className="empty-sub">{language === 'ru' ? 'Исследуйте арки, коридоры и двери через чат, чтобы открыть новые зоны.' : 'Explore gates, corridors, or doors in chat to branch into new areas.'}</span>
                        </div>
                    ) : (
                        <div className="scene-quick-actions" style={{ flexWrap: 'wrap', gap: '8px' }}>
                            {connectedLocations.map((loc) => (
                                <button
                                    key={loc}
                                    type="button"
                                    className="scene-action-chip reveal-highlight"
                                    style={{ borderColor: 'var(--amber-gold, #c89b3c)', background: 'rgba(200, 155, 60, 0.15)' }}
                                    onClick={() => handleTravelToLocation(loc)}
                                    title={language === 'ru' ? `Пройти через выход прямо в ${loc}` : `Pass through door/passage directly into ${loc}`}
                                >
                                    <span>🚪 {language === 'ru' ? `Войти в ${loc}` : `Enter ${loc}`}</span>
                                </button>
                            ))}
                            {otherKnownLocations.map((loc) => (
                                <button
                                    key={loc}
                                    type="button"
                                    className="scene-action-chip reveal-highlight"
                                    onClick={() => handleTravelToLocation(loc)}
                                    title={language === 'ru' ? `Отправиться в известную локацию: ${loc}` : `Travel to visited realm: ${loc}`}
                                >
                                    <span>🗺️ {language === 'ru' ? `Перейти в ${loc}` : `Travel to ${loc}`}</span>
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {/* Objects in Scene */}
                <div className="scene-menu-section">
                    <div className="scene-section-title">
                        <VectorIcon name="item" />
                        <span>{language === 'ru' ? 'Объекты сцены' : 'Objects & Props in Scene'} ({objects.length})</span>
                    </div>

                    {objects.length === 0 ? (
                        <div className="scene-empty-objects">
                            <span className="empty-glyph"><VectorIcon name="rune" /></span>
                            <p>{language === 'ru' ? 'Интерактивные объекты пока не зарегистрированы.' : 'No loose mechanisms or containers registered yet.'}</p>
                            <span className="empty-sub">{language === 'ru' ? 'Обыщите комнату, чтобы обнаружить скрытые детали.' : 'Interact with the room or search to uncover features.'}</span>
                        </div>
                    ) : (
                        <div className="scene-objects-list">
                            {objects.map((obj: any, idx: number) => {
                                const isSelected = selectedObj === obj;
                                const objName = obj.name || (language === 'ru' ? `Объект #${idx + 1}` : `Object #${idx + 1}`);
                                const objType = obj.obj_type || 'prop';
                                const posX = obj.position?.x ?? '-';
                                const posY = obj.position?.y ?? '-';

                                return (
                                    <div
                                        key={idx}
                                        className={`scene-object-card reveal-highlight geometric-tilt ${isSelected ? 'selected' : ''}`}
                                        onClick={() => setSelectedObj(isSelected ? null : obj)}
                                        onMouseMove={handleTiltAndHighlight}
                                        onMouseLeave={handleTiltReset}
                                    >
                                        <div className="obj-card-top">
                                            <div className="obj-name-group">
                                                <span className={`obj-type-icon type-${objType}`}>
                                                    {objType === 'container' ? '📦' :
                                                     objType === 'interactable' ? '⚙️' :
                                                     objType === 'hazard' ? '🔥' : '🗿'}
                                                </span>
                                                <div>
                                                    <span className="obj-title">{objName}</span>
                                                    <span className="obj-coords">{language === 'ru' ? 'Коорд' : 'Coord'}: ({posX}, {posY})</span>
                                                </div>
                                            </div>
                                            <span className={`obj-type-pill pill-${objType}`}>{objType}</span>
                                        </div>

                                        {obj.description && (
                                            <p className="obj-desc">{obj.description}</p>
                                        )}

                                        <div className="obj-actions-row">
                                            <button
                                                type="button"
                                                className="obj-interact-btn primary"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleInteract(obj);
                                                }}
                                            >
                                                ⚔️ {language === 'ru' ? 'Действие' : 'Interact'}
                                            </button>
                                            <button
                                                type="button"
                                                className="obj-interact-btn secondary"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleInspect(obj);
                                                }}
                                            >
                                                👁️ {language === 'ru' ? 'Осмотреть' : 'Inspect'}
                                            </button>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
