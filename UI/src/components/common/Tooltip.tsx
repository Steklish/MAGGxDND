import React, { ReactNode, useState, useRef, useEffect } from 'react';
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
    const [isVisible, setIsVisible] = useState(false);
    const [tooltipStyle, setTooltipStyle] = useState<React.CSSProperties>({});
    const triggerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (isVisible && triggerRef.current) {
            const triggerRect = triggerRef.current.getBoundingClientRect();
            const tooltipWidth = 320;
            const tooltipHeight = 280;
            const padding = 8;

            let left = 0;
            let top = 0;

            switch (position) {
                case 'right':
                    left = triggerRect.right + padding;
                    top = triggerRect.top + (triggerRect.height / 2) - (tooltipHeight / 2);
                    // Adjust if tooltip goes off right edge
                    if (left + tooltipWidth > window.innerWidth) {
                        left = triggerRect.left - tooltipWidth - padding;
                    }
                    break;
                case 'left':
                    left = triggerRect.left - tooltipWidth - padding;
                    top = triggerRect.top + (triggerRect.height / 2) - (tooltipHeight / 2);
                    // Adjust if tooltip goes off left edge
                    if (left < 0) {
                        left = triggerRect.right + padding;
                    }
                    break;
                case 'top':
                    left = triggerRect.left + (triggerRect.width / 2) - (tooltipWidth / 2);
                    top = triggerRect.top - tooltipHeight - padding;
                    // Adjust if tooltip goes off top edge
                    if (top < 0) {
                        top = triggerRect.bottom + padding;
                    }
                    break;
                case 'bottom':
                    left = triggerRect.left + (triggerRect.width / 2) - (tooltipWidth / 2);
                    top = triggerRect.bottom + padding;
                    // Adjust if tooltip goes off bottom edge
                    if (top + tooltipHeight > window.innerHeight) {
                        top = triggerRect.top - tooltipHeight - padding;
                    }
                    break;
            }

            // Ensure tooltip stays within viewport vertically
            if (top < 0) top = padding;
            if (top + tooltipHeight > window.innerHeight) {
                top = window.innerHeight - tooltipHeight - padding;
            }

            // Ensure tooltip stays within viewport horizontally
            if (left < 0) left = padding;
            if (left + tooltipWidth > window.innerWidth) {
                left = window.innerWidth - tooltipWidth - padding;
            }

            setTooltipStyle({
                position: 'fixed',
                left: `${left}px`,
                top: `${top}px`,
                width: `${tooltipWidth}px`,
                maxHeight: `${tooltipHeight}px`,
                zIndex: 9999,
                visibility: 'visible',
                opacity: 1
            });
        } else {
            setTooltipStyle({
                visibility: 'hidden',
                opacity: 0
            });
        }
    }, [isVisible, position]);

    return (
        <div 
            className={`tooltip-container ${className}`}
            onMouseEnter={() => setIsVisible(true)}
            onMouseLeave={() => setIsVisible(false)}
        >
            <div ref={triggerRef} className="tooltip-trigger">
                {children}
            </div>
            <div 
                className={`tooltip tooltip-${position}`}
                style={tooltipStyle}
            >
                {content}
            </div>
        </div>
    );
};
