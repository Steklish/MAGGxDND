# Procedural Generation System

## Overview

The game now features a **procedural generation system** that creates content dynamically when AI is unavailable. This ensures the game is fully playable without requiring an API key.

## What Gets Generated

### 🏰 Scenes

Scenes are generated based on keywords in your adventure wishes:

**Scene Types:**
- **Tavern** - "The Silver Dragon", "The Laughing Dragon", etc.
- **Cave** - "The Whispering Caverns", "The Crystal Cave", etc.
- **Forest** - "The Whispering Woods", "The Elder Grove", etc.
- **Castle** - "Castle Ravenmoor", "The Iron Keep", etc.
- **Default** - "The Adventurer's Rest", "The Crossroads Inn", etc.

**Example:**
```
Input: "A medieval tavern with adventurers"
Output: "The Silver Dragon" - "A cozy tavern with a roaring fireplace and the smell of roasted meat. A medieval tavern with adventurers"
```

### ⚔️ Player Characters

Characters are generated with:
- **Random Names**: Aldric Stormwind, Brynn Ironfoot, Cedric Shadowbane, etc.
- **Random Classes**: Fighter, Wizard, Rogue, Cleric
- **Random Stats**: Varied ability scores (8-18 range)
- **Class Abilities**: Specific to each class
- **Starting Inventory**: Appropriate gear for class

**Example Characters:**
- **Fighter**: Attack, Second Wind, Action Surge | Longsword, Shield, Chain Mail
- **Wizard**: Fire Bolt, Magic Missile, Shield | Quarterstaff, Spellbook, Robes
- **Rogue**: Attack, Sneak Attack, Cunning Action | Shortsword, Leather Armor, Thieves' Tools
- **Cleric**: Attack, Healing Word, Guiding Bolt | Mace, Shield, Holy Symbol

### 🧙 NPCs

NPCs are generated with:
- **Random Roles**: tavern keeper, blacksmith, merchant, guard, wizard, healer, thief, bard, hunter, farmer
- **Random Personalities**: Friendly, Reserved, Talkative, Suspicious
- **Random Motivations**: Earn living, protect family, gain knowledge, survive
- **Basic Inventory**: Common clothes, small amount of gold
- **Simple Abilities**: Help action

**Example NPCs:**
- "Aldric the Tavern Keeper" - Friendly, wants to earn a living
- "Brynn the Blacksmith" - Reserved, wants to protect family
- "Cedric the Merchant" - Talkative, wants to gain knowledge

## How It Works

### Flow Diagram

```
User clicks "Start Game"
         ↓
Backend receives wishes/prompts
         ↓
Is AI available? ────YES───→ Use Gemini API
         ↓ NO
Use Procedural Generator
         ↓
1. Parse scene keywords → Generate scene
2. Generate player character(s)
3. Generate NPC(s)
4. Return complete game data
         ↓
Frontend displays UI with generated content
```

### Code Location

**Procedural Generator:** `backend/src/api/routers/session_router.py`
- Lines 50-295: `ProceduralGenerator` class
- Line generation: `procedural_gen.generate_scene()`
- Character generation: `procedural_gen.generate_character()`
- NPC generation: `procedural_gen.generate_npc()`

**Frontend Prompts:** `frontend/src/components/GameLayout.tsx`
- Lines 333-348: Start game request with prompts

## Testing

1. **Clear browser** and create new session
2. **Start game** with wishes: "A medieval tavern with adventurers"
3. **Verify generated content:**
   - ✅ Scene has unique name (not "The Starting Location")
   - ✅ Character has random name (not "Hero1")
   - ✅ Character has random class (Fighter/Wizard/Rogue/Cleric)
   - ✅ Character has 3 abilities appropriate to class
   - ✅ Character has 5 inventory items appropriate to class
   - ✅ NPC has random role and occupation
   - ✅ All data displays correctly in UI

## Logs to Check

```
[START] Procedural scene generated: The Silver Dragon
[START] Procedural character generated: Aldric Stormwind (FIGHTER)
[START] Procedural NPC generated: Brynn the Tavern Keeper (Tavern Keeper)
```

## Benefits

✅ **No API key required** - Game is fully playable offline
✅ **Variety** - Each session has different content
✅ **Fast** - No waiting for AI responses
✅ **Predictable** - Balanced stats and abilities
✅ **Thematic** - Content matches adventure theme

## Limitations

❌ **Less creative** - Templates instead of unique AI creations
❌ **Limited variety** - ~20 names, ~20 scenes vs infinite AI
❌ **No dynamic story** - Static descriptions
❌ **Generic content** - Same classes/items every time

## Future Enhancements

- [ ] More scene templates (dungeon, desert, mountain, city, etc.)
- [ ] More character classes (paladin, ranger, barbarian, druid, etc.)
- [ ] Race variations (elf, dwarf, halfling, orc, etc.)
- [ ] Equipment tables by rarity
- [ ] Random encounter generation
- [ ] Treasure generation
- [ ] Quest generation

## AI vs Procedural

| Feature | AI Generation | Procedural |
|---------|--------------|------------|
| Scene Names | Unique, creative | Template-based |
| Character Names | Unique, thematic | Random from list |
| Abilities | Custom descriptions | Standard D&D 5e |
| Backstory | Creative, detailed | Generic template |
| Inventory | Thematic, varied | Class-based |
| Speed | Slow (5-10s) | Instant |
| API Required | Yes | No |
| Region Locked | Yes | No |

## Conclusion

The procedural generation system ensures **everyone can play** regardless of API availability or region restrictions. While AI generation provides more creative content, the procedural system offers a solid, balanced, and thematic experience that's perfect for quick games or when API is unavailable.
