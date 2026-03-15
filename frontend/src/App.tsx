import React, { useState, useEffect } from 'react';
import { useGameStore } from './store/gameStore';
import { LandingPage } from './components/LandingPage';
import { HomePage } from './components/HomePage';
import { ProfilePage } from './components/ProfilePage';
import { CharacterCreation } from './components/CharacterCreation';
import { SessionCreation } from './components/SessionCreation';
import { SessionDetail } from './components/SessionDetail';
import { CharacterDetail } from './components/CharacterDetail';
import { GameSetup } from './components/GameSetup';
import { GameLayout } from './components/GameLayout';
import { ToastProvider } from './components/common/Toast';
import './App.css';

type Page = 
  | 'landing'
  | 'home'
  | 'profile'
  | 'character-creation'
  | 'session-creation'
  | 'session-detail'
  | 'character-detail'
  | 'game-setup'
  | 'game';

function App() {
    const {
        isAuthenticated,
        userId,
        username,
        characters,
        loadCharacters,
        loadSessions,
        checkAuthPersistence,
        isGuest,
        setActiveSessions
    } = useGameStore();

    const [currentPage, setCurrentPage] = useState<Page>('landing');
    const [localUserId, setLocalUserId] = useState<number | null>(null);
    const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
    const [selectedCharacterId, setSelectedCharacterId] = useState<number | null>(null);
    const [isInitialized, setIsInitialized] = useState(false);

    // Initialize auth on mount
    useEffect(() => {
        checkAuthPersistence();

        const storedUserId = localStorage.getItem('userId');
        const token = localStorage.getItem('access_token');

        if (storedUserId && token) {
            const id = parseInt(storedUserId);
            setLocalUserId(id);
            loadCharacters(id);
            loadSessions();

            // If authenticated, go to home page
            setCurrentPage('home');
        } else {
            // If not authenticated, show landing page
            setCurrentPage('landing');
        }

        setIsInitialized(true);
    }, [checkAuthPersistence]);

    // Handle authentication state changes - reload sessions on auth change
    useEffect(() => {
        if (isInitialized) {
            if (isAuthenticated && localUserId) {
                setCurrentPage('home');
                // Reload sessions when auth state changes
                loadSessions();
            } else if (!isAuthenticated) {
                setCurrentPage('landing');
                // Clear sessions on logout
                setActiveSessions([]);
            }
        }
    }, [isAuthenticated, localUserId, isInitialized]);

    // Navigation handlers
    const handleShowProfile = () => {
        setCurrentPage('profile');
    };

    const handleBackFromProfile = () => {
        setCurrentPage('home');
    };

    const handleShowCharacterCreation = () => {
        setCurrentPage('character-creation');
    };

    const handleShowSessionCreation = () => {
        setCurrentPage('session-creation');
    };

    const handleShowSessionDetail = (sessionId: string) => {
        setSelectedSessionId(sessionId);
        setCurrentPage('session-detail');
    };

    const handleShowCharacterDetail = (characterId: number) => {
        setSelectedCharacterId(characterId);
        setCurrentPage('character-detail');
    };

    const handleJoinSession = async (sessionId: string) => {
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
                // Navigate to session detail page
                handleShowSessionDetail(sessionId);
            }
        } catch (error) {
            console.error('Failed to join session:', error);
        }
    };

    const handleStartGameSetup = (sessionId: string) => {
        setSelectedSessionId(sessionId);
        setCurrentPage('game-setup');
    };

    const handleStartGame = () => {
        setCurrentPage('game');
    };

    const handleCharacterComplete = () => {
        setCurrentPage('profile');
        if (localUserId) {
            loadCharacters(localUserId);
        }
    };

    const handleSessionComplete = () => {
        setCurrentPage('home');
        loadSessions();
    };

    // Render current page
    const renderPage = () => {
        switch (currentPage) {
            case 'landing':
                return <LandingPage />;
            
            case 'home':
                return (
                    <HomePage
                        onShowProfile={handleShowProfile}
                        onCreateCharacter={handleShowCharacterCreation}
                        onCreateSession={handleShowSessionCreation}
                        onViewSession={handleShowSessionDetail}
                        onViewCharacter={handleShowCharacterDetail}
                        onJoinSession={handleJoinSession}
                        onStartGameSetup={handleStartGameSetup}
                    />
                );
            
            case 'profile':
                return (
                    <ProfilePage
                        userId={localUserId || 0}
                        onBack={handleBackFromProfile}
                        onGoHome={() => setCurrentPage('home')}
                    />
                );
            
            case 'character-creation':
                return (
                    <CharacterCreation
                        userId={localUserId || 0}
                        onComplete={handleCharacterComplete}
                    />
                );
            
            case 'session-creation':
                return (
                    <SessionCreation
                        userId={localUserId || 0}
                        onComplete={handleSessionComplete}
                        onBack={() => setCurrentPage('home')}
                    />
                );
            
            case 'session-detail':
                return selectedSessionId ? (
                    <SessionDetail
                        sessionId={selectedSessionId}
                        onBack={() => setCurrentPage('home')}
                        onStartGame={handleStartGameSetup}
                        onLeave={() => setCurrentPage('home')}
                    />
                ) : (
                    <div className="app-loading">
                        <p>Session not found</p>
                        <button onClick={() => setCurrentPage('home')}>Back to Home</button>
                    </div>
                );
            
            case 'character-detail':
                return selectedCharacterId ? (
                    <CharacterDetail
                        characterId={selectedCharacterId}
                        onBack={() => setCurrentPage('profile')}
                        onEdit={() => {}}
                    />
                ) : (
                    <div className="app-loading">
                        <p>Character not found</p>
                        <button onClick={() => setCurrentPage('home')}>Back to Home</button>
                    </div>
                );
            
            case 'game-setup':
                return selectedSessionId ? (
                    <GameSetup
                        sessionId={selectedSessionId}
                        onComplete={handleStartGame}
                        onBack={() => setCurrentPage('session-detail')}
                    />
                ) : (
                    <div className="app-loading">
                        <p>Session not found</p>
                        <button onClick={() => setCurrentPage('home')}>Back to Home</button>
                    </div>
                );
            
            case 'game':
                return <GameLayout />;
            
            default:
                return <LandingPage />;
        }
    };

    if (!isInitialized) {
        return (
            <div className="app-loading">
                <div className="loading-spinner">
                    <div className="spinner-ring"></div>
                    <div className="spinner-ring"></div>
                    <div className="spinner-ring"></div>
                </div>
                <p>Loading...</p>
            </div>
        );
    }

    return (
        <ToastProvider>
            {renderPage()}
        </ToastProvider>
    );
}

export default App;
