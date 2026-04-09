# type: ignore[reportGeneralTypeIssues, reportAttributeAccessIssue, reportArgumentType, reportUndefinedVariable, reportCallIssue]
"""
Character API router

Handles two types of character operations:
1. Character Profiles - Save user's character templates to database (reusable across sessions)
2. In-Session Characters - Create characters within active game sessions
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from backend.src.database.session import get_db
from backend.src.auth.dependencies import get_current_user
from backend.src.models.user import User
from backend.src.game.session_manager import session_manager
from backend.src.repositories.session_repository import SessionRepository
from backend.src.repositories.character_profile_repository import CharacterProfileRepository

router = APIRouter(prefix="/characters", tags=["characters"])


# ===================================================================
# Request/Response Models
# ===================================================================

class CharacterProfileCreateRequest(BaseModel):
    """Request for saving a character profile to user's library."""
    name: str = Field(..., min_length=2, max_length=100)
    race: str = Field(default="Human", max_length=50)
    char_class: str = Field(..., max_length=50)
    level: int = Field(default=1, ge=1, le=20)
    character_data: Optional[Dict[str, Any]] = None
    backstory_summary: Optional[str] = Field(None, max_length=2000)
    personality_traits: Optional[List[str]] = None
    appearance_description: Optional[str] = Field(None, max_length=2000)
    background: Optional[str] = Field(None, max_length=100)
    alignment: Optional[str] = Field(None, max_length=50)
    max_hp: int = Field(default=10, ge=1)
    armor_class: int = Field(default=10)
    speed: int = Field(default=30)
    is_favorite: bool = False


class CharacterProfileResponse(BaseModel):
    """Response with saved character profile information."""
    success: bool
    profile_id: int
    name: str
    race: str
    char_class: str
    level: int
    max_hp: int
    armor_class: int
    speed: int
    message: str


# ===================================================================
# Endpoints
# ===================================================================

@router.post("/", response_model=CharacterProfileResponse)
async def create_or_save_character(
    request: Dict[str, Any],
    db=Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create/save a character.
    
    If request contains 'session_id' → Session-based character creation (AI generated)
    If request does NOT contain 'session_id' → Save as character profile to database
    """
    # Check if this is session-based creation or profile save
    if 'session_id' in request:
        return await _create_character_in_session(request, db, current_user)
    else:
        return await _save_character_profile(request, db, current_user)


async def _save_character_profile(
    request: Dict[str, Any],
    db,
    current_user: User
) -> CharacterProfileResponse:
    """Save a character profile to user's library for reuse across sessions."""
    repo = CharacterProfileRepository(db)
    
    try:
        profile = repo.create(
            user_id=current_user.id,
            name=request.get('name', 'Unnamed Character'),
            race=request.get('race', 'Human'),
            char_class=request.get('char_class', 'Fighter'),
            level=request.get('level', 1),
            character_data=request.get('character_data'),
            backstory_summary=request.get('backstory_summary'),
            personality_traits=request.get('personality_traits'),
            appearance_description=request.get('appearance_description'),
            background=request.get('background'),
            alignment=request.get('alignment'),
            max_hp=request.get('max_hp', 10),
            armor_class=request.get('armor_class', 10),
            speed=request.get('speed', 30),
            is_favorite=request.get('is_favorite', False)
        )
        
        return CharacterProfileResponse(
            success=True,
            profile_id=profile.id,
            name=profile.name,
            race=profile.race,
            char_class=profile.char_class,
            level=profile.level,
            max_hp=profile.max_hp,
            armor_class=profile.armor_class,
            speed=profile.speed,
            message=f"Character '{profile.name}' saved to your library!"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving character profile: {str(e)}")


async def _create_character_in_session(
    request: Dict[str, Any],
    db,
    current_user: User
) -> 'CharacterResponse':
    """Create a character within an active game session."""
    from core.schemas.in_game import Character
    from core.entity.player import Player
    from core.entity.orchestrator import Orchestrator
    
    # Validate required fields
    session_id = request.get('session_id')
    character_name = request.get('character_name')
    character_prompt = request.get('character_prompt', '')
    
    if not session_id or not character_name:
        raise HTTPException(status_code=422, detail="session_id and character_name are required")
    
    repository = SessionRepository(db)

    # Verify session exists in database
    db_session = repository.get_session_by_uuid(session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Verify user has access to session
    is_owner = db_session.owner_id == current_user.id
    participants = repository.get_session_participants(session_id)
    is_participant = any(p.get("user_id") == current_user.id for p in participants)

    if not is_owner and not is_participant:
        raise HTTPException(status_code=403, detail="You don't have access to this session")

    # Get active game session
    game_session = session_manager.get_session(session_id)
    if not game_session:
        raise HTTPException(status_code=400, detail="Session is not active. Please start the session first.")

    # Verify delivery is available
    if not hasattr(game_session, 'delivery') or not game_session.delivery:
        raise HTTPException(status_code=503, detail="Game delivery not available")

    try:
        # Build character prompt
        full_prompt = character_prompt
        if request.get('character_class'):
            full_prompt += f"\nClass: {request.get('character_class')}"
        if request.get('character_race'):
            full_prompt += f"\nRace: {request.get('character_race')}"

        character = None

        # Try AI generation first
        if hasattr(game_session, 'generator') and game_session.generator:
            try:
                character = game_session.generator.generate_one_shot(
                    pydantic_model=Character,
                    prompt=full_prompt
                )
                game_session.logger.info(f"AI Character generated: {character.name}")
            except Exception as e:
                game_session.logger.warning(f"AI generation failed: {e}, using procedural fallback")
                character = None

        # Fallback to procedural generation
        if not character:
            character = _procedural_generate_character(
                name=character_name,
                prompt=character_prompt,
                char_class=request.get('character_class'),
                race=request.get('character_race')
            )
            game_session.logger.info(f"Procedural character generated: {character.name}")

        # Create player orchestrator
        player_orchestrator = Orchestrator(
            generator=game_session.generator,
            logger=game_session.logger.getChild("player_orchestrator")
        )
        player_orchestrator.add_state(game_session)

        # Subscribe to events
        event_queue = game_session.event_pool.subscribe(character.name)

        # Create player
        player = Player(
            character=character,
            event_queuee=event_queue,
            logger=game_session.logger.getChild("player"),
            orchestrator=player_orchestrator
        )
        player.inject_state(game_session)

        # Add to session
        game_session.players.append(player)

        # Notify all players via delivery
        game_session.delivery.session_updated(game_session)

        # Extract stats
        stats = getattr(character, 'stats', None)
        stats_dict = {
            "strength": getattr(stats, 'strength', 10) if stats else 10,
            "dexterity": getattr(stats, 'dexterity', 10) if stats else 10,
            "constitution": getattr(stats, 'constitution', 10) if stats else 10,
            "intelligence": getattr(stats, 'intelligence', 10) if stats else 10,
            "wisdom": getattr(stats, 'wisdom', 10) if stats else 10,
            "charisma": getattr(stats, 'charisma', 10) if stats else 10,
        } if stats else {
            "strength": 10, "dexterity": 10, "constitution": 10,
            "intelligence": 10, "wisdom": 10, "charisma": 10,
        }

        return {
            "success": True,
            "character_name": character.name,
            "character_class": str(getattr(character, 'char_class', 'Unknown')),
            "character_race": getattr(character, 'race', 'Human'),
            "level": getattr(character, 'level', 1),
            "max_hp": getattr(character, 'max_hp', 10),
            "current_hp": getattr(character, 'current_hp', 10),
            "armor_class": getattr(character, 'armor_class', 10),
            "stats": stats_dict,
            "abilities": getattr(character, 'abilities', []),
            "inventory": [item if isinstance(item, dict) else item.model_dump() if hasattr(item, 'model_dump') else str(item) for item in getattr(character, 'inventory', [])],
            "message": f"Character '{character.name}' created successfully and added to session."
        }

    except Exception as e:
        game_session.logger.error(f"Error creating character: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating character: {str(e)}")


# ===================================================================
# Procedural Generation Helper
# ===================================================================

def _procedural_generate_character(
    name: str,
    prompt: str,
    char_class: Optional[str] = None,
    race: Optional[str] = None
) -> 'Character':
    """Procedurally generate a character when AI is unavailable."""
    import random
    from core.schemas.in_game import Character, CharacterClass, AbilityScores, Coordinate2D

    base_stats = 10 + random.randint(-2, 4)
    stats = AbilityScores(
        strength=base_stats + random.randint(-2, 4),
        dexterity=base_stats + random.randint(-2, 4),
        constitution=base_stats + random.randint(-2, 4),
        intelligence=base_stats + random.randint(-2, 4),
        wisdom=base_stats + random.randint(-2, 4),
        charisma=base_stats + random.randint(-2, 4),
    )

    if char_class:
        try:
            character_class = CharacterClass(char_class.upper())
        except ValueError:
            character_class = random.choice([CharacterClass.FIGHTER, CharacterClass.WIZARD, CharacterClass.ROGUE, CharacterClass.CLERIC])
    else:
        character_class = random.choice([CharacterClass.FIGHTER, CharacterClass.WIZARD, CharacterClass.ROGUE, CharacterClass.CLERIC])

    abilities = _generate_abilities_for_class(character_class)
    inventory = _generate_inventory_for_class(character_class)
    max_hp = 25 + stats.constitution + (4 if character_class == CharacterClass.FIGHTER else 0)

    return Character(
        name=name,
        race=race or "Human",
        char_class=character_class,
        level=1,
        backstory_summary=prompt,
        personality_traits=[random.choice(["Brave", "Cautious", "Curious", "Bold", "Thoughtful"])],
        max_hp=max_hp,
        current_hp=max_hp,
        temp_hp=0,
        armor_class=10 + max(0, (stats.dexterity - 10) // 2),
        speed=30,
        stats=stats,
        inventory=inventory,
        active_conditions_list=[],
        resources={"hit_dice": 1},
        position=Coordinate2D(x=0.0, y=0.0),
        abilities=abilities,
    )


def _generate_abilities_for_class(char_class) -> list:
    """Generate abilities based on character class."""
    from core.schemas.in_game import CharacterClass

    if char_class == CharacterClass.FIGHTER:
        return [
            {"name": "Attack", "short_summary": "Make a melee weapon attack dealing 1d8+3 slashing damage", "level": 0, "type": "action"},
            {"name": "Second Wind", "short_summary": "Regain 1d10+1 HP as a bonus action (1/short rest)", "level": 0, "type": "bonus_action"},
            {"name": "Action Surge", "short_summary": "Take one additional action on your turn (1/short rest)", "level": 0, "type": "special"},
        ]
    elif char_class == CharacterClass.WIZARD:
        return [
            {"name": "Fire Bolt", "short_summary": "Ranged spell attack dealing 1d10 fire damage", "level": 0, "type": "action"},
            {"name": "Magic Missile", "short_summary": "Create 3 darts dealing 1d4+1 force damage each", "level": 1, "type": "action"},
            {"name": "Shield", "short_summary": "+5 AC until next turn as a reaction", "level": 1, "type": "reaction"},
        ]
    elif char_class == CharacterClass.ROGUE:
        return [
            {"name": "Attack", "short_summary": "Make a melee weapon attack dealing 1d8+3 piercing damage", "level": 0, "type": "action"},
            {"name": "Sneak Attack", "short_summary": "Deal extra 1d6 damage when you have advantage", "level": 0, "type": "passive"},
            {"name": "Cunning Action", "short_summary": "Dash, Disengage, or Hide as a bonus action", "level": 0, "type": "bonus_action"},
        ]
    else:  # CLERIC
        return [
            {"name": "Attack", "short_summary": "Make a melee weapon attack dealing 1d6+3 bludgeoning damage", "level": 0, "type": "action"},
            {"name": "Healing Word", "short_summary": "Heal a creature for 1d4+3 HP as a bonus action", "level": 1, "type": "bonus_action"},
            {"name": "Guiding Bolt", "short_summary": "Ranged spell attack dealing 1d6 radiant damage", "level": 1, "type": "action"},
        ]


def _generate_inventory_for_class(char_class) -> list:
    """Generate starting inventory based on class."""
    from core.schemas.in_game import CharacterClass

    if char_class == CharacterClass.FIGHTER:
        return [
            {"name": "Longsword", "is_equipped": True, "type": "weapon", "damage": "1d8"},
            {"name": "Shield", "is_equipped": True, "type": "armor", "ac_bonus": 2},
            {"name": "Chain Mail", "is_equipped": True, "type": "armor", "ac": 16},
            {"name": "Rations (3 days)", "is_equipped": False, "type": "consumable"},
            {"name": "Health Potion", "is_equipped": False, "type": "consumable", "healing": "2d4+2"},
        ]
    elif char_class == CharacterClass.WIZARD:
        return [
            {"name": "Quarterstaff", "is_equipped": True, "type": "weapon", "damage": "1d6"},
            {"name": "Spellbook", "is_equipped": True, "type": "tool"},
            {"name": "Robes", "is_equipped": True, "type": "armor", "ac": 12},
            {"name": "Component Pouch", "is_equipped": False, "type": "tool"},
            {"name": "Scroll of Protection", "is_equipped": False, "type": "scroll"},
        ]
    elif char_class == CharacterClass.ROGUE:
        return [
            {"name": "Shortsword", "is_equipped": True, "type": "weapon", "damage": "1d6"},
            {"name": "Dagger (2)", "is_equipped": False, "type": "weapon", "damage": "1d4"},
            {"name": "Leather Armor", "is_equipped": True, "type": "armor", "ac": 11},
            {"name": "Thieves' Tools", "is_equipped": True, "type": "tool"},
            {"name": "Climbing Gear", "is_equipped": False, "type": "tool"},
        ]
    else:  # CLERIC
        return [
            {"name": "Mace", "is_equipped": True, "type": "weapon", "damage": "1d6"},
            {"name": "Shield", "is_equipped": True, "type": "armor", "ac_bonus": 2},
            {"name": "Scale Mail", "is_equipped": True, "type": "armor", "ac": 14},
            {"name": "Holy Symbol", "is_equipped": True, "type": "focus"},
            {"name": "Healing Potion", "is_equipped": False, "type": "consumable", "healing": "2d4+2"},
        ]
