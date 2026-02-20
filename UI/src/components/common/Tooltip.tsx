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
    const contentRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (isVisible && triggerRef.current && contentRef.current) {
            const triggerRect = triggerRef.current.getBoundingClientRect();
            const contentRect = contentRef.current.getBoundingClientRect();
            const padding = 8;

            let left = 0;
            let top = 0;

            switch (position) {
                case 'right':
                    left = triggerRect.right + padding;
                    top = triggerRect.top + (triggerRect.height / 2) - (contentRect.height / 2);
                    // Adjust if tooltip goes off right edge
                    if (left + contentRect.width > window.innerWidth) {
                        left = triggerRect.left - contentRect.width - padding;
                    }
                    break;
                case 'left':
                    left = triggerRect.left - contentRect.width - padding;
                    top = triggerRect.top + (triggerRect.height / 2) - (contentRect.height / 2);
                    // Adjust if tooltip goes off left edge
                    if (left < 0) {
                        left = triggerRect.right + padding;
                    }
                    break;
                case 'top':
                    left = triggerRect.left + (triggerRect.width / 2) - (contentRect.width / 2);
                    top = triggerRect.top - contentRect.height - padding;
                    // Adjust if tooltip goes off top edge
                    if (top < 0) {
                        top = triggerRect.bottom + padding;
                    }
                    break;
                case 'bottom':
                    left = triggerRect.left + (triggerRect.width / 2) - (contentRect.width / 2);
                    top = triggerRect.bottom + padding;
                    // Adjust if tooltip goes off bottom edge
                    if (top + contentRect.height > window.innerHeight) {
                        top = triggerRect.top - contentRect.height - padding;
                    }
                    break;
            }

            // Ensure tooltip stays within viewport vertically
            if (top < padding) top = padding;
            if (top + contentRect.height > window.innerHeight - padding) {
                top = window.innerHeight - contentRect.height - padding;
            }

            // Ensure tooltip stays within viewport horizontally
            if (left < padding) left = padding;
            if (left + contentRect.width > window.innerWidth - padding) {
                left = window.innerWidth - contentRect.width - padding;
            }

            setTooltipStyle({
                position: 'fixed',
                left: `${left}px`,
                top: `${top}px`,
                width: 'auto',
                maxWidth: `${Math.min(400, window.innerWidth - (padding * 2))}px`,
                maxHeight: 'none',
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
                ref={contentRef}
            >
                {content}
            </div>
        </div>
    );
};
