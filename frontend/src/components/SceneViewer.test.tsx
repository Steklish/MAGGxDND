import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SceneViewer } from './SceneViewer';
import * as gameStoreModule from '../store/gameStore';
import { SceneNode } from '../types/game';

describe('SceneViewer Tactical Battle Map & Grid Integration', () => {
    const mockScene: SceneNode = {
        name: 'The Drunken Dragon',
        description: 'A lively tavern with sturdy wooden tables.',
        center_position: { x: 10, y: 10 },
        dimensions: { x: 20, y: 20 },
        scale_unit: 'feet',
        objects: [
            {
                name: 'Oak Table',
                obj_type: 'prop',
                position: { x: 5, y: 5 },
                quantity: 1,
                is_equipped: false,
                short_summary: 'A sturdy table',
            } as any,
        ],
        battlemap_image_url: '/assets/maps/tavern_aerial_topdown.png',
        background_image_url: '/assets/maps/tavern_aerial_topdown.png',
    };

    const mockSession = {
        session_id: 'test-session-123',
        session_name: 'Quest of Valor',
        players: [
            {
                character: {
                    name: 'Kaelen',
                    race: 'Elf',
                    char_class: 'Ranger',
                    position: { x: 2, y: 3 },
                    current_hp: 25,
                    max_hp: 25,
                    armor_class: 14,
                    speed: 30,
                },
            },
        ],
        npcs: [
            {
                character: {
                    name: 'Goblin Scout',
                    char_class: 'Goblin',
                    alignment: 'Neutral Evil',
                    position: { x: 8, y: 8 },
                    current_hp: 7,
                    max_hp: 7,
                    armor_class: 12,
                    speed: 30,
                },
            },
        ],
    };

    beforeEach(() => {
        vi.restoreAllMocks();
    });

    it('renders empty state when currentScene is null', () => {
        vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
            currentScene: null,
            session: null,
            currentSession: null,
            sendAction: vi.fn(),
            activeCharacter: null,
            setCurrentScene: vi.fn(),
        } as any);

        render(<SceneViewer />);
        expect(screen.getByText('Tactical Battle Grid')).toBeInTheDocument();
        expect(screen.queryByTestId('tactical-map-background')).not.toBeInTheDocument();
    });

    it('renders tactical map background image beneath the grid with correct src and classes', () => {
        vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
            currentScene: mockScene,
            session: mockSession,
            currentSession: mockSession,
            sendAction: vi.fn(),
            activeCharacter: { name: 'Kaelen' },
            setCurrentScene: vi.fn(),
        } as any);

        render(<SceneViewer />);

        const mapBg = screen.getByTestId('tactical-map-background');
        expect(mapBg).toBeInTheDocument();
        expect(mapBg).toHaveClass('tactical-map-background');
        expect(mapBg).toHaveAttribute('src', '/assets/maps/tavern_aerial_topdown.png');
    });

    it('falls back to default placeholder if battlemap_image_url is not set', () => {
        const sceneWithoutMap: SceneNode = {
            ...mockScene,
            battlemap_image_url: undefined,
            background_image_url: undefined,
        };

        vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
            currentScene: sceneWithoutMap,
            session: mockSession,
            currentSession: mockSession,
            sendAction: vi.fn(),
            activeCharacter: { name: 'Kaelen' },
            setCurrentScene: vi.fn(),
        } as any);

        render(<SceneViewer />);

        const mapBg = screen.getByTestId('tactical-map-background');
        expect(mapBg).toBeInTheDocument();
        expect(mapBg).toHaveAttribute('src', '/assets/placeholders/battlemap_stone.svg');
    });

    it('renders the regenerate map button in toolbar', () => {
        vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
            currentScene: mockScene,
            session: mockSession,
            currentSession: mockSession,
            sendAction: vi.fn(),
            activeCharacter: null,
            setCurrentScene: vi.fn(),
        } as any);

        render(<SceneViewer />);

        const regenBtn = screen.getByTestId('regenerate-map-btn');
        expect(regenBtn).toBeInTheDocument();
        expect(regenBtn).toHaveTextContent('🎨 Gen Map');
    });

    it('triggers map regeneration API call and updates scene upon button click', async () => {
        const setCurrentSceneMock = vi.fn();

        vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
            currentScene: mockScene,
            session: mockSession,
            currentSession: mockSession,
            sendAction: vi.fn(),
            activeCharacter: null,
            setCurrentScene: setCurrentSceneMock,
        } as any);

        const newMapUrl = '/assets/maps/new_regenerated_battlemap.png';
        const fetchMock = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => ({
                status: 'ok',
                battlemap_image_url: newMapUrl,
                cached: false,
            }),
        });
        global.fetch = fetchMock;

        render(<SceneViewer />);

        const regenBtn = screen.getByTestId('regenerate-map-btn');
        fireEvent.click(regenBtn);

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledWith(
                '/api/v1/sessions/test-session-123/scene/regenerate-map',
                expect.objectContaining({
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                })
            );
        });

        await waitFor(() => {
            expect(setCurrentSceneMock).toHaveBeenCalledWith(
                expect.objectContaining({
                    battlemap_image_url: newMapUrl,
                    background_image_url: newMapUrl,
                })
            );
        });
    });

    it('renders tokens and grid overlay without disrupting background image', () => {
        vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
            currentScene: mockScene,
            session: mockSession,
            currentSession: mockSession,
            sendAction: vi.fn(),
            activeCharacter: { name: 'Kaelen' },
            setCurrentScene: vi.fn(),
        } as any);

        const { rerender } = render(<SceneViewer />);

        // Verify tokens are present
        expect(screen.getByText('K')).toBeInTheDocument(); // Kaelen initial
        expect(screen.getByText('G')).toBeInTheDocument(); // Goblin Scout initial

        const mapBg = screen.getByTestId('tactical-map-background');
        const initialSrc = mapBg.getAttribute('src');

        // Simulate token movement update in session
        const updatedSession = {
            ...mockSession,
            players: [
                {
                    character: {
                        ...mockSession.players[0].character,
                        position: { x: 4, y: 5 }, // moved
                    },
                },
            ],
        };

        vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
            currentScene: mockScene,
            session: updatedSession,
            currentSession: updatedSession,
            sendAction: vi.fn(),
            activeCharacter: { name: 'Kaelen' },
            setCurrentScene: vi.fn(),
        } as any);

        rerender(<SceneViewer />);

        // Verify map background src remains unchanged without reloading
        const updatedBg = screen.getByTestId('tactical-map-background');
        expect(updatedBg.getAttribute('src')).toBe(initialSrc);
    });

    describe('Tactical Context Menu on Tap', () => {
        it('opens tactical menu on grid cell tap with movement, exploration, and targeting options', () => {
            const sendActionMock = vi.fn();
            vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
                currentScene: mockScene,
                session: mockSession,
                currentSession: mockSession,
                sendAction: sendActionMock,
                activeCharacter: { name: 'Kaelen' },
                setCurrentScene: vi.fn(),
            } as any);

            const { container } = render(<SceneViewer />);
            const cell = container.querySelector('.tactical-cell[data-x="3"][data-y="4"]')!;
            expect(cell).toBeInTheDocument();

            fireEvent.click(cell);

            // Cell should now be marked selected
            expect(cell).toHaveClass('selected-cell', 'active-target-cell');

            // Floating tactical menu should appear
            const floatingMenu = screen.getByTestId('tactical-floating-menu');
            expect(floatingMenu).toBeInTheDocument();
            expect(screen.getAllByText(/Cell \(3, 4\)/i).length).toBeGreaterThan(0);

            // Contextual actions should be available
            expect(screen.getAllByText('Move Carefully').length).toBeGreaterThan(0);
            expect(screen.getAllByText('Sprint / Dash').length).toBeGreaterThan(0);
            expect(screen.getAllByText('Explore & Search').length).toBeGreaterThan(0);
            expect(screen.getAllByText('Take Cover').length).toBeGreaterThan(0);
            expect(screen.getAllByText('Target Area').length).toBeGreaterThan(0);

            // Click "Sprint / Dash"
            const sprintBtn = screen.getAllByText('Sprint / Dash')[0];
            fireEvent.click(sprintBtn);

            expect(sendActionMock).toHaveBeenCalledWith(
                'I sprint and dash to coordinate (3, 4).',
                { name: 'Kaelen' }
            );
        });

        it('opens object tactical menu with inspect, search, break, and cover actions', () => {
            const sendActionMock = vi.fn();
            vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
                currentScene: mockScene,
                session: mockSession,
                currentSession: mockSession,
                sendAction: sendActionMock,
                activeCharacter: { name: 'Kaelen' },
                setCurrentScene: vi.fn(),
            } as any);

            const { container } = render(<SceneViewer />);
            const objToken = container.querySelector('.object-token')!;
            expect(objToken).toBeInTheDocument();

            fireEvent.click(objToken);

            expect(screen.getByTestId('tactical-floating-menu')).toBeInTheDocument();
            expect(screen.getAllByText('Inspect & Examine').length).toBeGreaterThan(0);
            expect(screen.getAllByText('Open & Search').length).toBeGreaterThan(0);
            expect(screen.getAllByText('Force / Break').length).toBeGreaterThan(0);
            expect(screen.getAllByText('Use as Cover').length).toBeGreaterThan(0);

            // Click "Inspect & Examine"
            const inspectBtn = screen.getAllByText('Inspect & Examine')[0];
            fireEvent.click(inspectBtn);

            expect(sendActionMock).toHaveBeenCalledWith(
                'I inspect and examine Oak Table at coordinate (5, 5) for traps, runes, or mechanisms.',
                { name: 'Kaelen' }
            );
        });

        it('opens combat tactical menu for hostile NPC with attack, spell, threat, and intimidation', () => {
            const sendActionMock = vi.fn();
            vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
                currentScene: mockScene,
                session: mockSession,
                currentSession: mockSession,
                sendAction: sendActionMock,
                activeCharacter: { name: 'Kaelen' },
                setCurrentScene: vi.fn(),
            } as any);

            const { container } = render(<SceneViewer />);
            const npcToken = container.querySelector('.npc-token.hostile')!;
            expect(npcToken).toBeInTheDocument();

            fireEvent.click(npcToken);

            expect(screen.getByTestId('tactical-floating-menu')).toBeInTheDocument();
            expect(screen.getAllByText('Melee Attack').length).toBeGreaterThan(0);
            expect(screen.getAllByText('Ranged Attack').length).toBeGreaterThan(0);
            expect(screen.getAllByText('Cast Spell').length).toBeGreaterThan(0);
            expect(screen.getAllByText('Assess Threat').length).toBeGreaterThan(0);
            expect(screen.getAllByText('Intimidate / Parley').length).toBeGreaterThan(0);

            // Click "Melee Attack"
            const attackBtn = screen.getAllByText('Melee Attack')[0];
            fireEvent.click(attackBtn);

            expect(sendActionMock).toHaveBeenCalledWith(
                'I advance and make a melee attack against Goblin Scout.',
                { name: 'Kaelen' }
            );
        });

        it('opens defensive self tactical menu when clicking own token', () => {
            const sendActionMock = vi.fn();
            vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
                currentScene: mockScene,
                session: mockSession,
                currentSession: mockSession,
                sendAction: sendActionMock,
                activeCharacter: { name: 'Kaelen' },
                setCurrentScene: vi.fn(),
            } as any);

            const { container } = render(<SceneViewer />);
            const playerToken = container.querySelector('.player-token.self-token')!;
            expect(playerToken).toBeInTheDocument();

            fireEvent.click(playerToken);

            expect(screen.getByTestId('tactical-floating-menu')).toBeInTheDocument();
            expect(screen.getAllByText('Dodge Action').length).toBeGreaterThan(0);
            expect(screen.getAllByText('Disengage').length).toBeGreaterThan(0);
            expect(screen.getAllByText('Survey Field').length).toBeGreaterThan(0);

            // Click "Dodge Action"
            const dodgeBtn = screen.getAllByText('Dodge Action')[0];
            fireEvent.click(dodgeBtn);

            expect(sendActionMock).toHaveBeenCalledWith(
                'I take the Dodge action, focusing entirely on avoiding incoming attacks.',
                { name: 'Kaelen' }
            );
        });
    });
});
