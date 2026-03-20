import sys
from typing import TYPE_CHECKING, Any

# This is a temporary solution.
# In a real-world scenario, you'd have a better way to manage paths,
# probably by making the project a proper Python package.
sys.path.append(r"D:\Lectures\SDLC\MAGGxDND")

from schemas.in_game import Character, SceneNode, UnifiedObject
from pydantic import BaseModel

if TYPE_CHECKING:
    from game.engine import Session

def serialize_model(model: BaseModel) -> dict:
    """Safely serializes a Pydantic model, excluding sensitive fields."""
    # Use .model_dump() which is the Pydantic v2 equivalent of .dict()
    # It handles nested models automatically.
    # The `exclude` parameter is crucial for security.
    return model.model_dump(exclude={"gm_secret", "gm_secrets"})

def serialize_scene(scene: SceneNode) -> dict:
    """
    Serializes a SceneNode object, ensuring that GM-only information is excluded.
    """
    if not scene:
        return None
    
    # CRITICAL: Exclude gm_secret fields to prevent leaking to clients.
    scene_dict = scene.model_dump(exclude={"gm_secret", "gm_secrets"})
    
    # Recursively serialize objects within the scene
    if "objects" in scene_dict and scene_dict["objects"]:
        scene_dict["objects"] = [
            serialize_model(obj) for obj in scene.objects
        ]
        
    return scene_dict

def serialize_session(session: "Session") -> dict[str, Any]:
    """
    Converts the entire Session object into a JSON-serializable dictionary
    that matches the frontend's expected data structure.
    """
    if not session:
        return {}

    # Serialize players and NPCs
    players = [serialize_model(p.character) for p in session.players]
    npcs = [serialize_model(n.character) for n in session.npcs]

    # Serialize the turn queue
    turn_queue = []
    if session.turn_queue:
        # Sort by next_turn to determine the correct order
        sorted_queue = sorted(session.turn_queue, key=lambda x: x[2])
        for i, (char, _, next_turn) in enumerate(sorted_queue):
            turn_queue.append({
                "character_name": char.name,
                "character_type": "player" if char.name in [p.character.name for p in session.players] else "npc",
                "next_turn": next_turn,
                "is_next": i == 0, # The first character in the sorted list is the active one
            })

    # Assemble the final payload
    session_data = {
        "session_name": session.session_name_proper,
        "game_mode": session.game_mode.value,
        "turn_time": session.turn_time,
        "current_location_name": session.current_location_name,
        "spatial_enabled": session.spatial_enabled,
        
        # These are part of the UI's `SceneUpdate` message, so we include them here
        # for the initial state synchronization.
        "scene": serialize_scene(session.current_scene),
        "players": players,
        "npcs": npcs,
        "objects": [serialize_scene(obj) for obj in session.current_scene.objects] if session.current_scene else [],

        # The UI also needs a separate turn queue update, but we can include it
        # in the main session object for initial load.
        "turn_queue": turn_queue,
        
        # Messages are not explicitly in the spec's SessionUpdate, but are useful
        "messages": [msg.model_dump() for msg in session.messages],
    }
    
    return session_data
