import React, { ReactNode, useState, useRef, useEffect } from 'react';
import ReactDOM from 'react-dom';
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
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
        return () => setMounted(false);
    }, []);

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
                    if (left + contentRect.width > window.innerWidth) {
                        left = triggerRect.left - contentRect.width - padding;
                    }
                    break;
                case 'left':
                    left = triggerRect.left - contentRect.width - padding;
                    top = triggerRect.top + (triggerRect.height / 2) - (contentRect.height / 2);
                    if (left < 0) {
                        left = triggerRect.right + padding;
                    }
                    break;
                case 'top':
                    left = triggerRect.left + (triggerRect.width / 2) - (contentRect.width / 2);
                    top = triggerRect.top - contentRect.height - padding;
                    if (top < 0) {
                        top = triggerRect.bottom + padding;
                    }
                    break;
                case 'bottom':
                    left = triggerRect.left + (triggerRect.width / 2) - (contentRect.width / 2);
                    top = triggerRect.bottom + padding;
                    if (top + contentRect.height > window.innerHeight) {
                        top = triggerRect.top - contentRect.height - padding;
                    }
                    break;
            }

            if (top < padding) top = padding;
            if (top + contentRect.height > window.innerHeight - padding) {
                top = window.innerHeight - contentRect.height - padding;
            }

            if (left < padding) left = padding;
            if (left + contentRect.width > window.innerWidth - padding) {
                left = window.innerWidth - contentRect.width - padding;
            }

            setTooltipStyle({
                position: 'fixed',
                left: `${left}px`,
                top: `${top}px`,
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

    const tooltipElement = (
        <div 
            className={`tooltip tooltip-${position}`}
            style={tooltipStyle}
            ref={contentRef}
        >
            {content}
        </div>
    );

    return (
        <div 
            className={`tooltip-container ${className}`}
            onMouseEnter={() => setIsVisible(true)}
            onMouseLeave={() => setIsVisible(false)}
        >
            <div ref={triggerRef} className="tooltip-trigger">
                {children}
            </div>
            {mounted && isVisible && ReactDOM.createPortal(tooltipElement, document.body)}
        </div>
    );
};
