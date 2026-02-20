import React, { useState, useEffect } from 'react';
import './Footer.css';

export const Footer: React.FC = () => {
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        const handleScroll = () => {
            const scrollTop = window.scrollY || document.documentElement.scrollTop;
            const scrollHeight = document.documentElement.scrollHeight;
            const clientHeight = window.innerHeight || document.documentElement.clientHeight;

            // Show footer when scrolled to bottom (with 100px threshold)
            const isAtBottom = scrollTop + clientHeight >= scrollHeight - 100;
            setIsVisible(isAtBottom);
        };

        window.addEventListener('scroll', handleScroll);
        handleScroll(); // Check initial state

        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    return (
        <footer className={`footer ${isVisible ? 'visible' : ''}`}>
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
