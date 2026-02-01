from game.manipulators.base_manipulation import BaseManipulation
from utils.dice_utils import roll
from skls_generator.generator import Generator
from schemas.orchestration import Event, EventTypes
from thefuzz import process
from typing import Any, List, TYPE_CHECKING
from logging import Logger
from schemas.in_game import Character, UnifiedObject
from utils.spatial_utils import calculate_spatial_distances

if TYPE_CHECKING:
    from game.engine import Session

class AttackManipulation(BaseManipulation):
    """Handles attack-related manipulations, including damage calculation and attack resolution."""
    
    event_types_binded = [
        EventTypes.CHARACTER_ATTACK,
        EventTypes.CHARACTER_MELEE_ATTACK,
        EventTypes.CHARACTER_RANGED_ATTACK
    ]

    def __init__(self, generator : Generator, logger : Logger, session : 'Session') -> None:
        super().__init__(generator, logger)
        self.state = session

    def manipulate(self, attacker: Character, event: Event) -> List[Event]:
        """Process an attack event, calculate damage, and apply effects."""
        if event.event_type in [EventTypes.CHARACTER_ATTACK, 
                               EventTypes.CHARACTER_MELEE_ATTACK, 
                               EventTypes.CHARACTER_RANGED_ATTACK]:
            return self._handle_attack(attacker, event)
        else:
            return []

    def _handle_attack(self, attacker: Character, event: Event) -> List[Event]:
        """Handle the complete attack sequence: hit determination, damage calculation, and effect application."""
        
        # Extract defender from the event
        defender_name = event.event_subject
        
        # Find the defender character
        defender = None

        # Attempt to retrieve defender from event params if available, otherwise search
        if 'defender' in event.event_params and isinstance(event.event_params['defender'], Character):
            defender = event.event_params['defender']
        else:
            # Fallback to searching within the current scene (requires scene context in entity)
            if attacker.current_scene:
                scene_characters = [char for char in self.state.get_scene_characters(attacker.current_scene) if char.name == defender_name]
                defender = scene_characters[0] if scene_characters else None

        if not defender:
            self.logger.error(f"Could not find defender ({defender_name})")
            return []

        # Determine weapon/item used for the attack
        weapon = self._find_weapon(attacker, event)
        
        # Calculate attack success and damage
        attack_result = self._calculate_attack_outcome(attacker, defender, weapon, event)
        
        # Apply damage to defender
        damage_applied = self._apply_damage(defender, attack_result['damage'])
        
        # Create action result event
        action_result = Event(
            event_type=EventTypes.ACTION_RESULT,
            event_initiator=attacker.name,
            event_subject=defender.name,
            event_target="attack",
            description=f"{attacker.name} attacked {defender.name} with {weapon.name if weapon else 'unarmed strike'} and dealt {attack_result['damage']} damage. Defender HP: {defender.current_hp}/{defender.max_hp}"
        )
        
        result_events = [action_result]
        
        # Check if defender died
        if defender.current_hp <= 0:
            death_event = Event(
                event_type=EventTypes.CHARACTER_DEATH,
                event_initiator=attacker.name,
                event_subject=defender.name,
                event_target=event.event_target,
                description=f"{defender.name} has died due to attack from {attacker.name}. Cause: {event.description}"
            )
            result_events.append(death_event)
        
        return result_events

    def _find_weapon(self, character: Character, event: Event) -> UnifiedObject | None:
        """Find the weapon used in the attack from character's inventory or equipment."""
        # Look for weapon in inventory
        for item in character.inventory:
            if item.damage_dice:  # Assume items with damage_dice are weapons
                return item
        return None

    def _calculate_attack_outcome(self, attacker: Character, defender: Character, weapon: UnifiedObject | None, event: Event) -> dict:
        """Calculate if attack hits and how much damage is dealt."""
        # For simplicity, we'll use a basic system
        # In a full implementation, this would include attack rolls, AC checks, etc.
        
        # Calculate base damage
        damage_dice = weapon.damage_dice if weapon else "1d4"  # Unarmed strike
        damage = roll(damage_dice)
        
        # Apply strength modifier for melee or dex for ranged (simplified)
        if weapon and 'bow' in weapon.name.lower() or 'crossbow' in weapon.name.lower() or 'thrown' in event.description.lower():
            # Ranged attack - use dexterity
            damage += attacker.stats.dexterity // 2  # Simplified modifier calculation
        else:
            # Melee attack - use strength
            damage += attacker.stats.strength // 2  # Simplified modifier calculation
            
        # Ensure minimum damage of 1
        damage = max(1, damage)
        
        return {
            'hit': True,  # For now, assume all attacks hit (in a full implementation, this would involve rolls)
            'damage': damage
        }

    def _apply_damage(self, defender: Character, damage: int) -> int:
        """Apply damage to defender and return actual damage applied."""
        # Apply damage to current HP, ensuring it doesn't go below 0
        old_hp = defender.current_hp
        defender.current_hp = max(0, defender.current_hp - damage)
        actual_damage = old_hp - defender.current_hp
        
        self.logger.info(f"{defender.name} took {actual_damage} damage. HP: {defender.current_hp}/{defender.max_hp}")
        
        return actual_damage