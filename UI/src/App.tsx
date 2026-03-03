import React, { useState, useEffect } from 'react';
import { GameLayout } from './components/GameLayout';
import { ConnectionScreen } from './components/ConnectionScreen';
import { LandingPage } from './components/LandingPage';
import { ProfilePage } from './components/ProfilePage';
import { CharacterCreation } from './components/CharacterCreation';
import { useGameStore } from './store/gameStore';
import './App.css';

function App() {
    const { isAuthenticated, userId, characters, loadCharacters, setAuthenticated } = useGameStore();
    const [showLanding, setShowLanding] = useState(true);
    const [showProfile, setShowProfile] = useState(false);
    const [showCharacterCreation, setShowCharacterCreation] = useState(false);
    const [localUserId, setLocalUserId] = useState<number | null>(null);

    // Initialize from localStorage on mount
    useEffect(() => {
        const storedUserId = localStorage.getItem('userId');
        const storedUsername = localStorage.getItem('username');
        const token = localStorage.getItem('access_token');
        
        if (storedUserId && token && storedUsername) {
            const id = parseInt(storedUserId);
            setLocalUserId(id);
            loadCharacters(id);
        }
    }, []);

    // Handle showing profile
    const handleShowProfile = (id: string) => {
        const userId = parseInt(id);
        setLocalUserId(userId);
        setShowProfile(true);
        loadCharacters(userId);
    };

    const handleBackFromProfile = () => {
        setShowProfile(false);
    };

    const handleShowCharacterCreation = () => {
        setShowCharacterCreation(true);
        setShowProfile(false);
    };

    const handleCharacterCreationComplete = () => {
        setShowCharacterCreation(false);
        setShowProfile(true);
        if (localUserId) {
            loadCharacters(localUserId);
        }
    };

    const handleQuickStart = () => {
        // Demo mode - just show the game layout with mock data
        setAuthenticated(true);
        setShowLanding(false);
    };

    // If user is authenticated or has chosen to enter the game, show the game
    if (!showLanding || isAuthenticated) {
        // Show character creation if requested
        if (showCharacterCreation && localUserId) {
            return (
                <CharacterCreation
                    userId={localUserId}
                    onComplete={handleCharacterCreationComplete}
                />
            );
        }

        // Show profile page if requested
        if (showProfile && localUserId) {
            return (
                <ProfilePage
                    userId={localUserId}
                    onBack={handleBackFromProfile}
                    onCreateCharacter={handleShowCharacterCreation}
                />
            );
        }

        // Show connection screen only if explicitly in connecting mode
        if (useGameStore.getState().mode === 'connecting') {
            return <ConnectionScreen />;
        }

        // Show error if there's an error
        if (useGameStore.getState().mode === 'error' && useGameStore.getState().error) {
            return (
                <div className="error-screen">
                    <h1>Connection Error</h1>
                    <p>{useGameStore.getState().error}</p>
                    <button onClick={() => window.location.reload()}>
                        Try Again
                    </button>
                </div>
            );
        }

        // Default: show game layout (demo mode or authenticated)
        return <GameLayout />;
    }

    // Show landing page for first-time visitors
    return (
        <LandingPage
            onShowProfile={handleShowProfile}
        />
    );
}

export default App;
