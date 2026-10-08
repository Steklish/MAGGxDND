import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGameStore } from '../store/gameStore';
import sessionAPI, { GameSession } from '../services/sessionAPI';
import { VectorIcon, IconName } from '../components/common/VectorIcon';
import { LanguageSelector } from '../components/common/LanguageSelector';
import { useTranslation } from '../i18n/useTranslation';
import './LobbyPage.css';

interface PresetAdventure {
    name: { en: string; ru: string };
    prompt: { en: string; ru: string };
    icon: IconName;
}

const PRESET_ADVENTURES: PresetAdventure[] = [
    {
        name: { en: 'Citadel of Shadows', ru: 'Цитадель Теней' },
        prompt: {
            en: 'A ruined obsidian fortress overgrown with cursed briars. Goblins and dark cultists guard an ancient forgotten artifact.',
            ru: 'Разрушенная обсидиановая крепость, заросшая проклятым терновником. Гоблины и темные культисты охраняют древний забытый артефакт.'
        },
        icon: 'castle'
    },
    {
        name: { en: 'Whispering Caverns', ru: 'Шепчущие Пещеры' },
        prompt: {
            en: 'Luminescent fungi illuminate subterranean tunnels where a sleeping serpent dragon rests upon a hoard of gold.',
            ru: 'Светящиеся грибы освещают подземные туннели, где спящий змеевидный дракон покоится на горе золота.'
        },
        icon: 'swirl'
    },
    {
        name: { en: 'Sunken Crypts of Aethelgard', ru: 'Затопленные Склепы Этельгарда' },
        prompt: {
            en: 'Flooded stone catacombs haunted by skeleton warriors and eerie will-o-wisps hovering over murky waters.',
            ru: 'Затопленные каменные катакомбы, где бродят скелеты-воины и зловещие блуждающие огни над мутными водами.'
        },
        icon: 'helm'
    },
    {
        name: { en: 'The Rusty Tankard Brawl', ru: 'Потасовка в Ржавой Кружке' },
        prompt: {
            en: 'A rowdy dwarven tavern where a drunken brawl between mercenary guilds erupts into an unexpected magical mystery.',
            ru: 'Шумная дварфийская таверна, где пьяная драка между гильдиями наемников перерастает в неожиданную магическую тайну.'
        },
        icon: 'axe'
    }
];

export const LobbyPage: React.FC = () => {
    const navigate = useNavigate();
    const { username, logout, language } = useGameStore();
    const { t } = useTranslation();

    const [sessions, setSessions] = useState<GameSession[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    // Modal state for creating a new adventure
    const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);
    const [newSessionName, setNewSessionName] = useState<string>('');
    const [newSessionPrompt, setNewSessionPrompt] = useState<string>('');
    const [campaignLang, setCampaignLang] = useState<'ru' | 'en'>(language);
    const [isCreating, setIsCreating] = useState<boolean>(false);

    useEffect(() => {
        setCampaignLang(language);
    }, [language]);

    const displayName = username || localStorage.getItem('username') || t.nav.adventurer;

    const fetchSessions = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await sessionAPI.listSessions();
            setSessions(data.sessions || []);
        } catch (err: any) {
            console.error('Failed to load campaigns:', err);
            setError('Could not fetch active campaigns. Backend may be offline or initializing.');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        const token = localStorage.getItem('access_token');
        if (!token) {
            navigate('/login');
            return;
        }
        fetchSessions();
    }, [navigate]);

    const handleCreateAdventure = async (e: React.FormEvent) => {
        e.preventDefault();
        const defaultName = campaignLang === 'ru' ? `Приключение искателя ${displayName}` : `Adventure of ${displayName}`;
        const defaultPrompt = campaignLang === 'ru'
            ? 'Таинственный зал подземелья с мерцающими факелами и древними каменными арками.'
            : 'A mysterious dungeon chamber with flickering torches and ancient stone arches.';

        const sessionName = newSessionName.trim() || defaultName;
        const scenePrompt = newSessionPrompt.trim() || defaultPrompt;

        setIsCreating(true);
        try {
            const created = await sessionAPI.createSession({
                session_name: sessionName,
                scene_prompt: scenePrompt,
                description: scenePrompt,
                language: campaignLang,
                character_prompts: campaignLang === 'ru' ? [
                    'Валерос Воин, тяжело бронированный боец с полуторным мечом и щитом',
                    'Фэй Плутовка, скрытная разведчица с парными кинжалами и отмычками'
                ] : [
                    'Valeros the Fighter, heavily armored warrior with a broadsword',
                    'Faye the Rogue, stealthy scout with dual daggers and lockpicks'
                ],
                npc_prompts: campaignLang === 'ru' ? [
                    'Гоблин-разведчик, ловкий стрелок, прячущийся в тенях'
                ] : [
                    'Goblin Skirmisher, nimble ambush attacker lurking in corners'
                ]
            });

            setIsCreateModalOpen(false);
            setNewSessionName('');
            setNewSessionPrompt('');

            // Navigate directly to the session entrance / character claim page
            navigate(`/session/${created.session_id}`);
        } catch (err: any) {
            console.error('Failed to create session:', err);
            setError(err.response?.data?.detail || 'Failed to create campaign.');
        } finally {
            setIsCreating(false);
        }
    };

    const handleQuickAdventure = async () => {
        const randomPreset = PRESET_ADVENTURES[Math.floor(Math.random() * PRESET_ADVENTURES.length)];
        const presetName = language === 'ru' ? randomPreset.name.ru : randomPreset.name.en;
        const presetPrompt = language === 'ru' ? randomPreset.prompt.ru : randomPreset.prompt.en;

        setIsCreating(true);
        try {
            const created = await sessionAPI.createSession({
                session_name: `${presetName} #${Math.floor(Math.random() * 900 + 100)}`,
                scene_prompt: presetPrompt,
                description: presetPrompt,
                language: language,
                character_prompts: language === 'ru' ? [
                    'Валерос Храбрый, опытный ветеран битв с тяжелым щитом и мечом',
                    'Элдрин Маг, мудрый чародей со светящимся посохом огня'
                ] : [
                    'Valeros the Brave, battle-tested warrior with heavy shield and longsword',
                    'Eldrin the Mage, wise wizard carrying a glowing staff of arcane embers'
                ],
                npc_prompts: language === 'ru' ? [
                    'Пещерный Зверь, крадущийся хищник теней с острыми клыками'
                ] : [
                    'Cavern Beast, lurking shadow stalker with razor claws'
                ]
            });

            navigate(`/session/${created.session_id}`);
        } catch (err: any) {
            console.error('Quick adventure error:', err);
            setError('Failed to initiate quick adventure.');
        } finally {
            setIsCreating(false);
        }
    };

    const handleLogout = () => {
        logout();
        localStorage.clear();
        navigate('/login');
    };

    return (
        <div className="lobby-container">
            {/* Top Navigation */}
            <header className="lobby-navbar">
                <div className="lobby-brand" onClick={() => navigate('/lobby')}>
                    <span className="brand-glyph"><VectorIcon name="rune" /></span>
                    <span className="brand-title">MAGGxDND</span>
                    <span className="brand-version">2.0</span>
                </div>

                <div className="lobby-user-bar">
                    <LanguageSelector />
                    <div className="user-profile-badge">
                        <span className="user-avatar-glyph"><VectorIcon name="knight" /></span>
                        <div className="user-meta">
                            <span className="user-name">{displayName}</span>
                            <span className="user-role">{t.nav.adventurer}</span>
                        </div>
                    </div>
                    <button
                        type="button"
                        className="lobby-logout-btn"
                        onClick={handleLogout}
                        title={t.nav.logout}
                    >
                        {t.nav.logout}
                    </button>
                </div>
            </header>

            {/* Main Content Area */}
            <main className="lobby-main">
                {/* Hero Header */}
                <section className="lobby-hero">
                    <div className="hero-text-block">
                        <h1 className="hero-heading">{language === 'ru' ? `Добро пожаловать, ${displayName}` : `Welcome, ${displayName}`}</h1>
                        <p className="hero-subtext">{t.lobby.subtitle}</p>
                    </div>

                    <div className="hero-cta-group">
                        <button
                            type="button"
                            className="hero-btn quick-start-btn"
                            onClick={handleQuickAdventure}
                            disabled={isCreating}
                        >
                            <span className="btn-icon"><VectorIcon name="horse" /></span>
                            <span>{isCreating ? t.lobby.forging : (language === 'ru' ? '1-Клик Быстрое Приключение' : '1-Click Quick Adventure')}</span>
                        </button>
                        <button
                            type="button"
                            className="hero-btn create-adventure-btn"
                            onClick={() => setIsCreateModalOpen(true)}
                        >
                            <span className="btn-icon"><VectorIcon name="banner" /></span>
                            <span>{t.lobby.createAdventure}</span>
                        </button>
                    </div>
                </section>

                {error && (
                    <div className="lobby-alert-error">
                        <span>{error}</span>
                        <button type="button" onClick={() => setError(null)}>✕</button>
                    </div>
                )}

                {/* Campaign Sessions Explorer */}
                <section className="campaigns-section">
                    <div className="campaigns-header-row">
                        <div className="section-title-wrap">
                            <h2 className="section-title">{t.lobby.activeCampaigns}</h2>
                            <span className="campaign-count-badge">{sessions.length} {language === 'ru' ? 'Доступно' : 'Available'}</span>
                        </div>
                        <button
                            type="button"
                            className="refresh-btn"
                            onClick={fetchSessions}
                            disabled={isLoading}
                        >
                            {isLoading ? (language === 'ru' ? 'Обновление...' : 'Refreshing...') : <><VectorIcon name="rune-circle" /> {language === 'ru' ? 'Обновить' : 'Refresh List'}</>}
                        </button>
                    </div>

                    {isLoading ? (
                        <div className="campaigns-loading">
                            <div className="loading-spinner" />
                            <p>{language === 'ru' ? 'Поиск активных измерений подземелий...' : 'Scrying active dungeon realms...'}</p>
                        </div>
                    ) : sessions.length === 0 ? (
                        <div className="campaigns-empty">
                            <span className="empty-icon"><VectorIcon name="castle" size="2.6rem" /></span>
                            <h3>{t.lobby.noCampaigns}</h3>
                            <p>{language === 'ru' ? 'Станьте героем этого мира и создайте первое приключение.' : 'Be the hero this world needs and create the first adventure.'}</p>
                            <button
                                type="button"
                                className="empty-action-btn"
                                onClick={() => setIsCreateModalOpen(true)}
                            >
                                <VectorIcon name="banner" /> {t.lobby.forgeBtn}
                            </button>
                        </div>
                    ) : (
                        <div className="campaigns-grid">
                            {sessions.map((sess) => {
                                const id = sess.session_id;
                                const isReady = sess.status === 'in_game' || sess.status === 'active';
                                return (
                                    <div key={id} className="campaign-card">
                                        <div className="campaign-card-header">
                                            <div className="campaign-title-wrap">
                                                <h3 className="campaign-name">{sess.session_name || (language === 'ru' ? 'Безымянный мир' : 'Unnamed Realm')}</h3>
                                                <span className={`status-pill ${isReady ? 'active' : 'waiting'}`}>
                                                    {isReady ? (language === 'ru' ? 'Идет игра' : 'Active Game') : (language === 'ru' ? 'В лобби' : 'In Lobby')}
                                                </span>
                                            </div>
                                            <span className="campaign-mode">{sess.game_mode || 'D&D 5e'}</span>
                                        </div>

                                        <p className="campaign-desc">
                                            {sess.description || (language === 'ru' ? 'Опасный рубеж, ждущий храбрых душ.' : 'A dangerous frontier awaiting brave souls.')}
                                        </p>

                                        <div className="campaign-footer">
                                            <div className="campaign-meta">
                                                <span className="meta-item">
                                                    <VectorIcon name="knight" /> <strong>{sess.player_count || 1}</strong> {t.lobby.playersCount}
                                                </span>
                                            </div>

                                            <button
                                                type="button"
                                                className="enter-campaign-btn"
                                                onClick={() => navigate(`/session/${id}`)}
                                            >
                                                <span><VectorIcon name="sword" /> {t.lobby.enterCampaign}</span>
                                                <span className="btn-arrow">→</span>
                                            </button>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </section>
            </main>

            {/* Create Campaign Modal */}
            {isCreateModalOpen && (
                <div className="modal-backdrop" onClick={() => setIsCreateModalOpen(false)}>
                    <div className="modal-card" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <div className="modal-title-group">
                                <span className="modal-icon"><VectorIcon name="banner" /></span>
                                <h3>{t.lobby.modalTitle}</h3>
                            </div>
                            <button
                                type="button"
                                className="modal-close-btn"
                                onClick={() => setIsCreateModalOpen(false)}
                            >
                                ✕
                            </button>
                        </div>

                        <form onSubmit={handleCreateAdventure} className="modal-form">
                            <div className="form-group">
                                <label htmlFor="session-name">{t.lobby.campaignName}</label>
                                <input
                                    id="session-name"
                                    type="text"
                                    placeholder={t.lobby.campaignNamePlaceholder}
                                    value={newSessionName}
                                    onChange={(e) => setNewSessionName(e.target.value)}
                                    autoFocus
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="session-prompt">{t.lobby.scenePrompt}</label>
                                <textarea
                                    id="session-prompt"
                                    rows={3}
                                    placeholder={t.lobby.scenePromptPlaceholder}
                                    value={newSessionPrompt}
                                    onChange={(e) => setNewSessionPrompt(e.target.value)}
                                />
                            </div>

                            {/* Campaign Global Language Selection (Locked after creation) */}
                            <div className="form-group campaign-lang-group">
                                <label>
                                    {language === 'ru' ? 'Язык кампании (фиксируется после создания)' : 'Campaign Language (Locked after creation)'}
                                </label>
                                <div className="campaign-lang-selector" role="radiogroup">
                                    <button
                                        type="button"
                                        className={`campaign-lang-btn ${campaignLang === 'ru' ? 'active' : ''}`}
                                        onClick={() => setCampaignLang('ru')}
                                    >
                                        <span className="lang-flag">🇷🇺</span>
                                        <span className="lang-title">Русский (RU)</span>
                                        {campaignLang === 'ru' && <span className="lang-check">✓</span>}
                                    </button>
                                    <button
                                        type="button"
                                        className={`campaign-lang-btn ${campaignLang === 'en' ? 'active' : ''}`}
                                        onClick={() => setCampaignLang('en')}
                                    >
                                        <span className="lang-flag">🇬🇧</span>
                                        <span className="lang-title">English (EN)</span>
                                        {campaignLang === 'en' && <span className="lang-check">✓</span>}
                                    </button>
                                </div>
                                <span className="campaign-lang-hint">
                                    {language === 'ru'
                                        ? '🔒 Язык повествования Мастера Подземелий, диалогов и сцен фиксируется и не может быть изменен во время игры.'
                                        : '🔒 Narrative language for DM storytelling, dialogues, and scenes is locked permanently once created.'}
                                </span>
                            </div>

                            <div className="preset-suggestions">
                                <span className="preset-label">{t.lobby.quickPresets}:</span>
                                <div className="preset-chips">
                                    {PRESET_ADVENTURES.map((p) => {
                                        const pName = campaignLang === 'ru' ? p.name.ru : p.name.en;
                                        const pPrompt = campaignLang === 'ru' ? p.prompt.ru : p.prompt.en;
                                        return (
                                            <button
                                                key={p.name.en}
                                                type="button"
                                                className="preset-chip"
                                                onClick={() => {
                                                    setNewSessionName(pName);
                                                    setNewSessionPrompt(pPrompt);
                                                }}
                                            >
                                                <VectorIcon name={p.icon} /> {pName}
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>

                            <div className="modal-actions">
                                <button
                                    type="button"
                                    className="modal-cancel-btn"
                                    onClick={() => setIsCreateModalOpen(false)}
                                >
                                    {t.lobby.cancelBtn}
                                </button>
                                <button
                                    type="submit"
                                    className="modal-submit-btn"
                                    disabled={isCreating}
                                >
                                    {isCreating ? t.lobby.forging : <><VectorIcon name="magic" /> {t.lobby.forgeBtn}</>}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};
