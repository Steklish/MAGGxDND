import React, { useState, useEffect } from 'react';
import { GameLayout } from './components/GameLayout';
import { LandingPage } from './components/LandingPage';
import { ProfilePage } from './components/ProfilePage';
import { CharacterCreation } from './components/CharacterCreation';
import { SessionCreation } from './components/SessionCreation';
import { SessionDetail } from './components/SessionDetail';
import { SessionLobby } from './components/SessionLobby';
import { GamePage } from './components/GamePage';
import { useGameStore } from './store/gameStore';
import './App.css';

function App() {
    const { isAuthenticated, userId, characters, loadCharacters } = useGameStore();
    const [showProfile, setShowProfile] = useState(false);
    const [showCharacterCreation, setShowCharacterCreation] = useState(false);
    const [showSessionCreation, setShowSessionCreation] = useState(false);
    const [showSessionDetail, setShowSessionDetail] = useState(false);
    const [showSessionLobby, setShowSessionLobby] = useState(false);
    const [showGame, setShowGame] = useState(false);
    const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
    const [playerId, setPlayerId] = useState<string | null>(null);
    const [gameData, setGameData] = useState<any>(null);
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

    const handleJoinSession = (sessionId: string) => {
        setSelectedSessionId(sessionId);
        // Generate player ID for now (TODO: Get from backend)
        setPlayerId(`player_${Date.now()}`);
        setShowSessionLobby(true);
    };

    const handleSessionLobbyLeave = () => {
        setShowSessionLobby(false);
        setSelectedSessionId(null);
        setPlayerId(null);
    };

    const handleGameStart = (data: any) => {
        setGameData(data);
        setShowSessionLobby(false);
        setShowGame(true);
    };

    const handleGameLeave = () => {
        setShowGame(false);
        setGameData(null);
        handleSessionLobbyLeave();
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

    // Show game page if in game
    if (showGame && gameData) {
        return (
            <GamePage
                sessionId={selectedSessionId!}
                players={gameData.players}
                scene={gameData.scene}
                onLeave={handleGameLeave}
            />
        );
    }

    // Show session lobby if requested
    if (showSessionLobby && selectedSessionId && playerId) {
        return (
            <SessionLobby
                sessionId={selectedSessionId}
                playerId={playerId}
                isHost={true} // TODO: Get from backend
                onGameStart={handleGameStart}
                onLeave={handleSessionLobbyLeave}
            />
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
