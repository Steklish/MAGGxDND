import React, { useState, useMemo, useRef } from 'react';
import axios from 'axios';
import './CharacterCreation.css';

interface CharacterCreationProps {
    userId: number;
    onComplete: () => void;
}

// ==================== D&D 5e DATA ====================

const RACES: Record<string, { name: string; speed: number; size: string; darkvision: boolean; abilityBonuses: Record<string, number>; traits: string[]; languages: string[]; subraces?: string[] }> = {
    'Human': { name: 'Human', speed: 30, size: 'Medium', darkvision: false, abilityBonuses: { str: 1, dex: 1, con: 1, int: 1, wis: 1, cha: 1 }, traits: ['Extra Language'], languages: ['Common', 'Any One'] },
    'Elf': { name: 'Elf', speed: 30, size: 'Medium', darkvision: true, abilityBonuses: { dex: 2 }, traits: ['Darkvision', 'Keen Senses', 'Fey Ancestry', 'Trance'], languages: ['Common', 'Elvish'], subraces: ['High Elf', 'Wood Elf', 'Drow'] },
    'Dwarf': { name: 'Dwarf', speed: 25, size: 'Medium', darkvision: true, abilityBonuses: { con: 2 }, traits: ['Darkvision', 'Dwarven Resilience', 'Stonecunning'], languages: ['Common', 'Dwarvish'], subraces: ['Hill Dwarf', 'Mountain Dwarf'] },
    'Halfling': { name: 'Halfling', speed: 25, size: 'Small', darkvision: false, abilityBonuses: { dex: 2 }, traits: ['Lucky', 'Brave', 'Halfling Nimbleness'], languages: ['Common', 'Halfling'], subraces: ['Lightfoot', 'Stout'] },
    'Dragonborn': { name: 'Dragonborn', speed: 30, size: 'Medium', darkvision: false, abilityBonuses: { str: 2, cha: 1 }, traits: ['Draconic Ancestry', 'Breath Weapon', 'Damage Resistance'], languages: ['Common', 'Draconic'] },
    'Tiefling': { name: 'Tiefling', speed: 30, size: 'Medium', darkvision: true, abilityBonuses: { cha: 2, int: 1 }, traits: ['Darkvision', 'Hellish Resistance', 'Infernal Legacy'], languages: ['Common', 'Infernal'] },
    'Gnome': { name: 'Gnome', speed: 25, size: 'Small', darkvision: true, abilityBonuses: { int: 2 }, traits: ['Darkvision', 'Gnome Cunning'], languages: ['Common', 'Gnomish'], subraces: ['Forest Gnome', 'Rock Gnome'] },
    'Half-Elf': { name: 'Half-Elf', speed: 30, size: 'Medium', darkvision: true, abilityBonuses: { cha: 2 }, traits: ['Darkvision', 'Fey Ancestry', '+2 Skills', '+2 Ability Scores'], languages: ['Common', 'Elvish', 'Any One'] },
    'Half-Orc': { name: 'Half-Orc', speed: 30, size: 'Medium', darkvision: true, abilityBonuses: { str: 2, con: 1 }, traits: ['Darkvision', 'Menacing', 'Relentless Endurance', 'Savage Attacks'], languages: ['Common', 'Orc'] },
};

const CLASSES: Record<string, { name: string; hitDie: number; primaryAbility: string; savingThrows: string[]; armorProficiencies: string[]; weaponProficiencies: string[]; skillChoices: string[]; skillCount: number; startingEquipment: { weapons: string[]; equipment: string[] } }> = {
    'Barbarian': { name: 'Barbarian', hitDie: 12, primaryAbility: 'Strength', savingThrows: ['Strength', 'Constitution'], armorProficiencies: ['Light armor', 'Medium armor', 'Shields'], weaponProficiencies: ['Simple weapons', 'Martial weapons'], skillChoices: ['Animal Handling', 'Athletics', 'Intimidation', 'Nature', 'Perception', 'Survival'], skillCount: 2, startingEquipment: { weapons: ['Greataxe', 'Any simple melee weapon'], equipment: ["Explorer's pack", '4 Javelins'] } },
    'Bard': { name: 'Bard', hitDie: 8, primaryAbility: 'Charisma', savingThrows: ['Dexterity', 'Charisma'], armorProficiencies: ['Light armor'], weaponProficiencies: ['Simple weapons', 'Hand crossbows', 'Longswords', 'Rapiers', 'Shortswords'], skillChoices: ['Acrobatics', 'Animal Handling', 'Arcana', 'Athletics', 'Deception', 'History', 'Insight', 'Intimidation', 'Investigation', 'Medicine', 'Nature', 'Perception', 'Performance', 'Persuasion', 'Religion', 'Sleight of Hand', 'Stealth', 'Survival'], skillCount: 3, startingEquipment: { weapons: ['Rapier', 'Longsword', 'Any simple weapon'], equipment: ['Lute', 'Leather armor', 'Dagger'] } },
    'Cleric': { name: 'Cleric', hitDie: 8, primaryAbility: 'Wisdom', savingThrows: ['Wisdom', 'Charisma'], armorProficiencies: ['Light armor', 'Medium armor', 'Shields'], weaponProficiencies: ['Simple weapons'], skillChoices: ['History', 'Insight', 'Medicine', 'Persuasion', 'Religion'], skillCount: 2, startingEquipment: { weapons: ['Mace', 'Scale mail', 'Light crossbow & 20 bolts', 'Shield'], equipment: ['Holy symbol'] } },
    'Druid': { name: 'Druid', hitDie: 8, primaryAbility: 'Wisdom', savingThrows: ['Intelligence', 'Wisdom'], armorProficiencies: ['Light armor (nonmetal)', 'Medium armor (nonmetal)', 'Shields (nonmetal)'], weaponProficiencies: ['Clubs', 'Daggers', 'Javelins', 'Maces', 'Quarterstaffs', 'Scimitars', 'Slings', 'Spears'], skillChoices: ['Arcana', 'Animal Handling', 'Insight', 'Medicine', 'Nature', 'Perception', 'Religion', 'Survival'], skillCount: 2, startingEquipment: { weapons: ['Wooden shield', 'Scimitar'], equipment: ["Explorer's pack", 'Leather armor', 'Druidic focus'] } },
    'Fighter': { name: 'Fighter', hitDie: 10, primaryAbility: 'Strength or Dexterity', savingThrows: ['Strength', 'Constitution'], armorProficiencies: ['All armor', 'Shields'], weaponProficiencies: ['Simple weapons', 'Martial weapons'], skillChoices: ['Acrobatics', 'Animal Handling', 'Athletics', 'History', 'Insight', 'Intimidation', 'Perception', 'Survival'], skillCount: 2, startingEquipment: { weapons: ['Chain mail', 'Shield & longsword', 'Light crossbow & 20 bolts'], equipment: [] } },
    'Monk': { name: 'Monk', hitDie: 8, primaryAbility: 'Dexterity & Wisdom', savingThrows: ['Strength', 'Dexterity'], armorProficiencies: [], weaponProficiencies: ['Simple weapons', 'Shortswords'], skillChoices: ['Acrobatics', 'Athletics', 'History', 'Insight', 'Religion', 'Stealth'], skillCount: 2, startingEquipment: { weapons: ['Shortsword', 'Any simple weapon'], equipment: ['10 Darts'] } },
    'Paladin': { name: 'Paladin', hitDie: 10, primaryAbility: 'Strength & Charisma', savingThrows: ['Wisdom', 'Charisma'], armorProficiencies: ['All armor', 'Shields'], weaponProficiencies: ['Simple weapons', 'Martial weapons'], skillChoices: ['Athletics', 'Insight', 'Intimidation', 'Medicine', 'Persuasion', 'Religion'], skillCount: 2, startingEquipment: { weapons: ['Chain mail', 'Shield & longsword', '5 Javelins'], equipment: ['Holy symbol'] } },
    'Ranger': { name: 'Ranger', hitDie: 10, primaryAbility: 'Dexterity & Wisdom', savingThrows: ['Strength', 'Dexterity'], armorProficiencies: ['Light armor', 'Medium armor', 'Shields'], weaponProficiencies: ['Simple weapons', 'Martial weapons'], skillChoices: ['Animal Handling', 'Athletics', 'Insight', 'Investigation', 'Nature', 'Perception', 'Stealth', 'Survival'], skillCount: 3, startingEquipment: { weapons: ['Scale mail', '2 Shortswords', 'Longbow & 20 arrows'], equipment: [] } },
    'Rogue': { name: 'Rogue', hitDie: 8, primaryAbility: 'Dexterity', savingThrows: ['Dexterity', 'Intelligence'], armorProficiencies: ['Light armor'], weaponProficiencies: ['Simple weapons', 'Hand crossbows', 'Longswords', 'Rapiers', 'Shortswords'], skillChoices: ['Acrobatics', 'Athletics', 'Deception', 'Insight', 'Intimidation', 'Investigation', 'Perception', 'Performance', 'Persuasion', 'Sleight of Hand', 'Stealth'], skillCount: 4, startingEquipment: { weapons: ['Rapier', 'Shortsword', 'Shortbow & 20 arrows'], equipment: ["Thieves' tools", 'Leather armor', '2 Daggers'] } },
    'Sorcerer': { name: 'Sorcerer', hitDie: 6, primaryAbility: 'Charisma', savingThrows: ['Constitution', 'Charisma'], armorProficiencies: [], weaponProficiencies: ['Daggers', 'Darts', 'Slings', 'Quarterstaffs', 'Light crossbows'], skillChoices: ['Arcana', 'Deception', 'Insight', 'Intimidation', 'Persuasion', 'Religion'], skillCount: 2, startingEquipment: { weapons: ['Light crossbow & 20 bolts', 'Arcane focus'], equipment: ['2 Daggers'] } },
    'Warlock': { name: 'Warlock', hitDie: 8, primaryAbility: 'Charisma', savingThrows: ['Wisdom', 'Charisma'], armorProficiencies: ['Light armor'], weaponProficiencies: ['Simple weapons'], skillChoices: ['Arcana', 'Deception', 'History', 'Intimidation', 'Investigation', 'Nature', 'Religion'], skillCount: 2, startingEquipment: { weapons: ['Light crossbow & 20 bolts', 'Arcane focus'], equipment: ['Leather armor', 'Simple weapon', '2 Daggers'] } },
    'Wizard': { name: 'Wizard', hitDie: 6, primaryAbility: 'Intelligence', savingThrows: ['Intelligence', 'Wisdom'], armorProficiencies: [], weaponProficiencies: ['Daggers', 'Darts', 'Slings', 'Quarterstaffs', 'Light crossbows'], skillChoices: ['Arcana', 'History', 'Insight', 'Investigation', 'Medicine', 'Religion'], skillCount: 2, startingEquipment: { weapons: ['Quarterstaff', 'Arcane focus'], equipment: ['Spellbook'] } },
};

const SKILLS: Record<string, string> = {
    'Acrobatics': 'Dexterity', 'Animal Handling': 'Wisdom', 'Arcana': 'Intelligence', 'Athletics': 'Strength',
    'Deception': 'Charisma', 'History': 'Intelligence', 'Insight': 'Wisdom', 'Intimidation': 'Charisma',
    'Investigation': 'Intelligence', 'Medicine': 'Wisdom', 'Nature': 'Intelligence', 'Perception': 'Wisdom',
    'Performance': 'Charisma', 'Persuasion': 'Charisma', 'Religion': 'Intelligence', 'Sleight of Hand': 'Dexterity',
    'Stealth': 'Dexterity', 'Survival': 'Wisdom',
};

const BACKGROUNDS: Record<string, { skills: string[]; equipment: string[]; feature: string }> = {
    'Acolyte': { skills: ['Insight', 'Religion'], equipment: ['Holy symbol', 'Prayer book', '5 sticks of incense', 'Common clothes', '15 gp'], feature: 'Shelter of the Faithful' },
    'Charlatan': { skills: ['Deception', 'Sleight of Hand'], equipment: ['Fine clothes', 'Disguise kit', "Thieves' tools", '15 gp'], feature: 'False Identity' },
    'Criminal': { skills: ['Deception', 'Stealth'], equipment: ['Crowbar', "Thieves' tools", 'Common clothes', '15 gp'], feature: 'Criminal Contact' },
    'Entertainer': { skills: ['Acrobatics', 'Performance'], equipment: ['Musical instrument', "Entertainer's pack", 'Common clothes', '15 gp'], feature: 'By Popular Demand' },
    'Folk Hero': { skills: ['Animal Handling', 'Survival'], equipment: ["Artisan's tools", 'Shovel', 'Iron pot', 'Common clothes', '10 gp'], feature: 'Rustic Hospitality' },
    'Guild Artisan': { skills: ['Insight', 'Persuasion'], equipment: ["Artisan's tools", "Guild letter", "Traveler's clothes", '15 gp'], feature: 'Guild Membership' },
    'Hermit': { skills: ['Medicine', 'Religion'], equipment: ['Scroll case', 'Herbalism kit', "Winter blanket", 'Common clothes', '5 gp'], feature: 'Discovery' },
    'Noble': { skills: ['History', 'Persuasion'], equipment: ['Fine clothes', 'Signet ring', 'Scroll of pedigree', '25 gp'], feature: 'Position of Privilege' },
    'Outlander': { skills: ['Athletics', 'Survival'], equipment: ['Staff', 'Hunting trap', 'Animal trophy', "Traveler's clothes", '10 gp'], feature: 'Wanderer' },
    'Sage': { skills: ['Arcana', 'History'], equipment: ['Bottle of ink', 'Quill', 'Small knife', 'Common clothes', '10 gp'], feature: 'Researcher' },
    'Sailor': { skills: ['Athletics', 'Perception'], equipment: ['Belaying pin', '50 ft silk rope', "Lucky charm", 'Common clothes', '10 gp'], feature: "Ship's Passage" },
    'Soldier': { skills: ['Athletics', 'Intimidation'], equipment: ['Insignia of rank', 'Enemy trophy', 'Bone dice', "Traveler's clothes", '10 gp'], feature: 'Military Rank' },
    'Urchin': { skills: ['Sleight of Hand', 'Stealth'], equipment: ['Small knife', 'City map', 'Pet mouse', 'Common clothes', '10 gp'], feature: 'City Secrets' },
};

const ALIGNMENTS = ['Lawful Good', 'Neutral Good', 'Chaotic Good', 'Lawful Neutral', 'True Neutral', 'Chaotic Neutral', 'Lawful Evil', 'Neutral Evil', 'Chaotic Evil'];

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

const POINT_BUY_COSTS: Record<number, number> = { 8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9 };
const MAX_POINTS = 27;

// ==================== COMPONENT ====================

export const CharacterCreation: React.FC<CharacterCreationProps> = ({ userId, onComplete }) => {
    const [isLoading, setIsLoading] = useState(false);
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [step, setStep] = useState(1);
    const [portraitFile, setPortraitFile] = useState<File | null>(null);
    const [bgFile, setBgFile] = useState<File | null>(null);
    const [aiPortraitDesc, setAiPortraitDesc] = useState('');
    const [aiBgDesc, setAiBgDesc] = useState('');
    const [isGeneratingPortrait, setIsGeneratingPortrait] = useState(false);
    const [isGeneratingBg, setIsGeneratingBg] = useState(false);
    const portraitInputRef = useRef<HTMLInputElement>(null);
    const bgInputRef = useRef<HTMLInputElement>(null);

    const TOTAL_STEPS = 13;

    const [formData, setFormData] = useState({
        name: '',
        race: 'Human',
        subrace: '',
        char_class: 'Fighter',
        background: 'Soldier',
        alignment: 'True Neutral',
        baseStrength: 8, baseDexterity: 8, baseConstitution: 8,
        baseIntelligence: 8, baseWisdom: 8, baseCharisma: 8,
        chosenSkills: [] as string[],
        personalityTrait: '',
        ideal: '',
        bond: '',
        flaw: '',
        appearance: '',
        backstory: '',
        portrait_url: '',
        background_image_url: '',
    });

    const getModifier = (score: number) => Math.floor((score - 10) / 2);
    const raceData = useMemo(() => RACES[formData.race], [formData.race]);
    const classData = useMemo(() => CLASSES[formData.char_class], [formData.char_class]);
    const backgroundData = useMemo(() => BACKGROUNDS[formData.background], [formData.background]);

    const getFinalScore = (base: number, key: string) => base + (raceData?.abilityBonuses[key] || 0);
    const finalStr = getFinalScore(formData.baseStrength, 'str');
    const finalDex = getFinalScore(formData.baseDexterity, 'dex');
    const finalCon = getFinalScore(formData.baseConstitution, 'con');
    const finalInt = getFinalScore(formData.baseIntelligence, 'int');
    const finalWis = getFinalScore(formData.baseWisdom, 'wis');
    const finalCha = getFinalScore(formData.baseCharisma, 'cha');

    const pointsUsed = useMemo(() =>
        (POINT_BUY_COSTS[formData.baseStrength] || 0) + (POINT_BUY_COSTS[formData.baseDexterity] || 0) +
        (POINT_BUY_COSTS[formData.baseConstitution] || 0) + (POINT_BUY_COSTS[formData.baseIntelligence] || 0) +
        (POINT_BUY_COSTS[formData.baseWisdom] || 0) + (POINT_BUY_COSTS[formData.baseCharisma] || 0),
        [formData.baseStrength, formData.baseDexterity, formData.baseConstitution, formData.baseIntelligence, formData.baseWisdom, formData.baseCharisma]
    );
    const pointsRemaining = MAX_POINTS - pointsUsed;
    const calculateHP = () => classData.hitDie + getModifier(finalCon);
    const calculateAC = () => 10 + getModifier(finalDex);
    const proficiencyBonus = 2;

    const handleStatChange = (stat: string, delta: number) => {
        const key = `base${stat}` as keyof typeof formData;
        const current = formData[key] as number;
        const newValue = current + delta;
        if (newValue < 8 || newValue > 15) return;
        const currentCost = POINT_BUY_COSTS[current] || 0;
        const newCost = POINT_BUY_COSTS[newValue] || 0;
        if (delta > 0 && pointsRemaining < (newCost - currentCost)) return;
        setFormData(prev => ({ ...prev, [key]: newValue }));
    };

    const handleSkillToggle = (skill: string) => {
        setFormData(prev => {
            const chosen = prev.chosenSkills;
            const isClassSkill = classData.skillChoices.includes(skill);
            if (chosen.includes(skill)) return { ...prev, chosenSkills: chosen.filter(s => s !== skill) };
            if (!isClassSkill || chosen.length >= classData.skillCount) return prev;
            return { ...prev, chosenSkills: [...chosen, skill] };
        });
    };

    const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>, type: 'portrait' | 'background') => {
        const file = e.target.files?.[0];
        if (!file) return;
        if (!file.type.startsWith('image/')) return;
        if (file.size > 5 * 1024 * 1024) return; // 5MB limit

        const reader = new FileReader();
        reader.onloadend = () => {
            const result = reader.result as string;
            if (type === 'portrait') {
                setPortraitFile(file);
                setFormData(prev => ({ ...prev, portrait_url: result }));
            } else {
                setBgFile(file);
                setFormData(prev => ({ ...prev, background_image_url: result }));
            }
        };
        reader.readAsDataURL(file);
    };

    const handleAIGenerate = async (type: 'portrait' | 'background') => {
        const desc = type === 'portrait' ? aiPortraitDesc : aiBgDesc;
        if (!desc.trim()) return;

        const setGenerating = type === 'portrait' ? setIsGeneratingPortrait : setIsGeneratingBg;
        setGenerating(true);

        try {
            // Placeholder: uses a generated image service or Gemini
            // For now, create a placeholder URL that the user can replace
            const placeholderUrl = `https://image.pollinations.ai/prompt/${encodeURIComponent(desc + ' D&D fantasy art style, high quality, detailed')}`;
            setFormData(prev => ({
                ...prev,
                [type === 'portrait' ? 'portrait_url' : 'background_image_url']: placeholderUrl
            }));
        } catch (error) {
            console.error('AI generation failed:', error);
        } finally {
            setGenerating(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setErrors({});

        const newErrors: Record<string, string> = {};
        if (!formData.name.trim()) newErrors.name = 'Character name is required';
        if (formData.name.length < 2) newErrors.name = 'Name must be at least 2 characters';
        if (formData.chosenSkills.length === 0) newErrors.skills = 'Choose at least one skill';

        if (Object.keys(newErrors).length > 0) {
            setErrors(newErrors);
            setIsLoading(false);
            return;
        }

        const allSkills: Record<string, boolean> = {};
        formData.chosenSkills.forEach(s => { allSkills[s] = true; });
        backgroundData?.skills.forEach(s => { allSkills[s] = true; });

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
                trait: formData.personalityTrait, ideal: formData.ideal, bond: formData.bond, flaw: formData.flaw,
            }),
            max_hp: calculateHP(), current_hp: calculateHP(), armor_class: calculateAC(),
            speed: raceData.speed,
            stats: { strength: finalStr, dexterity: finalDex, constitution: finalCon, intelligence: finalInt, wisdom: finalWis, charisma: finalCha },
            abilities: racialTraits,
            inventory: classData.startingEquipment.weapons.concat(classData.startingEquipment.equipment),
        };

        try {
            const response = await axios.post('/api/v1/characters/', characterData);
            if (response.data.id) {
                await axios.post('/api/v1/profiles/', {
                    character_id: response.data.id,
                    alignment: formData.alignment,
                    background: formData.background,
                    appearance_description: formData.appearance,
                    deity: null, homeland: null,
                    hit_dice: `1d${classData.hitDie}`,
                    passive_wisdom: 10 + getModifier(finalWis),
                    inspiration: false,
                    saving_throws: { str: classData.savingThrows.includes('Strength') ? proficiencyBonus : 0, dex: classData.savingThrows.includes('Dexterity') ? proficiencyBonus : 0, con: classData.savingThrows.includes('Constitution') ? proficiencyBonus : 0, int: classData.savingThrows.includes('Intelligence') ? proficiencyBonus : 0, wis: classData.savingThrows.includes('Wisdom') ? proficiencyBonus : 0, cha: classData.savingThrows.includes('Charisma') ? proficiencyBonus : 0 },
                    skills: allSkills,
                    equipment: classData.startingEquipment.weapons.concat(classData.startingEquipment.equipment, backgroundData?.equipment || []),
                    attacks: classData.startingEquipment.weapons,
                    spell_slots: {},
                    features_traits: racialTraits,
                    notes: `Personality: ${formData.personalityTrait}\nIdeal: ${formData.ideal}\nBond: ${formData.bond}\nFlaw: ${formData.flaw}`,
                });
                onComplete();
            }
        } catch (error: any) {
            setIsLoading(false);
            setErrors({ submit: error.response?.data?.detail || 'Failed to create character' });
        }
    };

    const progress = ((step) / TOTAL_STEPS) * 100;

    // ==================== RENDER ====================
    return (
        <div className="character-creation-overlay">
            <div className="character-creation">
                <div className="cc-header">
                    <h2>Create Your Character</h2>
                    <p>Step {step} of {TOTAL_STEPS} — D&D 5e Rules</p>
                </div>

                {/* Linear Progress Bar */}
                <div className="cc-progress-bar">
                    <div className="progress-fill" style={{ width: `${progress}%` }}></div>
                    <span className="progress-label">{Math.round(progress)}%</span>
                </div>

                {errors.submit && (
                    <div className="cc-error"><span>⚠️</span><span>{errors.submit}</span></div>
                )}

                <form className="cc-form" onSubmit={handleSubmit}>

                    {/* ===== STEP 1: NAME ===== */}
                    {step === 1 && (
                        <div className="cc-section fade-in">
                            <h3>1. Character Name</h3>
                            <p className="step-description">Give your character a unique name for the campaign.</p>
                            <div className="form-group large">
                                <input
                                    type="text" id="name" name="name"
                                    value={formData.name}
                                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                                    placeholder="Enter your character name..."
                                    maxLength={50}
                                    className={errors.name ? 'error' : ''}
                                    autoFocus
                                />
                                {errors.name && <span className="error-message">{errors.name}</span>}
                            </div>
                            <div className="cc-actions">
                                <button type="button" className="cc-cancel" onClick={onComplete}>Cancel</button>
                                <button type="button" className="cc-next" onClick={() => setStep(2)} disabled={!formData.name.trim()}>Next →</button>
                            </div>
                        </div>
                    )}

                    {/* ===== STEP 2: RACE ===== */}
                    {step === 2 && (
                        <div className="cc-section fade-in">
                            <h3>2. Race</h3>
                            <p className="step-description">Your race determines your character's innate abilities, traits, and appearance.</p>
                            <div className="form-group large">
                                <select
                                    id="race"
                                    value={formData.race}
                                    onChange={(e) => setFormData(prev => ({ ...prev, race: e.target.value, subrace: '', selectedTraits: RACES[e.target.value]?.traits || [] }))}
                                >
                                    {Object.entries(RACES).map(([key, race]) => (
                                        <option key={key} value={key}>{race.name} — {Object.entries(race.abilityBonuses).map(([s, v]) => `${s.toUpperCase()} +${v}`).join(', ')}</option>
                                    ))}
                                </select>
                            </div>
                            {raceData.subraces && (
                                <div className="form-group large">
                                    <label>Subrace</label>
                                    <select id="subrace" value={formData.subrace} onChange={(e) => setFormData(prev => ({ ...prev, subrace: e.target.value }))}>
                                        <option value="">— None —</option>
                                        {raceData.subraces.map(sr => (<option key={sr} value={sr}>{sr}</option>))}
                                    </select>
                                </div>
                            )}
                            <div className="race-preview">
                                <div className="race-preview-item"><span>⚡ Speed</span><span>{raceData.speed} ft</span></div>
                                <div className="race-preview-item"><span>📏 Size</span><span>{raceData.size}</span></div>
                                {raceData.darkvision && <div className="race-preview-item"><span>👁️ Darkvision</span><span>60 ft</span></div>}
                            </div>
                            <div className="traits-list">
                                {raceData.traits.map(t => (<span key={t} className="trait-tag">✦ {t}</span>))}
                            </div>
                            <div className="cc-actions">
                                <button type="button" className="cc-back" onClick={() => setStep(1)}>← Back</button>
                                <button type="button" className="cc-next" onClick={() => setStep(3)}>Next →</button>
                            </div>
                        </div>
                    )}

                    {/* ===== STEP 3: CLASS ===== */}
                    {step === 3 && (
                        <div className="cc-section fade-in">
                            <h3>3. Class</h3>
                            <p className="step-description">Your class defines your character's role, combat style, and special abilities.</p>
                            <div className="form-group large">
                                <select
                                    id="char_class"
                                    value={formData.char_class}
                                    onChange={(e) => setFormData(prev => ({ ...prev, char_class: e.target.value, skillChoices: [] }))}
                                >
                                    {Object.entries(CLASSES).map(([key, cls]) => (
                                        <option key={key} value={key}>{cls.name} — HP: d{cls.hitDie}, Skills: {cls.skillCount}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="class-preview-grid">
                                <div className="class-preview-item"><span>❤️ Hit Die</span><span>d{classData.hitDie}</span></div>
                                <div className="class-preview-item"><span>🎯 Primary</span><span>{classData.primaryAbility}</span></div>
                                <div className="class-preview-item"><span>🛡️ Saves</span><span>{classData.savingThrows.join(', ')}</span></div>
                            </div>
                            <div className="proficiency-tags">
                                {classData.armorProficiencies.map(p => (<span key={p} className="prof-tag">{p}</span>))}
                                {classData.weaponProficiencies.map(p => (<span key={p} className="prof-tag">{p}</span>))}
                            </div>
                            <div className="cc-actions">
                                <button type="button" className="cc-back" onClick={() => setStep(2)}>← Back</button>
                                <button type="button" className="cc-next" onClick={() => setStep(4)}>Next →</button>
                            </div>
                        </div>
                    )}

                    {/* ===== STEP 4: BACKGROUND ===== */}
                    {step === 4 && (
                        <div className="cc-section fade-in">
                            <h3>4. Background</h3>
                            <p className="step-description">Your background represents your character's life before adventuring.</p>
                            <div className="form-group large">
                                <select
                                    id="background"
                                    value={formData.background}
                                    onChange={(e) => setFormData(prev => ({ ...prev, background: e.target.value }))}
                                >
                                    {Object.entries(BACKGROUNDS).map(([key, bg]) => (
                                        <option key={key} value={key}>{key} — Skills: {bg.skills.join(', ')}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="bg-preview">
                                <div className="bg-feature"><span>⭐ Feature</span><span>{backgroundData.feature}</span></div>
                                <h4>Starting Equipment</h4>
                                <div className="equipment-list">
                                    {backgroundData.equipment.map((item, i) => (
                                        <div key={i} className="equipment-item"><span className="equip-icon">📦</span><span>{item}</span></div>
                                    ))}
                                </div>
                            </div>
                            <div className="cc-actions">
                                <button type="button" className="cc-back" onClick={() => setStep(3)}>← Back</button>
                                <button type="button" className="cc-next" onClick={() => setStep(5)}>Next →</button>
                            </div>
                        </div>
                    )}

                    {/* ===== STEP 5: ALIGNMENT ===== */}
                    {step === 5 && (
                        <div className="cc-section fade-in">
                            <h3>5. Alignment</h3>
                            <p className="step-description">Alignment reflects your character's moral and ethical compass.</p>
                            <div className="alignment-grid">
                                {ALIGNMENTS.map(a => (
                                    <button
                                        key={a} type="button"
                                        className={`alignment-btn ${formData.alignment === a ? 'selected' : ''}`}
                                        onClick={() => setFormData(prev => ({ ...prev, alignment: a }))}
                                    >
                                        {a}
                                    </button>
                                ))}
                            </div>
                            <div className="cc-actions">
                                <button type="button" className="cc-back" onClick={() => setStep(4)}>← Back</button>
                                <button type="button" className="cc-next" onClick={() => setStep(6)}>Next →</button>
                            </div>
                        </div>
                    )}

                    {/* ===== STEP 6: ABILITY SCORES ===== */}
                    {step === 6 && (
                        <div className="cc-section fade-in">
                            <h3>6. Ability Scores</h3>
                            <p className="step-description">Distribute {MAX_POINTS} points using the Point Buy system. Range: 8–15 before racial bonuses.</p>
                            <p className="stat-points">
                                Points used: {pointsUsed}/{MAX_POINTS}
                                {pointsRemaining > 0 && <span className="points-remaining"> ({pointsRemaining} remaining)</span>}
                                {pointsRemaining <= 0 && <span className="points-max"> — Max reached!</span>}
                            </p>
                            <div className="stats-grid">
                                {[
                                    { label: 'Strength', key: 'Strength', bonusKey: 'str', base: formData.baseStrength, final: finalStr },
                                    { label: 'Dexterity', key: 'Dexterity', bonusKey: 'dex', base: formData.baseDexterity, final: finalDex },
                                    { label: 'Constitution', key: 'Constitution', bonusKey: 'con', base: formData.baseConstitution, final: finalCon },
                                    { label: 'Intelligence', key: 'Intelligence', bonusKey: 'int', base: formData.baseIntelligence, final: finalInt },
                                    { label: 'Wisdom', key: 'Wisdom', bonusKey: 'wis', base: formData.baseWisdom, final: finalWis },
                                    { label: 'Charisma', key: 'Charisma', bonusKey: 'cha', base: formData.baseCharisma, final: finalCha },
                                ].map(stat => {
                                    const racialBonus = raceData?.abilityBonuses[stat.bonusKey] || 0;
                                    return (
                                        <div key={stat.key} className="stat-control">
                                            <label className="stat-label">{stat.label}</label>
                                            <div className="stat-input">
                                                <button type="button" onClick={() => handleStatChange(stat.key, -1)} className="stat-btn minus" disabled={stat.base <= 8}>−</button>
                                                <div className="stat-value-group">
                                                    <span className="stat-value">{stat.base}</span>
                                                    {racialBonus > 0 && <span className="racial-bonus">+{racialBonus}</span>}
                                                    <span className="stat-final">= {stat.final}</span>
                                                </div>
                                                <button type="button" onClick={() => handleStatChange(stat.key, 1)} className="stat-btn plus" disabled={stat.base >= 15 || pointsRemaining <= 0}>+</button>
                                            </div>
                                            <span className="stat-modifier">Modifier: {getModifier(stat.final) >= 0 ? '+' : ''}{getModifier(stat.final)}</span>
                                        </div>
                                    );
                                })}
                            </div>
                            <div className="stat-summary">
                                <h4>Combat Preview</h4>
                                <div className="derived-stats">
                                    <div className="derived-stat"><span>❤️ HP</span><span className="value">{calculateHP()}</span></div>
                                    <div className="derived-stat"><span>🛡️ AC</span><span className="value">{calculateAC()}</span></div>
                                    <div className="derived-stat"><span>⚡ Initiative</span><span className="value">{getModifier(finalDex) >= 0 ? '+' : ''}{getModifier(finalDex)}</span></div>
                                    <div className="derived-stat"><span>👁️ Passive Wis</span><span className="value">{10 + getModifier(finalWis)}</span></div>
                                    <div className="derived-stat"><span>🏃 Speed</span><span className="value">{raceData.speed} ft</span></div>
                                    <div className="derived-stat"><span>🎯 Proficiency</span><span className="value">+{proficiencyBonus}</span></div>
                                </div>
                            </div>
                            <div className="cc-actions">
                                <button type="button" className="cc-back" onClick={() => setStep(5)}>← Back</button>
                                <button type="button" className="cc-next" onClick={() => setStep(7)}>Next →</button>
                            </div>
                        </div>
                    )}

                    {/* ===== STEP 7: SKILLS ===== */}
                    {step === 7 && (
                        <div className="cc-section fade-in">
                            <h3>7. Skills</h3>
                            <p className="step-description">Choose {classData.skillCount} skills from your class list. Background gives you {backgroundData?.skills.length} automatically.</p>
                            <div className="skill-category">
                                <h4>Background Skills (Fixed)</h4>
                                <div className="fixed-skills">
                                    {backgroundData?.skills.map(skill => (
                                        <div key={skill} className="fixed-skill-tag">{skill} <span className="skill-ability">({SKILLS[skill]?.slice(0, 3)})</span></div>
                                    ))}
                                </div>
                            </div>
                            <div className="skill-category">
                                <h4>Class Skills (Choose {classData.skillCount})</h4>
                                <div className="skills-grid">
                                    {classData.skillChoices.map(skill => {
                                        const isChosen = formData.chosenSkills.includes(skill);
                                        return (
                                            <button key={skill} type="button" className={`skill-btn ${isChosen ? 'chosen' : ''}`} onClick={() => handleSkillToggle(skill)}>
                                                <span className="skill-name">{skill}</span>
                                                <span className="skill-ability">{SKILLS[skill]?.slice(0, 3)}</span>
                                                {isChosen && <span className="skill-check">✓</span>}
                                            </button>
                                        );
                                    })}
                                </div>
                                <p className="choice-counter">Selected: {formData.chosenSkills.length}/{classData.skillCount}</p>
                            </div>
                            {errors.skills && <span className="error-message">{errors.skills}</span>}
                            <div className="cc-actions">
                                <button type="button" className="cc-back" onClick={() => setStep(6)}>← Back</button>
                                <button type="button" className="cc-next" onClick={() => setStep(8)}>Next →</button>
                            </div>
                        </div>
                    )}

                    {/* ===== STEP 8: PERSONALITY TRAIT ===== */}
                    {step === 8 && (
                        <div className="cc-section fade-in">
                            <h3>8. Personality Trait</h3>
                            <p className="step-description">A personality trait describes a distinctive quality of your character's behavior.</p>
                            <div className="form-group large">
                                <select id="personalityTrait" value={formData.personalityTrait} onChange={(e) => setFormData(prev => ({ ...prev, personalityTrait: e.target.value }))}>
                                    <option value="">— Select a trait —</option>
                                    {PERSONALITY_TRAITS.map((t, i) => (<option key={i} value={t}>{t}</option>))}
                                </select>
                            </div>
                            <div className="cc-actions">
                                <button type="button" className="cc-back" onClick={() => setStep(7)}>← Back</button>
                                <button type="button" className="cc-next" onClick={() => setStep(9)} disabled={!formData.personalityTrait}>Next →</button>
                            </div>
                        </div>
                    )}

                    {/* ===== STEP 9: IDEAL ===== */}
                    {step === 9 && (
                        <div className="cc-section fade-in">
                            <h3>9. Ideal</h3>
                            <p className="step-description">An ideal is a core principle or belief that drives your character.</p>
                            <div className="form-group large">
                                <select id="ideal" value={formData.ideal} onChange={(e) => setFormData(prev => ({ ...prev, ideal: e.target.value }))}>
                                    <option value="">— Select an ideal —</option>
                                    {IDEALS.map((t, i) => (<option key={i} value={t}>{t}</option>))}
                                </select>
                            </div>
                            <div className="cc-actions">
                                <button type="button" className="cc-back" onClick={() => setStep(8)}>← Back</button>
                                <button type="button" className="cc-next" onClick={() => setStep(10)} disabled={!formData.ideal}>Next →</button>
                            </div>
                        </div>
                    )}

                    {/* ===== STEP 10: BOND ===== */}
                    {step === 10 && (
                        <div className="cc-section fade-in">
                            <h3>10. Bond</h3>
                            <p className="step-description">A bond is a connection to something that motivates your character.</p>
                            <div className="form-group large">
                                <select id="bond" value={formData.bond} onChange={(e) => setFormData(prev => ({ ...prev, bond: e.target.value }))}>
                                    <option value="">— Select a bond —</option>
                                    {BONDS.map((t, i) => (<option key={i} value={t}>{t}</option>))}
                                </select>
                            </div>
                            <div className="cc-actions">
                                <button type="button" className="cc-back" onClick={() => setStep(9)}>← Back</button>
                                <button type="button" className="cc-next" onClick={() => setStep(11)} disabled={!formData.bond}>Next →</button>
                            </div>
                        </div>
                    )}

                    {/* ===== STEP 11: FLAW ===== */}
                    {step === 11 && (
                        <div className="cc-section fade-in">
                            <h3>11. Flaw</h3>
                            <p className="step-description">A flaw is a weakness or vulnerability that complicates your character's life.</p>
                            <div className="form-group large">
                                <select id="flaw" value={formData.flaw} onChange={(e) => setFormData(prev => ({ ...prev, flaw: e.target.value }))}>
                                    <option value="">— Select a flaw —</option>
                                    {FLAWS.map((t, i) => (<option key={i} value={t}>{t}</option>))}
                                </select>
                            </div>
                            <div className="cc-actions">
                                <button type="button" className="cc-back" onClick={() => setStep(10)}>← Back</button>
                                <button type="button" className="cc-next" onClick={() => setStep(12)} disabled={!formData.flaw}>Next →</button>
                            </div>
                        </div>
                    )}

                    {/* ===== STEP 12: APPEARANCE & BACKSTORY ===== */}
                    {step === 12 && (
                        <div className="cc-section fade-in">
                            <h3>12. Appearance & Backstory</h3>
                            <p className="step-description">Describe how your character looks and their history before adventuring.</p>
                            <div className="form-group large">
                                <label>Physical Description</label>
                                <textarea
                                    value={formData.appearance}
                                    onChange={(e) => setFormData(prev => ({ ...prev, appearance: e.target.value }))}
                                    placeholder="Height, build, hair color, eye color, scars, distinguishing features..."
                                    rows={4}
                                />
                            </div>
                            <div className="form-group large">
                                <label>Backstory (Optional)</label>
                                <textarea
                                    value={formData.backstory}
                                    onChange={(e) => setFormData(prev => ({ ...prev, backstory: e.target.value }))}
                                    placeholder="Tell the story of your character's life before the adventure began..."
                                    rows={5}
                                />
                            </div>
                            <div className="cc-actions">
                                <button type="button" className="cc-back" onClick={() => setStep(11)}>← Back</button>
                                <button type="button" className="cc-next" onClick={() => setStep(13)}>Next →</button>
                            </div>
                        </div>
                    )}

                    {/* ===== STEP 13: PORTRAIT & BACKGROUND IMAGE ===== */}
                    {step === 13 && (
                        <div className="cc-section fade-in">
                            <h3>13. Portrait & Background</h3>
                            <p className="step-description">Add a portrait and background image. Use a URL, upload a file, or generate with AI.</p>

                            {/* PORTRAIT */}
                            <div className="image-upload-section">
                                <h4>Character Portrait</h4>

                                <div className="upload-tabs">
                                    <input
                                        type="url"
                                        value={formData.portrait_url}
                                        onChange={(e) => setFormData(prev => ({ ...prev, portrait_url: e.target.value }))}
                                        placeholder="Paste image URL..."
                                        className="url-input"
                                    />
                                    <button type="button" className="upload-btn" onClick={() => portraitInputRef.current?.click()}>
                                        📁 Upload File
                                    </button>
                                    <input
                                        type="file"
                                        ref={portraitInputRef}
                                        accept="image/*"
                                        style={{ display: 'none' }}
                                        onChange={(e) => handleFileUpload(e, 'portrait')}
                                    />
                                </div>

                                <div className="ai-generate-row">
                                    <input
                                        type="text"
                                        value={aiPortraitDesc}
                                        onChange={(e) => setAiPortraitDesc(e.target.value)}
                                        placeholder="Describe portrait: 'Elven warrior with silver hair and glowing eyes'..."
                                        className="ai-desc-input"
                                    />
                                    <button
                                        type="button"
                                        className="ai-generate-btn"
                                        onClick={() => handleAIGenerate('portrait')}
                                        disabled={isGeneratingPortrait || !aiPortraitDesc.trim()}
                                    >
                                        {isGeneratingPortrait ? 'Generating...' : '✨ AI Generate'}
                                    </button>
                                    {formData.portrait_url && (
                                        <button
                                            type="button"
                                            className="ai-regenerate-btn"
                                            onClick={() => handleAIGenerate('portrait')}
                                            disabled={isGeneratingPortrait}
                                        >
                                            🔄 Regenerate
                                        </button>
                                    )}
                                </div>

                                {formData.portrait_url && (
                                    <div className="image-preview-large">
                                        <img src={formData.portrait_url} alt="Portrait" onError={(e) => (e.currentTarget.style.display = 'none')} />
                                    </div>
                                )}
                            </div>

                            {/* BACKGROUND */}
                            <div className="image-upload-section">
                                <h4>Background Image</h4>

                                <div className="upload-tabs">
                                    <input
                                        type="url"
                                        value={formData.background_image_url}
                                        onChange={(e) => setFormData(prev => ({ ...prev, background_image_url: e.target.value }))}
                                        placeholder="Paste background URL..."
                                        className="url-input"
                                    />
                                    <button type="button" className="upload-btn" onClick={() => bgInputRef.current?.click()}>
                                        📁 Upload File
                                    </button>
                                    <input
                                        type="file"
                                        ref={bgInputRef}
                                        accept="image/*"
                                        style={{ display: 'none' }}
                                        onChange={(e) => handleFileUpload(e, 'background')}
                                    />
                                </div>

                                <div className="ai-generate-row">
                                    <input
                                        type="text"
                                        value={aiBgDesc}
                                        onChange={(e) => setAiBgDesc(e.target.value)}
                                        placeholder="Describe background: 'Dark dungeon with torches and chains'..."
                                        className="ai-desc-input"
                                    />
                                    <button
                                        type="button"
                                        className="ai-generate-btn"
                                        onClick={() => handleAIGenerate('background')}
                                        disabled={isGeneratingBg || !aiBgDesc.trim()}
                                    >
                                        {isGeneratingBg ? 'Generating...' : '✨ AI Generate'}
                                    </button>
                                    {formData.background_image_url && (
                                        <button
                                            type="button"
                                            className="ai-regenerate-btn"
                                            onClick={() => handleAIGenerate('background')}
                                            disabled={isGeneratingBg}
                                        >
                                            🔄 Regenerate
                                        </button>
                                    )}
                                </div>

                                {formData.background_image_url && (
                                    <div className="image-preview-large bg-preview">
                                        <img src={formData.background_image_url} alt="Background" onError={(e) => (e.currentTarget.style.display = 'none')} />
                                    </div>
                                )}
                            </div>

                            <div className="cc-actions">
                                <button type="button" className="cc-back" onClick={() => setStep(12)}>← Back</button>
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
