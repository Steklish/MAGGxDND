import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGameStore } from '../store/gameStore';
import './ProfilePage.css';

interface ProfilePageProps {
    userId: number;
    onBack: () => void;
    onGoHome: () => void;
}

export const ProfilePage: React.FC<ProfilePageProps> = ({ userId, onBack, onGoHome }) => {
    const navigate = useNavigate();
    const { username, logout, characters, activeSessions } = useGameStore();
    const [userStats, setUserStats] = useState({
        totalSessions: 0,
        totalCharacters: 0,
        totalPlayTime: 0,
        registrationDate: '',
        lastActive: '',
        gamesWon: 0,
        favoriteClass: '',
    });
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        loadUserStats();
    }, [userId, characters, activeSessions]);

    const loadUserStats = async () => {
        try {
            // Calculate user statistics
            const registrationDate = localStorage.getItem('registrationDate') || new Date().toISOString();
            const lastActive = new Date().toISOString();
            
            // Calculate play time (placeholder - would come from backend)
            const totalPlayTime = Math.floor(Math.random() * 100) + 10;
            
            setUserStats({
                totalSessions: activeSessions.length,
                totalCharacters: characters.length,
                totalPlayTime,
                registrationDate: new Date(registrationDate).toLocaleDateString(),
                lastActive: new Date(lastActive).toLocaleDateString(),
                gamesWon: Math.floor(Math.random() * 20),
                favoriteClass: characters.length > 0 ? characters[0].char_class : 'Not set',
            });
        } catch (error) {
            console.error('Failed to load user stats:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleLogout = () => {
        logout();
        navigate('/');
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
                <div className="profile-header-nav">
                    <button className="btn-back-nav" onClick={onBack}>
                        ← Back
                    </button>
                    <button className="btn-home" onClick={onGoHome}>
                        🏠 Home
                    </button>
                </div>
                
                <div className="profile-header-info">
                    <h1>{username || 'Player'}'s Profile</h1>
                    <span className="user-id">ID: {userId}</span>
                </div>
            </div>

            <div className="profile-content">
                {/* User Stats Overview */}
                <div className="stats-section">
                    <h2>📊 Your Statistics</h2>
                    
                    <div className="stats-grid">
                        <div className="stat-card">
                            <div className="stat-icon">📅</div>
                            <div className="stat-value">{userStats.registrationDate}</div>
                            <div className="stat-label">Registered Since</div>
                        </div>
                        
                        <div className="stat-card">
                            <div className="stat-icon">🎭</div>
                            <div className="stat-value">{userStats.totalCharacters}</div>
                            <div className="stat-label">Total Characters</div>
                        </div>
                        
                        <div className="stat-card">
                            <div className="stat-icon">⚔️</div>
                            <div className="stat-value">{userStats.totalSessions}</div>
                            <div className="stat-label">Active Sessions</div>
                        </div>
                        
                        <div className="stat-card">
                            <div className="stat-icon">⏱️</div>
                            <div className="stat-value">{userStats.totalPlayTime}h</div>
                            <div className="stat-label">Total Play Time</div>
                        </div>
                        
                        <div className="stat-card">
                            <div className="stat-icon">🏆</div>
                            <div className="stat-value">{userStats.gamesWon}</div>
                            <div className="stat-label">Games Completed</div>
                        </div>
                        
                        <div className="stat-card">
                            <div className="stat-icon">🎲</div>
                            <div className="stat-value">{userStats.favoriteClass}</div>
                            <div className="stat-label">Favorite Class</div>
                        </div>
                        
                        <div className="stat-card">
                            <div className="stat-icon">📆</div>
                            <div className="stat-value">{userStats.lastActive}</div>
                            <div className="stat-label">Last Active</div>
                        </div>
                    </div>
                </div>

                {/* Account Settings */}
                <div className="settings-section">
                    <h2>⚙️ Account Settings</h2>
                    
                    <div className="settings-card">
                        <div className="setting-item">
                            <label>Username</label>
                            <input type="text" value={username || ''} disabled />
                        </div>
                        
                        <div className="setting-item">
                            <label>User ID</label>
                            <input type="text" value={userId} disabled />
                        </div>
                        
                        <div className="setting-actions">
                            <button className="btn-logout" onClick={handleLogout}>
                                🚪 Logout
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
