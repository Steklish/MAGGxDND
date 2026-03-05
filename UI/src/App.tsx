import React, { useState, useEffect } from 'react';
import { GameLayout } from './components/GameLayout';
import { LandingPage } from './components/LandingPage';
import { ProfilePage } from './components/ProfilePage';
import { CharacterCreation } from './components/CharacterCreation';
import { SessionCreation } from './components/SessionCreation';
import { SessionDetail } from './components/SessionDetail';
import { ToastProvider } from './components/common/Toast';
import { useGameStore } from './store/gameStore';
import './App.css';

function App() {
    const { isAuthenticated, userId, characters, loadCharacters, setAuthenticated, loadSessions } = useGameStore();
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
        console.log('🔵 Joining session:', sessionId);
        
        // Check if already joined this session
        const existingSessionId = localStorage.getItem('currentSessionId');
        const existingPlayerId = localStorage.getItem('currentPlayerId');
        
        if (existingSessionId && existingPlayerId) {
            // Already in a session - just open game interface
            console.log('✅ Already in session, opening game interface');
            setAuthenticated(true);
            return;
        }
        
        try {
            const username = localStorage.getItem('username') || 'Player';
            console.log('🔵 Username:', username);

            const response = await fetch(`/api/v1/sessions/${sessionId}/players`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ player_name: username }),
            });

            console.log('🔵 Response status:', response.status);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('🔴 Error response:', errorText);
                
                // Check for specific errors
                if (response.status === 400) {
                    if (errorText.includes('Session is full')) {
                        console.error('❌ Session is full');
                        return;
                    } else if (errorText.includes('already joined')) {
                        console.error('❌ Already joined this session');
                        return;
                    }
                }
                
                throw new Error(`Failed to join: ${response.status}`);
            }

            const data = await response.json();
            console.log('🟢 Joined successfully:', data);

            // Store connection info
            localStorage.setItem('currentSessionId', sessionId);
            localStorage.setItem('currentPlayerId', data.player_id);

            console.log('💾 Stored session:', sessionId);
            console.log('💾 Stored player:', data.player_id);

            // Update store with session info
            setAuthenticated(true);
            
            // Reload sessions to show updated player count
            loadSessions();

            console.log('✅ Session joined, game interface will open');
            // No reload needed - GameLayout will detect session from localStorage
        } catch (error) {
            console.error('🔴 Failed to join session:', error);
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

    // Show game layout if authenticated OR if already in active session
    const hasActiveSession = typeof window !== 'undefined' && localStorage.getItem('currentSessionId') && localStorage.getItem('currentPlayerId');
    
    if (isAuthenticated || hasActiveSession) {
        return <GameLayout onCreateSession={handleShowSessionCreation} onViewSession={handleShowSessionDetail} onJoinSession={handleJoinSession} />;
    }

    // Default: show landing page
    return (
        <LandingPage
            onShowProfile={handleShowProfile}
        />
    );
}

// Wrap entire app with ToastProvider
const AppWithProvider = () => (
    <ToastProvider>
        <App />
    </ToastProvider>
);

export default AppWithProvider;
