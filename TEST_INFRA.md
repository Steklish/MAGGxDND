# E2E Test Infra: MAGGxDND

## Test Philosophy
- Opaque-box, requirement-driven testing derived from `ORIGINAL_REQUEST.md`.
- Systematic 4-tier methodology: Category-Partition, Boundary Value Analysis, Pairwise Combinatorial Testing, and Real-World Workload Testing.
- Strict headless browser zero-console-error verification via Playwright / automated browser drivers.

## Feature Inventory
| # | Feature | Source | Tier 1 | Tier 2 | Tier 3 |
|---|---------|--------|:------:|:------:|:------:|
| 1 | Glassmorphism UI & Layout | R1 | 5 | 5 | ✓ |
| 2 | Dockable & Collapsible Drawers | R1 | 5 | 5 | ✓ |
| 3 | Persistent Entity Image Generation | R2 | 5 | 5 | ✓ |
| 4 | Asynchronous Non-blocking Generation | R2 | 5 | 5 | ✓ |
| 5 | Top-Down Tactical Battle Map | R3 | 5 | 5 | ✓ |
| 6 | Controlled Asset Storage & Static Serving | R4 | 5 | 5 | ✓ |

## Test Architecture
- **Backend Test Runner**: Pytest (`d:\Duty\MAGGxDND\.venv\Scripts\python.exe -m pytest backend/tests/test_image_assets.py -c backend/pytest.ini`).
  - Asserts model serialization/deserialization with `image_url` and `battlemap_image_url`.
  - Asserts static asset endpoint serving (`/assets/...`).
  - Asserts caching behavior (disk hits vs API generation calls).
  - Asserts fallback SVG placeholder serving when API is disabled or fails.
- **Frontend & E2E Test Runner**: Playwright / Automated headless browser test suite (`tests/e2e/` or `e2e/test_maggxdnd_e2e.py`).
  - Headless Chromium browser automation against running backend & frontend.
  - Intercepts all console events: `page.on("console", ...)` and `page.on("pageerror", ...)`.
  - Verifies zero console errors (`console.error` and unhandled exceptions).
  - Verifies visual element presence, glassmorphism styles, drawer collapse/dock behavior, character avatars, item cards, narrative banner, and battle map background image under grid.

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Tavern Exploration to Dungeon Combat | Map, Drawers, Characters, Chronicle, Dice, Scene Header | High |
| 2 | Tactical Battle Sequence with Movement & Turns | Token Movement, Map Persistence, Action Hotbar, Dice Tray | High |
| 3 | Inventory Inspection & Item Use | Hero Sheet Docking, Item Cards Artwork, Rarity Glow, Action Deck | Medium |
| 4 | Session Save, Close, and Reload | Model Persistence, Asset Cache Hit, No Redundant API Calls | High |

## Coverage Thresholds
- Tier 1: Feature Coverage (≥5 tests per feature = 30 tests)
- Tier 2: Boundary & Corner Cases (≥5 tests per feature = 30 tests)
- Tier 3: Cross-Feature Interaction Cases (≥6 tests)
- Tier 4: Real-World Application Workloads (≥4 tests)
- Total E2E test target: ≥70 verification points across backend test suite and automated browser runner.
