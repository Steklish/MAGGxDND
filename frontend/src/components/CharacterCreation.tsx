import React, { useState } from 'react';
import axios from 'axios';
import './CharacterCreation.css';

interface CharacterCreationProps {
    userId: number;
    onComplete: () => void;
}

export const CharacterCreation: React.FC<CharacterCreationProps> = ({ userId, onComplete }) => {
    const [isLoading, setIsLoading] = useState(false);
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [step, setStep] = useState(1);
    const [formData, setFormData] = useState({
        name: '',
        race: 'Human',
        char_class: 'Fighter',
        background: 'Soldier',
        alignment: 'True Neutral',
        backstory: '',
        appearance: '',
        strength: 15,
        dexterity: 12,
        constitution: 14,
        intelligence: 10,
        wisdom: 10,
        charisma: 10,
        portrait_url: '',
        background_image_url: '',
    });

    const races = [
        { name: 'Human', bonus: 'All +1', speed: 30, size: 'Medium' },
        { name: 'Elf', bonus: 'DEX +2', speed: 30, size: 'Medium' },
        { name: 'Dwarf', bonus: 'CON +2', speed: 25, size: 'Medium' },
        { name: 'Halfling', bonus: 'DEX +2', speed: 25, size: 'Small' },
        { name: 'Orc', bonus: 'STR +2', speed: 30, size: 'Medium' },
        { name: 'Tiefling', bonus: 'CHA +2, INT +1', speed: 30, size: 'Medium' },
        { name: 'Dragonborn', bonus: 'STR +2, CHA +1', speed: 30, size: 'Medium' },
    ];

    const classes = [
        { name: 'Fighter', hitDie: 'd10', primary: 'Strength/Dexterity' },
        { name: 'Wizard', hitDie: 'd6', primary: 'Intelligence' },
        { name: 'Rogue', hitDie: 'd8', primary: 'Dexterity' },
        { name: 'Cleric', hitDie: 'd8', primary: 'Wisdom' },
        { name: 'Ranger', hitDie: 'd10', primary: 'Dexterity/Wisdom' },
        { name: 'Paladin', hitDie: 'd10', primary: 'Strength/Charisma' },
        { name: 'Barbarian', hitDie: 'd12', primary: 'Strength' },
        { name: 'Bard', hitDie: 'd8', primary: 'Charisma' },
    ];

    const backgrounds = [
        'Acolyte', 'Criminal', 'Folk Hero', 'Noble', 'Sage', 'Soldier',
        'Entertainer', 'Guild Artisan', 'Hermit', 'Outlander', 'Sailor', 'Urchin'
    ];

    const alignments = [
        'Lawful Good', 'Neutral Good', 'Chaotic Good',
        'Lawful Neutral', 'True Neutral', 'Chaotic Neutral',
        'Lawful Evil', 'Neutral Evil', 'Chaotic Evil'
    ];

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
        if (errors[name]) {
            setErrors(prev => ({ ...prev, [name]: '' }));
        }
    };

    const handleStatChange = (stat: string, delta: number) => {
        setFormData(prev => {
            const newValue = Math.max(8, Math.min(17, prev[stat as keyof typeof prev] as number + delta));
            return { ...prev, [stat]: newValue };
        });
    };

    const getModifier = (score: number) => {
        return Math.floor((score - 10) / 2);
    };

    const calculateHP = () => {
        const classHitDie = classes.find(c => c.name === formData.char_class)?.hitDie || 'd8';
        const conMod = getModifier(formData.constitution);
        const hitDieValue = parseInt(classHitDie.replace('d', ''));
        return hitDieValue + conMod;
    };

    const calculateAC = () => {
        const dexMod = getModifier(formData.dexterity);
        return 10 + dexMod;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setErrors({});

        const newErrors: Record<string, string> = {};
        if (!formData.name) newErrors.name = 'Character name is required';
        if (formData.name.length < 3) newErrors.name = 'Name must be at least 3 characters';

        if (Object.keys(newErrors).length > 0) {
            setErrors(newErrors);
            setIsLoading(false);
            return;
        }

        try {
            const stats = {
                strength: formData.strength,
                dexterity: formData.dexterity,
                constitution: formData.constitution,
                intelligence: formData.intelligence,
                wisdom: formData.wisdom,
                charisma: formData.charisma,
            };

            const characterData = {
                user_id: userId,
                name: formData.name,
                race: formData.race,
                char_class: formData.char_class,
                level: 1,
                backstory_summary: formData.backstory,
                personality_traits: '[]',
                max_hp: calculateHP(),
                current_hp: calculateHP(),
                armor_class: calculateAC(),
                speed: races.find(r => r.name === formData.race)?.speed || 30,
                stats,
                abilities: [],
                inventory: [],
            };

            const response = await axios.post('/api/v1/characters/', characterData);

            if (response.data.id) {
                const profileData = {
                    character_id: response.data.id,
                    alignment: formData.alignment,
                    background: formData.background,
                    appearance_description: formData.appearance,
                    deity: null,
                    homeland: null,
                    hit_dice: `1${classes.find(c => c.name === formData.char_class)?.hitDie || 'd8'}`,
                    passive_wisdom: 10 + getModifier(formData.wisdom),
                    inspiration: false,
                    saving_throws: {},
                    skills: {},
                    equipment: [],
                    attacks: [],
                    spell_slots: {},
                    features_traits: [],
                    notes: '',
                };

                await axios.post('/api/v1/profiles/', profileData);
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

    const totalPoints = formData.strength + formData.dexterity + formData.constitution + 
                       formData.intelligence + formData.wisdom + formData.charisma;

    return (
        <div className="character-creation-overlay">
            <div className="character-creation">
                <div className="cc-header">
                    <h2>Create Your Character</h2>
                    <p>Forge your hero and begin your epic adventure</p>
                </div>

                <div className="cc-progress">
                    <div className={`progress-step ${step >= 1 ? 'active' : ''}`}>
                        <span className="step-number">1</span>
                        <span className="step-label">Basics</span>
                    </div>
                    <div className="progress-line"></div>
                    <div className={`progress-step ${step >= 2 ? 'active' : ''}`}>
                        <span className="step-number">2</span>
                        <span className="step-label">Appearance</span>
                    </div>
                    <div className="progress-line"></div>
                    <div className={`progress-step ${step >= 3 ? 'active' : ''}`}>
                        <span className="step-number">3</span>
                        <span className="step-label">Abilities</span>
                    </div>
                    <div className="progress-line"></div>
                    <div className={`progress-step ${step >= 4 ? 'active' : ''}`}>
                        <span className="step-number">4</span>
                        <span className="step-label">Review</span>
                    </div>
                </div>

                {errors.submit && (
                    <div className="cc-error">
                        <span>⚠️</span>
                        <span>{errors.submit}</span>
                    </div>
                )}

                <form className="cc-form" onSubmit={handleSubmit}>
                    {step === 1 && (
                        <div className="cc-section fade-in">
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
                                        className="race-select"
                                    >
                                        {races.map(race => (
                                            <option key={race.name} value={race.name}>
                                                {race.name} ({race.bonus})
                                            </option>
                                        ))}
                                    </select>
                                    <div className="race-info">
                                        <span>Speed: {races.find(r => r.name === formData.race)?.speed}ft</span>
                                        <span>Size: {races.find(r => r.name === formData.race)?.size}</span>
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label htmlFor="char_class">Class</label>
                                    <select
                                        id="char_class"
                                        name="char_class"
                                        value={formData.char_class}
                                        onChange={handleChange}
                                        className="class-select"
                                    >
                                        {classes.map(charClass => (
                                            <option key={charClass.name} value={charClass.name}>
                                                {charClass.name} (HD: {charClass.hitDie})
                                            </option>
                                        ))}
                                    </select>
                                    <div className="class-info">
                                        <span>Primary: {classes.find(c => c.name === formData.char_class)?.primary}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="form-row">
                                <div className="form-group">
                                    <label htmlFor="background">Background</label>
                                    <select
                                        id="background"
                                        name="background"
                                        value={formData.background}
                                        onChange={handleChange}
                                    >
                                        {backgrounds.map(bg => (
                                            <option key={bg} value={bg}>{bg}</option>
                                        ))}
                                    </select>
                                </div>

                                <div className="form-group">
                                    <label htmlFor="alignment">Alignment</label>
                                    <select
                                        id="alignment"
                                        name="alignment"
                                        value={formData.alignment}
                                        onChange={handleChange}
                                    >
                                        {alignments.map(align => (
                                            <option key={align} value={align}>{align}</option>
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

                            <div className="cc-actions">
                                <button type="button" className="cc-cancel" onClick={onComplete}>Cancel</button>
                                <button type="button" className="cc-next" onClick={() => setStep(2)}>Next →</button>
                            </div>
                        </div>
                    )}

                    {step === 2 && (
                        <div className="cc-section fade-in">
                            <h3>Appearance & Visuals</h3>

                            <div className="form-group">
                                <label htmlFor="appearance">Physical Description</label>
                                <textarea
                                    id="appearance"
                                    name="appearance"
                                    value={formData.appearance}
                                    onChange={handleChange}
                                    placeholder="Describe your character's appearance (height, weight, hair color, eye color, distinguishing features...)"
                                    rows={5}
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="portrait_url">Portrait URL (Optional)</label>
                                <input
                                    type="url"
                                    id="portrait_url"
                                    name="portrait_url"
                                    value={formData.portrait_url}
                                    onChange={handleChange}
                                    placeholder="https://example.com/portrait.jpg"
                                />
                                {formData.portrait_url && (
                                    <div className="image-preview">
                                        <img src={formData.portrait_url} alt="Portrait preview" onError={(e) => (e.currentTarget.style.display = 'none')} />
                                    </div>
                                )}
                            </div>

                            <div className="form-group">
                                <label htmlFor="background_image_url">Background Image URL (Optional)</label>
                                <input
                                    type="url"
                                    id="background_image_url"
                                    name="background_image_url"
                                    value={formData.background_image_url}
                                    onChange={handleChange}
                                    placeholder="https://example.com/background.jpg"
                                />
                                {formData.background_image_url && (
                                    <div className="image-preview background-preview">
                                        <img src={formData.background_image_url} alt="Background preview" onError={(e) => (e.currentTarget.style.display = 'none')} />
                                    </div>
                                )}
                            </div>

                            <div className="cc-actions">
                                <button type="button" className="cc-back" onClick={() => setStep(1)}>← Back</button>
                                <button type="button" className="cc-next" onClick={() => setStep(3)}>Next →</button>
                            </div>
                        </div>
                    )}

                    {step === 3 && (
                        <div className="cc-section fade-in">
                            <h3>Ability Scores</h3>
                            <p className="stat-points">Points used: {totalPoints} / 90 (Standard Array: 15, 14, 13, 12, 10, 8)</p>
                            
                            <div className="stats-grid">
                                {['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'].map(stat => (
                                    <div key={stat} className="stat-control">
                                        <label className="stat-label">
                                            {stat.charAt(0).toUpperCase() + stat.slice(1)}
                                        </label>
                                        <div className="stat-input">
                                            <button
                                                type="button"
                                                onClick={() => handleStatChange(stat, -1)}
                                                className="stat-btn minus"
                                            >
                                                -
                                            </button>
                                            <span className="stat-value">{formData[stat as keyof typeof formData] as number}</span>
                                            <button
                                                type="button"
                                                onClick={() => handleStatChange(stat, 1)}
                                                className="stat-btn plus"
                                            >
                                                +
                                            </button>
                                        </div>
                                        <span className="stat-modifier">
                                            Modifier: {getModifier(formData[stat as keyof typeof formData] as number) >= 0 ? '+' : ''}
                                            {getModifier(formData[stat as keyof typeof formData] as number)}
                                        </span>
                                    </div>
                                ))}
                            </div>

                            <div className="stat-summary">
                                <h4>Derived Stats Preview</h4>
                                <div className="derived-stats">
                                    <div className="derived-stat">
                                        <span>Hit Points (Level 1):</span>
                                        <span className="value">{calculateHP()}</span>
                                    </div>
                                    <div className="derived-stat">
                                        <span>Armor Class:</span>
                                        <span className="value">{calculateAC()}</span>
                                    </div>
                                    <div className="derived-stat">
                                        <span>Initiative:</span>
                                        <span className="value">{getModifier(formData.dexterity) >= 0 ? '+' : ''}{getModifier(formData.dexterity)}</span>
                                    </div>
                                    <div className="derived-stat">
                                        <span>Passive Wisdom:</span>
                                        <span className="value">{10 + getModifier(formData.wisdom)}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="cc-actions">
                                <button type="button" className="cc-back" onClick={() => setStep(2)}>← Back</button>
                                <button type="button" className="cc-next" onClick={() => setStep(4)}>Next →</button>
                            </div>
                        </div>
                    )}

                    {step === 4 && (
                        <div className="cc-section fade-in">
                            <h3>Review Your Character</h3>
                            
                            <div className="character-preview">
                                <div className="preview-header">
                                    {formData.portrait_url ? (
                                        <img src={formData.portrait_url} alt={formData.name} className="preview-portrait" />
                                    ) : (
                                        <div className="preview-portrait-placeholder">
                                            {formData.name.charAt(0).toUpperCase()}
                                        </div>
                                    )}
                                    <div className="preview-basic">
                                        <h4>{formData.name}</h4>
                                        <p>Level 1 {formData.race} {formData.char_class}</p>
                                        <p>{formData.alignment} • {formData.background}</p>
                                    </div>
                                </div>
                                
                                <div className="preview-stats">
                                    <div className="preview-stat-row">
                                        <span>HP:</span>
                                        <span className="stat-value hp">{calculateHP()}</span>
                                    </div>
                                    <div className="preview-stat-row">
                                        <span>AC:</span>
                                        <span className="stat-value ac">{calculateAC()}</span>
                                    </div>
                                    <div className="preview-stat-row">
                                        <span>Speed:</span>
                                        <span className="stat-value speed">{races.find(r => r.name === formData.race)?.speed}ft</span>
                                    </div>
                                </div>

                                <div className="preview-abilities">
                                    <h5>Ability Scores</h5>
                                    <div className="ability-grid">
                                        {Object.entries({
                                            STR: formData.strength,
                                            DEX: formData.dexterity,
                                            CON: formData.constitution,
                                            INT: formData.intelligence,
                                            WIS: formData.wisdom,
                                            CHA: formData.charisma,
                                        }).map(([abbr, score]) => (
                                            <div key={abbr} className="ability-preview">
                                                <span className="abbr">{abbr}</span>
                                                <span className="score">{score}</span>
                                                <span className="mod">{getModifier(score) >= 0 ? '+' : ''}{getModifier(score)}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {formData.backstory && (
                                    <div className="preview-backstory">
                                        <h5>Backstory</h5>
                                        <p>{formData.backstory}</p>
                                    </div>
                                )}
                            </div>

                            <div className="cc-actions">
                                <button type="button" className="cc-back" onClick={() => setStep(3)}>← Back</button>
                                <button type="submit" className="cc-submit" disabled={isLoading}>
                                    {isLoading ? 'Creating...' : 'Create Character ✨'}
                                </button>
                            </div>
                        </div>
                    )}
                </form>
            </div>
        </div>
    );
};
