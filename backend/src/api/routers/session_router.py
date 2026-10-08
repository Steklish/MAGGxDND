# type: ignore[reportGeneralTypeIssues, reportAttributeAccessIssue, reportArgumentType, reportUndefinedVariable, reportCallIssue]
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
import asyncio
import logging
from datetime import datetime

from sqlalchemy.orm import Session as DBSession
from sqlalchemy.orm.attributes import flag_modified

from backend.src.config import settings
from backend.src.database.session import get_db
from backend.src.auth.dependencies import get_current_user
from backend.src.models.user import User
from backend.src.models.session import GameSession, SessionStatusEnum
from backend.src.repositories.session_repository import SessionRepository
from backend.src.api.middleware.logging import Colors
from backend.src.utils import validate_safe_text, sanitize_string
from backend.src.game.session_manager import session_manager
from backend.src.game.session_factory import session_factory, SessionConfig
from core.game.engine import Session
from core.schemas.in_game import GameModes, CharacterClass

router = APIRouter(prefix="/sessions", tags=["sessions"])
logger = logging.getLogger(__name__)

# Store for active players (temporary, until full WebSocket integration)
active_players: Dict[str, Dict[str, any]] = {}

# Store for player ready status in waiting room
# Key: session_id, Value: Dict[user_id, is_ready] - track by user_id to prevent duplicates
waiting_room_ready_status: Dict[str, Dict[int, bool]] = {}


# === Helper Functions for Session Data Extraction ===

def get_session_description(db_session) -> Optional[str]:
    """Extract description from session_data JSON"""
    return (db_session.session_data or {}).get('description')

def get_session_guide(db_session) -> Optional[str]:
    """Extract guide from session_data JSON"""
    return (db_session.session_data or {}).get('guide')

def get_session_max_players(db_session) -> int:
    """Extract max_players from session_data JSON, default 5"""
    return (db_session.session_data or {}).get('max_players', 5)

def get_session_is_public(db_session) -> bool:
    """Extract is_public from session_data JSON, default False"""
    return (db_session.session_data or {}).get('is_public', False)

def get_session_gemini_model(db_session) -> str:
    """Extract gemini_model from session_data JSON, default gemini-3.5-flash-lite"""
    model = (db_session.session_data or {}).get('gemini_model', 'gemini-3.5-flash-lite')
    if model in ('gemini-2.5-flash', 'gemini-flash', 'gemini-flash-latest', 'gemini-3.8-flash'):
        return 'gemini-3.5-flash-lite'
    return model


def ensure_scene_battlemap(scene, session_id: Optional[str] = None) -> None:
    """
    Ensure scene has battlemap_image_url populated.
    If already set, does nothing.
    Otherwise, checks if a cached aerial battle map exists on disk,
    falling back to a default SVG placeholder (/assets/placeholders/battlemap_stone.svg).
    """
    if not scene:
        return
    current_map = getattr(scene, "battlemap_image_url", None)
    if not current_map:
        try:
            from backend.src.services.asset_manager import asset_manager
            from backend.src.services.image_gen_service import image_gen_service
            from backend.src.services.prompt_builder import PromptBuilder

            dim_x = int(scene.dimensions.x) if hasattr(scene, "dimensions") and hasattr(scene.dimensions, "x") else 20
            dim_y = int(scene.dimensions.y) if hasattr(scene, "dimensions") and hasattr(scene.dimensions, "y") else 20
            aspect_ratio = "1:1" if dim_x == dim_y else "16:9"

            prompt, _ = PromptBuilder.build_battlemap_prompt(
                name=getattr(scene, "name", "Scene"),
                description=getattr(scene, "description", ""),
                dimensions=(dim_x, dim_y),
            )
            chash = image_gen_service.compute_hash("maps", prompt, aspect_ratio)
            cached_file = image_gen_service.asset_dir / "maps" / f"{chash}.png"

            if cached_file.is_file() and cached_file.stat().st_size > 0:
                map_url = image_gen_service.get_asset_url("maps", f"{chash}.png")
            else:
                map_url = asset_manager.get_fallback_placeholder_url("battlemap", subtype="stone")
                if image_gen_service.is_configured:
                    async def _auto_gen_map(sc=scene, s_id=session_id, dx=dim_x, dy=dim_y):
                        try:
                            obstacles = [obj.name for obj in getattr(sc, "objects", []) if getattr(obj, "name", None)]
                            res = await image_gen_service.generate_battlemap(
                                scene_id=f"{s_id or 'scene'}_{getattr(sc, 'name', 'arena')}",
                                name=getattr(sc, "name", "Tactical Arena"),
                                description=getattr(sc, "description", ""),
                                dimensions=(dx, dy),
                                obstacles=obstacles if obstacles else None,
                            )
                            if res.image_url and not res.image_url.endswith(".svg"):
                                sc.battlemap_image_url = res.image_url
                                if hasattr(sc, "background_image_url"):
                                    sc.background_image_url = res.image_url
                                logger.info(f"[AUTO-MAP] Generated battlemap for scene '{sc.name}': {res.image_url}")
                        except Exception as e:
                            logger.debug(f"[AUTO-MAP] Error: {e}")
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(_auto_gen_map())
                    except RuntimeError:
                        pass

            scene.battlemap_image_url = map_url
            if hasattr(scene, "background_image_url"):
                setattr(scene, "background_image_url", map_url)
        except Exception:
            fallback = "/assets/placeholders/battlemap_stone.svg"
            scene.battlemap_image_url = fallback
            if hasattr(scene, "background_image_url"):
                setattr(scene, "background_image_url", fallback)

    # Ensure scene narrative image_url is also populated
    current_scene_img = getattr(scene, "image_url", None)
    if not current_scene_img:
        try:
            from backend.src.services.asset_manager import asset_manager
            from backend.src.services.image_gen_service import image_gen_service
            from backend.src.services.prompt_builder import PromptBuilder

            scene_name = getattr(scene, "name", "Scene")
            scene_desc = getattr(scene, "description", "")
            prompt, _ = PromptBuilder.build_scene_prompt(name=scene_name, description=scene_desc)
            chash = image_gen_service.compute_hash("scenes", prompt, "16:9")
            cached_file = image_gen_service.asset_dir / "scenes" / f"{chash}.png"
            if cached_file.is_file() and cached_file.stat().st_size > 0:
                scene.image_url = image_gen_service.get_asset_url("scenes", f"{chash}.png")
            else:
                subtype = ProceduralGenerator._find_scene_type(f"{scene_name} {scene_desc}")
                scene.image_url = asset_manager.get_fallback_placeholder_url("scene", subtype=subtype)
        except Exception:
            scene.image_url = "/assets/placeholders/scene_default.svg"


def ensure_character_portrait(character, session_id: Optional[str] = None) -> None:
    """
    Ensure character has image_url populated.
    Uses cached generated portrait if available, otherwise sets placeholder and triggers
    background generation automatically when image_gen_service is configured.
    """
    if not character:
        return
    current_img = getattr(character, "image_url", None)
    try:
        from backend.src.services.asset_manager import asset_manager
        from backend.src.services.image_gen_service import image_gen_service
        from backend.src.services.prompt_builder import PromptBuilder

        cclass = getattr(character, "char_class", "Fighter")
        class_str = cclass.value if hasattr(cclass, "value") else str(cclass)
        race_str = getattr(character, "race", "Human")
        char_name = getattr(character, "name", "Hero")
        char_desc = getattr(character, "backstory_summary", "")

        prompt, _ = PromptBuilder.build_character_prompt(
            name=char_name,
            race=race_str,
            char_class=class_str,
            appearance=char_desc,
        )
        chash = image_gen_service.compute_hash("characters", prompt, "1:1")
        cached_file = image_gen_service.asset_dir / "characters" / f"{chash}.png"

        if cached_file.is_file() and cached_file.stat().st_size > 0:
            character.image_url = image_gen_service.get_asset_url("characters", f"{chash}.png")
        else:
            if not current_img or current_img.endswith(".svg"):
                character.image_url = asset_manager.get_fallback_placeholder_url("character", subtype=class_str)
            if image_gen_service.is_configured:
                async def _auto_gen_char(ch=character, s_id=session_id, c_name=char_name, c_race=race_str, c_cls=class_str, c_app=char_desc):
                    try:
                        res = await image_gen_service.generate_character_portrait(
                            character_id=f"{s_id or 'char'}_{c_name}",
                            name=c_name,
                            race=c_race,
                            char_class=c_cls,
                            appearance=c_app,
                        )
                        if res.image_url and not res.image_url.endswith(".svg"):
                            ch.image_url = res.image_url
                            logger.info(f"[AUTO-PORTRAIT] Generated portrait for {c_name}: {res.image_url}")
                    except Exception as e:
                        logger.debug(f"[AUTO-PORTRAIT] Error: {e}")
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(_auto_gen_char())
                except RuntimeError:
                    pass
    except Exception:
        if not getattr(character, "image_url", None):
            character.image_url = "/assets/placeholders/character_default.svg"


class EntranceNarrative(BaseModel):
    narrative: str = Field(..., description="Vivid 1-2 sentence description of the character dramatically entering the scene.")


def generate_character_entrance_narrative(
    generator,
    session,
    character_name: str,
    character_class: str = "Adventurer",
    scene_name: str = "the active scene"
) -> str:
    """Generate dynamic DM narration describing how an adventurer enters the scene to join the party."""
    lang = getattr(session, "language", "ru") if session else "ru"

    if lang == "ru":
        prompt_text = (
            "### ЯЗЫКОВАЯ ДИРЕКТИВА: ОТВЕЧАЙ СТРОГО НА РУССКОМ ЯЗЫКЕ!\n"
            f"Создай красочное, кинематографичное описание в 1-2 предложениях в стиле Мастера Подземелий (Dungeon Master), "
            f"описывающее, как искатель приключений по имени {character_name} ({character_class}) эффектно появляется или входит в локацию: {scene_name}. "
            f"Опиши их появление, снаряжение или решительный настрой. Сделай это живо и атмосферно."
        )
    else:
        prompt_text = (
            f"Generate a vivid 1-2 sentence narrative in evocative tabletop RPG Dungeon Master style describing how "
            f"the hero named {character_name} (a {character_class}) dramatically arrives or enters the active scene: {scene_name}. "
            f"Describe their entrance, gear, or demeanor. Keep it concise, cinematic, and immersive."
        )

    if generator:
        try:
            res = generator.generate_one_shot(
                pydantic_model=EntranceNarrative,
                prompt=prompt_text
            )
            if res and hasattr(res, 'narrative') and res.narrative:
                return res.narrative.strip()
        except Exception:
            pass

    import random
    if lang == "ru":
        templates_ru = [
            f"Дверь со скрипом отворяется, и {character_name} ({character_class}) выступает из тени, держа руку на рукояти оружия и внимательно оглядывая помещение.",
            f"Порыв сквозняка возвещает о прибытии героя: {character_name} уверенным шагом входит в {scene_name}, взметнув полы плаща и приветственно кивнув отряду.",
            f"Выйдя размеренным шагом из смежного коридора, {character_name} ({character_class}) присоединяется к соратникам, готовый к любым грядущим опасностям.",
            f"{character_name} вступает в {scene_name}, отряхивая дорожную пыль с доспехов и окидывая пространство решительным взглядом."
        ]
        return random.choice(templates_ru)

    templates = [
        f"The doorway creaks open as {character_name} the {character_class} steps out of the shadows, resting a hand on their weapon while taking in the room with keen eyes.",
        f"A draft of wind heralds the arrival of {character_name}, who strides purposefully into {scene_name}, cloak billowing as they nod greeting to the company.",
        f"Emerging from the adjacent corridor with measured footsteps, {character_name} the {character_class} joins the party, ready for whatever perils lie ahead.",
        f"{character_name} arrives in {scene_name}, brushing trail dust from their armor and offering a resolute nod as they survey the surroundings."
    ]
    return random.choice(templates)


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

    SCENE_TEMPLATES_RU = {
        "tavern": {
            "names": ["Серебряный Дракон", "Сломанный Меч", "Смеющийся Дракон", "Ржавый Якорь", "Багровая Кружка"],
            "descriptions": [
                "Уютная таверна с пылающим очагом и аппетитным ароматом жареного мяса.",
                "Полутемная таверна, где путешественники собираются, чтобы поведать о былых подвигах.",
                "Оживленный трактир, полный купцов, бывалых наемников и таинственных незнакомцев.",
            ]
        },
        "cave": {
            "names": ["Шепчущие Пещеры", "Кристальный Грот", "Теневые Глубины", "Пасть Дракона", "Забытая Шахта"],
            "descriptions": [
                "Темная пещера, где друзы кристаллов мерцают зловещим лазурным светом.",
                "Древний грот, в котором гулким эхом отдается стук капель и далекие подземные шорохи.",
                "Обширный каменный зал со сталактитами, нависающими подобно обнаженным клинкам.",
            ]
        },
        "forest": {
            "names": ["Шепчущая Чаща", "Роща Древних", "Лес Тенетопи", "Лунная Дубрава", "Первобытный Бор"],
            "descriptions": [
                "Густой лес, где лучи солнца с трудом пробиваются сквозь кроны вековых исполинов.",
                "Таинственная чаща, где в самом воздухе витает древняя лесная магия.",
                "Темнолесье со скрученными узловатыми стволами и настороженными взглядами из теней.",
            ]
        },
        "castle": {
            "names": ["Замок Рейвенмур", "Железная Цитадель", "Дворец Рассвета", "Обсидиановая Крепость", "Кристальный Оплот"],
            "descriptions": [
                "Величественный замок с высокими шпилями и развевающимися боевыми знаменами.",
                "Древняя крепость, закаленная веками штормов и ожесточенных осад.",
                "Грандиозная цитадель из белого мрамора и золота, оплот благородных рыцарей.",
            ]
        },
        "default": {
            "names": ["Приют Искателя", "Трактир на Перепутье", "Обитель Путника", "Постоялый Двор"],
            "descriptions": [
                "Гостеприимное убежище, где искатели приключений собираются перед дальним странствием.",
                "Скромный, но надежный приют, дарующий тепло очага и сытную трапезу.",
            ]
        }
    }
    
    CHARACTER_NAMES = ["Aldric", "Brynn", "Cedric", "Dara", "Eldrin", "Faye", "Gareth", "Hanna", "Ivan", "Jora", "Kael", "Lyra", "Magnus", "Nora", "Owen", "Pipa", "Quinn", "Rhea", "Stefan", "Tessa"]
    CHARACTER_SURNAMES = ["Stormwind", "Ironfoot", "Shadowbane", "Lightbringer", "Fireheart", "Frostbeard", "Thunderstrike", "Moonwhisper", "Sunblade", "Nightshade"]
    NPC_ROLES = ["tavern keeper", "blacksmith", "merchant", "guard", "wizard", "healer", "thief", "bard", "hunter", "farmer"]

    CHARACTER_NAMES_RU = ["Алдрик", "Бринн", "Седрик", "Дара", "Элдрин", "Фэй", "Гарет", "Ханна", "Иван", "Жора", "Каэль", "Лира", "Магнус", "Нора", "Оуэн", "Квинн", "Рея", "Стефан", "Тесса", "Вален"]
    CHARACTER_SURNAMES_RU = ["Буревестник", "Железностоп", "Тенебой", "Светоносный", "Огнесердый", "Седобород", "Громовержец", "Лунношепт", "Солнцемеч", "Ночноцвет"]
    NPC_ROLES_RU = ["трактирщик", "кузнец", "купец", "стражник", "чародей", "целитель", "плут", "бард", "охотник", "следопыт"]
    
    @staticmethod
    def _find_scene_type(prompt: str) -> str:
        """Find scene type from prompt keywords."""
        prompt_lower = prompt.lower()
        if any(word in prompt_lower for word in ["tavern", "inn", "pub", "bar", "ale", "beer", "таверн", "трактир", "постоялый"]):
            return "tavern"
        if any(word in prompt_lower for word in ["cave", "cavern", "mine", "underground", "dungeon", "crypt", "tomb", "пещер", "грот", "подземел", "склеп", "гробниц"]):
            return "cave"
        if any(word in prompt_lower for word in ["forest", "wood", "tree", "grove", "wilderness", "лес", "чащ", "рощ", "пущ"]):
            return "forest"
        if any(word in prompt_lower for word in ["castle", "fortress", "palace", "keep", "tower", "замок", "крепост", "дворец", "цитадел", "башн"]):
            return "castle"
        return "default"
    
    @classmethod
    def generate_scene(cls, prompt: str, language: str = "ru"):
        """Generate a scene procedurally with thematic interactive objects."""
        from core.schemas.in_game import SceneNode, Coordinate2D, UnifiedObject, ObjectType
        from backend.src.services.asset_manager import asset_manager
        
        scene_type = cls._find_scene_type(prompt)
        templates_dict = cls.SCENE_TEMPLATES_RU if language == "ru" else cls.SCENE_TEMPLATES
        template = templates_dict.get(scene_type, templates_dict["default"])
        
        name = random.choice(template["names"])
        description = random.choice(template["descriptions"])
        
        # Add prompt-specific details
        if prompt:
            description = f"{description} {prompt}"
        
        # Thematic interactive objects for the scene
        if language == "ru":
            object_templates = {
                "tavern": [
                    {"name": "Дубовая стойка", "type": ObjectType.PROP, "pos": (5.0, 5.0), "desc": "Крепкая полированная стойка из темного дуба, где рекой льется эль и свежие сплетни.", "state": "normal", "tags": ["furniture", "cover"]},
                    {"name": "Пылающий очаг", "type": ObjectType.INTERACTABLE, "pos": (15.0, 3.0), "desc": "Каменный очаг, наполняющий зал теплым янтарным светом и потрескиванием дров.", "state": "active", "tags": ["fire", "light", "heat"]},
                    {"name": "Трактирный ящик", "type": ObjectType.CONTAINER, "pos": (3.0, 16.0), "desc": "Окованный железом ящик с запасами кружек, свечей и кладовой утвари.", "state": "closed", "tags": ["container", "storage"]},
                    {"name": "Тяжелый дубовый стол", "type": ObjectType.PROP, "pos": (10.0, 10.0), "desc": "Массивный стол, исчерченный именами и рунами бывалых искателей приключений.", "state": "normal", "tags": ["furniture", "table"]},
                ],
                "cave": [
                    {"name": "Древний саркофаг", "type": ObjectType.CONTAINER, "pos": (10.0, 10.0), "desc": "Истомленный веками каменный гроб, испещренный стершимися охранительными рунами.", "state": "closed", "tags": ["container", "relic", "stone"]},
                    {"name": "Друза кристаллов", "type": ObjectType.INTERACTABLE, "pos": (4.0, 15.0), "desc": "Скопление светящихся кристаллов, озаряющих свод потусторонним сиянием.", "state": "active", "tags": ["magical", "light", "crystal"]},
                    {"name": "Окованный сундук", "type": ObjectType.CONTAINER, "pos": (16.0, 4.0), "desc": "Ржавый железный сундук, наполовину погребенный под каменной осыпью.", "state": "closed", "tags": ["container", "treasure", "locked"]},
                    {"name": "Каменные сталагмиты", "type": ObjectType.PROP, "pos": (7.0, 8.0), "desc": "Природные каменные столпы, поднимающиеся из недр каменного дна.", "state": "normal", "tags": ["cover", "stone"]},
                ],
                "forest": [
                    {"name": "Мшистый алтарь", "type": ObjectType.INTERACTABLE, "pos": (10.0, 10.0), "desc": "Древний валун, освященный в честь хранителей дикой природы.", "state": "active", "tags": ["altar", "sacred", "relic"]},
                    {"name": "Дупло векового дуба", "type": ObjectType.CONTAINER, "pos": (8.0, 14.0), "desc": "Потайное дупло в узловатых корнях исполинского дерева, скрывающее дорожные припасы.", "state": "normal", "tags": ["container", "nature"]},
                    {"name": "Кострище", "type": ObjectType.INTERACTABLE, "pos": (14.0, 6.0), "desc": "Круг из речных камней с остывающими углями и сухим хворостом.", "state": "unlit", "tags": ["fire", "camp"]},
                    {"name": "Рунический менгир", "type": ObjectType.PROP, "pos": (3.0, 5.0), "desc": "Одинокий замшелый монолит, покрытый защитными витыми знаками.", "state": "normal", "tags": ["landmark", "stone"]},
                ],
                "castle": [
                    {"name": "Позолоченный трон", "type": ObjectType.PROP, "pos": (10.0, 4.0), "desc": "Искусный трон под выцветшим бархатом, увенчанный гербовыми штандартами.", "state": "normal", "tags": ["furniture", "royal"]},
                    {"name": "Стойка для оружия", "type": ObjectType.CONTAINER, "pos": (4.0, 8.0), "desc": "Оружейная стойка с алебардами, палашами и пехотными щитами.", "state": "open", "tags": ["weapons", "military"]},
                    {"name": "Кованая решетка", "type": ObjectType.INTERACTABLE, "pos": (10.0, 18.0), "desc": "Тяжелая опускная решетка из кованого железа, преграждающая проход.", "state": "closed", "tags": ["door", "barrier", "iron"]},
                    {"name": "Дворцовый камин", "type": ObjectType.INTERACTABLE, "pos": (16.0, 6.0), "desc": "Роскошный резной камин с гербом лорда, наполняющий залу теплом.", "state": "active", "tags": ["heat", "light"]},
                ],
                "default": [
                    {"name": "Резной постамент", "type": ObjectType.INTERACTABLE, "pos": (10.0, 10.0), "desc": "Возвышение из серого камня, на котором высечены тайные знаки.", "state": "normal", "tags": ["altar", "arcane"]},
                    {"name": "Тяжелый железный ларь", "type": ObjectType.CONTAINER, "pos": (14.0, 8.0), "desc": "Укрепленный металлический ящик с замысловатым замком.", "state": "closed", "tags": ["container", "treasure"]},
                    {"name": "Настенный факел", "type": ObjectType.INTERACTABLE, "pos": (3.0, 3.0), "desc": "Железное бра с горящей смоляной паклей, озаряющее каменную кладку.", "state": "active", "tags": ["light", "fire"]},
                    {"name": "Древняя каменная арка", "type": ObjectType.PROP, "pos": (8.0, 15.0), "desc": "Массивная арка со следами времени, ведущая вглубь таинственного зала.", "state": "normal", "tags": ["landmark", "portal"]},
                ]
            }
        else:
            object_templates = {
                "tavern": [
                    {"name": "Oak Bar Counter", "type": ObjectType.PROP, "pos": (5.0, 5.0), "desc": "A sturdy polished oak counter where drinks and rumors flow.", "state": "normal", "tags": ["furniture", "cover"]},
                    {"name": "Roaring Fireplace", "type": ObjectType.INTERACTABLE, "pos": (15.0, 3.0), "desc": "A stone hearth radiating warm amber light and crackling heat.", "state": "active", "tags": ["fire", "light", "heat"]},
                    {"name": "Supply Crate", "type": ObjectType.CONTAINER, "pos": (3.0, 16.0), "desc": "A wooden crate bound with iron bands, holding spare mugs and cellar goods.", "state": "closed", "tags": ["container", "storage"]},
                    {"name": "Heavy Oak Table", "type": ObjectType.PROP, "pos": (10.0, 10.0), "desc": "A well-used timber table carved with names of adventurers.", "state": "normal", "tags": ["furniture", "table"]},
                ],
                "cave": [
                    {"name": "Ancient Stone Sarcophagus", "type": ObjectType.CONTAINER, "pos": (10.0, 10.0), "desc": "A weathered stone coffin adorned with eroded protective runes.", "state": "closed", "tags": ["container", "relic", "stone"]},
                    {"name": "Glowing Crystal Cluster", "type": ObjectType.INTERACTABLE, "pos": (4.0, 15.0), "desc": "A formation of luminescent crystals casting an eerie azure radiance.", "state": "active", "tags": ["magical", "light", "crystal"]},
                    {"name": "Iron-Bound Chest", "type": ObjectType.CONTAINER, "pos": (16.0, 4.0), "desc": "A rusted iron chest half-buried under fallen cavern shale.", "state": "closed", "tags": ["container", "treasure", "locked"]},
                    {"name": "Stalagmite Barrier", "type": ObjectType.PROP, "pos": (7.0, 8.0), "desc": "Natural stone pillars rising from the subterranean bedrock.", "state": "normal", "tags": ["cover", "stone"]},
                ],
                "forest": [
                    {"name": "Mossy Stone Altar", "type": ObjectType.INTERACTABLE, "pos": (10.0, 10.0), "desc": "An ancient altar consecrated to spirits of the wild woods.", "state": "active", "tags": ["altar", "sacred", "relic"]},
                    {"name": "Hollow Ancient Oak", "type": ObjectType.CONTAINER, "pos": (8.0, 14.0), "desc": "A hollow knot in the roots of a massive oak hiding traveler caches.", "state": "normal", "tags": ["container", "nature"]},
                    {"name": "Campfire Pit", "type": ObjectType.INTERACTABLE, "pos": (14.0, 6.0), "desc": "A ring of river stones with charred embers and dry kindling.", "state": "unlit", "tags": ["fire", "camp"]},
                    {"name": "Carved Runestone", "type": ObjectType.PROP, "pos": (3.0, 5.0), "desc": "A standing monolith etched with spiraling warding runes.", "state": "normal", "tags": ["landmark", "stone"]},
                ],
                "castle": [
                    {"name": "Gilded Throne", "type": ObjectType.PROP, "pos": (10.0, 4.0), "desc": "An ornate throne upholstered in faded crimson velvet beneath heraldic banners.", "state": "normal", "tags": ["furniture", "royal"]},
                    {"name": "Weapon Rack", "type": ObjectType.CONTAINER, "pos": (4.0, 8.0), "desc": "A rack holding iron halberds, broadswords, and parade bucklers.", "state": "open", "tags": ["weapons", "military"]},
                    {"name": "Iron Portcullis", "type": ObjectType.INTERACTABLE, "pos": (10.0, 18.0), "desc": "A heavy lattice gate guarding the passage, operated by a stone lever.", "state": "closed", "tags": ["door", "barrier", "iron"]},
                    {"name": "Stone Hearth", "type": ObjectType.INTERACTABLE, "pos": (16.0, 6.0), "desc": "A grand carved fireplace bearing the royal coat of arms.", "state": "active", "tags": ["heat", "light"]},
                ],
                "default": [
                    {"name": "Carved Stone Dais", "type": ObjectType.INTERACTABLE, "pos": (10.0, 10.0), "desc": "An elevated stone platform inscribed with archaic sigils.", "state": "normal", "tags": ["altar", "arcane"]},
                    {"name": "Heavy Iron Chest", "type": ObjectType.CONTAINER, "pos": (14.0, 8.0), "desc": "A reinforced iron chest with a heavy locking mechanism.", "state": "closed", "tags": ["container", "treasure"]},
                    {"name": "Wall Sconce Torch", "type": ObjectType.INTERACTABLE, "pos": (3.0, 3.0), "desc": "An iron bracket holding a burning torch casting dancing shadows.", "state": "active", "tags": ["light", "fire"]},
                    {"name": "Ancient Archway", "type": ObjectType.PROP, "pos": (8.0, 15.0), "desc": "A weathered stone archway leading further into the mysterious complex.", "state": "normal", "tags": ["landmark", "portal"]},
                ]
            }

        raw_objects = object_templates.get(scene_type, object_templates["default"])
        initial_objects = []
        for i, obj_data in enumerate(raw_objects):
            px, py = obj_data["pos"]
            initial_objects.append(UnifiedObject(
                id=f"{scene_type}_obj_{i+1}",
                name=obj_data["name"],
                description=obj_data["desc"],
                obj_type=obj_data["type"],
                state=obj_data["state"],
                position=Coordinate2D(x=px, y=py),
                tags=obj_data["tags"],
                image_url=asset_manager.get_fallback_placeholder_url("item", subtype=obj_data["name"])
            ))

        scene = SceneNode(
            name=name,
            description=description,
            objects=initial_objects,
            center_position=Coordinate2D(x=10.0, y=10.0),
            dimensions=Coordinate2D(x=20.0, y=20.0),
            scale_unit="feet"
        )
        ensure_scene_battlemap(scene)
        return scene
    
    @classmethod
    def generate_character(cls, name: Optional[str] = None, prompt: str = "", language: str = "ru"):
        """Generate a character procedurally."""
        from core.schemas.in_game import Character, AbilityScores, Item, SpellAbility, Coordinate2D, CharacterClass
        
        if language == "ru":
            char_name = name or f"{random.choice(cls.CHARACTER_NAMES_RU)} {random.choice(cls.CHARACTER_SURNAMES_RU)}"
        else:
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
        
        # Calculate max HP based on class and Constitution modifier
        con_mod = (stats.constitution - 10) // 2
        hp_by_class = {
            CharacterClass.FIGHTER: 10 + con_mod,
            CharacterClass.CLERIC: 8 + con_mod,
            CharacterClass.ROGUE: 8 + con_mod,
            CharacterClass.WIZARD: 6 + con_mod,
        }
        max_hp = max(6, hp_by_class.get(char_class, 10 + con_mod))

        # Generate abilities based on class and language
        abilities = cls._generate_abilities_for_class_ru(char_class) if language == "ru" else cls._generate_abilities_for_class(char_class)
        
        # Generate inventory based on class and language
        inventory = cls._generate_inventory_for_class_ru(char_class) if language == "ru" else cls._generate_inventory_for_class(char_class)
        
        from backend.src.services.asset_manager import asset_manager
        class_str = char_class.value if hasattr(char_class, "value") else str(char_class)
        char_image = asset_manager.get_fallback_placeholder_url("character", subtype=class_str)
        
        default_backstory = "Молодой искатель приключений, жаждущий славы и подвигов." if language == "ru" else "A young adventurer seeking fame and fortune."
        personality_options = ["Храбрый", "Осмотрительный", "Любознательный", "Решительный", "Вдумчивый"] if language == "ru" else ["Brave", "Cautious", "Curious", "Bold", "Thoughtful"]

        return Character(
            name=char_name,
            race="Human",
            char_class=char_class,
            level=1,
            backstory_summary=prompt or default_backstory,
            personality_traits=[random.choice(personality_options)],
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
            image_url=char_image,
        )
        ensure_character_portrait(char)
        return char
    
    @classmethod
    def _generate_abilities_for_class(cls, char_class):
        """Generate abilities based on character class."""
        from core.schemas.in_game import CharacterClass
        if char_class == CharacterClass.FIGHTER:
            return [
                {"name": "Attack", "description": "Make a melee weapon attack dealing 1d8+3 slashing damage", "level": 0},
                {"name": "Second Wind", "description": "Regain 1d10+1 HP as a bonus action (1/short rest)", "level": 0},
                {"name": "Action Surge", "description": "Take one additional action on your turn (1/short rest)", "level": 0},
            ]
        elif char_class == CharacterClass.WIZARD:
            return [
                {"name": "Fire Bolt", "description": "Ranged spell attack dealing 1d10 fire damage", "level": 0},
                {"name": "Magic Missile", "description": "Create 3 darts dealing 1d4+1 force damage each", "level": 1},
                {"name": "Shield", "description": "+5 AC until next turn as a reaction", "level": 1},
            ]
        elif char_class == CharacterClass.ROGUE:
            return [
                {"name": "Attack", "description": "Make a melee weapon attack dealing 1d8+3 piercing damage", "level": 0},
                {"name": "Sneak Attack", "description": "Deal extra 1d6 damage when you have advantage", "level": 0},
                {"name": "Cunning Action", "description": "Dash, Disengage, or Hide as a bonus action", "level": 0},
            ]
        else:  # CLERIC
            return [
                {"name": "Attack", "description": "Make a melee weapon attack dealing 1d6+3 bludgeoning damage", "level": 0},
                {"name": "Healing Word", "description": "Heal a creature for 1d4+3 HP as a bonus action", "level": 1},
                {"name": "Guiding Bolt", "description": "Ranged spell attack dealing 1d6 radiant damage", "level": 1},
            ]

    @classmethod
    def _generate_abilities_for_class_ru(cls, char_class):
        """Generate abilities in Russian based on character class."""
        from core.schemas.in_game import CharacterClass
        if char_class == CharacterClass.FIGHTER:
            return [
                {"name": "Атака оружием", "description": "Рубящий удар оружием ближнего боя, наносящий 1d8+3 урона", "level": 0},
                {"name": "Второе дыхание", "description": "Восстанавливает 1d10+1 ОЗ бонусным действием (1/короткий отдых)", "level": 0},
                {"name": "Всплеск сил", "description": "Совершите одно дополнительное действие в свой ход (1/короткий отдых)", "level": 0},
            ]
        elif char_class == CharacterClass.WIZARD:
            return [
                {"name": "Огненный снаряд", "description": "Дальнобойная заклинательная атака, наносящая 1d10 урона огнем", "level": 0},
                {"name": "Волшебная стрела", "description": "Выпускает 3 самонаводящиеся стрелы, каждая наносит 1d4+1 силового урона", "level": 1},
                {"name": "Щит", "description": "+5 к КД до следующего хода реакцией", "level": 1},
            ]
        elif char_class == CharacterClass.ROGUE:
            return [
                {"name": "Атака клинком", "description": "Колющий удар кинжалом или шпагой, наносящий 1d8+3 урона", "level": 0},
                {"name": "Скрытая атака", "description": "Наносит дополнительные 1d6 урона при наличии преимущества", "level": 0},
                {"name": "Хитрое действие", "description": "Рывок, Отход или Засада бонусным действием", "level": 0},
            ]
        else:  # CLERIC
            return [
                {"name": "Атака булавой", "description": "Дробящий удар освященным оружием, наносящий 1d6+3 урона", "level": 0},
                {"name": "Исцеляющее слово", "description": "Восстанавливает существу 1d4+3 ОЗ бонусным действием", "level": 1},
                {"name": "Направляющий снаряд", "description": "Дальнобойная атака лучистым светом, наносящая 1d6 лучистого урона", "level": 1},
            ]
    
    @classmethod
    def _generate_inventory_for_class(cls, char_class):
        """Generate starting inventory based on class."""
        from core.schemas.in_game import CharacterClass
        from backend.src.services.asset_manager import asset_manager
        if char_class == CharacterClass.FIGHTER:
            items = [
                {"name": "Longsword", "is_equipped": True, "type": "weapon", "damage": "1d8"},
                {"name": "Shield", "is_equipped": True, "type": "armor", "ac_bonus": 2},
                {"name": "Chain Mail", "is_equipped": True, "type": "armor", "ac": 16},
                {"name": "Rations (3 days)", "is_equipped": False, "type": "consumable"},
                {"name": "Health Potion", "is_equipped": False, "type": "consumable", "healing": "2d4+2"},
            ]
        elif char_class == CharacterClass.WIZARD:
            items = [
                {"name": "Quarterstaff", "is_equipped": True, "type": "weapon", "damage": "1d6"},
                {"name": "Spellbook", "is_equipped": True, "type": "tool"},
                {"name": "Robes", "is_equipped": True, "type": "armor", "ac": 12},
                {"name": "Component Pouch", "is_equipped": False, "type": "tool"},
                {"name": "Scroll of Protection", "is_equipped": False, "type": "scroll"},
            ]
        elif char_class == CharacterClass.ROGUE:
            items = [
                {"name": "Shortsword", "is_equipped": True, "type": "weapon", "damage": "1d6"},
                {"name": "Dagger (2)", "is_equipped": False, "type": "weapon", "damage": "1d4"},
                {"name": "Leather Armor", "is_equipped": True, "type": "armor", "ac": 11},
                {"name": "Thieves' Tools", "is_equipped": True, "type": "tool"},
                {"name": "Climbing Gear", "is_equipped": False, "type": "tool"},
            ]
        else:  # CLERIC
            items = [
                {"name": "Mace", "is_equipped": True, "type": "weapon", "damage": "1d6"},
                {"name": "Shield", "is_equipped": True, "type": "armor", "ac_bonus": 2},
                {"name": "Scale Mail", "is_equipped": True, "type": "armor", "ac": 14},
                {"name": "Holy Symbol", "is_equipped": True, "type": "focus"},
                {"name": "Healing Potion", "is_equipped": False, "type": "consumable", "healing": "2d4+2"},
            ]

        for item in items:
            name_and_type = f"{item.get('name', '')} {item.get('type', '')}"
            item["image_url"] = asset_manager.get_fallback_placeholder_url("item", subtype=name_and_type)
        return items

    @classmethod
    def _generate_inventory_for_class_ru(cls, char_class):
        """Generate starting inventory in Russian based on class."""
        from core.schemas.in_game import CharacterClass
        from backend.src.services.asset_manager import asset_manager
        if char_class == CharacterClass.FIGHTER:
            items = [
                {"name": "Длинный меч", "is_equipped": True, "type": "weapon", "damage": "1d8"},
                {"name": "Щит", "is_equipped": True, "type": "armor", "ac_bonus": 2},
                {"name": "Кольчуга", "is_equipped": True, "type": "armor", "ac": 16},
                {"name": "Походный паек (3 дня)", "is_equipped": False, "type": "consumable"},
                {"name": "Зелье лечения", "is_equipped": False, "type": "consumable", "healing": "2d4+2"},
            ]
        elif char_class == CharacterClass.WIZARD:
            items = [
                {"name": "Боевой посох", "is_equipped": True, "type": "weapon", "damage": "1d6"},
                {"name": "Книга заклинаний", "is_equipped": True, "type": "tool"},
                {"name": "Мантия мага", "is_equipped": True, "type": "armor", "ac": 12},
                {"name": "Мешочек с компонентами", "is_equipped": False, "type": "tool"},
                {"name": "Свиток защиты", "is_equipped": False, "type": "scroll"},
            ]
        elif char_class == CharacterClass.ROGUE:
            items = [
                {"name": "Короткий меч", "is_equipped": True, "type": "weapon", "damage": "1d6"},
                {"name": "Кинжал (2)", "is_equipped": False, "type": "weapon", "damage": "1d4"},
                {"name": "Кожаный доспех", "is_equipped": True, "type": "armor", "ac": 11},
                {"name": "Воровские инструменты", "is_equipped": True, "type": "tool"},
                {"name": "Веревка и крюк", "is_equipped": False, "type": "tool"},
            ]
        else:  # CLERIC
            items = [
                {"name": "Окованная булава", "is_equipped": True, "type": "weapon", "damage": "1d6"},
                {"name": "Освященный щит", "is_equipped": True, "type": "armor", "ac_bonus": 2},
                {"name": "Чешуйчатый доспех", "is_equipped": True, "type": "armor", "ac": 14},
                {"name": "Священный символ", "is_equipped": True, "type": "focus"},
                {"name": "Зелье лечения", "is_equipped": False, "type": "consumable", "healing": "2d4+2"},
            ]

        for item in items:
            name_and_type = f"{item.get('name', '')} {item.get('type', '')}"
            item["image_url"] = asset_manager.get_fallback_placeholder_url("item", subtype=name_and_type)
        return items
    
    @classmethod
    def generate_npc(cls, role: str = None, prompt: str = "", language: str = "ru"):
        """Generate an NPC procedurally."""
        from core.schemas.in_game import NPCCharacter, CharacterClass, AbilityScores, Coordinate2D
        from backend.src.services.asset_manager import asset_manager

        if language == "ru":
            npc_role = role or random.choice(cls.NPC_ROLES_RU)
            npc_name = f"{random.choice(cls.CHARACTER_NAMES_RU)} ({npc_role})"
            backstory = prompt or f"Местный житель ({npc_role}), занимающийся повседневными делами."
            personality = [random.choice(["Дружелюбный", "Сдержанный", "Разговорчивый", "Подозрительный"])]
            motivation = random.choice(["Заработать на жизнь", "Защитить семью", "Обрести тайные знания", "Выжить в суровых землях"])
            inventory = [
                {"name": "Простая одежда", "is_equipped": True, "type": "clothing", "image_url": asset_manager.get_fallback_placeholder_url("item", subtype="armor")},
                {"name": "Кошель с 5 зол.", "is_equipped": False, "type": "container", "image_url": asset_manager.get_fallback_placeholder_url("item", subtype="default")},
            ]
            abilities = [
                {
                    "name": "Помощь",
                    "description": "Дает преимущество союзнику на следующую проверку характеристик или бросок атаки в пределах 30 футов",
                    "short_summary": "Дает преимущество союзнику на следующую проверку характеристик или атаку",
                    "level": 0,
                    "type": "action"
                },
            ]
        else:
            npc_role = role or random.choice(cls.NPC_ROLES)
            npc_name = f"{random.choice(cls.CHARACTER_NAMES)} the {npc_role.title()}"
            backstory = prompt or f"A local {npc_role} going about their daily business."
            personality = [random.choice(["Friendly", "Reserved", "Talkative", "Suspicious"])]
            motivation = random.choice(["To earn a living", "To protect their family", "To gain knowledge", "To survive"])
            inventory = [
                {"name": "Common Clothes", "is_equipped": True, "type": "clothing", "image_url": asset_manager.get_fallback_placeholder_url("item", subtype="armor")},
                {"name": "Pouch with 5 gp", "is_equipped": False, "type": "container", "image_url": asset_manager.get_fallback_placeholder_url("item", subtype="default")},
            ]
            abilities = [
                {
                    "name": "Help",
                    "description": "Give advantage to an ally's next ability check or attack within 30 feet",
                    "short_summary": "Give advantage to an ally's next ability check or attack",
                    "level": 0,
                    "type": "action"
                },
            ]
        
        stats = AbilityScores(
            strength=10 + random.randint(-2, 2),
            dexterity=10 + random.randint(-2, 2),
            constitution=10 + random.randint(-2, 2),
            intelligence=10 + random.randint(-2, 2),
            wisdom=10 + random.randint(-2, 2),
            charisma=10 + random.randint(-2, 2),
        )
        npc_image = asset_manager.get_fallback_placeholder_url("character", subtype=npc_role)
        
        return NPCCharacter(
            name=npc_name,
            race="Human",
            char_class=CharacterClass.PEASANT,
            level=1,
            backstory_summary=backstory,
            personality_traits=personality,
            max_hp=15 + stats.constitution,
            current_hp=15 + stats.constitution,
            temp_hp=0,
            armor_class=10,
            speed=30,
            stats=stats,
            image_url=npc_image,
            inventory=inventory,
            active_conditions_list=[],
            resources={},
            position=Coordinate2D(x=15.0, y=15.0),
            abilities=abilities,
            motivation=motivation,
            memory="",
            current_scene="",
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
    character_prompts: List[str] = Field(default_factory=list, description="Начальные описания персонажей в сессии")
    npc_prompts: List[str] = Field(default_factory=list, description="Начальные описания NPC в сессии")
    
    # Настройки AI (опционально)
    gemini_model: str = Field(default="gemini-3.5-flash-lite", description="Модель Gemini")
    language: str = Field(default="ru", description="Язык повествования и интерфейса ('ru' или 'en')")

    @validator('language')
    def validate_language(cls, v):
        if not v or v.lower() not in ("ru", "en"):
            return "ru"
        return v.lower()

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

    @validator('game_mode')
    def validate_game_mode(cls, v):
        if not v:
            return "STORY"
        valid_modes = {"STORY", "COMBAT", "SANDBOX"}
        if v.upper() not in valid_modes:
            raise ValueError(f"Invalid game mode: {v}. Must be one of {valid_modes}")
        return v.upper()


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
    language: Optional[str] = "ru"
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
    language: Optional[str] = Field(None, description="Язык повествования ('ru' или 'en')")
    max_players: Optional[int] = Field(None, ge=1, le=20)
    is_public: Optional[bool] = None
    
    @validator('session_name')
    def validate_session_name(cls, v):
        if v:
            v = sanitize_string(v, max_length=100)
            if len(v) < 2:
                raise ValueError("Session name must be at least 2 characters")
        return v


class LanguageUpdateRequest(BaseModel):
    """Запрос на изменение глобального языка сессии."""
    language: str = Field(..., description="Язык сессии ('ru' или 'en')")


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


class PlayerJoinWithProfileRequest(BaseModel):
    """Запрос на присоединение игрока с использованием сохранённого профиля персонажа."""
    player_name: str = Field(..., description="Имя игрока", min_length=2, max_length=100)
    profile_id: int = Field(..., description="ID сохранённого профиля персонажа")

    @validator('player_name')
    def validate_player_name(cls, v):
        v = sanitize_string(v, max_length=100)
        if len(v) < 2:
            raise ValueError("Player name must be at least 2 characters")
        return v


class PlayerJoinAIGeneratedRequest(BaseModel):
    """Запрос на присоединение с AI-генерацией персонажа."""
    player_name: str = Field(..., description="Имя игрока", min_length=2, max_length=100)
    character_description: str = Field(..., description="Краткое описание персонажа для AI", min_length=5, max_length=500)

    @validator('player_name')
    def validate_player_name(cls, v):
        v = sanitize_string(v, max_length=100)
        if len(v) < 2:
            raise ValueError("Player name must be at least 2 characters")
        return v


class PlayerJoinRandomRequest(BaseModel):
    """Запрос на присоединение со случайным персонажем."""
    player_name: str = Field(..., description="Имя игрока", min_length=2, max_length=100)

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


class CharacterRosterItem(BaseModel):
    """Character entry in a session roster with AI/player controller status."""
    name: str
    char_class: str
    race: str
    level: int = 1
    current_hp: int = 10
    max_hp: int = 10
    armor_class: int = 10
    image_url: Optional[str] = None
    is_occupied: bool = False
    is_ai_controlled: bool = False
    controller_name: Optional[str] = None
    controller_id: Optional[str] = None
    can_claim: bool = True


class ClaimCharacterRequest(BaseModel):
    """Request to join a session claiming an existing character."""
    character_name: str
    player_name: Optional[str] = None


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
    plot: Optional[Dict[str, Any]] = None
    current_chapter: Optional[Dict[str, Any]] = None


class SessionStartResponse(BaseModel):
    """Response for session start/restart."""
    success: bool
    session_id: str
    scene_name: Optional[str] = None
    player_count: int = 0
    npc_count: int = 0
    game_mode: str = "STORY"
    message: Optional[str] = None


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
    from backend.src.logging.request_tracing import RequestTracer, get_trace_id

    logger = logging.getLogger(__name__)
    trace_id = get_trace_id()

    session_uuid = str(uuid.uuid4())

    # Log request tracing
    logger.debug(
        f"ENTERING: create_session | "
        f"Trace ID: {trace_id} | Session UUID: {session_uuid} | User ID: {current_user.id}"
    )
    
    logger.info(f"Creating session: {session_uuid} - {request.session_name} for user {current_user.id}")

    repository = get_session_repository(db)

    try:
        # Step 1: Create session in database FIRST
        db_session = repository.create_session(
            session_uuid=session_uuid,
            session_name=request.session_name,
            owner_id=current_user.id,
            game_mode=request.game_mode,
            session_data={
                "max_players": request.max_players,
                "description": request.description,
                "guide": request.guide,
                "gemini_model": request.gemini_model,
                "language": request.language,
                "is_public": request.is_public,
                "participants": []
            }
        )

        logger.info(f"Database session created: {db_session.id} (UUID: {db_session.session_uuid}, owner_id={db_session.owner_id}, lang={request.language})")

        # Step 2: Create in-memory game session with the SAME UUID
        config = SessionConfig(
            session_name=request.session_name,
            game_mode=request.game_mode,
            max_players=request.max_players,
            description=request.description,
            guide=request.guide,
            gemini_model=request.gemini_model,
            language=request.language
        )

        # Pass the session_uuid to factory so it uses the same ID
        # SessionFactory will register it with session_manager automatically
        game_session = session_factory.create_session(config, session_id=session_uuid)

        logger.info(f"Game session created in memory: {session_uuid}")

        # Step 2.2: Initialize session-scoped characters & NPCs
        from core.entity.orchestrator import Orchestrator
        if request.character_prompts:
            char_prompts = request.character_prompts
        elif request.language == "ru":
            char_prompts = [
                "Валерос, воин-человек с тяжелым мечом и щитом",
                "Фэй, эльфийская плутовка с парными кинжалами и отмычками"
            ]
        else:
            char_prompts = [
                "Valeros, human fighter with a heavy broadsword and shield",
                "Faye, elven rogue with twin silver daggers and lockpicks"
            ]

        for cp in char_prompts:
            try:
                char = procedural_gen.generate_character(name=None, prompt=cp, language=request.language)
                ensure_character_portrait(char, session_uuid)
                char.is_ai_controlled = True
                orch = Orchestrator(
                    generator=game_session.generator,
                    logger=game_session.logger.getChild("player_orchestrator")
                )
                orch.add_state(game_session)
                p = game_session._init_player(char, orch)
                p.is_ai_controlled = True
                game_session.players.append(p)
                logger.info(f"[CREATE-SESSION] Added initial session character: {char.name}")
            except Exception as char_err:
                logger.warning(f"[CREATE-SESSION] Error creating initial character: {char_err}")

        npc_prompts_to_use = request.npc_prompts
        if not npc_prompts_to_use:
            scene_type = procedural_gen._find_scene_type(game_session.current_scene.name if game_session.current_scene else "")
            if request.language == "ru":
                default_npc_map = {
                    "tavern": [
                        "Барнаби, радушный трактирщик, знающий все окрестные слухи и вести о заданиях",
                        "Гаррик, отдыхающий городской стражник, пьющий эль, но чутко следящий за порядком"
                    ],
                    "cave": [
                        "Гимбл Писец, нервный гном-ученый, исследующий подземные друзы кристаллов",
                        "Корвин, суровый раненый наемник, устроивший привал у входа в пещеру"
                    ],
                    "forest": [
                        "Сайлас Следопыт, молчаливый разведчик, выслеживающий следы зверя в зарослях",
                        "Мейв, загадочная травница, собирающая лунные цветы и редкий мох"
                    ],
                    "castle": [
                        "Капитан Вэнс, непреклонный командир гарнизона, проверяющий посты и дозоры",
                        "Эловин, королевский архивариус с запечатанными имперскими свитками"
                    ],
                    "default": [
                        "Местный проводник, бывалый следопыт, знающий тропы и опасности здешних земель",
                        "Странствующий купец, расчетливый торговец с редкими диковинками и новостями"
                    ]
                }
            else:
                default_npc_map = {
                    "tavern": [
                        "Barnaby, a jovial tavern keeper who knows all regional rumors and rumors of quests",
                        "Garrick, an off-duty town guard enjoying an ale but watchful for trouble"
                    ],
                    "cave": [
                        "Gimble the Scribe, a nervous gnome scholar recording subterranean crystal formations",
                        "Corvin, a grim wounded mercenary camping near the cave entrance"
                    ],
                    "forest": [
                        "Silas the Ranger, a quiet wilderness scout tracking beast tracks in the brush",
                        "Maeve, an enigmatic herbalist gathering moonlit blossoms and rare moss"
                    ],
                    "castle": [
                        "Captain Vance, a stern garrison captain checking defenses and patrols",
                        "Elowen, a royal archivist carrying sealed imperial scrolls"
                    ],
                    "default": [
                        "Local Guide, a seasoned local who knows paths and perils of the realm",
                        "Wandering Merchant, a shrewd traveler with rare trade goods and gossip"
                    ]
                }
            npc_prompts_to_use = default_npc_map.get(scene_type, default_npc_map["default"])

        for np in npc_prompts_to_use:
            try:
                npc_char = procedural_gen.generate_npc(prompt=np, language=request.language)
                if game_session.current_scene:
                    npc_char.current_scene = game_session.current_scene.name
                game_session._init_npc(npc_char)
                logger.info(f"[CREATE-SESSION] Added initial session NPC: {npc_char.name} pinned to '{npc_char.current_scene}'")
            except Exception as npc_err:
                logger.warning(f"[CREATE-SESSION] Error creating initial NPC: {npc_err}")

        # Step 2.5: Persist initial game state (characters, starting scene, plot) to database
        try:
            initial_state = game_session.get_session_state()
            repository.update_session_data(session_uuid, initial_state, owner_id=current_user.id)
            if getattr(game_session, "current_scene", None):
                repository.update_session_scene(session_uuid, game_session.current_scene.name, owner_id=current_user.id)
            logger.info(f"Database session initialized with starting scene: '{game_session.current_scene.name if game_session.current_scene else None}' and {len(game_session.players)} characters")
        except Exception as state_err:
            logger.warning(f"Could not persist initial game state to DB: {state_err}")

        # Step 3: Add owner as participant in database
        participant = repository.add_participant(
            session_uuid=session_uuid,
            player_uuid=str(uuid.uuid4()),
            player_name=current_user.username,
            user_id=current_user.id,
            role="owner",
            owner_id=current_user.id
        )

        logger.info(f"Owner added as participant: {participant.get('player_uuid') if participant else 'FAILED'}")

        # Step 4: Verify session is in database
        verify_session = repository.get_session_by_uuid(session_uuid)
        if not verify_session:
            logger.error(f"VERIFICATION FAILED: Session not found in database after creation!")
        else:
            logger.info(f"VERIFIED: Session exists in database with owner_id={verify_session.owner_id}")

        # Log success
        logger.debug(
            f"EXITING: create_session | "
            f"Trace ID: {trace_id} | Status: SUCCESS | Session ID: {db_session.session_uuid}"
        )

        return SessionResponse(
            session_id=db_session.session_uuid,
            session_name=db_session.session_name,
            game_mode=db_session.game_mode.value,
            player_count=1,
            status=db_session.status.value,
            description=get_session_description(db_session),
            language=request.language,
            owner_id=db_session.owner_id,
            owner_name=current_user.username,
            created_at=db_session.created_at.isoformat(),
            is_owner=True
        )

    except ImportError as e:
        logger.error(f"ImportError creating session: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"SKLS dependencies not installed: {str(e)}")
    except Exception as e:
        logger.error(f"Exception creating session: {e}", exc_info=True)
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
        game_session = session_manager.get_session(db_session.session_uuid)
        player_count = 0

        if game_session:
            player_count = len(game_session.players)
        else:
            # Get from DB
            participants = repository.get_session_participants(db_session.session_uuid)
            player_count = len([p for p in participants if p.get('is_connected')])
        
        s_data = db_session.session_data or {}
        lang = s_data.get('language') or (getattr(game_session, 'language', 'ru') if game_session else 'ru')

        session_list.append(SessionResponse(
            session_id=db_session.session_uuid,
            session_name=db_session.session_name,
            game_mode=db_session.game_mode.value,
            player_count=player_count,
            status=db_session.status.value,
            description=get_session_description(db_session),
            language=lang,
            owner_id=db_session.owner_id,
            owner_name=current_user.username,
            created_at=db_session.created_at.isoformat(),
            is_owner=True
        ))
    
    return SessionListResponse(
        sessions=session_list,
        total=len(session_list)
    )


@router.get("/public", response_model=Dict[str, Any])
async def browse_public_sessions(
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Browse all active sessions.

    Returns all active sessions, with optional search by name, description, or session UUID.
    Any authenticated user can see and join these sessions.
    """
    repository = get_session_repository(db)

    # Get all active sessions
    all_sessions = repository.get_all_active_sessions()

    # Apply search filter by name, description, or UUID
    if search:
        search_lower = search.lower()
        filtered_sessions = []
        for s in all_sessions:
            session_data = s.session_data or {}
            matches = (
                search_lower in s.session_name.lower()
                or search_lower in session_data.get('description', '').lower()
                or search_lower in s.session_uuid.lower()
            )
            if matches:
                filtered_sessions.append(s)
        sessions_to_show = filtered_sessions
    else:
        sessions_to_show = all_sessions

    # Apply pagination
    total = len(sessions_to_show)
    paginated_sessions = sessions_to_show[skip:skip + limit]

    # Get user's joined sessions to mark them
    user_sessions = repository.get_owner_sessions(owner_id=current_user.id, active_only=False)
    user_session_ids = {s.session_uuid for s in user_sessions}

    # Also get sessions where user is a participant
    user_participant_sessions = set()
    for session in all_sessions:
        participants = repository.get_session_participants(session.session_uuid)
        for p in participants:
            if p.get('user_id') == current_user.id:
                user_participant_sessions.add(session.session_uuid)

    result_sessions = []
    for db_session in paginated_sessions:
        # Get participant count
        participants = repository.get_session_participants(db_session.session_uuid)
        player_count = len(participants)

        # Get max_players
        max_players = get_session_max_players(db_session)

        # Get owner name
        owner = db.query(User).filter(User.id == db_session.owner_id).first()
        owner_name = owner.username if owner else "Unknown"

        result_sessions.append({
            "session_id": db_session.session_uuid,
            "session_name": db_session.session_name,
            "game_mode": db_session.game_mode.value,
            "status": db_session.status.value,
            "description": get_session_description(db_session),
            "owner_name": owner_name,
            "player_count": player_count,
            "max_players": max_players,
            "created_at": db_session.created_at.isoformat(),
            "is_owner": db_session.owner_id == current_user.id,
            "has_joined": db_session.session_uuid in user_participant_sessions or db_session.session_uuid in user_session_ids
        })

    return {
        "sessions": result_sessions,
        "total": total,
        "skip": skip,
        "limit": limit,
        "search": search
    }


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
    game_session = session_manager.get_session(session_id)
    player_count = 0
    
    # Get players from DB
    participants = repository.get_session_participants(session_id)
    
    # Get ready status for this session
    session_ready_status = waiting_room_ready_status.get(session_id, {})
    
    players = []
    if game_session:
        player_count = len(game_session.players)
    else:
        player_count = len([p for p in participants if p.get('is_connected')])
    
    # Build players list with ready status
    for p in participants:
        is_ready = session_ready_status.get(p.get('user_id'), False) if p.get('user_id') else False
        players.append(PlayerResponse(
            player_id=p.get('player_uuid'),
            player_name=p.get('player_name'),
            character_name=p.get('character_name'),
            connected=p.get('is_connected'),
            role=p.get('role'),
            is_ready=is_ready
        ))

    s_data = db_session.session_data or {}
    session_lang = s_data.get('language') or (getattr(game_session, 'language', 'ru') if game_session else 'ru')

    return SessionResponse(
        session_id=db_session.session_uuid,
        session_name=db_session.session_name,
        game_mode=db_session.game_mode.value,
        player_count=player_count,
        status=db_session.status.value,
        description=get_session_description(db_session),
        language=session_lang,
        owner_id=db_session.owner_id,
        owner_name=current_user.username if db_session.owner_id == current_user.id else None,
        created_at=db_session.created_at.isoformat(),
        is_owner=(db_session.owner_id == current_user.id),
        players=players
    )


# ===================================================================
# PUBLIC SESSION BROWSING ENDPOINTS
# ===================================================================

class PublicSessionResponse(BaseModel):
    """Response for public session listing."""
    session_id: str
    session_name: str
    game_mode: str
    status: str
    description: Optional[str] = None
    owner_name: str
    player_count: int
    max_players: int
    created_at: str
    is_owner: bool
    has_joined: bool


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

    # Update session_data JSON instead of direct fields
    session_data_updates = {}
    
    if request.session_name is not None:
        db_session.session_name = request.session_name
    if request.description is not None:
        session_data_updates['description'] = request.description
    if request.guide is not None:
        session_data_updates['guide'] = request.guide
    if request.max_players is not None:
        session_data_updates['max_players'] = request.max_players
    if request.is_public is not None:
        session_data_updates['is_public'] = request.is_public
    if request.language is not None:
        session_data_updates['language'] = request.language
        game_session = session_manager.get_session(session_id)
        if game_session:
            game_session.set_language(request.language)

    # Apply session_data updates if any
    if session_data_updates:
        session_data = dict(db_session.session_data or {})
        session_data.update(session_data_updates)
        db_session.session_data = session_data
        flag_modified(db_session, "session_data")

    db_session.updated_at = datetime.now()
    db.commit()
    db.refresh(db_session)
    
    # Get player count
    participants = repository.get_session_participants(session_id)
    player_count = len([p for p in participants if p.get('is_connected')])
    
    current_lang = (db_session.session_data or {}).get('language', 'ru')

    return SessionResponse(
        session_id=db_session.session_uuid,
        session_name=db_session.session_name,
        game_mode=db_session.game_mode.value,
        player_count=player_count,
        status=db_session.status.value,
        description=get_session_description(db_session),
        language=current_lang,
        owner_id=db_session.owner_id,
        owner_name=current_user.username,
        created_at=db_session.created_at.isoformat(),
        is_owner=True
    )


@router.patch("/{session_id}/language", response_model=dict)
@router.post("/{session_id}/language", response_model=dict)
async def update_session_language(
    session_id: str,
    request: LanguageUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновить глобальный язык сессии (для Game Master, сюжетных описаний и персонажей).
    """
    repository = get_session_repository(db)
    db_session = get_session_by_uuid_or_404(session_id, repository)
    if request.language not in ["ru", "en"]:
        raise HTTPException(status_code=400, detail="Language must be 'ru' or 'en'")

    session_data = dict(db_session.session_data or {})
    if session_data.get("language"):
        raise HTTPException(
            status_code=400,
            detail="Session language is set when creating the adventure and locked afterwards."
        )

    # Update in DB
    session_data["language"] = request.language
    db_session.session_data = session_data
    flag_modified(db_session, "session_data")
    db_session.updated_at = datetime.now()
    db.commit()
    db.refresh(db_session)

    # Update in-memory session engine
    game_session = session_manager.get_session(session_id)
    if game_session:
        game_session.set_language(request.language)

    return {
        "status": "success",
        "session_id": session_id,
        "language": request.language,
        "message": f"Global session language switched to {request.language}"
    }


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
    game_session = session_manager.get_session(session_id)
    if game_session:
        await session_manager.remove_session(session_id)
    
    # Delete from database
    repository.delete_session(session_id, owner_id=current_user.id)


@router.post("/{session_id}/start", response_model=SessionStartResponse)
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
    game_session = session_manager.get_session(session_id)
    logger.info(f"[START] Session check: {session_id} - found: {game_session is not None}")

    # Check if we have saved game state in the database
    has_saved_state = bool(db_session.session_data and db_session.session_data.get("current_scene"))

    if not game_session:
        # Session exists in DB but not in memory - need to initialize it
        logger.warning(f"[START] Session {session_id} found in DB but not in memory. Initializing...")

        # Initialize the game session from DB
        try:
            config = SessionConfig(
                session_name=db_session.session_name,
                game_mode=db_session.game_mode.value,
                max_players=get_session_max_players(db_session),
                description=get_session_description(db_session),
                guide=get_session_guide(db_session),
                gemini_model=get_session_gemini_model(db_session) or "gemini-3.5-flash-lite"
            )
            logger.info(f"[START] Creating session factory config: {config.session_name}")
            game_session = session_factory.create_session(config, session_id=session_id)

            # Try to restore saved game state if it exists
            if has_saved_state:
                logger.info(f"[START] Restoring saved game state from database...")
                restored = game_session.restore_session_from_serialized(db_session.session_data)
                if restored:
                    logger.info(f"[START] ✓ Game state restored successfully: {len(game_session.players)} players, {len(game_session.npcs)} NPCs")
                    
                    # Restore player-character mappings if they exist
                    player_mapping = db_session.session_data.get('player_character_mapping', {})
                    if player_mapping:
                        logger.info(f"[START] ✓ Restored {len(player_mapping)} player-character mappings")
                        # Update participants with their character names
                        for participant in repository.get_session_participants(session_id):
                            player_id = participant.get('player_uuid')
                            if player_id and player_id in player_mapping:
                                char_name = player_mapping[player_id]
                                logger.info(f"[START]   Player {player_id} → {char_name}")
                    
                    logger.info(f"[START] ✓ Session fully restored - skipping fresh generation")
                    # Session is fully restored - skip fresh generation
                    # Save restored state to ensure database is in sync
                    try:
                        session_state = game_session.get_session_state()
                        repository.update_session_data(session_id, session_state)
                        logger.info(f"[START] ✓ Restored state saved to database")
                    except Exception as save_err:
                        logger.warning(f"[START] Failed to save restored state: {save_err}")

                    # Return success with restored session info
                    return SessionStartResponse(
                        success=True,
                        session_id=session_id,
                        scene_name=game_session.current_scene.name if game_session.current_scene else None,
                        player_count=len(game_session.players),
                        npc_count=len(game_session.npcs),
                        game_mode=game_session.game_mode.value,
                        message="Session restored from database"
                    )
                else:
                    logger.warning(f"[START] ✗ Failed to restore game state, will generate fresh session")
                    has_saved_state = False
            else:
                logger.info(f"[START] No saved game state found, will generate fresh session")
        except Exception as e:
            logger.error(f"[START] Failed to create session: {e}", exc_info=True)
            raise HTTPException(
                status_code=400,
                detail=f"Session not initialized: {str(e)}. Please recreate the session."
            )
    else:
        logger.info(f"[START] Session {session_id} found in memory")

        # Check if we should restore saved state (server restart scenario)
        if has_saved_state and not game_session.current_scene:
            logger.info(f"[START] Restoring saved game state to existing session...")
            restored = game_session.restore_session_from_serialized(db_session.session_data)
            if restored:
                logger.info(f"[START] ✓ Game state restored: {len(game_session.players)} players, {len(game_session.npcs)} NPCs")
                
                # Restore player-character mappings if they exist
                player_mapping = db_session.session_data.get('player_character_mapping', {})
                if player_mapping:
                    logger.info(f"[START] ✓ Restored {len(player_mapping)} player-character mappings")
                
                has_saved_state = True
                logger.info(f"[START] ✓ Session restored from database - skipping fresh generation")

                # Return success with restored session info
                return SessionStartResponse(
                    success=True,
                    session_id=session_id,
                    scene_name=game_session.current_scene.name if game_session.current_scene else None,
                    player_count=len(game_session.players),
                    npc_count=len(game_session.npcs),
                    game_mode=game_session.game_mode.value,
                    message="Session restored from database"
                )

    logger.info(f"[START] Game session found, saved_state={has_saved_state}, wishes={request.wishes}")

    # Only generate fresh scene if no saved state exists
    if not has_saved_state:
        logger.info(f"[START] === Generating fresh session content ===")
    
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
        ensure_scene_battlemap(scene)

        # Update DB
        repository.update_session_scene(session_id, game_session.current_scene.name, owner_id=current_user.id)
        repository.update_session_status(session_id, "running", owner_id=current_user.id)

        # === CRITICAL FIX: Map database participants to engine players ===
        # Get all participants who joined via the join endpoint
        db_participants = repository.get_session_participants(session_id)
        logger.info(f"[START] Found {len(db_participants)} database participants to assign characters to")

        # Get player profile IDs mapping (if players joined with profiles)
        session_data = db_session.session_data or {}
        player_profile_ids = session_data.get('player_profile_ids', {})
        if player_profile_ids:
            logger.info(f"[START] Found {len(player_profile_ids)} player profile mappings")

        # Build participant info list
        participants_to_assign = []
        for participant in db_participants:
            player_id = participant.get('player_uuid')
            profile_id = player_profile_ids.get(player_id)

            participants_to_assign.append({
                'player_id': player_id,
                'player_name': participant.get('player_name'),
                'user_id': participant.get('user_id'),
                'character_name': participant.get('character_name'),
                'role': participant.get('role', 'player'),
                'profile_id': profile_id
            })

        # Filter out participants who ALREADY have Player objects in the engine
        # (they joined while the game was running and created their own characters)
        engine_player_names = {p.character.name for p in game_session.players if hasattr(p, 'character')}
        participants_to_assign = [p for p in participants_to_assign if p['player_name'] not in engine_player_names]

        logger.info(f"[START] Will assign characters to {len(participants_to_assign)} participants (not yet in engine)")

        # DO NOT auto-generate characters during start_session.
        # All players (including the owner) pick their characters through JoinSession
        # after the game is running. This gives everyone full control over their character.
        character_prompts_to_use = []
        if participants_to_assign:
            logger.info(f"[START] {len(participants_to_assign)} participant(s) waiting — they will join via JoinSession to pick characters")

        logger.info(f"[START] Generating {len(character_prompts_to_use)} characters...")

        # Import profile converter for creating characters from profiles
        from backend.src.utils.character_converter import profile_to_character
        from backend.src.repositories.character_profile_repository import CharacterProfileRepository
        profile_repo = CharacterProfileRepository(db)

        # Track player_id to character_name mapping for persistence
        player_character_mapping = {}

        # Generate characters using AI/procedural OR from profiles
        for i, prompt in enumerate(character_prompts_to_use):
            logger.info(f"[START] Generating character {i+1}: {prompt[:100]}...")
            character = None

            # Check if this participant has a saved profile
            participant_has_profile = False
            if i < len(participants_to_assign):
                participant = participants_to_assign[i]
                profile_id = participant.get('profile_id')
                
                if profile_id:
                    logger.info(f"[START] Participant has profile ID {profile_id}, converting to character...")
                    try:
                        # Get profile from database
                        profile = profile_repo.get_by_id(profile_id, current_user.id)
                        if profile:
                            # Convert profile to Character
                            character = profile_to_character(profile)
                            participant_has_profile = True
                            logger.info(f"[START] ✓ Character created from profile: {character.name} ({profile.race} {profile.char_class})")
                        else:
                            logger.warning(f"[START] Profile {profile_id} not found, falling back to generation")
                    except Exception as e:
                        logger.error(f"[START] Failed to convert profile to character: {e}", exc_info=True)
                        # Fall through to AI/procedural generation

            # If no profile or profile conversion failed, use AI/procedural generation
            if not participant_has_profile:
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
                
                # Map this character to a participant if available
                if i < len(participants_to_assign):
                    participant = participants_to_assign[i]
                    player_id = participant.get('player_id')
                    if player_id:
                        player_character_mapping[player_id] = character.name
                        logger.info(f"[START] ✓ Mapped player_id {player_id} → character '{character.name}'")

                        # Update database participant with character_name
                        try:
                            repository.update_participant_character_name(
                                session_id, player_id, character.name, owner_id=current_user.id
                            )
                            logger.info(f"[START] ✓ Updated database participant with character_name: {character.name}")
                        except Exception as db_err:
                            logger.warning(f"[START] Failed to update participant character_name in DB: {db_err}")

                logger.info(f"[START] ✓ Character {character.name} added to session. Total players: {len(game_session.players)}")
            except Exception as e:
                logger.error(f"[START] Failed to create player: {e}", exc_info=True)
                # Continue anyway - we'll try procedural fallback for next character

        # Persist player-character mapping in session_data for restoration
        if player_character_mapping:
            logger.info(f"[START] Persisting {len(player_character_mapping)} player-character mappings")
            try:
                session_state = game_session.get_session_state()
                # Add player mapping to session_data
                if 'player_character_mapping' not in session_state:
                    session_state['player_character_mapping'] = {}
                session_state['player_character_mapping'].update(player_character_mapping)
                repository.update_session_data(session_id, session_state, owner_id=current_user.id)
                logger.info(f"[START] ✓ Player-character mappings saved to database")
            except Exception as e:
                logger.warning(f"[START] Failed to save player-character mapping: {e}")

        logger.info(f"[START] Session has {len(game_session.players)} players")

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
                "A fairy queen's messenger with urgent news for the kingdom",
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
                logger.info(f"[START] ✓ Procedural NPC generated: {npc_character.name} ({npc_character.char_class.value})")
                
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

        # Save game state to database
        try:
            session_state = game_session.get_session_state()
            repository.update_session_data(session_id, session_state, owner_id=current_user.id)
            logger.info(f"[START] ✓ Game state saved to database")
        except Exception as e:
            logger.warning(f"[START] Failed to save game state to database: {e}")

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

        return SessionStartResponse(
            success=True,
            session_id=session_id,
            scene_name=game_session.current_scene.name if game_session.current_scene else None,
            player_count=len(game_session.players),
            npc_count=len(game_session.npcs),
            game_mode=game_session.game_mode.value,
            message="Session started — connect via WebSocket to begin playing"
        )

    except Exception as e:
        game_session.logger.error(f"Ошибка при запуске сессии: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при запуске сессии: {str(e)}"
        )


# Track which sessions have their game loop running
_active_game_loops: set = set()


def ensure_session_in_memory(session_id: str, db: Optional[Session] = None):
    """
    Ensure the game session is loaded in session_manager RAM.
    If not loaded (e.g. after server reboot), automatically restore it from database.
    """
    game_session = session_manager.get_session(session_id)
    if game_session:
        # Self-healing: ensure scene and plot exist even if loaded from memory
        if not getattr(game_session, "current_scene", None):
            scene = procedural_gen.generate_scene(game_session.session_name)
            ensure_scene_battlemap(scene)
            game_session.current_scene = scene
            game_session.all_locations[scene.name] = scene
            game_session.current_location_name = scene.name
        if not getattr(game_session, "_plot", None):
            game_session._init_plot(game_session.session_name)
        return game_session

    close_db = False
    if db is None:
        from backend.src.database.session import SessionLocal
        db = SessionLocal()
        close_db = True

    try:
        from backend.src.repositories.session_repository import SessionRepository
        from backend.src.game.session_factory import SessionConfig
        repo = SessionRepository(db)
        db_session = repo.get_session_by_uuid(session_id)
        if not db_session:
            return None

        config = SessionConfig(
            session_name=db_session.session_name,
            game_mode=db_session.game_mode.value,
            max_players=get_session_max_players(db_session),
            description=get_session_description(db_session),
            guide=get_session_guide(db_session),
            gemini_model=get_session_gemini_model(db_session) or "gemini-3.5-flash-lite",
        )
        game_session = session_factory.create_session(config, session_id=session_id)

        if db_session.session_data:
            try:
                game_session.restore_session_from_serialized(db_session.session_data)
                for p in game_session.players:
                    if hasattr(p, 'character'):
                        ensure_character_portrait(p.character, session_id)
                logger.info(f"[RESTORE] Session {session_id} successfully restored from serialized state with {len(game_session.players)} players")
            except Exception as e:
                logger.warning(f"[RESTORE] Error restoring session_data for {session_id}: {e}")

        # Ensure current_scene is present
        if not getattr(game_session, "current_scene", None):
            guide = get_session_guide(db_session) or "A tactical battle encounter in an ancient stone chamber."
            game_session.current_scene = procedural_gen.generate_scene(guide)
            ensure_scene_battlemap(game_session.current_scene)
            game_session.all_locations[game_session.current_scene.name] = game_session.current_scene
            game_session.current_location_name = game_session.current_scene.name

        if not getattr(game_session, "_plot", None):
            game_session._init_plot(get_session_guide(db_session) or db_session.session_name)

        # Restore any missing participants from DB
        participants = repo.get_session_participants(session_id)
        for part in participants:
            cname = part.get("character_name")
            if cname and not any(hasattr(p, 'character') and p.character.name == cname for p in game_session.players):
                from core.entity.orchestrator import Orchestrator
                char = procedural_gen.generate_character(name=cname, prompt="")
                char.controlled_by_player_id = part.get("player_uuid")
                char.is_ai_controlled = True
                orchestrator = Orchestrator(
                    generator=game_session.generator,
                    logger=game_session.logger.getChild("player_orchestrator")
                )
                orchestrator.add_state(game_session)
                player = game_session._init_player(char, orchestrator)
                player.is_ai_controlled = True
                game_session.players.append(player)

        return game_session
    except Exception as err:
        logger.error(f"[ENSURE-SESSION] Error restoring session {session_id}: {err}", exc_info=True)
        return None
    finally:
        if close_db:
            db.close()


async def _run_game_loop(session_id: str, game_session) -> None:
    """Run the Session game_loop as a background task."""
    try:
        await game_session.game_loop()
    except Exception:
        game_session.logger.error("Game loop crashed", exc_info=True)
    finally:
        _active_game_loops.discard(session_id)
        game_session.logger.info("Game loop stopped")


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
    game_session = session_manager.get_session(session_id)
    
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
                player_id=p.get('player_uuid'),
                player_name=p.get('player_name'),
                character_name=p.get('character_name'),
                connected=p.get('is_connected'),
                role=p.get('role')
            ))
    
    return SessionInfoResponse(
        session_id=db_session.session_uuid,
        session_name=db_session.session_name,
        game_mode=db_session.game_mode.value,
        player_count=player_count,
        max_players=get_session_max_players(db_session),
        status=db_session.status.value,
        description=get_session_description(db_session),
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
    from core.entity.orchestrator import Orchestrator
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
    
    # Check if player already joined (by player_name)
    game_session = session_manager.get_session(session_id)
    for participant in existing_participants:
        if participant.get('player_name') == request.player_name:
            if participant.get('user_id') == current_user.id:
                char_name = participant.get('character_name')
                player_id = participant.get('player_uuid')
                if not char_name and request.character_name:
                    char_name = request.character_name
                    repository.update_participant_character_name(session_id, player_id, char_name)

                if game_session and char_name and not any(hasattr(p, 'character') and p.character.name == char_name for p in game_session.players):
                    character = ProceduralGenerator.generate_character(name=char_name, prompt="")
                    orchestrator = Orchestrator(
                        generator=game_session.generator,
                        logger=game_session.logger.getChild("player_orchestrator")
                    )
                    orchestrator.add_state(game_session)
                    player = game_session._init_player(character, orchestrator)
                    game_session.players.append(player)

                return PlayerResponse(
                    player_id=player_id,
                    player_name=participant.get('player_name'),
                    character_name=char_name,
                    connected=participant.get('is_connected', True),
                    role=participant.get('role', 'player')
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Player '{request.player_name}' is already in this session"
                )

    # Check max players
    if len(existing_participants) >= get_session_max_players(db_session):
        raise HTTPException(
            status_code=400,
            detail=f"Session is full (max {get_session_max_players(db_session)} players)"
        )

    # Determine role - owner gets 'owner' role only for their primary owner participant slot
    role = "owner" if (db_session.owner_id == current_user.id and request.player_name == current_user.username) else "player"

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

    if game_session and request.character_name:
        character = ProceduralGenerator.generate_character(name=request.character_name, prompt="")
        ensure_character_portrait(character, session_id)
        character.controlled_by_player_id = player_id
        character.is_ai_controlled = False
        orchestrator = Orchestrator(
            generator=game_session.generator,
            logger=game_session.logger.getChild("player_orchestrator")
        )
        orchestrator.add_state(game_session)
        player = game_session._init_player(character, orchestrator)
        player.is_ai_controlled = False
        if not any(hasattr(p, 'character') and p.character.name == character.name for p in game_session.players):
            game_session.players.append(player)
        try:
            repository.update_session_data(session_id, game_session.get_session_state())
        except Exception as e:
            logger.warning(f"Failed to update session data after player joined: {e}")

        entrance_narrative = generate_character_entrance_narrative(
            generator=game_session.generator,
            session=game_session,
            character_name=character.name,
            character_class=character.char_class.value if hasattr(character.char_class, 'value') else str(character.char_class),
            scene_name=game_session.current_scene.name if game_session.current_scene else "the scene"
        )
        if game_session.delivery:
            game_session.delivery.master_message(
                text=f"⚔️ **{request.player_name} arrives as {character.name}!**\n*{entrance_narrative}*",
                tag="character_entrance"
            )
            game_session.delivery.session_updated(game_session)

    return PlayerResponse(
        player_id=player_id,
        player_name=request.player_name,
        character_name=request.character_name,
        connected=True,
        role=role
    )


@router.post("/{session_id}/players/with-profile", response_model=PlayerResponse)
async def join_session_with_character_profile(
    session_id: str,
    request: PlayerJoinWithProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Join a session using a saved character profile as template.

    The character profile will be used to create an in-game Character object
    that the player will control during the session.
    """
    import logging
    logger = logging.getLogger(__name__)

    from core.schemas.in_game import Character, CharacterClass, AbilityScores, Coordinate2D
    from core.entity.player import Player
    from core.entity.orchestrator import Orchestrator
    from backend.src.repositories.character_profile_repository import CharacterProfileRepository

    repository = get_session_repository(db)
    profile_repo = CharacterProfileRepository(db)

    # Validate session exists
    db_session = get_session_by_uuid_or_404(session_id, repository)

    # Check if session is active
    if db_session.status not in [SessionStatusEnum.RUNNING, SessionStatusEnum.CREATED]:
        raise HTTPException(
            status_code=400,
            detail=f"Session is not accepting players (status: {db_session.status.value})"
        )

    # Get character profile
    profile = profile_repo.get_by_id(request.profile_id, current_user.id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"Character profile {request.profile_id} not found or not owned by user"
        )

    # Check if player already joined
    existing_participants = repository.get_session_participants(session_id)
    existing_participant = next((p for p in existing_participants if p.get('user_id') == current_user.id), None)

    # Get in-memory session if running
    game_session = session_manager.get_session(session_id)

    # If participant already joined AND already has a character assigned:
    if existing_participant and existing_participant.get('character_name'):
        char_name = existing_participant.get('character_name')
        if game_session and not any(hasattr(p, 'character') and p.character.name == char_name for p in game_session.players):
            from backend.src.utils.character_converter import profile_to_character
            character = profile_to_character(profile)
            character.position = Coordinate2D(x=0.0, y=0.0)
            orchestrator = Orchestrator(
                generator=game_session.generator,
                logger=game_session.logger.getChild("player_orchestrator")
            )
            orchestrator.add_state(game_session)
            player = game_session._init_player(character, orchestrator)
            game_session.players.append(player)
            logger.info(f"[JOIN-PROFILE] Restored player {char_name} into game_session.players")

        return PlayerResponse(
            player_id=existing_participant.get('player_uuid'),
            player_name=existing_participant.get('player_name'),
            character_name=char_name,
            connected=True,
            role=existing_participant.get('role', 'player')
        )

    # Check max players for new participants
    max_players = get_session_max_players(db_session)
    if not existing_participant and len(existing_participants) >= max_players:
        raise HTTPException(
            status_code=400,
            detail=f"Session is full (max {max_players} players)"
        )

    # Determine role
    role = "owner" if db_session.owner_id == current_user.id else "player"

    if existing_participant:
        player_id = existing_participant.get('player_uuid')
        repository.update_participant_character_name(session_id, player_id, profile.name)
        logger.info(f"[JOIN-PROFILE] Updated participant {player_id} character to {profile.name}")
    else:
        player_id = str(uuid.uuid4())
        # Add player to session with character name from profile
        participant = repository.add_participant(
            session_uuid=session_id,
            player_uuid=player_id,
            player_name=request.player_name,
            user_id=current_user.id,
            character_name=profile.name,
            role=role
        )
        if not participant:
            raise HTTPException(status_code=500, detail="Failed to add player to session")

    # If game session is already running, create in-memory Player object immediately
    if game_session:
        from core.schemas.in_game import Coordinate2D
        from backend.src.utils.character_converter import profile_to_character
        character = profile_to_character(profile)
        character.position = Coordinate2D(x=0.0, y=0.0)
        character.controlled_by_player_id = player_id
        character.is_ai_controlled = True
        orchestrator = Orchestrator(
            generator=game_session.generator,
            logger=game_session.logger.getChild("player_orchestrator")
        )
        orchestrator.add_state(game_session)
        player = game_session._init_player(character, orchestrator)
        player.is_ai_controlled = True
        if not any(hasattr(p, 'character') and p.character.name == character.name for p in game_session.players):
            game_session.players.append(player)
        logger.info(f"[JOIN-PROFILE] ✓ Player {request.player_name} added to running session with character {character.name}")

        entrance_narrative = generate_character_entrance_narrative(
            generator=game_session.generator,
            session=game_session,
            character_name=character.name,
            character_class=character.char_class.value if hasattr(character.char_class, 'value') else str(character.char_class),
            scene_name=game_session.current_scene.name if game_session.current_scene else "the adventure"
        )
        if game_session.delivery:
            game_session.delivery.master_message(
                text=f"⚔️ **{request.player_name} enters the realm as {character.name}!**\n*{entrance_narrative}*",
                tag="character_entrance"
            )
            game_session.delivery.session_updated(game_session)
    else:
        # Store profile ID for later character creation when game starts
        session_data = db_session.session_data or {}
        player_profiles = session_data.get('player_profile_ids', {})
        player_profiles[player_id] = request.profile_id
        session_data['player_profile_ids'] = player_profiles
        repository.update_session_data(session_id, session_data)

    logger.info(f"Player {request.player_name} joined session {session_id} with character profile {profile.name} (ID: {request.profile_id})")

    return PlayerResponse(
        player_id=player_id,
        player_name=request.player_name,
        character_name=profile.name,
        connected=True,
        role=role
    )


@router.post("/{session_id}/players/ai-generate", response_model=PlayerResponse)
async def join_session_with_ai_character(
    session_id: str,
    request: PlayerJoinAIGeneratedRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Join a session with an AI-generated character based on a description.

    The character will be created using the session's AI generator.
    """
    import logging
    logger = logging.getLogger(__name__)

    from core.schemas.in_game import Character, Coordinate2D
    from core.entity.player import Player
    from core.entity.orchestrator import Orchestrator

    repository = get_session_repository(db)

    # Validate session exists
    db_session = get_session_by_uuid_or_404(session_id, repository)

    # Check if session is active
    if db_session.status not in [SessionStatusEnum.RUNNING, SessionStatusEnum.CREATED]:
        raise HTTPException(
            status_code=400,
            detail=f"Session is not accepting players (status: {db_session.status.value})"
        )

    # Check if player already joined
    existing_participants = repository.get_session_participants(session_id)
    existing_participant = next((p for p in existing_participants if p.get('user_id') == current_user.id), None)

    # Get or create in-memory session
    game_session = session_manager.get_session(session_id)
    if not game_session:
        raise HTTPException(status_code=400, detail="Game session not initialized. Ask the owner to start it.")

    # If participant already joined AND already has a character assigned:
    if existing_participant and existing_participant.get('character_name'):
        char_name = existing_participant.get('character_name')
        if not any(hasattr(p, 'character') and p.character.name == char_name for p in game_session.players):
            character = ProceduralGenerator.generate_character(name=char_name, prompt="")
            orchestrator = Orchestrator(
                generator=game_session.generator,
                logger=game_session.logger.getChild("player_orchestrator")
            )
            orchestrator.add_state(game_session)
            player = game_session._init_player(character, orchestrator)
            game_session.players.append(player)
            logger.info(f"[JOIN-AI] Restored player {char_name} into game_session.players")

        return PlayerResponse(
            player_id=existing_participant.get('player_uuid'),
            player_name=existing_participant.get('player_name'),
            character_name=char_name,
            connected=True,
            role=existing_participant.get('role', 'player')
        )

    # Check max players for new participants
    if not existing_participant and len(existing_participants) >= get_session_max_players(db_session):
        raise HTTPException(status_code=400, detail="Session is full")

    role = "owner" if db_session.owner_id == current_user.id else "player"

    try:
        # Generate character via AI
        session_lang = getattr(game_session, "language", "ru")
        lang_rule = "Respond strictly in RUSSIAN for character name, backstory, traits, and abilities." if session_lang == "ru" else "Respond strictly in ENGLISH for character name, backstory, traits, and abilities."
        logger.info(f"[JOIN-AI] Generating character for {request.player_name} from description: {request.character_description[:80]}... (lang={session_lang})")
        character: Character = game_session.generator.generate_one_shot(
            pydantic_model=Character,
            prompt=f"""### Language Directive
            {lang_rule}

            Create a D&D 5e character based on this description: {request.character_description}

            Requirements:
            - Name: Use a fitting fantasy name in the target language
            - Level: 1
            - Starting position: Coordinate2D(x=0.0, y=0.0)
            - backstory_summary: Based on the description provided
            - personality_traits: 2-3 traits matching the concept
            - All stats, HP, AC, inventory, abilities should be valid D&D 5e values
            """
        )
        character.position = Coordinate2D(x=0.0, y=0.0)
        logger.info(f"[JOIN-AI] ✓ AI Character generated: {character.name}")
    except Exception as e:
        session_lang = getattr(game_session, "language", "ru")
        logger.warning(f"[JOIN-AI] AI generation failed: {e}, using procedural fallback (lang={session_lang})")
        character = ProceduralGenerator.generate_character(name=None, prompt=request.character_description, language=session_lang)

    if existing_participant:
        player_id = existing_participant.get('player_uuid')
        repository.update_participant_character_name(session_id, player_id, character.name)
        logger.info(f"[JOIN-AI] Updated participant {player_id} character to {character.name}")
    else:
        player_id = str(uuid.uuid4())
        repository.add_participant(
            session_uuid=session_id,
            player_uuid=player_id,
            player_name=request.player_name,
            user_id=current_user.id,
            character_name=character.name,
            role=role
        )

    ensure_character_portrait(character, session_id)
    character.controlled_by_player_id = player_id
    character.is_ai_controlled = False

    # Create in-memory player object
    orchestrator = Orchestrator(
        generator=game_session.generator,
        logger=game_session.logger.getChild("player_orchestrator")
    )
    orchestrator.add_state(game_session)
    player = game_session._init_player(character, orchestrator)
    player.is_ai_controlled = False
    if not any(hasattr(p, 'character') and p.character.name == character.name for p in game_session.players):
        game_session.players.append(player)

    try:
        repository.update_session_data(session_id, game_session.get_session_state())
    except Exception as e:
        logger.warning(f"Error persisting session data after join: {e}")

    entrance_narrative = generate_character_entrance_narrative(
        generator=game_session.generator,
        session=game_session,
        character_name=character.name,
        character_class=character.char_class.value if hasattr(character.char_class, 'value') else str(character.char_class),
        scene_name=game_session.current_scene.name if game_session.current_scene else "the realm"
    )
    if game_session.delivery:
        game_session.delivery.master_message(
            text=f"⚔️ **{request.player_name} arrives as {character.name}!**\n*{entrance_narrative}*",
            tag="character_entrance"
        )
        game_session.delivery.session_updated(game_session)

    logger.info(f"[JOIN-AI] ✓ Player {request.player_name} joined with character {character.name} (players count: {len(game_session.players)})")

    return PlayerResponse(
        player_id=player_id,
        player_name=request.player_name,
        character_name=character.name,
        connected=True,
        role=role
    )


@router.post("/{session_id}/players/random", response_model=PlayerResponse)
async def join_session_with_random_character(
    session_id: str,
    request: PlayerJoinRandomRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Join a session with a randomly generated character.
    """
    import logging
    logger = logging.getLogger(__name__)

    from core.schemas.in_game import Character
    from core.entity.player import Player
    from core.entity.orchestrator import Orchestrator

    repository = get_session_repository(db)

    # Validate session exists
    db_session = get_session_by_uuid_or_404(session_id, repository)

    # Check if session is active
    if db_session.status not in [SessionStatusEnum.RUNNING, SessionStatusEnum.CREATED]:
        raise HTTPException(
            status_code=400,
            detail=f"Session is not accepting players (status: {db_session.status.value})"
        )

    # Check if player already joined
    existing_participants = repository.get_session_participants(session_id)
    existing_participant = next((p for p in existing_participants if p.get('user_id') == current_user.id), None)

    # Get in-memory session
    game_session = session_manager.get_session(session_id)
    if not game_session:
        raise HTTPException(status_code=400, detail="Game session not initialized. Ask the owner to start it.")

    # If participant already joined AND already has a character assigned:
    if existing_participant and existing_participant.get('character_name'):
        char_name = existing_participant.get('character_name')
        # Ensure Player instance is in game_session.players
        if not any(hasattr(p, 'character') and p.character.name == char_name for p in game_session.players):
            character = ProceduralGenerator.generate_character(name=char_name, prompt="")
            orchestrator = Orchestrator(
                generator=game_session.generator,
                logger=game_session.logger.getChild("player_orchestrator")
            )
            orchestrator.add_state(game_session)
            player = game_session._init_player(character, orchestrator)
            game_session.players.append(player)
            logger.info(f"[JOIN-RANDOM] Restored player {char_name} into game_session.players")

        return PlayerResponse(
            player_id=existing_participant.get('player_uuid'),
            player_name=existing_participant.get('player_name'),
            character_name=char_name,
            connected=True,
            role=existing_participant.get('role', 'player')
        )

    # Check max players for new participants
    if not existing_participant and len(existing_participants) >= get_session_max_players(db_session):
        raise HTTPException(status_code=400, detail="Session is full")

    role = "owner" if db_session.owner_id == current_user.id else "player"

    # Generate random character
    session_lang = getattr(game_session, "language", "ru")
    character = ProceduralGenerator.generate_character(name=None, prompt="", language=session_lang)
    logger.info(f"[JOIN-RANDOM] ✓ Random character: {character.name} for {request.player_name} (lang={session_lang})")

    if existing_participant:
        player_id = existing_participant.get('player_uuid')
        repository.update_participant_character_name(session_id, player_id, character.name)
        logger.info(f"[JOIN-RANDOM] Updated participant {player_id} character to {character.name}")
    else:
        player_id = str(uuid.uuid4())
        repository.add_participant(
            session_uuid=session_id,
            player_uuid=player_id,
            player_name=request.player_name,
            user_id=current_user.id,
            character_name=character.name,
            role=role
        )

    ensure_character_portrait(character, session_id)
    character.controlled_by_player_id = player_id
    character.is_ai_controlled = False

    # Create in-memory player object
    orchestrator = Orchestrator(
        generator=game_session.generator,
        logger=game_session.logger.getChild("player_orchestrator")
    )
    orchestrator.add_state(game_session)
    player = game_session._init_player(character, orchestrator)
    player.is_ai_controlled = False
    if not any(hasattr(p, 'character') and p.character.name == character.name for p in game_session.players):
        game_session.players.append(player)

    try:
        repository.update_session_data(session_id, game_session.get_session_state())
    except Exception as e:
        logger.warning(f"Error persisting session data after join: {e}")

    entrance_narrative = generate_character_entrance_narrative(
        generator=game_session.generator,
        session=game_session,
        character_name=character.name,
        character_class=character.char_class.value if hasattr(character.char_class, 'value') else str(character.char_class),
        scene_name=game_session.current_scene.name if game_session.current_scene else "the realm"
    )
    if game_session.delivery:
        game_session.delivery.master_message(
            text=f"⚔️ **{request.player_name} arrives as {character.name}!**\n*{entrance_narrative}*",
            tag="character_entrance"
        )
        game_session.delivery.session_updated(game_session)

    logger.info(f"[JOIN-RANDOM] In-memory players count: {len(game_session.players)}")

    return PlayerResponse(
        player_id=player_id,
        player_name=request.player_name,
        character_name=character.name,
        connected=True,
        role=role
    )


@router.get("/{session_id}/roster", response_model=List[CharacterRosterItem])
async def get_session_roster(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all characters in a session with real-time controller status:
    whether occupied by a connected human player, or under AI control (available to claim).
    """
    repository = get_session_repository(db)
    db_session = get_session_by_uuid_or_404(session_id, repository)
    game_session = ensure_session_in_memory(session_id, db)

    connected_websockets = session_manager.get_all_session_websockets(session_id)
    connected_player_ids = set(connected_websockets.keys())

    participants = repository.get_session_participants(session_id)
    participant_by_char = {p.get("character_name"): p for p in participants if p.get("character_name")}

    roster: List[CharacterRosterItem] = []

    if game_session:
        for p in game_session.players:
            if hasattr(p, 'character'):
                c = p.character
                char_name = getattr(c, 'name', 'Unknown')
                ctrl_id = getattr(c, 'controlled_by_player_id', None)

                part = None
                if ctrl_id:
                    part = next((pt for pt in participants if pt.get("player_uuid") == ctrl_id), None)
                if not part:
                    part = next((pt for pt in participants if pt.get("character_name") == char_name and pt.get("player_uuid") in connected_player_ids), None)
                if not part:
                    part = next((pt for pt in participants if pt.get("character_name") == char_name), None)

                active_pid = ctrl_id or (part.get("player_uuid") if part else None)
                is_connected = bool(active_pid and active_pid in connected_player_ids)
                is_ai = not is_connected or getattr(p, 'is_ai_controlled', False)
                controller_name = (part.get("player_name") if part else None) if is_connected else "AI Companion"

                class_val = getattr(c, 'char_class', 'Fighter')
                class_str = class_val.value if hasattr(class_val, 'value') else str(class_val)

                roster.append(CharacterRosterItem(
                    name=char_name,
                    char_class=class_str,
                    race=getattr(c, 'race', 'Human'),
                    level=getattr(c, 'level', 1),
                    current_hp=getattr(c, 'current_hp', 10),
                    max_hp=getattr(c, 'max_hp', 10),
                    armor_class=getattr(c, 'armor_class', 10),
                    image_url=getattr(c, 'image_url', None),
                    is_occupied=is_connected,
                    is_ai_controlled=is_ai,
                    controller_name=controller_name,
                    controller_id=active_pid if is_connected else None,
                    can_claim=not is_connected
                ))

        # Include NPCs in the roster so players can take over existing NPCs
        for npc in game_session.npcs:
            if hasattr(npc, 'character'):
                c = npc.character
                char_name = getattr(c, 'name', 'Unknown')
                if not any(r.name == char_name for r in roster):
                    class_val = getattr(c, 'char_class', 'Peasant')
                    class_str = class_val.value if hasattr(class_val, 'value') else str(class_val)
                    roster.append(CharacterRosterItem(
                        name=char_name,
                        char_class=class_str,
                        race=getattr(c, 'race', 'Human'),
                        level=getattr(c, 'level', 1),
                        current_hp=getattr(c, 'current_hp', 10),
                        max_hp=getattr(c, 'max_hp', 10),
                        armor_class=getattr(c, 'armor_class', 10),
                        image_url=getattr(c, 'image_url', None),
                        is_occupied=False,
                        is_ai_controlled=True,
                        controller_name="NPC (Claimable)",
                        controller_id=None,
                        can_claim=True
                    ))
    else:
        for part in participants:
            cname = part.get("character_name")
            if cname:
                pid = part.get("player_uuid")
                is_connected = bool(pid and pid in connected_player_ids)
                roster.append(CharacterRosterItem(
                    name=cname,
                    char_class="Adventurer",
                    race="Human",
                    level=1,
                    current_hp=10,
                    max_hp=10,
                    armor_class=10,
                    is_occupied=is_connected,
                    is_ai_controlled=not is_connected,
                    controller_name=part.get("player_name") if is_connected else "AI Companion",
                    controller_id=pid if is_connected else None,
                    can_claim=not is_connected
                ))

    return roster


@router.post("/{session_id}/claim-character", response_model=PlayerResponse)
async def claim_character(
    session_id: str,
    request: ClaimCharacterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Claim an existing character in a session (taking over an AI-controlled player character or existing NPC).
    """
    repository = get_session_repository(db)
    db_session = get_session_by_uuid_or_404(session_id, repository)
    game_session = ensure_session_in_memory(session_id, db)
    if not game_session:
        raise HTTPException(status_code=404, detail="Active game session could not be loaded")

    target_char_name = request.character_name.strip()
    target_player_inst = next((p for p in game_session.players if hasattr(p, 'character') and p.character.name == target_char_name), None)
    target_npc_inst = next((n for n in game_session.npcs if hasattr(n, 'character') and n.character.name == target_char_name), None) if not target_player_inst else None

    if not target_player_inst and not target_npc_inst:
        raise HTTPException(status_code=404, detail=f"Character or NPC '{target_char_name}' not found in this session")

    connected_websockets = session_manager.get_all_session_websockets(session_id)
    connected_player_ids = set(connected_websockets.keys())
    existing_participants = repository.get_session_participants(session_id)

    char_participant = next((p for p in existing_participants if p.get("character_name") == target_char_name), None)
    if char_participant and char_participant.get("player_uuid") in connected_player_ids:
        # If the character is piloted by another user, reject with 409.
        # If it's the current user themselves reconnecting, allow reclaiming smoothly!
        if char_participant.get("user_id") != current_user.id:
            raise HTTPException(status_code=409, detail=f"Character '{target_char_name}' is already piloted by an active online player")

    player_name = request.player_name or current_user.username
    role = "owner" if db_session.owner_id == current_user.id else "player"

    user_participant = next((p for p in existing_participants if p.get("user_id") == current_user.id), None)
    if user_participant:
        player_id = user_participant.get("player_uuid")
        repository.update_participant_character_name(session_id, player_id, target_char_name)
    else:
        player_id = str(uuid.uuid4())
        repository.add_participant(
            session_uuid=session_id,
            player_uuid=player_id,
            player_name=player_name,
            user_id=current_user.id,
            character_name=target_char_name,
            role=role
        )

    # Clear target_char_name from any other participant who previously held it
    for p in existing_participants:
        if p.get("character_name") == target_char_name and p.get("player_uuid") != player_id:
            repository.update_participant_character_name(session_id, p.get("player_uuid"), None)

    # If claiming an existing NPC, promote them to a full player character
    if target_npc_inst:
        c = target_npc_inst.character
        from core.schemas.in_game import Character, Coordinate2D
        promoted_char = Character(
            name=c.name,
            race=getattr(c, 'race', 'Human'),
            char_class=getattr(c, 'char_class', CharacterClass.PEASANT),
            level=getattr(c, 'level', 1),
            max_hp=c.max_hp,
            current_hp=c.current_hp,
            stats=c.stats,
            inventory=c.inventory,
            abilities=c.abilities,
            position=c.position or Coordinate2D(x=10.0, y=10.0),
            image_url=c.image_url,
            current_scene=c.current_scene or (game_session.current_scene.name if game_session.current_scene else ""),
            is_ai_controlled=False,
            controlled_by_player_id=player_id
        )
        game_session.npcs.remove(target_npc_inst)
        from core.entity.orchestrator import Orchestrator
        orch = Orchestrator(
            generator=game_session.generator,
            logger=game_session.logger.getChild("player_orchestrator")
        )
        orch.add_state(game_session)
        target_player_inst = game_session._init_player(promoted_char, orch)
        target_player_inst.is_ai_controlled = False
        game_session.players.append(target_player_inst)
        logger.info(f"[CLAIM-NPC] Promoted NPC '{target_char_name}' to human-controlled Player")
    else:
        # Transfer control of existing player character
        target_player_inst.is_ai_controlled = False
        target_player_inst.character.is_ai_controlled = False
        target_player_inst.character.controlled_by_player_id = player_id

    ensure_character_portrait(target_player_inst.character, session_id)

    try:
        repository.update_session_data(session_id, game_session.get_session_state())
    except Exception as e:
        logger.warning(f"Error persisting session data after claim: {e}")

    # Generate dramatic entrance narrative
    entrance_narrative = generate_character_entrance_narrative(
        generator=game_session.generator,
        session=game_session,
        character_name=target_char_name,
        character_class=getattr(target_player_inst.character, 'char_class', 'Hero').value if hasattr(getattr(target_player_inst.character, 'char_class', 'Hero'), 'value') else str(getattr(target_player_inst.character, 'char_class', 'Hero')),
        scene_name=game_session.current_scene.name if game_session.current_scene else "the realm"
    )

    # Broadcast system event and narrative fanfare
    from core.schemas.orchestration import Event, EventTypes
    game_session.event_pool.add_event(Event(
        event_type=EventTypes.SYSTEM,
        event_initiator="Game System",
        description=f"{player_name} took control of {target_char_name}!",
        event_subject=target_char_name
    ))

    if game_session.delivery:
        game_session.delivery.master_message(
            text=f"⚔️ **{player_name} joins the adventure as {target_char_name}!**\n*{entrance_narrative}*",
            tag="character_entrance"
        )
        game_session.delivery.session_updated(game_session)

    return PlayerResponse(
        player_id=player_id,
        player_name=player_name,
        character_name=target_char_name,
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
    participant = next((p for p in participants if p.get('player_uuid') == player_id), None)
    
    if not participant:
        raise HTTPException(status_code=404, detail="Player not found in session")
    
    # Check if current user is the player being removed or the session owner
    is_own_action = participant.get('user_id') == current_user.id
    is_owner = db_session.owner_id == current_user.id
    
    if not is_own_action and not is_owner:
        raise HTTPException(
            status_code=403,
            detail="Only the player themselves or the session owner can remove this player"
        )

    # Remove from DB
    repository.remove_participant(session_id, player_id)

    # Hand over character to AI companion if present
    game_session = session_manager.get_session(session_id)
    if game_session and participant:
        char_name = participant.get('character_name')
        for p in game_session.players:
            if hasattr(p, 'character') and (
                getattr(p.character, 'controlled_by_player_id', None) == player_id
                or (char_name and getattr(p.character, 'name', None) == char_name)
            ):
                p.is_ai_controlled = True
                p.character.is_ai_controlled = True
                p.character.controlled_by_player_id = None
                from core.schemas.orchestration import Event, EventTypes
                game_session.event_pool.add_event(Event(
                    event_type=EventTypes.SYSTEM,
                    event_initiator="Game System",
                    description=f"{p.character.name} was abandoned by their player and is now an AI companion available to claim.",
                    event_subject=p.character.name
                ))
                if game_session.delivery:
                    game_session.delivery.master_message(
                        text=f"🤖 **{p.character.name}** is now controlled by AI companion and available to claim.",
                        tag="character_abandoned"
                    )
                    game_session.delivery.session_updated(game_session)
                break

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
    participant = next((p for p in participants if p.get('player_uuid') == player_id), None)
    
    if not participant:
        raise HTTPException(status_code=404, detail="Player not found in session")
    
    # Cannot kick the owner
    if participant.get('role') == "owner":
        raise HTTPException(
            status_code=400,
            detail="Cannot kick the session owner"
        )

    # Remove from DB
    repository.remove_participant(session_id, player_id)

    # Hand over character to AI companion if present
    game_session = session_manager.get_session(session_id)
    if game_session and participant:
        char_name = participant.get('character_name')
        for p in game_session.players:
            if hasattr(p, 'character') and (
                getattr(p.character, 'controlled_by_player_id', None) == player_id
                or (char_name and getattr(p.character, 'name', None) == char_name)
            ):
                p.is_ai_controlled = True
                p.character.is_ai_controlled = True
                p.character.controlled_by_player_id = None
                from core.schemas.orchestration import Event, EventTypes
                game_session.event_pool.add_event(Event(
                    event_type=EventTypes.SYSTEM,
                    event_initiator="Game System",
                    description=f"{p.character.name} was kicked and is now an AI companion available to claim.",
                    event_subject=p.character.name
                ))
                if game_session.delivery:
                    game_session.delivery.master_message(
                        text=f"🤖 **{p.character.name}** was released to AI companion control and is open to claim.",
                        tag="character_abandoned"
                    )
                    game_session.delivery.session_updated(game_session)
                break

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
            player_id=p.get('player_uuid'),
            player_name=p.get('player_name'),
            character_name=p.get('character_name'),
            connected=p.get('is_connected'),
            role=p.get('role'),
            is_ready=session_ready_status.get(p.get('user_id'), False) if p.get('user_id') else False
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

    # Try to get or restore active game session
    game_session = ensure_session_in_memory(session_id, db)

    if not game_session:
        raise HTTPException(
            status_code=404,
            detail="Session could not be loaded or restored"
        )

    try:
        # Get DB participants for complete player list
        db_participants = repository.get_session_participants(session_id)
        db_player_names = {p.get('player_name') for p in db_participants}
        
        # Build players data from game engine - use model_dump() for complete data
        players_data = []
        for player in game_session.players:
            if hasattr(player, 'character'):
                char = player.character
                # Use model_dump() to get ALL fields including inventory, conditions, position, resources
                players_data.append(char.model_dump(mode='json'))
            else:
                # Player object without character attribute
                players_data.append(player.model_dump(mode='json') if hasattr(player, 'model_dump') else {})

        # Add DB participants who don't have characters yet (waiting room players)
        engine_player_names = {p.get('name') for p in players_data if p.get('name')}
        for participant in db_participants:
            if participant.get('player_name') not in engine_player_names:
                # Player joined but doesn't have a character yet
                players_data.append({
                    "name": participant.get('player_name'),
                    "race": "Human",
                    "char_class": "Adventurer",
                    "level": 1,
                    "current_hp": 10,
                    "max_hp": 10,
                    "temp_hp": 0,
                    "armor_class": 10,
                    "speed": 30,
                    "proficiency_bonus": 2,
                    "initiative_bonus": 0,
                    "is_alive": True,
                    "stats": {
                        "strength": 10, "dexterity": 10, "constitution": 10,
                        "intelligence": 10, "wisdom": 10, "charisma": 10,
                    },
                    "inventory": [],
                    "active_conditions_list": [],
                    "active_conditions": "",
                    "resources": {},
                    "position": {"x": 0, "y": 0},
                    "abilities": [],
                    "backstory_summary": "",
                    "personality_traits": [],
                })

        # Build NPCs data - use model_dump() for complete data
        npcs_data = []
        for npc in game_session.npcs:
            if hasattr(npc, 'character'):
                char = npc.character
                # Use model_dump() to get ALL fields
                npcs_data.append(char.model_dump(mode='json'))
            else:
                npcs_data.append(npc.model_dump(mode='json') if hasattr(npc, 'model_dump') else {})

        # Build scene data (ensuring scene exists)
        if not getattr(game_session, "current_scene", None):
            scene_prompt = getattr(db_session, 'session_name', None) or "A tactical battle encounter in an ancient stone chamber."
            game_session.current_scene = procedural_gen.generate_scene(scene_prompt)
            game_session.all_locations[game_session.current_scene.name] = game_session.current_scene
            game_session.current_location_name = game_session.current_scene.name
            ensure_scene_battlemap(game_session.current_scene)

        scene = game_session.current_scene
        ensure_scene_battlemap(scene)
        scene_data = scene.model_dump(mode='json') if hasattr(scene, 'model_dump') else {}

        # Build turn queue data
        turn_queue_data = []
        if hasattr(game_session, 'turn_queue') and game_session.turn_queue:
            for char_obj, time_added, next_turn in game_session.turn_queue:
                char_name = "Unknown"
                char_type = "unknown"
                if hasattr(char_obj, 'character'):
                    char_name = getattr(char_obj.character, 'name', 'Unknown')
                    char_type = "player" if hasattr(char_obj, '_init_player') else "npc"
                elif hasattr(char_obj, 'name'):
                    char_name = char_obj.name
                    char_type = "npc"

                turn_queue_data.append({
                    "character_name": char_name,
                    "type": char_type,
                    "next_turn": next_turn,
                })

        # Build participant data with player_id mapping
        db_participants = repository.get_session_participants(session_id)
        participant_mapping = {}
        for participant in db_participants:
            player_id = participant.get('player_uuid')
            player_name = participant.get('player_name')
            character_name = participant.get('character_name')
            if player_id:
                participant_mapping[player_name] = {
                    'player_id': player_id,
                    'character_name': character_name
                }

        # Return complete game info with FULL character data and plot
        return {
            "session_id": game_session.session_id if hasattr(game_session, 'session_id') else session_id,
            "session_name": getattr(game_session, 'session_name', 'Unknown'),
            "game_mode": game_session.game_mode.value if hasattr(game_session, 'game_mode') else "STORY",
            "language": getattr(game_session, "language", "ru"),
            "status": game_session.status.value if hasattr(game_session, 'status') else "running",
            "player_count": len(game_session.players),
            "npc_count": len(game_session.npcs),
            "max_players": 5,
            "players": players_data,
            "npcs": npcs_data,
            "scene": scene_data,
            "current_scene": scene_data,
            "plot": game_session.plot.model_dump(mode='json') if hasattr(game_session.plot, 'model_dump') else {},
            "current_chapter": game_session.plot.current_chapter.model_dump(mode='json') if game_session.plot and game_session.plot.current_chapter else None,
            "turn_queue": turn_queue_data,
            "messages": [
                {"sender_name": m.sender_name, "text": m.text, "type": getattr(m, 'tag', 'narration') or "narration", "timestamp": ""}
                for m in game_session.messages[-20:]
            ] if hasattr(game_session, 'messages') else [],
            # Include player mapping so frontend can identify which character belongs to which player_id
            "player_mapping": participant_mapping,
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
    player_count = len([p for p in participants if p.get('is_connected')])
    
    # Get ready status for this session (tracked by user_id)
    session_ready_status = waiting_room_ready_status.get(session_id, {})
    
    players = []
    for p in participants:
        # Get ready status by user_id (None for guest users without account)
        user_id_key = p.get('user_id') if p.get('user_id') is not None else hash(p.get('player_uuid'))
        is_ready = session_ready_status.get(user_id_key, False)
        players.append(PlayerResponse(
            player_id=p.get('player_uuid'),
            player_name=p.get('player_name'),
            character_name=p.get('character_name'),
            connected=p.get('is_connected'),
            role=p.get('role'),
            is_ready=is_ready
        ))

    return WaitingRoomResponse(
        session_id=db_session.session_uuid,
        session_name=db_session.session_name,
        game_mode=db_session.game_mode.value,
        player_count=player_count,
        max_players=get_session_max_players(db_session),
        status=db_session.status.value,
        description=get_session_description(db_session),
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
    participant = next((p for p in participants if p.get('user_id') == current_user.id), None)
    
    if not participant:
        raise HTTPException(
            status_code=404,
            detail="Player not found in session. Please join the session first."
        )
    
    # Check if player is already connected (prevent double connection)
    if participant.get('is_connected'):
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
        "player_name": participant.get('player_name'),
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
    connected_players = [p for p in participants if p.get('is_connected')]
    
    if not connected_players:
        raise HTTPException(
            status_code=400,
            detail="No connected players. Wait for players to join before starting."
        )
    
    # Check if ALL connected players are ready
    session_ready_status = waiting_room_ready_status.get(session_id, {})
    
    not_ready_players = []
    for player in connected_players:
        user_id_key = player.get('user_id') if player.get('user_id') is not None else hash(player.get('player_uuid'))
        is_ready = session_ready_status.get(user_id_key, False)
        if not is_ready:
            not_ready_players.append(player.get('player_name'))
    
    if not_ready_players:
        raise HTTPException(
            status_code=400,
            detail=f"Waiting for players to ready: {', '.join(not_ready_players)}"
        )

    logger.info(f"[START-GAME] Session {session_id} - Starting from waiting room with {len(connected_players)} ready players")

    # Get or create game session
    game_session = session_manager.get_session(session_id)

    if not game_session:
        # Initialize the game session from DB
        logger.warning(f"[START-GAME] Session {session_id} found in DB but not in memory. Initializing...")

        try:
            from backend.src.game.session_factory import SessionConfig
            config = SessionConfig(
                session_name=db_session.session_name,
                game_mode=db_session.game_mode.value,
                max_players=get_session_max_players(db_session),
                description=get_session_description(db_session),
                guide=get_session_guide(db_session),
                gemini_model=get_session_gemini_model(db_session) or "gemini-3.5-flash-lite"
            )
            game_session = session_factory.create_session(config, session_id=session_id)
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
        scene_description = get_session_guide(db_session) or "A dimly lit tavern with worn wooden tables and the smell of ale."

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
        ensure_scene_battlemap(scene)
        game_session.current_scene = scene

        # Update DB status
        repository.update_session_scene(session_id, scene.name, owner_id=current_user.id)
        repository.update_session_status(session_id, "running", owner_id=current_user.id)

        # Get player profile IDs mapping (if players joined with profiles)
        session_data = db_session.session_data or {}
        player_profile_ids = session_data.get('player_profile_ids', {})
        if player_profile_ids:
            logger.info(f"[START-GAME] Found {len(player_profile_ids)} player profile mappings")

        # Import profile converter
        from backend.src.utils.character_converter import profile_to_character
        from backend.src.repositories.character_profile_repository import CharacterProfileRepository
        profile_repo = CharacterProfileRepository(db)

        # Initialize player characters from ALL connected players
        for i, participant in enumerate(connected_players):
            player_id = participant.get('player_uuid')
            profile_id = player_profile_ids.get(player_id)
            character = None

            # Check if player has a saved profile
            if profile_id:
                try:
                    profile = profile_repo.get_by_id(profile_id, current_user.id)
                    if profile:
                        character = profile_to_character(profile, position=Coordinate2D(x=float(i*2), y=float(i*2)))
                        logger.info(f"[START-GAME] ✓ Created character from profile: {character.name}")
                except Exception as e:
                    logger.warning(f"[START-GAME] Failed to convert profile, using default: {e}")

            # Fallback to default character if no profile or conversion failed
            if not character:
                character = Character(
                    name=participant.get('character_name') or participant.get('player_name'),
                    race="Human",
                    char_class=CharacterClass.FIGHTER,
                    level=1,
                    backstory_summary=f"{participant.get('player_name')}'s character",
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
            description=get_session_description(db_session),
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
    game_session = session_manager.get_session(session_id)
    
    if not game_session:
        # Initialize from DB
        try:
            from backend.src.game.session_factory import SessionConfig
            config = SessionConfig(
                session_name=db_session.session_name,
                game_mode=db_session.game_mode.value,
                max_players=get_session_max_players(db_session),
                description=get_session_description(db_session),
                guide=get_session_guide(db_session),
                gemini_model=get_session_gemini_model(db_session) or "gemini-3.5-flash-lite"
            )
            game_session = session_factory.create_session(config, session_id=session_id)
            logger.info(f"[AI-INIT] Session {session_id} created")
        except Exception as e:
            logger.error(f"[AI-INIT] Failed to create session: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to create session: {str(e)}"
            )
    
    try:
        # Verify delivery is available
        if not hasattr(game_session, 'delivery') or not game_session.delivery:
            raise HTTPException(status_code=503, detail="Game delivery not available")
        
        # Prepare prompts
        scene_prompt = request.scene_prompt or request.wishes or "A mysterious adventure begins..."
        character_prompts = request.character_prompts or []
        npc_prompts = request.npc_prompts or []

        # Initialize scene and characters through session factory methods
        from backend.src.game.session_factory import session_factory
        
        # Generate scene
        scene = session_factory.init_scene(game_session, scene_prompt)
        
        # Generate characters
        for i, char_prompt in enumerate(character_prompts):
            player_name = f"Player_{i+1}"
            player_id = str(uuid.uuid4())
            session_factory.init_player(game_session, char_prompt, player_name, player_id)
        
        # Generate NPCs
        for npc_prompt in npc_prompts:
            session_factory.init_npc(game_session, npc_prompt)
        
        # Update DB status
        repository.update_session_status(session_id, "running", owner_id=current_user.id)

        # Send welcome message through delivery
        welcome_msg = f"Welcome to {scene.name}! {scene.description}"
        game_session.delivery.master_message(welcome_msg)
        game_session.delivery.session_updated(game_session)

        return AIInitializeResponse(
            success=True,
            session_id=session_id,
            scene_description=scene.description,
            characters_count=len(game_session.players),
            npcs_count=len(game_session.npcs),
            message=f"Session initialized with {len(game_session.players)} players and {len(game_session.npcs)} NPCs"
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
    import logging
    from backend.src.logging.request_tracing import RequestTracer, get_trace_id
    from backend.src.api.middleware.logging import Colors

    logger = logging.getLogger(__name__)
    trace_id = get_trace_id()

    # Log request tracing
    logger.debug(
        f"PLAYER ACTION ENDPOINT | "
        f"Trace ID: {trace_id} | Session ID: {session_id} | "
        f"User: {current_user.username} (ID: {current_user.id}) | "
        f"Character: {request.character_name} | "
        f"Action: {request.action[:100]}... | "
        f"Journey: Frontend → Backend → Core Engine → AI Processing"
    )

    # Get active game session (restore from DB if needed)
    game_session = ensure_session_in_memory(session_id, db)

    if not game_session:
        logger.error(f"Game session not found: {session_id}")
        raise HTTPException(
            status_code=404,
            detail="Game session not found or not initialized"
        )

    # Launch game loop if not already running
    if session_id not in _active_game_loops:
        logger.info(f"[ACTION] Auto-launching game loop for session {session_id}")
        asyncio.create_task(_run_game_loop(session_id, game_session))
        _active_game_loops.add(session_id)

    try:
        # Enqueue the action for the game loop to pick up via delivery.player_request()
        from core.interface.delivery import Request
        import time as _time
        _req = Request(
            player_id=request.character_name,
            request_text=request.action,
            timestamp=_time.time(),
            character=None,
        )
        game_session.delivery.put_request(_req)
        game_session.logger.info(f"[ACTION] Queued action for {request.character_name}: {request.action[:80]}...")

        result = {
            "success": True,
            "dm_response": "",  # Will be delivered via master_message broadcast
            "events": [],
            "game_state": {
                "scene": game_session.current_scene.name if game_session.current_scene else None,
                "players": len(game_session.players),
                "npcs": len(game_session.npcs),
            }
        }

        game_session.delivery.session_updated(game_session)

        # Save game state to database after each action
        try:
            repository = get_session_repository(db)
            session_state = game_session.get_session_state()
            repository.update_session_data(session_id, session_state)
            game_session.logger.debug(f"[ACTION] ✓ Game state saved to database")
        except Exception as e:
            game_session.logger.warning(f"[ACTION] Failed to save game state: {e}")

        # Log response
        logger.debug(
            f"RESPONSE READY | "
            f"Trace ID: {trace_id} | Session: {session_id} | "
            f"Status: SUCCESS | Journey: Backend → Frontend (SENDING)"
        )

        return PlayerActionResponse(
            success=result['success'],
            dm_response=result['dm_response'],
            events=result.get('events', []),
            game_state=result.get('game_state', {}),
            error=None
        )

    except Exception as e:
        logger.error(
            f"PLAYER ACTION ERROR | "
            f"Trace ID: {trace_id} | Session: {session_id} | "
            f"Error: {str(e)} | Journey: Backend → Frontend (ERROR)",
            exc_info=True
        )
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
    # Get active game session (restore from DB if needed)
    game_session = ensure_session_in_memory(session_id, db)
    
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
        # Get game state directly from session
        session = game_session
        
        state = {
            'scene': {
                'name': session.current_scene.name if session.current_scene else None,
                'description': session.current_scene.description if session.current_scene else None,
            } if session.current_scene else None,
            'players': [
                {
                    'name': p.character.name if hasattr(p, 'character') else str(p),
                    'hp': p.character.current_hp if hasattr(p, 'character') else 0,
                    'max_hp': p.character.max_hp if hasattr(p, 'character') else 0,
                }
                for p in session.players
            ],
            'npcs': [
                {
                    'name': n.character.name if hasattr(n, 'character') else str(n),
                    'hp': n.character.current_hp if hasattr(n, 'character') else 0,
                    'current_scene': n.character.current_scene if hasattr(n, 'character') else None,
                }
                for n in session.npcs
            ],
            'messages': [
                {
                    'sender': msg.sender_name,
                    'text': msg.text,
                    'tag': getattr(msg, 'tag', 'narration'),
                }
                for msg in session.messages
            ],
            'turn_queue': [
                {
                    'entity_id': str(entity.id if hasattr(entity, 'id') else entity),
                    'entity_type': 'player' if hasattr(entity, 'character') else 'npc'
                }
                for entity, _, _ in session.turn_queue
            ] if session.turn_queue else []
        }

        plot_dict = session.plot.model_dump(mode='json') if hasattr(session.plot, 'model_dump') else {}
        current_ch = session.plot.current_chapter.model_dump(mode='json') if session.plot and session.plot.current_chapter else None

        return SessionStateResponse(
            success=True,
            scene=state.get('scene'),
            players=state.get('players', []),
            npcs=state.get('npcs', []),
            messages=state.get('messages', []),
            turn_queue=state.get('turn_queue', []),
            plot=plot_dict,
            current_chapter=current_ch
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


# === Tactical Battle Map Regeneration Endpoint ===

class RegenerateMapRequest(BaseModel):
    prompt_override: Optional[str] = None
    terrain_type: Optional[str] = None


class RegenerateMapResponse(BaseModel):
    status: str = "ok"
    battlemap_image_url: str
    cached: bool = False


@router.post("/{session_id}/scene/regenerate-map", response_model=RegenerateMapResponse)
async def regenerate_scene_map(
    session_id: str,
    request: Optional[RegenerateMapRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Regenerate or retrieve top-down tactical battle map for the active session's scene.
    Uses image_gen_service, updates current_scene.battlemap_image_url,
    persists updated session state to the database, and returns the asset URL.
    """
    import logging
    logger = logging.getLogger(__name__)

    repository = get_session_repository(db)
    db_session = get_session_by_uuid_or_404(session_id, repository)

    game_session = session_manager.get_session(session_id)
    if not game_session:
        # Attempt to restore or create session
        try:
            config = SessionConfig(
                session_name=db_session.session_name,
                game_mode=db_session.game_mode.value,
                max_players=get_session_max_players(db_session),
                description=get_session_description(db_session),
                guide=get_session_guide(db_session),
                gemini_model=get_session_gemini_model(db_session) or "gemini-3.5-flash-lite",
            )
            game_session = session_factory.create_session(config, session_id=session_id)
            if db_session.session_data and db_session.session_data.get("current_scene"):
                game_session.restore_session_from_serialized(db_session.session_data)
        except Exception as e:
            logger.warning(f"[REGEN-MAP] Could not restore session from DB: {e}")

    if not game_session:
        raise HTTPException(status_code=400, detail="Session could not be initialized")

    if not getattr(game_session, "current_scene", None):
        guide = get_session_guide(db_session) or "A tactical battle encounter in a stone dungeon."
        game_session.current_scene = ProceduralGenerator.generate_scene(guide)

    scene = game_session.current_scene
    dim_x = int(scene.dimensions.x) if hasattr(scene, "dimensions") and hasattr(scene.dimensions, "x") else 20
    dim_y = int(scene.dimensions.y) if hasattr(scene, "dimensions") and hasattr(scene.dimensions, "y") else 20
    obstacles = [obj.name for obj in getattr(scene, "objects", []) if getattr(obj, "name", None)]

    from backend.src.services.image_gen_service import image_gen_service
    prompt_override = request.prompt_override if request else None
    terrain_type = request.terrain_type if request else None

    if prompt_override:
        result = await image_gen_service.generate_for_entity(
            entity_type="battlemap",
            entity_id=f"{session_id}_{scene.name}",
            description=prompt_override,
            prompt_override=prompt_override,
        )
    else:
        result = await image_gen_service.generate_battlemap(
            scene_id=f"{session_id}_{scene.name}",
            name=scene.name,
            description=scene.description,
            dimensions=(dim_x, dim_y),
            terrain_type=terrain_type,
            obstacles=obstacles if obstacles else None,
        )

    map_url = result.image_url
    scene.battlemap_image_url = map_url
    if hasattr(scene, "background_image_url"):
        scene.background_image_url = map_url

    # Persist in DB
    session_data = dict(db_session.session_data or {})
    if hasattr(game_session, "get_session_state"):
        session_data.update(game_session.get_session_state())
    elif hasattr(scene, "model_dump"):
        session_data["current_scene"] = scene.model_dump(mode="json")
    elif hasattr(scene, "dict"):
        session_data["current_scene"] = scene.dict()

    session_data["battlemap_image_url"] = map_url
    if "current_scene" in session_data and isinstance(session_data["current_scene"], dict):
        session_data["current_scene"]["battlemap_image_url"] = map_url
        session_data["current_scene"]["background_image_url"] = map_url

    db_session.session_data = session_data
    flag_modified(db_session, "session_data")
    db_session.updated_at = datetime.now()
    db.commit()
    db.refresh(db_session)

    # Broadcast WebSocket update if delivery available
    if hasattr(game_session, "delivery") and game_session.delivery:
        try:
            game_session.delivery.session_updated(game_session)
        except Exception as e:
            logger.debug(f"[REGEN-MAP] Broadcast error: {e}")

    return RegenerateMapResponse(
        status="ok",
        battlemap_image_url=map_url,
        cached=result.cached,
    )


class TransitionLocationRequest(BaseModel):
    location_name: str = Field(..., description="Name of the target location to transition to")
    description: Optional[str] = Field(None, description="Optional description of the location if newly discovered")


class TransitionLocationResponse(BaseModel):
    status: str
    current_location_name: str
    is_new_location: bool
    all_locations: List[str]
    connected_locations: List[str]
    scene: Dict[str, Any]
    npcs_present: List[str]


@router.post("/{session_id}/transition-location", response_model=TransitionLocationResponse)
async def transition_location(
    session_id: str,
    payload: TransitionLocationRequest,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Transition the party to a new or previously visited location in the session's location graph.
    - If previously visited: loads existing scene and objects.
    - If unvisited: dynamically generates new scene, objects, pins new thematic NPCs, and connects edge in graph.
    - Updates all player characters to the new scene.
    - Broadcasts location change narrative and session update to all connected clients.
    """
    repository = get_session_repository(db)
    db_session = get_session_by_uuid_or_404(session_id, repository)

    game_session = session_manager.get_session(session_id)
    if not game_session:
        try:
            config = SessionConfig(
                session_name=db_session.session_name,
                game_mode=db_session.game_mode.value,
                max_players=get_session_max_players(db_session),
                description=get_session_description(db_session),
                guide=get_session_guide(db_session),
                gemini_model=get_session_gemini_model(db_session) or "gemini-3.5-flash-lite",
            )
            game_session = session_factory.create_session(config, session_id=session_id)
            if db_session.session_data:
                game_session.restore_session_from_serialized(db_session.session_data)
        except Exception as e:
            logger.warning(f"[TRANSITION-LOC] Could not restore session from DB: {e}")

    if not game_session:
        raise HTTPException(status_code=400, detail="Session could not be initialized")

    is_new = payload.location_name not in game_session.all_locations
    scene = game_session.transition_to_location(payload.location_name, description=payload.description)

    # Persist updated session state in DB
    session_data = dict(db_session.session_data or {})
    if hasattr(game_session, "get_session_state"):
        session_data.update(game_session.get_session_state())
    db_session.session_data = session_data
    flag_modified(db_session, "session_data")
    db_session.updated_at = datetime.now()
    db.commit()
    db.refresh(db_session)

    # Get present NPCs
    npcs_here = [
        npc.character.name for npc in game_session.npcs
        if getattr(npc.character, "current_scene", None) == game_session.current_location_name
    ]

    scene_dict = scene.dict() if hasattr(scene, "dict") else (scene.model_dump(mode="json") if hasattr(scene, "model_dump") else {})

    return TransitionLocationResponse(
        status="ok",
        current_location_name=game_session.current_location_name,
        is_new_location=is_new,
        all_locations=game_session.get_all_locations(),
        connected_locations=list(game_session.get_connected_locations(game_session.current_location_name)),
        scene=scene_dict,
        npcs_present=npcs_here,
    )

