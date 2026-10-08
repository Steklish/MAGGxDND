import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useGameStore } from '../store/gameStore';
import { ChatPanel } from '../components/ChatPanel';
import { SceneViewer } from '../components/SceneViewer';
import { CharacterPanel } from '../components/CharacterPanel';
import { SceneMenu } from '../components/SceneMenu';
import { TurnQueue } from '../components/TurnQueue';
import { Tooltip } from '../components/common/Tooltip';
import { VectorIcon } from '../components/common/VectorIcon';
import { useTranslation } from '../i18n/useTranslation';
import { handleTiltAndHighlight, handleTiltReset } from '../utils/cardTilt';
import api from '../services/api';
import './GamePage.css';

export const GamePage: React.FC = () => {
    const { sessionId } = useParams<{ sessionId: string }>();
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const { t } = useTranslation();

    const {
        username,
        activeCharacter,
        currentSession,
        currentScene,
        language,
        setActiveCharacter,
        setCurrentSession,
        setCurrentScene,
        setTurnQueue,
        connectWebSocket,
        disconnectWebSocket,
        isDMThinking,
        setLanguage,
    } = useGameStore();

    // Layout and panel state
    const [layoutMode, setLayoutMode] = useState<'story' | 'split' | 'map'>('story');
    const [panelOrder, setPanelOrder] = useState<['chronicle' | 'map', 'chronicle' | 'map']>(['chronicle', 'map']);
    const [isChronicleFolded, setIsChronicleFolded] = useState<boolean>(false);
    const [isMapFolded, setIsMapFolded] = useState<boolean>(false);
    const [splitPercent, setSplitPercent] = useState<number>(55);
    const [isResizing, setIsResizing] = useState<boolean>(false);

    // Collapsible side tabs: 'codex' | 'scene' | 'quests' | null
    const [activeSideTab, setActiveSideTab] = useState<'codex' | 'scene' | 'quests' | null>(null);

    const [expandQuests, setExpandQuests] = useState<boolean>(false);
    const [isRehydrating, setIsRehydrating] = useState<boolean>(true);
    const [wsConnected, setWsConnected] = useState<boolean>(false);
    const [roster, setRoster] = useState<any[]>([]);

    const activeCharName = searchParams.get('character') ||
        localStorage.getItem('active_character_name') ||
        activeCharacter?.name ||
        '';

    const playerName = username || localStorage.getItem('username') || 'Adventurer';

    // Rehydrate session & character state on load/refresh
    const rehydrateSession = useCallback(async () => {
        if (!sessionId) {
            navigate('/lobby');
            return;
        }

        setIsRehydrating(true);
        try {
            const [sessionResp, gameInfoResp, rosterData] = await Promise.all([
                api.get(`/sessions/${sessionId}`).catch(err => {
                    console.warn('Session detail fetch error:', err);
                    return { data: null };
                }),
                api.get(`/sessions/${sessionId}/game_info`).catch(err => {
                    console.warn('game_info fetch error:', err);
                    return { data: null };
                }),
                api.get(`/sessions/${sessionId}/roster`).then(r => r.data).catch(() => []),
            ]);

            const fullSession = sessionResp.data;
            const gameInfo = gameInfoResp.data;

            if (fullSession) {
                setCurrentSession(fullSession);
            }

            // Sync locked session language
            const sessionLang = fullSession?.language || gameInfo?.language || currentSession?.language;
            if (sessionLang === 'ru' || sessionLang === 'en') {
                setLanguage(sessionLang);
            }

            // Sync current scene
            const activeScene = fullSession?.current_scene || gameInfo?.current_scene;
            if (activeScene) {
                setCurrentScene(activeScene);
            }

            // Sync turn queue
            const queue = fullSession?.turn_queue || gameInfo?.turn_queue || [];
            if (Array.isArray(queue) && queue.length > 0) {
                setTurnQueue(queue);
            }

            // Sync party roster
            if (Array.isArray(rosterData) && rosterData.length > 0) {
                setRoster(rosterData);
            }

            // Reconcile active character
            const targetCharName = searchParams.get('character') ||
                localStorage.getItem('active_character_name') ||
                '';

            let foundChar: any = null;
            const allCandidates: any[] = [
                ...(fullSession?.players || []).map((p: any) => p?.character || p),
                ...(gameInfo?.players || []).map((p: any) => p?.character || p),
                ...(Array.isArray(rosterData) ? rosterData.map((r: any) => r?.character || r) : []),
            ];

            if (targetCharName) {
                foundChar = allCandidates.find((c: any) =>
                    c?.name?.toLowerCase() === targetCharName.toLowerCase()
                );
            }

            if (!foundChar && allCandidates.length > 0) {
                foundChar = allCandidates[0];
            }

            if (foundChar) {
                setActiveCharacter(foundChar);
                if (foundChar.name) {
                    localStorage.setItem('active_character_name', foundChar.name);
                }
            }

            // Connect WebSocket
            const playerId = localStorage.getItem('player_id') || localStorage.getItem('userId') || playerName;
            await connectWebSocket(sessionId, playerId);
            setWsConnected(true);

        } catch (error) {
            console.error('Rehydration error:', error);
        } finally {
            setIsRehydrating(false);
        }
    }, [sessionId, playerName, navigate, setCurrentSession, setCurrentScene, setTurnQueue, setActiveCharacter, connectWebSocket, searchParams]);

    useEffect(() => {
        const token = localStorage.getItem('access_token');
        if (!token) {
            navigate('/login');
            return;
        }
        rehydrateSession();

        return () => {
            disconnectWebSocket();
        };
    }, [sessionId]);

    // Resizing panels logic
    const handleResizerMouseDown = (e: React.MouseEvent) => {
        e.preventDefault();
        setIsResizing(true);
    };

    useEffect(() => {
        if (!isResizing) return;
        const handleMouseMove = (e: MouseEvent) => {
            const stage = document.querySelector('.game-main-stage');
            if (!stage) return;
            const rect = stage.getBoundingClientRect();
            const relativeX = e.clientX - rect.left;
            const percent = Math.max(20, Math.min(80, (relativeX / rect.width) * 100));
            setSplitPercent(panelOrder[0] === 'chronicle' ? percent : 100 - percent);
        };
        const handleMouseUp = () => setIsResizing(false);

        window.addEventListener('mousemove', handleMouseMove);
        window.addEventListener('mouseup', handleMouseUp);
        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isResizing, panelOrder]);

    const handleSwapPanels = () => {
        setPanelOrder(prev => [prev[1], prev[0]]);
    };

    const sessionTitle = currentSession?.session_name || 'Campaign Realm';
    const sceneTitle = currentScene?.name || 'Tactical Arena';

    const currentChapter = (currentSession as any)?.current_chapter || (currentSession as any)?.plot?.current_chapter;
    const tasks = currentChapter?.tasks || {};
    const taskEntries = Object.entries(tasks);
    const totalTasks = taskEntries.length;
    const tasksCompleted = taskEntries.filter(([_, done]) => Boolean(done)).length;
    const nextIncompleteTask = taskEntries.find(([_, done]) => !done)?.[0];

    // Render individual draggable and foldable panel
    const renderPanel = (type: 'chronicle' | 'map') => {
        if (type === 'chronicle') {
            const isFolded = isChronicleFolded;
            const flexValue = isFolded ? '0 0 42px' : isMapFolded ? '1 1 100%' : `${splitPercent}%`;

            return (
                <section
                    key="chronicle-panel"
                    className={`draggable-panel stage-chronicle-wrapper ${isFolded ? 'is-folded' : ''}`}
                    style={{ flex: flexValue }}
                >
                    <div className="panel-tab-bar">
                        <div
                            className="panel-drag-handle"
                            title={language === 'ru' ? 'Сменить расположение панелей' : 'Drag or click to swap panel order'}
                            onClick={handleSwapPanels}
                        >
                            <span className="drag-grip">⋮⋮</span>
                            <span className="panel-tab-title"><VectorIcon name="banner" /> {language === 'ru' ? 'Летопись' : 'Chronicle'}</span>
                        </div>
                        <div className="panel-tab-actions">
                            <button
                                type="button"
                                className="panel-tool-btn"
                                onClick={handleSwapPanels}
                                title={language === 'ru' ? 'Поменять с тактической картой' : 'Swap with Battle Map'}
                            >
                                ⇄
                            </button>
                            <button
                                type="button"
                                className="panel-tool-btn"
                                onClick={() => setIsChronicleFolded(!isChronicleFolded)}
                                title={isFolded ? (language === 'ru' ? 'Развернуть летопись' : 'Expand Chronicle') : (language === 'ru' ? 'Свернуть летопись' : 'Fold Chronicle')}
                            >
                                {isFolded ? '▼' : '▲'}
                            </button>
                        </div>
                    </div>
                    {!isFolded && (
                        <div className="panel-content-body">
                            <ChatPanel />
                        </div>
                    )}
                </section>
            );
        }

        const isFolded = isMapFolded;
        const flexValue = isFolded ? '0 0 42px' : isChronicleFolded ? '1 1 100%' : `${100 - splitPercent}%`;

        return (
            <section
                key="map-panel"
                className={`draggable-panel stage-map-wrapper ${isFolded ? 'is-folded' : ''}`}
                style={{ flex: flexValue }}
            >
                <div className="panel-tab-bar">
                    <div
                        className="panel-drag-handle"
                        title={language === 'ru' ? 'Сменить расположение панелей' : 'Drag or click to swap panel order'}
                        onClick={handleSwapPanels}
                    >
                        <span className="drag-grip">⋮⋮</span>
                        <span className="panel-tab-title"><VectorIcon name="gate" /> {language === 'ru' ? 'Тактическая Карта' : 'Battle Grid'}</span>
                    </div>
                    <div className="panel-tab-actions">
                        <button
                            type="button"
                            className="panel-tool-btn"
                            onClick={handleSwapPanels}
                            title={language === 'ru' ? 'Поменять с летописью' : 'Swap with Chronicle'}
                        >
                            ⇄
                        </button>
                        <button
                            type="button"
                            className="panel-tool-btn"
                            onClick={() => setIsMapFolded(!isMapFolded)}
                            title={isFolded ? (language === 'ru' ? 'Развернуть карту' : 'Expand Battle Map') : (language === 'ru' ? 'Свернуть карту' : 'Fold Battle Map')}
                        >
                            {isFolded ? '▼' : '▲'}
                        </button>
                    </div>
                </div>
                {!isFolded && (
                    <div className="panel-content-body">
                        <SceneViewer />
                    </div>
                )}
            </section>
        );
    };

    return (
        <div className="game-screen-container">
            {/* Unified Sleek Top Tactical Bar */}
            <div className="game-top-bar" data-testid="game-top-bar">
                <div className="top-bar-left">
                    <button
                        type="button"
                        className="compact-nav-btn"
                        onClick={() => navigate('/lobby')}
                        title={language === 'ru' ? 'Вернуться в зал кампаний' : 'Return to Main Campaign Lobby'}
                    >
                        ← {t.nav.lobby}
                    </button>

                    <div className="compact-session-badge" title={sessionTitle}>
                        <VectorIcon name="castle" />
                        <span className="compact-badge-text">{sessionTitle}</span>
                    </div>

                    <button
                        type="button"
                        className={`compact-scene-pill ${activeSideTab === 'scene' ? 'active' : ''}`}
                        onClick={() => setActiveSideTab(activeSideTab === 'scene' ? null : 'scene')}
                        title={language === 'ru' ? 'Осмотреть досье сцены' : 'Inspect Scene Dossier'}
                    >
                        <VectorIcon name="tower" />
                        <span className="compact-badge-text">{sceneTitle}</span>
                    </button>
                </div>

                <div className="top-bar-center">
                    <TurnQueue />
                    {isDMThinking && (
                        <div className="dm-resolving-indicator" data-testid="dm-thinking-indicator">
                            <span className="spinner-dot" />
                            <span>{t.game.dmThinking}</span>
                        </div>
                    )}
                </div>

                <div className="top-bar-right">
                    <div className="compact-layout-pills">
                        <button
                            type="button"
                            className={`layout-pill ${layoutMode === 'story' ? 'active' : ''}`}
                            onClick={() => {
                                setLayoutMode('story');
                                setIsChronicleFolded(false);
                                setSplitPercent(65);
                            }}
                            title={language === 'ru' ? 'Режим Сюжета: Летопись в приоритете' : 'Story Mode: Chronicle takes priority'}
                        >
                            <VectorIcon name="banner" />
                            <span className="pill-text">{t.game.storyFocus}</span>
                        </button>
                        <button
                            type="button"
                            className={`layout-pill ${layoutMode === 'split' ? 'active' : ''}`}
                            onClick={() => {
                                setLayoutMode('split');
                                setIsChronicleFolded(false);
                                setIsMapFolded(false);
                                setSplitPercent(50);
                            }}
                            title={language === 'ru' ? 'Сбалансированный режим: Разделенный экран' : 'Balanced Tactical: Split Screen'}
                        >
                            <VectorIcon name="shield-checked" />
                            <span className="pill-text">{t.game.splitView}</span>
                        </button>
                        <button
                            type="button"
                            className={`layout-pill ${layoutMode === 'map' ? 'active' : ''}`}
                            onClick={() => {
                                setLayoutMode('map');
                                setIsMapFolded(false);
                                setSplitPercent(35);
                            }}
                            title={language === 'ru' ? 'Тактическая карта: Увеличенная сетка поля боя' : 'Tactical Map Focus: Enlarged Battle Grid'}
                        >
                            <VectorIcon name="gate" />
                            <span className="pill-text">{t.game.mapFocus}</span>
                        </button>
                    </div>

                    <Tooltip
                        content={
                            language === 'ru'
                                ? 'Язык кампании зафиксирован при создании (Русский)'
                                : 'Campaign language is locked for this session (English)'
                        }
                        position="bottom"
                    >
                        <div className="locked-session-language-badge" data-testid="locked-session-language">
                            <span className="locked-lang-text">{language.toUpperCase()}</span>
                            <span className="locked-lang-icon">🔒</span>
                        </div>
                    </Tooltip>

                    <button
                        type="button"
                        className={`compact-hero-btn ${activeSideTab === 'codex' ? 'active' : ''}`}
                        onClick={() => setActiveSideTab(activeSideTab === 'codex' ? null : 'codex')}
                        title={language === 'ru' ? 'Открыть кодекс героя' : 'Open Hero Codex Side Tab'}
                    >
                        <span className="hero-btn-glyph"><VectorIcon name="shield" /></span>
                        <span className="hero-btn-name">{activeCharacter?.name || (language === 'ru' ? 'Кодекс' : 'Hero')}</span>
                        <span className="hero-btn-hp">
                            {activeCharacter?.current_hp ?? 10}/{activeCharacter?.max_hp ?? 10} HP
                        </span>
                    </button>
                </div>
            </div>

            {/* Quest & Chapter Progression Banner (Foldable) */}
            {currentChapter && (
                <div className="quest-progression-bar" data-testid="quest-progression-bar">
                    <div className="quest-header-row" onClick={() => setExpandQuests(!expandQuests)}>
                        <div className="quest-title-badge">
                            <span className="quest-scroll-icon">📜</span>
                            <span className="chapter-label">{currentChapter.name || t.game.currentChapter}</span>
                            <span className="quest-status-pill">{tasksCompleted}/{totalTasks} {t.game.objectives}</span>
                        </div>
                        <div className="quest-toggle-prompt">
                            <span className="quest-progress-preview">
                                {nextIncompleteTask ? `${language === 'ru' ? 'Цель:' : 'Next:'} ${nextIncompleteTask}` : `${t.game.allCompleted} 🎉`}
                            </span>
                            <span className="expand-indicator">{expandQuests ? `▲ ${t.game.hideQuests}` : `▼ ${t.game.viewQuests}`}</span>
                        </div>
                    </div>

                    {expandQuests && (
                        <div className="quest-drawer-content">
                            {currentChapter.description && (
                                <p className="chapter-synopsis">{currentChapter.description}</p>
                            )}
                            <div className="quest-task-checklist">
                                {taskEntries.map(([task, isDone]: [string, any], idx: number) => (
                                    <div key={idx} className={`quest-task-item ${isDone ? 'completed' : 'pending'}`}>
                                        <span className="task-checkbox">{isDone ? '✓' : '○'}</span>
                                        <span className="task-label">{task}</span>
                                        {isDone && <span className="task-done-badge">{t.game.completed}</span>}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Main Stage: Narrative Chronicle & Tactical Grid (Draggable & Foldable) */}
            <div className="game-stage-wrapper-with-dock">
                <main className={`game-main-stage layout-${layoutMode} ${isResizing ? 'is-resizing' : ''}`}>
                    {renderPanel(panelOrder[0])}

                    {/* Draggable Divider Handle */}
                    {!isChronicleFolded && !isMapFolded && (
                        <div
                            className={`panel-resizer-line ${isResizing ? 'resizing' : ''}`}
                            onMouseDown={handleResizerMouseDown}
                            title={language === 'ru' ? 'Тяните для изменения размера панелей' : 'Drag to resize panels'}
                        >
                            <div className="resizer-nub" />
                        </div>
                    )}

                    {renderPanel(panelOrder[1])}
                </main>

                {/* Medieval Persistent Side Tab Dock */}
                <aside className="game-side-dock">
                    <Tooltip content={language === 'ru' ? 'Кодекс героя и лист персонажа' : 'Hero Codex & Character Sheet'} position="left">
                        <button
                            type="button"
                            className={`side-dock-btn ${activeSideTab === 'codex' ? 'active' : ''} reveal-highlight`}
                            onClick={() => setActiveSideTab(activeSideTab === 'codex' ? null : 'codex')}
                            onMouseMove={handleTiltAndHighlight}
                            onMouseLeave={handleTiltReset}
                        >
                            <VectorIcon name="shield" />
                            <span className="dock-btn-label">{language === 'ru' ? 'Герой' : 'Codex'}</span>
                        </button>
                    </Tooltip>

                    <Tooltip content={language === 'ru' ? 'Досье сцены и интерактивные объекты' : 'Scene Dossier & Interactive Objects'} position="left">
                        <button
                            type="button"
                            className={`side-dock-btn ${activeSideTab === 'scene' ? 'active' : ''} reveal-highlight`}
                            onClick={() => setActiveSideTab(activeSideTab === 'scene' ? null : 'scene')}
                            onMouseMove={handleTiltAndHighlight}
                            onMouseLeave={handleTiltReset}
                        >
                            <VectorIcon name="tower" />
                            <span className="dock-btn-label">{language === 'ru' ? 'Сцена' : 'Scene'}</span>
                            {(currentScene?.objects?.length ?? 0) > 0 && (
                                <span className="dock-badge">{currentScene?.objects?.length}</span>
                            )}
                        </button>
                    </Tooltip>

                    <Tooltip content={language === 'ru' ? 'Задания главы и прогресс сюжета' : 'Chapter Quests & Plot Progress'} position="left">
                        <button
                            type="button"
                            className={`side-dock-btn ${activeSideTab === 'quests' ? 'active' : ''} reveal-highlight`}
                            onClick={() => setActiveSideTab(activeSideTab === 'quests' ? null : 'quests')}
                            onMouseMove={handleTiltAndHighlight}
                            onMouseLeave={handleTiltReset}
                        >
                            <span className="dock-emoji-icon">📜</span>
                            <span className="dock-btn-label">{language === 'ru' ? 'Квесты' : 'Quests'}</span>
                            {totalTasks > 0 && (
                                <span className="dock-badge">{tasksCompleted}/{totalTasks}</span>
                            )}
                        </button>
                    </Tooltip>
                </aside>

                {/* Collapsible Slide-out Side Tab Drawer */}
                {activeSideTab && (
                    <div className="side-drawer-container">
                        <div className="side-drawer-header">
                            <div className="drawer-title-group">
                                <span>
                                    {activeSideTab === 'codex' && <><VectorIcon name="shield" /> {language === 'ru' ? 'Кодекс Героя' : 'Adventurer Codex'}</>}
                                    {activeSideTab === 'scene' && <><VectorIcon name="tower" /> {language === 'ru' ? 'Досье Сцены' : 'Scene Dossier'}</>}
                                    {activeSideTab === 'quests' && <>📜 {language === 'ru' ? 'Задания Главы' : 'Chapter Quests'}</>}
                                </span>
                            </div>
                            <button
                                type="button"
                                className="close-drawer-btn"
                                onClick={() => setActiveSideTab(null)}
                                title={language === 'ru' ? 'Закрыть панель' : 'Close Drawer'}
                            >
                                ✕
                            </button>
                        </div>
                        <div className="side-drawer-body">
                            {activeSideTab === 'codex' && <CharacterPanel />}
                            {activeSideTab === 'scene' && <SceneMenu onClose={() => setActiveSideTab(null)} />}
                            {activeSideTab === 'quests' && (
                                <div className="side-quest-content">
                                    {currentChapter?.description && (
                                        <p className="chapter-synopsis">{currentChapter.description}</p>
                                    )}
                                    <div className="quest-task-checklist">
                                        {taskEntries.map(([task, isDone]: [string, any], idx: number) => (
                                            <div key={idx} className={`quest-task-item ${isDone ? 'completed' : 'pending'}`}>
                                                <span className="task-checkbox">{isDone ? '✓' : '○'}</span>
                                                <span className="task-label">{task}</span>
                                                {isDone && <span className="task-done-badge">COMPLETED</span>}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
