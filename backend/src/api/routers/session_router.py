"""
REST API router для управления игровыми сессиями с поддержкой БД и владения.

Эндпоинты:
- POST /sessions - Создать сессию (требуется аутентификация)
- GET /sessions - Список сессий пользователя (требуется аутентификация)
- GET /sessions/{session_id} - Информация о сессии
- PUT /sessions/{session_id} - Обновить сессию (только владелец)
- DELETE /sessions/{session_id} - Удалить сессию (только владелец)
- POST /sessions/{session_id}/players - Добавить игрока
- DELETE /sessions/{session_id}/players/{player_id} - Удалить игрока
- POST /sessions/{session_id}/start - Запустить игру
- GET /sessions/{session_id}/game_info - Получить данные игры
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
import uuid
import os
from datetime import datetime

from sqlalchemy.orm import Session

from backend.src.config import settings
from backend.src.database.session import get_db
from backend.src.auth.dependencies import get_current_user
from backend.src.models.user import User
from backend.src.models.session import GameSession, SessionStatusEnum
from backend.src.repositories.session_repository import SessionRepository
from backend.src.utils import validate_safe_text, sanitize_string
from backend.src.game.session_manager import session_manager
from backend.src.game.session_factory import session_factory, SessionConfig
from core.game.engine import Session
from core.schemas.in_game import GameModes

router = APIRouter(prefix="/sessions", tags=["sessions"])

# Store for active game sessions (in-memory engine sessions)
# Key: session_uuid, Value: Session engine object
active_game_sessions: Dict[str, Session] = {}

# Store for active players (temporary, until full WebSocket integration)
active_players: Dict[str, Dict[str, any]] = {}

# Store for player ready status in waiting room
# Key: session_id, Value: Dict[user_id, is_ready] - track by user_id to prevent duplicates
waiting_room_ready_status: Dict[str, Dict[int, bool]] = {}


# === Procedural Generation Helpers (Fallback when AI unavailable) ===

import random

class ProceduralGenerator:
    """Procedural content generator for fallback when AI is unavailable."""
    
    # Scene templates based on keywords
    SCENE_TEMPLATES = {
        "tavern": {
            "names": ["The Silver Dragon", "The Broken Sword", "The Laughing Dragon", "The Rusty Anchor", "The Crimson Mug"],
            "descriptions": [
                "A cozy tavern with a roaring fireplace and the smell of roasted meat.",
                "A dimly lit inn where travelers gather to share tales of adventure.",
                "A bustling tavern filled with merchants, mercenaries, and mysterious strangers.",
            ]
        },
        "cave": {
            "names": ["The Whispering Caverns", "The Crystal Cave", "The Shadowed Depths", "The Dragon's Maw", "The Forgotten Mine"],
            "descriptions": [
                "A dark cave where crystals glow with an eerie blue light.",
                "An ancient cavern echoing with the drip of water and distant whispers.",
                "A vast underground chamber with stalactites hanging like swords.",
            ]
        },
        "forest": {
            "names": ["The Whispering Woods", "The Elder Grove", "The Shadowfen Forest", "The Moonlit Thicket", "The Ancient Wood"],
            "descriptions": [
                "A dense forest where sunlight filters through ancient trees.",
                "A mystical woodland where magic lingers in the air.",
                "A dark forest with twisted trees and watchful eyes in the shadows.",
            ]
        },
        "castle": {
            "names": ["Castle Ravenmoor", "The Iron Keep", "Palace of Dawn", "The Obsidian Fortress", "The Crystal Citadel"],
            "descriptions": [
                "A majestic castle with towering spires and fluttering banners.",
                "An ancient fortress weathered by centuries of storms and sieges.",
                "A grand palace of marble and gold, home to a noble court.",
            ]
        },
        "default": {
            "names": ["The Adventurer's Rest", "The Crossroads Inn", "The Traveler's Haven", "The Wayfarer's Lodge"],
            "descriptions": [
                "A welcoming place where adventurers gather before their quests.",
                "A humble establishment offering warm beds and warm meals.",
            ]
        }
    }
    
    CHARACTER_NAMES = ["Aldric", "Brynn", "Cedric", "Dara", "Eldrin", "Faye", "Gareth", "Hanna", "Ivan", "Jora", "Kael", "Lyra", "Magnus", "Nora", "Owen", "Pipa", "Quinn", "Rhea", "Stefan", "Tessa"]
    CHARACTER_SURNAMES = ["Stormwind", "Ironfoot", "Shadowbane", "Lightbringer", "Fireheart", "Frostbeard", "Thunderstrike", "Moonwhisper", "Sunblade", "Nightshade"]
    
    NPC_ROLES = ["tavern keeper", "blacksmith", "merchant", "guard", "wizard", "healer", "thief", "bard", "hunter", "farmer"]
    
    @staticmethod
    def _find_scene_type(prompt: str) -> str:
        """Find scene type from prompt keywords."""
        prompt_lower = prompt.lower()
        if any(word in prompt_lower for word in ["tavern", "inn", "pub", "bar", "ale", "beer"]):
            return "tavern"
        if any(word in prompt_lower for word in ["cave", "cavern", "mine", "underground", "dungeon"]):
            return "cave"
        if any(word in prompt_lower for word in ["forest", "wood", "tree", "grove", "wilderness"]):
            return "forest"
        if any(word in prompt_lower for word in ["castle", "fortress", "palace", "keep", "tower"]):
            return "castle"
        return "default"
    
    @classmethod
    def generate_scene(cls, prompt: str):
        """Generate a scene procedurally."""
        from core.schemas.in_game import SceneNode, Coordinate2D
        
        scene_type = cls._find_scene_type(prompt)
        template = cls.SCENE_TEMPLATES.get(scene_type, cls.SCENE_TEMPLATES["default"])
        
        name = random.choice(template["names"])
        description = random.choice(template["descriptions"])
        
        # Add prompt-specific details
        if prompt:
            description = f"{description} {prompt}"
        
        return SceneNode(
            name=name,
            description=description,
            objects=[],
            center_position=Coordinate2D(x=10.0, y=10.0),
            dimensions=Coordinate2D(x=20.0, y=20.0),
            scale_unit="feet"
        )
    
    @classmethod
    def generate_character(cls, name: str = None, prompt: str = ""):
        """Generate a character procedurally."""
        from core.schemas.in_game import Character, CharacterClass, AbilityScores
        
        char_name = name or f"{random.choice(cls.CHARACTER_NAMES)} {random.choice(cls.CHARACTER_SURNAMES)}"
        
        # Random stats with some variation
        base_stats = 10 + random.randint(-2, 4)
        stats = AbilityScores(
            strength=base_stats + random.randint(-2, 4),
            dexterity=base_stats + random.randint(-2, 4),
            constitution=base_stats + random.randint(-2, 4),
            intelligence=base_stats + random.randint(-2, 4),
            wisdom=base_stats + random.randint(-2, 4),
            charisma=base_stats + random.randint(-2, 4),
        )
        
        # Random class
        char_class = random.choice([CharacterClass.FIGHTER, CharacterClass.WIZARD, CharacterClass.ROGUE, CharacterClass.CLERIC])
        
        # Generate abilities based on class
        abilities = cls._generate_abilities_for_class(char_class)
        
        # Generate inventory based on class
        inventory = cls._generate_inventory_for_class(char_class)
        
        max_hp = 25 + stats.constitution + (4 if char_class == CharacterClass.FIGHTER else 0)
        
        return Character(
            name=char_name,
            race="Human",
            char_class=char_class,
            level=1,
            backstory_summary=prompt or f"A young adventurer seeking fame and fortune.",
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
            active_conditions="",
            proficiency_bonus=2,
            is_alive=True,
            initiative_bonus=10 + max(0, (stats.dexterity - 10) // 2),
            short_summary=f"{char_name} the {char_class.value}",
            alignment=random.choice(["Neutral Good", "Lawful Neutral", "Chaotic Good", "True Neutral"]),
            appearance=f"A {random.choice(['tall', 'short', 'average'])} human with {random.choice(['bright', 'steady', 'keen'])} eyes.",
            age=20 + random.randint(0, 20),
        )
    
    @classmethod
    def _generate_abilities_for_class(cls, char_class):
        """Generate abilities based on character class."""
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
    
    @classmethod
    def _generate_inventory_for_class(cls, char_class):
        """Generate starting inventory based on class."""
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
    
    @classmethod
    def generate_npc(cls, role: str = None, prompt: str = ""):
        """Generate an NPC procedurally."""
        from core.schemas.in_game import NPCCharacter, CharacterClass, AbilityScores
        
        npc_role = role or random.choice(cls.NPC_ROLES)
        npc_name = f"{random.choice(cls.CHARACTER_NAMES)} the {npc_role.title()}"
        
        stats = AbilityScores(
            strength=10 + random.randint(-2, 2),
            dexterity=10 + random.randint(-2, 2),
            constitution=10 + random.randint(-2, 2),
            intelligence=10 + random.randint(-2, 2),
            wisdom=10 + random.randint(-2, 2),
            charisma=10 + random.randint(-2, 2),
        )
        
        return NPCCharacter(
            name=npc_name,
            race="Human",
            char_class=CharacterClass.COMMONER,
            level=1,
            backstory_summary=prompt or f"A local {npc_role} going about their daily business.",
            personality_traits=[random.choice(["Friendly", "Reserved", "Talkative", "Suspicious"])],
            max_hp=15 + stats.constitution,
            current_hp=15 + stats.constitution,
            temp_hp=0,
            armor_class=10,
            speed=30,
            stats=stats,
            inventory=[
                {"name": "Common Clothes", "is_equipped": True, "type": "clothing"},
                {"name": "Pouch with 5 gp", "is_equipped": False, "type": "container"},
            ],
            active_conditions_list=[],
            resources={},
            position=Coordinate2D(x=15.0, y=15.0),
            abilities=[
                {"name": "Help", "short_summary": "Give advantage to an ally's next ability check or attack", "level": 0, "type": "action"},
            ],
            active_conditions="",
            proficiency_bonus=2,
            is_alive=True,
            initiative_bonus=10,
            short_summary=f"{npc_name}",
            motivation=random.choice(["To earn a living", "To protect their family", "To gain knowledge", "To survive"]),
            alignment="Neutral",
            memory="",
            current_scene=None,  # Will be set by caller
            occupation=npc_role.title(),
            appearance=f"A {random.choice ['middle-aged', 'young', 'elderly']} human with a {random.choice(['warm', 'stern', 'tired'])} expression.",
        )


# === Procedural Generator Instance ===
procedural_gen = ProceduralGenerator()


# === Schemas ===

class SessionCreateRequest(BaseModel):
    """Запрос на создание сессии."""
    session_name: str = Field(..., description="Название сессии", min_length=2, max_length=100)
    game_mode: str = Field(default="STORY", description="Режим игры: STORY или COMBAT")
    max_players: int = Field(default=5, description="Максимум игроков", ge=1, le=20)
    description: Optional[str] = Field(None, description="Описание сессии", max_length=500)
    guide: Optional[str] = Field(None, description="Сюжетная подсказка для AI", max_length=2000)
    is_public: bool = Field(default=False, description="Публичная сессия")
    
    # Настройки AI (опционально)
    gemini_model: str = Field(default="gemini-2.0-flash", description="Модель Gemini")

    @validator('session_name')
    def validate_session_name(cls, v):
        v = sanitize_string(v, max_length=100)
        if len(v) < 2:
            raise ValueError("Session name must be at least 2 characters")
        return v

    @validator('description')
    def validate_description(cls, v):
        if v:
            return validate_safe_text(v, "Description")
        return v

    @validator('guide')
    def validate_guide(cls, v):
        if v:
            return validate_safe_text(v, "Guide")
        return v


class PlayerResponse(BaseModel):
    """Информация об игроке."""
    player_id: str
    player_name: str
    character_name: Optional[str]
    connected: bool
    role: str = "player"
    is_ready: bool = False  # Ready status for waiting room


class NPCResponse(BaseModel):
    """Информация об NPC."""
    name: str
    race: str
    char_class: str
    alignment: Optional[str] = None
    level: int = 1
    current_hp: int = 10
    max_hp: int = 10
    armor_class: int = 10
    speed: int = 30
    is_alive: bool = True
    stats: Dict[str, int] = Field(default_factory=lambda: {
        "strength": 10, "dexterity": 10, "constitution": 10,
        "intelligence": 10, "wisdom": 10, "charisma": 10,
    })
    abilities: List[Dict[str, Any]] = Field(default_factory=list)
    inventory: List[Dict[str, Any]] = Field(default_factory=list)


class SessionResponse(BaseModel):
    """Ответ с информацией о сессии."""
    session_id: str  # UUID
    session_name: str
    game_mode: str
    player_count: int
    status: str
    description: Optional[str] = None
    owner_id: int
    owner_name: Optional[str] = None
    created_at: str
    is_owner: bool = False  # True if current user is the owner
    players: List[PlayerResponse] = Field(default_factory=list)  # Players in session
    npcs: List[NPCResponse] = Field(default_factory=list)  # NPCs in session


class SessionListResponse(BaseModel):
    """Список сессий."""
    sessions: List[SessionResponse]
    total: int


class SessionUpdateRequest(BaseModel):
    """Запрос на обновление сессии."""
    session_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    guide: Optional[str] = Field(None, max_length=2000)
    max_players: Optional[int] = Field(None, ge=1, le=20)
    is_public: Optional[bool] = None
    
    @validator('session_name')
    def validate_session_name(cls, v):
        if v:
            v = sanitize_string(v, max_length=100)
            if len(v) < 2:
                raise ValueError("Session name must be at least 2 characters")
        return v


class PlayerJoinRequest(BaseModel):
    """Запрос на присоединение игрока."""
    player_name: str = Field(..., description="Имя игрока", min_length=2, max_length=100)
    character_name: Optional[str] = Field(None, description="Имя персонажа", max_length=100)

    @validator('player_name')
    def validate_player_name(cls, v):
        v = sanitize_string(v, max_length=100)
        if len(v) < 2:
            raise ValueError("Player name must be at least 2 characters")
        return v


class SessionStartRequest(BaseModel):
    """Запрос на запуск игровой сессии."""
    scene_prompt: Optional[str] = Field(None, description="Описание начальной сцены", max_length=2000)
    character_prompts: List[str] = Field(default_factory=list, description="Описания персонажей")
    npc_prompts: List[str] = Field(default_factory=list, description="Описания NPC")
    # Frontend GameSetup fields (alternative format)
    wishes: Optional[str] = Field(None, description="Adventure preferences from GameSetup", max_length=1000)
    character_choice: Optional[str] = Field(None, description="Character selection choice")
    character_description: Optional[str] = Field(None, description="Character description for AI creation")
    # Extra field from frontend (ignored)
    sessionId: Optional[str] = Field(None, description="Session ID from frontend")
    
    class Config:
        extra = "ignore"  # Ignore extra fields from frontend


class SessionInfoResponse(BaseModel):
    """Расширенная информация о сессии."""
    session_id: str
    session_name: str
    game_mode: str
    player_count: int
    max_players: int
    status: str
    description: Optional[str] = None
    owner_id: int
    owner_name: str
    is_owner: bool
    players: List[PlayerResponse] = []


class WaitingRoomResponse(BaseModel):
    """Waiting room information."""
    session_id: str
    session_name: str
    game_mode: str
    player_count: int
    max_players: int
    status: str
    description: Optional[str] = None
    owner_id: int
    owner_name: str
    is_owner: bool
    players: List[PlayerResponse] = []


class PlayerReadyRequest(BaseModel):
    """Player ready status update."""
    is_ready: bool


class AIInitializeRequest(BaseModel):
    """Запрос на AI инициализацию сессии."""
    scene_prompt: Optional[str] = Field(None, description="Описание начальной сцены", max_length=2000)
    character_prompts: List[str] = Field(default_factory=list, description="Описания персонажей")
    npc_prompts: List[str] = Field(default_factory=list, description="Описания NPC")
    wishes: Optional[str] = Field(None, description="Adventure preferences", max_length=2000)


class AIInitializeResponse(BaseModel):
    """Ответ AI инициализации."""
    success: bool
    session_id: str
    scene_description: str
    characters_count: int
    npcs_count: int
    message: str


class PlayerActionRequest(BaseModel):
    """Запрос действия игрока."""
    character_name: str = Field(..., description="Имя персонажа", min_length=1, max_length=100)
    action: str = Field(..., description="Описание действия", min_length=1, max_length=2000)


class PlayerActionResponse(BaseModel):
    """Ответ действия игрока."""
    success: bool
    dm_response: str
    events: List[Dict[str, Any]]
    game_state: Dict[str, Any]
    error: Optional[str] = None


class SessionStateResponse(BaseModel):
    """Состояние сессии."""
    success: bool
    scene: Optional[Dict[str, Any]]
    players: List[Dict[str, Any]]
    npcs: List[Dict[str, Any]]
    messages: List[Dict[str, Any]]
    turn_queue: List[Any]


# === Helper Functions ===

def get_session_repository(db: Session) -> SessionRepository:
    """Get session repository instance."""
    return SessionRepository(db)


def get_session_by_uuid_or_404(
    session_uuid: str,
    repository: SessionRepository
) -> GameSession:
    """Get session by UUID or raise 404."""
    session = repository.get_session_by_uuid(session_uuid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


def verify_session_owner(
    session: GameSession,
    current_user: User
) -> None:
    """Verify that current user is the session owner."""
    if session.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized: Only the session owner can perform this action"
        )


# === Endpoints ===

@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(
    request: SessionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создать новую игровую сессию.
    
    Требуется аутентификация. Сессия будет закреплена за создателем.
    """
    import logging
    logger = logging.getLogger(__name__)

    session_uuid = str(uuid.uuid4())
    logger.info(f"Creating session: {session_uuid} - {request.session_name} for user {current_user.id}")

    repository = get_session_repository(db)

    try:
        # Step 1: Create session in database FIRST
        db_session = repository.create_session(
            session_uuid=session_uuid,
            session_name=request.session_name,
            owner_id=current_user.id,
            game_mode=request.game_mode,
            max_players=request.max_players,
            description=request.description,
            guide=request.guide,
            gemini_model=request.gemini_model
        )

        logger.info(f"Database session created: {db_session.id} (UUID: {db_session.session_uuid}, owner_id={db_session.owner_id})")

        # Step 2: Create in-memory game session with the SAME UUID
        config = SessionConfig(
            session_name=request.session_name,
            game_mode=request.game_mode,
            max_players=request.max_players,
            description=request.description,
            guide=request.guide,
            gemini_model=request.gemini_model
        )

        # Pass the session_uuid to factory so it uses the same ID
        game_session = session_factory.create_session(config, session_id=session_uuid)
        active_game_sessions[session_uuid] = game_session

        logger.info(f"Game session created in memory: {session_uuid}")

        # Step 3: Add owner as participant in database
        participant = repository.add_participant(
            session_uuid=session_uuid,
            player_uuid=str(uuid.uuid4()),
            player_name=current_user.username,
            user_id=current_user.id,
            role="owner"
        )

        logger.info(f"Owner added as participant: {participant.id if participant else 'FAILED'}")

        # Step 4: Verify session is in database
        verify_session = repository.get_session_by_uuid(session_uuid)
        if not verify_session:
            logger.error(f"VERIFICATION FAILED: Session not found in database after creation!")
        else:
            logger.info(f"VERIFIED: Session exists in database with owner_id={verify_session.owner_id}")

        return SessionResponse(
            session_id=db_session.session_uuid,
            session_name=db_session.session_name,
            game_mode=db_session.game_mode.value,
            player_count=1,
            status=db_session.status.value,
            description=db_session.description,
            owner_id=db_session.owner_id,
            owner_name=current_user.username,
            created_at=db_session.created_at.isoformat(),
            is_owner=True
        )

    except ImportError as e:
        logger.error(f"ImportError: {e}")
        raise HTTPException(status_code=503, detail=f"SKLS dependencies not installed: {str(e)}")
    except Exception as e:
        logger.error(f"Exception: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить список сессий пользователя.
    
    Возвращает только сессии, принадлежащие текущему пользователю.
    """
    repository = get_session_repository(db)
    
    # Get only user's own sessions
    db_sessions = repository.get_owner_sessions(owner_id=current_user.id, active_only=True)
    
    session_list = []
    for db_session in db_sessions:
        # Check if session has active game engine
        game_session = active_game_sessions.get(db_session.session_uuid)
        player_count = 0
        
        if game_session:
            player_count = len(game_session.players)
        else:
            # Get from DB
            participants = repository.get_session_participants(db_session.session_uuid)
            player_count = len([p for p in participants if p.is_connected])
        
        session_list.append(SessionResponse(
            session_id=db_session.session_uuid,
            session_name=db_session.session_name,
            game_mode=db_session.game_mode.value,
            player_count=player_count,
            status=db_session.status.value,
            description=db_session.description,
            owner_id=db_session.owner_id,
            owner_name=current_user.username,
            created_at=db_session.created_at.isoformat(),
            is_owner=True
        ))
    
    return SessionListResponse(
        sessions=session_list,
        total=len(session_list)
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить информацию о конкретной сессии."""
    repository = get_session_repository(db)

    db_session = get_session_by_uuid_or_404(session_id, repository)

    # Get player count
    game_session = active_game_sessions.get(session_id)
    player_count = 0
    
    # Get players from DB
    participants = repository.get_session_participants(session_id)
    
    # Get ready status for this session
    session_ready_status = waiting_room_ready_status.get(session_id, {})
    
    players = []
    if game_session:
        player_count = len(game_session.players)
    else:
        player_count = len([p for p in participants if p.is_connected])
    
    # Build players list with ready status
    for p in participants:
        is_ready = session_ready_status.get(p.user_id, False) if p.user_id else False
        players.append(PlayerResponse(
            player_id=p.player_uuid,
            player_name=p.player_name,
            character_name=p.character_name,
            connected=p.is_connected,
            role=p.role,
            is_ready=is_ready
        ))

    return SessionResponse(
        session_id=db_session.session_uuid,
        session_name=db_session.session_name,
        game_mode=db_session.game_mode.value,
        player_count=player_count,
        status=db_session.status.value,
        description=db_session.description,
        owner_id=db_session.owner_id,
        owner_name=current_user.username if db_session.owner_id == current_user.id else None,
        created_at=db_session.created_at.isoformat(),
        is_owner=(db_session.owner_id == current_user.id),
        players=players
    )


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    request: SessionUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновить сессию.
    
    Только владелец может обновлять сессию.
    """
    repository = get_session_repository(db)
    
    db_session = get_session_by_uuid_or_404(session_id, repository)
    verify_session_owner(db_session, current_user)
    
    # Update fields
    if request.session_name is not None:
        db_session.session_name = request.session_name
    if request.description is not None:
        db_session.description = request.description
    if request.guide is not None:
        db_session.guide = request.guide
    if request.max_players is not None:
        db_session.max_players = request.max_players
    if request.is_public is not None:
        db_session.is_public = request.is_public
        
    db_session.updated_at = datetime.now()
    db.commit()
    db.refresh(db_session)
    
    # Get player count
    participants = repository.get_session_participants(session_id)
    player_count = len([p for p in participants if p.is_connected])
    
    return SessionResponse(
        session_id=db_session.session_uuid,
        session_name=db_session.session_name,
        game_mode=db_session.game_mode.value,
        player_count=player_count,
        status=db_session.status.value,
        description=db_session.description,
        owner_id=db_session.owner_id,
        owner_name=current_user.username,
        created_at=db_session.created_at.isoformat(),
        is_owner=True
    )


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Удалить сессию.
    
    Только владелец может удалить сессию. Это действие необратимо!
    """
    repository = get_session_repository(db)
    
    db_session = get_session_by_uuid_or_404(session_id, repository)
    verify_session_owner(db_session, current_user)
    
    # Remove from active game sessions
    game_session = active_game_sessions.get(session_id)
    if game_session:
        await session_manager.remove_session(session_id)
        del active_game_sessions[session_id]
    
    # Delete from database
    repository.delete_session(session_id, owner_id=current_user.id)


@router.post("/{session_id}/start", response_model=SessionResponse)
async def start_session(
    session_id: str,
    request: SessionStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Запустить игровую сессию с инициализацией сцены и персонажей.

    Только владелец может запустить сессию.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"[START] Session {session_id} - Request data: {request.dict()}")
    
    repository = get_session_repository(db)

    db_session = get_session_by_uuid_or_404(session_id, repository)
    verify_session_owner(db_session, current_user)

    # Get or create game session
    game_session = active_game_sessions.get(session_id)
    logger.info(f"[START] active_game_sessions check: {session_id} - found: {game_session is not None}")

    if not game_session:
        # Session exists in DB but not in memory - need to initialize it
        logger.warning(f"[START] Session {session_id} found in DB but not in memory. Initializing...")

        # Initialize the game session from DB
        try:
            config = SessionConfig(
                session_name=db_session.session_name,
                game_mode=db_session.game_mode.value,
                max_players=db_session.max_players,
                description=db_session.description,
                guide=db_session.guide,
                gemini_model=db_session.gemini_model or "gemini-2.0-flash"
            )
            logger.info(f"[START] Creating session factory config: {config.session_name}")
            game_session = session_factory.create_session(config, session_id=session_id)
            active_game_sessions[session_id] = game_session
            logger.info(f"[START] Session {session_id} created with generator: {hasattr(game_session, 'generator')}")
        except Exception as e:
            logger.error(f"[START] Failed to create session: {e}", exc_info=True)
            raise HTTPException(
                status_code=400,
                detail=f"Session not initialized: {str(e)}. Please recreate the session."
            )
    else:
        logger.info(f"[START] Session {session_id} found in memory")

    logger.info(f"[START] Game session found, starting with wishes={request.wishes}, character_description={request.character_description}")

    # FORCE fresh generation - clear any existing session data
    logger.info(f"[START] === FORCING FRESH GENERATION - Clearing old session data ===")
    game_session.current_scene = None
    if hasattr(game_session, 'players'):
        game_session.players.clear()
    if hasattr(game_session, 'npcs'):
        game_session.npcs.clear()
    
    try:
        # Initialize scene and characters using AI
        from core.schemas.in_game import SceneNode, Coordinate2D, UnifiedObject, ObjectType
        from core.entity.player import Player
        from core.schemas.in_game import Character, CharacterClass, AbilityScores
        from core.entity.orchestrator import Orchestrator

        # Use wishes as scene prompt - create diverse fantasy prompts if not provided
        scene_prompt = request.wishes or request.scene_prompt
        if not scene_prompt:
            # Random fantasy scene prompts for variety
            random_prompts = [
                "A bustling medieval marketplace in a magical city where wizards sell potions alongside merchants",
                "An ancient forest temple overgrown with glowing vines, sacred to forgotten nature gods",
                "A pirate ship sailing through a stormy sea near a mysterious cursed island",
                "A dwarven mining colony deep underground, illuminated by glowing crystals",
                "A floating castle in the clouds, accessible only by giant birds or magic",
                "A haunted swamp where will-o'-wisps guide travelers to hidden treasure or doom",
                "A gladiator arena in a desert city, where champions fight for freedom and fame",
                "An enchanted library where books come alive and knowledge is guarded by magical beasts",
                "A volcanic fortress of a dark lord, surrounded by rivers of lava and obsidian towers",
                "A peaceful elven village hidden in misty mountains, protected by ancient wards"
            ]
            scene_prompt = random.choice(random_prompts)
            logger.info(f"[START] Using random scene prompt: {scene_prompt[:80]}...")

        # ALWAYS generate fresh scene
        logger.info(f"[START] Generating fresh scene with AI: {scene_prompt[:100]}...")
        try:
            if hasattr(game_session, 'generator') and game_session.generator:
                scene = game_session.generator.generate_one_shot(
                    pydantic_model=SceneNode,
                    prompt=scene_prompt
                )
                logger.info(f"[START] Scene generated: {scene.name}")
                game_session.current_scene = scene
                logger.info(f"[START] Scene assigned to game_session")
            else:
                logger.warning("[START] No generator available, using procedural fallback scene")
                # Procedural scene generation based on wishes
                scene = procedural_gen.generate_scene(scene_prompt)
                logger.info(f"[START] Procedural scene generated: {scene.name}")
                game_session.current_scene = scene
        except Exception as e:
            logger.error(f"[START] Scene generation error: {e}", exc_info=True)
            scene = procedural_gen.generate_scene(scene_prompt)
            logger.info(f"[START] Procedural scene generated (error fallback): {scene.name}")
            game_session.current_scene = scene

        scene = game_session.current_scene

        # Update DB
        repository.update_session_scene(session_id, game_session.current_scene.name, owner_id=current_user.id)
        repository.update_session_status(session_id, "running", owner_id=current_user.id)

        # Initialize player characters - ALWAYS create at least one character with random variety
        character_prompts_to_use = request.character_prompts
        if request.character_description and not character_prompts_to_use:
            character_prompts_to_use = [request.character_description]

        # If no character prompts, use a random diverse character prompt
        if not character_prompts_to_use or len(character_prompts_to_use) == 0:
            # Random D&D character prompts for variety
            random_character_prompts = [
                "A half-elf bard with a magical lute who knows secrets of the ancient dragons",
                "A dwarf paladin sworn to protect the innocent, wielding a holy warhammer",
                "A human wizard specializing in fire magic, seeking the lost spells of power",
                "An elf ranger with a wolf companion, guardian of the mystical forests",
                "A tiefling rogue with shadow powers, searching for redemption",
                "A halfling cleric of the harvest god, spreading joy and healing wherever they go",
                "A dragonborn sorcerer with lightning breath, destined for greatness",
                "A gnome artificer with mechanical inventions and a clockwork companion",
                "A half-orc barbarian with a heart of gold, protecting their adopted family",
                "A human monk mastering the elements, seeking inner peace through adventure"
            ]
            character_prompts_to_use = [random.choice(random_character_prompts)]
            logger.info(f"[START] Using random character prompt for variety")

        logger.info(f"[START] Generating {len(character_prompts_to_use)} characters...")

        # Generate characters using AI or procedural generation
        for i, prompt in enumerate(character_prompts_to_use):
            logger.info(f"[START] Generating character {i+1}: {prompt[:100]}...")
            character = None
            
            # Try AI generation first
            if hasattr(game_session, 'generator') and game_session.generator:
                try:
                    character = game_session.generator.generate_one_shot(
                        pydantic_model=Character,
                        prompt=prompt
                    )
                    logger.info(f"[START] ✓ AI Character generated: {character.name}")
                except Exception as e:
                    logger.warning(f"[START] AI generation failed: {e}, using procedural fallback")
                    character = None
            
            # Use procedural generator if AI failed or unavailable
            if not character:
                try:
                    character = procedural_gen.generate_character(name=None, prompt=prompt)
                    logger.info(f"[START] ✓ Procedural character generated: {character.name} ({character.char_class.value})")
                except Exception as e:
                    logger.error(f"[START] Procedural generation failed: {e}")
                    continue  # Skip this character

            # Create player with character
            try:
                logger.info(f"[START] Creating player object for {character.name}...")
                player_orchestrator = Orchestrator(
                    generator=game_session.generator,
                    logger=game_session.logger.getChild("player_orchestrator")
                )
                player_orchestrator.add_state(game_session)

                event_queue = game_session.event_pool.subscribe(character.name)

                player = Player(
                    character=character,
                    event_queuee=event_queue,
                    logger=game_session.logger.getChild("player"),
                    orchestrator=player_orchestrator
                )
                player.inject_state(game_session)
                game_session.players.append(player)
                logger.info(f"[START] ✓ Character {character.name} added to session. Total players: {len(game_session.players)}")
            except Exception as e:
                logger.error(f"[START] Failed to create player: {e}", exc_info=True)
                # Continue anyway - we'll try procedural fallback for next character

        logger.info(f"[START] Session already has {len(game_session.players)} players")

        # Initialize NPCs using procedural generation with random variety
        npc_prompts_to_use = request.npc_prompts
        if not npc_prompts_to_use or len(npc_prompts_to_use) == 0:
            # Random NPC prompts for variety
            random_npc_prompts = [
                'A mysterious hooded figure with glowing eyes who knows ancient secrets',
                'A cheerful tavern keeper who hears all the local gossip and rumors',
                'A battle-scarred mercenary captain looking for new recruits',
                'A young apprentice wizard who lost their master to dark magic',
                'A cunning merchant selling exotic goods from distant lands',
                'A hermit druid who can speak with animals and plants',
                'A retired adventurer with tales of legendary treasures',
                'A cultist seeking redemption after leaving a dark order',
                'A fairy queen's messenger with urgent news for the kingdom',
                'A blacksmith who forges magical weapons in secret'
            ]
            # Pick 2 random NPCs
            npc_prompts_to_use = random.sample(random_npc_prompts, 2)
            logger.info(f"[START] Using random NPC prompts for variety")

        logger.info(f"[START] Generating {len(npc_prompts_to_use)} NPCs...")

        for i, prompt in enumerate(npc_prompts_to_use):
            try:
                logger.info(f"[START] Generating NPC {i+1}: {prompt[:50]}...")
                # Use procedural generator for NPCs
                npc_character = procedural_gen.generate_npc(role=None, prompt=prompt)
                npc_character.current_scene = scene.name
                logger.info(f"[START] ✓ Procedural NPC generated: {npc_character.name} ({npc_character.occupation})")
                
                logger.info(f"[START] Adding NPC to session...")
                game_session._init_npc(npc_character)
                logger.info(f"[START] ✓ NPC {npc_character.name} added. Total NPCs: {len(game_session.npcs)}")
            except Exception as e:
                logger.error(f"[START] NPC generation error: {e}", exc_info=True)

        logger.info(f"[START] === Session initialized: {len(game_session.players)} players, {len(game_session.npcs)} NPCs ===")

        # Send welcome message
        game_session.delivery.master_message(
            f"Welcome to {scene.name}! {scene.description}"
        )
        game_session.delivery.session_updated(game_session)

        # Build NPCs list for response
        npcs_response = []
        for npc in game_session.npcs:
            if hasattr(npc, 'character'):
                char = npc.character
                stats = getattr(char, 'stats', None)
                
                # Convert abilities to dict format
                abilities_data = []
                if hasattr(char, 'abilities') and char.abilities:
                    for ability in char.abilities:
                        if isinstance(ability, dict):
                            abilities_data.append(ability)
                        else:
                            abilities_data.append({
                                "name": getattr(ability, 'name', 'Unknown'),
                                "short_summary": getattr(ability, 'short_summary', ''),
                                "level": getattr(ability, 'level', 0),
                                "type": getattr(ability, 'type', 'action'),
                            })
                
                # Convert inventory to dict format
                inventory_data = []
                if hasattr(char, 'inventory') and char.inventory:
                    for item in char.inventory:
                        if isinstance(item, dict):
                            inventory_data.append(item)
                        else:
                            inventory_data.append({
                                "name": getattr(item, 'name', 'Unknown'),
                                "is_equipped": getattr(item, 'is_equipped', False),
                                "type": getattr(item, 'type', 'item'),
                            })
                
                npcs_response.append(NPCResponse(
                    name=getattr(char, 'name', 'Unknown'),
                    race=getattr(char, 'race', 'Human'),
                    char_class=str(getattr(char, 'char_class', 'Commoner')),
                    alignment=getattr(char, 'alignment', 'Neutral'),
                    level=getattr(char, 'level', 1),
                    current_hp=getattr(char, 'current_hp', 10),
                    max_hp=getattr(char, 'max_hp', 10),
                    armor_class=getattr(char, 'armor_class', 10),
                    speed=getattr(char, 'speed', 30),
                    is_alive=getattr(char, 'is_alive', True),
                    stats={
                        "strength": getattr(stats, 'strength', 10) if stats else 10,
                        "dexterity": getattr(stats, 'dexterity', 10) if stats else 10,
                        "constitution": getattr(stats, 'constitution', 10) if stats else 10,
                        "intelligence": getattr(stats, 'intelligence', 10) if stats else 10,
                        "wisdom": getattr(stats, 'wisdom', 10) if stats else 10,
                        "charisma": getattr(stats, 'charisma', 10) if stats else 10,
                    } if stats else {
                        "strength": 10, "dexterity": 10, "constitution": 10,
                        "intelligence": 10, "wisdom": 10, "charisma": 10,
                    },
                    abilities=abilities_data,
                    inventory=inventory_data,
                ))

        return SessionResponse(
            session_id=session_id,
            session_name=db_session.session_name,
            game_mode=db_session.game_mode.value,
            player_count=len(game_session.players),
            status="running",
            description=db_session.description,
            owner_id=db_session.owner_id,
            owner_name=current_user.username,
            created_at=db_session.created_at.isoformat(),
            is_owner=True,
            players=[
                PlayerResponse(
                    player_id=f"player_{i}",
                    player_name=getattr(p.character, 'name', 'Unknown') if hasattr(p, 'character') else f"Player_{i}",
                    character_name=getattr(p.character, 'name', None) if hasattr(p, 'character') else None,
                    connected=True,
                    role="player"
                ) for i, p in enumerate(game_session.players)
            ],
            npcs=npcs_response
        )
        
    except Exception as e:
        game_session.logger.error(f"Ошибка при запуске сессии: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при запуске сессии: {str(e)}"
        )


@router.get("/{session_id}/info", response_model=SessionInfoResponse)
async def get_session_info(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get extended session information."""
    repository = get_session_repository(db)
    
    db_session = get_session_by_uuid_or_404(session_id, repository)
    
    # Get game session
    game_session = active_game_sessions.get(session_id)
    
    # Get players
    players = []
    player_count = 0
    
    if game_session:
        player_count = len(game_session.players)
        # Get from active game session
        for i, player in enumerate(game_session.players):
            if hasattr(player, 'character'):
                char = player.character
                players.append(PlayerResponse(
                    player_id=f"player_{i}",
                    player_name=getattr(char, 'name', 'Unknown'),
                    character_name=getattr(char, 'name', None),
                    connected=True,
                    role="player"
                ))
    else:
        # Get from DB
        participants = repository.get_session_participants(session_id)
        player_count = len(participants)
        for p in participants:
            players.append(PlayerResponse(
                player_id=p.player_uuid,
                player_name=p.player_name,
                character_name=p.character_name,
                connected=p.is_connected,
                role=p.role
            ))
    
    return SessionInfoResponse(
        session_id=db_session.session_uuid,
        session_name=db_session.session_name,
        game_mode=db_session.game_mode.value,
        player_count=player_count,
        max_players=db_session.max_players,
        status=db_session.status.value,
        description=db_session.description,
        owner_id=db_session.owner_id,
        owner_name=current_user.username if db_session.owner_id == current_user.id else "Unknown",
        is_owner=(db_session.owner_id == current_user.id),
        players=players
    )


@router.post("/{session_id}/players", response_model=PlayerResponse)
async def join_session(
    session_id: str,
    request: PlayerJoinRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Join a session as a player.

    Returns player_id for WebSocket connection.
    Each player can only join once per session.
    """
    repository = get_session_repository(db)

    # Validate session exists
    db_session = get_session_by_uuid_or_404(session_id, repository)

    # Check if session is active
    if db_session.status != SessionStatusEnum.RUNNING and db_session.status != SessionStatusEnum.CREATED:
        raise HTTPException(
            status_code=400,
            detail=f"Session is not accepting players (status: {db_session.status.value})"
        )

    # Check if player already joined (by user_id or player_name)
    existing_participants = repository.get_session_participants(session_id)
    
    # Check if current user already joined
    for participant in existing_participants:
        if participant.user_id == current_user.id:
            # User already joined - return existing player_id
            return PlayerResponse(
                player_id=participant.player_uuid,
                player_name=participant.player_name,
                character_name=participant.character_name,
                connected=participant.is_connected,
                role=participant.role
            )
        # Also check by player_name for guest users
        if participant.player_name == request.player_name and participant.user_id is None:
            raise HTTPException(
                status_code=400,
                detail=f"Player '{request.player_name}' is already in this session"
            )

    # Check max players
    if len(existing_participants) >= db_session.max_players:
        raise HTTPException(
            status_code=400,
            detail=f"Session is full (max {db_session.max_players} players)"
        )

    # Determine role - owner gets 'owner' role
    role = "owner" if db_session.owner_id == current_user.id else "player"

    # Generate player ID
    player_id = str(uuid.uuid4())

    # Add player to session
    participant = repository.add_participant(
        session_uuid=session_id,
        player_uuid=player_id,
        player_name=request.player_name,
        user_id=current_user.id,
        character_name=request.character_name,
        role=role
    )

    if not participant:
        raise HTTPException(status_code=500, detail="Failed to add player to session")

    return PlayerResponse(
        player_id=player_id,
        player_name=request.player_name,
        character_name=request.character_name,
        connected=True,
        role=role
    )


@router.delete("/{session_id}/players/{player_id}", status_code=204)
async def leave_session(
    session_id: str,
    player_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove a player from a session.
    
    Players can remove themselves, or the session owner can kick any player.
    """
    repository = get_session_repository(db)

    # Get session to check ownership
    db_session = get_session_by_uuid_or_404(session_id, repository)
    
    # Get participant to check if it's the current user
    participants = repository.get_session_participants(session_id)
    participant = next((p for p in participants if p.player_uuid == player_id), None)
    
    if not participant:
        raise HTTPException(status_code=404, detail="Player not found in session")
    
    # Check if current user is the player being removed or the session owner
    is_own_action = participant.user_id == current_user.id
    is_owner = db_session.owner_id == current_user.id
    
    if not is_own_action and not is_owner:
        raise HTTPException(
            status_code=403,
            detail="Only the player themselves or the session owner can remove this player"
        )

    # Remove from DB
    repository.remove_participant(session_id, player_id)

    # Unsubscribe from events
    session_manager.unregister_player_websocket(session_id, player_id)
    session_manager.unsubscribe_player_from_events(session_id, player_id)

    return None


@router.post("/{session_id}/players/{player_id}/kick", status_code=204)
async def kick_player(
    session_id: str,
    player_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Kick a player from the session.
    
    Only the session owner can kick players.
    """
    repository = get_session_repository(db)

    # Get session to check ownership
    db_session = get_session_by_uuid_or_404(session_id, repository)
    
    # Verify current user is the owner
    if db_session.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the session owner can kick players"
        )
    
    # Get participant
    participants = repository.get_session_participants(session_id)
    participant = next((p for p in participants if p.player_uuid == player_id), None)
    
    if not participant:
        raise HTTPException(status_code=404, detail="Player not found in session")
    
    # Cannot kick the owner
    if participant.role == "owner":
        raise HTTPException(
            status_code=400,
            detail="Cannot kick the session owner"
        )

    # Remove from DB
    repository.remove_participant(session_id, player_id)

    # Unsubscribe from events
    session_manager.unregister_player_websocket(session_id, player_id)
    session_manager.unsubscribe_player_from_events(session_id, player_id)

    return None


@router.get("/{session_id}/players", response_model=List[PlayerResponse])
async def get_session_players_endpoint(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all players in a session."""
    repository = get_session_repository(db)

    db_session = get_session_by_uuid_or_404(session_id, repository)

    participants = repository.get_session_participants(session_id)
    
    # Get ready status for this session
    session_ready_status = waiting_room_ready_status.get(session_id, {})

    return [
        PlayerResponse(
            player_id=p.player_uuid,
            player_name=p.player_name,
            character_name=p.character_name,
            connected=p.is_connected,
            role=p.role,
            is_ready=session_ready_status.get(p.user_id, False) if p.user_id else False
        )
        for p in participants
    ]


@router.get("/{session_id}/game_info", response_model=dict)
async def get_session_game_info(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed game session info including players, NPCs, and scene.
    For active game sessions with full engine integration.
    
    Returns data from both game engine (if active) and database.
    """
    repository = get_session_repository(db)

    db_session = get_session_by_uuid_or_404(session_id, repository)

    # Try to get from active game sessions
    game_session = active_game_sessions.get(session_id)

    if not game_session:
        raise HTTPException(
            status_code=400,
            detail="Session is not an active game session"
        )

    try:
        # Get DB participants for complete player list
        db_participants = repository.get_session_participants(session_id)
        db_player_names = {p.player_name for p in db_participants}
        
        # Build players data from game engine
        players_data = []
        for player in game_session.players:
            if hasattr(player, 'character'):
                char = player.character
                stats = getattr(char, 'stats', None)
                
                # Convert abilities to dict format
                abilities_data = []
                if hasattr(char, 'abilities') and char.abilities:
                    for ability in char.abilities:
                        if isinstance(ability, dict):
                            abilities_data.append(ability)
                        else:
                            abilities_data.append({
                                "name": getattr(ability, 'name', 'Unknown'),
                                "short_summary": getattr(ability, 'short_summary', ''),
                                "level": getattr(ability, 'level', 0),
                                "type": getattr(ability, 'type', 'action'),
                            })
                
                # Convert inventory to dict format
                inventory_data = []
                if hasattr(char, 'inventory') and char.inventory:
                    for item in char.inventory:
                        if isinstance(item, dict):
                            inventory_data.append(item)
                        else:
                            inventory_data.append({
                                "name": getattr(item, 'name', 'Unknown'),
                                "is_equipped": getattr(item, 'is_equipped', False),
                                "type": getattr(item, 'type', 'item'),
                            })
                
                # Convert conditions to string
                conditions_str = ""
                if hasattr(char, 'active_conditions_list') and char.active_conditions_list:
                    conditions_str = '\n'.join(char.active_conditions_list)
                elif hasattr(char, 'active_conditions') and char.active_conditions:
                    conditions_str = char.active_conditions
                
                players_data.append({
                    "name": getattr(char, 'name', 'Unknown'),
                    "race": getattr(char, 'race', 'Human'),
                    "char_class": str(getattr(char, 'char_class', 'Fighter')),
                    "level": getattr(char, 'level', 1),
                    "current_hp": getattr(char, 'current_hp', 10),
                    "max_hp": getattr(char, 'max_hp', 10),
                    "armor_class": getattr(char, 'armor_class', 10),
                    "speed": getattr(char, 'speed', 30),
                    "proficiency_bonus": getattr(char, 'proficiency_bonus', 2),
                    "initiative_bonus": getattr(char, 'initiative_bonus', 0),
                    "is_alive": getattr(char, 'is_alive', True),
                    "stats": {
                        "strength": getattr(stats, 'strength', 10) if stats else 10,
                        "dexterity": getattr(stats, 'dexterity', 10) if stats else 10,
                        "constitution": getattr(stats, 'constitution', 10) if stats else 10,
                        "intelligence": getattr(stats, 'intelligence', 10) if stats else 10,
                        "wisdom": getattr(stats, 'wisdom', 10) if stats else 10,
                        "charisma": getattr(stats, 'charisma', 10) if stats else 10,
                    } if stats else {
                        "strength": 10, "dexterity": 10, "constitution": 10,
                        "intelligence": 10, "wisdom": 10, "charisma": 10,
                    },
                    "abilities": abilities_data,
                    "inventory": inventory_data,
                    "active_conditions": conditions_str,
                })
        
        # Add DB participants who don't have characters yet (waiting room players)
        engine_player_names = {p.get('name') for p in players_data}
        for participant in db_participants:
            if participant.player_name not in engine_player_names:
                # Player joined but doesn't have a character yet
                players_data.append({
                    "name": participant.player_name,
                    "race": "Human",
                    "char_class": "Adventurer",
                    "level": 1,
                    "current_hp": 10,
                    "max_hp": 10,
                    "armor_class": 10,
                    "speed": 30,
                    "proficiency_bonus": 2,
                    "initiative_bonus": 0,
                    "is_alive": True,
                    "stats": {
                        "strength": 10, "dexterity": 10, "constitution": 10,
                        "intelligence": 10, "wisdom": 10, "charisma": 10,
                    },
                })

        # Build NPCs data
        npcs_data = []
        for npc in game_session.npcs:
            if hasattr(npc, 'character'):
                char = npc.character
                stats = getattr(char, 'stats', None)
                
                # Convert abilities to dict format
                abilities_data = []
                if hasattr(char, 'abilities') and char.abilities:
                    for ability in char.abilities:
                        if isinstance(ability, dict):
                            abilities_data.append(ability)
                        else:
                            abilities_data.append({
                                "name": getattr(ability, 'name', 'Unknown'),
                                "short_summary": getattr(ability, 'short_summary', ''),
                                "level": getattr(ability, 'level', 0),
                                "type": getattr(ability, 'type', 'action'),
                            })
                
                # Convert inventory to dict format
                inventory_data = []
                if hasattr(char, 'inventory') and char.inventory:
                    for item in char.inventory:
                        if isinstance(item, dict):
                            inventory_data.append(item)
                        else:
                            inventory_data.append({
                                "name": getattr(item, 'name', 'Unknown'),
                                "is_equipped": getattr(item, 'is_equipped', False),
                                "type": getattr(item, 'type', 'item'),
                            })
                
                npcs_data.append({
                    "name": getattr(char, 'name', 'Unknown'),
                    "race": getattr(char, 'race', 'Human'),
                    "char_class": str(getattr(char, 'char_class', 'Commoner')),
                    "alignment": getattr(char, 'alignment', 'Neutral'),
                    "current_hp": getattr(char, 'current_hp', 10),
                    "max_hp": getattr(char, 'max_hp', 10),
                    "armor_class": getattr(char, 'armor_class', 10),
                    "speed": getattr(char, 'speed', 30),
                    "is_alive": getattr(char, 'is_alive', True),
                    "stats": {
                        "strength": getattr(stats, 'strength', 10) if stats else 10,
                        "dexterity": getattr(stats, 'dexterity', 10) if stats else 10,
                        "constitution": getattr(stats, 'constitution', 10) if stats else 10,
                        "intelligence": getattr(stats, 'intelligence', 10) if stats else 10,
                        "wisdom": getattr(stats, 'wisdom', 10) if stats else 10,
                        "charisma": getattr(stats, 'charisma', 10) if stats else 10,
                    } if stats else {
                        "strength": 10, "dexterity": 10, "constitution": 10,
                        "intelligence": 10, "wisdom": 10, "charisma": 10,
                    },
                    "abilities": abilities_data,
                    "inventory": inventory_data,
                })

        # Build scene data
        scene_data = None
        if game_session.current_scene:
            scene = game_session.current_scene
            scene_data = {
                "name": getattr(scene, 'name', 'Unknown'),
                "description": getattr(scene, 'description', ''),
            }

        return {
            "session_id": session_id,
            "session_name": db_session.session_name,
            "game_mode": db_session.game_mode.value,
            "status": db_session.status.value,
            "owner_id": db_session.owner_id,
            "players": players_data,
            "npcs": npcs_data,
            "current_scene": scene_data,
        }

    except Exception as e:
        game_session.logger.error(f"Error getting game info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting game info: {str(e)}"
        )


@router.get("/{session_id}/waiting-room", response_model=WaitingRoomResponse)
async def get_waiting_room(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get waiting room information for a session.
    
    Returns session details with player ready status.
    """
    repository = get_session_repository(db)

    db_session = get_session_by_uuid_or_404(session_id, repository)

    # Get players from DB
    participants = repository.get_session_participants(session_id)
    player_count = len([p for p in participants if p.is_connected])
    
    # Get ready status for this session (tracked by user_id)
    session_ready_status = waiting_room_ready_status.get(session_id, {})
    
    players = []
    for p in participants:
        # Get ready status by user_id (None for guest users without account)
        user_id_key = p.user_id if p.user_id is not None else hash(p.player_uuid)
        is_ready = session_ready_status.get(user_id_key, False)
        players.append(PlayerResponse(
            player_id=p.player_uuid,
            player_name=p.player_name,
            character_name=p.character_name,
            connected=p.is_connected,
            role=p.role,
            is_ready=is_ready
        ))

    return WaitingRoomResponse(
        session_id=db_session.session_uuid,
        session_name=db_session.session_name,
        game_mode=db_session.game_mode.value,
        player_count=player_count,
        max_players=db_session.max_players,
        status=db_session.status.value,
        description=db_session.description,
        owner_id=db_session.owner_id,
        owner_name=current_user.username if db_session.owner_id == current_user.id else "Unknown",
        is_owner=(db_session.owner_id == current_user.id),
        players=players
    )


@router.post("/{session_id}/ready", status_code=200)
async def set_player_ready(
    session_id: str,
    request: PlayerReadyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Set player ready status in waiting room.
    
    Players can toggle their ready status before game start.
    Each user can only join once per session.
    """
    repository = get_session_repository(db)

    # Validate session exists
    db_session = get_session_by_uuid_or_404(session_id, repository)

    # Verify player is in the session - check by user_id
    participants = repository.get_session_participants(session_id)
    participant = next((p for p in participants if p.user_id == current_user.id), None)
    
    if not participant:
        raise HTTPException(
            status_code=404,
            detail="Player not found in session. Please join the session first."
        )
    
    # Check if player is already connected (prevent double connection)
    if participant.is_connected:
        # Player already connected - this is fine, just update ready status
        pass

    # Initialize session ready status if not exists
    if session_id not in waiting_room_ready_status:
        waiting_room_ready_status[session_id] = {}
    
    # Set ready status using user_id as key (prevents duplicates)
    waiting_room_ready_status[session_id][current_user.id] = request.is_ready

    return {
        "success": True,
        "user_id": current_user.id,
        "player_name": participant.player_name,
        "is_ready": request.is_ready,
        "session_id": session_id
    }


@router.post("/{session_id}/start-game", response_model=SessionResponse)
async def start_game_from_waiting_room(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start the game from waiting room.
    
    Only the session owner can start the game.
    ALL connected players must be ready before starting.
    """
    import logging
    logger = logging.getLogger(__name__)

    repository = get_session_repository(db)

    db_session = get_session_by_uuid_or_404(session_id, repository)
    
    # Verify current user is the owner
    if db_session.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the session owner can start the game"
        )

    # Get all connected players
    participants = repository.get_session_participants(session_id)
    connected_players = [p for p in participants if p.is_connected]
    
    if not connected_players:
        raise HTTPException(
            status_code=400,
            detail="No connected players. Wait for players to join before starting."
        )
    
    # Check if ALL connected players are ready
    session_ready_status = waiting_room_ready_status.get(session_id, {})
    
    not_ready_players = []
    for player in connected_players:
        user_id_key = player.user_id if player.user_id is not None else hash(player.player_uuid)
        is_ready = session_ready_status.get(user_id_key, False)
        if not is_ready:
            not_ready_players.append(player.player_name)
    
    if not_ready_players:
        raise HTTPException(
            status_code=400,
            detail=f"Waiting for players to ready: {', '.join(not_ready_players)}"
        )

    logger.info(f"[START-GAME] Session {session_id} - Starting from waiting room with {len(connected_players)} ready players")

    # Get or create game session
    game_session = active_game_sessions.get(session_id)

    if not game_session:
        # Initialize the game session from DB
        logger.warning(f"[START-GAME] Session {session_id} found in DB but not in memory. Initializing...")

        try:
            from backend.src.game.session_factory import SessionConfig
            config = SessionConfig(
                session_name=db_session.session_name,
                game_mode=db_session.game_mode.value,
                max_players=db_session.max_players,
                description=db_session.description,
                guide=db_session.guide,
                gemini_model=db_session.gemini_model or "gemini-2.0-flash"
            )
            game_session = session_factory.create_session(config, session_id=session_id)
            active_game_sessions[session_id] = game_session
            logger.info(f"[START-GAME] Session {session_id} restored from DB")
        except Exception as e:
            logger.error(f"[START-GAME] Failed to restore session {session_id}: {e}")
            raise HTTPException(
                status_code=400,
                detail="Session not initialized. Please recreate the session."
            )

    try:
        # Initialize scene and characters
        from core.schemas.in_game import SceneNode, Coordinate2D, UnifiedObject, ObjectType
        from core.entity.player import Player
        from core.schemas.in_game import Character, CharacterClass, AbilityScores
        from core.entity.orchestrator import Orchestrator

        # Create initial scene
        scene_description = db_session.guide or "A dimly lit tavern with worn wooden tables and the smell of ale."

        scene = SceneNode(
            name="The Drunken Dragon",
            description=scene_description,
            objects=[
                UnifiedObject(
                    name="Wooden Table",
                    obj_type=ObjectType.PROP,
                    quantity=1,
                    is_equipped=False,
                    position=Coordinate2D(x=5.0, y=5.0),
                    short_summary="A sturdy wooden table"
                ),
            ],
            center_position=Coordinate2D(x=10.0, y=10.0),
            dimensions=Coordinate2D(x=20.0, y=20.0),
            scale_unit="feet"
        )
        game_session.current_scene = scene

        # Update DB status
        repository.update_session_scene(session_id, scene.name, owner_id=current_user.id)
        repository.update_session_status(session_id, "running", owner_id=current_user.id)

        # Initialize player characters from ALL connected players
        for i, participant in enumerate(connected_players):
            character = Character(
                name=participant.character_name or participant.player_name,
                race="Human",
                char_class=CharacterClass.FIGHTER,
                level=1,
                backstory_summary=f"{participant.player_name}'s character",
                personality_traits=["Brave"],
                max_hp=30,
                current_hp=30,
                temp_hp=0,
                armor_class=12,
                speed=30,
                stats=AbilityScores(
                    strength=15, dexterity=12, constitution=14,
                    intelligence=10, wisdom=10, charisma=10
                ),
                inventory=[],
                active_conditions_list=[],
                resources={},
                position=Coordinate2D(x=float(i*2), y=float(i*2)),
                abilities=[],
                active_conditions="",
                proficiency_bonus=2,
                is_alive=True,
                initiative_bonus=11,
                short_summary=f"{participant.player_name}'s character"
            )

            player_orchestrator = Orchestrator(
                generator=game_session.generator,
                logger=game_session.logger.getChild("player_orchestrator")
            )
            player_orchestrator.add_state(game_session)

            event_queue = game_session.event_pool.subscribe(character.name)

            player = Player(
                character=character,
                event_queuee=event_queue,
                logger=game_session.logger.getChild("player"),
                orchestrator=player_orchestrator
            )
            player.inject_state(game_session)
            game_session.players.append(player)

        game_session.logger.info(
            f"Сессия запущена: {len(game_session.players)} игроков"
        )

        # Send welcome message
        game_session.delivery.master_message(
            f"Welcome to {scene.name}! {scene.description}"
        )
        game_session.delivery.session_updated(game_session)

        # Clear waiting room ready status
        if session_id in waiting_room_ready_status:
            del waiting_room_ready_status[session_id]

        return SessionResponse(
            session_id=session_id,
            session_name=db_session.session_name,
            game_mode=db_session.game_mode.value,
            player_count=len(game_session.players),
            status="running",
            description=db_session.description,
            owner_id=db_session.owner_id,
            owner_name=current_user.username,
            created_at=db_session.created_at.isoformat(),
            is_owner=True
        )

    except Exception as e:
        game_session.logger.error(f"Ошибка при запуске сессии: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при запуске сессии: {str(e)}"
        )


# === AI Game Service Endpoints ===

@router.post("/{session_id}/ai-initialize", response_model=AIInitializeResponse)
async def ai_initialize_session(
    session_id: str,
    request: AIInitializeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Инициализировать сессию через AI (Google Gemini).
    
    Генерирует сцену, персонажей и NPC используя AI.
    Только владелец сессии может инициализировать.
    """
    repository = get_session_repository(db)
    db_session = get_session_by_uuid_or_404(session_id, repository)
    
    # Verify owner
    if db_session.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the session owner can initialize the game"
        )
    
    # Get or create game session
    game_session = active_game_sessions.get(session_id)
    
    if not game_session:
        # Initialize from DB
        try:
            from backend.src.game.session_factory import SessionConfig
            config = SessionConfig(
                session_name=db_session.session_name,
                game_mode=db_session.game_mode.value,
                max_players=db_session.max_players,
                description=db_session.description,
                guide=db_session.guide,
                gemini_model=db_session.gemini_model or "gemini-2.0-flash"
            )
            game_session = session_factory.create_session(config, session_id=session_id)
            active_game_sessions[session_id] = game_session
            logger.info(f"[AI-INIT] Session {session_id} created")
        except Exception as e:
            logger.error(f"[AI-INIT] Failed to create session: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to create session: {str(e)}"
            )
    
    try:
        # Create AI service
        from backend.src.services.ai_game_service import AIGameService
        ai_service = AIGameService(game_session)
        
        # Prepare prompts
        scene_prompt = request.scene_prompt or request.wishes or "A mysterious adventure begins..."
        character_prompts = request.character_prompts or []
        npc_prompts = request.npc_prompts or []
        
        # Initialize through AI
        result = await ai_service.initialize_session(
            scene_prompt=scene_prompt,
            character_prompts=character_prompts,
            npc_prompts=npc_prompts
        )
        
        # Update DB status
        repository.update_session_status(session_id, "running", owner_id=current_user.id)
        
        # Send welcome message
        game_session.delivery.master_message(result['message'])
        game_session.delivery.session_updated(game_session)
        
        return AIInitializeResponse(
            success=result['success'],
            session_id=result['session_id'],
            scene_description=result['scene'].get('description', '') if result.get('scene') else '',
            characters_count=len(result.get('characters', [])),
            npcs_count=len(result.get('npcs', [])),
            message=result['message']
        )
        
    except Exception as e:
        logger.error(f"[AI-INIT] Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"AI initialization failed: {str(e)}"
        )


@router.post("/{session_id}/action", response_model=PlayerActionResponse)
async def player_action(
    session_id: str,
    request: PlayerActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обработать действие игрока через AI.
    
    Использует MAGG и Orchestrator для обработки действия
    и генерации нарративного ответа.
    """
    # Get active game session
    game_session = active_game_sessions.get(session_id)
    
    if not game_session:
        raise HTTPException(
            status_code=404,
            detail="Game session not found or not initialized"
        )
    
    try:
        # Create AI service
        from backend.src.services.ai_game_service import AIGameService
        ai_service = AIGameService(game_session)
        
        # Process action
        result = await ai_service.process_player_action(
            character_name=request.character_name,
            action=request.action
        )
        
        # Send DM message to all players
        if result.get('dm_response'):
            game_session.delivery.master_message(result['dm_response'])
        
        game_session.delivery.session_updated(game_session)
        
        return PlayerActionResponse(
            success=result['success'],
            dm_response=result['dm_response'],
            events=result.get('events', []),
            game_state=result.get('game_state', {}),
            error=None
        )
        
    except Exception as e:
        logger.error(f"[ACTION] Error: {e}", exc_info=True)
        return PlayerActionResponse(
            success=False,
            dm_response="",
            events=[],
            game_state={},
            error=str(e)
        )


@router.get("/{session_id}/state", response_model=SessionStateResponse)
async def get_session_state(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить текущее состояние сессии.
    
    Возвращает сцену, игроков, NPC, сообщения и очередь ходов.
    """
    # Get active game session
    game_session = active_game_sessions.get(session_id)
    
    if not game_session:
        return SessionStateResponse(
            success=False,
            scene=None,
            players=[],
            npcs=[],
            messages=[],
            turn_queue=[]
        )
    
    try:
        # Create AI service
        from backend.src.services.ai_game_service import AIGameService
        ai_service = AIGameService(game_session)
        
        # Get game state
        state = ai_service.get_game_state()
        
        return SessionStateResponse(
            success=True,
            scene=state.get('scene'),
            players=state.get('players', []),
            npcs=state.get('npcs', []),
            messages=state.get('messages', []),
            turn_queue=state.get('turn_queue', [])
        )
        
    except Exception as e:
        logger.error(f"[STATE] Error: {e}", exc_info=True)
        return SessionStateResponse(
            success=False,
            scene=None,
            players=[],
            npcs=[],
            messages=[],
            turn_queue=[],
        )
