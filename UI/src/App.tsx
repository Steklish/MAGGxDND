import React, { useState, useEffect } from 'react';
import { GameLayout } from './components/GameLayout';
import { LandingPage } from './components/LandingPage';
import { ProfilePage } from './components/ProfilePage';
import { CharacterCreation } from './components/CharacterCreation';
import { SessionCreation } from './components/SessionCreation';
import { SessionDetail } from './components/SessionDetail';
import { useGameStore } from './store/gameStore';
import './App.css';

function App() {
    const { isAuthenticated, userId, characters, loadCharacters, setAuthenticated } = useGameStore();
    const [showProfile, setShowProfile] = useState(false);
    const [showCharacterCreation, setShowCharacterCreation] = useState(false);
    const [showSessionCreation, setShowSessionCreation] = useState(false);
    const [showSessionDetail, setShowSessionDetail] = useState(false);
    const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
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

    // Listen for show-profile event from GameLayout
    useEffect(() => {
        const handleShowProfile = () => {
            if (localUserId) {
                setShowProfile(true);
            }
        };

        window.addEventListener('show-profile', handleShowProfile);
        return () => window.removeEventListener('show-profile', handleShowProfile);
    }, [localUserId]);

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

    const handleShowSessionCreation = () => {
        setShowSessionCreation(true);
    };

    const handleShowSessionDetail = (sessionId: string) => {
        setSelectedSessionId(sessionId);
        setShowSessionDetail(true);
    };

    const handleJoinSession = async (sessionId: string) => {
        try {
            const username = localStorage.getItem('username') || 'Player';
            const response = await fetch(`/api/v1/sessions/${sessionId}/players`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ player_name: username }),
            });
            
            if (!response.ok) throw new Error('Failed to join');
            const data = await response.json();
            
            // Store connection info
            localStorage.setItem('currentSessionId', sessionId);
            localStorage.setItem('currentPlayerId', data.player_id);
            
            // Set authenticated and redirect to game
            setAuthenticated(true);
            setShowProfile(false);
            setShowSessionDetail(false);
            
            // Force reload to update GameLayout with new session info
            window.location.reload();
        } catch (error) {
            console.error('Failed to join session:', error);
            alert('Failed to join session. Make sure backend is running on port 8000.');
        }
    };

    const handleSessionDetailBack = () => {
        setShowSessionDetail(false);
        setSelectedSessionId(null);
    };

    const handleCharacterComplete = () => {
        setShowCharacterCreation(false);
        setShowProfile(true);
        if (localUserId) {
            loadCharacters(localUserId);
        }
    };

    const handleSessionComplete = (sessionId: string) => {
        setShowSessionCreation(false);
        // Redirect to game with session
        console.log('Session created:', sessionId);
        // TODO: Redirect to game session
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

    // Show session detail if requested
    if (showSessionDetail && selectedSessionId) {
        return (
            <SessionDetail
                sessionId={selectedSessionId}
                onBack={handleSessionDetailBack}
                onLeave={handleSessionDetailBack}
            />
        );
    }

    // Show session creation if requested
    if (showSessionCreation && localUserId) {
        return (
            <SessionCreation
                userId={localUserId}
                onComplete={handleSessionComplete}
                onBack={() => setShowSessionCreation(false)}
            />
        );
    }

    // Show character creation if requested
    if (showCharacterCreation && localUserId) {
        return (
            <CharacterCreation
                userId={localUserId}
                onComplete={handleCharacterComplete}
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
                onCreateSession={handleShowSessionCreation}
                onViewSession={handleShowSessionDetail}
                onJoinSession={handleJoinSession}
            />
        );
    }

    // Show game layout if authenticated
    if (isAuthenticated) {
        return <GameLayout onCreateSession={handleShowSessionCreation} onViewSession={handleShowSessionDetail} onJoinSession={handleJoinSession} />;
    }

    // Default: show landing page
    return (
        <LandingPage
            onShowProfile={handleShowProfile}
        />
    );
}

export default App;
