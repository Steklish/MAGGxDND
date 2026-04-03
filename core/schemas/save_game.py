from typing import List, Dict, Set, Union
from pydantic import BaseModel
from core.schemas.in_game import Character, NPCCharacter, SceneNode

class SaveGameData(BaseModel):
    player_characters: List[Character]
    npcs: List[NPCCharacter]
    current_scene: SceneNode
    # Location graph data - using Union to allow both Set and List for flexibility
    location_graph: Dict[str, Union[Set[str], List[str]]] = {}
    all_locations: Dict[str, SceneNode] = {}
    current_location_name: str | None = None