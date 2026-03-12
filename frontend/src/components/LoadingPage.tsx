import React, { useState, useEffect } from 'react';
import './LoadingPage.css';

interface LoadingPageProps {
    message?: string;
    showDice?: boolean;
}

export const LoadingPage: React.FC<LoadingPageProps> = ({ 
    message = 'Загрузка...', 
    showDice = true 
}) => {
    const [diceRoll, setDiceRoll] = useState<number>(20);
    const [isRolling, setIsRolling] = useState(true);
    const [rollHistory, setRollHistory] = useState<number[]>([]);

    useEffect(() => {
        if (showDice && isRolling) {
            // Animate dice rolls
            const rollInterval = setInterval(() => {
                const roll = Math.floor(Math.random() * 20) + 1;
                setDiceRoll(roll);
                setRollHistory(prev => [...prev.slice(-4), roll]);
            }, 150);

            // Stop rolling after 2 seconds
            const stopTimeout = setTimeout(() => {
                setIsRolling(false);
                clearInterval(rollInterval);
                // Final roll - make it dramatic
                setDiceRoll(20); // Critical hit!
                setRollHistory(prev => [...prev.slice(-4), 20]);
            }, 2000);

            return () => {
                clearInterval(rollInterval);
                clearTimeout(stopTimeout);
            };
        }
    }, [showDice, isRolling]);

    return (
        <div className="loading-page">
            <div className="loading-background">
                <div className="bg-particles">
                    {[...Array(20)].map((_, i) => (
                        <div 
                            key={i} 
                            className="particle"
                            style={{
                                left: `${Math.random() * 100}%`,
                                top: `${Math.random() * 100}%`,
                                animationDelay: `${Math.random() * 3}s`,
                                animationDuration: `${3 + Math.random() * 2}s`
                            }}
                        />
                    ))}
                </div>
            </div>

            <div className="loading-content">
                {showDice && (
                    <div className="dice-animation">
                        <div className="dice-container">
                            {/* Main D20 */}
                            <div className={`d20-dice ${isRolling ? 'rolling' : 'landed'}`}>
                                <svg viewBox="0 0 100 100" className="d20-svg">
                                    <polygon 
                                        points="50,5 95,27.5 95,72.5 50,95 5,72.5 5,27.5"
                                        className="d20-face"
                                    />
                                    <text 
                                        x="50" 
                                        y="60" 
                                        textAnchor="middle"
                                        className="d20-number"
                                    >
                                        {diceRoll}
                                    </text>
                                </svg>
                            </div>

                            {/* Rolling effect */}
                            {isRolling && (
                                <div className="roll-effect">
                                    {[...Array(6)].map((_, i) => (
                                        <div 
                                            key={i}
                                            className="roll-number"
                                            style={{
                                                transform: `rotate(${i * 60}deg) translateY(-60px)`,
                                                opacity: 0.3 + Math.random() * 0.7
                                            }}
                                        >
                                            {Math.floor(Math.random() * 20) + 1}
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* Roll history */}
                            <div className="roll-history">
                                {rollHistory.map((roll, index) => (
                                    <div 
                                        key={index}
                                        className={`history-die ${roll === 20 ? 'crit-success' : roll === 1 ? 'crit-fail' : ''}`}
                                        style={{
                                            opacity: (index + 1) / rollHistory.length
                                        }}
                                    >
                                        {roll}
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Roll message */}
                        <div className="roll-message">
                            {isRolling ? (
                                <span className="rolling-text">Бросок кубика...</span>
                            ) : diceRoll === 20 ? (
                                <span className="crit-success-text">🎉 Критический успех! 🎉</span>
                            ) : diceRoll === 1 ? (
                                <span className="crit-fail-text">💀 Критический провал! 💀</span>
                            ) : diceRoll >= 15 ? (
                                <span className="success-text">✨ Успех! ✨</span>
                            ) : diceRoll >= 10 ? (
                                <span className="neutral-text">👍 Неплохо</span>
                            ) : (
                                <span className="fail-text">😅 Неудача</span>
                            )}
                        </div>
                    </div>
                )}

                {/* Loading message */}
                <div className="loading-message">
                    <h2>{message}</h2>
                    <div className="loading-dots">
                        <span className="dot">.</span>
                        <span className="dot">.</span>
                        <span className="dot">.</span>
                    </div>
                </div>

                {/* Loading bar */}
                <div className="loading-bar-container">
                    <div className="loading-bar">
                        <div className="loading-bar-fill"></div>
                    </div>
                </div>

                {/* Tips section */}
                <div className="loading-tips">
                    <div className="tip-icon">💡</div>
                    <p className="tip-text">
                        {getRandomTip()}
                    </p>
                </div>
            </div>
        </div>
    );
};

// Random loading tips
const tips = [
    "Совет: Проверяйте характеристики вашего персонажа перед боем.",
    "Совет: Взаимодействуйте с NPC для получения ценной информации.",
    "Совет: Исследуйте мир внимательно - тайны повсюду!",
    "Совет: Сохраняйте баланс между осторожностью и смелостью.",
    "Совет: Работайте в команде для достижения лучших результатов.",
    "Совет: Читайте описания заклинаний перед использованием.",
    "Совет: Экипируйте лучшие предметы для повышения шансов на успех.",
    "Совет: Отдыхайте между боями для восстановления здоровья.",
    "Совет: Запоминайте слабости врагов для эффективной борьбы.",
    "Совет: Используйте окружение в свою пользу во время сражений."
];

function getRandomTip(): string {
    return tips[Math.floor(Math.random() * tips.length)];
}
