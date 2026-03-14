import React, { useState } from 'react';
import './Rulebook.css';

interface RulebookProps {
    onClose: () => void;
}

export const Rulebook: React.FC<RulebookProps> = ({ onClose }) => {
    const [selectedCategory, setSelectedCategory] = useState<string>('basics');
    const [searchQuery, setSearchQuery] = useState('');

    const categories = [
        { id: 'basics', name: '📖 Basics', icon: '📖' },
        { id: 'combat', name: '⚔️ Combat', icon: '⚔️' },
        { id: 'spells', name: '✨ Spells', icon: '✨' },
        { id: 'equipment', name: '🎒 Equipment', icon: '🎒' },
        { id: 'skills', name: '🎯 Skills', icon: '🎯' },
        { id: 'races', name: '🧝 Races', icon: '🧝' },
        { id: 'classes', name: '⚔️ Classes', icon: '⚔️' },
    ];

    const ruleContent: Record<string, { title: string; content: string }[]> = {
        basics: [
            {
                title: 'Ability Scores',
                content: 'The six ability scores are Strength, Dexterity, Constitution, Intelligence, Wisdom, and Charisma. They range from 1 to 20 for most characters, with modifiers ranging from -5 to +5.',
            },
            {
                title: 'Proficiency Bonus',
                content: 'Your proficiency bonus starts at +2 at 1st level and increases as you gain levels. Add it to ability checks, attack rolls, and saving throws you\'re proficient in.',
            },
            {
                title: 'Advantage & Disadvantage',
                content: 'When you have advantage, roll 2d20 and use the higher result. With disadvantage, roll 2d20 and use the lower result.',
            },
        ],
        combat: [
            {
                title: 'Initiative',
                content: 'At the start of combat, each participant makes a Dexterity check to determine their place in the initiative order.',
            },
            {
                title: 'Actions in Combat',
                content: 'On your turn, you can move and take one action. Common actions include Attack, Cast a Spell, Dash, Disengage, Dodge, Help, Hide, and Use an Object.',
            },
            {
                title: 'Attack Rolls',
                content: 'Roll a d20 and add your proficiency bonus (if proficient) and the appropriate ability modifier. If the total equals or exceeds the target\'s AC, you hit.',
            },
        ],
        spells: [
            {
                title: 'Spell Slots',
                content: 'You expend spell slots to cast spells. Higher-level spells require higher-level slots. You regain all expended spell slots after a long rest.',
            },
            {
                title: 'Spell Components',
                content: 'Spells require components: Verbal (V), Somatic (S), and/or Material (M). You must be able to provide all components to cast the spell.',
            },
            {
                title: 'Concentration',
                content: 'Some spells require concentration. You can only concentrate on one spell at a time. Taking damage may require a Constitution save to maintain concentration.',
            },
        ],
        equipment: [
            {
                title: 'Armor Class (AC)',
                content: 'Your AC determines how hard you are to hit. Base AC is 10 + Dexterity modifier. Armor provides additional protection.',
            },
            {
                title: 'Weapons',
                content: 'Weapons are either melee or ranged. Add your Strength modifier to melee attacks and Dexterity to ranged attacks (unless finesse or thrown).',
            },
        ],
        skills: [
            {
                title: 'Skill Checks',
                content: 'Skill checks are ability checks using specific skills. If proficient, add your proficiency bonus to the roll.',
            },
            {
                title: 'Passive Skills',
                content: 'Passive scores represent average results. Passive Perception = 10 + Perception modifier. DM uses this for secret checks.',
            },
        ],
        races: [
            {
                title: 'Human',
                content: 'Humans are versatile and ambitious. +1 to all ability scores. Some variants get a feat and skill proficiency.',
            },
            {
                title: 'Elf',
                content: 'Elves are magical and graceful. +2 Dexterity. Darkvision, keen senses, and Fey Ancestry. Subraces include High Elf, Wood Elf, and Drow.',
            },
            {
                title: 'Dwarf',
                content: 'Dwarves are stout and resilient. +2 Constitution. Darkvision, Dwarven Resilience, and weapon proficiencies. Subraces include Hill Dwarf and Mountain Dwarf.',
            },
        ],
        classes: [
            {
                title: 'Fighter',
                content: 'Masters of martial combat. Features include Fighting Style, Second Wind, Action Surge, and Extra Attack.',
            },
            {
                title: 'Wizard',
                content: 'Scholars of magic. Use Intelligence for spellcasting. Have a spellbook and can learn many spells. Arcane Recovery feature.',
            },
            {
                title: 'Rogue',
                content: 'Skilled experts and sneak attackers. Use Dexterity. Features include Sneak Attack, Cunning Action, and Uncanny Dodge.',
            },
        ],
    };

    const filteredContent = selectedCategory 
        ? ruleContent[selectedCategory].filter(item => 
            item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
            item.content.toLowerCase().includes(searchQuery.toLowerCase())
        )
        : [];

    return (
        <div className="rulebook-overlay" onClick={onClose}>
            <div className="rulebook-modal" onClick={(e) => e.stopPropagation()}>
                <div className="rulebook-header">
                    <h2>📚 Rulebook</h2>
                    <button className="rb-close" onClick={onClose}>✕</button>
                </div>

                <div className="rulebook-search">
                    <input
                        type="text"
                        className="rb-search-input"
                        placeholder="Search rules..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>

                <div className="rulebook-content">
                    <div className="rb-sidebar">
                        {categories.map((cat) => (
                            <button
                                key={cat.id}
                                className={`rb-category-btn ${selectedCategory === cat.id ? 'active' : ''}`}
                                onClick={() => setSelectedCategory(cat.id)}
                            >
                                {cat.icon} {cat.name.replace(/📖|⚔️|✨|🎒|🎯|🧝/g, '').trim()}
                            </button>
                        ))}
                    </div>

                    <div className="rb-main-content">
                        <h3 className="rb-section-title">
                            {categories.find(c => c.id === selectedCategory)?.name}
                        </h3>
                        
                        {filteredContent.length > 0 ? (
                            <div className="rb-rules-list">
                                {filteredContent.map((rule, index) => (
                                    <div key={index} className="rb-rule-card">
                                        <h4 className="rb-rule-title">{rule.title}</h4>
                                        <p className="rb-rule-content">{rule.content}</p>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="rb-empty">
                                <span className="rb-empty-icon">📖</span>
                                <p>No rules found</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};
