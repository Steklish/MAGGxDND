import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SceneViewer } from './SceneViewer';
import * as gameStoreModule from '../store/gameStore';
import { SceneNode } from '../types/game';

describe('SceneViewer Empirical Stress & Boundary Verification', () => {
    const baseMockScene: SceneNode = {
        name: 'Ironhold Fortress Courtyard',
        description: 'A cobblestone courtyard flanked by granite bastions and weathered ramparts.',
        center_position: { x: 10, y: 10 },
        dimensions: { x: 20, y: 20 },
        scale_unit: 'feet',
        objects: [
            {
                name: 'Supply Crate',
                obj_type: 'container',
                position: { x: 2, y: 2 },
                quantity: 1,
                is_equipped: false,
                short_summary: 'Reinforced wooden crate',
            } as any,
            {
                name: 'Siege Ballista',
                obj_type: 'interactable',
                position: { x: 8, y: 8 },
                quantity: 1,
                is_equipped: false,
                short_summary: 'Heavy siege weapon',
            } as any,
        ],
        battlemap_image_url: '/assets/maps/courtyard_aerial_topdown.png',
        background_image_url: '/assets/maps/courtyard_aerial_topdown.png',
    };

    const baseMockSession = {
        session_id: 'stress-session-001',
        session_name: 'Siege of Ironhold',
        players: [
            {
                character: {
                    name: 'Valerius',
                    race: 'Human',
                    char_class: 'Paladin',
                    position: { x: 4, y: 4 },
                    current_hp: 36,
                    max_hp: 40,
                    armor_class: 18,
                    speed: 30,
                },
            },
        ],
        npcs: [
            {
                character: {
                    name: 'Orc Warlord',
                    char_class: 'Barbarian',
                    alignment: 'Chaotic Evil',
                    position: { x: 12, y: 12 },
                    current_hp: 55,
                    max_hp: 60,
                    armor_class: 15,
                    speed: 35,
                },
            },
        ],
    };

    beforeEach(() => {
        vi.restoreAllMocks();
    });

    describe('1. Dynamic Grid Dimensions & Cell Rendering', () => {
        it('renders 10x10 grid with exactly 100 cells and correct CSS template', () => {
            const scene10: SceneNode = {
                ...baseMockScene,
                dimensions: { x: 10, y: 10 },
            };

            vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
                currentScene: scene10,
                session: baseMockSession,
                currentSession: baseMockSession,
                sendAction: vi.fn(),
                activeCharacter: null,
                setCurrentScene: vi.fn(),
            } as any);

            const { container } = render(<SceneViewer />);
            const grid = container.querySelector('.tactical-grid');
            expect(grid).toBeInTheDocument();
            expect(grid).toHaveStyle({
                gridTemplateColumns: 'repeat(10, 1fr)',
                gridTemplateRows: 'repeat(10, 1fr)',
            });

            const cells = container.querySelectorAll('.tactical-cell');
            expect(cells).toHaveLength(100);
            expect(screen.getByText('10×10 feet')).toBeInTheDocument();
        });

        it('renders 20x20 grid with exactly 400 cells and correct CSS template', () => {
            const scene20: SceneNode = {
                ...baseMockScene,
                dimensions: { x: 20, y: 20 },
            };

            vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
                currentScene: scene20,
                session: baseMockSession,
                currentSession: baseMockSession,
                sendAction: vi.fn(),
                activeCharacter: null,
                setCurrentScene: vi.fn(),
            } as any);

            const { container } = render(<SceneViewer />);
            const cells = container.querySelectorAll('.tactical-cell');
            expect(cells).toHaveLength(400);
            expect(screen.getByText('20×20 feet')).toBeInTheDocument();
        });

        it('stress-tests 50x50 grid with 2500 cells without crashing', () => {
            const scene50: SceneNode = {
                ...baseMockScene,
                dimensions: { x: 50, y: 50 },
            };

            vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
                currentScene: scene50,
                session: baseMockSession,
                currentSession: baseMockSession,
                sendAction: vi.fn(),
                activeCharacter: null,
                setCurrentScene: vi.fn(),
            } as any);

            const startTime = performance.now();
            const { container } = render(<SceneViewer />);
            const renderDuration = performance.now() - startTime;

            const grid = container.querySelector('.tactical-grid');
            expect(grid).toBeInTheDocument();
            expect(grid).toHaveStyle({
                gridTemplateColumns: 'repeat(50, 1fr)',
                gridTemplateRows: 'repeat(50, 1fr)',
            });

            const cells = container.querySelectorAll('.tactical-cell');
            expect(cells).toHaveLength(2500);
            expect(screen.getByText('50×50 feet')).toBeInTheDocument();
            // Should render within a reasonable threshold (< 500ms in jsdom)
            expect(renderDuration).toBeLessThan(1000);
        });

        it('handles minimal 1x1 grid dimension cleanly with token clamping', () => {
            const scene1x1: SceneNode = {
                ...baseMockScene,
                dimensions: { x: 1, y: 1 },
            };

            vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
                currentScene: scene1x1,
                session: baseMockSession,
                currentSession: baseMockSession,
                sendAction: vi.fn(),
                activeCharacter: null,
                setCurrentScene: vi.fn(),
            } as any);

            const { container } = render(<SceneViewer />);
            const cells = container.querySelectorAll('.tactical-cell');
            expect(cells).toHaveLength(1);
            expect(screen.getByText('1×1 feet')).toBeInTheDocument();

            const playerToken = container.querySelector('.player-token');
            expect(playerToken).toBeInTheDocument();
            // Clamped to 0 (column 1, row 1)
            expect(playerToken).toHaveStyle({
                gridColumnStart: '1',
                gridRowStart: '1',
            });
        });

        it('renders non-square grid dimensions (e.g. 10x30 and 25x12) accurately', () => {
            const sceneNonSquare: SceneNode = {
                ...baseMockScene,
                dimensions: { x: 10, y: 30 },
            };

            vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
                currentScene: sceneNonSquare,
                session: baseMockSession,
                currentSession: baseMockSession,
                sendAction: vi.fn(),
                activeCharacter: null,
                setCurrentScene: vi.fn(),
            } as any);

            const { container } = render(<SceneViewer />);
            const grid = container.querySelector('.tactical-grid');
            expect(grid).toHaveStyle({
                gridTemplateColumns: 'repeat(10, 1fr)',
                gridTemplateRows: 'repeat(30, 1fr)',
            });

            const cells = container.querySelectorAll('.tactical-cell');
            expect(cells).toHaveLength(300);
            expect(screen.getByText('10×30 feet')).toBeInTheDocument();
        });

        it('safely falls back to default 20x20 when dimensions are invalid, non-positive, or missing', () => {
            const sceneInvalid: SceneNode = {
                ...baseMockScene,
                dimensions: { x: 0, y: -15 } as any,
            };

            vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
                currentScene: sceneInvalid,
                session: baseMockSession,
                currentSession: baseMockSession,
                sendAction: vi.fn(),
                activeCharacter: null,
                setCurrentScene: vi.fn(),
            } as any);

            const { container } = render(<SceneViewer />);
            const cells = container.querySelectorAll('.tactical-cell');
            expect(cells).toHaveLength(400); // 20x20 default
            expect(screen.getByText('20×20 feet')).toBeInTheDocument();
        });

        it('clamps extreme out-of-bounds token coordinates into valid grid boundaries', () => {
            const extremeSession = {
                ...baseMockSession,
                players: [
                    {
                        character: {
                            ...baseMockSession.players[0].character,
                            position: { x: 9999, y: 9999 }, // Far out of bounds
                        },
                    },
                ],
                npcs: [
                    {
                        character: {
                            ...baseMockSession.npcs[0].character,
                            position: { x: -500, y: -200 }, // Negative out of bounds
                        },
                    },
                ],
            };

            vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
                currentScene: { ...baseMockScene, dimensions: { x: 10, y: 10 } },
                session: extremeSession,
                currentSession: extremeSession,
                sendAction: vi.fn(),
                activeCharacter: null,
                setCurrentScene: vi.fn(),
            } as any);

            const { container } = render(<SceneViewer />);
            const playerToken = container.querySelector('.player-token');
            const npcToken = container.querySelector('.npc-token');

            // x: 9999 clamped to 9 -> gridColumnStart: 10
            // y: 9999 clamped to 9 -> gridRowStart: 10
            expect(playerToken).toHaveStyle({
                gridColumnStart: '10',
                gridRowStart: '10',
            });

            // x: -500 clamped to 0 -> gridColumnStart: 1
            // y: -200 clamped to 0 -> gridRowStart: 1
            expect(npcToken).toHaveStyle({
                gridColumnStart: '1',
                gridRowStart: '1',
            });
        });
    });

    describe('2. Fallback Behavior for Missing and Broken (404) Battle Map Images', () => {
        it('falls back to default SVG placeholder when battlemap_image_url is undefined, null, or empty', () => {
            const scenesWithMissing = [
                { ...baseMockScene, battlemap_image_url: undefined, background_image_url: undefined },
                { ...baseMockScene, battlemap_image_url: null, background_image_url: null },
                { ...baseMockScene, battlemap_image_url: '', background_image_url: '' },
            ];

            for (const sc of scenesWithMissing) {
                vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
                    currentScene: sc as any,
                    session: baseMockSession,
                    currentSession: baseMockSession,
                    sendAction: vi.fn(),
                    activeCharacter: null,
                    setCurrentScene: vi.fn(),
                } as any);

                const { unmount } = render(<SceneViewer />);
                const mapBg = screen.getByTestId('tactical-map-background');
                expect(mapBg).toBeInTheDocument();
                expect(mapBg).toHaveAttribute('src', '/assets/placeholders/battlemap_stone.svg');
                unmount();
            }
        });

        it('does not crash when battlemap image encounters a 404/network error event', () => {
            const scene404: SceneNode = {
                ...baseMockScene,
                battlemap_image_url: '/assets/maps/nonexistent_404_error.png',
                background_image_url: '/assets/maps/nonexistent_404_error.png',
            };

            vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
                currentScene: scene404,
                session: baseMockSession,
                currentSession: baseMockSession,
                sendAction: vi.fn(),
                activeCharacter: null,
                setCurrentScene: vi.fn(),
            } as any);

            render(<SceneViewer />);
            const mapBg = screen.getByTestId('tactical-map-background');
            expect(mapBg).toBeInTheDocument();
            expect(mapBg).toHaveAttribute('src', '/assets/maps/nonexistent_404_error.png');

            // Trigger image load error event (simulating 404 or network failure)
            expect(() => {
                fireEvent.error(mapBg);
            }).not.toThrow();

            // Component remains completely operational and mounted
            expect(screen.getByTestId('tactical-map-background')).toBeInTheDocument();
            expect(screen.getByText('Valerius'.charAt(0))).toBeInTheDocument();
        });
    });

    describe('3. Rapid Token Updates & Background Stability (Anti-Flicker / No Unmounting)', () => {
        it('preserves exact DOM image node and src across 50 rapid token updates', () => {
            let currentSessionState = { ...baseMockSession };

            const storeMock = {
                currentScene: baseMockScene,
                session: currentSessionState,
                currentSession: currentSessionState,
                sendAction: vi.fn(),
                activeCharacter: { name: 'Valerius' },
                setCurrentScene: vi.fn(),
            };

            const storeSpy = vi.spyOn(gameStoreModule, 'useGameStore').mockImplementation(() => storeMock as any);

            const { rerender } = render(<SceneViewer />);

            const originalImg = screen.getByTestId('tactical-map-background');
            const originalSrc = originalImg.getAttribute('src');
            expect(originalSrc).toBe('/assets/maps/courtyard_aerial_topdown.png');

            // Simulate 50 rapid sequential token movement ticks
            for (let step = 1; step <= 50; step++) {
                const nextX = (4 + step) % 20;
                const nextY = (4 + Math.floor(step / 2)) % 20;

                const updatedSession = {
                    ...currentSessionState,
                    players: [
                        {
                            character: {
                                ...currentSessionState.players[0].character,
                                position: { x: nextX, y: nextY },
                            },
                        },
                    ],
                };

                storeMock.session = updatedSession;
                storeMock.currentSession = updatedSession;
                rerender(<SceneViewer />);

                // 1. Image element identity MUST be preserved (no unmount/re-mount)
                const currentImg = screen.getByTestId('tactical-map-background');
                expect(currentImg).toBe(originalImg);

                // 2. Image src MUST NOT flicker or mutate
                expect(currentImg.getAttribute('src')).toBe(originalSrc);

                // 3. Token position MUST accurately update in grid styles
                const playerToken = document.querySelector('.player-token');
                expect(playerToken).toHaveStyle({
                    gridColumnStart: `${nextX + 1}`,
                    gridRowStart: `${nextY + 1}`,
                });
            }
        });
    });

    describe('4. Zoom Scaling Transform Interactions', () => {
        it('handles zoom in, zoom out, reset, and clamp bounds properly', () => {
            vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
                currentScene: baseMockScene,
                session: baseMockSession,
                currentSession: baseMockSession,
                sendAction: vi.fn(),
                activeCharacter: null,
                setCurrentScene: vi.fn(),
            } as any);

            const { container } = render(<SceneViewer />);
            const zoomContainer = container.querySelector('.grid-zoom-container');
            const zoomInBtn = screen.getByTitle('Zoom In');
            const zoomOutBtn = screen.getByTitle('Zoom Out');
            const resetBtn = screen.getByTitle('Reset Zoom');

            // Default zoom 1.0 (100%)
            expect(screen.getByText('100%')).toBeInTheDocument();
            expect(zoomContainer).toHaveStyle({ transform: 'scale(1)' });

            // Zoom In (+ 0.15) -> 1.15 (115%)
            fireEvent.click(zoomInBtn);
            expect(screen.getByText('115%')).toBeInTheDocument();
            expect(zoomContainer).toHaveStyle({ transform: 'scale(1.15)' });

            // Multiple Zoom In -> should clamp at 2.0 (200%)
            for (let i = 0; i < 10; i++) {
                fireEvent.click(zoomInBtn);
            }
            expect(screen.getByText('200%')).toBeInTheDocument();
            expect(zoomContainer).toHaveStyle({ transform: 'scale(2)' });

            // Reset Zoom
            fireEvent.click(resetBtn);
            expect(screen.getByText('100%')).toBeInTheDocument();
            expect(zoomContainer).toHaveStyle({ transform: 'scale(1)' });

            // Zoom Out (- 0.15) -> 0.85 (85%)
            fireEvent.click(zoomOutBtn);
            expect(screen.getByText('85%')).toBeInTheDocument();
            expect(zoomContainer).toHaveStyle({ transform: 'scale(0.85)' });

            // Multiple Zoom Out -> should clamp at 0.6 (60%)
            for (let i = 0; i < 10; i++) {
                fireEvent.click(zoomOutBtn);
            }
            expect(screen.getByText('60%')).toBeInTheDocument();
            expect(zoomContainer).toHaveStyle({ transform: 'scale(0.6)' });
        });
    });

    describe('5. Entity Interactions & Inspector Drawer', () => {
        it('opens inspector on token click and closes cleanly', () => {
            const sendActionMock = vi.fn();
            vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
                currentScene: baseMockScene,
                session: baseMockSession,
                currentSession: baseMockSession,
                sendAction: sendActionMock,
                activeCharacter: { name: 'Valerius' },
                setCurrentScene: vi.fn(),
            } as any);

            const { container } = render(<SceneViewer />);
            const playerToken = container.querySelector('.player-token')!;
            fireEvent.click(playerToken);

            // Drawer should appear with stats
            expect(screen.getByText('Coord: (4, 4)')).toBeInTheDocument();
            expect(screen.getByText('HP:')).toBeInTheDocument();
            expect(screen.getByText('36/40')).toBeInTheDocument();
            expect(screen.getByText('AC:')).toBeInTheDocument();
            expect(screen.getByText('18')).toBeInTheDocument();

            // Click target button
            const targetBtn = screen.getByText('🎯 Target in Action');
            fireEvent.click(targetBtn);
            expect(sendActionMock).toHaveBeenCalledWith('I target Valerius with my action.', { name: 'Valerius' });

            // Close inspector
            const closeBtn = screen.getByText('✕');
            fireEvent.click(closeBtn);
            expect(screen.queryByText('Coord: (4, 4)')).not.toBeInTheDocument();
        });

        it('inspects object tokens with correct glyph and handles interaction action', () => {
            const sendActionMock = vi.fn();
            vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
                currentScene: baseMockScene,
                session: baseMockSession,
                currentSession: baseMockSession,
                sendAction: sendActionMock,
                activeCharacter: { name: 'Valerius' },
                setCurrentScene: vi.fn(),
            } as any);

            const { container } = render(<SceneViewer />);
            const objectTokens = container.querySelectorAll('.object-token');
            expect(objectTokens).toHaveLength(2);

            // Click first object (Supply Crate at 2, 2)
            fireEvent.click(objectTokens[0]);
            expect(screen.getByText('Supply Crate')).toBeInTheDocument();
            expect(screen.getByText('Coord: (2, 2)')).toBeInTheDocument();

            // Click target action for object
            const targetBtn = screen.getByText('🎯 Target in Action');
            fireEvent.click(targetBtn);
            expect(sendActionMock).toHaveBeenCalledWith(
                'I interact with Supply Crate at coordinate (2, 2).',
                { name: 'Valerius' }
            );
        });
    });

    describe('6. Map Regeneration Error Handling & State Resilience', () => {
        it('handles network failure during map regeneration without breaking the UI', async () => {
            vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
                currentScene: baseMockScene,
                session: baseMockSession,
                currentSession: baseMockSession,
                sendAction: vi.fn(),
                activeCharacter: null,
                setCurrentScene: vi.fn(),
            } as any);

            const fetchMock = vi.fn().mockRejectedValue(new Error('Network connection timeout'));
            global.fetch = fetchMock;

            render(<SceneViewer />);
            const regenBtn = screen.getByTestId('regenerate-map-btn');
            fireEvent.click(regenBtn);

            await waitFor(() => {
                expect(fetchMock).toHaveBeenCalled();
            });

            // Button should recover from loading state back to enabled
            await waitFor(() => {
                expect(regenBtn).not.toBeDisabled();
                expect(regenBtn).toHaveTextContent('🎨 Gen Map');
            });

            // Tactical map background remains intact
            const mapBg = screen.getByTestId('tactical-map-background');
            expect(mapBg).toHaveAttribute('src', '/assets/maps/courtyard_aerial_topdown.png');
        });

        it('handles HTTP 500 error response during map regeneration', async () => {
            vi.spyOn(gameStoreModule, 'useGameStore').mockReturnValue({
                currentScene: baseMockScene,
                session: baseMockSession,
                currentSession: baseMockSession,
                sendAction: vi.fn(),
                activeCharacter: null,
                setCurrentScene: vi.fn(),
            } as any);

            const fetchMock = vi.fn().mockResolvedValue({
                ok: false,
                status: 500,
                json: async () => ({ detail: 'Internal GenAI API Error' }),
            });
            global.fetch = fetchMock;

            render(<SceneViewer />);
            const regenBtn = screen.getByTestId('regenerate-map-btn');
            fireEvent.click(regenBtn);

            await waitFor(() => {
                expect(fetchMock).toHaveBeenCalled();
            });

            await waitFor(() => {
                expect(regenBtn).not.toBeDisabled();
                expect(regenBtn).toHaveTextContent('🎨 Gen Map');
            });
        });
    });
});
