import React, { ReactNode } from 'react';
import './Tooltip.css';

interface TooltipProps {
    content: ReactNode;
    children: ReactNode;
    position?: 'top' | 'bottom' | 'left' | 'right';
    className?: string;
}

export const Tooltip: React.FC<TooltipProps> = ({ 
    content, 
    children, 
    position = 'right',
    className = '' 
}) => {
    return (
        <div className={`tooltip-container ${className}`}>
            {children}
            <div className={`tooltip ${position}`}>
                {content}
            </div>
        </div>
    );
};
