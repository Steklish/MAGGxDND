import React from 'react';
import './FooterPages.css';

interface FooterPagesProps {
    page: 'what-is-dnd' | 'about' | 'how-to-play' | 'faq' | 'contact';
    onClose: () => void;
}

export const FooterPages: React.FC<FooterPagesProps> = ({ page, onClose }) => {
    const pages = {
        'what-is-dnd': {
            title: '🐉 What is D&D?',
            content: (
                <>
                    <section className="fp-section">
                        <h3>Introduction to Dungeons & Dragons</h3>
                        <p>
                            Dungeons & Dragons (D&D) is a fantasy tabletop role-playing game (RPG) originally 
                            designed by Gary Gygax and Dave Arneson. It was first published in 1974 by Tactical 
                            Studies Rules, Inc. (TSR) and has been published by Wizards of the Coast since 1997.
                        </p>
                    </section>

                    <section className="fp-section">
                        <h3>How It Works</h3>
                        <p>
                            In D&D, players create fictional characters and embark on imaginary adventures within 
                            a fantasy setting. A special player, the Dungeon Master (DM), serves as the game's 
                            referee and storyteller, maintaining the setting in which adventures occur and playing 
                            the role of the inhabitants.
                        </p>
                        <div className="fp-highlight">
                            <h4>Key Components:</h4>
                            <ul>
                                <li><strong>Players:</strong> Create and control player characters (PCs)</li>
                                <li><strong>Dungeon Master:</strong> Narrates the story and controls NPCs</li>
                                <li><strong>Character Sheets:</strong> Track character abilities and progress</li>
                                <li><strong>Dice:</strong> Primarily 20-sided dice (d20) for resolving actions</li>
                            </ul>
                        </div>
                    </section>

                    <section className="fp-section">
                        <h3>The Game Flow</h3>
                        <p>
                            The players describe what their characters want to do, and the DM describes what 
                            happens in the game world. When the outcome of an action is uncertain, the game's 
                            rules determine the success or failure, often involving rolling a die and comparing 
                            the result to a target number.
                        </p>
                    </section>

                    <section className="fp-section">
                        <h3>Why Play D&D?</h3>
                        <div className="fp-benefits">
                            <div className="fp-benefit-card">
                                <span className="fp-benefit-icon">🎭</span>
                                <h4>Storytelling</h4>
                                <p>Create epic narratives and memorable characters</p>
                            </div>
                            <div className="fp-benefit-card">
                                <span className="fp-benefit-icon">🧠</span>
                                <h4>Creativity</h4>
                                <p>Solve problems in innovative ways</p>
                            </div>
                            <div className="fp-benefit-card">
                                <span className="fp-benefit-icon">👥</span>
                                <h4>Social</h4>
                                <p>Build friendships and collaborate with others</p>
                            </div>
                            <div className="fp-benefit-card">
                                <span className="fp-benefit-icon">⚔️</span>
                                <h4>Adventure</h4>
                                <p>Experience epic quests and heroic moments</p>
                            </div>
                        </div>
                    </section>
                </>
            ),
        },
        'about': {
            title: '🚀 About Project',
            content: (
                <>
                    <section className="fp-section">
                        <h3>MAGGxDND - AI-Powered D&D Experience</h3>
                        <p>
                            MAGGxDND is an innovative platform that combines the timeless appeal of Dungeons & 
                            Dragons with cutting-edge artificial intelligence. Our mission is to make D&D 
                            accessible to everyone while preserving the magic that makes tabletop RPGs special.
                        </p>
                    </section>

                    <section className="fp-section">
                        <h3>Features</h3>
                        <div className="fp-features-grid">
                            <div className="fp-feature-card">
                                <span className="fp-feature-icon">🤖</span>
                                <h4>AI Dungeon Master</h4>
                                <p>Advanced AI that adapts to your playstyle and creates dynamic narratives</p>
                            </div>
                            <div className="fp-feature-card">
                                <span className="fp-feature-icon">🎲</span>
                                <h4>Automated Gameplay</h4>
                                <p>Streamlined character creation, session management, and rule lookup</p>
                            </div>
                            <div className="fp-feature-card">
                                <span className="fp-feature-icon">🌐</span>
                                <h4>Online Multiplayer</h4>
                                <p>Play with friends from anywhere in the world</p>
                            </div>
                            <div className="fp-feature-card">
                                <span className="fp-feature-icon">📊</span>
                                <h4>Progress Tracking</h4>
                                <p>Track your adventures, characters, and campaign history</p>
                            </div>
                        </div>
                    </section>

                    <section className="fp-section">
                        <h3>Our Mission</h3>
                        <p>
                            Whether you're a veteran player with decades of experience or curious about D&D 
                            for the first time, our AI adapts to your level and creates the perfect adventure 
                            for you. We believe everyone should have access to the magic of tabletop RPGs.
                        </p>
                    </section>

                    <section className="fp-section">
                        <h3>Technology Stack</h3>
                        <ul className="fp-tech-list">
                            <li><strong>Frontend:</strong> React, TypeScript, Vite</li>
                            <li><strong>Backend:</strong> Python, FastAPI</li>
                            <li><strong>AI:</strong> Google Gemini AI, Custom ML models</li>
                            <li><strong>Database:</strong> SQLite/PostgreSQL</li>
                        </ul>
                    </section>
                </>
            ),
        },
        'how-to-play': {
            title: '🎮 How to Play',
            content: (
                <>
                    <section className="fp-section">
                        <h3>Getting Started with MAGGxDND</h3>
                        <div className="fp-steps">
                            <div className="fp-step">
                                <span className="fp-step-number">1</span>
                                <div className="fp-step-content">
                                    <h4>Create Your Account</h4>
                                    <p>Sign up using email, Google, or Discord. You can also try as a guest!</p>
                                </div>
                            </div>
                            <div className="fp-step">
                                <span className="fp-step-number">2</span>
                                <div className="fp-step-content">
                                    <h4>Create Your Character</h4>
                                    <p>Use our character builder or let AI create one for you. Choose your race, class, background, and abilities.</p>
                                </div>
                            </div>
                            <div className="fp-step">
                                <span className="fp-step-number">3</span>
                                <div className="fp-step-content">
                                    <h4>Join or Create a Session</h4>
                                    <p>Browse available sessions or create your own. Set the tone, difficulty, and adventure type.</p>
                                </div>
                            </div>
                            <div className="fp-step">
                                <span className="fp-step-number">4</span>
                                <div className="fp-step-content">
                                    <h4>Start Your Adventure</h4>
                                    <p>Enter your preferences, choose your character, and let the AI Dungeon Master guide your story!</p>
                                </div>
                            </div>
                        </div>
                    </section>

                    <section className="fp-section">
                        <h3>Basic Gameplay</h3>
                        <div className="fp-gameplay-info">
                            <h4>During Your Turn:</h4>
                            <ol>
                                <li><strong>Describe Your Action:</strong> Tell the DM what you want to do</li>
                                <li><strong>Roll Dice:</strong> If needed, roll a d20 to determine success</li>
                                <li><strong>Resolve:</strong> The DM describes the outcome</li>
                                <li><strong>Continue:</strong> Play passes to the next player</li>
                            </ol>
                        </div>
                    </section>

                    <section className="fp-section">
                        <h3>Tips for Beginners</h3>
                        <ul className="fp-tips-list">
                            <li>Don't worry about knowing all the rules - the AI DM will guide you</li>
                            <li>Focus on having fun and telling a great story</li>
                            <li>Work together with your fellow players</li>
                            <li>Be creative with your character's actions</li>
                            <li>Remember: there are no wrong choices, only interesting consequences!</li>
                        </ul>
                    </section>
                </>
            ),
        },
        'faq': {
            title: '❓ FAQ',
            content: (
                <>
                    <section className="fp-section">
                        <h3>Frequently Asked Questions</h3>
                        
                        <div className="fp-faq-item">
                            <h4>🎯 Is MAGGxDND free to use?</h4>
                            <p>Yes! MAGGxDND is completely free. We believe everyone should have access to D&D.</p>
                        </div>

                        <div className="fp-faq-item">
                            <h4>👥 Do I need other players to start?</h4>
                            <p>No! You can play solo with the AI Dungeon Master, or invite friends to join your session.</p>
                        </div>

                        <div className="fp-faq-item">
                            <h4>🤖 How does the AI Dungeon Master work?</h4>
                            <p>Our AI uses advanced language models to understand your actions, create narratives, and respond dynamically to your choices.</p>
                        </div>

                        <div className="fp-faq-item">
                            <h4>📱 Can I play on mobile?</h4>
                            <p>Yes! MAGGxDND is fully responsive and works on desktop, tablet, and mobile devices.</p>
                        </div>

                        <div className="fp-faq-item">
                            <h4>💾 Is my progress saved?</h4>
                            <p>Yes! Your characters, sessions, and campaign history are automatically saved to your account.</p>
                        </div>

                        <div className="fp-faq-item">
                            <h4>🌍 Can I play with friends from other countries?</h4>
                            <p>Absolutely! MAGGxDND supports players from around the world.</p>
                        </div>

                        <div className="fp-faq-item">
                            <h4>🎲 Do I need physical dice?</h4>
                            <p>No! MAGGxDND includes a built-in dice roller. But you can use physical dice if you prefer!</p>
                        </div>

                        <div className="fp-faq-item">
                            <h4>🔒 Is my data secure?</h4>
                            <p>Yes! We use industry-standard security measures to protect your account and data.</p>
                        </div>
                    </section>
                </>
            ),
        },
        'contact': {
            title: '📧 Contact Us',
            content: (
                <>
                    <section className="fp-section">
                        <h3>Get In Touch</h3>
                        <p>
                            Have questions, suggestions, or feedback? We'd love to hear from you!
                        </p>
                    </section>

                    <section className="fp-section">
                        <h3>Contact Methods</h3>
                        <div className="fp-contact-grid">
                            <div className="fp-contact-card">
                                <span className="fp-contact-icon">📧</span>
                                <h4>Email</h4>
                                <p>support@maggxdnd.com</p>
                                <p className="fp-contact-note">Response time: 24-48 hours</p>
                            </div>
                            <div className="fp-contact-card">
                                <span className="fp-contact-icon">💬</span>
                                <h4>Discord</h4>
                                <p>Join our community server</p>
                                <p className="fp-contact-note">Real-time support & discussion</p>
                            </div>
                            <div className="fp-contact-card">
                                <span className="fp-contact-icon">🐦</span>
                                <h4>Twitter</h4>
                                <p>@MAGGxDND</p>
                                <p className="fp-contact-note">Updates & announcements</p>
                            </div>
                            <div className="fp-contact-card">
                                <span className="fp-contact-icon">📋</span>
                                <h4>GitHub</h4>
                                <p>Report issues & contribute</p>
                                <p className="fp-contact-note">Open source project</p>
                            </div>
                        </div>
                    </section>

                    <section className="fp-section">
                        <h3>Support</h3>
                        <p>
                            For technical support, bug reports, or feature requests, please visit our 
                            GitHub repository or join our Discord community.
                        </p>
                    </section>

                    <section className="fp-section">
                        <h3>Community</h3>
                        <p>
                            Join our growing community of D&D enthusiasts! Share your stories, 
                            get help with rules, and find other players to game with.
                        </p>
                    </section>
                </>
            ),
        },
    };

    const currentPage = pages[page];

    return (
        <div className="footer-page-overlay" onClick={onClose}>
            <div className="footer-page-modal" onClick={(e) => e.stopPropagation()}>
                <div className="fp-header">
                    <h2>{currentPage.title}</h2>
                    <button className="fp-close" onClick={onClose}>✕</button>
                </div>
                
                <div className="fp-content">
                    {currentPage.content}
                </div>
            </div>
        </div>
    );
};
