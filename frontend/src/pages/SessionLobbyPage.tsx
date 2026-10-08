import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useGameStore } from '../store/gameStore';
import sessionAPI from '../services/sessionAPI';
import api from '../services/api';
import { VectorIcon } from '../components/common/VectorIcon';
import { LanguageSelector } from '../components/common/LanguageSelector';
import { useTranslation } from '../i18n/useTranslation';
import './SessionLobbyPage.css';

interface RosterItem {
    name: string;
    char_class: string;
    race: string;
    level: number;
    current_hp: number;
    max_hp: number;
    armor_class: number;
    image_url?: string;
    is_occupied: boolean;
    is_ai_controlled: boolean;
    controller_name?: string;
    controller_id?: string;
    can_claim: boolean;
}

export const SessionLobbyPage: React.FC = () => {
    const { sessionId } = useParams<{ sessionId: string }>();
    const navigate = useNavigate();
    const { username, setActiveCharacter, setCurrentSession, language } = useGameStore();
    const { t } = useTranslation();

    const [sessionMeta, setSessionMeta] = useState<any>(null);
    const [roster, setRoster] = useState<RosterItem[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [claimingChar, setClaimingChar] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Roll new hero modal / drawer
    const [showNewHeroForm, setShowNewHeroForm] = useState<boolean>(false);
    const [heroName, setHeroName] = useState<string>('');
    const [heroClass, setHeroClass] = useState<string>('Fighter');
    const [heroRace, setHeroRace] = useState<string>('Human');
    const [isCreatingHero, setIsCreatingHero] = useState<boolean>(false);

    const playerName = username || localStorage.getItem('username') || t.nav.adventurer;

    const loadSessionData = useCallback(async () => {
        if (!sessionId) return;
        setIsLoading(true);
        setError(null);

        try {
            // Load session meta and roster in parallel
            const [metaResp, rosterData] = await Promise.all([
                api.get(`/sessions/${sessionId}`).catch(e => {
                    console.warn('Session detail error:', e);
                    return { data: { session_name: 'Dungeon Session', session_id: sessionId } };
                }),
                sessionAPI.getSessionRoster(sessionId).catch(e => {
                    console.warn('Roster fetch error:', e);
                    return [];
                })
            ]);

            setSessionMeta(metaResp.data);
            setCurrentSession(metaResp.data);
            setRoster(rosterData);
        } catch (err: any) {
            console.error('Failed to load session:', err);
            setError('Could not load session roster. Backend might be restarting.');
        } finally {
            setIsLoading(false);
        }
    }, [sessionId, setCurrentSession]);

    useEffect(() => {
        const token = localStorage.getItem('access_token');
        if (!token) {
            navigate('/login');
            return;
        }
        loadSessionData();
        // Periodically refresh roster every 6 seconds to show dynamic online/offline players
        const interval = setInterval(() => {
            if (sessionId) {
                sessionAPI.getSessionRoster(sessionId)
                    .then(data => setRoster(data))
                    .catch(() => {});
            }
        }, 6000);

        return () => clearInterval(interval);
    }, [loadSessionData, sessionId]);

    const handleClaimCharacter = async (char: RosterItem) => {
        if (!sessionId) return;
        setClaimingChar(char.name);
        setError(null);

        try {
            const claimResp: any = await sessionAPI.claimCharacter(sessionId, {
                character_name: char.name,
                player_name: playerName
            });

            if (claimResp && claimResp.player_id) {
                localStorage.setItem('player_id', claimResp.player_id);
            }

            // Update Zustand store and persist selection for refresh resilience
            const claimedCharObj = {
                id: (char as any).id || Math.floor(Math.random() * 10000),
                name: char.name,
                char_class: char.char_class,
                race: char.race,
                level: char.level || 1,
                current_hp: char.current_hp || 10,
                max_hp: char.max_hp || 10,
                armor_class: char.armor_class || 10,
                image_url: char.image_url,
            };

            setActiveCharacter(claimedCharObj as any);
            localStorage.setItem('active_character_name', char.name);
            localStorage.setItem('active_session_id', sessionId);

            // Direct route to play!
            navigate(`/session/${sessionId}/play?character=${encodeURIComponent(char.name)}`);
        } catch (err: any) {
            console.error('Failed to claim character:', err);
            setError(err.response?.data?.detail || 'Failed to claim character. It may already be occupied.');
        } finally {
            setClaimingChar(null);
        }
    };

    const handleCreateNewHero = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!sessionId) return;

        const trimmedName = heroName.trim() || `Hero_${Math.floor(Math.random() * 900 + 100)}`;
        setIsCreatingHero(true);
        setError(null);

        try {
            // Join with new character
            const resp = await api.post(`/sessions/${sessionId}/players`, {
                player_name: playerName,
                character_name: trimmedName,
                character_prompt: `A Level 1 ${heroRace} ${heroClass} seeking renown and fortune.`
            });

            if (resp.data?.player_id) {
                localStorage.setItem('player_id', resp.data.player_id);
            }

            const newChar = {
                id: resp.data?.character_id || Math.floor(Math.random() * 10000),
                name: trimmedName,
                char_class: heroClass,
                race: heroRace,
                level: 1,
                current_hp: 12,
                max_hp: 12,
                armor_class: 14,
            };

            setActiveCharacter(newChar as any);
            localStorage.setItem('active_character_name', trimmedName);
            localStorage.setItem('active_session_id', sessionId);

            navigate(`/session/${sessionId}/play?character=${encodeURIComponent(trimmedName)}`);
        } catch (err: any) {
            console.error('Failed to add hero:', err);
            setError(err.response?.data?.detail || 'Failed to add hero to session.');
        } finally {
            setIsCreatingHero(false);
        }
    };

    return (
        <div className="session-lobby-container">
            {/* Top Navigation */}
            <header className="session-lobby-navbar">
                <button
                    type="button"
                    className="back-btn"
                    onClick={() => navigate('/lobby')}
                >
                    {t.nav.backToCampaigns}
                </button>

                <div className="session-nav-title">
                    <span className="realm-icon"><VectorIcon name="castle" /></span>
                    <span className="realm-name">{sessionMeta?.session_name || (language === 'ru' ? 'Игровой мир' : 'Campaign Realm')}</span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <LanguageSelector />
                    <div className="nav-adventurer-badge">
                        <span>{t.nav.adventurer}: <strong>{playerName}</strong></span>
                    </div>
                </div>
            </header>

            {/* Main Stage */}
            <main className="session-lobby-main">
                {/* Campaign Header Card */}
                <section className="campaign-brief-card">
                    <div className="brief-content">
                        <div className="brief-tag-row">
                            <span className="mode-badge">{sessionMeta?.game_mode || 'D&D 5e'}</span>
                            <span className="status-badge">{t.sessionLobby.activeSession}</span>
                        </div>
                        <h1 className="campaign-headline">{sessionMeta?.session_name || (language === 'ru' ? 'Игровая сессия' : 'Campaign Session')}</h1>
                        <p className="campaign-brief-desc">
                            {sessionMeta?.description || sessionMeta?.scene_prompt || t.sessionLobby.claimPrompt}
                        </p>
                    </div>

                    <div className="brief-actions">
                        <button
                            type="button"
                            className="create-hero-btn"
                            onClick={() => setShowNewHeroForm(!showNewHeroForm)}
                        >
                            {showNewHeroForm ? t.sessionLobby.closeForm : <><VectorIcon name="banner" /> {t.sessionLobby.rollNewHero}</>}
                        </button>
                    </div>
                </section>

                {error && (
                    <div className="session-alert-error">
                        <span>{error}</span>
                        <button type="button" onClick={() => setError(null)}>✕</button>
                    </div>
                )}

                {/* Create Hero Form (when expanded) */}
                {showNewHeroForm && (
                    <div className="new-hero-drawer">
                        <h3 className="drawer-title"><VectorIcon name="magic" /> {t.sessionLobby.rollNewHero}</h3>
                        <form onSubmit={handleCreateNewHero} className="hero-form-grid">
                            <div className="form-field">
                                <label htmlFor="hero-name">{t.sessionLobby.heroName}</label>
                                <input
                                    id="hero-name"
                                    type="text"
                                    placeholder={t.sessionLobby.heroNamePlaceholder}
                                    value={heroName}
                                    onChange={(e) => setHeroName(e.target.value)}
                                    autoFocus
                                />
                            </div>

                            <div className="form-field">
                                <label htmlFor="hero-class">{t.sessionLobby.heroClass}</label>
                                <select
                                    id="hero-class"
                                    value={heroClass}
                                    onChange={(e) => setHeroClass(e.target.value)}
                                >
                                    <option value="Fighter">{language === 'ru' ? 'Воин (Танк и оружие)' : 'Fighter (Martial Tank)'}</option>
                                    <option value="Rogue">{language === 'ru' ? 'Плут (Скрытность и криты)' : 'Rogue (Stealth & Crits)'}</option>
                                    <option value="Wizard">{language === 'ru' ? 'Волшебник (Тайная магия)' : 'Wizard (Arcane Spells)'}</option>
                                    <option value="Cleric">{language === 'ru' ? 'Жрец (Божественное исцеление)' : 'Cleric (Divine Healing)'}</option>
                                    <option value="Paladin">{language === 'ru' ? 'Паладин (Священная кара)' : 'Paladin (Holy Smite)'}</option>
                                    <option value="Ranger">{language === 'ru' ? 'Следопыт (Лучник-охотник)' : 'Ranger (Ranged Hunter)'}</option>
                                    <option value="Barbarian">{language === 'ru' ? 'Варвар (Ярость)' : 'Barbarian (Rage)'}</option>
                                </select>
                            </div>

                            <div className="form-field">
                                <label htmlFor="hero-race">{t.sessionLobby.heroRace}</label>
                                <select
                                    id="hero-race"
                                    value={heroRace}
                                    onChange={(e) => setHeroRace(e.target.value)}
                                >
                                    <option value="Human">{language === 'ru' ? 'Человек' : 'Human'}</option>
                                    <option value="Elf">{language === 'ru' ? 'Эльф' : 'Elf'}</option>
                                    <option value="Dwarf">{language === 'ru' ? 'Дварф' : 'Dwarf'}</option>
                                    <option value="Halfling">{language === 'ru' ? 'Полурослик' : 'Halfling'}</option>
                                    <option value="Dragonborn">{language === 'ru' ? 'Драконорожденный' : 'Dragonborn'}</option>
                                    <option value="Tiefling">{language === 'ru' ? 'Тифлинг' : 'Tiefling'}</option>
                                </select>
                            </div>

                            <div className="hero-form-actions">
                                <button
                                    type="submit"
                                    className="hero-submit-btn"
                                    disabled={isCreatingHero}
                                >
                                    {isCreatingHero ? (language === 'ru' ? 'Создание героя...' : 'Rolling Hero...') : <><VectorIcon name="sword" /> {t.sessionLobby.rollHeroBtn}</>}
                                </button>
                            </div>
                        </form>
                    </div>
                )}

                {/* Character Roster */}
                <section className="roster-section">
                    <div className="roster-header">
                        <div className="roster-title-wrap">
                            <h2 className="roster-title">{t.sessionLobby.partyRoster}</h2>
                            <span className="roster-counter">{roster.length} {language === 'ru' ? 'Персонажей' : 'Characters in Realm'}</span>
                        </div>
                        <span className="roster-info-pill">
                            <VectorIcon name="rune" /> {language === 'ru' ? 'ИИ автоматически управляет свободными спутниками' : 'AI pilots disconnected/unclaimed companions automatically'}
                        </span>
                    </div>

                    {isLoading ? (
                        <div className="roster-loading">
                            <div className="loading-spinner" />
                            <p>{language === 'ru' ? 'Загрузка состояния отряда...' : 'Loading party status and character controllers...'}</p>
                        </div>
                    ) : roster.length === 0 ? (
                        <div className="roster-empty">
                            <span className="empty-glyph"><VectorIcon name="shield" size="2.5rem" /></span>
                            <h3>{language === 'ru' ? 'В отряде пока нет персонажей' : 'No Characters in Session Yet'}</h3>
                            <p>{language === 'ru' ? 'Создайте первого искателя выше, чтобы войти в подземелье.' : 'Create the first adventurer above to embark into the dungeon.'}</p>
                            <button
                                type="button"
                                className="empty-create-btn"
                                onClick={() => setShowNewHeroForm(true)}
                            >
                                {t.sessionLobby.rollNewHero}
                            </button>
                        </div>
                    ) : (
                        <div className="roster-grid">
                            {roster.map((char) => {
                                const isClaiming = claimingChar === char.name;
                                const isSelf = char.controller_name === playerName;
                                const isAi = char.is_ai_controlled;
                                const isOccupiedByOther = char.is_occupied && !isSelf && !isAi;

                                return (
                                    <div
                                        key={char.name}
                                        className={`character-card ${isAi ? 'ai-controlled' : ''} ${isOccupiedByOther ? 'occupied' : ''} ${isSelf ? 'controlled-by-self' : ''}`}
                                    >
                                        {/* Avatar / Portrait */}
                                        <div className="char-portrait-wrap">
                                            {char.image_url ? (
                                                <img
                                                    src={char.image_url}
                                                    alt={char.name}
                                                    className="char-portrait"
                                                    onError={(e) => {
                                                        (e.currentTarget as HTMLElement).style.display = 'none';
                                                    }}
                                                />
                                            ) : (
                                                <div className="portrait-fallback">
                                                    {char.char_class.toLowerCase().includes('wizard') ? <VectorIcon name="wizard" size="2rem" /> :
                                                     char.char_class.toLowerCase().includes('rogue') ? <VectorIcon name="broadsword" size="2rem" /> :
                                                     char.char_class.toLowerCase().includes('cleric') ? <VectorIcon name="magic" size="2rem" /> :
                                                     <VectorIcon name="sword" size="2rem" />}
                                                </div>
                                            )}

                                            <div className="status-badge-floating">
                                                {isSelf ? (
                                                    <span className="badge-self"><VectorIcon name="crown" /> {t.sessionLobby.claimedByYou}</span>
                                                ) : isOccupiedByOther ? (
                                                    <span className="badge-player"><VectorIcon name="knight" /> {t.sessionLobby.occupiedBy}: {char.controller_name || 'Online'}</span>
                                                ) : isAi ? (
                                                    <span className="badge-ai"><VectorIcon name="rune" /> {t.sessionLobby.aiControlled}</span>
                                                ) : (
                                                    <span className="badge-available"><VectorIcon name="magic" /> {language === 'ru' ? 'Доступен' : 'Available'}</span>
                                                )}
                                            </div>
                                        </div>

                                        {/* Info */}
                                        <div className="char-body">
                                            <h3 className="char-name">{char.name}</h3>
                                            <div className="char-tags">
                                                <span className="class-tag">{char.race || 'Hero'} {char.char_class || 'Adventurer'}</span>
                                                <span className="lvl-tag">Lvl {char.level || 1}</span>
                                            </div>

                                            {/* Vitals */}
                                            <div className="char-vitals-row">
                                                <div className="vital-box">
                                                    <span className="vital-label">HP</span>
                                                    <span className="vital-val">{char.current_hp}/{char.max_hp}</span>
                                                </div>
                                                <div className="vital-box">
                                                    <span className="vital-label">AC</span>
                                                    <span className="vital-val">{char.armor_class}</span>
                                                </div>
                                            </div>

                                            {isAi && (
                                                <p className="char-ai-note">
                                                    {language === 'ru'
                                                        ? 'Управляется ИИ-спутником. Вы можете взять управление и бесшовно продолжить игру.'
                                                        : 'Currently piloted by AI companion engine. Taking control will seamlessly transition the character to you.'}
                                                </p>
                                            )}
                                        </div>

                                        {/* Action Button */}
                                        <div className="char-card-footer">
                                            {isOccupiedByOther ? (
                                                <button
                                                    type="button"
                                                    className="claim-btn occupied-btn"
                                                    disabled
                                                >
                                                    {t.sessionLobby.occupiedBy} {char.controller_name}
                                                </button>
                                            ) : (
                                                <button
                                                    type="button"
                                                    className={`claim-btn ${isSelf ? 'resume-btn' : 'take-control-btn'}`}
                                                    onClick={() => handleClaimCharacter(char)}
                                                    disabled={isClaiming}
                                                >
                                                    {isClaiming ? (language === 'ru' ? 'Вход за героя...' : 'Claiming Hero...') :
                                                     isSelf ? <><VectorIcon name="sword" /> {language === 'ru' ? 'Продолжить за героя' : 'Resume as this Hero'}</> :
                                                     isAi ? <><VectorIcon name="rune" /> {t.sessionLobby.claimHero}</> : <><VectorIcon name="knight" /> {t.sessionLobby.enterGame}</>}
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </section>
            </main>
        </div>
    );
};
