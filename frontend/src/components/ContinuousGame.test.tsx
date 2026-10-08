import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import * as gameStoreModule from '../store/gameStore';
import { ChatPanel } from './ChatPanel';
import { SceneMenu } from './SceneMenu';
import { TurnQueue } from './TurnQueue';
import { GamePage } from '../pages/GamePage';

describe('Frontend Continuous Game Loop & Multi-Turn UI Integration', () => {
    const mockCharacter = {
        name: 'Valeros',
        char_class: 'Fighter',
        race: 'Human',
        level: 3,
        current_hp: 28,
        max_hp: 32,
        armor_class: 17,
        speed: 30,
        abilities: {
            str: 16,
            dex: 12,
            con: 14,
            int: 10,
            wis: 12,
            cha: 10,
        },
        image_url: '/assets/characters/valeros.png',
        spells: [
            { name: 'Second Wind', level: 0, description: 'Regain 1d10+3 HP as a bonus action.' }
        ],
        inventory: [
            { name: 'Longsword +1', quantity: 1, type: 'Weapon', description: 'Masterwork blade with glowing runes.' }
        ]
    };

    const mockScene = {
        name: 'The Sunken Crypt',
        description: 'Damp stone walls covered with luminescent moss and ancient hieroglyphs.',
        dimensions: { x: 25, y: 25 },
        scale_unit: 'feet',
        battlemap_image_url: '/assets/maps/sunken_crypt.png',
        objects: [
            {
                name: 'Carved Sarcophagus',
                obj_type: 'Interactable',
                position: { x: 8, y: 12 },
                description: 'An ornate stone coffin inscribed with draconic runes.',
                interactive: true
            },
            {
                name: 'Rusted Iron Chest',
                obj_type: 'Container',
                position: { x: 18, y: 5 },
                description: 'A padlocked chest buried partially in sand.',
                interactive: true
            }
        ]
    };

    const mockTurnQueue = [
        { character: 'Valeros', next_turn: 10, is_player: true },
        { character: 'Skeleton Archer', next_turn: 20, is_player: false },
        { character: 'Crypt Guardian', next_turn: 30, is_player: false }
    ];

    let mockStoreState: any;

    beforeEach(() => {
        vi.restoreAllMocks();

        // Mock scrollIntoView for JSDOM
        window.HTMLElement.prototype.scrollIntoView = vi.fn();

        mockStoreState = {
            username: 'Player_Valeros',
            isAuthenticated: true,
            activeCharacter: mockCharacter,
            currentSession: {
                session_id: 'session-cont-001',
                session_name: 'Crypt of Whispers',
                players: [{ character: mockCharacter }],
                current_scene: mockScene,
                turn_queue: mockTurnQueue,
                current_chapter: {
                    name: 'Chapter 1: The Tomb of the Wyrm',
                    description: 'Explore the sunken halls and locate the dragon seal.',
                    tasks: {
                        'Investigate the tomb entrance': true,
                        'Unlock the inner sanctuary': false
                    }
                }
            },
            currentScene: mockScene,
            turnQueue: mockTurnQueue,
            messages: [
                {
                    id: 'msg-1',
                    sender_name: 'GM',
                    text: 'The heavy stone door grinds open, revealing The Sunken Crypt. In the center rests a Carved Sarcophagus flanked by a Rusted Iron Chest.',
                    type: 'system',
                    timestamp: new Date().toISOString()
                }
            ],
            events: [],
            isDMThinking: false,
            sendAction: vi.fn(),
            addMessage: vi.fn(),
            setCurrentScene: vi.fn(),
            setActiveCharacter: vi.fn(),
            setTurnQueue: vi.fn(),
            connectWebSocket: vi.fn().mockResolvedValue(undefined),
            disconnectWebSocket: vi.fn(),
            language: 'en',
            setLanguage: vi.fn()
        };

        vi.spyOn(gameStoreModule, 'useGameStore').mockImplementation(((selector?: any) => {
            if (typeof selector === 'function') {
                return selector(mockStoreState);
            }
            return mockStoreState;
        }) as any);
    });

    it('Turn 1: processes player action and renders DM response with interactive keyword tags', async () => {
        render(<ChatPanel />);

        // Verify initial narrative message is rendered
        expect(screen.getByText(/The Sunken Crypt/)).toBeInTheDocument();

        // Simulate player submitting an investigation action
        const input = screen.getByPlaceholderText(/What does .* do/i);
        fireEvent.change(input, { target: { value: 'I carefully inspect the Carved Sarcophagus for hidden glyphs.' } });

        const sendBtn = screen.getByRole('button', { name: /^Act$/i });
        fireEvent.click(sendBtn);

        expect(mockStoreState.sendAction).toHaveBeenCalledWith(
            'I carefully inspect the Carved Sarcophagus for hidden glyphs.',
            mockCharacter
        );

        // Verify keyword tokenizer highlights keywords in the narrative bubble
        const keywordTags = document.querySelectorAll('.kw-tag');
        expect(keywordTags.length).toBeGreaterThan(0);
    });

    it('Turn 2: displays CharacterStatHoverCard when hovering over character avatar in chat', async () => {
        // Add a message from Valeros to have character avatar in chat
        mockStoreState.messages.push({
            id: 'msg-2',
            sender_name: 'Valeros',
            text: 'I ready my shield and advance.',
            type: 'player',
            timestamp: new Date().toISOString()
        });

        render(<ChatPanel />);

        // Hover over the avatar in the message row
        const avatars = document.querySelectorAll('.chat-avatar-wrapper');
        expect(avatars.length).toBeGreaterThan(0);

        const playerAvatar = avatars[avatars.length - 1];
        fireEvent.mouseEnter(playerAvatar);

        // Verify character stats card is rendered
        await waitFor(() => {
            expect(document.querySelector('.character-stat-card') || document.querySelector('.hover-tip-card')).toBeInTheDocument();
        });

        fireEvent.mouseLeave(playerAvatar);
    });

    it('Turn 3: SceneMenu displays interactive objects and executes quick room exploration actions', async () => {
        render(<SceneMenu />);

        // Verify scene title and objects
        expect(screen.getByText('The Sunken Crypt')).toBeInTheDocument();
        expect(screen.getByText('Carved Sarcophagus')).toBeInTheDocument();
        expect(screen.getByText('Rusted Iron Chest')).toBeInTheDocument();

        // Click "⚔️ Interact" on the Carved Sarcophagus
        const interactButtons = screen.getAllByRole('button', { name: /Interact/i });
        expect(interactButtons.length).toBeGreaterThan(0);
        fireEvent.click(interactButtons[0]);

        expect(mockStoreState.sendAction).toHaveBeenCalledWith(
            'I interact with Carved Sarcophagus at coordinate (8, 12).',
            mockCharacter
        );

        // Click room action: "🔍 Search Chamber"
        const searchRoomBtn = screen.getByRole('button', { name: /Search Chamber/i });
        fireEvent.click(searchRoomBtn);

        expect(mockStoreState.sendAction).toHaveBeenCalledWith(
            'I search the entire The Sunken Crypt for hidden doors, concealed treasure, or secret passages.',
            mockCharacter
        );
    });

    it('Turn 4: TurnQueue shows active combatant, initiative order badges, and tooltip details', () => {
        render(<TurnQueue />);

        // Verify turn queue combatants
        expect(screen.getByText('Valeros')).toBeInTheDocument();
        expect(screen.getByText('Skeleton Archer')).toBeInTheDocument();
        expect(screen.getByText('Crypt Guardian')).toBeInTheDocument();

        // Verify initiative order badges
        expect(screen.getByText('ACTING')).toBeInTheDocument();
        expect(screen.getAllByText('WAITING').length).toBe(2);
        expect(screen.getByText('#1')).toBeInTheDocument();
        expect(screen.getByText('#2')).toBeInTheDocument();
        expect(screen.getByText('#3')).toBeInTheDocument();
    });

    it('Turn 5: GamePage verifies draggable layout swapping, panel folding, and side tabs', async () => {
        localStorage.setItem('access_token', 'mock_token');
        localStorage.setItem('username', 'Player_Valeros');

        render(
            <MemoryRouter initialEntries={['/game/session-cont-001']}>
                <GamePage />
            </MemoryRouter>
        );

        // Verify main components are present in GamePage
        expect(screen.getByText('Crypt of Whispers')).toBeInTheDocument();
        expect(screen.getAllByText('The Sunken Crypt').length).toBeGreaterThan(0);

        // Verify folding Chronicle panel
        const foldChronicleBtn = screen.getByTitle(/Fold Chronicle/i);
        expect(foldChronicleBtn).toBeInTheDocument();
        fireEvent.click(foldChronicleBtn);

        // After folding, button should prompt to expand
        expect(screen.getByTitle(/Expand Chronicle/i)).toBeInTheDocument();

        // Re-expand Chronicle
        fireEvent.click(screen.getByTitle(/Expand Chronicle/i));
        expect(screen.getByTitle(/Fold Chronicle/i)).toBeInTheDocument();

        // Verify swapping panel order
        const swapBtn = screen.getAllByTitle(/Swap with/i)[0];
        fireEvent.click(swapBtn);

        // Verify Scene Dossier side tab opens SceneMenu drawer
        const sceneCrumb = screen.getByTitle(/Inspect Scene Dossier/i);
        fireEvent.click(sceneCrumb);

        await waitFor(() => {
            expect(document.querySelector('.side-drawer-container')).toBeInTheDocument();
            expect(screen.getByText('Scene Dossier')).toBeInTheDocument();
        });
    });
});
