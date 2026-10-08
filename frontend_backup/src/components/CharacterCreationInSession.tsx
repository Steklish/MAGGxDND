/**
 * CharacterCreationInSession.tsx
 * 
 * Creates a character within a session using the backend's delivery system.
 * This component is used when joining a session without an existing character.
 * 
 * Backend expects:
 * {
 *   session_id: string,
 *   character_name: string,
 *   character_prompt: string,
 *   character_class?: string,
 *   character_race?: string
 * }
 */

import React, { useState } from 'react';
import './CharacterCreation.css';

interface CharacterCreationInSessionProps {
    sessionId: string;
    onComplete: () => void;
    onCancel: () => void;
}

const RACES = ['Human', 'Elf', 'Dwarf', 'Halfling', 'Dragonborn', 'Tiefling', 'Gnome', 'Half-Elf', 'Half-Orc'];
const CLASSES = ['Barbarian', 'Bard', 'Cleric', 'Druid', 'Fighter', 'Monk', 'Paladin', 'Ranger', 'Rogue', 'Sorcerer', 'Warlock', 'Wizard'];

const CharacterCreationInSession: React.FC<CharacterCreationInSessionProps> = ({ sessionId, onComplete, onCancel }) => {
    const [formData, setFormData] = useState({
        name: '',
        race: 'Human',
        char_class: 'Fighter',
        description: ''
    });
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        // Validate
        const newErrors: Record<string, string> = {};
        if (!formData.name.trim()) {
            newErrors.name = 'Character name is required';
        }
        if (!formData.description.trim()) {
            newErrors.description = 'Brief description is required';
        }
        if (Object.keys(newErrors).length > 0) {
            setErrors(newErrors);
            return;
        }

        setIsLoading(true);

        try {
            // Create character through session delivery
            const response = await fetch('/api/v1/characters/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    character_name: formData.name,
                    character_prompt: formData.description,
                    character_class: formData.char_class,
                    character_race: formData.race
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to create character');
            }

            const data = await response.json();
            
            if (data.success) {
                console.log('Character created successfully:', data.character_name);
                onComplete();
            } else {
                throw new Error(data.message || 'Character creation failed');
            }
        } catch (error: any) {
            setErrors({ submit: error.message || 'Failed to create character' });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="character-creation-overlay">
            <div className="character-creation">
                <div className="cc-header">
                    <h2>Create Your Character</h2>
                    <p>Join the session with a new character</p>
                </div>

                {errors.submit && (
                    <div className="cc-error">
                        <span>⚠️</span>
                        <span>{errors.submit}</span>
                    </div>
                )}

                <form className="cc-form" onSubmit={handleSubmit}>
                    <div className="form-group large">
                        <label htmlFor="char-name">Character Name</label>
                        <input
                            type="text"
                            id="char-name"
                            value={formData.name}
                            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                            placeholder="Enter character name..."
                            maxLength={50}
                            className={errors.name ? 'error' : ''}
                            autoFocus
                        />
                        {errors.name && <span className="error-message">{errors.name}</span>}
                    </div>

                    <div className="form-group">
                        <label htmlFor="char-race">Race</label>
                        <select
                            id="char-race"
                            value={formData.race}
                            onChange={(e) => setFormData(prev => ({ ...prev, race: e.target.value }))}
                        >
                            {RACES.map(race => (
                                <option key={race} value={race}>{race}</option>
                            ))}
                        </select>
                    </div>

                    <div className="form-group">
                        <label htmlFor="char-class">Class</label>
                        <select
                            id="char-class"
                            value={formData.char_class}
                            onChange={(e) => setFormData(prev => ({ ...prev, char_class: e.target.value }))}
                        >
                            {CLASSES.map(cls => (
                                <option key={cls} value={cls}>{cls}</option>
                            ))}
                        </select>
                    </div>

                    <div className="form-group large">
                        <label htmlFor="char-desc">Brief Description</label>
                        <textarea
                            id="char-desc"
                            value={formData.description}
                            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                            placeholder="A brave warrior seeking adventure..."
                            maxLength={500}
                            rows={4}
                            className={errors.description ? 'error' : ''}
                        />
                        {errors.description && <span className="error-message">{errors.description}</span>}
                        <p className="hint">The AI will use this to generate your character</p>
                    </div>

                    <div className="cc-actions">
                        <button type="button" className="cc-cancel" onClick={onCancel}>
                            Cancel
                        </button>
                        <button type="submit" className="cc-next" disabled={isLoading}>
                            {isLoading ? 'Creating...' : 'Create Character'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default CharacterCreationInSession;
