import React, { useState, useEffect } from 'react';
import { useGameStore } from '../store/gameStore';
import { CharacterProfile } from '../services/characterAPI';
import './CharacterProfileSelector.css';

interface CharacterProfileSelectorProps {
    sessionId: string;
    playerName: string;
    onSelect: (profileId: number) => void;
    onCancel: () => void;
    isLoading?: boolean;
}

export const CharacterProfileSelector: React.FC<CharacterProfileSelectorProps> = ({
    sessionId,
    playerName,
    onSelect,
    onCancel,
    isLoading = false
}) => {
    const { characterProfiles, loadCharacterProfiles, joinSessionWithProfile } = useGameStore();
    const [selectedProfileId, setSelectedProfileId] = useState<number | null>(null);
    const [isJoining, setIsJoining] = useState(false);

    useEffect(() => {
        // Load profiles when component mounts
        const userId = useGameStore.getState().userId;
        if (userId) {
            loadCharacterProfiles(userId);
        }
    }, [loadCharacterProfiles]);

    const profiles = Array.from(characterProfiles.values());

    const handleJoinWithProfile = async () => {
        if (!selectedProfileId) return;

        setIsJoining(true);
        try {
            await joinSessionWithProfile(sessionId, playerName, selectedProfileId);
            onSelect(selectedProfileId);
        } catch (error) {
            console.error('Failed to join session with profile:', error);
        } finally {
            setIsJoining(false);
        }
    };

    if (isLoading) {
        return (
            <div className="profile-selector-overlay">
                <div className="profile-selector">
                    <div className="loading-state">
                        <div className="spinner"></div>
                        <p>Loading character profiles...</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="profile-selector-overlay">
            <div className="profile-selector">
                <div className="profile-selector-header">
                    <h2>Choose Your Character</h2>
                    <p>Select a saved character to join the session</p>
                </div>

                {profiles.length === 0 ? (
                    <div className="no-profiles">
                        <div className="no-profiles-icon">📜</div>
                        <h3>No Saved Characters</h3>
                        <p>You don't have any saved character profiles yet.</p>
                        <p className="hint">
                            Create a character in the Character Creation screen to save profiles for future sessions.
                        </p>
                        <button className="btn-cancel" onClick={onCancel}>
                            Go Back
                        </button>
                    </div>
                ) : (
                    <>
                        <div className="profiles-grid">
                            {profiles.map(profile => (
                                <div
                                    key={profile.id}
                                    className={`profile-card ${selectedProfileId === profile.id ? 'selected' : ''} ${profile.is_favorite ? 'favorite' : ''}`}
                                    onClick={() => setSelectedProfileId(profile.id)}
                                >
                                    <div className="profile-card-header">
                                        <h3>{profile.name}</h3>
                                        {profile.is_favorite && <span className="favorite-badge">⭐</span>}
                                    </div>
                                    
                                    <div className="profile-info">
                                        <div className="profile-race-class">
                                            {profile.race} {profile.char_class}
                                        </div>
                                        <div className="profile-level">
                                            Level {profile.level}
                                        </div>
                                        
                                        <div className="profile-stats">
                                            <div className="stat">
                                                <span className="stat-label">HP</span>
                                                <span className="stat-value">{profile.max_hp}</span>
                                            </div>
                                            <div className="stat">
                                                <span className="stat-label">AC</span>
                                                <span className="stat-value">{profile.armor_class}</span>
                                            </div>
                                            <div className="stat">
                                                <span className="stat-label">SPD</span>
                                                <span className="stat-value">{profile.speed}</span>
                                            </div>
                                        </div>

                                        {profile.backstory_summary && (
                                            <div className="profile-backstory">
                                                {profile.backstory_summary.substring(0, 100)}
                                                {profile.backstory_summary.length > 100 ? '...' : ''}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="profile-selector-actions">
                            <button className="btn-cancel" onClick={onCancel} disabled={isJoining}>
                                Cancel
                            </button>
                            <button
                                className="btn-join"
                                onClick={handleJoinWithProfile}
                                disabled={!selectedProfileId || isJoining}
                            >
                                {isJoining ? 'Joining...' : `Join as ${profiles.find(p => p.id === selectedProfileId)?.name || 'Character'}`}
                            </button>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};
