"""
Library of predefined characters for testing purposes.
"""

from schemas.in_game import Character, AbilityScores, CharacterClass


def get_test_hero() -> Character:
    """Returns a standard hero character for testing."""
    return Character(
        name="Test Hero",
        race="Human",
        char_class=CharacterClass.FIGHTER,
        level=5,
        backstory_summary="A brave warrior who protects the innocent.",
        personality_traits=["Brave", "Loyal", "Honorable"],
        max_hp=100,
        current_hp=100,
        temp_hp=0,
        armor_class=16,
        speed=30,
        abilities=AbilityScores(
            strength=16,
            dexterity=14,
            constitution=15,
            intelligence=12,
            wisdom=13,
            charisma=14
        ),
        inventory=[],
        active_conditions=[]
    )


def get_test_wizard() -> Character:
    """Returns a wizard character for testing."""
    return Character(
        name="Test Wizard",
        race="Elf",
        char_class=CharacterClass.WIZARD,
        level=5,
        backstory_summary="A scholarly magic user who seeks ancient knowledge.",
        personality_traits=["Curious", "Intelligent", "Cautious"],
        max_hp=60,
        current_hp=60,
        temp_hp=0,
        armor_class=12,
        speed=30,
        abilities=AbilityScores(
            strength=8,
            dexterity=12,
            constitution=13,
            intelligence=18,
            wisdom=15,
            charisma=10
        ),
        inventory=[],
        active_conditions=[]
    )


def get_test_rogue() -> Character:
    """Returns a rogue character for testing."""
    return Character(
        name="Test Rogue",
        race="Halfling",
        char_class=CharacterClass.ROGUE,
        level=5,
        backstory_summary="A nimble thief with a mysterious past.",
        personality_traits=["Clever", "Sneaky", "Independent"],
        max_hp=70,
        current_hp=70,
        temp_hp=0,
        armor_class=14,
        speed=30,
        abilities=AbilityScores(
            strength=10,
            dexterity=18,
            constitution=14,
            intelligence=14,
            wisdom=11,
            charisma=12
        ),
        inventory=[],
        active_conditions=[]
    )


def get_test_cleric() -> Character:
    """Returns a cleric character for testing."""
    return Character(
        name="Test Cleric",
        race="Dwarf",
        char_class=CharacterClass.CLERIC,
        level=5,
        backstory_summary="A devoted healer and divine spellcaster.",
        personality_traits=["Compassionate", "Faithful", "Protective"],
        max_hp=80,
        current_hp=80,
        temp_hp=0,
        armor_class=15,
        speed=25,
        abilities=AbilityScores(
            strength=14,
            dexterity=10,
            constitution=16,
            intelligence=12,
            wisdom=17,
            charisma=13
        ),
        inventory=[],
        active_conditions=[]
    )


def get_custom_character(
    name: str,
    char_class: CharacterClass = CharacterClass.FIGHTER,
    level: int = 1,
    race: str = "Human",
    max_hp: int = 10,
    current_hp: int = 10,
    strength: int = 10,
    dexterity: int = 10,
    constitution: int = 10,
    intelligence: int = 10,
    wisdom: int = 10,
    charisma: int = 10,
    backstory: str = "",
    traits: list = []
) -> Character:
    """Creates a custom character with specified parameters."""
    if traits is None:
        traits = ["Neutral"]
    
    return Character(
        name=name,
        race=race,
        char_class=char_class,
        level=level,
        backstory_summary=backstory,
        personality_traits=traits,
        max_hp=max_hp,
        current_hp=current_hp,
        temp_hp=0,
        armor_class=10,
        speed=30,
        abilities=AbilityScores(
            strength=strength,
            dexterity=dexterity,
            constitution=constitution,
            intelligence=intelligence,
            wisdom=wisdom,
            charisma=charisma
        ),
        inventory=[],
        active_conditions=[]
    )