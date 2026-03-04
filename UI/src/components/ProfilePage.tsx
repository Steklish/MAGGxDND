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

interface GameSession {
    session_id: string;
    session_name: string;
    game_mode: string;
    status: string;
    description?: string;
    player_count: number;
    max_players: number;
    created_at?: string;
}

interface UserProfile {
    id: number;
    username: string;
    group_id?: number;
}

interface ProfilePageProps {
    userId: number;
    onBack: () => void;
    onCreateCharacter?: () => void;
    onCreateSession?: () => void;
    onViewSession?: (sessionId: string) => void;
    onJoinSession?: (sessionId: string) => void;
}

export const ProfilePage: React.FC<ProfilePageProps> = ({ userId, onBack, onCreateCharacter, onCreateSession, onViewSession, onJoinSession }) => {
    const [characters, setCharacters] = useState<CharacterProfile[]>([]);
    const [selectedCharacter, setSelectedCharacter] = useState<CharacterProfile | null>(null);
    const [characterTab, setCharacterTab] = useState<'overview' | 'combat' | 'skills' | 'equipment' | 'spells' | 'notes'>('overview');
    const [activeTab, setActiveTab] = useState<'characters' | 'games' | 'settings'>('characters');
    const [isLoading, setIsLoading] = useState(true);
    const [isEditing, setIsEditing] = useState(false);
    const [editData, setEditData] = useState<any>({});
    const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
    const [activeGames, setActiveGames] = useState<GameSession[]>([]);
    const [gameHistory, setGameHistory] = useState<GameSession[]>([]);

    useEffect(() => {
        loadUserProfile();
        loadCharacters();
        loadActiveGames();
    }, [userId]);

    const loadUserProfile = async () => {
        try {
            const response = await axios.get(`/api/v1/users/username/${localStorage.getItem('username')}`);
            setUserProfile(response.data);
        } catch (error) {
            console.error('Failed to load user profile:', error);
        }
    };

    const loadCharacters = async () => {
        try {
            const response = await axios.get(`/api/v1/characters/user/${userId}`);
            const chars = response.data;

            if (chars.length === 0) {
                setCharacters([]);
                setIsLoading(false);
                return;
            }

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
                        return { 
                            ...char, 
                            stats: typeof char.stats === 'string' ? JSON.parse(char.stats) : char.stats,
                            alignment: 'True Neutral',
                            background: char.background || 'Unknown',
                            appearance_description: '',
                            speed: 30,
                            proficiency_bonus: 2,
                        };
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

    const loadActiveGames = async () => {
        try {
            const response = await axios.get('/api/v1/sessions');
            const sessions = response.data.sessions || [];
            setActiveGames(sessions.filter((s: any) => s.status === 'active'));
            setGameHistory(sessions.filter((s: any) => s.status === 'completed'));
        } catch (error) {
            console.error('Failed to load games:', error);
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

    const handleDeleteCharacter = async (characterId: number) => {
        if (!confirm('Are you sure you want to delete this character? This action cannot be undone.')) {
            return;
        }

        try {
            await axios.delete(`/api/v1/characters/${characterId}`);
            setCharacters(characters.filter(c => c.id !== characterId));
            if (selectedCharacter?.id === characterId) {
                setSelectedCharacter(characters.find(c => c.id !== characterId) || null);
            }
        } catch (error) {
            console.error('Failed to delete character:', error);
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
                notes: selectedCharacter.notes || '',
            });
            setIsEditing(true);
        }
    };

    const handleJoinGame = async (sessionId: string) => {
        try {
            const username = localStorage.getItem('username') || 'Player';
            const response = await axios.post(`/api/v1/sessions/${sessionId}/players`, {
                player_name: username,
            });
            
            const playerId = response.data.player_id;
            console.log('Joined session with player ID:', playerId);
            
            // Store connection info
            localStorage.setItem('currentSessionId', sessionId);
            localStorage.setItem('currentPlayerId', playerId);
            
            alert(`Successfully joined session!\nPlayer ID: ${playerId}`);
        } catch (error) {
            console.error('Failed to join game:', error);
            alert('Failed to join session: ' + (error as any).response?.data?.detail || 'Unknown error');
        }
    };

    const handleCreateGame = () => {
        if (onCreateSession) {
            onCreateSession();
        }
    };

    if (isLoading) {
        return (
            <div className="profile-page loading">
                <div className="loading-spinner">
                    <div className="spinner-ring"></div>
                    <div className="spinner-ring"></div>
                    <div className="spinner-ring"></div>
                </div>
                <p>Loading your profile...</p>
            </div>
        );
    }

    return (
        <div className="profile-page">
            <div className="profile-header">
                <button className="btn-back" onClick={onBack}>← Back to Home</button>
                <div className="profile-header-info">
                    <h1>{userProfile?.username || 'Player'}'s Profile</h1>
                    {userProfile && (
                        <span className="user-id">ID: {userProfile.id}</span>
                    )}
                </div>
            </div>

            {/* Main Tabs */}
            <div className="profile-main-tabs">
                <button
                    className={`main-tab ${activeTab === 'characters' ? 'active' : ''}`}
                    onClick={() => setActiveTab('characters')}
                >
                    <span className="tab-icon">🎭</span>
                    <span>Characters ({characters.length})</span>
                </button>
                <button
                    className={`main-tab ${activeTab === 'games' ? 'active' : ''}`}
                    onClick={() => setActiveTab('games')}
                >
                    <span className="tab-icon">⚔️</span>
                    <span>Active Games ({activeGames.length})</span>
                </button>
                <button
                    className={`main-tab ${activeTab === 'settings' ? 'active' : ''}`}
                    onClick={() => setActiveTab('settings')}
                >
                    <span className="tab-icon">⚙️</span>
                    <span>Settings</span>
                </button>
            </div>

            <div className="profile-content">
                {/* Characters Tab */}
                {activeTab === 'characters' && (
                    <div className="characters-tab fade-in">
                        {characters.length === 0 ? (
                            <div className="no-characters">
                                <div className="empty-state-icon">📜</div>
                                <h2>No Characters Yet</h2>
                                <p>Create your first character to begin your epic adventure!</p>
                                <div className="empty-actions">
                                    <button className="btn-create" onClick={onCreateCharacter}>
                                        <span className="btn-icon">✨</span>
                                        Create Your First Character
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <>
                                {/* Character Selector */}
                                <div className="character-selector">
                                    {characters.map(char => (
                                        <div
                                            key={char.id}
                                            className={`character-option ${selectedCharacter?.id === char.id ? 'active' : ''}`}
                                            onClick={() => setSelectedCharacter(char)}
                                        >
                                            <div className="character-option-main">
                                                <div className="character-option-avatar">
                                                    {char.portrait_url ? (
                                                        <img src={char.portrait_url} alt={char.name} />
                                                    ) : (
                                                        <span>{char.name.charAt(0)}</span>
                                                    )}
                                                </div>
                                                <div className="character-option-info">
                                                    <span className="character-option-name">{char.name}</span>
                                                    <span className="character-option-class">
                                                        Lvl {char.level} {char.race} {char.char_class}
                                                    </span>
                                                </div>
                                            </div>
                                            <button
                                                className="btn-delete-char"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleDeleteCharacter(char.character_id);
                                                }}
                                                title="Delete character"
                                            >
                                                🗑️
                                            </button>
                                        </div>
                                    ))}
                                    <div
                                        className="character-option add-new"
                                        onClick={onCreateCharacter}
                                    >
                                        <div className="character-option-avatar">
                                            <span>+</span>
                                        </div>
                                        <div className="character-option-info">
                                            <span className="character-option-name">Create New</span>
                                            <span className="character-option-class">Forge a new hero</span>
                                        </div>
                                    </div>
                                </div>

                                {selectedCharacter && (
                                    <>
                                        {/* Character Display */}
                                        <div className="character-display">
                                            <div
                                                className="character-portrait-container"
                                                style={{
                                                    backgroundImage: selectedCharacter.background_image_url 
                                                        ? `url(${selectedCharacter.background_image_url})` 
                                                        : 'linear-gradient(135deg, var(--bg-tertiary) 0%, var(--bg-secondary) 100%)'
                                                }}
                                            >
                                                <div className="character-portrait">
                                                    {selectedCharacter.portrait_url ? (
                                                        <img src={selectedCharacter.portrait_url} alt={selectedCharacter.name} />
                                                    ) : (
                                                        <div className="portrait-placeholder">
                                                            {selectedCharacter.name.charAt(0)}
                                                        </div>
                                                    )}
                                                </div>
                                                <div className="character-basic-info">
                                                    <h2>{selectedCharacter.name}</h2>
                                                    <p className="character-subtitle">
                                                        Level {selectedCharacter.level} {selectedCharacter.race} {selectedCharacter.char_class}
                                                    </p>
                                                    <p className="character-alignment">{selectedCharacter.alignment}</p>

                                                    {!isEditing ? (
                                                        <div className="character-actions">
                                                            <button className="btn-edit" onClick={startEditing}>
                                                                ✏️ Edit Profile
                                                            </button>
                                                        </div>
                                                    ) : (
                                                        <div className="edit-actions">
                                                            <button className="btn-save" onClick={handleSaveProfile}>
                                                                💾 Save Changes
                                                            </button>
                                                            <button className="btn-cancel" onClick={() => setIsEditing(false)}>
                                                                Cancel
                                                            </button>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>

                                            {/* Stats Bar */}
                                            <div className="stats-bar">
                                                <div className="stat-item">
                                                    <span className="stat-label">
                                                        <span className="stat-icon">❤️</span> HP
                                                    </span>
                                                    <span className="stat-value">{selectedCharacter.current_hp}/{selectedCharacter.max_hp}</span>
                                                </div>
                                                <div className="stat-item">
                                                    <span className="stat-label">
                                                        <span className="stat-icon">🛡️</span> AC
                                                    </span>
                                                    <span className="stat-value">{selectedCharacter.armor_class}</span>
                                                </div>
                                                <div className="stat-item">
                                                    <span className="stat-label">
                                                        <span className="stat-icon">⚡</span> Initiative
                                                    </span>
                                                    <span className="stat-value">
                                                        {Math.floor((selectedCharacter.stats?.dexterity || 10) / 2) - 5 >= 0 ? '+' : ''}
                                                        {Math.floor((selectedCharacter.stats?.dexterity || 10) / 2) - 5}
                                                    </span>
                                                </div>
                                                <div className="stat-item">
                                                    <span className="stat-label">
                                                        <span className="stat-icon">👟</span> Speed
                                                    </span>
                                                    <span className="stat-value">{selectedCharacter.speed || 30}ft</span>
                                                </div>
                                                <div className="stat-item">
                                                    <span className="stat-label">
                                                        <span className="stat-icon">⭐</span> Proficiency
                                                    </span>
                                                    <span className="stat-value">+{selectedCharacter.proficiency_bonus || 2}</span>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Character Tabs */}
                                        <div className="profile-tabs">
                                            <button
                                                className={`tab ${characterTab === 'overview' ? 'active' : ''}`}
                                                onClick={() => setCharacterTab('overview')}
                                            >
                                                Overview
                                            </button>
                                            <button
                                                className={`tab ${characterTab === 'combat' ? 'active' : ''}`}
                                                onClick={() => setCharacterTab('combat')}
                                            >
                                                Combat
                                            </button>
                                            <button
                                                className={`tab ${characterTab === 'skills' ? 'active' : ''}`}
                                                onClick={() => setCharacterTab('skills')}
                                            >
                                                Skills
                                            </button>
                                            <button
                                                className={`tab ${characterTab === 'equipment' ? 'active' : ''}`}
                                                onClick={() => setCharacterTab('equipment')}
                                            >
                                                Equipment
                                            </button>
                                            <button
                                                className={`tab ${characterTab === 'spells' ? 'active' : ''}`}
                                                onClick={() => setCharacterTab('spells')}
                                            >
                                                Spells
                                            </button>
                                            <button
                                                className={`tab ${characterTab === 'notes' ? 'active' : ''}`}
                                                onClick={() => setCharacterTab('notes')}
                                            >
                                                Notes
                                            </button>
                                        </div>

                                        {/* Tab Content */}
                                        <div className="tab-content">
                                            {characterTab === 'overview' && (
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
                                                                    {['Lawful Good', 'Neutral Good', 'Chaotic Good',
                                                                      'Lawful Neutral', 'True Neutral', 'Chaotic Neutral',
                                                                      'Lawful Evil', 'Neutral Evil', 'Chaotic Evil'].map(a => (
                                                                        <option key={a} value={a}>{a}</option>
                                                                    ))}
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
                                                            <div className="form-group">
                                                                <label>Notes</label>
                                                                <textarea
                                                                    value={editData.notes || ''}
                                                                    onChange={(e) => setEditData({...editData, notes: e.target.value})}
                                                                    placeholder="Personal notes about your character..."
                                                                    rows={3}
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
                                                                            <span className="ability-modifier">
                                                                                {value >= 10 ? '+' : ''}{Math.floor((value - 10) / 2)}
                                                                            </span>
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            </div>
                                                        </>
                                                    )}
                                                </div>
                                            )}

                                            {characterTab === 'combat' && (
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

                                            {characterTab === 'skills' && (
                                                <div className="skills-tab">
                                                    <h3>Skill Modifiers</h3>
                                                    <div className="skills-grid">
                                                        {(() => {
                                                            // Parse skills if it's a string
                                                            let skillsObj = selectedCharacter.skills || {};
                                                            if (typeof skillsObj === 'string') {
                                                                try {
                                                                    skillsObj = JSON.parse(skillsObj);
                                                                } catch {
                                                                    skillsObj = {};
                                                                }
                                                            }
                                                            
                                                            const skillEntries = Object.entries(skillsObj);
                                                            if (skillEntries.length > 0) {
                                                                return skillEntries.map(([skill, modifier]) => (
                                                                    <div key={skill} className="skill-item">
                                                                        <span className="skill-name">{skill.replace(/_/g, ' ')}</span>
                                                                        <span className="skill-modifier">{modifier >= 0 ? '+' : ''}{modifier}</span>
                                                                    </div>
                                                                ));
                                                            }
                                                            return <p className="empty-message">No skill proficiencies set yet</p>;
                                                        })()}
                                                    </div>
                                                </div>
                                            )}

                                            {characterTab === 'equipment' && (
                                                <div className="equipment-tab">
                                                    <h3>Equipment & Inventory</h3>
                                                    {(() => {
                                                        // Parse equipment if it's a string
                                                        let equipmentList = selectedCharacter.equipment || [];
                                                        if (typeof equipmentList === 'string') {
                                                            try {
                                                                equipmentList = JSON.parse(equipmentList);
                                                            } catch {
                                                                equipmentList = [];
                                                            }
                                                        }
                                                        
                                                        if (Array.isArray(equipmentList) && equipmentList.length > 0) {
                                                            return (
                                                                <ul className="equipment-list">
                                                                    {equipmentList.map((item, idx) => {
                                                                        let itemName = 'Unknown Item';
                                                                        if (typeof item === 'string') {
                                                                            itemName = item;
                                                                        } else if (item && typeof item === 'object') {
                                                                            itemName = item.name || item.short_summary || 'Unknown Item';
                                                                        }
                                                                        return (
                                                                            <li key={idx} className="equipment-item">
                                                                                {itemName}
                                                                            </li>
                                                                        );
                                                                    })}
                                                                </ul>
                                                            );
                                                        }
                                                        return <p className="empty-message">No equipment yet</p>;
                                                    })()}
                                                </div>
                                            )}

                                            {characterTab === 'spells' && (
                                                <div className="spells-tab">
                                                    <h3>Spell Slots</h3>
                                                    {(() => {
                                                        // Parse spell_slots if it's a string
                                                        let spellSlotsObj = selectedCharacter.spell_slots || {};
                                                        if (typeof spellSlotsObj === 'string') {
                                                            try {
                                                                spellSlotsObj = JSON.parse(spellSlotsObj);
                                                            } catch {
                                                                spellSlotsObj = {};
                                                            }
                                                        }
                                                        
                                                        const spellSlotEntries = Object.entries(spellSlotsObj);
                                                        if (spellSlotEntries.length > 0) {
                                                            return (
                                                                <div className="spell-slots-grid">
                                                                    {spellSlotEntries.map(([level, slots]) => {
                                                                        const slotCount = typeof slots === 'number' ? slots : parseInt(slots) || 0;
                                                                        if (slotCount > 0) {
                                                                            return (
                                                                                <div key={level} className="spell-slot">
                                                                                    <span className="spell-level">Level {parseInt(level) + 1}</span>
                                                                                    <div className="slot-dots">
                                                                                        {Array.from({ length: slotCount }).map((_, i) => (
                                                                                            <span key={i} className="slot-dot filled"></span>
                                                                                        ))}
                                                                                    </div>
                                                                                </div>
                                                                            );
                                                                        }
                                                                        return null;
                                                                    })}
                                                                </div>
                                                            );
                                                        }
                                                        return <p className="empty-message">No spell slots available</p>;
                                                    })()}
                                                </div>
                                            )}

                                            {characterTab === 'notes' && (
                                                <div className="notes-tab">
                                                    <h3>Character Notes</h3>
                                                    {selectedCharacter.notes ? (
                                                        <div className="notes-content">
                                                            <p>{selectedCharacter.notes}</p>
                                                        </div>
                                                    ) : (
                                                        <p className="empty-message">No notes yet</p>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    </>
                                )}
                            </>
                        )}
                    </div>
                )}

                {/* Games Tab */}
                {activeTab === 'games' && (
                    <div className="games-tab fade-in">
                        <div className="games-header">
                            <h2>Game Sessions</h2>
                            <button className="btn-create-game" onClick={handleCreateGame}>
                                <span className="btn-icon">+</span>
                                Create Session
                            </button>
                        </div>

                        {/* Active Games */}
                        <div className="games-section">
                            <h3>
                                <span className="section-icon">🔴</span> Active Sessions
                            </h3>
                            {activeGames.length > 0 ? (
                                <div className="games-grid">
                                    {activeGames.map((game) => (
                                        <div key={game.session_id} className="game-card active">
                                            <div className="game-card-header">
                                                <h4>{game.session_name}</h4>
                                                <span className="game-status status-active">Live</span>
                                            </div>
                                            <p className="game-description">{game.description || 'No description'}</p>
                                            <div className="game-info">
                                                <span className="game-mode">{game.game_mode}</span>
                                                <span className="game-players">
                                                    👥 {game.player_count}/{game.max_players} players
                                                </span>
                                            </div>
                                            <div className="game-card-actions">
                                                <button
                                                    className="btn-view-session"
                                                    onClick={() => onViewSession && onViewSession(game.session_id)}
                                                >
                                                    👁️ View Details
                                                </button>
                                                <button
                                                    className="btn-join-game"
                                                    onClick={() => onJoinSession && onJoinSession(game.session_id)}
                                                >
                                                    🚪 Join Session
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="empty-state">
                                    <span className="empty-icon">🎮</span>
                                    <p>No active sessions</p>
                                    <button className="btn-create" onClick={handleCreateGame}>
                                        Create Your First Session
                                    </button>
                                </div>
                            )}
                        </div>

                        {/* Game History */}
                        <div className="games-section">
                            <h3>
                                <span className="section-icon">📜</span> Session History
                            </h3>
                            {gameHistory.length > 0 ? (
                                <div className="games-list">
                                    {gameHistory.map((game) => (
                                        <div key={game.session_id} className="game-list-item">
                                            <div className="game-list-info">
                                                <h4>{game.session_name}</h4>
                                                <p>{game.description || 'Completed session'}</p>
                                            </div>
                                            <span className="game-status status-completed">Completed</span>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="empty-state">
                                    <span className="empty-icon">📋</span>
                                    <p>No session history</p>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Settings Tab */}
                {activeTab === 'settings' && (
                    <div className="settings-tab fade-in">
                        <h2>Account Settings</h2>
                        
                        <div className="settings-section">
                            <h3>Profile Information</h3>
                            <div className="settings-form">
                                <div className="form-group">
                                    <label>User ID</label>
                                    <input type="text" value={userId} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Username</label>
                                    <input type="text" value={userProfile?.username || ''} disabled />
                                </div>
                            </div>
                        </div>

                        <div className="settings-section">
                            <h3>Preferences</h3>
                            <div className="settings-form">
                                <div className="form-group">
                                    <label>Theme</label>
                                    <select defaultValue="dark">
                                        <option value="dark">Dark (Default)</option>
                                        <option value="light">Light</option>
                                        <option value="auto">Auto</option>
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label>Language</label>
                                    <select defaultValue="en">
                                        <option value="en">English</option>
                                        <option value="ru">Русский</option>
                                    </select>
                                </div>
                            </div>
                        </div>

                        <div className="settings-section danger-zone">
                            <h3>⚠️ Danger Zone</h3>
                            <p className="danger-description">
                                Irreversible actions that will permanently affect your account
                            </p>
                            <div className="danger-actions">
                                <button className="btn-danger">
                                    Delete All Characters
                                </button>
                                <button className="btn-danger">
                                    Delete Account
                                </button>
                            </div>
                        </div>

                        <div className="settings-section">
                            <h3>Session</h3>
                            <button 
                                className="btn-logout"
                                onClick={() => {
                                    localStorage.removeItem('access_token');
                                    localStorage.removeItem('username');
                                    localStorage.removeItem('userId');
                                    window.location.reload();
                                }}
                            >
                                🚪 Logout
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
