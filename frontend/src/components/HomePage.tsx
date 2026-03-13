import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGameStore } from '../store/gameStore';
import { CharacterPanel } from './CharacterPanel';
import { SessionCreation } from './SessionCreation';
import { ProfilePage } from './ProfilePage';
import './HomePage.css';

export const HomePage: React.FC = () => {
    const navigate = useNavigate();
    const { 
        isAuthenticated, 
        userId, 
        username, 
        characters, 
        loadCharacters,
        activeSessions,
        loadSessions,
        logout 
    } = useGameStore();
    
    const [showSessionCreation, setShowSessionCreation] = useState(false);
    const [showProfile, setShowProfile] = useState(false);
    const [scrolled, setScrolled] = useState(false);
    const [activeTab, setActiveTab] = useState<'overview' | 'characters' | 'sessions'>('overview');

    useEffect(() => {
        if (!isAuthenticated || !userId) {
            navigate('/');
            return;
        }

        loadCharacters(userId);
        loadSessions();

        const handleScroll = () => {
            setScrolled(window.scrollY > 50);
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, [isAuthenticated, userId, navigate]);

    const handleLogout = () => {
        logout();
        navigate('/');
    };

    const handleCharacterSelect = (characterId: number) => {
        console.log('Selected character:', characterId);
        // Navigate to game or character detail
    };

    const handleSessionJoin = (sessionId: string) => {
        console.log('Joining session:', sessionId);
        // Navigate to session
    };

    return (
        <div className="home-page">
            {/* Navigation Header */}
            <header className={`home-header ${scrolled ? 'scrolled' : ''}`}>
                <div className="header-content">
                    <div className="logo" onClick={() => navigate('/home')}>
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
                            onClick={() => setShowProfile(true)}
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
                        Welcome back, <span className="highlight">{username || 'Adventurer'}</span>!
                    </h1>
                    <p className="hero-subtitle">
                        Your epic journey continues. Pick up where you left off or start a new adventure.
                    </p>
                </div>
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
                                    onClick={() => {
                                        alert('Character creation coming soon!');
                                    }}
                                >
                                    <span className="action-icon">📝</span>
                                    <span>New Character</span>
                                </button>
                                <button 
                                    className="action-btn"
                                    onClick={() => {
                                        alert('Quick Play coming soon!');
                                    }}
                                >
                                    <span className="action-icon">🎲</span>
                                    <span>Quick Play</span>
                                </button>
                                <button 
                                    className="action-btn"
                                    onClick={() => {
                                        alert('Rulebook coming soon!');
                                    }}
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
                                    <div key={char.id} className="character-card-placeholder">
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
                                        onClick={() => handleSessionJoin(session.session_id)}
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
                        // Handle session created
                        console.log('Session created:', sessionId);
                    }}
                />
            )}

            {/* Profile Modal */}
            {showProfile && (
                <ProfilePage
                    userId={userId || 0}
                    onBack={() => setShowProfile(false)}
                    onGoHome={() => {
                        setShowProfile(false);
                        // Already on home page, just close profile
                    }}
                />
            )}
        </div>
    );
};
