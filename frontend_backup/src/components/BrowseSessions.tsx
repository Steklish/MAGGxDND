import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { sessionAPI, PublicSession } from '../services/sessionAPI';
import { useGameStore } from '../store/gameStore';
import './BrowseSessions.css';

interface BrowseSessionsProps {
    onJoinSession?: (sessionId: string) => void;
}

export const BrowseSessions: React.FC<BrowseSessionsProps> = ({ onJoinSession }) => {
    const navigate = useNavigate();

    const [sessions, setSessions] = useState<PublicSession[]>([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadSessions();
    }, []);

    const loadSessions = async (search?: string) => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await sessionAPI.browsePublicSessions(search);
            setSessions(response.sessions);
        } catch (err: any) {
            console.error('Failed to load public sessions:', err);
            setError(err.response?.data?.detail || 'Failed to load sessions');
        } finally {
            setIsLoading(false);
        }
    };

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        loadSessions(searchTerm);
    };

    const handleJoinClick = (session: PublicSession) => {
        if (onJoinSession) {
            onJoinSession(session.session_id);
        }
    };

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'created':
                return <span className="status-badge status-created">Waiting</span>;
            case 'running':
                return <span className="status-badge status-running">Running</span>;
            case 'completed':
                return <span className="status-badge status-completed">Completed</span>;
            default:
                return <span className="status-badge">{status}</span>;
        }
    };

    const getGameModeIcon = (mode: string) => {
        return mode === 'COMBAT' ? '⚔️' : '📖';
    };

    if (isLoading) {
        return (
            <div className="browse-sessions">
                <div className="loading-state">
                    <div className="spinner"></div>
                    <p>Loading public sessions...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="browse-sessions">
            <div className="browse-header">
                <h2>Browse Public Sessions</h2>
                <p>Find and join sessions created by other players</p>
            </div>

            {/* Search Bar */}
            <form className="search-bar" onSubmit={handleSearch}>
                <input
                    type="text"
                    placeholder="Search sessions by name or description..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="search-input"
                />
                <button type="submit" className="search-btn">
                    🔍 Search
                </button>
                {searchTerm && (
                    <button 
                        type="button" 
                        className="clear-btn"
                        onClick={() => {
                            setSearchTerm('');
                            loadSessions();
                        }}
                    >
                        Clear
                    </button>
                )}
            </form>

            {/* Error State */}
            {error && (
                <div className="error-message">
                    <span>⚠️</span>
                    <span>{error}</span>
                </div>
            )}

            {/* Sessions List */}
            {sessions.length === 0 ? (
                <div className="empty-state">
                    <div className="empty-icon">🎲</div>
                    <h3>No Public Sessions Found</h3>
                    <p>
                        {searchTerm 
                            ? 'Try a different search term or clear the search.'
                            : 'There are no public sessions available right now.'}
                    </p>
                </div>
            ) : (
                <div className="sessions-grid">
                    {sessions.map(session => (
                        <div 
                            key={session.session_id} 
                            className={`session-card ${session.has_joined ? 'joined' : ''} ${session.is_owner ? 'owner' : ''}`}
                        >
                            <div className="session-card-header">
                                <h3>{session.session_name}</h3>
                                <div className="session-badges">
                                    {getStatusBadge(session.status)}
                                    {session.is_owner && <span className="badge badge-owner">Owner</span>}
                                    {session.has_joined && <span className="badge badge-joined">Joined</span>}
                                </div>
                            </div>

                            <div className="session-card-info">
                                <div className="info-row">
                                    <span className="info-label">Owner:</span>
                                    <span className="info-value">{session.owner_name}</span>
                                </div>
                                <div className="info-row">
                                    <span className="info-label">Mode:</span>
                                    <span className="info-value">
                                        {getGameModeIcon(session.game_mode)} {session.game_mode}
                                    </span>
                                </div>
                                <div className="info-row">
                                    <span className="info-label">Players:</span>
                                    <span className="info-value">
                                        {session.player_count} / {session.max_players}
                                    </span>
                                </div>
                                {session.description && (
                                    <div className="session-description">
                                        {session.description.substring(0, 150)}
                                        {session.description.length > 150 ? '...' : ''}
                                    </div>
                                )}
                            </div>

                            <div className="session-card-actions">
                                {session.has_joined ? (
                                    <button
                                        className="btn-continue"
                                        onClick={() => handleJoinClick(session)}
                                    >
                                        Continue Game
                                    </button>
                                ) : session.status === 'created' || session.status === 'running' ? (
                                    <button
                                        className="btn-join"
                                        onClick={() => handleJoinClick(session)}
                                    >
                                        Join Session
                                    </button>
                                ) : (
                                    <button className="btn-disabled" disabled>
                                        Session {session.status}
                                    </button>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};
