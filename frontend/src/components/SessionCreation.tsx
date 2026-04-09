import React, { useState } from 'react';
import axios from 'axios';
import './SessionCreation.css';

// Game mode options
const gameModes = [
    {
        value: 'STORY',
        label: 'Story Mode',
        icon: '📖',
        description: 'Focus on narrative and exploration'
    },
    {
        value: 'COMBAT',
        label: 'Combat Mode',
        icon: '⚔️',
        description: 'Turn-based tactical combat'
    }
];

interface SessionCreationProps {
    userId: number;
    onComplete: (sessionId: string) => void;
    onBack: () => void;
}

export const SessionCreation: React.FC<SessionCreationProps> = ({ userId: _userId, onComplete, onBack }) => {
    const [isLoading, setIsLoading] = useState(false);
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [step, setStep] = useState(1);
    const [formData, setFormData] = useState({
        session_name: '',
        game_mode: 'STORY',
        max_players: 5,
        description: '',
        is_public: true,
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
        if (errors[name]) {
            setErrors(prev => ({ ...prev, [name]: '' }));
        }
    };

    const handleNumberChange = (field: string, delta: number) => {
        setFormData(prev => {
            const newValue = Math.max(2, Math.min(10, (prev[field as keyof typeof prev] as number) + delta));
            return { ...prev, [field]: newValue };
        });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        console.log('Form submitted, current step:', step);
        console.log('Form data:', formData);

        // Prevent double submission
        if (isLoading) {
            console.log('Already loading, returning early');
            return;
        }

        setIsLoading(true);
        setErrors({});

        const newErrors: Record<string, string> = {};
        if (!formData.session_name) newErrors.session_name = 'Session name is required';
        if (formData.session_name.length < 3) newErrors.session_name = 'Name must be at least 3 characters';

        if (Object.keys(newErrors).length > 0) {
            setErrors(newErrors);
            setIsLoading(false);
            console.log('Validation errors:', newErrors);
            return;
        }

        try {
            const sessionData = {
                session_name: formData.session_name,
                game_mode: formData.game_mode,
                max_players: formData.max_players,
                description: formData.description,
            };

            console.log('Sending request to /api/v1/sessions:', sessionData);
            const response = await axios.post('/api/v1/sessions', sessionData);
            console.log('Session creation response status:', response.status);
            console.log('Session creation response data:', response.data);

            if (response.data && response.data.session_id) {
                console.log('Session ID received:', response.data.session_id);
                // Auto-join the session as owner
                try {
                    const username = localStorage.getItem('username') || 'Owner';
                    console.log('Joining session as:', username);
                    await axios.post(`/api/v1/sessions/${response.data.session_id}/players`, {
                        player_name: username
                    });
                    console.log('✓ Owner joined session:', response.data.session_id);
                } catch (joinError) {
                    console.warn('Failed to auto-join session:', joinError);
                }

                console.log('Calling onComplete with session ID');
                setIsLoading(false);
                onComplete(response.data.session_id);
            } else {
                console.error('No session_id in response:', response.data);
                setErrors({ submit: 'Session created but no session ID returned' });
                setIsLoading(false);
            }
        } catch (error: any) {
            console.error('Session creation error:', error);
            console.error('Error response:', error.response?.data);
            console.error('Error status:', error.response?.status);
            console.error('Error message:', error.message);
            setIsLoading(false);
            if (error.response) {
                setErrors({ submit: error.response.data.detail || 'Failed to create session' });
            } else if (error.request) {
                setErrors({ submit: 'No response from server. Is the backend running?' });
            } else {
                setErrors({ submit: 'Network error. Please try again.' });
            }
        }
    };

    return (
        <div className="session-creation-overlay">
            <div className="session-creation">
                <div className="sc-header">
                    <h2>Create Game Session</h2>
                    <p>Start your epic adventure with friends</p>
                </div>

                <div className="sc-progress">
                    <div className={`progress-step ${step >= 1 ? 'active' : ''}`}>
                        <span className="step-number">1</span>
                        <span className="step-label">Basics</span>
                    </div>
                    <div className="progress-line"></div>
                    <div className={`progress-step ${step >= 2 ? 'active' : ''}`}>
                        <span className="step-number">2</span>
                        <span className="step-label">Settings</span>
                    </div>
                    <div className="progress-line"></div>
                    <div className={`progress-step ${step >= 3 ? 'active' : ''}`}>
                        <span className="step-number">3</span>
                        <span className="step-label">Review</span>
                    </div>
                </div>

                {errors.submit && (
                    <div className="sc-error">
                        <span>⚠️</span>
                        <span>{errors.submit}</span>
                    </div>
                )}

                <form className="sc-form" onSubmit={handleSubmit}>
                    {step === 1 && (
                        <div className="sc-section fade-in">
                            <h3>Session Basics</h3>

                            <div className="form-group">
                                <label htmlFor="session_name">Session Name *</label>
                                <input
                                    type="text"
                                    id="session_name"
                                    name="session_name"
                                    value={formData.session_name}
                                    onChange={handleChange}
                                    placeholder="Enter session name"
                                    className={errors.session_name ? 'error' : ''}
                                    autoFocus
                                />
                                {errors.session_name && <span className="error-message">{errors.session_name}</span>}
                            </div>

                            <div className="form-group">
                                <label htmlFor="description">Description (Optional)</label>
                                <textarea
                                    id="description"
                                    name="description"
                                    value={formData.description}
                                    onChange={handleChange}
                                    placeholder="Describe your session theme, story, or rules..."
                                    rows={4}
                                />
                            </div>

                            <div className="sc-actions">
                                <button type="button" className="sc-cancel" onClick={onBack}>Cancel</button>
                                <button type="button" className="sc-next" onClick={() => setStep(2)}>Next →</button>
                            </div>
                        </div>
                    )}

                    {step === 2 && (
                        <div className="sc-section fade-in">
                            <h3>Game Settings</h3>

                            <div className="form-group">
                                <label>Game Mode</label>
                                <div className="mode-grid">
                                    {gameModes.map(mode => (
                                        <button
                                            key={mode.value}
                                            type="button"
                                            className={`mode-card ${formData.game_mode === mode.value ? 'selected' : ''}`}
                                            onClick={() => setFormData(prev => ({ ...prev, game_mode: mode.value }))}
                                        >
                                            <span className="mode-icon">{mode.icon}</span>
                                            <span className="mode-name">{mode.label}</span>
                                            <span className="mode-desc">{mode.description}</span>
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Max Players</label>
                                <div className="player-count-control">
                                    <button
                                        type="button"
                                        onClick={() => handleNumberChange('max_players', -1)}
                                        className="count-btn"
                                    >
                                        -
                                    </button>
                                    <span className="count-value">{formData.max_players} players</span>
                                    <button
                                        type="button"
                                        onClick={() => handleNumberChange('max_players', 1)}
                                        className="count-btn"
                                    >
                                        +
                                    </button>
                                </div>
                                <div className="player-range">
                                    <span>2</span>
                                    <div className="range-bar">
                                        <div className="range-fill" style={{ width: `${((formData.max_players - 2) / 8) * 100}%` }}></div>
                                    </div>
                                    <span>10</span>
                                </div>
                            </div>

                            <div className="sc-actions">
                                <button type="button" className="sc-back" onClick={() => setStep(1)}>← Back</button>
                                <button type="button" className="sc-next" onClick={() => setStep(3)}>Next →</button>
                            </div>
                        </div>
                    )}

                    {step === 3 && (
                        <div className="sc-section fade-in">
                            <h3>Review Session</h3>
                            
                            <div className="session-preview">
                                <div className="preview-icon">🎲</div>
                                <h4>{formData.session_name}</h4>
                                <div className="preview-details">
                                    <div className="preview-item">
                                        <span className="preview-label">Mode:</span>
                                        <span className="preview-value">{gameModes.find(m => m.value === formData.game_mode)?.label}</span>
                                    </div>
                                    <div className="preview-item">
                                        <span className="preview-label">Players:</span>
                                        <span className="preview-value">{formData.max_players} max</span>
                                    </div>
                                </div>
                                {formData.description && (
                                    <div className="preview-description">
                                        <p>{formData.description}</p>
                                    </div>
                                )}
                            </div>

                            <div className="sc-actions">
                                <button type="button" className="sc-back" onClick={() => setStep(2)}>← Back</button>
                                <button 
                                    type="submit" 
                                    className="sc-submit" 
                                    disabled={isLoading}
                                >
                                    {isLoading ? 'Creating...' : '🚀 Create Session'}
                                </button>
                            </div>
                        </div>
                    )}
                </form>
            </div>
        </div>
    );
};
