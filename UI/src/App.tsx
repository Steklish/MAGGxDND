import React from 'react';
import { GameLayout } from './components/GameLayout';
import { ConnectionScreen } from './components/ConnectionScreen';
import { useGameStore } from './store/gameStore';
import './App.css';

function App() {
    const { mode, error } = useGameStore();

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

    return <GameLayout />;
}

export default App;
