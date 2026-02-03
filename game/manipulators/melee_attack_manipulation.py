from typing import TYPE_CHECKING, List, Any

from pydantic import BaseModel, Field
from utils.dice_utils import roll_dice

if TYPE_CHECKING:
    from game.engine import Session
from game.manipulators.base_manipulation import BaseManipulation
from schemas.orchestration import Event, EventTypes
from schemas.in_game import Character, Condition


class MeleeAttackBreakdown(BaseModel):
    """Breakdown of a melee attack action."""
    target_name: str = Field(..., description="Name of the character being attacked")
    damage_dealt: str = Field(..., description="Amount of damage dealt using dnd dice notation (e.g., '1d8+3')")
    attack_success: bool = Field(..., description="Whether the attack was successful")
    attack_description: str = Field(..., description="Description of the attack action")
    conditions_applied: List[Condition] = Field(..., description="A list of conditions that an attack may cause")
 
class MeleeAttackManipulator(BaseManipulation):
    event_types_binded = [
        EventTypes.CHARACTER_MELEE_ATTACK
    ]

    def __init__(self, state: 'Session'):
        super().__init__(state)
        self.logger.info("MeleeAttackManipulator initialized")

    def manipulate(self, event: Event) -> List[Event]:
        """
        Process a melee attack event and apply the results to the game state.
        """
        self.logger.info(f"Processing melee attack event: {event.description}")
        actor = None
        if event.event_initiator:
            actor = self.session.find_entity_by_name(event.event_initiator)
        if actor is None:
            raise ValueError(f"Cannot find the attacker {event.event_initiator}")
        
        event_target = self.session.find_entity_by_name(event.event_target) if event.event_target else None
        
        task = self.generator.generate_one_shot(
            pydantic_model=MeleeAttackBreakdown,
            prompt=f"""
# Role:
You are an action classificator and you need to determine exact information of an action described in artistic form and bind it to its context data.

## Rules:
1. You need to a weapon and a target of the attack.
2. If an attack was successful based on scene context and character stats and environment.
3. Provide exact damage dice expressins for damage dealt.
4. Provide exiting artistic description of an attack using environment.

## Scene context:
{self.session.get_session_context()}

## Attack actor:
{actor.character.short_summary}

## Target (if found):
{event_target}
"""
        )
        
        if not task.attack_success:
            return [Event(
                event_type=EventTypes.ACTION_RESULT,
                description=task.attack_description + f"(attack failed)"
            )]
            
        target = self.session.find_entity_by_name(task.target_name)
        if target is None:
            self.logger.warning(f"Can't find attack target (skipped)")
            return [Event(
                event_type=EventTypes.ACTION_RESULT,
                description=f"(attack failed) (cant find attack target)"
            )]
        
        events = []
        target.character.active_conditions_list += task.conditions_applied
        if task.conditions_applied != []:
            events.append(Event(
                event_type=EventTypes.ACTION_RESULT,
                description=f"(conditions applied after an attack) {"/".join(c.short_summary for c in task.conditions_applied)}"
            ))
            self.logger.info(f"🤢(conditions applied after an attack) {"/".join(c.short_summary for c in task.conditions_applied)}")
        damage = roll_dice(task.damage_dealt)
        target.take_damage(damage)
        self.logger.info(f"💕Character {target.character.name} takes {damage} ({task.damage_dealt})")
        return events
            