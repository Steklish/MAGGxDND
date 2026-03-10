import React from 'react';
import './LoadingSpinner.css';

interface LoadingSpinnerProps {
    size?: 'small' | 'medium' | 'large';
    color?: 'orange' | 'purple' | 'green' | 'yellow';
    text?: string;
    fullScreen?: boolean;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
    size = 'medium',
    color = 'orange',
    text,
    fullScreen = false,
}) => {
    const sizeClass = `spinner-${size}`;
    const colorClass = `spinner-${color}`;

    const spinner = (
        <div className={`loading-spinner-container ${colorClass}`}>
            <div className={`loading-spinner ${sizeClass}`}>
                <div className="spinner-ring ring-1"></div>
                <div className="spinner-ring ring-2"></div>
                <div className="spinner-ring ring-3"></div>
            </div>
            {text && <div className="spinner-text">{text}</div>}
        </div>
    );

    if (fullScreen) {
        return (
            <div className="loading-spinner-fullscreen">
                {spinner}
            </div>
        );
    }

    return spinner;
};
