import React, { useState } from 'react';
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
    const [formData, setFormData] = useState({
        username: '',
        password: '',
        confirmPassword: '',
    });
    const [errors, setErrors] = useState<Record<string, string>>({});

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
            if (isLogin) {
                // Login
                const formParams = new URLSearchParams();
                formParams.append('username', formData.username);
                formParams.append('password', formData.password);
                
                const response = await axios.post('/api/v1/auth/login', formParams, {
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                });
                
                if (response.data.access_token) {
                    localStorage.setItem('access_token', response.data.access_token);
                    localStorage.setItem('username', formData.username);

                    // Get user ID
                    try {
                        const userResponse = await axios.get(`/api/v1/users/username/${formData.username}`);
                        const userId = userResponse.data.id.toString();
                        localStorage.setItem('userId', userId);
                        
                        // Call onLoginSuccess FIRST before setting authenticated
                        onLoginSuccess?.(userResponse.data.id, formData.username);
                        
                        setAuthenticated(true);
                        onClose();
                    } catch (error) {
                        console.error('Failed to get user ID:', error);
                        setAuthenticated(true);
                        onClose();
                    }
                }
            } else {
                // Register
                const response = await axios.post('/api/v1/users/', {
                    username: formData.username,
                    password: formData.password,
                });
                
                if (response.data.id) {
                    // Auto-login after registration
                    const formParams = new URLSearchParams();
                    formParams.append('username', formData.username);
                    formParams.append('password', formData.password);
                    
                    const loginResponse = await axios.post('/api/v1/auth/login', formParams, {
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                    });
                    
                    if (loginResponse.data.access_token) {
                        localStorage.setItem('access_token', loginResponse.data.access_token);
                        localStorage.setItem('username', formData.username);
                        localStorage.setItem('userId', response.data.id.toString());
                        setAuthenticated(true);
                        onRegisterSuccess?.(response.data.id, formData.username);
                        onClose();
                    }
                }
            }
        } catch (error: any) {
            setIsLoading(false);
            if (error.response) {
                setErrors({ submit: error.response.data.detail || 'Authentication failed' });
            } else {
                setErrors({ submit: 'Network error. Please try again.' });
            }
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
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
        });
    };

    return (
        <div className="auth-modal-overlay" onClick={onClose}>
            <div className="auth-modal" onClick={e => e.stopPropagation()}>
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
                                    <input type="checkbox" name="remember" />
                                    <span>Remember me</span>
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
                        <button className="social-btn discord">
                            <span className="social-icon">🎮</span>
                            <span>Discord</span>
                        </button>
                        <button className="social-btn google">
                            <span className="social-icon">G</span>
                            <span>Google</span>
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
