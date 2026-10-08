import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CharacterPanel } from './CharacterPanel';
import * as gameStoreModule from '../store/gameStore';

describe('CharacterPanel Rich Items, Spells, and Interactivity', () => {
    const sendActionMock = vi.fn();
    const setActiveCharacterMock = vi.fn();

    const mockCharacter = {
        name: 'Cedric Ironfoot',
        race: 'Dwarf',
        char_class: 'Fighter',
        level: 3,
        current_hp: 28,
        max_hp: 28,
        armor_class: 18,
        speed: 25,
        stats: {
            strength: 16,
            dexterity: 12,
            constitution: 16,
            intelligence: 10,
            wisdom: 12,
            charisma: 8,
        },
        inventory: [
            {
                name: 'Длинный меч',
                is_equipped: true,
                type: 'weapon',
                damage_dice: '1d8',
                damage_type: 'Рубящий',
            },
            {
                name: 'Щит',
                is_equipped: true,
                type: 'shield',
                ac_bonus: '+2 КБ',
            },
            {
                name: 'Кольчуга',
                is_equipped: true,
                type: 'armor',
            },
            {
                name: 'Походный паск (3 дня)',
                is_equipped: false,
                type: 'gear',
            },
            {
                name: 'Зелье лечения',
                is_equipped: false,
                type: 'potion',
                quantity: 2,
            },
        ],
        abilities: [
            {
                name: 'Второе дыхание',
                type: 'Bonus Action',
                level: 0,
                healing_dice: '1d10+3',
                description: 'Восстанавливает 1d10 + уровень хитов.',
            },
            {
                name: 'Всплеск действий',
                type: 'Special',
                level: 0,
                description: 'Одно дополнительное действие в свой ход.',
            },
            {
                name: 'Огненный шар',
                type: 'Action',
                level: 3,
                damage_dice: '8d6',
                damage_type: 'Огонь',
                description: 'Взрыв пламени радиусом 20 футов.',
            },
        ],
    };

    const mockSession = {
        session_id: 'session-test',
        session_name: 'The Lost Crypt',
        players: [
            { character: mockCharacter, name: 'Cedric' },
            { character: { name: 'Faye Frostbeard', current_hp: 20, max_hp: 20 }, name: 'Faye' },
        ],
        npcs: [],
    };

    beforeEach(() => {
        vi.restoreAllMocks();
        sendActionMock.mockClear();
        setActiveCharacterMock.mockClear();

        vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
            activeCharacter: mockCharacter,
            session: mockSession,
            currentSession: mockSession,
            sendAction: sendActionMock,
            setActiveCharacter: setActiveCharacterMock,
            language: 'en',
            setLanguage: vi.fn(),
        } as any);
    });

    it('renders hero sheet tab with ability scores and rolls check on click', () => {
        render(<CharacterPanel />);
        expect(screen.getByText('Cedric Ironfoot')).toBeInTheDocument();
        expect(screen.getByText('28 / 28')).toBeInTheDocument();

        // Click STR check
        const strCard = screen.getByTitle(/Roll Strength Check/i);
        fireEvent.click(strCard);
        expect(sendActionMock).toHaveBeenCalledWith(
            expect.stringContaining('I roll a Strength check (+3)'),
            mockCharacter
        );
    });

    it('displays enriched item details and combat chips in Items tab', () => {
        render(<CharacterPanel />);
        
        // Switch to items tab
        const itemsTabBtn = screen.getByText(/Items \(5\)/i);
        fireEvent.click(itemsTabBtn);

        // Check item names exist
        expect(screen.getByText('Длинный меч')).toBeInTheDocument();
        expect(screen.getAllByText('Щит').length).toBeGreaterThanOrEqual(1);
        expect(screen.getByText('Кольчуга')).toBeInTheDocument();
        expect(screen.getByText('Походный паск (3 дня)')).toBeInTheDocument();
        expect(screen.getByText('Зелье лечения')).toBeInTheDocument();

        // Check combat stats chips
        expect(screen.getByText(/1d8 Рубящий/i)).toBeInTheDocument();
        expect(screen.getByText(/\+2 КБ/i)).toBeInTheDocument();
        expect(screen.getByText(/16 КБ/i)).toBeInTheDocument();
        expect(screen.getByText(/2d4 \+ 2/i)).toBeInTheDocument();
        expect(screen.getByText('×2')).toBeInTheDocument(); // Potion quantity
    });

    it('allows category filtering in Items tab', () => {
        render(<CharacterPanel />);
        fireEvent.click(screen.getByText(/Items \(5\)/i));

        // Filter by Potions
        const potionsFilter = screen.getByRole('button', { name: /🧪 Potions/i });
        fireEvent.click(potionsFilter);

        expect(screen.getByText('Зелье лечения')).toBeInTheDocument();
        expect(screen.queryByText('Длинный меч')).not.toBeInTheDocument();
        expect(screen.queryByText('Кольчуга')).not.toBeInTheDocument();
    });

    it('triggers interactive actions for items: drink potion, attack with weapon, unequip', () => {
        render(<CharacterPanel />);
        fireEvent.click(screen.getByText(/Items \(5\)/i));

        // Drink potion
        const drinkBtn = screen.getByRole('button', { name: /🧪 Drink/i });
        fireEvent.click(drinkBtn);
        expect(sendActionMock).toHaveBeenCalledWith(
            expect.stringContaining('I drink Зелье лечения and regain vitality!'),
            mockCharacter
        );

        // Attack with weapon
        const attackBtn = screen.getByRole('button', { name: /⚔️ Attack/i });
        fireEvent.click(attackBtn);
        expect(sendActionMock).toHaveBeenCalledWith(
            expect.stringContaining('I make an attack with my Длинный меч (1d8 Рубящий)!'),
            mockCharacter
        );

        // Unequip weapon
        const unequipButtons = screen.getAllByRole('button', { name: /Unequip/i });
        fireEvent.click(unequipButtons[0]);
        expect(sendActionMock).toHaveBeenCalledWith(
            'I unequip Длинный меч.',
            mockCharacter
        );
    });

    it('toggles expandable item dossier with description and properties', () => {
        render(<CharacterPanel />);
        fireEvent.click(screen.getByText(/Items \(5\)/i));

        // Toggle info for Longsword
        const infoButtons = screen.getAllByRole('button', { name: /📜 Info/i });
        fireEvent.click(infoButtons[0]);

        // Description and properties become visible
        expect(screen.getByText(/Классический стальной полуторный меч/i)).toBeInTheDocument();
        expect(screen.getByText(/Универсальное \(1d10\)/i)).toBeInTheDocument();
    });

    it('displays enriched spells and triggers casting and rolling effects', () => {
        render(<CharacterPanel />);
        
        // Switch to spells tab
        const spellsTabBtn = screen.getByText(/(Spells|Abilities) \(3\)/i);
        fireEvent.click(spellsTabBtn);

        expect(screen.getByText('Второе дыхание')).toBeInTheDocument();
        expect(screen.getByText('Всплеск действий')).toBeInTheDocument();
        expect(screen.getByText('Огненный шар')).toBeInTheDocument();

        // Check spell parameters
        expect(screen.getByText(/8d6 Огонь/i)).toBeInTheDocument();
        expect(screen.getByText(/1d10\+3/i)).toBeInTheDocument();

        // Cast Fireball
        const castButtons = screen.getAllByRole('button', { name: /✨ Cast/i });
        fireEvent.click(castButtons[2]); // Fireball
        expect(sendActionMock).toHaveBeenCalledWith(
            'I cast Огненный шар!',
            mockCharacter
        );

        // Roll Fireball damage
        const rollButtons = screen.getAllByRole('button', { name: /🎲 Roll/i });
        fireEvent.click(rollButtons[1]); // Fireball
        expect(sendActionMock).toHaveBeenCalledWith(
            expect.stringContaining('I roll the spell effect for Огненный шар (8d6)'),
            mockCharacter
        );
    });
});
