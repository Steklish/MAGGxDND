import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGameStore } from '../store/gameStore';
import api from '../services/api';
import { VectorIcon } from '../components/common/VectorIcon';
import { LanguageSelector } from '../components/common/LanguageSelector';
import { useTranslation } from '../i18n/useTranslation';
import './AuthPage.css';

export const AuthPage: React.FC = () => {
    const navigate = useNavigate();
    const { setAuthenticated, setUsername, setUserId, setAccessToken, setIsGuest } = useGameStore();
    const { t } = useTranslation();

    const [nickname, setNickname] = useState(localStorage.getItem('username') || '');
    const [isPasswordMode, setIsPasswordMode] = useState(false);
    const [password, setPassword] = useState('');
    const [isRegister, setIsRegister] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleQuickEnter = async (e?: React.FormEvent) => {
        if (e) e.preventDefault();
        const trimmedName = nickname.trim() || `Adventurer_${Math.floor(Math.random() * 9000 + 1000)}`;
        setIsLoading(true);
        setError(null);

        try {
            const resp = await api.post('/auth/guest', { username: trimmedName });
            const data = resp.data;

            // Save credentials
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('username', data.username);
            localStorage.setItem('userId', String(data.user_id));
            localStorage.setItem('is_guest', 'true');

            // Update Zustand store
            setAccessToken(data.access_token);
            setUsername(data.username);
            setUserId(data.user_id);
            setAuthenticated(true);
            setIsGuest(true);

            navigate('/lobby');
        } catch (err: any) {
            console.error('Login error:', err);
            setError(err.response?.data?.detail || 'Failed to enter the realm. Server may be warming up.');
        } finally {
            setIsLoading(false);
        }
    };

    const handlePasswordAuth = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!nickname.trim() || !password) {
            setError(t.auth.errorFillBoth);
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const endpoint = isRegister ? '/auth/register' : '/auth/login/json';
            const payload = { username: nickname.trim(), password };
            const resp = await api.post(endpoint, payload);
            const data = resp.data;

            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('username', data.username || nickname.trim());
            if (data.user_id) localStorage.setItem('userId', String(data.user_id));
            localStorage.setItem('is_guest', 'false');

            setAccessToken(data.access_token);
            setUsername(data.username || nickname.trim());
            if (data.user_id) setUserId(data.user_id);
            setAuthenticated(true);
            setIsGuest(false);

            navigate('/lobby');
        } catch (err: any) {
            console.error('Auth error:', err);
            setError(err.response?.data?.detail || 'Authentication failed. Please check your credentials.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="auth-portal-container">
            <div style={{ position: 'absolute', top: '1.25rem', right: '1.5rem', zIndex: 20 }}>
                <LanguageSelector />
            </div>
            <div className="auth-portal-card">
                <div className="portal-header">
                    <div className="portal-emblem">
                        <VectorIcon name="rune" size="2.8rem" />
                    </div>
                    <h1 className="portal-title">{t.auth.title}</h1>
                    <p className="portal-subtitle">{t.auth.subtitle}</p>
                </div>

                {error && <div className="portal-alert-error">{error}</div>}

                {!isPasswordMode ? (
                    <form onSubmit={handleQuickEnter} className="portal-form">
                        <div className="portal-input-group">
                            <label htmlFor="adventurer-name">{t.auth.username}</label>
                            <input
                                id="adventurer-name"
                                type="text"
                                placeholder={t.auth.usernamePlaceholder}
                                value={nickname}
                                onChange={(e) => setNickname(e.target.value)}
                                autoFocus
                                maxLength={32}
                            />
                            <span className="portal-hint">{t.auth.guestHeading}</span>
                        </div>

                        <button
                            type="submit"
                            className="portal-btn-primary"
                            disabled={isLoading}
                        >
                            {isLoading ? t.auth.connecting : <><VectorIcon name="sword" /> {t.auth.enterTheRealm}</>}
                        </button>

                        <div className="portal-footer-links">
                            <button
                                type="button"
                                className="portal-text-btn"
                                onClick={() => {
                                    setIsPasswordMode(true);
                                    setError(null);
                                }}
                            >
                                <VectorIcon name="helm" /> {t.auth.switchPassword}
                            </button>
                        </div>
                    </form>
                ) : (
                    <form onSubmit={handlePasswordAuth} className="portal-form">
                        <div className="portal-input-group">
                            <label htmlFor="auth-username">{t.auth.username}</label>
                            <input
                                id="auth-username"
                                type="text"
                                placeholder={t.auth.usernamePlaceholder}
                                value={nickname}
                                onChange={(e) => setNickname(e.target.value)}
                                autoFocus
                            />
                        </div>

                        <div className="portal-input-group">
                            <label htmlFor="auth-password">{t.auth.password}</label>
                            <input
                                id="auth-password"
                                type="password"
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </div>

                        <button
                            type="submit"
                            className="portal-btn-primary"
                            disabled={isLoading}
                        >
                            {isLoading ? t.auth.connecting : isRegister ? (
                                <><VectorIcon name="magic" /> {t.auth.register}</>
                            ) : (
                                <><VectorIcon name="gate" /> {t.auth.login}</>
                            )}
                        </button>

                        <div className="portal-footer-links">
                            <button
                                type="button"
                                className="portal-text-btn"
                                onClick={() => setIsRegister(!isRegister)}
                            >
                                {isRegister ? t.auth.switchLogin : t.auth.switchRegister}
                            </button>
                            <span className="dot-divider">•</span>
                            <button
                                type="button"
                                className="portal-text-btn"
                                onClick={() => {
                                    setIsPasswordMode(false);
                                    setError(null);
                                }}
                            >
                                <VectorIcon name="horse" /> {t.auth.switchGuest}
                            </button>
                        </div>
                    </form>
                )}
            </div>
        </div>
    );
};
