import React, { useEffect, useState } from 'react';
import './ErrorPage.css';

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

    useEffect(() => {
        // Trigger fade-in animation
        requestAnimationFrame(() => setVisible(true));
    }, []);

    return (
        <div className={`error-page ${visible ? 'visible' : ''}`}>
            <div className="error-background">
                <img src="/arts/backgrounds/bg-error.png" alt="Error" className="error-bg-image" />
                <div className="error-overlay"></div>
            </div>

            <div className="error-content">
                <div className="error-icon">⚠️</div>
                <h1 className="error-title">{title}</h1>
                <p className="error-message">{message}</p>

                {onRetry && (
                    <button className="error-retry-btn" onClick={onRetry}>
                        <span className="retry-icon">🔄</span>
                        <span>Try Again</span>
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
