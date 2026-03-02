import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './CharacterCreation.css';

interface CharacterCreationProps {
    userId: number;
    onComplete: () => void;
}

export const CharacterCreation: React.FC<CharacterCreationProps> = ({ userId, onComplete }) => {
    const navigate = useNavigate();
    const [isLoading, setIsLoading] = useState(false);
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [formData, setFormData] = useState({
        name: '',
        race: 'Human',
        char_class: 'Fighter',
        backstory: '',
        strength: 15,
        dexterity: 12,
        constitution: 14,
        intelligence: 10,
        wisdom: 10,
        charisma: 10,
    });

    const races = ['Human', 'Elf', 'Dwarf', 'Halfling', 'Orc', 'Tiefling', 'Dragonborn'];
    const classes = ['Fighter', 'Wizard', 'Rogue', 'Cleric', 'Ranger', 'Paladin', 'Barbarian', 'Bard'];

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
        if (errors[name]) {
            setErrors(prev => ({ ...prev, [name]: '' }));
        }
    };

    const handleStatChange = (stat: string, delta: number) => {
        setFormData(prev => {
            const newValue = Math.max(1, Math.min(30, prev[stat as keyof typeof prev] as number + delta));
            return { ...prev, [stat]: newValue };
        });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setErrors({});

        // Validate
        const newErrors: Record<string, string> = {};
        if (!formData.name) newErrors.name = 'Character name is required';
        if (formData.name.length < 3) newErrors.name = 'Name must be at least 3 characters';

        if (Object.keys(newErrors).length > 0) {
            setErrors(newErrors);
            setIsLoading(false);
            return;
        }

        try {
            const characterData = {
                user_id: userId,
                name: formData.name,
                race: formData.race,
                char_class: formData.char_class,
                level: 1,
                backstory_summary: formData.backstory,
                personality_traits: '[]',
                max_hp: 30,
                current_hp: 30,
                armor_class: 12,
                speed: 30,
                stats: {
                    strength: formData.strength,
                    dexterity: formData.dexterity,
                    constitution: formData.constitution,
                    intelligence: formData.intelligence,
                    wisdom: formData.wisdom,
                    charisma: formData.charisma,
                },
                abilities: [],
                inventory: [],
            };

            const response = await axios.post('/api/v1/characters/', characterData);
            
            if (response.data.id) {
                onComplete();
            }
        } catch (error: any) {
            setIsLoading(false);
            if (error.response) {
                setErrors({ submit: error.response.data.detail || 'Failed to create character' });
            } else {
                setErrors({ submit: 'Network error. Please try again.' });
            }
        }
    };

    return (
        <div className="character-creation-overlay">
            <div className="character-creation">
                <div className="cc-header">
                    <h2>Create Your Character</h2>
                    <p>Forge your hero and begin your epic adventure</p>
                </div>

                {errors.submit && (
                    <div className="cc-error">
                        <span>⚠️</span>
                        <span>{errors.submit}</span>
                    </div>
                )}

                <form className="cc-form" onSubmit={handleSubmit}>
                    <div className="cc-section">
                        <h3>Basic Information</h3>
                        
                        <div className="form-group">
                            <label htmlFor="name">Character Name *</label>
                            <input
                                type="text"
                                id="name"
                                name="name"
                                value={formData.name}
                                onChange={handleChange}
                                placeholder="Enter character name"
                                className={errors.name ? 'error' : ''}
                            />
                            {errors.name && <span className="error-message">{errors.name}</span>}
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label htmlFor="race">Race</label>
                                <select
                                    id="race"
                                    name="race"
                                    value={formData.race}
                                    onChange={handleChange}
                                >
                                    {races.map(race => (
                                        <option key={race} value={race}>{race}</option>
                                    ))}
                                </select>
                            </div>

                            <div className="form-group">
                                <label htmlFor="char_class">Class</label>
                                <select
                                    id="char_class"
                                    name="char_class"
                                    value={formData.char_class}
                                    onChange={handleChange}
                                >
                                    {classes.map(charClass => (
                                        <option key={charClass} value={charClass}>{charClass}</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        <div className="form-group">
                            <label htmlFor="backstory">Backstory (Optional)</label>
                            <textarea
                                id="backstory"
                                name="backstory"
                                value={formData.backstory}
                                onChange={handleChange}
                                placeholder="Tell us about your character's past..."
                                rows={4}
                            />
                        </div>
                    </div>

                    <div className="cc-section">
                        <h3>Ability Scores</h3>
                        <div className="stats-grid">
                            {['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'].map(stat => (
                                <div key={stat} className="stat-control">
                                    <label>{stat.charAt(0).toUpperCase() + stat.slice(1)}</label>
                                    <div className="stat-input">
                                        <button
                                            type="button"
                                            onClick={() => handleStatChange(stat, -1)}
                                            className="stat-btn"
                                        >
                                            -
                                        </button>
                                        <span className="stat-value">{formData[stat as keyof typeof formData] as number}</span>
                                        <button
                                            type="button"
                                            onClick={() => handleStatChange(stat, 1)}
                                            className="stat-btn"
                                        >
                                            +
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="cc-actions">
                        <button
                            type="button"
                            className="cc-cancel"
                            onClick={() => navigate('/')}
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            className="cc-submit"
                            disabled={isLoading}
                        >
                            {isLoading ? 'Creating...' : 'Create Character'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};
