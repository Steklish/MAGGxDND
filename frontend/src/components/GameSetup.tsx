import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './GameSetup.css';

interface GameSetupProps {
    sessionId: string;
    onComplete: (sessionId: string) => void;
    onBack: () => void;
}

export const GameSetup: React.FC<GameSetupProps> = ({ sessionId, onComplete, onBack }) => {
    const [step, setStep] = useState<1 | 2 | 3>(1);
    const [wishes, setWishes] = useState('');
    const [characterChoice, setCharacterChoice] = useState<'existing' | 'ai-create' | 'ai-random'>('existing');
    const [characterDescription, setCharacterDescription] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);

    const handleContinue = () => {
        if (step < 3) {
            setStep((prev) => (prev + 1) as 2 | 3);
        }
    };

    const handleBack = () => {
        if (step > 1) {
            setStep(step as 1 | 2);
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

            // Build character prompt based on selection
            let characterPrompt = '';
            if (characterChoice === 'ai-create' && characterDescription) {
                characterPrompt = characterDescription;
            } else if (characterChoice === 'ai-random') {
                characterPrompt = 'Create a random D&D character with interesting backstory and abilities';
            }

            // Use the existing /start endpoint which initializes the session
            const gameSetup = {
                wishes: wishes || 'Create an exciting adventure with interesting NPCs and challenging encounters',
                scene_prompt: undefined,
                character_prompts: characterPrompt ? [characterPrompt] : [],
                character_description: characterPrompt,
                npc_prompts: [] // Empty = backend will use random variety
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
                
                // Save playerId from response if available
                if (data.player_id) {
                    localStorage.setItem('currentPlayerId', data.player_id);
                    console.log('✓ PlayerId saved:', data.player_id);
                }
                
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
        setCharacterChoice('ai-random');
    };

    return (
        <div className="game-setup">
            <div className="setup-header">
                <div className="header-spacer"></div>
                <h2>Game Setup</h2>
                <div className="setup-progress">
                    <div className="progress-fill" style={{ width: step === 1 ? '0%' : step === 2 ? '50%' : '100%' }}></div>
                    <div className={`step ${step >= 1 ? (step > 1 ? 'completed' : 'active') : ''}`}>
                        <span className="step-number">1</span>
                        <span className="step-label">Adventure</span>
                    </div>
                    <div className={`step ${step >= 2 ? (step > 2 ? 'completed' : 'active') : ''}`}>
                        <span className="step-number">2</span>
                        <span className="step-label">Character</span>
                    </div>
                    <div className={`step ${step >= 3 ? 'completed' : ''}`}>
                        <span className="step-number">3</span>
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
                        <h3>🧙 Character Selection</h3>
                        <p className="step-description">
                            How would you like to play?
                        </p>

                        <div className="character-options">
                            <button
                                type="button"
                                className={`option-card ${characterChoice === 'existing' ? 'selected' : ''}`}
                                onClick={() => setCharacterChoice('existing')}
                            >
                                <div className="option-icon">📋</div>
                                <h4>Use Existing Character</h4>
                                <p>Select from your created characters</p>
                            </button>

                            <button
                                type="button"
                                className={`option-card ${characterChoice === 'ai-create' ? 'selected' : ''}`}
                                onClick={() => setCharacterChoice('ai-create')}
                            >
                                <div className="option-icon">🎨</div>
                                <h4>AI Create Character</h4>
                                <p>Describe your ideal character and AI will create it</p>
                                {characterChoice === 'ai-create' && (
                                    <textarea
                                        className="char-desc-input"
                                        placeholder="Describe your character... (e.g., 'A wise old wizard who seeks ancient knowledge')"
                                        value={characterDescription}
                                        onChange={(e) => setCharacterDescription(e.target.value)}
                                        onClick={(e) => e.stopPropagation()}
                                    />
                                )}
                            </button>

                            <button
                                type="button"
                                className={`option-card ${characterChoice === 'ai-random' ? 'selected' : ''}`}
                                onClick={() => setCharacterChoice('ai-random')}
                            >
                                <div className="option-icon">🎲</div>
                                <h4>Random Character</h4>
                                <p>Let AI create a completely random character for you</p>
                            </button>
                        </div>
                    </div>
                )}

                {step === 3 && (
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
                                <h4>🧙 Character</h4>
                                <p>
                                    {characterChoice === 'existing' && 'Use your existing character'}
                                    {characterChoice === 'ai-create' && 'AI will create character based on your description'}
                                    {characterChoice === 'ai-random' && 'AI will create a random character'}
                                </p>
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

            {step < 3 && (
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
