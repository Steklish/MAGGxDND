import asyncio
import logging
from typing import TYPE_CHECKING
import sys

# This is a temporary solution.
# In a real-world scenario, you'd have a better way to manage paths,
# probably by making the project a proper Python package.
sys.path.append(r"D:\Lectures\SDLC\MAGGxDND")

from interface.delivery import Delivery
from schemas.in_game import Character
from game.event_pool import SubscriberQueue
from websocket.manager import ConnectionManager

if TYPE_CHECKING:
    from game.engine import Session, Player

logger = logging.getLogger("server.delivery")

class GameDelivery(Delivery):
    """
    WebSocket-based delivery implementation.
    This class acts as a bridge between the game engine and the WebSocket clients.
    """

    def __init__(
        self,
        event_queue: SubscriberQueue,
        logger: logging.Logger,
        manager: ConnectionManager,
    ):
        super().__init__(event_queue, logger)
        self.manager = manager
        # This will hold the player choice from the UI
        self._pending_player_choice: "Player" | None = None
        self._choice_event = asyncio.Event()

    def master_message(self, text: str, tag: str | None = None):
        """Broadcasts a GM message to all connected UI clients."""
        logger.info(f"Broadcasting master_message: {text}")
        message = {"type": "MASTER_MESSAGE", "payload": {"text": text, "tag": tag}}
        asyncio.create_task(self.manager.broadcast(message))

    def player_request(self, character: Character) -> str:
        """
        Waits for a player action from the UI via WebSocket.
        This is a blocking call that will be fulfilled when a message
        arrives and is placed in the request queue.
        """
        logger.info(f"Waiting for player request for: {character.name}")
        # The `wait_for_request_from_player` method comes from the base Delivery class.
        # It will block until a request for this player is put into the queue.
        request = self.wait_for_request_from_player(character.name, timeout=300) # 5 min timeout
        if request:
            logger.info(f"Player request received for {character.name}: {request.request_text}")
            return request.request_text
        
        logger.warning(f"Timeout waiting for player request from {character.name}")
        return "wait" # Return a default action on timeout

    def choose_player(self, session: "Session") -> "Player":
        """
        Asks the UI to select which player acts next. This is a blocking call.
        """
        logger.info("Requesting player choice from UI.")
        self._pending_player_choice = None
        self._choice_event.clear()

        # Create a list of players for the UI to choose from
        player_options = [
            {"id": p.character.name, "name": p.character.name}
            for p in session.players if p.character.is_alive
        ]

        message = {
            "type": "CHOOSE_PLAYER_REQUEST",
            "payload": {"players": player_options},
        }

        # For simplicity, we broadcast this choice request.
        # A more robust system might send it only to a GM client.
        asyncio.create_task(self.manager.broadcast(message))

        # Wait for the choice to be made (see `set_player_choice` method)
        try:
            # This will block until `_choice_event.set()` is called
            asyncio.get_event_loop().run_until_complete(
                asyncio.wait_for(self._choice_event.wait(), timeout=300)
            )
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for player choice. Defaulting to first player.")
            return session.players[0]

        logger.info(f"Player choice received: {self._pending_player_choice.character.name}")
        return self._pending_player_choice
    
    def set_player_choice(self, player: "Player"):
        """Called by the WebSocket handler when a choice is received from the UI."""
        self._pending_player_choice = player
        self._choice_event.set()

    from models.serializers import serialize_session

# ... (inside GameDelivery class)

    def session_updated(self, session: "Session") -> None:
        """Broadcasts the entire session state to all clients."""
        logger.info("Session updated, broadcasting new state.")
        
        # Use the serializer to convert the session object to a dict
        serialized_data = serialize_session(session)
        
        message = {
            "type": "SESSION_UPDATE",
            "payload": {
                "session": serialized_data
            },
        }
        asyncio.create_task(self.manager.broadcast(message))
