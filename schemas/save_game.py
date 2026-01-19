from typing import List
from pydantic import BaseModel
from schemas.in_game import Character, SceneNode

class SaveGameData(BaseModel):
    player_characters: List[Character]
    npcs: List[Character]
    current_scene: SceneNode