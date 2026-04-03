import React, { useState, useEffect } from 'react';
import { useGameStore } from './store/gameStore';
import { useServerConnection } from './hooks/useServerConnection';
import { LandingPage } from './components/LandingPage';
import { HomePage } from './components/HomePage';
import { ProfilePage } from './components/ProfilePage';
import { CharacterCreation } from './components/CharacterCreation';
import { SessionCreation } from './components/SessionCreation';
import { SessionDetail } from './components/SessionDetail';
import { CharacterDetail } from './components/CharacterDetail';
import { GameSetup } from './components/GameSetup';
import { WaitingRoom } from './components/WaitingRoom';
import { GameLayout } from './components/GameLayout';
import { LoadingPage } from './components/LoadingPage';
import { ErrorPage } from './components/ErrorPage';
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
  | 'waiting-room'
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

    // Server connection monitoring
    const { isConnected, error, hideError } = useServerConnection({
        endpoint: '/health',
        interval: 5000,
        failureThreshold: 3,
    });

    const [currentPage, setCurrentPage] = useState<Page>('landing');
    const [localUserId, setLocalUserId] = useState<number | null>(null);
    const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
    const [selectedCharacterId, setSelectedCharacterId] = useState<number | null>(null);
    const [isInitialized, setIsInitialized] = useState(false);
    const [isLoadingAfterAuth, setIsLoadingAfterAuth] = useState(false);
    const [isWaitingRoomReady, setIsWaitingRoomReady] = useState(false);

    // Initialize auth on mount
    useEffect(() => {
        const initAuth = async () => {
            checkAuthPersistence();

            const storedUserId = localStorage.getItem('userId');
            const token = localStorage.getItem('access_token');

            if (storedUserId && token) {
                const id = parseInt(storedUserId);
                setLocalUserId(id);
                // Wait for characters and sessions to load before navigating
                await Promise.all([
                    loadCharacters(id).catch(console.warn),
                    loadSessions().catch(console.warn)
                ]);

                // If authenticated, go to home page
                setCurrentPage('home');
            } else {
                // If not authenticated, show landing page
                setCurrentPage('landing');
            }

            setIsInitialized(true);
        };

        initAuth();
    }, [checkAuthPersistence]);

    // Handle authentication state changes - reload sessions on auth change
    useEffect(() => {
        if (isInitialized && !isLoadingAfterAuth) {
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
    }, [isAuthenticated, localUserId, isInitialized, isLoadingAfterAuth]);

    // Watch for auth changes during landing page to show loading state
    useEffect(() => {
        if (isAuthenticated && currentPage === 'landing' && !localUserId) {
            setIsLoadingAfterAuth(true);
        }
        if (isLoadingAfterAuth && localUserId) {
            setIsLoadingAfterAuth(false);
        }
    }, [isAuthenticated, currentPage, localUserId, isLoadingAfterAuth]);

    // Listen for loading complete event from LoadingPage
    useEffect(() => {
        const handleLoadingComplete = () => {
            const storedUserId = localStorage.getItem('userId');
            if (storedUserId) {
                const id = parseInt(storedUserId);
                setLocalUserId(id);
                setIsLoadingAfterAuth(false);
                setCurrentPage('home');
            }
        };

        window.addEventListener('auth-loading-complete', handleLoadingComplete);
        return () => window.removeEventListener('auth-loading-complete', handleLoadingComplete);
    }, []);

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
        setCurrentPage('waiting-room');
    };

    const handleGoToGameSetup = (sessionId: string) => {
        setSelectedSessionId(sessionId);
        setCurrentPage('game-setup');
    };

    const handleStartGame = (sessionId: string) => {
        // Update localStorage with ALL required fields
        localStorage.setItem('currentSessionId', sessionId);
        localStorage.setItem('gameStatus', 'running');
        
        console.log('🎮 Game started, session:', sessionId);
        console.log('📋 localStorage:', {
            sessionId: localStorage.getItem('currentSessionId'),
            playerId: localStorage.getItem('currentPlayerId'),
            gameStatus: localStorage.getItem('gameStatus')
        });
        
        // Navigate to game page
        setCurrentPage('game');
    };

    const handleCharacterComplete = () => {
        setCurrentPage('profile');
        if (localUserId) {
            loadCharacters(localUserId);
        }
    };

    const handleSessionComplete = (sessionId: string) => {
        // Persist session ID to localStorage immediately
        if (sessionId) {
            localStorage.setItem('currentSessionId', sessionId);
            console.log('✓ Session persisted to localStorage:', sessionId);
        }
        // Navigate to waiting room instead of home
        setSelectedSessionId(sessionId);
        setCurrentPage('waiting-room');
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

            case 'waiting-room':
                return selectedSessionId ? (
                    <WaitingRoom
                        sessionId={selectedSessionId}
                        onGameStart={handleStartGame}
                        onBack={() => setCurrentPage('home')}
                        onGoToSetup={handleGoToGameSetup}
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

    // Show loading page after authentication during data load
    if (isLoadingAfterAuth) {
        return <LoadingPage message="Preparing your adventure..." showDice={true} />;
    }

    return (
        <ToastProvider>
            {/* Error page - shown when server is unreachable */}
            {!isConnected && (
                <ErrorPage
                    title="Server Unavailable"
                    message={error || 'The game server is currently offline. Please try again later.'}
                    onRetry={hideError}
                />
            )}
            {renderPage()}
        </ToastProvider>
    );
}

export default App;
