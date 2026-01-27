"""
Library of predefined NPCs for testing purposes.
"""

from schemas.in_game import NPCCharacter, AbilityScores, CharacterClass, Alignment


def get_guard_npc() -> NPCCharacter:
    """Returns a guard NPC for testing."""
    return NPCCharacter(
        name="Guard John",
        race="Human",
        char_class=CharacterClass.FIGHTER,
        level=3,
        backstory_summary="A loyal city guard who takes his duty seriously.",
        personality_traits=["Dutiful", "Suspicious", "Professional"],
        max_hp=45,
        current_hp=45,
        temp_hp=0,
        armor_class=16,
        speed=30,
        abilities=AbilityScores(
            strength=15,
            dexterity=13,
            constitution=14,
            intelligence=10,
            wisdom=12,
            charisma=11
        ),
        inventory=[],
        active_conditions=[],
        motivation="Protect the citizens and maintain order",
        alignment=Alignment.LAWFUL_GOOD,
        memory="Has been guarding this area for 2 years.",
        current_scene="City Gate"
    )


def get_merchant_npc() -> NPCCharacter:
    """Returns a merchant NPC for testing."""
    return NPCCharacter(
        name="Merchant Tom",
        race="Human",
        char_class=CharacterClass.PEASANT,
        level=1,
        backstory_summary="A traveling merchant who sells exotic goods.",
        personality_traits=["Friendly", "Shrewd", "Talkative"],
        max_hp=8,
        current_hp=8,
        temp_hp=0,
        armor_class=10,
        speed=30,
        abilities=AbilityScores(
            strength=10,
            dexterity=12,
            constitution=11,
            intelligence=14,
            wisdom=10,
            charisma=15
        ),
        inventory=[],
        active_conditions=[],
        motivation="Make profit and expand trade routes",
        alignment=Alignment.TRUE_NEUTRAL,
        memory="Trades in rare spices and magical components.",
        current_scene="Marketplace"
    )


def get_bandit_npc() -> NPCCharacter:
    """Returns a bandit NPC for testing."""
    return NPCCharacter(
        name="Bandit Leader",
        race="Half-orc",
        char_class=CharacterClass.ROGUE,
        level=4,
        backstory_summary="A ruthless bandit leader who terrorizes travelers.",
        personality_traits=["Cunning", "Ruthless", "Charismatic"],
        max_hp=40,
        current_hp=40,
        temp_hp=0,
        armor_class=14,
        speed=30,
        abilities=AbilityScores(
            strength=14,
            dexterity=16,
            constitution=13,
            intelligence=12,
            wisdom=11,
            charisma=13
        ),
        inventory=[],
        active_conditions=[],
        motivation="Gain wealth and power through robbery",
        alignment=Alignment.CHAOTIC_EVIL,
        memory="Leads a gang of bandits in the nearby forest.",
        current_scene="Forest Road"
    )


def get_wise_old_man_npc() -> NPCCharacter:
    """Returns a wise old man NPC for testing."""
    return NPCCharacter(
        name="Elder Thaddeus",
        race="Human",
        char_class=CharacterClass.WIZARD,
        level=8,
        backstory_summary="An ancient wizard who guards old secrets.",
        personality_traits=["Wise", "Cryptic", "Patient"],
        max_hp=40,
        current_hp=40,
        temp_hp=0,
        armor_class=12,
        speed=30,
        abilities=AbilityScores(
            strength=8,
            dexterity=12,
            constitution=13,
            intelligence=19,
            wisdom=18,
            charisma=14
        ),
        inventory=[],
        active_conditions=[],
        motivation="Preserve ancient knowledge and guide worthy heroes",
        alignment=Alignment.LAWFUL_NEUTRAL,
        memory="Has lived for over 100 years studying ancient magic.",
        current_scene="Ancient Library"
    )


def get_friendly_villager_npc() -> NPCCharacter:
    """Returns a friendly villager NPC for testing."""
    return NPCCharacter(
        name="Villager Mary",
        race="Human",
        char_class=CharacterClass.PEASANT,
        level=1,
        backstory_summary="A kind-hearted villager who helps travelers.",
        personality_traits=["Kind", "Hospitable", "Gossipy"],
        max_hp=8,
        current_hp=8,
        temp_hp=0,
        armor_class=10,
        speed=30,
        abilities=AbilityScores(
            strength=10,
            dexterity=10,
            constitution=11,
            intelligence=12,
            wisdom=13,
            charisma=14
        ),
        inventory=[],
        active_conditions=[],
        motivation="Keep her family and village safe",
        alignment=Alignment.NEUTRAL_GOOD,
        memory="Knows everyone in the village and their stories.",
        current_scene="Village Square"
    )


def get_custom_npc(
    name: str,
    char_class: CharacterClass = CharacterClass.PEASANT,
    level: int = 1,
    race: str = "Human",
    max_hp: int = 8,
    current_hp: int = 8,
    strength: int = 10,
    dexterity: int = 10,
    constitution: int = 10,
    intelligence: int = 10,
    wisdom: int = 10,
    charisma: int = 10,
    backstory: str = "",
    traits: list = None, # type: ignore
    motivation: str = "",
    alignment: Alignment = Alignment.TRUE_NEUTRAL,
    memory: str = "",
    current_scene: str = "Unknown"
) -> NPCCharacter:
    """Creates a custom NPC with specified parameters."""
    if traits is None:
        traits = ["Neutral"]

    return NPCCharacter(
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
        active_conditions=[],
        motivation=motivation,
        alignment=alignment,
        memory=memory,
        current_scene=current_scene
    )