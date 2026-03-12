import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useGameStore } from '../store/gameStore';
import './OAuthCallback.css';

export const OAuthCallback: React.FC = () => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const { setAuthenticated, setUserId, setUsername, setAccessToken } = useGameStore();
    
    const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
    const [message, setMessage] = useState('');

    useEffect(() => {
        const handleOAuthCallback = async () => {
            const provider = searchParams.get('provider');
            const username = searchParams.get('username');
            const userId = searchParams.get('user_id');

            if (!provider || !username || !userId) {
                setStatus('error');
                setMessage('Invalid OAuth callback parameters');
                return;
            }

            try {
                // Get the access token from cookie (set by backend)
                let token: string | null = localStorage.getItem('access_token');
                
                if (!token) {
                    // Try to get from cookie directly
                    const cookieToken = document.cookie
                        .split('; ')
                        .find(row => row.startsWith('access_token='))
                        ?.split('=')[1];
                    
                    if (!cookieToken) {
                        setStatus('error');
                        setMessage('Failed to retrieve authentication token');
                        return;
                    }
                    
                    token = cookieToken;
                    localStorage.setItem('access_token', token);
                }

                // Update store
                setAuthenticated(true);
                setUserId(parseInt(userId));
                setUsername(username);
                setAccessToken(token);

                // Store in localStorage
                localStorage.setItem('userId', userId);
                localStorage.setItem('username', username);
                localStorage.setItem('is_guest', 'false');

                setStatus('success');
                setMessage(`Successfully logged in with ${provider}!`);

                // Redirect to home page after short delay
                setTimeout(() => {
                    navigate('/home');
                }, 2000);

            } catch (error) {
                console.error('OAuth callback error:', error);
                setStatus('error');
                setMessage('Failed to complete authentication');
            }
        };

        handleOAuthCallback();
    }, [searchParams, navigate]);

    return (
        <div className="oauth-callback">
            <div className="oauth-content">
                {status === 'processing' && (
                    <>
                        <div className="oauth-spinner">
                            <div className="spinner-ring"></div>
                            <div className="spinner-ring"></div>
                            <div className="spinner-ring"></div>
                        </div>
                        <h2>Completing your login...</h2>
                        <p>Please wait while we set up your adventure</p>
                    </>
                )}

                {status === 'success' && (
                    <>
                        <div className="oauth-success-icon">✓</div>
                        <h2>Login Successful!</h2>
                        <p>{message}</p>
                        <p>Redirecting to your adventure...</p>
                    </>
                )}

                {status === 'error' && (
                    <>
                        <div className="oauth-error-icon">✕</div>
                        <h2>Login Failed</h2>
                        <p>{message}</p>
                        <button 
                            className="btn-primary"
                            onClick={() => navigate('/')}
                        >
                            Return to Home
                        </button>
                    </>
                )}
            </div>
        </div>
    );
};
