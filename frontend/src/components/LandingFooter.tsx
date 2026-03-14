import React, { useState } from 'react';
import { FooterPages } from './FooterPages';
import './LandingFooter.css';

export const LandingFooter: React.FC = () => {
    const [currentPage, setCurrentPage] = useState<'what-is-dnd' | 'about' | 'how-to-play' | 'faq' | 'contact' | null>(null);
    const currentYear = new Date().getFullYear();

    const handlePageClick = (page: 'what-is-dnd' | 'about' | 'how-to-play' | 'faq' | 'contact') => {
        setCurrentPage(page);
    };

    return (
        <>
            <footer className="landing-footer">
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
                                <a href="https://www.dndbeyond.com/sources/dnd/mm-2024" target="_blank" rel="noopener noreferrer">
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
                                <button className="footer-link-btn" onClick={() => handlePageClick('what-is-dnd')}>
                                    What is D&D?
                                </button>
                            </li>
                            <li>
                                <button className="footer-link-btn" onClick={() => handlePageClick('about')}>
                                    About Project
                                </button>
                            </li>
                            <li>
                                <button className="footer-link-btn" onClick={() => handlePageClick('how-to-play')}>
                                    How to Play
                                </button>
                            </li>
                            <li>
                                <button className="footer-link-btn" onClick={() => handlePageClick('faq')}>
                                    FAQ
                                </button>
                            </li>
                            <li>
                                <button className="footer-link-btn" onClick={() => handlePageClick('contact')}>
                                    Contact
                                </button>
                            </li>
                        </ul>
                    </div>
                </div>

                <div className="footer-bottom">
                    <p>MAGGxDND © {currentYear} — AI-powered D&D Game Master</p>
                    <p className="footer-disclaimer">
                        D&D and Wizards of the Coast are trademarks of Wizards of the Coast LLC.
                    </p>
                </div>
            </footer>

            {/* Footer Pages Modal */}
            {currentPage && (
                <FooterPages
                    page={currentPage}
                    onClose={() => setCurrentPage(null)}
                />
            )}
        </>
    );
};
