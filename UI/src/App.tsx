import React from 'react';
import { GameLayout } from './components/GameLayout';
import { ConnectionScreen } from './components/ConnectionScreen';
import { useGameStore } from './store/gameStore';
import './App.css';

function App() {
    const { mode, error, sessionId } = useGameStore();

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

export default App;
