import logging
import time
import sys
import asyncio
from typing import TYPE_CHECKING
from fastapi import WebSocket

# This is a temporary solution.
# In a real-world scenario, you'd have a better way to manage paths,
# probably by making the project a proper Python package.
sys.path.append(r"D:\Lectures\SDLC\MAGGxDND")

from delivery.game_delivery import GameDelivery
from interface.delivery import Request
from game.event_pool import SubscriberQueue

if TYPE_CHECKING:
    from game.engine import Session

logger = logging.getLogger("server.ws_handler")


async def listen_for_events(websocket: WebSocket, event_queue: SubscriberQueue, client_id: str):
    """
    Continuously listen for events from the event_queue and forward to the client.
    This bridges the synchronous game engine (using threading.Queue) with the
    asynchronous server (using asyncio).
    """
    logger.info(f"Starting event listener for {client_id}")
    loop = asyncio.get_event_loop()
    try:
        while True:
            # The event_queue.get() is a blocking call.
            # We run it in a separate thread from the asyncio event loop
            # to prevent it from blocking the entire server.
            event = await loop.run_in_executor(None, event_queue.get)

            if event:
                logger.debug(f"Forwarding event '{event.event_type}' to {client_id}")
                await websocket.send_json({
                    "type": "GAME_EVENT",
                    "payload": {"event": event.model_dump()}
                })
    except Exception as e:
        logger.warning(f"Event listener for {client_id} stopped. Reason: {e}")


async def handle_websocket_message(
    data: dict,
    session: "Session",
    delivery: GameDelivery,
    player_id: str,
):
    """Handles incoming WebSocket messages."""
    msg_type = data.get("type")
    payload = data.get("payload", {})
    logger.debug(f"Received message type '{msg_type}' from {player_id}")

    if msg_type == "PLAYER_ACTION":
        # As per the docs, create a Request object and add it to the queue.
        # The game loop's call to `delivery.player_request` will then pick it up.
        try:
            # The character object is required by the Request schema in the engine
            player = next((p for p in session.players if p.character.name == payload["player_id"]), None)
            if not player:
                logger.error(f"Player '{payload['player_id']}' not found in session for PLAYER_ACTION.")
                return

            request = Request(
                player_id=payload["player_id"],
                request_text=payload["request_text"],
                character=player.character,
                timestamp=time.time(),
            )
            delivery.put_request(request)
            logger.info(f"Queued PLAYER_ACTION from {player_id}: '{payload['request_text']}'")
        except KeyError as e:
            logger.error(f"Invalid PLAYER_ACTION payload from {player_id}: missing {e}")


    elif msg_type == "CHOOSE_PLAYER":
        # The GM/UI has selected the next player to act.
        try:
            selected_id = payload["selected_player_id"]
            player = next((p for p in session.players if p.character.name == selected_id), None)
            if player:
                delivery.set_player_choice(player)
                logger.info(f"Player choice '{selected_id}' was set by {player_id}")
            else:
                logger.error(f"Player '{selected_id}' chosen by {player_id} not found in session.")
        except KeyError as e:
            logger.error(f"Invalid CHOOSE_PLAYER payload from {player_id}: missing {e}")

    elif msg_type == "META_REQUEST":
        logger.info(f"Received meta request from {player_id}: {payload.get('message')}")
        # Handle meta requests (e.g., asking the GM a question)
        # This could be forwarded to a GM-specific message queue or handled directly.
        delivery.master_message(
            f"Meta-request from {player_id}: {payload.get('message')}",
            tag="Meta"
        )
    
    else:
        logger.warning(f"Received unknown message type '{msg_type}' from {player_id}")
