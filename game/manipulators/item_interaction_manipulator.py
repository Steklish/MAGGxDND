from typing import TYPE_CHECKING, List

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from game.engine import Session
from game.manipulators.base_manipulation import BaseManipulation
from schemas.orchestration import Event, EventTypes
from schemas.in_game import UnifiedObject, Condition


class ItemInteractionBreakdown(BaseModel):
    """Breakdown of an item interaction action."""
    item_name: str = Field(..., description="Name of the item being interacted with")
    character_name: str = Field(..., description="Name of the character interacting with the item")
    interaction_type: str = Field(..., description="Type of interaction (e.g., 'use', 'equip', 'consume', 'open', 'inspect')")
    interaction_description: str = Field(..., description="Artistic description of the interaction")
    interaction_successful: bool = Field(True, description="Whether the interaction was successful")
    interaction_effects: List[str] = Field(default_factory=list, description="Effects of the interaction (e.g., healing, damage, status effects)")
    conditions_applied: List[Condition] = Field(default_factory=list, description="A list of conditions that the interaction may cause")
    # Fields for item transfer when opening containers
    requires_item_transfer: bool = Field(False, description="Whether this interaction requires transferring items between locations (e.g., opening a container)")
    source_location: str = Field(description="Source location of items if transfer is required ('scene', 'container', 'player_inventory', 'npc_inventory')")
    target_location: str = Field(description="Target location for items if transfer is required ('scene', 'container', 'player_inventory', 'npc_inventory')")
    items_to_transfer: List[str] = Field(default_factory=list, description="Names of items to transfer if transfer is required")
    target_container_name: str = Field(description="Name of the target container if transferring to a container")
    source_container_name: str = Field(description="Name of the source container if transferring from a container")


class ItemInteractionManipulator(BaseManipulation):
    event_types_binded = [
        EventTypes.ITEM_INTERACTION
    ]

    def __init__(self, state: 'Session'):
        super().__init__(state)
        self.logger.info("ItemInteractionManipulator initialized")

    def manipulate(self, event: Event) -> List[Event]:
        """
        Process an item interaction event and apply the results to the game state.
        """
        self.logger.info(f"Processing item interaction event: {event.description}")

        task = self.generator.generate_one_shot(
            pydantic_model=ItemInteractionBreakdown,
            prompt=f"""
# Role:
You are an action classifier and you need to determine exact information of an item interaction action described in artistic form and bind it to its context data.

## Rules:
1. Identify the item being interacted with and the character performing the interaction.
2. Determine the type of interaction (use, equip, consume, open, inspect, etc.).
3. Determine if the interaction is possible based on scene context, character stats, item properties, and environment.
4. Calculate any effects of the interaction (healing, damage, status effects, etc.).
5. Determine if any conditions are applied to the character as a result of the interaction.
6. For interactions involving containers (e.g., opening a chest), determine if items need to be transferred between locations.
7. If item transfer is required, specify the source location, target location, and items to transfer.
8. Provide an artistic description of the interaction using the environment.

## Scene context:
{self.session.get_session_context()}

## Item interaction event:
{event.description}
"""
        )

        if not task.interaction_successful:
            return [Event(
                event_type=EventTypes.ACTION_RESULT,
                description=task.interaction_description + f"(interaction failed)"
            )]

        # Find the character performing the interaction
        character = self.session.find_entity_by_name(task.character_name)
        if character is None:
            self.logger.warning(f"Could not find character {task.character_name} for item interaction")
            return [Event(
                event_type=EventTypes.ACTION_RESULT,
                description=f"(interaction failed) (could not find character {task.character_name})"
            )]

        # Find the item being interacted with
        item = self.session.find_object_by_name(task.item_name)
        if item is None:
            self.logger.warning(f"Could not find item {task.item_name} for interaction")
            return [Event(
                event_type=EventTypes.ACTION_RESULT,
                description=f"(interaction failed) (could not find item {task.item_name})"
            )]

        # Apply any conditions to the character
        events = []
        if task.conditions_applied:
            character.character.active_conditions_list.extend(task.conditions_applied)
            events.append(Event(
                event_type=EventTypes.CHARACTER_STATUS_CHANGE,
                event_subject=character.character.name,
                description=f"Applied conditions to {character.character.name}: {', '.join(c.short_summary for c in task.conditions_applied)}"
            ))
            self.logger.info(f"🤢Applied conditions to {character.character.name}: {', '.join(c.short_summary for c in task.conditions_applied)}")

        # Process any interaction effects (healing, damage, etc.)
        for effect in task.interaction_effects:
            # This is a simplified approach - in a real implementation you'd want more detailed parsing
            # of the effect string to determine what type of effect it is
            self.logger.info(f"🎭Effect of interaction: {effect}")

        # If this interaction requires item transfer (e.g., opening a container),
        # generate appropriate transfer events for the ObjectTransferManipulator to handle
        if task.requires_item_transfer and task.items_to_transfer:
            for item_name in task.items_to_transfer:
                item_to_transfer = self.session.find_object_by_name(item_name)
                if item_to_transfer:
                    # Find the current location of the item
                    obj, current_location, owner, container = self.session.find_object_and_location(item_name)

                    # Create an item transfer event for the ObjectTransferManipulator to handle
                    transfer_event = Event(
                        event_type=EventTypes.ITEM_TRANSFER,
                        event_initiator=task.character_name,
                        event_subject=item_name,
                        description=f"{task.character_name} transfers {item_name} from {current_location or task.source_location} to {task.target_location}",
                    )
                    events.append(transfer_event)
                    self.logger.info(f"📦Generated transfer event for {item_name} from {current_location or task.source_location} to {task.target_location}")

        # Add the main interaction result
        events.append(Event(
            event_type=EventTypes.ACTION_RESULT,
            description=f"{task.interaction_description} (interaction successful)"
        ))

        self.logger.info(f"{task.character_name} interacted with {task.item_name} successfully")
        return events