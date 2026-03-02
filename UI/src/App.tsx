import React, { useState } from 'react';
import { GameLayout } from './components/GameLayout';
import { ConnectionScreen } from './components/ConnectionScreen';
import { LandingPage } from './components/LandingPage';
import { ProfilePage } from './components/ProfilePage';
import { useGameStore } from './store/gameStore';
import './App.css';

function App() {
    const { mode, error, sessionId, isAuthenticated, setAuthenticated } = useGameStore();
    const [showLanding, setShowLanding] = useState(true);
    const [showProfile, setShowProfile] = useState(false);
    const [userId, setUserId] = useState<string | null>(null);

    // Handle showing profile
    const handleShowProfile = (id: string) => {
        setUserId(id);
        setShowProfile(true);
    };

    const handleBackFromProfile = () => {
        setShowProfile(false);
    };

    // If user is authenticated or has chosen to enter the game, show the game
    if (!showLanding || isAuthenticated) {
        // Show profile page if requested
        if (showProfile && userId) {
            return <ProfilePage userId={parseInt(userId)} onBack={handleBackFromProfile} />;
        }

        // Show connection screen only if explicitly in connecting mode
        if (mode === 'connecting') {
            return <ConnectionScreen />;
        }

        if (mode === 'error' && error) {
            return (
                <div className="error-screen">
                    <h1>Connection Error</h1>
                    <p>{error}</p>
                    <button onClick={() => window.location.reload()}>
                        Try Again
                    </button>
                </div>
            );
        }

        // Default: show game layout (demo mode)
        return <GameLayout />;
    }

    // Show landing page for first-time visitors
    return <LandingPage onShowProfile={handleShowProfile} />;
}

export default App;
