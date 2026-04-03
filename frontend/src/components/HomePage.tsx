import React, { useState, useEffect, useRef } from 'react';
import { useGameStore } from '../store/gameStore';
import { CharacterPanel } from './CharacterPanel';
import { SessionCreation } from './SessionCreation';
import { QuickPlay } from './QuickPlay';
import { Rulebook } from './Rulebook';
import { LandingFooter } from './LandingFooter';
import './HomePage.css';

interface HomePageProps {
    onShowProfile: () => void;
    onCreateCharacter: () => void;
    onCreateSession: () => void;
    onViewSession: (sessionId: string) => void;
    onViewCharacter: (characterId: number) => void;
    onJoinSession: (sessionId: string) => void;
    onStartGameSetup: (sessionId: string) => void;
}

export const HomePage: React.FC<HomePageProps> = ({
    onShowProfile,
    onViewSession,
    onViewCharacter,
    onJoinSession,
    onStartGameSetup
}) => {
    const {
        isAuthenticated,
        userId,
        username,
        characters,
        loadCharacters,
        activeSessions,
        loadSessions,
        logout,
        setAuthenticated
    } = useGameStore();

    // Check if user has an active running session
    const runningSession = activeSessions.find(s => s.status === 'running');

    const [showSessionCreation, setShowSessionCreation] = useState(false);
    const [showQuickPlay, setShowQuickPlay] = useState(false);
    const [showRulebook, setShowRulebook] = useState(false);
    const [scrolled, setScrolled] = useState(false);
    const [activeTab, setActiveTab] = useState<'overview' | 'characters' | 'sessions'>('overview');
    const backgroundRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!isAuthenticated || !userId) {
            // Force logout and redirect to landing by clearing auth state
            console.warn('⚠️ Not authenticated - redirecting to landing');
            setAuthenticated(false);
            return;
        }

        // Load data with error handling
        const loadData = async () => {
            try {
                await Promise.all([
                    loadCharacters(userId),
                    loadSessions()
                ]);
            } catch (error) {
                console.error('Failed to load data:', error);
            }
        };
        
        loadData();

        // Add class to body for background override
        document.body.classList.add('has-home-bg');

        // Parallax background scroll (10% faster than page scroll)
        const handleScroll = () => {
            const scrollTop = window.scrollY;
            const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
            const scrollProgress = maxScroll > 0 ? scrollTop / maxScroll : 0;

            setScrolled(scrollTop > 50);

            // Update scrollbar color based on scroll position
            const scrollbar = document.documentElement;
            let color: string;

            if (scrollProgress < 0.25) {
                const t = scrollProgress / 0.25;
                color = `rgb(${42 + t * (233 - 42)}, ${157 + t * (196 - 157)}, ${143 + t * (106 - 143)})`;
            } else if (scrollProgress < 0.5) {
                const t = (scrollProgress - 0.25) / 0.25;
                color = `rgb(${233 + t * (255 - 233)}, ${196 + t * (107 - 196)}, ${106 + t * (53 - 106)})`;
            } else if (scrollProgress < 0.75) {
                const t = (scrollProgress - 0.5) / 0.25;
                color = `rgb(${255 + t * (230 - 255)}, ${107 + t * (57 - 107)}, ${53 + t * (70 - 53)})`;
            } else {
                const t = (scrollProgress - 0.75) / 0.25;
                color = `rgb(${230 + t * (157 - 230)}, ${57 + t * (78 - 57)}, ${70 + t * (221 - 70)})`;
            }

            scrollbar.style.setProperty('--scrollbar-color', color);

            // Move background at 20% scroll speed with limit
            // Background stops when it reaches the end of its extra 20% buffer
            const maxBackgroundScroll = maxScroll * 0.2;
            const backgroundScroll = Math.min(scrollTop * 0.2, maxBackgroundScroll);

            if (backgroundRef.current) {
                backgroundRef.current.style.transform = `translateY(-${backgroundScroll}px)`;
            }
        };

        window.addEventListener('scroll', handleScroll);
        handleScroll(); // Initialize on mount

        return () => {
            window.removeEventListener('scroll', handleScroll);
            document.body.classList.remove('has-home-bg');
        };
    }, [isAuthenticated, userId]);

    const handleLogout = () => {
        logout();
    };

    const handleCharacterSelect = (characterId: number) => {
        if (onViewCharacter) {
            onViewCharacter(characterId);
        }
    };

    const handleSessionJoin = (sessionId: string) => {
        if (onJoinSession) {
            onJoinSession(sessionId);
        }
    };

    const handleSessionView = (sessionId: string) => {
        if (onViewSession) {
            onViewSession(sessionId);
        }
    };

    const handleProfileClick = () => {
        // Navigate to profile page instead of showing modal
        onShowProfile();
    };

    const handleQuickPlayClick = () => {
        setShowQuickPlay(true);
    };

    const handleRulebookClick = () => {
        setShowRulebook(true);
    };

    const handleQuickJoin = async (sessionId: string) => {
        try {
            const username = localStorage.getItem('username') || 'Player';
            const response = await fetch(`/api/v1/sessions/${sessionId}/players`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ player_name: username }),
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('currentSessionId', sessionId);
                localStorage.setItem('currentPlayerId', data.player_id);
                setShowQuickPlay(false);
                // Could navigate to game or session detail
            }
        } catch (error) {
            console.error('Failed to join session:', error);
        }
    };

    return (
        <div className="home-page">
            {/* Background */}
            <div className="home-bg" ref={backgroundRef}></div>
            
            {/* Navigation Header */}
            <header className={`home-header ${scrolled ? 'scrolled' : ''}`}>
                <div className="header-content">
                    <div className="logo" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
                        <span className="logo-icon">🐉</span>
                        <span className="logo-text">
                            <span className="logo-magg">MAGG</span>
                            <span className="logo-x">x</span>
                            <span className="logo-dnd">DND</span>
                        </span>
                    </div>
                    
                    <nav className="header-nav">
                        <button 
                            className={activeTab === 'overview' ? 'active' : ''}
                            onClick={() => setActiveTab('overview')}
                        >
                            Overview
                        </button>
                        <button 
                            className={activeTab === 'characters' ? 'active' : ''}
                            onClick={() => setActiveTab('characters')}
                        >
                            Characters
                        </button>
                        <button 
                            className={activeTab === 'sessions' ? 'active' : ''}
                            onClick={() => setActiveTab('sessions')}
                        >
                            Sessions
                        </button>
                    </nav>

                    <div className="header-actions">
                        <button
                            className="btn-create-session"
                            onClick={() => setShowSessionCreation(true)}
                        >
                            <span>⚔️</span>
                            <span>Create Session</span>
                        </button>
                        
                        <button
                            className="btn-profile"
                            onClick={handleProfileClick}
                        >
                            <span className="profile-avatar">👤</span>
                            <span className="profile-name">{username || 'Adventurer'}</span>
                        </button>
                        
                        <button
                            className="btn-logout"
                            onClick={handleLogout}
                            title="Logout"
                        >
                            <span>🚪</span>
                        </button>
                    </div>
                </div>
            </header>

            {/* Hero Section */}
            <section className="home-hero">
                <div className="hero-content">
                    <h1 className="hero-title">
                        <span className="welcome-text">Welcome back,</span> <span className="username-highlight">{username || 'Adventurer'}</span>!
                    </h1>
                    <p className="hero-subtitle">
                        Your epic journey continues. Pick up where you left off or start a new adventure.
                    </p>
                </div>
                
                {/* Continue Game Button - Show if there's a running session */}
                {runningSession && (
                    <div className="continue-game-section">
                        <button className="btn-continue-game" onClick={() => onStartGameSetup(runningSession.session_id)}>
                            <span className="btn-icon">🎮</span>
                            <div className="btn-text">
                                <span className="btn-title">Continue Adventure</span>
                                <span className="btn-subtitle">{runningSession.session_name}</span>
                            </div>
                            <span className="btn-arrow">→</span>
                        </button>
                    </div>
                )}
                
                <div className="hero-stats">
                    <div className="stat-card">
                        <span className="stat-value">{characters.length}</span>
                        <span className="stat-label">Characters</span>
                    </div>
                    <div className="stat-divider"></div>
                    <div className="stat-card">
                        <span className="stat-value">{activeSessions.length}</span>
                        <span className="stat-label">Active Sessions</span>
                    </div>
                    <div className="stat-divider"></div>
                    <div className="stat-card">
                        <span className="stat-value">∞</span>
                        <span className="stat-label">Possibilities</span>
                    </div>
                </div>
            </section>

            {/* Main Content */}
            <main className="home-content">
                {activeTab === 'overview' && (
                    <div className="overview-section">
                        {/* Recent Sessions */}
                        <div className="content-card">
                            <div className="card-header">
                                <h2>Recent Sessions</h2>
                                <button 
                                    className="btn-view-all"
                                    onClick={() => setActiveTab('sessions')}
                                >
                                    View All →
                                </button>
                            </div>
                            {activeSessions.length > 0 ? (
                                <div className="session-list">
                                    {activeSessions.slice(0, 3).map((session) => (
                                        <div 
                                            key={session.session_id} 
                                            className="session-item"
                                            onClick={() => handleSessionJoin(session.session_id)}
                                        >
                                            <div className="session-icon">
                                                {session.status === 'running' ? '🎮' : '📋'}
                                            </div>
                                            <div className="session-info">
                                                <h3>{session.session_name}</h3>
                                                <p>{session.player_count}/{session.max_players} players</p>
                                            </div>
                                            <div className="session-status">
                                                <span className={`status-badge ${session.status}`}>
                                                    {session.status}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="empty-state">
                                    <span className="empty-icon">📜</span>
                                    <p>No active sessions</p>
                                    <button 
                                        className="btn-primary"
                                        onClick={() => setShowSessionCreation(true)}
                                    >
                                        Create Your First Session
                                    </button>
                                </div>
                            )}
                        </div>

                        {/* Recent Characters */}
                        <div className="content-card">
                            <div className="card-header">
                                <h2>Your Characters</h2>
                                <button 
                                    className="btn-view-all"
                                    onClick={() => setActiveTab('characters')}
                                >
                                    View All →
                                </button>
                            </div>
                            {characters.length > 0 ? (
                                <div className="character-grid">
                                    {characters.slice(0, 3).map((char) => (
                                        <div 
                                            key={char.id} 
                                            className="character-card-mini"
                                            onClick={() => handleCharacterSelect(char.id)}
                                        >
                                            <div className="char-avatar">
                                                {char.race === 'Human' ? '🧙' : char.race === 'Elf' ? '🧝' : '🧌'}
                                            </div>
                                            <div className="char-info">
                                                <h3>{char.name}</h3>
                                                <p>Lvl {char.level} {char.race} {char.char_class}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="empty-state">
                                    <span className="empty-icon">⚔️</span>
                                    <p>No characters yet</p>
                                    <button className="btn-primary">
                                        Create Your First Character
                                    </button>
                                </div>
                            )}
                        </div>

                        {/* Quick Actions */}
                        <div className="content-card">
                            <div className="card-header">
                                <h2>Quick Actions</h2>
                            </div>
                            <div className="quick-actions">
                                <button className="action-btn" onClick={() => setShowSessionCreation(true)}>
                                    <span className="action-icon">⚔️</span>
                                    <span>Create Session</span>
                                </button>
                                <button
                                    className="action-btn"
                                    onClick={onShowProfile}
                                >
                                    <span className="action-icon">📝</span>
                                    <span>New Character</span>
                                </button>
                                <button 
                                    className="action-btn"
                                    onClick={handleQuickPlayClick}
                                >
                                    <span className="action-icon">🎲</span>
                                    <span>Quick Play</span>
                                </button>
                                <button 
                                    className="action-btn"
                                    onClick={handleRulebookClick}
                                >
                                    <span className="action-icon">📚</span>
                                    <span>Rulebook</span>
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'characters' && (
                    <div className="characters-section">
                        <div className="section-header">
                            <h2>Your Characters</h2>
                            <button 
                                className="btn-primary"
                                onClick={() => {
                                    // Navigate to character creation or open modal
                                    alert('Character creation coming soon!');
                                }}
                            >
                                + Create Character
                            </button>
                        </div>
                        {characters.length > 0 ? (
                            <div className="characters-grid-full">
                                {characters.map((char) => (
                                    <div 
                                        key={char.id} 
                                        className="character-card-placeholder"
                                        onClick={() => handleCharacterSelect(char.id)}
                                    >
                                        <div className="char-card-inner">
                                            <div className="char-avatar-large">
                                                {char.race === 'Human' ? '🧙' : char.race === 'Elf' ? '🧝' : '🧌'}
                                            </div>
                                            <h3>{char.name}</h3>
                                            <p>Lvl {char.level} {char.race} {char.char_class}</p>
                                            <div className="char-stats">
                                                <span>HP: {char.current_hp}/{char.max_hp}</span>
                                                <span>AC: {char.armor_class}</span>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="empty-state-large">
                                <span className="empty-icon">⚔️</span>
                                <h3>No characters yet</h3>
                                <p>Create your first character and start your adventure!</p>
                                <button 
                                    className="btn-primary btn-large"
                                    onClick={() => {
                                        alert('Character creation coming soon!');
                                    }}
                                >
                                    Create Character
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'sessions' && (
                    <div className="sessions-section">
                        <div className="section-header">
                            <h2>Game Sessions</h2>
                            <button 
                                className="btn-primary"
                                onClick={() => setShowSessionCreation(true)}
                            >
                                + Create Session
                            </button>
                        </div>
                        {activeSessions.length > 0 ? (
                            <div className="sessions-list">
                                {activeSessions.map((session) => (
                                    <div
                                        key={session.session_id}
                                        className="session-card-full"
                                        onClick={() => handleSessionView(session.session_id)}
                                    >
                                        <div className="session-header">
                                            <h3>{session.session_name}</h3>
                                            <span className={`status-badge ${session.status}`}>
                                                {session.status}
                                            </span>
                                        </div>
                                        <p className="session-description">
                                            {session.description || 'No description'}
                                        </p>
                                        <div className="session-meta">
                                            <span>👥 {session.player_count}/{session.max_players} players</span>
                                            <span>🎮 {session.game_mode}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="empty-state-large">
                                <span className="empty-icon">📜</span>
                                <h3>No sessions yet</h3>
                                <p>Create or join a session to start playing!</p>
                                <button 
                                    className="btn-primary btn-large"
                                    onClick={() => setShowSessionCreation(true)}
                                >
                                    Create Session
                                </button>
                            </div>
                        )}
                    </div>
                )}
            </main>

            {/* Session Creation Modal */}
            {showSessionCreation && (
                <SessionCreation
                    userId={userId || 0}
                    onBack={() => setShowSessionCreation(false)}
                    onComplete={(sessionId: string) => {
                        setShowSessionCreation(false);
                        // Persist session ID to localStorage immediately
                        if (sessionId) {
                            localStorage.setItem('currentSessionId', sessionId);
                            console.log('✓ Session persisted to localStorage:', sessionId);
                        }
                        // Reload sessions to show newly created one
                        loadSessions();
                        console.log('Session created:', sessionId);
                    }}
                />
            )}

            {/* Quick Play Modal */}
            {showQuickPlay && (
                <QuickPlay
                    onJoinGame={handleQuickJoin}
                    onCreateGame={() => setShowSessionCreation(true)}
                    onClose={() => setShowQuickPlay(false)}
                />
            )}

            {/* Rulebook Modal */}
            {showRulebook && (
                <Rulebook
                    onClose={() => setShowRulebook(false)}
                />
            )}

            {/* Footer */}
            <LandingFooter />
        </div>
    );
};
