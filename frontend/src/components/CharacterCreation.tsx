import React, { useState, useMemo } from 'react';
import axios from 'axios';
import './CharacterCreation.css';

interface CharacterCreationProps {
    userId: number;
    onComplete: () => void;
}

// ==================== D&D 5e DATA ====================

const RACES: Record<string, {
    name: string;
    speed: number;
    size: string;
    darkvision: boolean;
    abilityBonuses: Record<string, number>;
    traits: string[];
    languages: string[];
    subraces?: string[];
}> = {
    'Human': {
        name: 'Human',
        speed: 30,
        size: 'Medium',
        darkvision: false,
        abilityBonuses: { str: 1, dex: 1, con: 1, int: 1, wis: 1, cha: 1 },
        traits: ['Extra Language'],
        languages: ['Common', 'Any One'],
    },
    'Elf': {
        name: 'Elf',
        speed: 30,
        size: 'Medium',
        darkvision: true,
        abilityBonuses: { dex: 2 },
        traits: ['Darkvision', 'Keen Senses', 'Fey Ancestry', 'Trance'],
        languages: ['Common', 'Elvish'],
        subraces: ['High Elf', 'Wood Elf', 'Drow'],
    },
    'Dwarf': {
        name: 'Dwarf',
        speed: 25,
        size: 'Medium',
        darkvision: true,
        abilityBonuses: { con: 2 },
        traits: ['Darkvision', 'Dwarven Resilience', 'Stonecunning'],
        languages: ['Common', 'Dwarvish'],
        subraces: ['Hill Dwarf', 'Mountain Dwarf'],
    },
    'Halfling': {
        name: 'Halfling',
        speed: 25,
        size: 'Small',
        darkvision: false,
        abilityBonuses: { dex: 2 },
        traits: ['Lucky', 'Brave', 'Halfling Nimbleness'],
        languages: ['Common', 'Halfling'],
        subraces: ['Lightfoot', 'Stout'],
    },
    'Dragonborn': {
        name: 'Dragonborn',
        speed: 30,
        size: 'Medium',
        darkvision: false,
        abilityBonuses: { str: 2, cha: 1 },
        traits: ['Draconic Ancestry', 'Breath Weapon', 'Damage Resistance'],
        languages: ['Common', 'Draconic'],
    },
    'Tiefling': {
        name: 'Tiefling',
        speed: 30,
        size: 'Medium',
        darkvision: true,
        abilityBonuses: { cha: 2, int: 1 },
        traits: ['Darkvision', 'Hellish Resistance', 'Infernal Legacy'],
        languages: ['Common', 'Infernal'],
    },
    'Gnome': {
        name: 'Gnome',
        speed: 25,
        size: 'Small',
        darkvision: true,
        abilityBonuses: { int: 2 },
        traits: ['Darkvision', 'Gnome Cunning'],
        languages: ['Common', 'Gnomish'],
        subraces: ['Forest Gnome', 'Rock Gnome'],
    },
    'Half-Elf': {
        name: 'Half-Elf',
        speed: 30,
        size: 'Medium',
        darkvision: true,
        abilityBonuses: { cha: 2 },
        traits: ['Darkvision', 'Fey Ancestry', '+2 Skills', '+2 Ability Scores'],
        languages: ['Common', 'Elvish', 'Any One'],
    },
    'Half-Orc': {
        name: 'Half-Orc',
        speed: 30,
        size: 'Medium',
        darkvision: true,
        abilityBonuses: { str: 2, con: 1 },
        traits: ['Darkvision', 'Menacing', 'Relentless Endurance', 'Savage Attacks'],
        languages: ['Common', 'Orc'],
    },
};

const CLASSES: Record<string, {
    name: string;
    hitDie: number;
    primaryAbility: string;
    savingThrows: string[];
    armorProficiencies: string[];
    weaponProficiencies: string[];
    skillChoices: string[];
    skillCount: number;
    startingEquipment: {
        armor?: string;
        weapons: string[];
        equipment: string[];
    };
}> = {
    'Barbarian': {
        name: 'Barbarian',
        hitDie: 12,
        primaryAbility: 'Strength',
        savingThrows: ['Strength', 'Constitution'],
        armorProficiencies: ['Light armor', 'Medium armor', 'Shields'],
        weaponProficiencies: ['Simple weapons', 'Martial weapons'],
        skillChoices: ['Animal Handling', 'Athletics', 'Intimidation', 'Nature', 'Perception', 'Survival'],
        skillCount: 2,
        startingEquipment: {
            weapons: ['Greataxe', 'Any simple melee weapon'],
            equipment: ["Explorer's pack", '4 Javelins'],
        },
    },
    'Bard': {
        name: 'Bard',
        hitDie: 8,
        primaryAbility: 'Charisma',
        savingThrows: ['Dexterity', 'Charisma'],
        armorProficiencies: ['Light armor'],
        weaponProficiencies: ['Simple weapons', 'Hand crossbows', 'Longswords', 'Rapiers', 'Shortswords'],
        skillChoices: ['Acrobatics', 'Animal Handling', 'Arcana', 'Athletics', 'Deception', 'History', 'Insight', 'Intimidation', 'Investigation', 'Medicine', 'Nature', 'Perception', 'Performance', 'Persuasion', 'Religion', 'Sleight of Hand', 'Stealth', 'Survival'],
        skillCount: 3,
        startingEquipment: {
            weapons: ['Rapier', 'Longsword', 'Any simple weapon'],
            equipment: ['Lute', 'Leather armor', 'Dagger'],
        },
    },
    'Cleric': {
        name: 'Cleric',
        hitDie: 8,
        primaryAbility: 'Wisdom',
        savingThrows: ['Wisdom', 'Charisma'],
        armorProficiencies: ['Light armor', 'Medium armor', 'Shields'],
        weaponProficiencies: ['Simple weapons'],
        skillChoices: ['History', 'Insight', 'Medicine', 'Persuasion', 'Religion'],
        skillCount: 2,
        startingEquipment: {
            weapons: ['Mace', 'Scale mail', 'Light crossbow & 20 bolts', 'Shield'],
            equipment: ['Holy symbol'],
        },
    },
    'Druid': {
        name: 'Druid',
        hitDie: 8,
        primaryAbility: 'Wisdom',
        savingThrows: ['Intelligence', 'Wisdom'],
        armorProficiencies: ['Light armor (nonmetal)', 'Medium armor (nonmetal)', 'Shields (nonmetal)'],
        weaponProficiencies: ['Clubs', 'Daggers', 'Darts', 'Javelins', 'Maces', 'Quarterstaffs', 'Scimitars', 'Sickles', 'Slings', 'Spears'],
        skillChoices: ['Arcana', 'Animal Handling', 'Insight', 'Medicine', 'Nature', 'Perception', 'Religion', 'Survival'],
        skillCount: 2,
        startingEquipment: {
            weapons: ['Wooden shield', 'Scimitar'],
            equipment: ["Explorer's pack", 'Leather armor', 'Druidic focus'],
        },
    },
    'Fighter': {
        name: 'Fighter',
        hitDie: 10,
        primaryAbility: 'Strength or Dexterity',
        savingThrows: ['Strength', 'Constitution'],
        armorProficiencies: ['All armor', 'Shields'],
        weaponProficiencies: ['Simple weapons', 'Martial weapons'],
        skillChoices: ['Acrobatics', 'Animal Handling', 'Athletics', 'History', 'Insight', 'Intimidation', 'Perception', 'Survival'],
        skillCount: 2,
        startingEquipment: {
            weapons: ['Chain mail', 'Shield & longsword', 'Light crossbow & 20 bolts'],
            equipment: [],
        },
    },
    'Monk': {
        name: 'Monk',
        hitDie: 8,
        primaryAbility: 'Dexterity & Wisdom',
        savingThrows: ['Strength', 'Dexterity'],
        armorProficiencies: [],
        weaponProficiencies: ['Simple weapons', 'Shortswords'],
        skillChoices: ['Acrobatics', 'Athletics', 'History', 'Insight', 'Religion', 'Stealth'],
        skillCount: 2,
        startingEquipment: {
            weapons: ['Shortsword', 'Any simple weapon'],
            equipment: ['10 Darts'],
        },
    },
    'Paladin': {
        name: 'Paladin',
        hitDie: 10,
        primaryAbility: 'Strength & Charisma',
        savingThrows: ['Wisdom', 'Charisma'],
        armorProficiencies: ['All armor', 'Shields'],
        weaponProficiencies: ['Simple weapons', 'Martial weapons'],
        skillChoices: ['Athletics', 'Insight', 'Intimidation', 'Medicine', 'Persuasion', 'Religion'],
        skillCount: 2,
        startingEquipment: {
            weapons: ['Chain mail', 'Shield & longsword', '5 Javelins'],
            equipment: ['Holy symbol'],
        },
    },
    'Ranger': {
        name: 'Ranger',
        hitDie: 10,
        primaryAbility: 'Dexterity & Wisdom',
        savingThrows: ['Strength', 'Dexterity'],
        armorProficiencies: ['Light armor', 'Medium armor', 'Shields'],
        weaponProficiencies: ['Simple weapons', 'Martial weapons'],
        skillChoices: ['Animal Handling', 'Athletics', 'Insight', 'Investigation', 'Nature', 'Perception', 'Stealth', 'Survival'],
        skillCount: 3,
        startingEquipment: {
            weapons: ['Scale mail', '2 Shortswords', 'Longbow & 20 arrows'],
            equipment: [],
        },
    },
    'Rogue': {
        name: 'Rogue',
        hitDie: 8,
        primaryAbility: 'Dexterity',
        savingThrows: ['Dexterity', 'Intelligence'],
        armorProficiencies: ['Light armor'],
        weaponProficiencies: ['Simple weapons', 'Hand crossbows', 'Longswords', 'Rapiers', 'Shortswords'],
        skillChoices: ['Acrobatics', 'Athletics', 'Deception', 'Insight', 'Intimidation', 'Investigation', 'Perception', 'Performance', 'Persuasion', 'Sleight of Hand', 'Stealth'],
        skillCount: 4,
        startingEquipment: {
            weapons: ['Rapier', 'Shortsword', 'Shortbow & 20 arrows'],
            equipment: ["Thieves' tools", 'Leather armor', '2 Daggers'],
        },
    },
    'Sorcerer': {
        name: 'Sorcerer',
        hitDie: 6,
        primaryAbility: 'Charisma',
        savingThrows: ['Constitution', 'Charisma'],
        armorProficiencies: [],
        weaponProficiencies: ['Daggers', 'Darts', 'Slings', 'Quarterstaffs', 'Light crossbows'],
        skillChoices: ['Arcana', 'Deception', 'Insight', 'Intimidation', 'Persuasion', 'Religion'],
        skillCount: 2,
        startingEquipment: {
            weapons: ['Light crossbow & 20 bolts', 'Arcane focus'],
            equipment: ['2 Daggers'],
        },
    },
    'Warlock': {
        name: 'Warlock',
        hitDie: 8,
        primaryAbility: 'Charisma',
        savingThrows: ['Wisdom', 'Charisma'],
        armorProficiencies: ['Light armor'],
        weaponProficiencies: ['Simple weapons'],
        skillChoices: ['Arcana', 'Deception', 'History', 'Intimidation', 'Investigation', 'Nature', 'Religion'],
        skillCount: 2,
        startingEquipment: {
            weapons: ['Light crossbow & 20 bolts', 'Arcane focus'],
            equipment: ['Leather armor', 'Simple weapon', '2 Daggers'],
        },
    },
    'Wizard': {
        name: 'Wizard',
        hitDie: 6,
        primaryAbility: 'Intelligence',
        savingThrows: ['Intelligence', 'Wisdom'],
        armorProficiencies: [],
        weaponProficiencies: ['Daggers', 'Darts', 'Slings', 'Quarterstaffs', 'Light crossbows'],
        skillChoices: ['Arcana', 'History', 'Insight', 'Investigation', 'Medicine', 'Religion'],
        skillCount: 2,
        startingEquipment: {
            weapons: ['Quarterstaff', 'Arcane focus'],
            equipment: ['Spellbook'],
        },
    },
};

const SKILLS: Record<string, string> = {
    'Acrobatics': 'Dexterity',
    'Animal Handling': 'Wisdom',
    'Arcana': 'Intelligence',
    'Athletics': 'Strength',
    'Deception': 'Charisma',
    'History': 'Intelligence',
    'Insight': 'Wisdom',
    'Intimidation': 'Charisma',
    'Investigation': 'Intelligence',
    'Medicine': 'Wisdom',
    'Nature': 'Intelligence',
    'Perception': 'Wisdom',
    'Performance': 'Charisma',
    'Persuasion': 'Charisma',
    'Religion': 'Intelligence',
    'Sleight of Hand': 'Dexterity',
    'Stealth': 'Dexterity',
    'Survival': 'Wisdom',
};

const BACKGROUNDS: Record<string, {
    skills: string[];
    equipment: string[];
    feature: string;
}> = {
    'Acolyte': {
        skills: ['Insight', 'Religion'],
        equipment: ['Holy symbol', 'Prayer book', '5 sticks of incense', 'Common clothes', '15 gp'],
        feature: 'Shelter of the Faithful',
    },
    'Charlatan': {
        skills: ['Deception', 'Sleight of Hand'],
        equipment: ['Fine clothes', 'Disguise kit', "Thieves' tools", '15 gp'],
        feature: 'False Identity',
    },
    'Criminal': {
        skills: ['Deception', 'Stealth'],
        equipment: ['Crowbar', "Thieves' tools", 'Common clothes', '15 gp'],
        feature: 'Criminal Contact',
    },
    'Entertainer': {
        skills: ['Acrobatics', 'Performance'],
        equipment: ['Musical instrument', "Entertainer's pack", 'Common clothes', '15 gp'],
        feature: 'By Popular Demand',
    },
    'Folk Hero': {
        skills: ['Animal Handling', 'Survival'],
        equipment: ["Artisan's tools", 'Shovel', 'Iron pot', 'Common clothes', '10 gp'],
        feature: 'Rustic Hospitality',
    },
    'Guild Artisan': {
        skills: ['Insight', 'Persuasion'],
        equipment: ["Artisan's tools", "Guild letter of introduction", "Traveler's clothes", '15 gp'],
        feature: 'Guild Membership',
    },
    'Hermit': {
        skills: ['Medicine', 'Religion'],
        equipment: ['Scroll case', 'Herbalism kit', "Winter blanket", 'Common clothes', '5 gp'],
        feature: 'Discovery',
    },
    'Noble': {
        skills: ['History', 'Persuasion'],
        equipment: ['Fine clothes', 'Signet ring', 'Scroll of pedigree', '25 gp'],
        feature: 'Position of Privilege',
    },
    'Outlander': {
        skills: ['Athletics', 'Survival'],
        equipment: ['Staff', 'Hunting trap', 'Animal trophy', "Traveler's clothes", '10 gp'],
        feature: 'Wanderer',
    },
    'Sage': {
        skills: ['Arcana', 'History'],
        equipment: ['Bottle of ink', 'Quill', 'Small knife', 'Common clothes', '10 gp'],
        feature: 'Researcher',
    },
    'Sailor': {
        skills: ['Athletics', 'Perception'],
        equipment: ['Belaying pin (club)', '50 ft silk rope', "Lucky charm", 'Common clothes', '10 gp'],
        feature: "Ship's Passage",
    },
    'Soldier': {
        skills: ['Athletics', 'Intimidation'],
        equipment: ['Insignia of rank', 'Trophy from fallen enemy', 'Bone dice', "Traveler's clothes", '10 gp'],
        feature: 'Military Rank',
    },
    'Urchin': {
        skills: ['Sleight of Hand', 'Stealth'],
        equipment: ['Small knife', 'Map of city', 'Pet mouse', 'Common clothes', '10 gp'],
        feature: 'City Secrets',
    },
};

const ALIGNMENTS = [
    'Lawful Good', 'Neutral Good', 'Chaotic Good',
    'Lawful Neutral', 'True Neutral', 'Chaotic Neutral',
    'Lawful Evil', 'Neutral Evil', 'Chaotic Evil',
];

const PERSONALITY_TRAITS = [
    'I idolize a particular hero and constantly refer to their deeds.',
    'I can find common ground between the fiercest enemies.',
    'Nothing can shake my optimistic attitude.',
    'I quote sacred texts and proverbs in almost every situation.',
    'I am tolerant of other faiths and respect the worship of other gods.',
    "I've enjoyed fine food, drink, and high society among my temple's elite.",
    'I see omens in every event and action.',
    'I can resist temptation and stay focused on my goals.',
    "I'm always calm, no matter the situation.",
    'I would rather make a new friend than a new enemy.',
    'I blow up at the slightest insult.',
    'I am haunted by a past mistake that I cannot forgive.',
    'I secretly believe I am better than most people.',
    'I face problems head-on, with direct action.',
    'I think carefully before making decisions.',
    "I'm quick to assume someone is lying.",
    'I love a good puzzle or mystery.',
    'I believe everything in life can be negotiated.',
];

const IDEALS = [
    'Tradition. The ancient traditions must be preserved.',
    'Charity. I try to help those in need, no matter the cost.',
    'Change. We must help bring about the changes the world needs.',
    'Power. I hope to one day rise to the top of my order.',
    'Faith. I trust that my deity will guide my actions.',
    'Aspiration. I seek to prove myself worthy of my god.',
    'Freedom. Chains are meant to be broken.',
    'Creativity. The world needs new ideas and perspectives.',
    'Honor. A person is only as good as their word.',
    'Greed. I will do whatever it takes to become wealthy.',
    'People. I like seeing the smiles on peoples faces.',
    'Redemption. Theres a spark of good in everyone.',
];

const BONDS = [
    'I would die to recover an ancient relic of my faith.',
    'I will someday get revenge on the dark temple that branded me a heretic.',
    'I owe my life to the priest who took me in when my parents died.',
    'Everything I do is for the common people.',
    'I will do anything to protect the temple where I served.',
    'I seek to preserve a sacred text that others consider heretical.',
    'A noble I once saved will always provide me shelter.',
    'My instruments are the only things that remind me of my homeland.',
    'I was cheated out of my rightful inheritance and will reclaim it.',
    'My mentor gave their life protecting me, and I honor their sacrifice.',
    'I fight for my homeland and the people I left behind.',
    'A childhood friend is in grave danger, and I must reach them in time.',
];

const FLAWS = [
    'I judge others harshly and myself even more severely.',
    'I put too much trust in the institutions of my faith.',
    'My piety leads me to blindly trust those who share my beliefs.',
    'I am inflexible in my thinking and resist change.',
    'My devotion to my ideals puts others at risk.',
    'I am secretly cynical and doubt the goodness of others.',
    'I have a weakness for the vices of city life.',
    'I cannot resist a pretty face or charming smile.',
    'I am quick to anger when my beliefs are challenged.',
    'I hoard resources and am reluctant to share.',
    'I have a gambling problem I cannot control.',
    'I am terrified of being alone or separated from my group.',
];

// ==================== POINT BUY TABLE ====================

const POINT_BUY_COSTS: Record<number, number> = {
    8: 0,
    9: 1,
    10: 2,
    11: 3,
    12: 4,
    13: 5,
    14: 7,
    15: 9,
};

const MAX_POINTS = 27;

// ==================== COMPONENT ====================

export const CharacterCreation: React.FC<CharacterCreationProps> = ({ userId, onComplete }) => {
    const [isLoading, setIsLoading] = useState(false);
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [step, setStep] = useState(1);

    const [formData, setFormData] = useState({
        // Step 1: Basics
        name: '',
        race: 'Human',
        subrace: '',
        char_class: 'Fighter',
        background: 'Soldier',
        alignment: 'True Neutral',

        // Step 2: Race Details
        selectedTraits: [] as string[],
        extraLanguage: '',

        // Step 3: Class Features
        fightingStyle: '',
        skillChoices: [] as string[],

        // Step 4: Ability Scores (base, before racial bonuses)
        baseStrength: 8,
        baseDexterity: 8,
        baseConstitution: 8,
        baseIntelligence: 8,
        baseWisdom: 8,
        baseCharisma: 8,

        // Step 5: Skills
        chosenSkills: [] as string[],

        // Step 6: Equipment (starting package choices)
        equipmentChoice: 'default',

        // Step 7: Appearance & Personality
        appearance: '',
        backstory: '',
        personalityTrait: '',
        ideal: '',
        bond: '',
        flaw: '',
        portrait_url: '',
        background_image_url: '',
    });

    // ==================== HELPERS ====================

    const getModifier = (score: number) => Math.floor((score - 10) / 2);

    const raceData = useMemo(() => RACES[formData.race], [formData.race]);
    const classData = useMemo(() => CLASSES[formData.char_class], [formData.char_class]);
    const backgroundData = useMemo(() => BACKGROUNDS[formData.background], [formData.background]);

    // Calculate final ability scores with racial bonuses
    const getFinalScore = (baseStat: number, bonusKey: string): number => {
        return baseStat + (raceData?.abilityBonuses[bonusKey] || 0);
    };

    const finalStr = getFinalScore(formData.baseStrength, 'str');
    const finalDex = getFinalScore(formData.baseDexterity, 'dex');
    const finalCon = getFinalScore(formData.baseConstitution, 'con');
    const finalInt = getFinalScore(formData.baseIntelligence, 'int');
    const finalWis = getFinalScore(formData.baseWisdom, 'wis');
    const finalCha = getFinalScore(formData.baseCharisma, 'cha');

    // Point buy calculation
    const pointsUsed = useMemo(() => {
        return (POINT_BUY_COSTS[formData.baseStrength] || 0) +
               (POINT_BUY_COSTS[formData.baseDexterity] || 0) +
               (POINT_BUY_COSTS[formData.baseConstitution] || 0) +
               (POINT_BUY_COSTS[formData.baseIntelligence] || 0) +
               (POINT_BUY_COSTS[formData.baseWisdom] || 0) +
               (POINT_BUY_COSTS[formData.baseCharisma] || 0);
    }, [formData.baseStrength, formData.baseDexterity, formData.baseConstitution,
        formData.baseIntelligence, formData.baseWisdom, formData.baseCharisma]);

    const pointsRemaining = MAX_POINTS - pointsUsed;

    // HP calculation
    const calculateHP = () => classData.hitDie + getModifier(finalCon);

    // AC calculation (unarmored = 10 + Dex mod)
    const calculateAC = () => 10 + getModifier(finalDex);

    // Proficiency bonus (level 1 = +2)
    const proficiencyBonus = 2;

    const handleStatChange = (stat: string, delta: number) => {
        const key = `base${stat}` as keyof typeof formData;
        const current = formData[key] as number;
        const newValue = current + delta;

        // Validate: min 8, max 15 for point buy
        if (newValue < 8 || newValue > 15) return;

        // Check if adding would exceed point budget
        const currentCost = POINT_BUY_COSTS[current] || 0;
        const newCost = POINT_BUY_COSTS[newValue] || 0;
        const costDiff = newCost - currentCost;

        if (delta > 0 && pointsRemaining < costDiff) return;

        setFormData(prev => ({ ...prev, [key]: newValue }));
    };

    const handleSkillToggle = (skill: string) => {
        setFormData(prev => {
            const chosen = prev.chosenSkills;
            const classAllowed = classData.skillChoices;
            const isClassSkill = classAllowed.includes(skill);
            const maxSkills = classData.skillCount + (formData.background === 'Custom' ? 0 : backgroundData?.skills.length || 0);

            // Background gives fixed skills, so we only count beyond that
            const backgroundSkillCount = backgroundData?.skills.length || 0;
            const classSkillSlots = classData.skillCount;

            if (chosen.includes(skill)) {
                return { ...prev, chosenSkills: chosen.filter(s => s !== skill) };
            }

            if (chosen.length >= maxSkills) return prev;

            return { ...prev, chosenSkills: [...chosen, skill] };
        });
    };

    // ==================== SUBMIT ====================

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setErrors({});

        const newErrors: Record<string, string> = {};
        if (!formData.name.trim()) newErrors.name = 'Character name is required';
        if (formData.name.length < 2) newErrors.name = 'Name must be at least 2 characters';
        if (formData.name.length > 50) newErrors.name = 'Name must be less than 50 characters';

        if (pointsRemaining < 0) newErrors.stats = 'You have exceeded the point buy limit!';

        if (formData.chosenSkills.length === 0) newErrors.skills = 'Choose at least one skill';

        if (Object.keys(newErrors).length > 0) {
            setErrors(newErrors);
            setIsLoading(false);
            return;
        }

        const allSkills: Record<string, boolean> = {};
        formData.chosenSkills.forEach(s => { allSkills[s] = true; });
        backgroundData?.skills.forEach(s => { allSkills[s] = true; });

        const stats = {
            strength: finalStr,
            dexterity: finalDex,
            constitution: finalCon,
            intelligence: finalInt,
            wisdom: finalWis,
            charisma: finalCha,
        };

        const racialTraits = [...raceData.traits];
        if (formData.subrace) racialTraits.push(`${formData.subrace} Trait`);

        const characterData = {
            user_id: userId,
            name: formData.name,
            race: formData.subrace ? `${formData.race} (${formData.subrace})` : formData.race,
            char_class: formData.char_class,
            level: 1,
            backstory_summary: formData.backstory || `${formData.background} seeking adventure`,
            personality_traits: JSON.stringify({
                trait: formData.personalityTrait,
                ideal: formData.ideal,
                bond: formData.bond,
                flaw: formData.flaw,
            }),
            max_hp: calculateHP(),
            current_hp: calculateHP(),
            armor_class: calculateAC(),
            speed: raceData.speed,
            stats,
            abilities: racialTraits,
            inventory: classData.startingEquipment.weapons.concat(classData.startingEquipment.equipment),
        };

        try {
            const response = await axios.post('/api/v1/characters/', characterData);

            if (response.data.id) {
                const profileData = {
                    character_id: response.data.id,
                    alignment: formData.alignment,
                    background: formData.background,
                    appearance_description: formData.appearance,
                    deity: null,
                    homeland: null,
                    hit_dice: `1d${classData.hitDie}`,
                    passive_wisdom: 10 + getModifier(finalWis),
                    inspiration: false,
                    saving_throws: {
                        str: classData.savingThrows.includes('Strength') ? proficiencyBonus : 0,
                        dex: classData.savingThrows.includes('Dexterity') ? proficiencyBonus : 0,
                        con: classData.savingThrows.includes('Constitution') ? proficiencyBonus : 0,
                        int: classData.savingThrows.includes('Intelligence') ? proficiencyBonus : 0,
                        wis: classData.savingThrows.includes('Wisdom') ? proficiencyBonus : 0,
                        cha: classData.savingThrows.includes('Charisma') ? proficiencyBonus : 0,
                    },
                    skills: allSkills,
                    equipment: classData.startingEquipment.weapons.concat(classData.startingEquipment.equipment, backgroundData?.equipment || []),
                    attacks: classData.startingEquipment.weapons,
                    spell_slots: {},
                    features_traits: racialTraits,
                    notes: `Personality: ${formData.personalityTrait}\nIdeal: ${formData.ideal}\nBond: ${formData.bond}\nFlaw: ${formData.flaw}`,
                };

                await axios.post('/api/v1/profiles/', profileData);
                onComplete();
            }
        } catch (error: any) {
            setIsLoading(false);
            if (error.response) {
                setErrors({ submit: error.response.data.detail || 'Failed to create character' });
            } else {
                setErrors({ submit: 'Network error. Please try again.' });
            }
        }
    };

    // ==================== RENDER ====================

    const stepLabels = [
        'Basics', 'Race', 'Class', 'Abilities',
        'Skills', 'Equipment', 'Personality', 'Review'
    ];

    return (
        <div className="character-creation-overlay">
            <div className="character-creation">
                {/* Header */}
                <div className="cc-header">
                    <h2>Create Your Character</h2>
                    <p>Follow the D&D 5e rules to forge your hero</p>
                </div>

                {/* Progress Bar */}
                <div className="cc-progress">
                    {stepLabels.map((label, i) => (
                        <React.Fragment key={i}>
                            <div className={`progress-step ${step >= i + 1 ? 'active' : ''}`}>
                                <span className="step-number">{i + 1}</span>
                                <span className="step-label">{label}</span>
                            </div>
                            {i < stepLabels.length - 1 && <div className="progress-line"></div>}
                        </React.Fragment>
                    ))}
                </div>

                {/* Error Display */}
                {errors.submit && (
                    <div className="cc-error">
                        <span>⚠️</span>
                        <span>{errors.submit}</span>
                    </div>
                )}

                <form className="cc-form" onSubmit={handleSubmit}>

                    {/* ==================== STEP 1: BASICS ==================== */}
                    {step === 1 && (
                        <div className="cc-section fade-in">
                            <h3>Basic Information</h3>

                            <div className="form-group">
                                <label htmlFor="name">Character Name *</label>
                                <input
                                    type="text"
                                    id="name"
                                    name="name"
                                    value={formData.name}
                                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                                    placeholder="Enter character name"
                                    maxLength={50}
                                    className={errors.name ? 'error' : ''}
                                />
                                {errors.name && <span className="error-message">{errors.name}</span>}
                            </div>

                            <div className="form-row">
                                <div className="form-group">
                                    <label htmlFor="race">Race</label>
                                    <select
                                        id="race"
                                        value={formData.race}
                                        onChange={(e) => setFormData(prev => ({
                                            ...prev,
                                            race: e.target.value,
                                            subrace: '',
                                            selectedTraits: RACES[e.target.value]?.traits || [],
                                        }))}
                                        className="race-select"
                                    >
                                        {Object.entries(RACES).map(([key, race]) => (
                                            <option key={key} value={key}>
                                                {race.name} ({Object.entries(race.abilityBonuses).map(([s, v]) => `${s.toUpperCase()} +${v}`).join(', ')})
                                            </option>
                                        ))}
                                    </select>
                                    <div className="race-info">
                                        <span>⚡ Speed: {raceData.speed}ft</span>
                                        <span>📏 Size: {raceData.size}</span>
                                        {raceData.darkvision && <span>👁️ Darkvision</span>}
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label htmlFor="char_class">Class</label>
                                    <select
                                        id="char_class"
                                        value={formData.char_class}
                                        onChange={(e) => setFormData(prev => ({
                                            ...prev,
                                            char_class: e.target.value,
                                            skillChoices: [],
                                        }))}
                                        className="class-select"
                                    >
                                        {Object.entries(CLASSES).map(([key, cls]) => (
                                            <option key={key} value={key}>
                                                {cls.name} (d{cls.hitDie}, {cls.skillCount} skills)
                                            </option>
                                        ))}
                                    </select>
                                    <div className="class-info">
                                        <span>🎯 {classData.primaryAbility}</span>
                                        <span>🛡️ Saves: {classData.savingThrows.join(', ')}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="form-row">
                                <div className="form-group">
                                    <label htmlFor="background">Background</label>
                                    <select
                                        id="background"
                                        value={formData.background}
                                        onChange={(e) => setFormData(prev => ({ ...prev, background: e.target.value }))}
                                    >
                                        {Object.keys(BACKGROUNDS).map(bg => (
                                            <option key={bg} value={bg}>{bg}</option>
                                        ))}
                                    </select>
                                    <div className="race-info" style={{ marginTop: '8px' }}>
                                        <span>Skills: {backgroundData?.skills.join(', ')}</span>
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label htmlFor="alignment">Alignment</label>
                                    <select
                                        id="alignment"
                                        value={formData.alignment}
                                        onChange={(e) => setFormData(prev => ({ ...prev, alignment: e.target.value }))}
                                    >
                                        {ALIGNMENTS.map(a => (
                                            <option key={a} value={a}>{a}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>

                            <div className="cc-actions">
                                <button type="button" className="cc-cancel" onClick={onComplete}>Cancel</button>
                                <button type="button" className="cc-next" onClick={() => setStep(2)}>Next →</button>
                            </div>
                        </div>
                    )}

                    {/* ==================== STEP 2: RACE DETAILS ==================== */}
                    {step === 2 && (
                        <div className="cc-section fade-in">
                            <h3>Racial Details — {formData.race}</h3>

                            {raceData.subraces && (
                                <div className="form-group">
                                    <label htmlFor="subrace">Subrace</label>
                                    <select
                                        id="subrace"
                                        value={formData.subrace}
                                        onChange={(e) => setFormData(prev => ({ ...prev, subrace: e.target.value }))}
                                    >
                                        <option value="">None</option>
                                        {raceData.subraces.map(sr => (
                                            <option key={sr} value={sr}>{sr}</option>
                                        ))}
                                    </select>
                                </div>
                            )}

                            <div className="form-group">
                                <label>Racial Traits</label>
                                <div className="traits-list">
                                    {raceData.traits.map(trait => (
                                        <div key={trait} className="trait-tag">
                                            <span className="trait-icon">✦</span>
                                            <span>{trait}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Languages</label>
                                <div className="languages-list">
                                    {raceData.languages.map(lang => (
                                        <span key={lang} className="lang-tag">{lang}</span>
                                    ))}
                                </div>
                            </div>

                            <div className="cc-actions">
                                <button type="button" className="cc-back" onClick={() => setStep(1)}>← Back</button>
                                <button type="button" className="cc-next" onClick={() => setStep(3)}>Next →</button>
                            </div>
                        </div>
                    )}

                    {/* ==================== STEP 3: CLASS FEATURES ==================== */}
                    {step === 3 && (
                        <div className="cc-section fade-in">
                            <h3>Class Features — {formData.char_class}</h3>

                            <div className="class-features">
                                <div className="feature-block">
                                    <h4>Hit Points</h4>
                                    <div className="feature-value">
                                        <span className="highlight">d{classData.hitDie}</span> per level
                                        <p className="feature-desc">HP at level 1: {classData.hitDie} + Con modifier</p>
                                    </div>
                                </div>

                                <div className="feature-block">
                                    <h4>Proficiency Bonus</h4>
                                    <div className="feature-value">
                                        <span className="highlight">+{proficiencyBonus}</span> (Level 1)
                                    </div>
                                </div>

                                <div className="feature-block">
                                    <h4>Saving Throw Proficiencies</h4>
                                    <div className="feature-value">
                                        {classData.savingThrows.map(st => (
                                            <span key={st} className="save-tag">{st}</span>
                                        ))}
                                    </div>
                                </div>

                                <div className="feature-block">
                                    <h4>Armor Proficiencies</h4>
                                    <div className="feature-value">
                                        {classData.armorProficiencies.length > 0 ? (
                                            classData.armorProficiencies.map(ap => (
                                                <span key={ap} className="prof-tag">{ap}</span>
                                            ))
                                        ) : (
                                            <span className="none-tag">None</span>
                                        )}
                                    </div>
                                </div>

                                <div className="feature-block">
                                    <h4>Weapon Proficiencies</h4>
                                    <div className="feature-value">
                                        {classData.weaponProficiencies.map(wp => (
                                            <span key={wp} className="prof-tag">{wp}</span>
                                        ))}
                                    </div>
                                </div>

                                <div className="feature-block">
                                    <h4>Skill Choices (Choose {classData.skillCount})</h4>
                                    <div className="class-skill-choices">
                                        {classData.skillChoices.map(skill => {
                                            const ability = SKILLS[skill];
                                            const isChosen = formData.skillChoices.includes(skill);
                                            return (
                                                <button
                                                    key={skill}
                                                    type="button"
                                                    className={`skill-choice-btn ${isChosen ? 'chosen' : ''}`}
                                                    onClick={() => {
                                                        setFormData(prev => {
                                                            const choices = prev.skillChoices;
                                                            if (choices.includes(skill)) {
                                                                return { ...prev, skillChoices: choices.filter(s => s !== skill) };
                                                            }
                                                            if (choices.length >= classData.skillCount) return prev;
                                                            return { ...prev, skillChoices: [...choices, skill] };
                                                        });
                                                    }}
                                                >
                                                    {skill} <span className="skill-ability">({ability.slice(0, 3)})</span>
                                                </button>
                                            );
                                        })}
                                    </div>
                                    <p className="choice-counter">
                                        Selected: {formData.skillChoices.length}/{classData.skillCount}
                                    </p>
                                </div>
                            </div>

                            <div className="cc-actions">
                                <button type="button" className="cc-back" onClick={() => setStep(2)}>← Back</button>
                                <button type="button" className="cc-next" onClick={() => setStep(4)}>Next →</button>
                            </div>
                        </div>
                    )}

                    {/* ==================== STEP 4: ABILITY SCORES ==================== */}
                    {step === 4 && (
                        <div className="cc-section fade-in">
                            <h3>Ability Scores</h3>
                            <p className="stat-points">
                                Point Buy: {pointsUsed}/{MAX_POINTS} points used
                                {pointsRemaining > 0 && (
                                    <span className="points-remaining"> ({pointsRemaining} remaining)</span>
                                )}
                                {pointsRemaining <= 0 && (
                                    <span className="points-max"> — Maximum reached!</span>
                                )}
                            </p>

                            <div className="stats-grid">
                                {[
                                    { label: 'Strength', abbr: 'STR', key: 'Strength', bonusKey: 'str', base: formData.baseStrength, final: finalStr },
                                    { label: 'Dexterity', abbr: 'DEX', key: 'Dexterity', bonusKey: 'dex', base: formData.baseDexterity, final: finalDex },
                                    { label: 'Constitution', abbr: 'CON', key: 'Constitution', bonusKey: 'con', base: formData.baseConstitution, final: finalCon },
                                    { label: 'Intelligence', abbr: 'INT', key: 'Intelligence', bonusKey: 'int', base: formData.baseIntelligence, final: finalInt },
                                    { label: 'Wisdom', abbr: 'WIS', key: 'Wisdom', bonusKey: 'wis', base: formData.baseWisdom, final: finalWis },
                                    { label: 'Charisma', abbr: 'CHA', key: 'Charisma', bonusKey: 'cha', base: formData.baseCharisma, final: finalCha },
                                ].map(stat => {
                                    const racialBonus = raceData?.abilityBonuses[stat.bonusKey] || 0;
                                    return (
                                        <div key={stat.key} className="stat-control">
                                            <label className="stat-label">{stat.label}</label>
                                            <div className="stat-input">
                                                <button
                                                    type="button"
                                                    onClick={() => handleStatChange(stat.key, -1)}
                                                    className="stat-btn minus"
                                                    disabled={stat.base <= 8}
                                                >
                                                    −
                                                </button>
                                                <div className="stat-value-group">
                                                    <span className="stat-value">{stat.base}</span>
                                                    {racialBonus > 0 && (
                                                        <span className="racial-bonus">+{racialBonus}</span>
                                                    )}
                                                    <span className="stat-final">= {stat.final}</span>
                                                </div>
                                                <button
                                                    type="button"
                                                    onClick={() => handleStatChange(stat.key, 1)}
                                                    className="stat-btn plus"
                                                    disabled={stat.base >= 15 || pointsRemaining <= 0}
                                                >
                                                    +
                                                </button>
                                            </div>
                                            <span className="stat-modifier">
                                                Modifier: {getModifier(stat.final) >= 0 ? '+' : ''}{getModifier(stat.final)}
                                            </span>
                                        </div>
                                    );
                                })}
                            </div>

                            {errors.stats && <span className="error-message">{errors.stats}</span>}

                            <div className="stat-summary">
                                <h4>Combat Stats Preview</h4>
                                <div className="derived-stats">
                                    <div className="derived-stat">
                                        <span>❤️ Hit Points:</span>
                                        <span className="value">{calculateHP()}</span>
                                    </div>
                                    <div className="derived-stat">
                                        <span>🛡️ Armor Class:</span>
                                        <span className="value">{calculateAC()}</span>
                                    </div>
                                    <div className="derived-stat">
                                        <span>⚡ Initiative:</span>
                                        <span className="value">{getModifier(finalDex) >= 0 ? '+' : ''}{getModifier(finalDex)}</span>
                                    </div>
                                    <div className="derived-stat">
                                        <span>👁️ Passive Wisdom:</span>
                                        <span className="value">{10 + getModifier(finalWis)}</span>
                                    </div>
                                    <div className="derived-stat">
                                        <span>🏃 Speed:</span>
                                        <span className="value">{raceData.speed}ft</span>
                                    </div>
                                    <div className="derived-stat">
                                        <span>🎯 Proficiency:</span>
                                        <span className="value">+{proficiencyBonus}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="cc-actions">
                                <button type="button" className="cc-back" onClick={() => setStep(3)}>← Back</button>
                                <button type="button" className="cc-next" onClick={() => setStep(5)}>Next →</button>
                            </div>
                        </div>
                    )}

                    {/* ==================== STEP 5: SKILLS ==================== */}
                    {step === 5 && (
                        <div className="cc-section fade-in">
                            <h3>Skills & Proficiencies</h3>

                            <div className="skills-section">
                                <div className="skill-category">
                                    <h4>Background Skills (Fixed)</h4>
                                    <div className="fixed-skills">
                                        {backgroundData?.skills.map(skill => (
                                            <div key={skill} className="fixed-skill-tag">
                                                {skill} <span className="skill-ability">({SKILLS[skill]?.slice(0, 3)})</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div className="skill-category">
                                    <h4>Class Skills (Choose {classData.skillCount})</h4>
                                    <div className="skills-grid">
                                        {Object.entries(SKILLS).map(([skill, ability]) => {
                                            const isClassSkill = classData.skillChoices.includes(skill);
                                            const isChosen = formData.chosenSkills.includes(skill);
                                            const isBackgroundSkill = backgroundData?.skills.includes(skill);

                                            return (
                                                <button
                                                    key={skill}
                                                    type="button"
                                                    className={`skill-btn ${isChosen ? 'chosen' : ''} ${!isClassSkill ? 'disabled' : ''}`}
                                                    disabled={!isClassSkill}
                                                    onClick={() => handleSkillToggle(skill)}
                                                >
                                                    <span className="skill-name">{skill}</span>
                                                    <span className="skill-ability">{ability.slice(0, 3)}</span>
                                                    {isChosen && <span className="skill-check">✓</span>}
                                                </button>
                                            );
                                        })}
                                    </div>
                                </div>

                                <div className="skill-summary">
                                    <h4>Total Skills: {formData.chosenSkills.length + (backgroundData?.skills.length || 0)}</h4>
                                    <div className="total-skills-list">
                                        {[...formData.chosenSkills, ...(backgroundData?.skills || [])].map(skill => (
                                            <span key={skill} className="total-skill-tag">{skill}</span>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            {errors.skills && <span className="error-message">{errors.skills}</span>}

                            <div className="cc-actions">
                                <button type="button" className="cc-back" onClick={() => setStep(4)}>← Back</button>
                                <button type="button" className="cc-next" onClick={() => setStep(6)}>Next →</button>
                            </div>
                        </div>
                    )}

                    {/* ==================== STEP 6: EQUIPMENT ==================== */}
                    {step === 6 && (
                        <div className="cc-section fade-in">
                            <h3>Starting Equipment</h3>

                            <div className="equipment-section">
                                <div className="equipment-category">
                                    <h4>🎒 Background Equipment</h4>
                                    <div className="equipment-list">
                                        {backgroundData?.equipment.map((item, i) => (
                                            <div key={i} className="equipment-item">
                                                <span className="equip-icon">📦</span>
                                                <span>{item}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div className="equipment-category">
                                    <h4>⚔️ Class Starting Equipment</h4>
                                    <div className="equipment-list">
                                        {classData.startingEquipment.weapons.map((item, i) => (
                                            <div key={`weapon-${i}`} className="equipment-item weapon">
                                                <span className="equip-icon">⚔️</span>
                                                <span>{item}</span>
                                            </div>
                                        ))}
                                        {classData.startingEquipment.equipment.map((item, i) => (
                                            <div key={`equip-${i}`} className="equipment-item">
                                                <span className="equip-icon">🎒</span>
                                                <span>{item}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div className="equipment-summary-box">
                                    <h4>Starting Gold (Alternative)</h4>
                                    <p className="gold-info">Instead of starting equipment, you can roll for gold:</p>
                                    <div className="gold-amounts">
                                        <div className="gold-row">
                                            <span>Barbarian/Fighter/Paladin/Ranger:</span>
                                            <span className="gold-value">5d4 × 10 gp</span>
                                        </div>
                                        <div className="gold-row">
                                            <span>Bard/Cleric/Druid/Monk/Rogue/Warlock:</span>
                                            <span className="gold-value">4d4 × 10 gp</span>
                                        </div>
                                        <div className="gold-row">
                                            <span>Sorcerer/Wizard:</span>
                                            <span className="gold-value">3d4 × 10 gp</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="cc-actions">
                                <button type="button" className="cc-back" onClick={() => setStep(5)}>← Back</button>
                                <button type="button" className="cc-next" onClick={() => setStep(7)}>Next →</button>
                            </div>
                        </div>
                    )}

                    {/* ==================== STEP 7: PERSONALITY ==================== */}
                    {step === 7 && (
                        <div className="cc-section fade-in">
                            <h3>Personality & Appearance</h3>

                            <div className="personality-section">
                                <div className="personality-grid">
                                    <div className="form-group">
                                        <label htmlFor="personalityTrait">Personality Trait</label>
                                        <select
                                            id="personalityTrait"
                                            value={formData.personalityTrait}
                                            onChange={(e) => setFormData(prev => ({ ...prev, personalityTrait: e.target.value }))}
                                        >
                                            <option value="">Select a trait...</option>
                                            {PERSONALITY_TRAITS.map((t, i) => (
                                                <option key={i} value={t}>{t}</option>
                                            ))}
                                        </select>
                                    </div>

                                    <div className="form-group">
                                        <label htmlFor="ideal">Ideal</label>
                                        <select
                                            id="ideal"
                                            value={formData.ideal}
                                            onChange={(e) => setFormData(prev => ({ ...prev, ideal: e.target.value }))}
                                        >
                                            <option value="">Select an ideal...</option>
                                            {IDEALS.map((t, i) => (
                                                <option key={i} value={t}>{t}</option>
                                            ))}
                                        </select>
                                    </div>

                                    <div className="form-group">
                                        <label htmlFor="bond">Bond</label>
                                        <select
                                            id="bond"
                                            value={formData.bond}
                                            onChange={(e) => setFormData(prev => ({ ...prev, bond: e.target.value }))}
                                        >
                                            <option value="">Select a bond...</option>
                                            {BONDS.map((t, i) => (
                                                <option key={i} value={t}>{t}</option>
                                            ))}
                                        </select>
                                    </div>

                                    <div className="form-group">
                                        <label htmlFor="flaw">Flaw</label>
                                        <select
                                            id="flaw"
                                            value={formData.flaw}
                                            onChange={(e) => setFormData(prev => ({ ...prev, flaw: e.target.value }))}
                                        >
                                            <option value="">Select a flaw...</option>
                                            {FLAWS.map((t, i) => (
                                                <option key={i} value={t}>{t}</option>
                                            ))}
                                        </select>
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label htmlFor="appearance">Physical Description</label>
                                    <textarea
                                        id="appearance"
                                        value={formData.appearance}
                                        onChange={(e) => setFormData(prev => ({ ...prev, appearance: e.target.value }))}
                                        placeholder="Describe your character's appearance (height, build, hair color, eye color, scars, distinguishing features...)"
                                        rows={4}
                                    />
                                </div>

                                <div className="form-group">
                                    <label htmlFor="backstory">Backstory (Optional)</label>
                                    <textarea
                                        id="backstory"
                                        value={formData.backstory}
                                        onChange={(e) => setFormData(prev => ({ ...prev, backstory: e.target.value }))}
                                        placeholder="Tell the story of your character's life before the adventure began..."
                                        rows={5}
                                    />
                                </div>

                                <div className="form-row">
                                    <div className="form-group">
                                        <label htmlFor="portrait_url">Portrait URL (Optional)</label>
                                        <input
                                            type="url"
                                            id="portrait_url"
                                            value={formData.portrait_url}
                                            onChange={(e) => setFormData(prev => ({ ...prev, portrait_url: e.target.value }))}
                                            placeholder="https://example.com/portrait.jpg"
                                        />
                                        {formData.portrait_url && (
                                            <div className="image-preview">
                                                <img src={formData.portrait_url} alt="Portrait" onError={(e) => (e.currentTarget.style.display = 'none')} />
                                            </div>
                                        )}
                                    </div>

                                    <div className="form-group">
                                        <label htmlFor="background_image_url">Background Image (Optional)</label>
                                        <input
                                            type="url"
                                            id="background_image_url"
                                            value={formData.background_image_url}
                                            onChange={(e) => setFormData(prev => ({ ...prev, background_image_url: e.target.value }))}
                                            placeholder="https://example.com/background.jpg"
                                        />
                                        {formData.background_image_url && (
                                            <div className="image-preview background-preview">
                                                <img src={formData.background_image_url} alt="Background" onError={(e) => (e.currentTarget.style.display = 'none')} />
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>

                            <div className="cc-actions">
                                <button type="button" className="cc-back" onClick={() => setStep(6)}>← Back</button>
                                <button type="button" className="cc-next" onClick={() => setStep(8)}>Next →</button>
                            </div>
                        </div>
                    )}

                    {/* ==================== STEP 8: REVIEW ==================== */}
                    {step === 8 && (
                        <div className="cc-section fade-in">
                            <h3>Review Your Character</h3>

                            <div className="character-preview">
                                <div className="preview-header">
                                    {formData.portrait_url ? (
                                        <img src={formData.portrait_url} alt={formData.name} className="preview-portrait" />
                                    ) : (
                                        <div className="preview-portrait-placeholder">
                                            {formData.name.charAt(0).toUpperCase() || '?'}
                                        </div>
                                    )}
                                    <div className="preview-basic">
                                        <h4>{formData.name || 'Unnamed Hero'}</h4>
                                        <p>Level 1 {formData.race} {formData.char_class}</p>
                                        <p>{formData.alignment} • {formData.background}</p>
                                        {formData.subrace && <p>Subrace: {formData.subrace}</p>}
                                    </div>
                                </div>

                                <div className="preview-stats">
                                    <div className="preview-stat-row">
                                        <span>❤️ HP:</span>
                                        <span className="stat-value hp">{calculateHP()}</span>
                                    </div>
                                    <div className="preview-stat-row">
                                        <span>🛡️ AC:</span>
                                        <span className="stat-value ac">{calculateAC()}</span>
                                    </div>
                                    <div className="preview-stat-row">
                                        <span>🏃 Speed:</span>
                                        <span className="stat-value speed">{raceData.speed}ft</span>
                                    </div>
                                </div>

                                <div className="preview-abilities">
                                    <h5>Ability Scores</h5>
                                    <div className="ability-grid">
                                        {[
                                            { abbr: 'STR', final: finalStr },
                                            { abbr: 'DEX', final: finalDex },
                                            { abbr: 'CON', final: finalCon },
                                            { abbr: 'INT', final: finalInt },
                                            { abbr: 'WIS', final: finalWis },
                                            { abbr: 'CHA', final: finalCha },
                                        ].map(({ abbr, final }) => (
                                            <div key={abbr} className="ability-preview">
                                                <span className="abbr">{abbr}</span>
                                                <span className="score">{final}</span>
                                                <span className="mod">{getModifier(final) >= 0 ? '+' : ''}{getModifier(final)}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div className="preview-section">
                                    <h5>Racial Traits</h5>
                                    <div className="traits-list">
                                        {raceData.traits.map(t => (
                                            <span key={t} className="trait-tag">{t}</span>
                                        ))}
                                    </div>
                                </div>

                                <div className="preview-section">
                                    <h5>Skills ({formData.chosenSkills.length + (backgroundData?.skills.length || 0)})</h5>
                                    <div className="total-skills-list">
                                        {[...formData.chosenSkills, ...(backgroundData?.skills || [])].map(skill => (
                                            <span key={skill} className="total-skill-tag">{skill}</span>
                                        ))}
                                    </div>
                                </div>

                                {(formData.personalityTrait || formData.ideal || formData.bond || formData.flaw) && (
                                    <div className="preview-section">
                                        <h5>Personality</h5>
                                        {formData.personalityTrait && <p><strong>Trait:</strong> {formData.personalityTrait}</p>}
                                        {formData.ideal && <p><strong>Ideal:</strong> {formData.ideal}</p>}
                                        {formData.bond && <p><strong>Bond:</strong> {formData.bond}</p>}
                                        {formData.flaw && <p><strong>Flaw:</strong> {formData.flaw}</p>}
                                    </div>
                                )}

                                {formData.appearance && (
                                    <div className="preview-section">
                                        <h5>Appearance</h5>
                                        <p>{formData.appearance}</p>
                                    </div>
                                )}

                                {formData.backstory && (
                                    <div className="preview-section">
                                        <h5>Backstory</h5>
                                        <p>{formData.backstory}</p>
                                    </div>
                                )}

                                <div className="preview-section">
                                    <h5>Starting Equipment</h5>
                                    <div className="equipment-list">
                                        {[...classData.startingEquipment.weapons, ...classData.startingEquipment.equipment, ...(backgroundData?.equipment || [])].map((item, i) => (
                                            <div key={i} className="equipment-item">
                                                <span className="equip-icon">{item.includes('weapon') || item.includes('sword') || item.includes('bow') ? '⚔️' : '📦'}</span>
                                                <span>{item}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            <div className="cc-actions">
                                <button type="button" className="cc-back" onClick={() => setStep(7)}>← Back</button>
                                <button type="submit" className="cc-submit" disabled={isLoading}>
                                    {isLoading ? 'Creating...' : '✨ Create Character'}
                                </button>
                            </div>
                        </div>
                    )}

                </form>
            </div>
        </div>
    );
};
