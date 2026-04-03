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
                        <h3>What is Dungeons & Dragons?</h3>
                        <p>
                            Dungeons & Dragons (D&D) is the world's most popular fantasy tabletop role-playing game.
                            First published in 1974 by Gary Gygax and Dave Arneson, it has entertained millions of
                            players for over 50 years. The current edition (5th Edition, revised in 2024) makes the
                            game more accessible than ever.
                        </p>
                    </section>

                    <section className="fp-section">
                        <h3>How It Works</h3>
                        <p>
                            D&D is a cooperative storytelling game. Players create unique characters — brave warriors,
                            cunning rogues, wise wizards — and embark on imaginary adventures together. One player takes
                            on the role of the Dungeon Master (DM), who narrates the world, controls monsters and NPCs,
                            and guides the story.
                        </p>
                        <div className="fp-highlight">
                            <h4>What You Need:</h4>
                            <ul>
                                <li><strong>Players (1-6):</strong> Each creates and controls a character</li>
                                <li><strong>Dungeon Master:</strong> The storyteller and referee of the game</li>
                                <li><strong>Character Sheets:</strong> Your character's abilities, equipment, and backstory</li>
                                <li><strong>Dice:</strong> Polyhedral dice (d4, d6, d8, d10, d12, d20) — we handle this digitally!</li>
                            </ul>
                        </div>
                    </section>

                    <section className="fp-section">
                        <h3>The Core Mechanic</h3>
                        <p>
                            When you want to do something risky — attack a monster, pick a lock, persuade a guard — you
                            roll a 20-sided die (d20) and add your relevant ability modifier. If the total meets or
                            exceeds the Difficulty Class (DC) set by the DM, you succeed!
                        </p>
                        <div className="fp-highlight">
                            <p><strong>Formula:</strong> d20 roll + Ability Modifier + Proficiency Bonus ≥ DC = Success!</p>
                        </div>
                    </section>

                    <section className="fp-section">
                        <h3>Why Play D&D?</h3>
                        <div className="fp-benefits">
                            <div className="fp-benefit-card">
                                <span className="fp-benefit-icon">🎭</span>
                                <h4>Unlimited Creativity</h4>
                                <p>If you can imagine it, you can try it. No video game can match this freedom.</p>
                            </div>
                            <div className="fp-benefit-card">
                                <span className="fp-benefit-icon">👥</span>
                                <h4>Social Connection</h4>
                                <p>Build lasting friendships through shared adventures and memorable moments.</p>
                            </div>
                            <div className="fp-benefit-card">
                                <span className="fp-benefit-icon">🧠</span>
                                <h4>Problem Solving</h4>
                                <p>Think critically, negotiate, strategize, and adapt to unexpected challenges.</p>
                            </div>
                            <div className="fp-benefit-card">
                                <span className="fp-benefit-icon">⚔️</span>
                                <h4>Epic Adventures</h4>
                                <p>From humble taverns to cosmic horrors — every session is a new story.</p>
                            </div>
                        </div>
                    </section>

                    <section className="fp-section">
                        <h3>Playing with MAGGxDND</h3>
                        <p>
                            Traditional D&D requires a human Dungeon Master. With MAGGxDND, our AI takes on that role,
                            allowing you to play solo or with friends anytime — no scheduling conflicts, no DM burnout.
                            The AI adapts to your choices, creates compelling narratives, and handles all the rules
                            automatically.
                        </p>
                    </section>
                </>
            ),
        },
        'about': {
            title: '🚀 About Project',
            content: (
                <>
                    <section className="fp-section fp-hero-section">
                        <div className="fp-hero-content">
                            <div className="fp-hero-icon">🐉</div>
                            <h3>MAGGxDND - AI-Powered D&D Experience</h3>
                            <p className="fp-hero-description">
                                MAGGxDND is an innovative platform that combines the timeless appeal of Dungeons &
                                Dragons with cutting-edge artificial intelligence. Our mission is to make D&D
                                accessible to everyone while preserving the magic that makes tabletop RPGs special.
                            </p>
                        </div>
                    </section>

                    <section className="fp-section">
                        <h3>✨ Features</h3>
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
                        <h3>🎯 Our Mission</h3>
                        <p>
                            Whether you're a veteran player with decades of experience or curious about D&D
                            for the first time, our AI adapts to your level and creates the perfect adventure
                            for you. We believe everyone should have access to the magic of tabletop RPGs.
                        </p>
                    </section>

                    <section className="fp-section fp-creator-section">
                        <h3>👨‍💻 Created By</h3>
                        <div className="fp-creator-card">
                            <div className="fp-creator-avatar">👤</div>
                            <div className="fp-creator-info">
                                <h4>anton kozlov</h4>
                                <p className="fp-creator-role">Developer & Creator</p>
                                <p className="fp-creator-bio">
                                    Built with passion for D&D and cutting-edge technology. 
                                    This project represents a journey of learning and innovation, 
                                    combining artificial intelligence with the timeless art of storytelling.
                                </p>
                            </div>
                        </div>
                    </section>

                    <section className="fp-section">
                        <h3>🛠 Technology Stack</h3>
                        <div className="fp-tech-stack">
                            <div className="fp-tech-category">
                                <span className="fp-tech-icon">⚛️</span>
                                <strong>Frontend</strong>
                                <p>React, TypeScript, Vite</p>
                            </div>
                            <div className="fp-tech-category">
                                <span className="fp-tech-icon">🐍</span>
                                <strong>Backend</strong>
                                <p>Python, FastAPI</p>
                            </div>
                            <div className="fp-tech-category">
                                <span className="fp-tech-icon">🧠</span>
                                <strong>AI</strong>
                                <p>Google Gemini AI, Custom ML models</p>
                            </div>
                            <div className="fp-tech-category">
                                <span className="fp-tech-icon">💾</span>
                                <strong>Database</strong>
                                <p>SQLite/PostgreSQL</p>
                            </div>
                        </div>
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
                            <p>Yes! MAGGxDND is completely free to play. We believe everyone should have access to the magic of D&D. The AI Dungeon Master is powered by Google Gemini AI — you'll need a free API key from Google AI Studio to unlock full features.</p>
                        </div>

                        <div className="fp-faq-item">
                            <h4>👥 Do I need other players to start?</h4>
                            <p>No! You can play solo with the AI Dungeon Master — perfect for when your group can't meet. You can also invite friends to join your session for a multiplayer experience.</p>
                        </div>

                        <div className="fp-faq-item">
                            <h4>🤖 How does the AI Dungeon Master work?</h4>
                            <p>Our AI uses Google's Gemini language model to understand your actions, create dynamic narratives, control NPCs, and respond to your choices in real-time. It knows D&D 5e rules, generates balanced encounters, and adapts the story based on your decisions. If AI is unavailable, a procedural generation system ensures you can still play.</p>
                        </div>

                        <div className="fp-faq-item">
                            <h4>📱 Can I play on mobile?</h4>
                            <p>Yes! MAGGxDND is fully responsive and works on desktop, tablet, and mobile devices. The interface adapts to your screen size for the best experience anywhere.</p>
                        </div>

                        <div className="fp-faq-item">
                            <h4>💾 Is my progress saved?</h4>
                            <p>Yes! Your characters, sessions, and campaign history are automatically saved to your account. You can pick up right where you left off, even days later.</p>
                        </div>

                        <div className="fp-faq-item">
                            <h4>🌍 Can I play with friends from other countries?</h4>
                            <p>Absolutely! MAGGxDND is a web application — anyone with a browser and internet connection can join your session, regardless of location.</p>
                        </div>

                        <div className="fp-faq-item">
                            <h4>🎲 Do I need physical dice?</h4>
                            <p>No! MAGGxDND includes a built-in dice roller that handles all D&D dice (d4, d6, d8, d10, d12, d20). The AI also rolls behind the screen for hidden checks.</p>
                        </div>

                        <div className="fp-faq-item">
                            <h4>🔒 Is my data secure?</h4>
                            <p>Yes! We use JWT authentication, bcrypt password hashing, and industry-standard security practices. Your personal data is never shared with third parties.</p>
                        </div>

                        <div className="fp-faq-item">
                            <h4>🎭 Do I need to know D&D rules?</h4>
                            <p>Not at all! The AI Dungeon Master guides you through the rules as you play. It's a great way to learn D&D naturally. Experienced players can dive right into complex scenarios.</p>
                        </div>

                        <div className="fp-faq-item">
                            <h4>📖 What edition of D&D does this use?</h4>
                            <p>MAGGxDND is based on D&D 5th Edition (5e) rules, the most popular and accessible edition. The AI handles character creation, combat, skill checks, and spellcasting according to 5e mechanics.</p>
                        </div>

                        <div className="fp-faq-item">
                            <h4>🛠 Can I contribute to the project?</h4>
                            <p>Yes! MAGGxDND is open source. Check out our GitHub repository to report issues, suggest features, or submit pull requests. We welcome contributions of all kinds!</p>
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
                            Whether you're reporting a bug, suggesting a feature, or just want to share
                            your epic adventure story — every message matters to us.
                        </p>
                    </section>

                    <section className="fp-section">
                        <h3>Best Ways to Reach Us</h3>
                        <div className="fp-contact-grid">
                            <div className="fp-contact-card">
                                <span className="fp-contact-icon">🐙</span>
                                <h4>GitHub</h4>
                                <p>Report bugs, request features, or contribute code</p>
                                <p className="fp-contact-note">Best for: Technical issues & contributions</p>
                            </div>
                            <div className="fp-contact-card">
                                <span className="fp-contact-icon">💬</span>
                                <h4>Discord</h4>
                                <p>Join our community for real-time chat and support</p>
                                <p className="fp-contact-note">Best for: Quick questions & finding players</p>
                            </div>
                            <div className="fp-contact-card">
                                <span className="fp-contact-icon">📧</span>
                                <h4>Email</h4>
                                <p>support@maggxdnd.com</p>
                                <p className="fp-contact-note">Best for: Business inquiries & partnerships</p>
                            </div>
                            <div className="fp-contact-card">
                                <span className="fp-contact-icon">🐦</span>
                                <h4>Social Media</h4>
                                <p>Follow @MAGGxDND for updates</p>
                                <p className="fp-contact-note">Best for: News & community highlights</p>
                            </div>
                        </div>
                    </section>

                    <section className="fp-section">
                        <h3>Before You Contact Us</h3>
                        <ul className="fp-tips-list">
                            <li><strong>Bug Reports:</strong> Check our GitHub Issues first — someone may have already reported it</li>
                            <li><strong>Game Questions:</strong> Our FAQ section covers most common questions</li>
                            <li><strong>Feature Requests:</strong> We track all suggestions on GitHub — add yours there!</li>
                            <li><strong>Community Help:</strong> Our Discord community is often faster than official support</li>
                        </ul>
                    </section>

                    <section className="fp-section">
                        <h3>Community Guidelines</h3>
                        <p>
                            We welcome players of all experience levels and backgrounds. Be respectful,
                            help each other out, and most importantly — have fun! Our community thrives
                            on creativity and collaboration.
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
