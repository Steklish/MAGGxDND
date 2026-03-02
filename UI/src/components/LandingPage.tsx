import React, { useState, useEffect } from 'react';
import { LandingFooter } from './LandingFooter';
import { AuthModal } from './AuthModal';
import { CharacterCreation } from './CharacterCreation';
import { ProfilePage } from './ProfilePage';
import { useGameStore } from '../store/gameStore';
import './LandingPage.css';

export const LandingPage: React.FC = () => {
    const { setAuthenticated } = useGameStore();
    const [authModalOpen, setAuthModalOpen] = useState<'login' | 'register' | null>(null);
    const [showCharacterCreation, setShowCharacterCreation] = useState(false);
    const [showProfile, setShowProfile] = useState(false);
    const [userId, setUserId] = useState<number | null>(null);
    const [scrolled, setScrolled] = useState(false);

    // Handle quick start (demo mode)
    const handleQuickStart = () => {
        setAuthenticated(true);
    };

    // Handle registration success
    const handleRegisterSuccess = (newUserId: number, username: string) => {
        setUserId(newUserId);
        setShowCharacterCreation(true);
    };

    // Handle character creation complete
    const handleCharacterComplete = () => {
        setShowCharacterCreation(false);
        setAuthModalOpen(null);
        setShowProfile(true);
    };

    // Handle profile back
    const handleProfileBack = () => {
        setShowProfile(false);
    };

    useEffect(() => {
        const handleScroll = () => {
            const scrollTop = window.scrollY;
            const docHeight = document.documentElement.scrollHeight - window.innerHeight;
            const progress = docHeight > 0 ? scrollTop / docHeight : 0;
            
            setScrolled(scrollTop > 50);
            setScrollProgress(progress);

            // Update scrollbar color based on scroll position
            const scrollbar = document.documentElement;
            let color1, color2;
            
            if (progress < 0.25) {
                // Green to Yellow
                const t = progress / 0.25;
                color1 = `rgb(${42 + t * (233 - 42)}, ${157 + t * (196 - 157)}, ${143 + t * (106 - 143)})`;
                color2 = `rgb(${42 + t * (233 - 42)}, ${157 + t * (196 - 157)}, ${143 + t * (106 - 143)})`;
            } else if (progress < 0.5) {
                // Yellow to Orange
                const t = (progress - 0.25) / 0.25;
                color1 = `rgb(${233 + t * (255 - 233)}, ${196 + t * (107 - 196)}, ${106 + t * (53 - 106)})`;
                color2 = `rgb(${233 + t * (255 - 233)}, ${196 + t * (107 - 196)}, ${106 + t * (53 - 106)})`;
            } else if (progress < 0.75) {
                // Orange to Red
                const t = (progress - 0.5) / 0.25;
                color1 = `rgb(${255 + t * (230 - 255)}, ${107 + t * (57 - 107)}, ${53 + t * (70 - 53)})`;
                color2 = `rgb(${255 + t * (230 - 255)}, ${107 + t * (57 - 107)}, ${53 + t * (70 - 53)})`;
            } else {
                // Red to Purple
                const t = (progress - 0.75) / 0.25;
                color1 = `rgb(${230 + t * (157 - 230)}, ${57 + t * (78 - 57)}, ${70 + t * (221 - 70)})`;
                color2 = `rgb(${230 + t * (157 - 230)}, ${57 + t * (78 - 57)}, ${70 + t * (221 - 70)})`;
            }
            
            scrollbar.style.setProperty('--scrollbar-color', color1);

            // Animate sections on scroll
            const sections = document.querySelectorAll('.feature-card, .step-card');
            sections.forEach((section) => {
                const rect = section.getBoundingClientRect();
                const isInView = rect.top < window.innerHeight * 0.85;
                if (isInView) {
                    section.classList.add('visible');
                }
            });
        };

        window.addEventListener('scroll', handleScroll);
        handleScroll();

        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const scrollToSection = (id: string) => {
        const element = document.getElementById(id);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth' });
        }
    };

    return (
        <div className="landing-page">
            {/* Animated Background */}
            <div className="landing-background">
                <div className="bg-overlay"></div>
                <div className="bg-gradient-orbs">
                    <div className="orb orb-1"></div>
                    <div className="orb orb-2"></div>
                    <div className="orb orb-3"></div>
                    <div className="orb orb-4"></div>
                </div>
            </div>

            {/* Navigation Header */}
            <header className={`landing-header ${scrolled ? 'scrolled' : ''}`}>
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
                        <button onClick={() => scrollToSection('features')}>Features</button>
                        <button onClick={() => scrollToSection('how-it-works')}>How It Works</button>
                        <button onClick={() => scrollToSection('about')}>About</button>
                    </nav>
                    <div className="header-actions">
                        {useGameStore.getState().isAuthenticated ? (
                            <>
                                <button
                                    className="btn-profile"
                                    onClick={() => setShowProfile(true)}
                                >
                                    <span className="profile-icon">👤</span>
                                    <span className="profile-name">{localStorage.getItem('username') || 'Profile'}</span>
                                </button>
                                <button
                                    className="btn-logout"
                                    onClick={() => {
                                        localStorage.removeItem('access_token');
                                        localStorage.removeItem('username');
                                        localStorage.removeItem('userId');
                                        setAuthenticated(false);
                                        window.location.reload();
                                    }}
                                >
                                    Logout
                                </button>
                            </>
                        ) : (
                            <>
                                <button
                                    className="btn-login"
                                    onClick={() => setAuthModalOpen('login')}
                                >
                                    Sign In
                                </button>
                                <button
                                    className="btn-register"
                                    onClick={() => setAuthModalOpen('register')}
                                >
                                    Get Started
                                </button>
                            </>
                        )}
                        <button
                            className="btn-quick-start"
                            onClick={handleQuickStart}
                            title="Try demo without account"
                        >
                            Quick Start ⚡
                        </button>
                    </div>
                </div>
            </header>

            {/* Hero Section */}
            <section className="hero-section">
                <div className="hero-content">
                    <div className="hero-badge">
                        <span className="badge-pulse"></span>
                        AI-Powered D&D Experience
                    </div>
                    <h1 className="hero-title">
                        Your Adventure,<br />
                        <span className="title-gradient">Reimagined by AI</span>
                    </h1>
                    <p className="hero-subtitle">
                        Experience Dungeons & Dragons like never before with our AI-driven 
                        game engine that adapts to your choices, creates dynamic narratives, 
                        and brings your fantasy world to life.
                    </p>
                    <div className="hero-cta">
                        <button 
                            className="btn-primary btn-glow"
                            onClick={() => setAuthModalOpen('register')}
                        >
                            <span>Start Your Adventure</span>
                            <span className="btn-arrow">→</span>
                        </button>
                        <button 
                            className="btn-secondary"
                            onClick={() => scrollToSection('features')}
                        >
                            <span className="btn-icon">⚔️</span>
                            <span>Learn More</span>
                        </button>
                    </div>
                    <div className="hero-stats">
                        <div className="stat-item">
                            <span className="stat-value">∞</span>
                            <span className="stat-label">Possible Stories</span>
                        </div>
                        <div className="stat-divider"></div>
                        <div className="stat-item">
                            <span className="stat-value">24/7</span>
                            <span className="stat-label">AI Dungeon Master</span>
                        </div>
                        <div className="stat-divider"></div>
                        <div className="stat-item">
                            <span className="stat-value">100%</span>
                            <span className="stat-label">Your Choices Matter</span>
                        </div>
                    </div>
                </div>
                <div className="hero-visual">
                    <div className="hero-card">
                        <div className="card-glow"></div>
                        <div className="card-content">
                            <div className="card-header">
                                <span className="card-icon">🎲</span>
                                <span className="card-title">Session #2847</span>
                            </div>
                            <div className="card-body">
                                <p className="card-text">"The ancient dragon's eyes glow as it speaks in a voice that echoes through the ages..."</p>
                                <div className="card-actions">
                                    <span className="action-tag">Combat</span>
                                    <span className="action-tag">Epic</span>
                                    <span className="action-tag">Level 15</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section id="features" className="features-section">
                <div className="section-header">
                    <span className="section-tag">Features</span>
                    <h2 className="section-title">Everything You Need for Epic Adventures</h2>
                    <p className="section-subtitle">
                        Powered by cutting-edge AI, built for legendary storytelling
                    </p>
                </div>
                <div className="features-grid">
                    <div className="feature-card" id="feature-1">
                        <div className="feature-icon">🧙‍♂️</div>
                        <h3>AI Dungeon Master</h3>
                        <p>
                            Our AI adapts to your playstyle, creating personalized narratives 
                            that respond to every choice you make.
                        </p>
                        <div className="feature-tags">
                            <span>Dynamic</span>
                            <span>Adaptive</span>
                            <span>Immersive</span>
                        </div>
                    </div>
                    <div className="feature-card" id="feature-2">
                        <div className="feature-icon">⚔️</div>
                        <h3>Real-Time Combat</h3>
                        <p>
                            Engaging turn-based combat with initiative tracking, 
                            HP monitoring, and tactical decision-making.
                        </p>
                        <div className="feature-tags">
                            <span>Strategic</span>
                            <span>Fast</span>
                            <span>Fair</span>
                        </div>
                    </div>
                    <div className="feature-card" id="feature-3">
                        <div className="feature-icon">📜</div>
                        <h3>Living World</h3>
                        <p>
                            A world that evolves with your actions. NPCs remember, 
                            locations change, and your legacy grows.
                        </p>
                        <div className="feature-tags">
                            <span>Persistent</span>
                            <span>Reactive</span>
                            <span>Deep</span>
                        </div>
                    </div>
                    <div className="feature-card" id="feature-4">
                        <div className="feature-icon">👥</div>
                        <h3>Multiplayer Ready</h3>
                        <p>
                            Play with friends online. Coordinate strategies, share 
                            moments, and create legends together.
                        </p>
                        <div className="feature-tags">
                            <span>Cooperative</span>
                            <span>Social</span>
                            <span>Connected</span>
                        </div>
                    </div>
                    <div className="feature-card" id="feature-5">
                        <div className="feature-icon">🎭</div>
                        <h3>Character Creation</h3>
                        <p>
                            Build unique characters with deep customization. 
                            Your backstory matters and shapes the narrative.
                        </p>
                        <div className="feature-tags">
                            <span>Custom</span>
                            <span>Detailed</span>
                            <span>Unique</span>
                        </div>
                    </div>
                    <div className="feature-card" id="feature-6">
                        <div className="feature-icon">📊</div>
                        <h3>Progress Tracking</h3>
                        <p>
                            Track your adventures, review past sessions, and 
                            watch your character grow stronger.
                        </p>
                        <div className="feature-tags">
                            <span>Analytics</span>
                            <span>History</span>
                            <span>Growth</span>
                        </div>
                    </div>
                </div>
            </section>

            {/* How It Works Section */}
            <section id="how-it-works" className="how-it-works-section">
                <div className="section-header">
                    <span className="section-tag">How It Works</span>
                    <h2 className="section-title">Begin Your Journey in Three Steps</h2>
                </div>
                <div className="steps-container">
                    <div className="step-card" id="step-1">
                        <div className="step-number">01</div>
                        <div className="step-content">
                            <h3>Create Your Account</h3>
                            <p>
                                Sign up in seconds and start building your adventurer. 
                                Choose your class, background, and destiny.
                            </p>
                            <div className="step-visual">
                                <span className="visual-icon">📝</span>
                            </div>
                        </div>
                    </div>
                    <div className="step-connector"></div>
                    <div className="step-card" id="step-2">
                        <div className="step-number">02</div>
                        <div className="step-content">
                            <h3>Join or Create a Session</h3>
                            <p>
                                Jump into an ongoing campaign or start your own. 
                                Play solo or gather your party.
                            </p>
                            <div className="step-visual">
                                <span className="visual-icon">🎮</span>
                            </div>
                        </div>
                    </div>
                    <div className="step-connector"></div>
                    <div className="step-card" id="step-3">
                        <div className="step-number">03</div>
                        <div className="step-content">
                            <h3>Play & Immerse</h3>
                            <p>
                                Make choices, roll dice, fight monsters, and weave 
                                your legend. The AI responds to everything.
                            </p>
                            <div className="step-visual">
                                <span className="visual-icon">🎲</span>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* About Section */}
            <section id="about" className="about-section">
                <div className="about-content">
                    <div className="about-text">
                        <span className="section-tag">About</span>
                        <h2 className="section-title">Crafted for D&D Lovers</h2>
                        <p className="about-description">
                            MAGGxDND combines the timeless appeal of Dungeons & Dragons with 
                            cutting-edge artificial intelligence. Our mission is to make D&D 
                            accessible to everyone while preserving the magic that makes 
                            tabletop RPGs special.
                        </p>
                        <p className="about-description">
                            Whether you're a veteran player with decades of experience or 
                            curious about D&D for the first time, our AI adapts to your 
                            level and creates the perfect adventure for you.
                        </p>
                        <div className="about-features">
                            <div className="about-feature-item">
                                <span className="feature-check">✓</span>
                                <span>Built by D&D enthusiasts</span>
                            </div>
                            <div className="about-feature-item">
                                <span className="feature-check">✓</span>
                                <span>Powered by advanced AI</span>
                            </div>
                            <div className="about-feature-item">
                                <span className="feature-check">✓</span>
                                <span>Always improving</span>
                            </div>
                        </div>
                    </div>
                    <div className="about-visual">
                        <div className="dice-container">
                            <div className="dice d20">
                                <span>20</span>
                            </div>
                            <div className="dice d12">
                                <span>12</span>
                            </div>
                            <div className="dice d8">
                                <span>8</span>
                            </div>
                            <div className="dice d6">
                                <span>6</span>
                            </div>
                            <div className="dice d4">
                                <span>4</span>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="cta-section">
                <div className="cta-content">
                    <h2 className="cta-title">Ready to Begin Your Legend?</h2>
                    <p className="cta-subtitle">
                        Join thousands of adventurers already exploring infinite worlds
                    </p>
                    <div className="cta-buttons">
                        <button 
                            className="btn-primary btn-large"
                            onClick={() => setAuthModalOpen('register')}
                        >
                            Create Free Account
                        </button>
                        <button 
                            className="btn-outline btn-large"
                            onClick={() => setAuthModalOpen('login')}
                        >
                            Sign In
                        </button>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <LandingFooter />

            {/* Auth Modal */}
            {authModalOpen && (
                <AuthModal
                    mode={authModalOpen}
                    onClose={() => setAuthModalOpen(null)}
                    onRegisterSuccess={handleRegisterSuccess}
                />
            )}

            {/* Character Creation */}
            {showCharacterCreation && userId && (
                <CharacterCreation
                    userId={userId}
                    onComplete={handleCharacterComplete}
                />
            )}

            {/* Profile Page */}
            {showProfile && userId && (
                <ProfilePage
                    userId={userId}
                    onBack={handleProfileBack}
                />
            )}
        </div>
    );
};
