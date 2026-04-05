import React, { useEffect, useState, useRef } from 'react';
import './ErrorPage.css';

// Preload the error background image so it's ready instantly
const preloadErrorBackground = () => {
    const img = new Image();
    img.src = '/arts/backgrounds/bg-error.png';
};

// Run preload immediately when module loads
preloadErrorBackground();

interface ErrorPageProps {
    title?: string;
    message?: string;
    onRetry?: () => void;
}

export const ErrorPage: React.FC<ErrorPageProps> = ({
    title = 'Connection Lost',
    message = 'The server is currently unavailable. Please try again later.',
    onRetry,
}) => {
    const [visible, setVisible] = useState(false);
    const [retrying, setRetrying] = useState(false);
    const retryTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    useEffect(() => {
        // Trigger fade-in animation
        requestAnimationFrame(() => setVisible(true));
    }, []);

    useEffect(() => {
        // Disable body scroll when error page is shown
        const html = document.documentElement;
        const body = document.body;
        html.style.overflow = 'hidden';
        body.style.overflow = 'hidden';
        // Also lock touch scroll on mobile
        html.style.touchAction = 'none';

        return () => {
            // Restore body scroll when error page is removed
            html.style.overflow = '';
            body.style.overflow = '';
            html.style.touchAction = '';
            if (retryTimeoutRef.current) {
                clearTimeout(retryTimeoutRef.current);
            }
        };
    }, []);

    const handleRetry = () => {
        if (retrying || !onRetry) return;

        setRetrying(true);

        // Call the retry callback
        onRetry();

        // Reset the retrying state after a short delay
        retryTimeoutRef.current = setTimeout(() => {
            setRetrying(false);
        }, 2000);
    };

    return (
        <div className={`error-page ${visible ? 'visible' : ''}`} role="dialog" aria-modal="true" aria-labelledby="error-title">
            <div className="error-background"></div>

            <div className="error-content">
                <div className="error-icon">⚠️</div>
                <h1 className="error-title" id="error-title">{title}</h1>
                <p className="error-message">{message}</p>

                {onRetry && (
                    <button
                        className={`error-retry-btn ${retrying ? 'retrying' : ''}`}
                        onClick={handleRetry}
                        disabled={retrying}
                        aria-busy={retrying}
                    >
                        <span className="retry-icon">🔄</span>
                        <span>{retrying ? 'Retrying...' : 'Try Again'}</span>
                    </button>
                )}

                <div className="error-hints">
                    <p>💡 <strong>Tips:</strong></p>
                    <ul>
                        <li>Check if the server is running</li>
                        <li>Verify your internet connection</li>
                        <li>Try refreshing the page</li>
                    </ul>
                </div>
            </div>
        </div>
    );
};
