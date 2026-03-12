import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useGameStore } from '../store/gameStore';
import './AuthModal.css';

interface AuthModalProps {
    mode: 'login' | 'register';
    onClose: () => void;
    onRegisterSuccess?: (userId: number, username: string) => void;
    onLoginSuccess?: (userId: number, username: string) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ mode, onClose, onRegisterSuccess, onLoginSuccess }) => {
    const [isLogin, setIsLogin] = useState(mode === 'login');
    const [isLoading, setIsLoading] = useState(false);
    const setAuthenticated = useGameStore(state => state.setAuthenticated);
    const setUserId = useGameStore(state => state.setUserId);
    const setUsername = useGameStore(state => state.setUsername);
    const setAccessToken = useGameStore(state => state.setAccessToken);
    
    const [formData, setFormData] = useState({
        username: '',
        password: '',
        confirmPassword: '',
        rememberMe: false,
    });
    const [errors, setErrors] = useState<Record<string, string>>({});
    
    // Ref for the modal content to detect clicks inside
    const modalRef = useRef<HTMLDivElement>(null);

    // Prevent modal close when clicking inside modal content (including text selection)
    useEffect(() => {
        const handleMouseDown = (e: MouseEvent) => {
            if (modalRef.current && !modalRef.current.contains(e.target as Node)) {
                // Only close if clicking on overlay, not on modal content
                const overlay = document.querySelector('.auth-modal-overlay');
                if (overlay && overlay.contains(e.target as Node)) {
                    // Check if the click is actually on the overlay and not due to text selection
                    const selection = window.getSelection();
                    if (selection && selection.toString().length === 0) {
                        onClose();
                    }
                }
            }
        };

        document.addEventListener('mousedown', handleMouseDown);
        return () => {
            document.removeEventListener('mousedown', handleMouseDown);
        };
    }, [onClose]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setErrors({});

        // Validate form
        const newErrors: Record<string, string> = {};

        if (!formData.username) {
            newErrors.username = 'Username is required';
        } else if (formData.username.length < 3) {
            newErrors.username = 'Username must be at least 3 characters';
        }

        if (!formData.password) {
            newErrors.password = 'Password is required';
        } else if (formData.password.length < 8) {
            newErrors.password = 'Password must be at least 8 characters';
        }

        if (!isLogin) {
            if (formData.password !== formData.confirmPassword) {
                newErrors.confirmPassword = 'Passwords do not match';
            }
        }

        if (Object.keys(newErrors).length > 0) {
            setErrors(newErrors);
            setIsLoading(false);
            return;
        }

        try {
            // Use backend API for authentication
            const loginUrl = isLogin ? '/api/v1/auth/login/json' : '/api/v1/auth/register';
            
            if (isLogin) {
                // Login with backend
                const response = await axios.post('/api/v1/auth/login/json', {
                    username: formData.username,
                    password: formData.password,
                    remember_me: formData.rememberMe,
                }, {
                    withCredentials: true, // Send cookies
                });

                const { access_token, user_id, username: respUsername, is_guest } = response.data;

                // Store auth state
                setAccessToken(access_token);
                if (user_id) {
                    setUserId(user_id);
                }
                if (respUsername) {
                    setUsername(respUsername);
                }
                setAuthenticated(true);

                // Store in localStorage for persistence across refreshes
                if (formData.rememberMe) {
                    localStorage.setItem('remember_me', 'true');
                    localStorage.setItem('access_token', access_token);
                    if (user_id) {
                        localStorage.setItem('userId', user_id.toString());
                    }
                    if (respUsername) {
                        localStorage.setItem('username', respUsername);
                    }
                }

                console.log('✅ Login successful:', respUsername, is_guest ? '(Guest)' : '(User)');

                if (onLoginSuccess) {
                    onLoginSuccess(user_id || 0, respUsername || formData.username);
                }
            } else {
                // Register with backend
                const registerResponse = await axios.post('/api/v1/auth/register', {
                    username: formData.username,
                    password: formData.password,
                }, {
                    withCredentials: true,
                });

                const { access_token, user_id, username: respUsername } = registerResponse.data;

                // Store auth state
                setAccessToken(access_token);
                if (user_id) {
                    setUserId(user_id);
                }
                if (respUsername) {
                    setUsername(respUsername);
                }
                setAuthenticated(true);

                // Store in localStorage
                localStorage.setItem('access_token', access_token);
                if (user_id) {
                    localStorage.setItem('userId', user_id.toString());
                }
                if (respUsername) {
                    localStorage.setItem('username', respUsername);
                }

                console.log('✅ Registration successful:', respUsername);

                if (onRegisterSuccess) {
                    onRegisterSuccess(user_id || 0, respUsername || formData.username);
                }
            }

            setAuthenticated(true);
            onClose();
        } catch (error: any) {
            console.error('Auth error:', error);
            const errorMessage = error.response?.data?.detail || 'Authentication failed. Please try again.';
            setErrors({ submit: errorMessage });
        } finally {
            setIsLoading(false);
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value, type, checked } = e.target;
        const newValue = type === 'checkbox' ? checked : value;
        setFormData(prev => ({ ...prev, [name]: newValue }));
        if (errors[name]) {
            setErrors(prev => ({ ...prev, [name]: '' }));
        }
    };

    const toggleMode = () => {
        setIsLogin(!isLogin);
        setErrors({});
        setFormData({
            username: '',
            password: '',
            confirmPassword: '',
            rememberMe: false,
        });
    };

    const handleGuestLogin = async () => {
        setIsLoading(true);
        try {
            const response = await axios.post('/api/v1/auth/guest', {}, {
                withCredentials: true,
            });

            const { access_token, expires_at } = response.data;

            setAccessToken(access_token);
            setAuthenticated(true);

            // Store guest info
            localStorage.setItem('access_token', access_token);
            localStorage.setItem('is_guest', 'true');

            console.log('✅ Guest login successful');
            onClose();
        } catch (error: any) {
            console.error('Guest login error:', error);
            setErrors({ submit: 'Failed to enter as guest. Please try again.' });
        } finally {
            setIsLoading(false);
        }
    };

    const handleGoogleLogin = () => {
        // Redirect to backend OAuth endpoint
        window.location.href = '/api/v1/oauth/google/login';
    };

    const handleDiscordLogin = () => {
        // Redirect to backend OAuth endpoint
        window.location.href = '/api/v1/oauth/discord/login';
    };

    return (
        <div className="auth-modal-overlay">
            <div className="auth-modal" ref={modalRef}>
                <div className="auth-modal-header">
                    <div className="auth-logo">
                        <span className="auth-logo-icon">🐉</span>
                        <span className="auth-logo-text">
                            <span className="auth-magg">MAGG</span>
                            <span className="auth-x">x</span>
                            <span className="auth-dnd">DND</span>
                        </span>
                    </div>
                    <button className="auth-close" onClick={onClose}>
                        <span>✕</span>
                    </button>
                </div>

                <div className="auth-modal-body">
                    <div className="auth-title-section">
                        <h2 className="auth-title">
                            {isLogin ? 'Welcome Back, Adventurer!' : 'Begin Your Journey'}
                        </h2>
                        <p className="auth-subtitle">
                            {isLogin
                                ? 'Sign in to continue your adventure'
                                : 'Create an account and start your epic quest'}
                        </p>
                    </div>

                    {errors.submit && (
                        <div className="auth-submit-error">
                            <span>⚠️</span>
                            <span>{errors.submit}</span>
                        </div>
                    )}

                    <form className="auth-form" onSubmit={handleSubmit}>
                        <div className="form-group">
                            <label htmlFor="username">Username</label>
                            <div className="input-wrapper">
                                <span className="input-icon">👤</span>
                                <input
                                    type="text"
                                    id="username"
                                    name="username"
                                    value={formData.username}
                                    onChange={handleChange}
                                    placeholder={isLogin ? "Enter your username" : "Choose a username"}
                                    className={errors.username ? 'error' : ''}
                                    required
                                    autoComplete="username"
                                />
                            </div>
                            {errors.username && (
                                <span className="error-message">{errors.username}</span>
                            )}
                        </div>

                        <div className="form-group">
                            <label htmlFor="password">Password</label>
                            <div className="input-wrapper">
                                <span className="input-icon">🔒</span>
                                <input
                                    type="password"
                                    id="password"
                                    name="password"
                                    value={formData.password}
                                    onChange={handleChange}
                                    placeholder="Enter your password"
                                    className={errors.password ? 'error' : ''}
                                    required
                                    autoComplete={isLogin ? "current-password" : "new-password"}
                                />
                            </div>
                            {errors.password && (
                                <span className="error-message">{errors.password}</span>
                            )}
                        </div>

                        {!isLogin && (
                            <div className="form-group">
                                <label htmlFor="confirmPassword">Confirm Password</label>
                                <div className="input-wrapper">
                                    <span className="input-icon">🔐</span>
                                    <input
                                        type="password"
                                        id="confirmPassword"
                                        name="confirmPassword"
                                        value={formData.confirmPassword}
                                        onChange={handleChange}
                                        placeholder="Confirm your password"
                                        className={errors.confirmPassword ? 'error' : ''}
                                        autoComplete="new-password"
                                    />
                                </div>
                                {errors.confirmPassword && (
                                    <span className="error-message">{errors.confirmPassword}</span>
                                )}
                            </div>
                        )}

                        {isLogin && (
                            <div className="form-options">
                                <label className="remember-me">
                                    <input 
                                        type="checkbox" 
                                        name="rememberMe"
                                        checked={formData.rememberMe}
                                        onChange={handleChange}
                                    />
                                    <span>Remember me (30 days)</span>
                                </label>
                                <a href="#" className="forgot-password">Forgot password?</a>
                            </div>
                        )}

                        <button
                            type="submit"
                            className="auth-submit"
                            disabled={isLoading}
                        >
                            {isLoading ? (
                                <span className="loading-spinner"></span>
                            ) : (
                                <span>{isLogin ? 'Sign In' : 'Create Account'}</span>
                            )}
                        </button>
                    </form>

                    <div className="auth-divider">
                        <span>or continue with</span>
                    </div>

                    <div className="social-auth">
                        <button
                            className="social-btn google"
                            onClick={handleGoogleLogin}
                            disabled={isLoading}
                            title="Sign in with Google"
                        >
                            <svg className="social-icon-svg" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                            </svg>
                            <span>Continue with Google</span>
                        </button>
                        <button
                            className="social-btn discord"
                            onClick={handleDiscordLogin}
                            disabled={isLoading}
                            title="Sign in with Discord"
                        >
                            <svg className="social-icon-svg" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" fill="currentColor"/>
                            </svg>
                            <span>Continue with Discord</span>
                        </button>
                        <button
                            className="social-btn guest"
                            onClick={handleGuestLogin}
                            disabled={isLoading}
                            title="Continue as guest"
                        >
                            <span className="social-icon">🎭</span>
                            <span>Continue as Guest</span>
                        </button>
                    </div>

                    <div className="auth-switch">
                        <span>
                            {isLogin ? "Don't have an account?" : 'Already have an account?'}
                        </span>
                        <button onClick={toggleMode} className="toggle-auth">
                            {isLogin ? 'Sign Up' : 'Sign In'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
