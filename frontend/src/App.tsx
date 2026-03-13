import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGameStore } from './store/gameStore';
import { LandingPage } from './components/LandingPage';
import { HomePage } from './components/HomePage';
import { ProfilePage } from './components/ProfilePage';
import { CharacterCreation } from './components/CharacterCreation';
import { SessionCreation } from './components/SessionCreation';
import { SessionDetail } from './components/SessionDetail';
import { GameSetup } from './components/GameSetup';
import { GameLayout } from './components/GameLayout';
import { ToastProvider } from './components/common/Toast';
import './App.css';

function App() {
    const navigate = useNavigate();
    const { 
        isAuthenticated, 
        userId, 
        username, 
        characters, 
        loadCharacters, 
        setAuthenticated,
        loadSessions,
        checkAuthPersistence,
        isGuest 
    } = useGameStore();
    
    // Page states
    const [currentPage, setCurrentPage] = useState<'landing' | 'home' | 'profile' | 'character-creation' | 'session-creation' | 'session-detail' | 'game-setup' | 'game'>('landing');
    const [localUserId, setLocalUserId] = useState<number | null>(null);
    const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
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

    // Handle authentication state changes
    useEffect(() => {
        if (isInitialized) {
            if (isAuthenticated && localUserId) {
                setCurrentPage('home');
            } else if (!isAuthenticated) {
                setCurrentPage('landing');
            }
        }
    }, [isAuthenticated, localUserId, isInitialized]);

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
            {currentPage === 'landing' && <LandingPage />}
            {currentPage === 'home' && <HomePage />}
            {currentPage === 'profile' && localUserId && (
                <ProfilePage 
                    userId={localUserId} 
                    onBack={() => setCurrentPage('home')}
                    onGoHome={() => setCurrentPage('home')}
                />
            )}
            {currentPage === 'character-creation' && localUserId && (
                <CharacterCreation
                    userId={localUserId}
                    onComplete={() => setCurrentPage('profile')}
                />
            )}
            {currentPage === 'session-creation' && localUserId && (
                <SessionCreation
                    userId={localUserId}
                    onComplete={() => setCurrentPage('home')}
                    onBack={() => setCurrentPage('home')}
                />
            )}
            {currentPage === 'session-detail' && selectedSessionId && (
                <SessionDetail
                    sessionId={selectedSessionId}
                    onBack={() => setCurrentPage('home')}
                    onLeave={() => setCurrentPage('home')}
                />
            )}
            {currentPage === 'game-setup' && selectedSessionId && (
                <GameSetup
                    sessionId={selectedSessionId}
                    onComplete={() => setCurrentPage('game')}
                    onBack={() => setCurrentPage('session-detail')}
                />
            )}
            {currentPage === 'game' && <GameLayout />}
        </ToastProvider>
    );
}

export default App;
