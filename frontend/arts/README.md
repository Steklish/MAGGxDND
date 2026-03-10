# MAGGxDND UI Assets

## 📁 Asset Directory Structure

This directory contains all UI assets for the MAGGxDND frontend.

### Organization

```
arts/
├── backgrounds/          # Background images
│   ├── bg-login.jpg     # Login screen background (1920x1080)
│   ├── bg-game.jpg      # Main game screen background (1920x1080)
│   ├── bg-character.jpg # Character sheet background (1920x1080)
│   ├── bg-combat.jpg    # Combat mode background (1920x1080)
│   ├── bg-tavern.jpg    # Tavern/peaceful mode background (1920x1080)
│   └── bg-dungeon.jpg   # Dungeon/cave background (1920x1080)
│
├── characters/           # Character portraits and avatars
│   ├── portrait-placeholder.png  # Default character portrait (256x256)
│   ├── avatar-warrior.png       # Warrior class avatar (64x64)
│   ├── avatar-wizard.png        # Wizard class avatar (64x64)
│   ├── avatar-rogue.png         # Rogue class avatar (64x64)
│   ├── avatar-cleric.png        # Cleric class avatar (64x64)
│   └── avatar-default.png       # Default avatar (64x64)
│
├── items/                # Item icons
│   ├── icon-sword.png    # Sword icon (64x64)
│   ├── icon-shield.png   # Shield icon (64x64)
│   ├── icon-potion.png   # Potion icon (64x64)
│   ├── icon-scroll.png   # Scroll icon (64x64)
│   ├── icon-key.png      # Key icon (64x64)
│   └── icon-default.png  # Default item icon (64x64)
│
├── locations/            # Location images
│   ├── loc-tavern.jpg    # Tavern location (800x600)
│   ├── loc-dungeon.jpg   # Dungeon location (800x600)
│   ├── loc-forest.jpg    # Forest location (800x600)
│   ├── loc-castle.jpg    # Castle location (800x600)
│   └── loc-cave.jpg      # Cave location (800x600)
│
├── effects/              # Visual effects
│   ├── fx-attack.png     # Attack effect sprite sheet (512x512)
│   ├── fx-spell.png      # Spell effect sprite sheet (512x512)
│   ├── fx-heal.png       # Heal effect sprite sheet (512x512)
│   └── fx-turn.png       # Turn indicator effect (256x256)
│
├── ui-elements/          # UI component images
│   ├── ui-logo.png       # MAGGxDND logo (256x256)
│   ├── ui-button-hover.png   # Button hover state (200x50)
│   ├── ui-button-active.png  # Button active state (200x50)
│   ├── ui-panel.png      # Generic panel background (400x300)
│   ├── ui-border.png     # Decorative border tile (32x32)
│   └── ui-divider.png    # Section divider (800x4)
│
└── README.md             # This file
```

---

## 🎨 Asset Specifications

### Backgrounds
- **Format**: JPG or PNG
- **Resolution**: 1920x1080 (Full HD)
- **Style**: Dark fantasy, atmospheric
- **File size**: < 500KB each

### Character Portraits
- **Format**: PNG with transparency
- **Resolution**: 256x256 (portrait), 64x64 (avatar)
- **Style**: Consistent art style
- **File size**: < 100KB each

### Item Icons
- **Format**: PNG with transparency
- **Resolution**: 64x64
- **Style**: Clear, recognizable silhouettes
- **File size**: < 20KB each

### Location Images
- **Format**: JPG
- **Resolution**: 800x600
- **Style**: Atmospheric, detailed
- **File size**: < 300KB each

---

## 📝 Naming Convention

Use clear, descriptive names:

**Good:**
- `bg-login.jpg`
- `icon-sword-fire.png`
- `portrait-elf-mage.png`

**Bad:**
- `image1.png`
- `sword_final_v2_really.png`
- `temp_bg.jpg`

### Prefix System

| Prefix | Type | Example |
|--------|------|---------|
| `bg-` | Background | `bg-game.jpg` |
| `icon-` | Item icon | `icon-potion-health.png` |
| `portrait-` | Character portrait | `portrait-warrior.png` |
| `avatar-` | Small avatar | `avatar-wizard.png` |
| `loc-` | Location | `loc-forest-night.jpg` |
| `fx-` | Effect | `fx-lightning.png` |
| `ui-` | UI element | `ui-button-primary.png` |

---

## 🖼️ Placeholder Assets

For development, use these placeholder services:

### Backgrounds
- https://placeholder.com/
- https://picsum.photos/1920/1080

### Icons
- https://www.iconfinder.com/
- https://game-icons.net/

### Generate Placeholders
```bash
# Using placeholder.com
https://via.placeholder.com/1920x1080/1a1a2e/ffffff?text=Game+Background

# Using picsum
https://picsum.photos/1920/1080?grayscale&blur=2
```

---

## 🎯 Required Minimum Assets

For MVP, create at least:

1. **Backgrounds (3)**:
   - `bg-login.jpg` - Login/landing page
   - `bg-game.jpg` - Main game screen
   - `bg-combat.jpg` - Combat mode

2. **Icons (10)**:
   - Sword, Shield, Potion, Scroll, Key
   - Heart (HP), Star (MP), Fist (Attack), Boot (Move), Clock (Turn)

3. **UI Elements (5)**:
   - Logo, Button states, Panel, Border

---

## 📦 Export Guidelines

### For Web
- Use WebP format when possible (better compression)
- Provide PNG fallback
- Optimize with tools like TinyPNG

### For High DPI
- Export @2x and @3x versions
- Name: `icon-sword@2x.png`, `icon-sword@3x.png`

### Color Profiles
- Use sRGB color space
- Embed color profile

---

## 🔧 Tools

### Free Tools
- **GIMP** - Image editing
- **Inkscape** - Vector graphics
- **Krita** - Digital painting
- **Photopea** - Online Photoshop alternative

### Optimization
- **TinyPNG** - PNG compression
- **Squoosh** - Image optimization
- **SVGOMG** - SVG optimization

---

## 📄 License

Remember to:
- [ ] Use assets you have rights to
- [ ] Credit original artists
- [ ] Include license files for third-party assets

---

**Last Updated**: 2026-03-10
**Version**: 1.0
