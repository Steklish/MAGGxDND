from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, computed_field

class Coordinate3D(BaseModel):
    """3D coordinate system for spatial positioning."""
    x: float = Field(default=0.0, description="X coordinate (horizontal axis)")
    y: float = Field(default=0.0, description="Y coordinate (vertical axis)")
    z: float = Field(default=0.0, description="Z coordinate (depth axis)")

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

    # Spatial information (for objects in scenes)
    position: Optional[Coordinate3D] = Field(default_factory=Coordinate3D, description="Current position of the object in 3D space when in a scene")

    # Metadata
    tags: Optional[List[str]] = Field(default_factory=list, description="Keywords for the GM: ['trapped', 'magical', 'explosive'].")
    item_description: Optional[str] = Field(None, description="Description when taken as an inventory item.")

    @computed_field
    @property
    def short_summary(self) -> str:
        """
        Returns a compressed string for the AI context window.
        Example: "Longsword: 1d8 Slashing | Weapon | Equipped | Locked"
        """
        summary_parts = [self.name]

        # Add combat properties if present
        if self.damage_dice:
            damage_info = f"{self.damage_dice}"
            if self.damage_type:
                damage_info += f" {self.damage_type.value}"
            summary_parts.append(damage_info)

        # Add object type if specified
        if self.obj_type:
            summary_parts.append(f"| {self.obj_type.value}")

        # Add state if not normal
        if self.state and self.state != "normal":
            summary_parts.append(f"| {self.state.title()}")

        # Add equipment status if equipped
        if self.is_equipped:
            summary_parts.append("| Equipped")

        # Add lock status if locked
        if self.is_locked:
            summary_parts.append("| Locked")

        # Add hidden status if hidden
        if self.is_hidden:
            summary_parts.append("| Hidden")

        # Add capacity if container with capacity
        if self.capacity is not None:
            summary_parts.append(f"| Capacity: {len(self.content or [])}/{self.capacity}")

        # Add quantity if more than 1
        if self.quantity > 1:
            summary_parts.append(f"| Qty: {self.quantity}")

        # Add standout tags if present
        if self.tags:
            tag_str = ", ".join(self.tags[:3])  # Limit to first 3 tags to keep summary concise
            summary_parts.append(f"| Tags: {tag_str}")

        return " ".join(summary_parts)

# For backward compatibility, Item is now an alias for UnifiedObject
Item = UnifiedObject

class Skill(BaseModel):
    """A specific skill proficiency."""
    name: str = Field(..., description="Name of the skill (e.g., 'Stealth', 'Arcana').")
    proficient: bool = Field(False, description="If true, add proficiency bonus to checks.")
    expert: bool = Field(False, description="If true, add double proficiency bonus.")

class ActionType(str, Enum):
    ACTION = "Action"
    BONUS_ACTION = "Bonus Action"
    REACTION = "Reaction"
    PASSIVE = "Passive"
    FREE = "Free Interaction"
    MINUTE = "Minute(s)"  # For rituals or longer casting
    HOUR = "Hour(s)"

class AbilityType(str, Enum):
    SPELL = "Spell"
    CLASS_FEATURE = "Class Feature" # e.g. Second Wind, Sneak Attack
    RACIAL_TRAIT = "Racial Trait"   # e.g. Breath Weapon
    FEAT = "Feat"                   # e.g. Lucky
    LEGENDARY = "Legendary Action"

class MagicSchool(str, Enum):
    NONE = "None" # For non-magical abilities
    ABJURATION = "Abjuration"
    CONJURATION = "Conjuration"
    DIVINATION = "Divination"
    ENCHANTMENT = "Enchantment"
    EVOCATION = "Evocation"
    ILLUSION = "Illusion"
    NECROMANCY = "Necromancy"
    TRANSMUTATION = "Transmutation"

class SpellAbility(BaseModel):
    """
    Represents a Spell, Class Feature, or Special Ability.
    Combines narrative description with mechanical dice logic.
    """
    # Identity
    name: str = Field(..., description="Name of the spell or ability (e.g., 'Fireball').")
    type: AbilityType = Field(AbilityType.SPELL, description="Category of the ability.")
    level: int = Field(0, ge=0, le=9, description="Spell level (0 for Cantrips/Features).")
    school: MagicSchool = Field(MagicSchool.NONE, description="Magic school if applicable.")
    
    # Narrative
    description: str = Field(..., description="Full text description of effects.")
    
    # Action Economy & Cost
    casting_time: ActionType = Field(ActionType.ACTION, description="Time required to use.")
    range: str = Field("Self", description="Distance (e.g., '60 feet', 'Touch', 'Self (15-foot cone)').")
    duration: str = Field("Instantaneous", description="How long it lasts (e.g., '1 minute', 'Concentration').")
    
    # Resource Logic
    resource_cost: Optional[str] = Field(None, description="Key in Character.resources to consume (e.g., 'spell_slots_lvl3', 'ki_points').")
    cost_amount: int = Field(0, description="How much of the resource is consumed.")
    is_concentration: bool = Field(False, description="Does it require focus?")
    is_ritual: bool = Field(False, description="Can be cast as a ritual?")

    # Combat Mechanics (The "Crunch")
    # Attack Roll Logic
    requires_attack_roll: bool = Field(False, description="True if this needs a d20 roll against AC.")
    attack_bonus: int = Field(0, description="Pre-calculated bonus to hit (Base + Stat + Prof).")

    # Saving Throw Logic
    requires_save: bool = Field(False, description="True if the target must roll a save.")
    save_dc: Optional[int] = Field(None, description="Difficulty Class for the save.")
    save_ability: Optional[str] = Field(None, description="Ability used for save (e.g., 'DEX', 'WIS').")

    # Damage / Healing Logic
    damage_dice: Optional[str] = Field(None, description="Dice notation for damage (e.g., '8d6', '1d10+4').")
    damage_type: Optional[DamageType] = Field(None, description="Type of damage dealt.")
    
    healing_dice: Optional[str] = Field(None, description="Dice notation for healing (e.g., '2d4+2').")

    # Metadata
    tags: List[str] = Field(default_factory=list, description="AI helper tags: ['aoe', 'buff', 'control', 'finisher'].")

    @computed_field
    @property
    def short_summary(self) -> str:
        """
        Returns a compressed string for the AI context window.
        Example: "[Action] Fireball: 8d6 Fire (Dex Save DC 15) - 150ft"
        """
        summary = f"[{self.casting_time.value}] {self.name}"
        
        # Add Damage/Heal info
        if self.damage_dice:
            summary += f": {self.damage_dice} {self.damage_type.value if self.damage_type else ''}"
        elif self.healing_dice:
            summary += f": Heals {self.healing_dice}"
        
        # Add Hit/Save info
        if self.requires_attack_roll:
            summary += f" (+{self.attack_bonus} to hit)"
        elif self.requires_save:
            summary += f" ({self.save_ability} Save DC {self.save_dc})"
            
        return summary

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

    # 3. Core Stats
    stats: AbilityScores = Field(..., description="The nested object containing STR, DEX, CON, etc.")

    # 4. Inventory & State
    inventory: List[Item] = Field(default_factory=list, description="List of all items carried.")
    active_conditions: List[str] = Field(default_factory=list, description="List of status effects (e.g., 'Poisoned', 'Prone').")

    # 5. Resources (Spell Slots, etc.)
    # Using a flexible dict allows for different systems (Ki points, Spell Slots, Rage charges)
    resources: dict = Field(default_factory=dict, description="Trackable resources. Example: {'spell_slots_lvl1': 3, 'rages': 2}")

    # 6. Spatial Information
    position: Coordinate3D = Field(default_factory=Coordinate3D, description="Current position of the character in 3D space")
    facing_direction: Coordinate3D = Field(default_factory=lambda: Coordinate3D(x=1.0, y=0.0, z=0.0),
                                          description="Direction the character is facing (unit vector)")
    abilities: List[SpellAbility] = Field(
        default_factory=list, 
        description="Known spells, class features, and racial traits available for use."
    )
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

    @computed_field
    @property
    def initiative_bonus(self) -> float:
        """
        Calculated initiative bonus based on Dexterity modifier and character speed.
        Used for tuen order calculation. Speed based queue, not DnD style.
        """
        return self.stats.dexterity  + self.speed

    @computed_field
    @property
    def short_summary(self) -> str:
        """
        Returns a compressed string for the AI context window.
        Includes appearance, behavior, abilities, and inventory.
        Example: "Ogorek the Human Wizard (Lvl 5) | HP: 24/30 | AC: 12 | Str: 8, Dex: 14, Con: 13, Int: 18, Wis: 12, Cha: 10 | Fireball, Magic Missile | Staff, Robes"
        """
        # Basic identity
        summary_parts = [f"{self.name} the {self.race} {self.char_class.value} (Lvl {self.level})"]

        # Health and armor
        summary_parts.append(f"HP: {self.current_hp}/{self.max_hp}")
        if self.armor_class != 10:  # Only show AC if not default
            summary_parts.append(f"AC: {self.armor_class}")

        # Stats
        stats_part = f"Str: {self.stats.strength}, Dex: {self.stats.dexterity}, Con: {self.stats.constitution}, Int: {self.stats.intelligence}, Wis: {self.stats.wisdom}, Cha: {self.stats.charisma}"
        summary_parts.append(stats_part)

        # Personality traits (behavior)
        if self.personality_traits:
            behavior = ", ".join(self.personality_traits[:3])  # Limit to first 3 traits
            summary_parts.append(f"Behavior: {behavior}")

        # Abilities (using their short summaries)
        if self.abilities:
            ability_names = [ability.short_summary for ability in self.abilities[:3]]  # Limit to first 3 abilities
            summary_parts.append(f"Abilities: {', '.join(ability_names)}")

        # Inventory (using item short summaries)
        if self.inventory:
            inventory_names = [item.short_summary.split(' ', 1)[0] for item in self.inventory[:5]]  # Take just the name part of the item summary, limit to first 5 items
            summary_parts.append(f"Inventory: {', '.join(inventory_names)}")

        # Active conditions
        if self.active_conditions:
            conditions = ", ".join(self.active_conditions)
            summary_parts.append(f"Conditions: {conditions}")

        return " | ".join(summary_parts)

class NPCCharacter(Character):
    """An NPC variant that may have additional AI-specific fields in the future."""
    motivation: Optional[str] = Field(None, description="What drives this NPC?")
    alignment: Optional[Alignment] = Field(None, description="Moral alignment of the NPC.")
    memory : str = Field("", description="NPC's internal memory log.")
    current_scene: str = Field(description="Name of the scene the NPC is currently in")
    
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

    # Spatial information
    center_position: Coordinate3D = Field(default_factory=Coordinate3D, description="Center position of the scene")
    dimensions: Coordinate3D = Field(default_factory=lambda: Coordinate3D(x=10.0, y=10.0, z=10.0),
                                   description="Dimensions of the scene (width, height, depth)")
    scale_unit: str = Field("feet", description="Unit of measurement for coordinates (e.g., feet, meters)")