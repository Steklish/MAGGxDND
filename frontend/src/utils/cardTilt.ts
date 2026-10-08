import React from 'react';

/**
 * Updates CSS custom properties --mouse-x, --mouse-y, --mouse-x-norm, --mouse-y-norm
 * for Reveal Highlight candlelight and 3D geometric transformations.
 */
export const handleTiltAndHighlight = (e: React.MouseEvent<HTMLElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const normX = Math.max(0, Math.min(1, x / rect.width));
    const normY = Math.max(0, Math.min(1, y / rect.height));

    e.currentTarget.style.setProperty('--mouse-x', `${x}px`);
    e.currentTarget.style.setProperty('--mouse-y', `${y}px`);
    e.currentTarget.style.setProperty('--mouse-x-norm', `${normX}`);
    e.currentTarget.style.setProperty('--mouse-y-norm', `${normY}`);
};

export const handleTiltReset = (e: React.MouseEvent<HTMLElement>) => {
    e.currentTarget.style.setProperty('--mouse-x', '-999px');
    e.currentTarget.style.setProperty('--mouse-y', '-999px');
    e.currentTarget.style.setProperty('--mouse-x-norm', '0.5');
    e.currentTarget.style.setProperty('--mouse-y-norm', '0.5');
};
