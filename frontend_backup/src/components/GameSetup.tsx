import React, { useState } from 'react';
import './GameSetup.css';

interface GameSetupProps {
    sessionId: string;
    onComplete: (sessionId: string) => void;
    onBack: () => void;
}

export const GameSetup: React.FC<GameSetupProps> = ({ sessionId, onComplete, onBack }) => {
    const [step, setStep] = useState<1 | 2>(1);
    const [wishes, setWishes] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);

    const handleContinue = () => {
        if (step < 2) {
            setStep(2);
        }
    };

    const handleBack = () => {
        if (step > 1) {
            setStep(1);
        } else {
            onBack();
        }
    };

    const handleStartGame = async () => {
        setIsGenerating(true);

        try {
            // Clear old session data from localStorage to ensure fresh start
            localStorage.removeItem('currentSessionId');
            localStorage.removeItem('currentPlayerId');
            localStorage.removeItem('gameStatus');
            localStorage.removeItem('currentSessionName');
            localStorage.removeItem('activeSessionIds');
            console.log('[GameSetup] Cleared old session data from localStorage');

            // Build request - characters are auto-assigned from database participants
            const gameSetup = {
                wishes: wishes || 'Create an exciting adventure with interesting NPCs and challenging encounters',
                scene_prompt: undefined,
                character_prompts: [],  // Empty = backend auto-generates for each participant
                npc_prompts: []  // Empty = backend uses random variety
            };

            console.log('[GameSetup] Starting session with:', gameSetup);

            // Call backend API to start session
            const response = await fetch(`/api/v1/sessions/${sessionId}/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify(gameSetup),
            });

            // Get response text first
            const responseText = await response.text();
            console.log('[GameSetup] Response status:', response.status);
            console.log('[GameSetup] Response text:', responseText);

            if (response.ok) {
                const data = JSON.parse(responseText);
                console.log('[GameSetup] Session started successfully:', data);

                // The session is now running but the owner hasn't chosen a character yet.
                // Navigate to JoinSession so the owner can pick their character.
                localStorage.setItem('currentSessionId', sessionId);
                localStorage.setItem('gameStatus', 'running');

                // Pass session ID to parent for navigation
                onComplete(sessionId);
            } else {
                let errorData;
                try {
                    errorData = JSON.parse(responseText);
                } catch {
                    errorData = { detail: responseText || 'Unknown error' };
                }
                console.error('[GameSetup] Failed to start session:', errorData);
                alert(`Failed to start: ${errorData.detail || 'Unknown error'}`);
            }
        } catch (error: any) {
            console.error('[GameSetup] Failed to start game:', error);
            alert(`Network error: ${error.message || 'Please try again'}`);
        } finally {
            setIsGenerating(false);
        }
    };

    const handleUseAI = () => {
        setWishes('Create an exciting adventure with interesting NPCs and challenging encounters');
    };

    return (
        <div className="game-setup">
            <div className="setup-header">
                <div className="header-spacer"></div>
                <h2>Game Setup</h2>
                <div className="setup-progress">
                    <div className="progress-fill" style={{ width: step === 1 ? '0%' : '100%' }}></div>
                    <div className={`step ${step >= 1 ? (step > 1 ? 'completed' : 'active') : ''}`}>
                        <span className="step-number">1</span>
                        <span className="step-label">Adventure</span>
                    </div>
                    <div className={`step ${step >= 2 ? 'completed' : ''}`}>
                        <span className="step-number">2</span>
                        <span className="step-label">Ready</span>
                    </div>
                </div>
            </div>

            <div className="setup-content">
                {step === 1 && (
                    <div className="setup-step fade-in">
                        <h3>🎭 What kind of adventure do you want?</h3>
                        <p className="step-description">
                            Tell us what you're looking for in this gaming session.
                            The AI will use your preferences to create an unforgettable experience.
                        </p>

                        <textarea
                            className="wishes-input"
                            placeholder="Describe your desired adventure... (e.g., 'A dark mystery in a haunted castle', 'Epic dragon battle', 'Political intrigue in the capital')"
                            value={wishes}
                            onChange={(e) => setWishes(e.target.value)}
                            maxLength={1000}
                        />

                        <div className="char-count">{wishes.length}/1000</div>

                        <div className="quick-options">
                            <button
                                type="button"
                                className="quick-btn"
                                onClick={() => setWishes('A mysterious dungeon with ancient treasures and dangerous monsters')}
                            >
                                🏰 Dungeon Crawl
                            </button>
                            <button
                                type="button"
                                className="quick-btn"
                                onClick={() => setWishes('Political intrigue and social encounters in a bustling city')}
                            >
                                👑 Political Intrigue
                            </button>
                            <button
                                type="button"
                                className="quick-btn"
                                onClick={() => setWishes('Wilderness exploration with survival challenges')}
                            >
                                🌲 Wilderness Adventure
                            </button>
                            <button
                                type="button"
                                className="quick-btn"
                                onClick={() => setWishes('Horror and mystery in a haunted location')}
                            >
                                👻 Horror Mystery
                            </button>
                        </div>

                        <button type="button" className="btn-ai-fill" onClick={handleUseAI}>
                            ✨ Let AI Decide
                        </button>
                    </div>
                )}

                {step === 2 && (
                    <div className="setup-step fade-in">
                        <h3>✅ Ready to Begin</h3>
                        <p className="step-description">
                            Review your choices and start the adventure!
                        </p>

                        <div className="setup-summary">
                            <div className="summary-card">
                                <h4>🎭 Adventure Preferences</h4>
                                <p>{wishes || 'AI will create an exciting adventure'}</p>
                            </div>

                            <div className="summary-card">
                                <h4>👥 Characters & Players</h4>
                                <p>Characters will be automatically assigned to all joined players</p>
                                <p className="summary-note">Each player will receive a unique character based on their name</p>
                            </div>

                            <div className="summary-card">
                                <h4>🎭 NPCs & World</h4>
                                <p>AI will generate interesting NPCs and encounters for your adventure</p>
                            </div>
                        </div>

                        <button
                            type="button"
                            className="btn-start-game"
                            onClick={handleStartGame}
                            disabled={isGenerating}
                        >
                            {isGenerating ? (
                                <>
                                    <span className="loading-spinner"></span>
                                    Generating Adventure...
                                </>
                            ) : (
                                <>
                                    🚀 Start Adventure
                                </>
                            )}
                        </button>
                    </div>
                )}
            </div>

            {step < 2 && (
                <div className="setup-footer">
                    <button
                        type="button"
                        className="btn-secondary"
                        onClick={handleBack}
                    >
                        ← Back
                    </button>
                    <button
                        type="button"
                        className="btn-primary"
                        onClick={handleContinue}
                        disabled={step === 1 && !wishes}
                    >
                        Continue →
                    </button>
                </div>
            )}
        </div>
    );
};
