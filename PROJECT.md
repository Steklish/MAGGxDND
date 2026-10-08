# Project: MAGGxDND Modernization & Visual Asset System

## Architecture
MAGGxDND is an interactive AI-assisted tabletop RPG application featuring a FastAPI Python backend and a React 19 / TypeScript / Zustand frontend.
- **Backend Architecture**:
  - FastAPI server (`backend/main.py`) running via Uvicorn.
  - Domain models in `core/schemas/in_game.py` (`Character`, `UnifiedObject`, `SceneNode`, `CharacterProfile`).
  - Session and profile persistence in SQLite (`data/maggxdnd.db`) and file saves (`saves/*.json`).
  - **Dynamic Scene & World Graph Engine (`core/game/engine.py`)**:
    - Automatic generation of starting scene with thematic interactive objects and initial location-pinned NPCs upon session creation.
    - Campaign plot and chapter task generation (`Plot`, `Chapter`).
    - Visited locations maintained as an undirected graph (`location_graph`, `all_locations`).
    - Traveling to unvisited locations procedurally generates new scene nodes, interactive objects, and pins new NPCs; traveling to previously visited locations loads existing cached scenes without duplication.
  - **Location-Pinned NPC Processing**:
    - NPCs are anchored to specific scenes (`npc.character.current_scene`).
    - The engine processes NPC actions and reactions ONLY when they are present in the party's current location (`current_location_name`). Off-screen NPCs remain dormant.
  - **Omniscient AI Dungeon Master (MAGG)**:
    - DM context injects overarching campaign plot, chapter tasks, current scene objects & positions, visited world graph topology, PCs & NPCs present, and off-screen characters in other locations.
  - **Dual-Mode Event & Turn Queues**:
    - *Story Mode*: Free-form party action queue. Player action -> Location-present NPCs process event queue reactions -> DM narratively comments and evaluates plot advancement.
    - *Combat Mode*: Strict initiative/speed time-sliced turn queue (`turn_queue` with `RoundDeterminator`). Dormant off-scene NPCs are skipped.
  - **Adventurer Entrance & NPC Takeover System**:
    - Dynamic entrance narratives ("how exactly they entered the game") generated and broadcast when a player joins or claims a character.
    - Abandoned player characters seamlessly convert to AI companion NPCs.
    - New or rejoining players can claim AI companion characters or promote existing session NPCs into player-controlled characters.
  - Google GenAI SDK (`google-genai` 2.28.0) used for Gemini text storytelling and Imagen visual generation.
  - Dedicated asset repository (`data/assets/`) served via FastAPI static mounts (`/assets` and `/api/v1/assets`).
  - Asynchronous background task pipeline for non-blocking image generation with WebSocket broadcast updates.
- **Frontend Architecture**:
  - React 19 + TypeScript + Vite 6 + Zustand 5.
  - Glassmorphism UI design system with backdrop-filter, translucent containers, glowing accents, and dark theme palette.
  - Dockable and collapsible drawers for Hero Sheet, Tactical Inspector, and Dice Tray.
  - Tactical battle map (`SceneViewer.tsx`) with an underlying aerial terrain background image layer beneath an interactive DOM CSS grid.
  - Visual asset displays for character portraits, item cards, atmospheric scene headers, and battle map backgrounds.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Model Schema Extension | Add `image_url` to `Character`, `UnifiedObject`, `SceneNode`, and `CharacterProfile` | M1 | R2, Survey BE |
| 2 | Asset Storage & Static Serving | Dedicated `data/assets/` directory served via FastAPI static mount at `/assets` and `/api/v1/assets` | M1 | R4, Survey BE |
| 3 | Google GenAI Image Generator | Service utilizing `google-genai` for characters, items, scenes with prompt synthesis and disk caching | M1 | R2, R4, Survey BE |
| 4 | Fallback Placeholder System | Pre-bundled thematic SVG placeholders for all entity types when API fails or is offline | M1 | R2, R4, Survey BE |
| 5 | Asynchronous Image Pipeline | Background non-blocking image generation during session initialization and actions | M1 | R2, Survey BE |
| 6 | Aerial Battle Map Generator | Top-down orthographic prompt engineering matching scene dimensions, terrain, and obstacles | M2 | R3, Survey Map |
| 7 | Tactical Grid Background Layer | SceneViewer background image layer positioned under DOM grid with cell alignment | M2 | R3, Survey Map |
| 8 | Map Persistence & Cache | Preserve battle map background across token moves/turns, regenerate on scene change | M2 | R3, Survey Map |
| 9 | World Location Graph & Transitions | Dynamic scene creation for new locations, caching for visited, graph edge connections, and location transition REST API | M2 | User Req |
| 10 | Location-Pinned NPC Processing | NPCs bound to scenes; engine only processes turns/reactions for NPCs in the party's current location | M2 | User Req |
| 11 | DM Omniscience Context Engine | Full context feeding: plot, quest objectives, world graph topology, present & off-screen characters, and interactive objects | M2 | User Req |
| 12 | Dual-Mode Turn & Event Queues | Story mode party event reaction loop vs Combat mode initiative time-slice queue | M2 | User Req |
| 13 | Dynamic Entrance Narratives & Claiming | AI entrance narration on player join; player abandonment converts to AI; roster takeover of AI/NPCs | M2 | User Req |
| 14 | Glassmorphism UI System | Sleek dark translucent theme with backdrop blur, borders, and polished screen real estate | M3 | R1, Survey FE |
| 15 | Dockable Hero Sheet Drawer | Dual-mode Hero Sheet (docked column vs slide-over drawer) with collapse controls | M3 | R1, Survey FE |
| 16 | Ergonomic Tactical Inspector | Modular inspector docking into side panel or floating minimizable glass HUD pill | M3 | R1, Survey FE |
| 17 | Unified Smooth Dice Tray | Single dockable/slide-over dice tray integrated with action hotbar and header | M3 | R1, Survey FE |
| 18 | Viewport Layout Optimization | Map, Chronicle, and Action Deck coexistence without overlapping or awkward scrolling | M3 | R1, Survey FE |
| 19 | Visual Artwork Components | Render portraits in hero sheet, tokens, item cards, and narrative scene headers | M3 | R2, Survey FE |
| 20 | Backend Test Suite | Automated pytest suite for models, image endpoints, asset serving, and caching | M4 | AC, Survey Map |
| 21 | E2E Browser Test Suite | Automated Playwright headless suite covering 4 tiers with zero console errors | M4 | AC, Survey Map |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1: Backend Image Gen & Asset Infra | Schema extension, static asset serving, GenAI service, async task pipeline, fallbacks | none | DONE |
| 2 | M2: World Graph, Engine & Battle Map | Aerial map gen, location graph, location-pinned NPCs, DM omniscience, entrance narratives, NPC claiming | M1 | DONE |
| 3 | M3: Glassmorphism UI & Dockable Drawers | Glassmorphism design, dockable drawers, unified viewport layout, artwork integration | M1, M2 | DONE |
| 4 | M4: E2E Verification & Test Suite | 100% automated test suite execution, Playwright browser verification, zero console errors | M1, M2, M3 | IN_PROGRESS |

## Interface Contracts
### Backend Static & Image Generation API ↔ Frontend
- **Static Assets Endpoint**: `GET /assets/{category}/{filename}` and `GET /api/v1/assets/{category}/{filename}`
  - Categories: `characters/`, `items/`, `scenes/`, `maps/`, `placeholders/`
- **Image Generation Endpoints**:
  - `POST /api/v1/assets/generate`:
    - Request: `{"entity_type": "character"|"item"|"scene"|"battlemap", "entity_id": str, "description": str, "metadata": dict}`
    - Response: `{"status": "completed"|"processing", "image_url": str, "cached": bool}`
  - `POST /api/v1/sessions/{session_id}/scene/regenerate-map`:
    - Response: `{"status": "ok", "battlemap_image_url": str}`
- **Entity Schemas**:
  - `Character.image_url: Optional[str]`
  - `UnifiedObject.image_url: Optional[str]`
  - `SceneNode.image_url: Optional[str]`
  - `SceneNode.battlemap_image_url: Optional[str]`

### SceneViewer ↔ Tactical Grid Background
- `currentScene.battlemap_image_url` or `currentScene.background_image_url` feeds underlying `<img className="tactical-map-background" />` positioned behind `.tactical-grid`.
- Tokens render on `.tactical-grid` with `z-index: 5` to `10`.
- Token moves update coordinates in Zustand `gameStore` without triggering background image reload.

### World Location Graph & Character Claiming Endpoints
- **Transition Location**:
  - `POST /sessions/{session_id}/transition-location`
  - Request: `{"location_name": str, "description": Optional[str]}`
  - Response: `{"status": "ok", "current_location_name": str, "is_new_location": bool, "all_locations": list[str], "connected_locations": list[str], "scene": dict, "npcs_present": list[str]}`
- **Roster & Claiming**:
  - `GET /sessions/{session_id}/roster`: returns PCs and session NPCs with `can_claim=True`
  - `POST /sessions/{session_id}/claim-character`: claims AI companion or promotes NPC to player with dynamic entrance narration

## Code Layout
- `backend/src/services/image_gen_service.py` — GenAI image generation service, prompt builder, disk caching
- `backend/src/services/asset_manager.py` — Local asset directory manager, fallback SVG generator/provider
- `backend/src/api/routers/assets_router.py` — REST endpoints for asset retrieval and manual generation triggers
- `core/schemas/in_game.py` — Schema definitions for Character, UnifiedObject, SceneNode
- `frontend/src/components/GameLayout.tsx` — Main game viewport, drawer docking orchestration
- `frontend/src/components/GameLayout.css` — Glassmorphism styles, drawer transitions, layout grid
- `frontend/src/components/SceneViewer.tsx` — Tactical battle map, grid canvas, background layer
- `frontend/src/components/SceneViewer.css` — Map styling, tactical background alignment
- `frontend/src/components/CharacterPanel.tsx` — Hero sheet, item cards with artwork, portrait display
- `frontend/src/components/TacticalInspector.tsx` — Modular dockable/floating entity inspector
- `frontend/src/components/DiceRoller.tsx` — Unified dockable dice tray
- `frontend/src/components/ChatPanel.tsx` — Narrative chronicle with atmospheric scene header
- `data/assets/` — Dedicated runtime visual asset directory
- `backend/tests/test_image_assets.py` — Backend tests for image generation & asset persistence
- `e2e/` — Playwright test suite for browser zero-error verification
