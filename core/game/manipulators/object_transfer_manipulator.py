from typing import TYPE_CHECKING, List

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from core.game.engine import Session
from core.game.manipulators.base_manipulation import BaseManipulation
from core.schemas.orchestration import Event, EventTypes
from core.schemas.in_game import UnifiedObject


class ObjectTransferBreakdown(BaseModel):
    """Breakdown of an object transfer action."""
    object_name: str = Field(..., description="Name of the object being transferred")
    source_location: str = Field(..., description="Source location of the object ('inventory', 'container', or 'scene')")
    target_location: str = Field(..., description="Target location for the object ('inventory', 'container', or 'scene')")
    target_container_name: str = Field(description="Name of the target container if transferring to a container")
    source_container_name: str = Field(description="Name of the source container if transferring from a container")
    transfer_quantity: int = Field(1, description="Quantity of the object to transfer")
    transfer_description: str = Field(..., description="Description of the transfer action")
    transfer_successful: bool = Field(True, description="Whether the transfer was successful")
    transfer_reason: str = Field(..., description="Reason why the transfer occurred")


class ObjectTransferManipulator(BaseManipulation):
    event_types_binded = [
        EventTypes.OBJECT_TRANSFER,
        EventTypes.ITEM_TRANSFER,
        EventTypes.ITEM_PICKUP,
        EventTypes.ITEM_DROP,
        EventTypes.CONTAINER_TRANSFER
    ]

    def __init__(self, state: 'Session'):
        super().__init__(state)
        self.logger.info("ObjectTransferManipulator initialized")

    def manipulate(self, event: Event) -> List[Event]:
        """
        Process an object transfer event and apply the results to the game state.
        """
        self.logger.info(f"Processing object transfer event: {event.description}")
        
        task = self.generator.generate_one_shot(
            pydantic_model=ObjectTransferBreakdown,
            prompt=f"""
# Role:
You are an action classifier and you need to determine exact information of an object transfer action described in artistic form and bind it to its context data.

## Rules:
1. Identify the object being transferred, its source location, and target location.
2. Determine if the transfer is possible based on scene context, container capacities, object properties, and character inventories.
3. Specify if the transfer is between containers, from/to inventory, from/to scene, etc.
4. Provide the quantity of objects being transferred (default to 1 if not specified).
5. Provide the reason for the transfer (e.g., picked up by character, moved between containers, dropped in scene, etc.).
6. Provide an artistic description of the transfer using the environment.

## Scene context:
{self.session.get_session_context()}

## Transfer event:
{event.description}
"""
        )

        if not task.transfer_successful:
            return [Event(
                event_type=EventTypes.ACTION_RESULT,
                description=task.transfer_description + f"(object transfer failed)"
            )]

        # Perform the actual transfer
        transfer_result = self._perform_transfer(task)

        if not transfer_result:
            return [Event(
                event_type=EventTypes.ACTION_RESULT,
                description=f"(object transfer failed) (could not perform transfer of {task.object_name})"
            )]

        events = []
        events.append(Event(
            event_type=EventTypes.ACTION_RESULT,
            description=f"{task.transfer_description} (transferred {task.transfer_quantity} of {task.object_name} from {task.source_location} to {task.target_location} because {task.transfer_reason})"
        ))
        
        self.logger.info(f"📦Object {task.object_name} transferred from {task.source_location} to {task.target_location}")
        return events

    def _perform_transfer(self, task: ObjectTransferBreakdown) -> bool:
        """
        Perform the actual transfer of the object between locations using session methods.
        """
        # Use the session's find_object_and_location method to locate the object and its current location
        obj_to_transfer, current_location, owner, container = self.session.find_object_and_location(task.object_name)
        if obj_to_transfer is None or current_location is None:
            self.logger.warning(f"Could not find object {task.object_name} using session.find_object_and_location")
            return False

        # Determine the target owner and container if needed
        target_owner = None
        target_container = None

        if task.target_location in ['player_inventory', 'npc_inventory'] and not target_owner:
            # If no specific owner was designated, default to the first player
            if self.session.players:
                target_owner = self.session.players[0]
            elif self.session.npcs:
                target_owner = self.session.npcs[0]

        if task.target_location == 'container' and task.target_container_name:
            # Find the target container
            target_container, _, _, _ = self.session.find_object_and_location(task.target_container_name)
            if not target_container:
                self.logger.warning(f"Could not find target container {task.target_container_name}")
                return False

        # Perform the actual transfer using the session's transfer method
        transfer_success = self.session.transfer_object(
            obj=obj_to_transfer,
            from_location=current_location,
            to_location=task.target_location,
            quantity=task.transfer_quantity,
            target_owner=target_owner,
            target_container=target_container
        )

        if transfer_success:
            self.logger.info(f"Successfully transferred {task.transfer_quantity} of {task.object_name} from {current_location} to {task.target_location}")
            return True
        else:
            self.logger.warning(f"Failed to transfer {task.object_name}")
            return False