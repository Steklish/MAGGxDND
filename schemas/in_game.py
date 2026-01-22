from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, computed_field

# --- Enums for Strict Typing ---
class GameModes(str, Enum):
    STORY = "STORY" # for story and peaceful / social scenes
    COMBAT = "COMBAT" # for combats with strict turns order and rules

class Alignment(str, Enum):
    LAWFUL_GOOD = "Lawful Good"
    NEUTRAL_GOOD = "Neutral Good"
    CHAOTIC_GOOD = "Chaotic Good"
    LAWFUL_NEUTRAL = "Lawful Neutral"
    TRUE_NEUTRAL = "True Neutral"
    CHAOTIC_NEUTRAL = "Chaotic Neutral"
    LAWFUL_EVIL = "Lawful Evil"
    NEUTRAL_EVIL = "Neutral Evil"
    CHAOTIC_EVIL = "Chaotic Evil"

class CharacterClass(str, Enum):
    PEASANT = "Peasant"
    FIGHTER = "Fighter"
    WIZARD = "Wizard"
    ROGUE = "Rogue"
    CLERIC = "Cleric"
    RANGER = "Ranger"
    PALADIN = "Paladin"
    BARBARIAN = "Barbarian"
    BARD = "Bard"

class DamageType(str, Enum):
    SLASHING = "Slashing"
    PIERCING = "Piercing"
    BLUDGEONING = "Bludgeoning"
    FIRE = "Fire"
    COLD = "Cold"
    LIGHTNING = "Lightning"

# --- Sub-Models for Modularity ---

class AbilityScores(BaseModel):
    """The six core stats that define a character's capabilities."""
    strength: int = Field(10, ge=1, le=30, description="Muscular power. Affects melee attack/damage.")
    dexterity: int = Field(10, ge=1, le=30, description="Agility and reflexes. Affects AC and initiative.")
    constitution: int = Field(10, ge=1, le=30, description="Health and stamina. Affects HP.")
    intelligence: int = Field(10, ge=1, le=30, description="Reasoning and memory. Important for Wizards.")
    wisdom: int = Field(10, ge=1, le=30, description="Perception and insight. Important for Clerics.")
    charisma: int = Field(10, ge=1, le=30, description="Personality and leadership. Important for Bards.")

# --- Additional Models for Game Objects ---

class ObjectType(str, Enum):
    PROP = "Prop"               # Just for looking (Painting, Statue)
    CONTAINER = "Container"     # Holds items (Chest, Corpse)
    INTERACTABLE = "Interactable" # Doors, Levers, Traps

class UnifiedObject(BaseModel):
    """
    A unified object representation that combines both inventory items and scene objects.
    """
    # Core identification fields
    id: Optional[str] = Field(None, description="Unique ID (e.g., 'chest_01'). Used when in a scene.")
    name: str = Field(..., description="The name of the object (e.g., 'Longsword +1').")
    description: Optional[str] = Field(None, description="Flavor text or mechanical effects.")

    # Object type classification
    obj_type: Optional[ObjectType] = Field(None, description="Category of interaction: Prop, Container, Interactable.")
    state: Optional[str] = Field("normal", description="Current status: 'closed', 'open', 'broken', 'active'.")

    # Physical properties
    quantity: int = Field(1, ge=1, description="How many of this object exist.")
    is_equipped: bool = Field(False, description="Whether the character is currently holding/wearing this or if object is equipped when in scene.")

    # Combat properties
    damage_dice: Optional[str] = Field(None, description="If a weapon, the dice notation (e.g., '1d8').")
    damage_type: Optional[DamageType] = Field(None, description="The type of damage this weapon inflicts.")

    # Interaction properties
    is_locked: Optional[bool] = Field(None, description="Requires key/picking?")
    is_hidden: Optional[bool] = Field(None, description="Requires perception check?")

    # Container properties
    content: Optional[List[str]] = Field(default_factory=list, description="Items inside (e.g. ['gold_coin', 'rusty_dagger']).")
    capacity: Optional[int] = Field(None, description="Maximum number of objects this container can hold.")
    contained_objects: Optional[List['UnifiedObject']] = Field(default_factory=list, description="Other objects contained within this object.")

    # Metadata
    tags: Optional[List[str]] = Field(default_factory=list, description="Keywords for the GM: ['trapped', 'magical', 'explosive'].")
    item_description: Optional[str] = Field(None, description="Description when taken as an inventory item.")

# For backward compatibility, Item is now an alias for UnifiedObject
Item = UnifiedObject

class Skill(BaseModel):
    """A specific skill proficiency."""
    name: str = Field(..., description="Name of the skill (e.g., 'Stealth', 'Arcana').")
    proficient: bool = Field(False, description="If true, add proficiency bonus to checks.")
    expert: bool = Field(False, description="If true, add double proficiency bonus.")

# --- The Main Character Model ---

class Character(BaseModel):
    """
    The master object representing a Player Character (PC) or NPC.
    This schema is designed to be serialized to JSON for the AI Context.
    """

    # 1. Identity & Narrative
    name: str = Field(..., description="The character's name.")
    race: str = Field("Human", description="The biological race (e.g., Elf, Dwarf).")
    char_class: CharacterClass = Field(..., description="The primary job/class.")
    level: int = Field(1, ge=1, le=20, description="Current power level.")
    backstory_summary: str = Field("", description="A concise summary of the character's history for the AI narrator.")
    personality_traits: List[str] = Field(default_factory=list, description="Keywords for the AI to determine roleplay style (e.g., 'Brave', 'Greedy').")

    # 2. Vitals (Battle State)
    max_hp: int = Field(..., ge=1, description="Maximum Hit Points.")
    current_hp: int = Field(..., description="Current Hit Points. If <= 0, character is unconscious or dead.")
    temp_hp: int = Field(0, ge=0, description="Temporary buffer HP that is lost before real HP.")
    armor_class: int = Field(10, description="Target number to hit this character.")
    speed: int = Field(30, description="Movement speed in feet per turn.")
    initiative_bonus: int = Field(0, description="Modifier added to initiative rolls.")

    # 3. Core Stats
    abilities: AbilityScores = Field(..., description="The nested object containing STR, DEX, CON, etc.")

    # 4. Inventory & State
    inventory: List[Item] = Field(default_factory=list, description="List of all items carried.")
    active_conditions: List[str] = Field(default_factory=list, description="List of status effects (e.g., 'Poisoned', 'Prone').")

    # 5. Resources (Spell Slots, etc.)
    # Using a flexible dict allows for different systems (Ki points, Spell Slots, Rage charges)
    resources: dict = Field(default_factory=dict, description="Trackable resources. Example: {'spell_slots_lvl1': 3, 'rages': 2}")

    # --- Computed Helpers (Logic) ---
    # These create derived fields automatically when serialized, giving the AI the math results.

    @computed_field
    @property
    def proficiency_bonus(self) -> int:
        """Calculates proficiency bonus based on level (Standard 5e rules)."""
        return (self.level - 1) // 4 + 2

    @computed_field
    @property
    def is_alive(self) -> bool:
        """Quick check for the system router."""
        return self.current_hp > 0

    def get_modifier(self, score: int) -> int:
        """Helper to calculate standard DnD modifier: (Score - 10) / 2."""
        return (score - 10) // 2
    
class NPCCharacter(Character):
    """An NPC variant that may have additional AI-specific fields in the future."""
    motivation: Optional[str] = Field(None, description="What drives this NPC?")
    alignment: Optional[Alignment] = Field(None, description="Moral alignment of the NPC.")
    memory : str = Field("", description="NPC's internal memory log.")
    
class SceneNode(BaseModel):
    """
    A lightweight scene optimized for LLM context windows.
    """
    name: str = Field(..., description="Display title (e.g., 'The Prancing Pony').")
    # The Visuals
    description: str = Field(..., description="What the players see immediately upon entering.")
    # This replaces complex flags. Put trap info, hidden enemies, and plot hooks here.
    gm_secret: str = Field(
        default="",
        description="Hidden info for the GM only. E.g. 'The rug covers a pit trap', 'The barmaid is a spy'."
    )
    objects: List['UnifiedObject'] = Field(default_factory=list, description="Interactable items present.")