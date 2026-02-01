"""
Utility functions for the game system.
"""

from schemas.orchestration import Event
from game.engine import Session
from typing import List


def calculate_spatial_distances(state: Session, event: Event) -> str:
    """
    Calculate spatial distances between objects mentioned in the event.

    Args:
        state: The current session state
        event: The event to analyze for spatial relationships

    Returns:
        A string containing formatted spatial distance information
    """
    if not hasattr(state, 'spatial_enabled') or not state.spatial_enabled:
        return "Spatial system is disabled."

    # Get all characters that might be involved in the event
    character_pool = [n.character for n in state.players] + [n.character for n in state.npcs]

    # Identify characters mentioned in the event
    mentioned_chars = []
    if event.event_initiator:
        for char in character_pool:
            if event.event_initiator.lower() in char.name.lower() or char.name.lower() in event.event_initiator.lower():
                mentioned_chars.append(char)
    if event.event_subject:
        for char in character_pool:
            if event.event_subject.lower() in char.name.lower() or char.name.lower() in event.event_subject.lower():
                if char not in mentioned_chars:
                    mentioned_chars.append(char)
    if event.event_target:
        for char in character_pool:
            if event.event_target.lower() in char.name.lower() or char.name.lower() in event.event_target.lower():
                if char not in mentioned_chars:
                    mentioned_chars.append(char)

    # Calculate distances between all pairs of mentioned characters
    distances = []
    for i, char1 in enumerate(mentioned_chars):
        for j, char2 in enumerate(mentioned_chars):
            if i < j:  # Avoid duplicate calculations
                distance = state.calculate_distance_3d(char1.position, char2.position)
                distances.append(f"Distance between {char1.name} and {char2.name}: {distance:.2f} {state.current_scene.scale_unit if state.current_scene else 'units'}")

    if distances:
        return "Spatial distances:\n" + "\n".join(distances)
    else:
        return "No relevant characters found for distance calculation."