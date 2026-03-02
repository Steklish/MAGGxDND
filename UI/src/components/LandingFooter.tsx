import React from 'react';
import './LandingFooter.css';

export const LandingFooter: React.FC = () => {
    const currentYear = new Date().getFullYear();

    return (
        <footer className="landing-footer">
            <div className="footer-content">
                <div className="footer-main">
                    <div className="footer-brand">
                        <div className="footer-logo">
                            <span className="logo-icon">🐉</span>
                            <span className="logo-text">MAGG<span className="logo-accent">xDND</span></span>
                        </div>
                        <p className="footer-brand-description">
                            AI-powered Dungeons & Dragons experience. 
                            Your adventure, reimagined.
                        </p>
                        <div className="footer-social">
                            <a href="#" className="social-link" aria-label="Discord">
                                <span>🎮</span>
                            </a>
                            <a href="#" className="social-link" aria-label="Twitter">
                                <span>🐦</span>
                            </a>
                            <a href="#" className="social-link" aria-label="GitHub">
                                <span>💻</span>
                            </a>
                            <a href="#" className="social-link" aria-label="Reddit">
                                <span>📱</span>
                            </a>
                        </div>
                    </div>

                    <div className="footer-links">
                        <div className="footer-column">
                            <h4>Game</h4>
                            <ul>
                                <li><a href="#">Features</a></li>
                                <li><a href="#">How It Works</a></li>
                                <li><a href="#">Pricing</a></li>
                                <li><a href="#">FAQ</a></li>
                            </ul>
                        </div>
                        <div className="footer-column">
                            <h4>Community</h4>
                            <ul>
                                <li><a href="#">Discord</a></li>
                                <li><a href="#">Forum</a></li>
                                <li><a href="#">Events</a></li>
                                <li><a href="#">Blog</a></li>
                            </ul>
                        </div>
                        <div className="footer-column">
                            <h4>Resources</h4>
                            <ul>
                                <li><a href="#">D&D Rules</a></li>
                                <li><a href="#">Character Builder</a></li>
                                <li><a href="#">Tutorials</a></li>
                                <li><a href="#">API Docs</a></li>
                            </ul>
                        </div>
                        <div className="footer-column">
                            <h4>Company</h4>
                            <ul>
                                <li><a href="#">About Us</a></li>
                                <li><a href="#">Careers</a></li>
                                <li><a href="#">Press Kit</a></li>
                                <li><a href="#">Contact</a></li>
                            </ul>
                        </div>
                    </div>
                </div>

                <div className="footer-bottom">
                    <div className="footer-legal">
                        <p>© {currentYear} MAGGxDND. All rights reserved.</p>
                        <div className="footer-legal-links">
                            <a href="#">Privacy Policy</a>
                            <a href="#">Terms of Service</a>
                            <a href="#">Cookie Policy</a>
                        </div>
                    </div>
                    <div className="footer-dnd-notice">
                        <p>
                            MAGGxDND is a fan-created tool and is not affiliated with or endorsed by 
                            Wizards of the Coast. Dungeons & Dragons and D&D are trademarks of 
                            Wizards of the Coast LLC.
                        </p>
                    </div>
                </div>
            </div>
        </footer>
    );
};
