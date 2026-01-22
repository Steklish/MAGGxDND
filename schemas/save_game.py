from typing import List
from pydantic import BaseModel
from schemas.in_game import Character, NPCCharacter, SceneNode

class SaveGameData(BaseModel):
    player_characters: List[Character]
    npcs: List[NPCCharacter]
    current_scene: SceneNode