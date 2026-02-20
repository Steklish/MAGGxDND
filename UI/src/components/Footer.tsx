import React, { useState, useEffect, useRef } from 'react';
import './Footer.css';

export const Footer: React.FC = () => {
    const [isVisible, setIsVisible] = useState(false);
    const [dragOffset, setDragOffset] = useState(0);
    const [isDragging, setIsDragging] = useState(false);
    const startY = useRef(0);

    useEffect(() => {
        const handleTouchStart = (e: TouchEvent) => {
            startY.current = e.touches[0].clientY;
            setIsDragging(true);
        };

        const handleTouchMove = (e: TouchEvent) => {
            const currentY = e.touches[0].clientY;
            const delta = currentY - startY.current;

            // Only trigger on downward drag
            if (delta > 0) {
                setDragOffset(Math.min(delta, 300));
            }
        };

        const handleTouchEnd = () => {
            // Show footer if dragged enough
            if (dragOffset > 100) {
                setIsVisible(true);
            } else {
                setIsVisible(false);
            }
            setDragOffset(0);
            setIsDragging(false);
        };

        const handleMouseDown = (e: MouseEvent) => {
            startY.current = e.clientY;
            setIsDragging(true);
        };

        const handleMouseMove = (e: MouseEvent) => {
            const delta = e.clientY - startY.current;
            if (delta > 0) {
                setDragOffset(Math.min(delta, 300));
            }
        };

        const handleMouseUp = () => {
            if (dragOffset > 100) {
                setIsVisible(true);
            } else {
                setIsVisible(false);
            }
            setDragOffset(0);
            setIsDragging(false);
        };

        // Also allow clicking anywhere to toggle when footer is visible
        const handleClick = (e: MouseEvent) => {
            const target = e.target as HTMLElement;
            // Don't close if clicking inside footer
            if (target.closest('.footer')) return;

            if (isVisible) {
                setIsVisible(false);
            }
        };

        document.addEventListener('touchstart', handleTouchStart);
        document.addEventListener('touchmove', handleTouchMove);
        document.addEventListener('touchend', handleTouchEnd);
        document.addEventListener('mousedown', handleMouseDown);
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
        document.addEventListener('click', handleClick);

        return () => {
            document.removeEventListener('touchstart', handleTouchStart);
            document.removeEventListener('touchmove', handleTouchMove);
            document.removeEventListener('touchend', handleTouchEnd);
            document.removeEventListener('mousedown', handleMouseDown);
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
            document.removeEventListener('click', handleClick);
        };
    }, [dragOffset, isVisible]);

    return (
        <>
            {/* Drag overlay - shows during drag */}
            <div className={`footer-drag-overlay ${isDragging ? 'active' : ''}`} />

            <footer className={`footer ${isVisible ? 'visible' : ''}`} style={{
                transform: isVisible ? 'translateY(0)' : `translateY(calc(100% - ${Math.max(0, dragOffset - 50)}px))`
            }}>
            <div className="footer-content">
                {/* Left Section - Game Rules */}
                <div className="footer-section">
                    <h4 className="footer-title">📚 D&D Rules</h4>
                    <ul className="footer-links">
                        <li>
                            <a href="https://dnd.wizards.com/resources/rules" target="_blank" rel="noopener noreferrer">
                                Latest D&D Rules
                            </a>
                        </li>
                        <li>
                            <a href="https://dnd.wizards.com/articles/features/basicrules" target="_blank" rel="noopener noreferrer">
                                Basic Rules
                            </a>
                        </li>
                        <li>
                            <a href="https://www.dndbeyond.com/sources/phb" target="_blank" rel="noopener noreferrer">
                                Player's Handbook
                            </a>
                        </li>
                        <li>
                            <a href="https://www.dndbeyond.com/sources/dmg" target="_blank" rel="noopener noreferrer">
                                Dungeon Master's Guide
                            </a>
                        </li>
                        <li>
                            <a href="https://www.dndbeyond.com/sources/mmotm" target="_blank" rel="noopener noreferrer">
                                Monster Manual
                            </a>
                        </li>
                    </ul>
                </div>

                {/* Center Section - Resources */}
                <div className="footer-section">
                    <h4 className="footer-title">🎲 Resources</h4>
                    <ul className="footer-links">
                        <li>
                            <a href="https://www.dndbeyond.com/characters" target="_blank" rel="noopener noreferrer">
                                Character Sheet
                            </a>
                        </li>
                        <li>
                            <a href="https://www.dndbeyond.com/spells" target="_blank" rel="noopener noreferrer">
                                Spells
                            </a>
                        </li>
                        <li>
                            <a href="https://www.dndbeyond.com/items" target="_blank" rel="noopener noreferrer">
                                Items
                            </a>
                        </li>
                        <li>
                            <a href="https://www.dndbeyond.com/feats" target="_blank" rel="noopener noreferrer">
                                Feats
                            </a>
                        </li>
                        <li>
                            <a href="https://www.dndbeyond.com/backgrounds" target="_blank" rel="noopener noreferrer">
                                Backgrounds
                            </a>
                        </li>
                    </ul>
                </div>

                {/* Right Section - Project */}
                <div className="footer-section">
                    <h4 className="footer-title">🐉 About</h4>
                    <ul className="footer-links">
                        <li>
                            <a href="#what-is-dnd">What is D&D?</a>
                        </li>
                        <li>
                            <a href="#about-project">About Project</a>
                        </li>
                        <li>
                            <a href="#how-to-play">How to Play</a>
                        </li>
                        <li>
                            <a href="#faq">FAQ</a>
                        </li>
                        <li>
                            <a href="#contact">Contact</a>
                        </li>
                    </ul>
                </div>
            </div>

            <div className="footer-bottom">
                <p>MAGGxDND © 2026 — AI-powered D&D Game Master</p>
                <p className="footer-disclaimer">
                    D&D and Wizards of the Coast are trademarks of Wizards of the Coast LLC.
                </p>
            </div>
        </footer>
    );
};
