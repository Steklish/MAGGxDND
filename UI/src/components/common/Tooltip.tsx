import React, { ReactNode, useState, useRef, useEffect, useCallback } from 'react';
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

    const calculatePosition = useCallback(() => {
        if (!triggerRef.current || !contentRef.current) return;

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

        // Clamp to viewport with padding
        const viewportPadding = 8;
        if (top < viewportPadding) top = viewportPadding;
        if (top + contentRect.height > window.innerHeight - viewportPadding) {
            top = window.innerHeight - contentRect.height - viewportPadding;
        }

        if (left < viewportPadding) left = viewportPadding;
        if (left + contentRect.width > window.innerWidth - viewportPadding) {
            left = window.innerWidth - contentRect.width - viewportPadding;
        }

        setTooltipStyle({
            position: 'fixed',
            left: `${left}px`,
            top: `${top}px`,
            zIndex: 9999,
            visibility: 'visible',
            opacity: 1
        });
    }, [position]);

    useEffect(() => {
        if (!isVisible) {
            setTooltipStyle({
                visibility: 'hidden',
                opacity: 0
            });
            return;
        }

        // Calculate position immediately
        calculatePosition();

        // Use requestAnimationFrame for smooth updates
        let animationFrameId: number;
        const updatePosition = () => {
            calculatePosition();
            animationFrameId = requestAnimationFrame(updatePosition);
        };

        // Start continuous updates while visible
        animationFrameId = requestAnimationFrame(updatePosition);

        // Also listen to scroll and resize as backup
        const handleScroll = () => calculatePosition();
        const handleResize = () => calculatePosition();

        window.addEventListener('scroll', handleScroll, true);
        window.addEventListener('resize', handleResize);

        return () => {
            cancelAnimationFrame(animationFrameId);
            window.removeEventListener('scroll', handleScroll, true);
            window.removeEventListener('resize', handleResize);
        };
    }, [isVisible, calculatePosition]);

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
