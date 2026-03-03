import React, { useState, useEffect } from 'react';
import { GameLayout } from './components/GameLayout';
import { LandingPage } from './components/LandingPage';
import { ProfilePage } from './components/ProfilePage';
import { CharacterCreation } from './components/CharacterCreation';
import { useGameStore } from './store/gameStore';
import './App.css';

function App() {
    const { isAuthenticated, userId, characters, loadCharacters } = useGameStore();
    const [showProfile, setShowProfile] = useState(false);
    const [showCharacterCreation, setShowCharacterCreation] = useState(false);
    const [localUserId, setLocalUserId] = useState<number | null>(null);
    const [isInitialized, setIsInitialized] = useState(false);

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
        setIsInitialized(true);
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

    // Show nothing while initializing
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

    // Show game layout if authenticated
    if (isAuthenticated) {
        return <GameLayout />;
    }

    // Default: show landing page
    return (
        <LandingPage
            onShowProfile={handleShowProfile}
        />
    );
}

export default App;
