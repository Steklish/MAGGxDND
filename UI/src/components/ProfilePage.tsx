import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './ProfilePage.css';

interface CharacterProfile {
    id: number;
    character_id: number;
    name: string;
    race: string;
    char_class: string;
    level: number;
    portrait_url?: string;
    background_image_url?: string;
    alignment: string;
    deity?: string;
    homeland?: string;
    background?: string;
    appearance_description: string;
    max_hp: number;
    current_hp: number;
    armor_class: number;
    speed: number;
    proficiency_bonus: number;
    hit_dice?: string;
    passive_wisdom?: number;
    inspiration?: number;
    stats: Record<string, number>;
    saving_throws: Record<string, number>;
    skills: Record<string, number>;
    equipment: any[];
    attacks: any[];
    spell_slots: Record<string, number>;
    features_traits: string[];
    notes: string;
}

interface ProfilePageProps {
    userId: number;
    onBack: () => void;
}

export const ProfilePage: React.FC<ProfilePageProps> = ({ userId, onBack }) => {
    const [characters, setCharacters] = useState<CharacterProfile[]>([]);
    const [selectedCharacter, setSelectedCharacter] = useState<CharacterProfile | null>(null);
    const [activeTab, setActiveTab] = useState<'overview' | 'combat' | 'skills' | 'equipment' | 'spells' | 'notes'>('overview');
    const [isLoading, setIsLoading] = useState(true);
    const [isEditing, setIsEditing] = useState(false);
    const [editData, setEditData] = useState<any>({});

    useEffect(() => {
        loadCharacters();
    }, [userId]);

    const loadCharacters = async () => {
        try {
            const response = await axios.get(`/api/v1/characters/user/${userId}`);
            const chars = response.data;
            
            // Load profiles for each character
            const charsProfiles = await Promise.all(
                chars.map(async (char: any) => {
                    try {
                        const profileRes = await axios.get(`/api/v1/profiles/character/${char.id}`);
                        return {
                            ...char,
                            ...profileRes.data,
                            stats: typeof char.stats === 'string' ? JSON.parse(char.stats) : char.stats,
                        };
                    } catch {
                        return { ...char, stats: typeof char.stats === 'string' ? JSON.parse(char.stats) : char.stats };
                    }
                })
            );
            
            setCharacters(charsProfiles);
            if (charsProfiles.length > 0) {
                setSelectedCharacter(charsProfiles[0]);
            }
        } catch (error) {
            console.error('Failed to load characters:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSaveProfile = async () => {
        if (!selectedCharacter) return;
        
        try {
            await axios.put(`/api/v1/profiles/character/${selectedCharacter.character_id}`, editData);
            setIsEditing(false);
            loadCharacters();
        } catch (error) {
            console.error('Failed to save profile:', error);
        }
    };

    const startEditing = () => {
        if (selectedCharacter) {
            setEditData({
                alignment: selectedCharacter.alignment,
                deity: selectedCharacter.deity || '',
                homeland: selectedCharacter.homeland || '',
                background: selectedCharacter.background || '',
                appearance_description: selectedCharacter.appearance_description || '',
                portrait_url: selectedCharacter.portrait_url || '',
                background_image_url: selectedCharacter.background_image_url || '',
            });
            setIsEditing(true);
        }
    };

    if (isLoading) {
        return <div className="profile-page loading"><div className="loading-spinner">Loading...</div></div>;
    }

    if (characters.length === 0) {
        return (
            <div className="profile-page no-characters">
                <h2>No Characters Yet</h2>
                <p>Create your first character to start your adventure!</p>
                <button className="btn-create" onClick={onBack}>Create Character</button>
            </div>
        );
    }

    return (
        <div className="profile-page">
            <div className="profile-header">
                <button className="btn-back" onClick={onBack}>← Back</button>
                <h1>Character Profile</h1>
            </div>

            <div className="profile-content">
                {/* Character Selector */}
                <div className="character-selector">
                    {characters.map(char => (
                        <button
                            key={char.id}
                            className={`character-option ${selectedCharacter?.id === char.id ? 'active' : ''}`}
                            onClick={() => setSelectedCharacter(char)}
                        >
                            <div className="character-option-avatar">
                                {char.portrait_url ? (
                                    <img src={char.portrait_url} alt={char.name} />
                                ) : (
                                    <span>{char.name.charAt(0)}</span>
                                )}
                            </div>
                            <div className="character-option-info">
                                <span className="character-option-name">{char.name}</span>
                                <span className="character-option-class">{char.race} {char.char_class} • Lvl {char.level}</span>
                            </div>
                        </button>
                    ))}
                </div>

                {selectedCharacter && (
                    <>
                        {/* Character Portrait & Basic Info */}
                        <div className="character-display">
                            <div 
                                className="character-portrait-container"
                                style={{
                                    backgroundImage: selectedCharacter.background_image_url ? `url(${selectedCharacter.background_image_url})` : 'none'
                                }}
                            >
                                <div className="character-portrait">
                                    {selectedCharacter.portrait_url ? (
                                        <img src={selectedCharacter.portrait_url} alt={selectedCharacter.name} />
                                    ) : (
                                        <div className="portrait-placeholder">
                                            <span>{selectedCharacter.name.charAt(0)}</span>
                                        </div>
                                    )}
                                </div>
                                <div className="character-basic-info">
                                    <h2>{selectedCharacter.name}</h2>
                                    <p className="character-subtitle">
                                        {selectedCharacter.level} Level {selectedCharacter.race} {selectedCharacter.char_class}
                                    </p>
                                    <p className="character-alignment">{selectedCharacter.alignment}</p>
                                    
                                    {!isEditing ? (
                                        <button className="btn-edit" onClick={startEditing}>Edit Profile</button>
                                    ) : (
                                        <div className="edit-actions">
                                            <button className="btn-save" onClick={handleSaveProfile}>Save</button>
                                            <button className="btn-cancel" onClick={() => setIsEditing(false)}>Cancel</button>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Stats Bar */}
                            <div className="stats-bar">
                                <div className="stat-item">
                                    <span className="stat-label">HP</span>
                                    <span className="stat-value">{selectedCharacter.current_hp}/{selectedCharacter.max_hp}</span>
                                </div>
                                <div className="stat-item">
                                    <span className="stat-label">AC</span>
                                    <span className="stat-value">{selectedCharacter.armor_class}</span>
                                </div>
                                <div className="stat-item">
                                    <span className="stat-label">Initiative</span>
                                    <span className="stat-value">+{Math.floor((selectedCharacter.stats?.dexterity || 10) / 2) - 5}</span>
                                </div>
                                <div className="stat-item">
                                    <span className="stat-label">Speed</span>
                                    <span className="stat-value">{selectedCharacter.speed || 30}ft</span>
                                </div>
                                <div className="stat-item">
                                    <span className="stat-label">Proficiency</span>
                                    <span className="stat-value">+{selectedCharacter.proficiency_bonus || 2}</span>
                                </div>
                            </div>
                        </div>

                        {/* Tabs */}
                        <div className="profile-tabs">
                            <button 
                                className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
                                onClick={() => setActiveTab('overview')}
                            >
                                Overview
                            </button>
                            <button 
                                className={`tab ${activeTab === 'combat' ? 'active' : ''}`}
                                onClick={() => setActiveTab('combat')}
                            >
                                Combat
                            </button>
                            <button 
                                className={`tab ${activeTab === 'skills' ? 'active' : ''}`}
                                onClick={() => setActiveTab('skills')}
                            >
                                Skills
                            </button>
                            <button 
                                className={`tab ${activeTab === 'equipment' ? 'active' : ''}`}
                                onClick={() => setActiveTab('equipment')}
                            >
                                Equipment
                            </button>
                            <button 
                                className={`tab ${activeTab === 'spells' ? 'active' : ''}`}
                                onClick={() => setActiveTab('spells')}
                            >
                                Spells
                            </button>
                            <button 
                                className={`tab ${activeTab === 'notes' ? 'active' : ''}`}
                                onClick={() => setActiveTab('notes')}
                            >
                                Notes
                            </button>
                        </div>

                        {/* Tab Content */}
                        <div className="tab-content">
                            {activeTab === 'overview' && (
                                <div className="overview-tab">
                                    {isEditing ? (
                                        <div className="edit-form">
                                            <div className="form-group">
                                                <label>Portrait URL</label>
                                                <input
                                                    type="text"
                                                    value={editData.portrait_url || ''}
                                                    onChange={(e) => setEditData({...editData, portrait_url: e.target.value})}
                                                    placeholder="https://..."
                                                />
                                            </div>
                                            <div className="form-group">
                                                <label>Background Image URL</label>
                                                <input
                                                    type="text"
                                                    value={editData.background_image_url || ''}
                                                    onChange={(e) => setEditData({...editData, background_image_url: e.target.value})}
                                                    placeholder="https://..."
                                                />
                                            </div>
                                            <div className="form-group">
                                                <label>Alignment</label>
                                                <select
                                                    value={editData.alignment || 'True Neutral'}
                                                    onChange={(e) => setEditData({...editData, alignment: e.target.value})}
                                                >
                                                    <option value="Lawful Good">Lawful Good</option>
                                                    <option value="Neutral Good">Neutral Good</option>
                                                    <option value="Chaotic Good">Chaotic Good</option>
                                                    <option value="Lawful Neutral">Lawful Neutral</option>
                                                    <option value="True Neutral">True Neutral</option>
                                                    <option value="Chaotic Neutral">Chaotic Neutral</option>
                                                    <option value="Lawful Evil">Lawful Evil</option>
                                                    <option value="Neutral Evil">Neutral Evil</option>
                                                    <option value="Chaotic Evil">Chaotic Evil</option>
                                                </select>
                                            </div>
                                            <div className="form-group">
                                                <label>Deity</label>
                                                <input
                                                    type="text"
                                                    value={editData.deity || ''}
                                                    onChange={(e) => setEditData({...editData, deity: e.target.value})}
                                                    placeholder="Deity name"
                                                />
                                            </div>
                                            <div className="form-group">
                                                <label>Homeland</label>
                                                <input
                                                    type="text"
                                                    value={editData.homeland || ''}
                                                    onChange={(e) => setEditData({...editData, homeland: e.target.value})}
                                                    placeholder="Place of origin"
                                                />
                                            </div>
                                            <div className="form-group">
                                                <label>Background</label>
                                                <input
                                                    type="text"
                                                    value={editData.background || ''}
                                                    onChange={(e) => setEditData({...editData, background: e.target.value})}
                                                    placeholder="Character background"
                                                />
                                            </div>
                                            <div className="form-group">
                                                <label>Appearance</label>
                                                <textarea
                                                    value={editData.appearance_description || ''}
                                                    onChange={(e) => setEditData({...editData, appearance_description: e.target.value})}
                                                    placeholder="Describe your character's appearance..."
                                                    rows={4}
                                                />
                                            </div>
                                        </div>
                                    ) : (
                                        <>
                                            <div className="info-section">
                                                <h3>Character Details</h3>
                                                <div className="info-grid">
                                                    <div className="info-item">
                                                        <span className="info-label">Alignment</span>
                                                        <span className="info-value">{selectedCharacter.alignment}</span>
                                                    </div>
                                                    {selectedCharacter.deity && (
                                                        <div className="info-item">
                                                            <span className="info-label">Deity</span>
                                                            <span className="info-value">{selectedCharacter.deity}</span>
                                                        </div>
                                                    )}
                                                    {selectedCharacter.homeland && (
                                                        <div className="info-item">
                                                            <span className="info-label">Homeland</span>
                                                            <span className="info-value">{selectedCharacter.homeland}</span>
                                                        </div>
                                                    )}
                                                    {selectedCharacter.background && (
                                                        <div className="info-item">
                                                            <span className="info-label">Background</span>
                                                            <span className="info-value">{selectedCharacter.background}</span>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                            
                                            {selectedCharacter.appearance_description && (
                                                <div className="info-section">
                                                    <h3>Appearance</h3>
                                                    <p className="appearance-text">{selectedCharacter.appearance_description}</p>
                                                </div>
                                            )}
                                            
                                            <div className="info-section">
                                                <h3>Ability Scores</h3>
                                                <div className="ability-scores">
                                                    {Object.entries(selectedCharacter.stats || {}).map(([stat, value]) => (
                                                        <div key={stat} className="ability-score">
                                                            <span className="ability-name">{stat}</span>
                                                            <span className="ability-value">{value}</span>
                                                            <span className="ability-modifier">{value >= 10 ? '+' : ''}{Math.floor((value - 10) / 2)}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        </>
                                    )}
                                </div>
                            )}

                            {activeTab === 'combat' && (
                                <div className="combat-tab">
                                    <h3>Combat Stats</h3>
                                    <div className="combat-grid">
                                        <div className="combat-item">
                                            <span className="combat-label">Hit Dice</span>
                                            <span className="combat-value">{selectedCharacter.hit_dice || '1d10'}</span>
                                        </div>
                                        <div className="combat-item">
                                            <span className="combat-label">Passive Wisdom</span>
                                            <span className="combat-value">{selectedCharacter.passive_wisdom || 10}</span>
                                        </div>
                                        <div className="combat-item">
                                            <span className="combat-label">Inspiration</span>
                                            <span className="combat-value">{selectedCharacter.inspiration ? '✓' : '✗'}</span>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {activeTab === 'skills' && (
                                <div className="skills-tab">
                                    <h3>Skill Modifiers</h3>
                                    <div className="skills-grid">
                                        {Object.entries(selectedCharacter.skills || {}).map(([skill, modifier]) => (
                                            <div key={skill} className="skill-item">
                                                <span className="skill-name">{skill.replace(/_/g, ' ')}</span>
                                                <span className="skill-modifier">{modifier >= 0 ? '+' : ''}{modifier}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {activeTab === 'equipment' && (
                                <div className="equipment-tab">
                                    <h3>Equipment & Inventory</h3>
                                    {selectedCharacter.equipment && selectedCharacter.equipment.length > 0 ? (
                                        <ul className="equipment-list">
                                            {selectedCharacter.equipment.map((item, idx) => (
                                                <li key={idx} className="equipment-item">
                                                    {typeof item === 'string' ? item : item.name}
                                                </li>
                                            ))}
                                        </ul>
                                    ) : (
                                        <p className="empty-message">No equipment yet</p>
                                    )}
                                </div>
                            )}

                            {activeTab === 'spells' && (
                                <div className="spells-tab">
                                    <h3>Spell Slots</h3>
                                    <div className="spell-slots">
                                        {Object.entries(selectedCharacter.spell_slots || {}).map(([level, slots]) => (
                                            slots > 0 && (
                                                <div key={level} className="spell-slot-item">
                                                    <span className="spell-level">Level {level.replace('lvl', '')}</span>
                                                    <div className="slot-dots">
                                                        {Array.from({ length: slots }).map((_, i) => (
                                                            <span key={i} className="slot-dot filled"></span>
                                                        ))}
                                                    </div>
                                                </div>
                                            )
                                        ))}
                                    </div>
                                </div>
                            )}

                            {activeTab === 'notes' && (
                                <div className="notes-tab">
                                    <h3>Character Notes</h3>
                                    {selectedCharacter.notes ? (
                                        <div className="notes-content">{selectedCharacter.notes}</div>
                                    ) : (
                                        <p className="empty-message">No notes yet</p>
                                    )}
                                </div>
                            )}
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};
