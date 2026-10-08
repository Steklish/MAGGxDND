import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './CharacterDetail.css';

interface CharacterDetailProps {
    characterId: number;
    onBack: () => void;
    onEdit: () => void;
}

export const CharacterDetail: React.FC<CharacterDetailProps> = ({ characterId, onBack, onEdit }) => {
    const [character, setCharacter] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'overview' | 'combat' | 'skills' | 'equipment'>('overview');

    useEffect(() => {
        loadCharacter();
    }, [characterId]);

    const loadCharacter = async () => {
        try {
            const response = await axios.get(`/api/v1/characters/${characterId}`);
            setCharacter(response.data);
        } catch (error) {
            console.error('Failed to load character:', error);
        } finally {
            setIsLoading(false);
        }
    };

    if (isLoading || !character) {
        return (
            <div className="character-detail loading">
                <div className="loading-spinner">
                    <div className="spinner-ring"></div>
                    <div className="spinner-ring"></div>
                    <div className="spinner-ring"></div>
                </div>
                <p>Loading character...</p>
            </div>
        );
    }

    return (
        <div className="character-detail">
            <div className="detail-header">
                <button className="btn-back" onClick={onBack}>← Back</button>
                <h1>{character.name}</h1>
                <button className="btn-edit" onClick={onEdit}>✏️ Edit</button>
            </div>

            <div className="detail-content">
                {/* Character Overview */}
                <div className="char-overview">
                    <div className="char-portrait">
                        <div className="portrait-placeholder">
                            {character.race === 'Human' ? '🧙' : character.race === 'Elf' ? '🧝' : '🧌'}
                        </div>
                    </div>
                    
                    <div className="char-basic-info">
                        <h2>{character.name}</h2>
                        <p className="char-class">Level {character.level} {character.race} {character.char_class}</p>
                        
                        <div className="char-stats-brief">
                            <div className="stat-brief">
                                <span className="stat-label">HP</span>
                                <span className="stat-value">{character.current_hp}/{character.max_hp}</span>
                            </div>
                            <div className="stat-brief">
                                <span className="stat-label">AC</span>
                                <span className="stat-value">{character.armor_class}</span>
                            </div>
                            <div className="stat-brief">
                                <span className="stat-label">Speed</span>
                                <span className="stat-value">{character.speed}</span>
                            </div>
                            <div className="stat-brief">
                                <span className="stat-label">Proficiency</span>
                                <span className="stat-value">+{character.proficiency_bonus}</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Tabs */}
                <div className="char-tabs">
                    <button 
                        className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
                        onClick={() => setActiveTab('overview')}
                    >
                        Overview
                    </button>
                    <button 
                        className={`tab-btn ${activeTab === 'combat' ? 'active' : ''}`}
                        onClick={() => setActiveTab('combat')}
                    >
                        Combat
                    </button>
                    <button 
                        className={`tab-btn ${activeTab === 'skills' ? 'active' : ''}`}
                        onClick={() => setActiveTab('skills')}
                    >
                        Skills
                    </button>
                    <button 
                        className={`tab-btn ${activeTab === 'equipment' ? 'active' : ''}`}
                        onClick={() => setActiveTab('equipment')}
                    >
                        Equipment
                    </button>
                </div>

                {/* Tab Content */}
                <div className="tab-content">
                    {activeTab === 'overview' && (
                        <div className="overview-tab">
                            <h3>Ability Scores</h3>
                            <div className="ability-scores">
                                {Object.entries(character.stats || {}).map(([stat, value]) => (
                                    <div key={stat} className="ability-score">
                                        <div className="ability-label">{stat}</div>
                                        <div className="ability-value">{String(value)}</div>
                                        <div className="ability-modifier">
                                            {Number(value) >= 10 ? '+' : ''}{Math.floor((Number(value) - 10) / 2)}
                                        </div>
                                    </div>
                                ))}
                            </div>
                            
                            <h3>Backstory</h3>
                            <p className="backstory">{character.backstory_summary || 'No backstory provided'}</p>
                        </div>
                    )}

                    {activeTab === 'combat' && (
                        <div className="combat-tab">
                            <h3>Combat Stats</h3>
                            <div className="combat-stats">
                                <div className="combat-stat">
                                    <span>Initiative Bonus</span>
                                    <span>{character.initiative_bonus || 0}</span>
                                </div>
                                <div className="combat-stat">
                                    <span>Hit Dice</span>
                                    <span>{character.hit_dice || '1d8'}</span>
                                </div>
                            </div>
                            
                            <h3>Attacks</h3>
                            <div className="attacks-list">
                                {character.attacks?.map((attack: any, idx: number) => (
                                    <div key={idx} className="attack-item">
                                        <span>{attack.name}</span>
                                        <span>{attack.damage}</span>
                                    </div>
                                )) || <p>No attacks configured</p>}
                            </div>
                        </div>
                    )}

                    {activeTab === 'skills' && (
                        <div className="skills-tab">
                            <h3>Skill Proficiencies</h3>
                            <div className="skills-list">
                                {Object.entries(character.skills || {}).map(([skill, value]) => (
                                    <div key={skill} className="skill-item">
                                        <span className="skill-name">{skill}</span>
                                        <span className="skill-value">{String(value)}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {activeTab === 'equipment' && (
                        <div className="equipment-tab">
                            <h3>Inventory</h3>
                            <div className="equipment-list">
                                {character.inventory?.map((item: any, idx: number) => (
                                    <div key={idx} className="equipment-item">
                                        {item}
                                    </div>
                                )) || <p>No equipment</p>}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
