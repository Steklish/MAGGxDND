import React, { useState, useEffect } from 'react';
import './GamePage.css';

interface Character {
    player_id: string;
    player_name: string;
    character: {
        name: string;
        race: string;
        char_class: string;
        level: number;
        hp: number;
        max_hp: number;
        ac: number;
        initiative: number;
        portrait_url?: string;
    };
}

interface Scene {
    name: string;
    description: string;
}

interface GameMessage {
    id: string;
    sender: string;
    text: string;
    type: 'narration' | 'player' | 'dm' | 'system';
    timestamp: number;
}

interface GamePageProps {
    sessionId: string;
    players: Character[];
    scene: Scene;
    onLeave: () => void;
}

export const GamePage: React.FC<GamePageProps> = ({ sessionId, players, scene, onLeave }) => {
    const [currentTurn, setCurrentTurn] = useState(0);
    const [turnQueue, setTurnQueue] = useState<Character[]>(players);
    const [messages, setMessages] = useState<GameMessage[]>([
        {
            id: '1',
            sender: 'DM',
            text: scene.description,
            type: 'narration',
            timestamp: Date.now()
        }
    ]);
    const [actionInput, setActionInput] = useState('');
    const [isProcessing, setIsProcessing] = useState(false);

    const currentPlayer = turnQueue[currentTurn];

    useEffect(() => {
        // Add system message when turn changes
        if (currentPlayer) {
            addSystemMessage(`${currentPlayer.character.name}'s turn!`);
        }
    }, [currentTurn]);

    const addSystemMessage = (text: string) => {
        setMessages(prev => [...prev, {
            id: Date.now().toString(),
            sender: 'System',
            text,
            type: 'system',
            timestamp: Date.now()
        }]);
    };

    const handleEndTurn = () => {
        setCurrentTurn((prev) => (prev + 1) % turnQueue.length);
    };

    const handleAction = async () => {
        if (!actionInput.trim() || isProcessing) return;

        setIsProcessing(true);
        const playerAction = actionInput;
        setActionInput('');

        // Add player message
        setMessages(prev => [...prev, {
            id: Date.now().toString(),
            sender: currentPlayer.character.name,
            text: playerAction,
            type: 'player',
            timestamp: Date.now()
        }]);

        // Simulate DM response (TODO: Connect to backend AI)
        setTimeout(() => {
            setMessages(prev => [...prev, {
                id: Date.now().toString(),
                sender: 'DM',
                text: `You attempt to ${playerAction}. Rolling d20... (Demo response - backend integration needed)`,
                type: 'dm',
                timestamp: Date.now()
            }]);
            setIsProcessing(false);
            handleEndTurn();
        }, 1500);
    };

    const handleRollDice = (sides: number) => {
        const result = Math.floor(Math.random() * sides) + 1;
        addSystemMessage(`${currentPlayer.character.name} rolled d${sides}: ${result}`);
    };

    return (
        <div className="game-page">
            <div className="game-header">
                <div className="session-info">
                    <h1>⚔️ Game Session</h1>
                    <span className="session-id">{sessionId}</span>
                </div>
                <button className="btn-leave-game" onClick={onLeave}>
                    🚪 Leave Game
                </button>
            </div>

            <div className="game-content">
                {/* Turn Order */}
                <div className="turn-order-panel">
                    <h3>📜 Turn Order</h3>
                    <div className="turn-list">
                        {turnQueue.map((player, index) => (
                            <div 
                                key={player.player_id} 
                                className={`turn-item ${index === currentTurn ? 'active' : ''}`}
                            >
                                <div className="turn-avatar">
                                    {player.character.portrait_url ? (
                                        <img src={player.character.portrait_url} alt={player.character.name} />
                                    ) : (
                                        <span>{player.character.name.charAt(0)}</span>
                                    )}
                                </div>
                                <div className="turn-info">
                                    <span className="turn-name">{player.character.name}</span>
                                    <span className="turn-initiative">Init: {player.character.initiative}</span>
                                </div>
                                {index === currentTurn && (
                                    <span className="turn-badge">Current</span>
                                )}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Main Game Area */}
                <div className="main-game-area">
                    {/* Scene Description */}
                    <div className="scene-panel">
                        <h2>📍 {scene.name}</h2>
                        <p className="scene-description">{scene.description}</p>
                    </div>

                    {/* Messages Log */}
                    <div className="messages-panel">
                        <h3>💬 Message Log</h3>
                        <div className="messages-list">
                            {messages.map(msg => (
                                <div key={msg.id} className={`message ${msg.type}`}>
                                    <span className="message-sender">{msg.sender}:</span>
                                    <span className="message-text">{msg.text}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Action Panel */}
                    <div className="action-panel">
                        <div className="current-player">
                            <h3>🎯 Your Turn: {currentPlayer?.character.name}</h3>
                            <div className="character-stats">
                                <span>HP: {currentPlayer?.character.hp}/{currentPlayer?.character.max_hp}</span>
                                <span>AC: {currentPlayer?.character.ac}</span>
                            </div>
                        </div>

                        <div className="action-input">
                            <textarea
                                value={actionInput}
                                onChange={(e) => setActionInput(e.target.value)}
                                placeholder="Describe your action..."
                                rows={3}
                                disabled={isProcessing}
                            />
                            <div className="action-buttons">
                                <button 
                                    className="btn-action"
                                    onClick={handleAction}
                                    disabled={!actionInput.trim() || isProcessing}
                                >
                                    {isProcessing ? '⏳ Processing...' : '✅ Do Action'}
                                </button>
                                <button 
                                    className="btn-end-turn"
                                    onClick={handleEndTurn}
                                >
                                    ⏭️ End Turn
                                </button>
                            </div>
                        </div>

                        <div className="dice-buttons">
                            <span className="dice-label">Roll Dice:</span>
                            <button className="btn-dice" onClick={() => handleRollDice(20)}>D20</button>
                            <button className="btn-dice" onClick={() => handleRollDice(12)}>D12</button>
                            <button className="btn-dice" onClick={() => handleRollDice(10)}>D10</button>
                            <button className="btn-dice" onClick={() => handleRollDice(8)}>D8</button>
                            <button className="btn-dice" onClick={() => handleRollDice(6)}>D6</button>
                            <button className="btn-dice" onClick={() => handleRollDice(4)}>D4</button>
                        </div>
                    </div>
                </div>

                {/* Character Panels */}
                <div className="characters-panel">
                    <h3>👥 Party</h3>
                    {turnQueue.map(player => (
                        <div key={player.player_id} className="character-card">
                            <div className="char-avatar">
                                {player.character.portrait_url ? (
                                    <img src={player.character.portrait_url} alt={player.character.name} />
                                ) : (
                                    <span>{player.character.name.charAt(0)}</span>
                                )}
                            </div>
                            <div className="char-info">
                                <span className="char-name">{player.character.name}</span>
                                <span className="char-class">{player.character.race} {player.character.char_class}</span>
                                <div className="char-stats">
                                    <span className="hp-bar">
                                        HP: {player.character.hp}/{player.character.max_hp}
                                    </span>
                                    <span className="ac">AC: {player.character.ac}</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};
