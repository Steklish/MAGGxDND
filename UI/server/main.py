"""
MAGGxDND Game Server - WebSocket & REST API
Bridges the game engine with the React UI
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from uvicorn import Config, Server

# Add parent directory to path to import game engine
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from game.event_pool import EventPool, SubscriberQueue
from interface.delivery import Delivery, Request
from schemas.in_game import Character
from schemas.orchestration import Event

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("game_server")


class GameDelivery(Delivery):
    """
    WebSocket-based delivery implementation.
    Bridges the game engine with WebSocket clients.
    """

    def __init__(self, event_queue: SubscriberQueue, logger_instance: logging.Logger):
        super().__init__(event_queue, logger_instance)
        self.websocket_handlers: Dict[str, 'WebSocketHandler'] = {}
        self._pending_player_choice: Optional[Any] = None
        self._player_choice_event = asyncio.Event()

    def register_handler(self, player_id: str, handler: 'WebSocketHandler'):
        """Register a WebSocket handler for a player."""
        self.websocket_handlers[player_id] = handler
        self.logger.info(f"Registered WebSocket handler for player: {player_id}")

    def unregister_handler(self, player_id: str):
        """Unregister a WebSocket handler."""
        if player_id in self.websocket_handlers:
            del self.websocket_handlers[player_id]
            self.logger.info(f"Unregistered WebSocket handler for player: {player_id}")

    async def master_message(self, text: str, tag: Optional[str] = None):
        """Broadcast GM/DM narration message to all connected clients."""
        self.logger.info(f"[MASTER] {tag or ''}: {text}")
        
        # Send to all connected handlers
        for handler in self.websocket_handlers.values():
            try:
                await handler.send_master_message(text, tag)
            except Exception as e:
                self.logger.error(f"Failed to send master message: {e}")

    async def player_request(self, character: Character) -> str:
        """
        Wait for player input via WebSocket.
        This is async and will wait until a message is received.
        """
        player_id = character.name
        self.logger.info(f"Waiting for request from player: {player_id}")

        # Wait for request from this player
        request = self.wait_for_request_from_player(player_id, timeout=300.0)
        
        if request:
            self.logger.info(f"Received request from {player_id}: {request.request_text}")
            return request.request_text
        else:
            self.logger.warning(f"Timeout waiting for request from {player_id}")
            return ""

    async def choose_player(self, session) -> 'Player':
        """
        Select which player acts next.
        For now, automatically selects the first player.
        Can be extended to allow GM selection via UI.
        """
        if not session.players:
            raise ValueError("No players in session")
        
        # For now, just return the first player
        # Can be extended to allow GM selection
        selected_player = session.players[0]
        self.logger.info(f"Selected player: {selected_player.character.name}")
        return selected_player

    async def session_updated(self, session) -> None:
        """Broadcast session state to all connected clients."""
        self.logger.debug("Session updated, broadcasting to clients")
        
        # Send to all connected handlers
        for handler in self.websocket_handlers.values():
            try:
                await handler.send_session_update(session)
            except Exception as e:
                self.logger.error(f"Failed to send session update: {e}")

    async def send_game_event(self, event: Event):
        """Send a game event to all connected clients."""
        self.logger.debug(f"Sending game event: {event.event_type}")
        
        for handler in self.websocket_handlers.values():
            try:
                await handler.send_game_event(event)
            except Exception as e:
                self.logger.error(f"Failed to send game event: {e}")


class WebSocketHandler:
    """
    Handles WebSocket connections for a single player.
    """

    def __init__(
        self,
        websocket: WebSocket,
        session_id: str,
        player_id: str,
        delivery: GameDelivery,
        event_queue: SubscriberQueue,
        logger_instance: logging.Logger
    ):
        self.websocket = websocket
        self.session_id = session_id
        self.player_id = player_id
        self.delivery = delivery
        self.event_queue = event_queue
        self.logger = logger_instance
        self._listen_task: Optional[asyncio.Task] = None

    async def connect(self):
        """Accept WebSocket connection and start listening for messages."""
        await self.websocket.accept()
        self.logger.info(f"WebSocket connected: {self.player_id} in session {self.session_id}")
        
        # Register with delivery
        self.delivery.register_handler(self.player_id, self)
        
        # Send connection confirmation
        await self.websocket.send_json({
            "type": "CONNECTED",
            "session_id": self.session_id,
            "player_id": self.player_id
        })
        
        # Start listening for messages
        self._listen_task = asyncio.create_task(self.listen_for_messages())
        
        # Start forwarding events from event queue
        asyncio.create_task(self.forward_events())

    async def disconnect(self):
        """Close WebSocket connection and cleanup."""
        self.logger.info(f"WebSocket disconnecting: {self.player_id}")
        
        # Unregister from delivery
        self.delivery.unregister_handler(self.player_id)
        
        # Cancel listen task
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        
        # Close WebSocket
        try:
            await self.websocket.close()
        except Exception:
            pass

    async def listen_for_messages(self):
        """Listen for incoming WebSocket messages and process them."""
        try:
            while True:
                data = await self.websocket.receive_json()
                await self.handle_message(data)
        except WebSocketDisconnect:
            self.logger.info(f"WebSocket disconnected: {self.player_id}")
        except asyncio.CancelledError:
            self.logger.info(f"WebSocket listen task cancelled: {self.player_id}")
        except Exception as e:
            self.logger.error(f"Error in WebSocket listen loop: {e}")

    async def handle_message(self, data: dict):
        """Process incoming WebSocket message."""
        msg_type = data.get("type")
        payload = data.get("payload", {})
        
        self.logger.debug(f"Received message from {self.player_id}: {msg_type}")
        
        if msg_type == "PLAYER_ACTION":
            await self.handle_player_action(payload)
        elif msg_type == "CHOOSE_PLAYER":
            await self.handle_choose_player(payload)
        elif msg_type == "SUBSCRIBE_EVENTS":
            await self.handle_subscribe_events(payload)
        elif msg_type == "META_REQUEST":
            await self.handle_meta_request(payload)
        else:
            self.logger.warning(f"Unknown message type: {msg_type}")

    async def handle_player_action(self, payload: dict):
        """Handle player action request."""
        try:
            player_id = payload.get("player_id")
            request_text = payload.get("request_text", "")
            timestamp = payload.get("timestamp", 0.0)
            character_data = payload.get("character", {})
            
            if not player_id or not request_text:
                await self.send_error("Invalid player action: missing player_id or request_text")
                return
            
            # Create Character object from data
            character = Character(**character_data)
            
            # Create Request and add to delivery queue
            request = Request(
                player_id=player_id,
                request_text=request_text,
                timestamp=timestamp,
                character=character
            )
            
            self.delivery.put_request(request)
            self.logger.info(f"Player action queued: {player_id} - {request_text[:50]}...")
            
            # Confirm action received
            await self.websocket.send_json({
                "type": "ACTION_CONFIRMED",
                "payload": {
                    "player_id": player_id,
                    "request_text": request_text
                }
            })
            
        except Exception as e:
            self.logger.error(f"Error handling player action: {e}")
            await self.send_error(f"Failed to process action: {str(e)}")

    async def handle_choose_player(self, payload: dict):
        """Handle GM player selection."""
        try:
            selected_player_id = payload.get("selected_player_id")
            if selected_player_id:
                self.delivery._pending_player_choice = selected_player_id
                self.delivery._player_choice_event.set()
                self.logger.info(f"GM selected player: {selected_player_id}")
        except Exception as e:
            self.logger.error(f"Error handling choose player: {e}")

    async def handle_subscribe_events(self, payload: dict):
        """Handle event subscription."""
        subscriber_id = payload.get("subscriber_id")
        if subscriber_id:
            self.logger.info(f"Player {self.player_id} subscribed to events as {subscriber_id}")

    async def handle_meta_request(self, payload: dict):
        """Handle out-of-character meta request."""
        try:
            message = payload.get("message", "")
            self.logger.info(f"Meta request from {self.player_id}: {message}")
            
            # Send as master message with Meta tag
            await self.send_master_message(message, tag="Meta")
        except Exception as e:
            self.logger.error(f"Error handling meta request: {e}")

    async def send_master_message(self, text: str, tag: Optional[str] = None):
        """Send GM/DM message to client."""
        await self.websocket.send_json({
            "type": "MASTER_MESSAGE",
            "payload": {
                "text": text,
                "tag": tag
            }
        })

    async def send_session_update(self, session):
        """Send full session state to client."""
        try:
            # Serialize session (simplified for now)
            session_data = {
                "session_name": session.session_name,
                "game_mode": session.game_mode.value if hasattr(session.game_mode, 'value') else str(session.game_mode),
                "current_scene": self._serialize_scene(session.current_scene) if session.current_scene else None,
                "players": [self._serialize_player(p) for p in session.players],
                "npcs": [self._serialize_npc(n) for n in session.npcs],
                "turn_queue": self._serialize_turn_queue(session.turn_queue),
                "turn_time": session.turn_time,
                "current_location_name": session.current_location_name,
                "spatial_enabled": session.spatial_enabled
            }
            
            await self.websocket.send_json({
                "type": "SESSION_UPDATE",
                "payload": {
                    "session": session_data
                }
            })
        except Exception as e:
            self.logger.error(f"Error sending session update: {e}")

    async def send_game_event(self, event: Event):
        """Send game event to client."""
        await self.websocket.send_json({
            "type": "GAME_EVENT",
            "payload": {
                "event": {
                    "event_type": event.event_type,
                    "event_initiator": event.event_initiator,
                    "event_subject": event.event_subject,
                    "event_target": event.event_target,
                    "description": event.description
                }
            }
        })

    async def send_error(self, message: str, details: Optional[str] = None):
        """Send error message to client."""
        await self.websocket.send_json({
            "type": "ERROR",
            "payload": {
                "message": message,
                "details": details
            }
        })

    async def forward_events(self):
        """Forward events from event queue to WebSocket client."""
        try:
            while True:
                event = self.event_queue.get()
                if event:
                    await self.send_game_event(event)
                else:
                    await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Error forwarding events: {e}")

    def _serialize_scene(self, scene) -> dict:
        """Serialize SceneNode to dict (without gm_secret)."""
        if not scene:
            return {}
        
        data = scene.dict() if hasattr(scene, 'dict') else {}
        # Remove sensitive information
        data.pop("gm_secret", None)
        data.pop("gm_secrets", None)
        return data

    def _serialize_player(self, player) -> dict:
        """Serialize Player entity to dict."""
        if hasattr(player, 'character'):
            return {
                "character": self._serialize_character(player.character)
            }
        return {}

    def _serialize_npc(self, npc) -> dict:
        """Serialize NPC entity to dict."""
        if hasattr(npc, 'character'):
            return {
                "character": self._serialize_character(npc.character)
            }
        return {}

    def _serialize_character(self, character: Character) -> dict:
        """Serialize Character to dict."""
        return character.dict() if hasattr(character, 'dict') else {}

    def _serialize_turn_queue(self, turn_queue: list) -> list:
        """Serialize turn queue to list of dicts."""
        result = []
        for entry in turn_queue:
            if len(entry) >= 3:
                char, time_added, next_turn = entry[0], entry[1], entry[2]
                char_name = char.character.name if hasattr(char, 'character') else str(char)
                result.append({
                    "character": char_name,
                    "time_added": time_added,
                    "next_turn": next_turn
                })
        return result


# Create FastAPI app
app = FastAPI(
    title="MAGGxDND Game Server",
    description="WebSocket & REST API for MAGGxDND game engine",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
active_sessions: Dict[str, dict] = {}
event_pools: Dict[str, EventPool] = {}


@app.on_event("startup")
async def startup_event():
    """Initialize server on startup."""
    logger.info("MAGGxDND Game Server starting...")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown."""
    logger.info("MAGGxDND Game Server shutting down...")


@app.get("/")
async def root():
    """Root endpoint - server status."""
    return {
        "status": "running",
        "service": "MAGGxDND Game Server",
        "version": "0.1.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.websocket("/ws/{session_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, player_id: str):
    """WebSocket endpoint for real-time game communication."""
    logger.info(f"New WebSocket connection: session={session_id}, player={player_id}")
    
    # Get or create event pool for this session
    if session_id not in event_pools:
        event_pools[session_id] = EventPool()
        logger.info(f"Created new EventPool for session: {session_id}")
    
    event_pool = event_pools[session_id]
    
    # Subscribe player to events
    subscriber_queue = event_pool.subscribe(player_id)
    
    # Create delivery instance (or get existing one)
    if session_id not in active_sessions:
        delivery = GameDelivery(subscriber_queue, logger)
        active_sessions[session_id] = {
            "delivery": delivery,
            "players": {}
        }
    else:
        delivery = active_sessions[session_id]["delivery"]
    
    # Create WebSocket handler
    handler = WebSocketHandler(
        websocket=websocket,
        session_id=session_id,
        player_id=player_id,
        delivery=delivery,
        event_queue=subscriber_queue,
        logger_instance=logger
    )
    
    # Connect and handle
    await handler.connect()
    
    # Keep connection alive
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        await handler.disconnect()
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await handler.disconnect()


# Import routes
from server.routes import sessions, characters, auth

# Include routers
app.include_router(sessions.router, prefix="/api/v1", tags=["Sessions"])
app.include_router(characters.router, prefix="/api/v1", tags=["Characters"])
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])


if __name__ == "__main__":
    # Run server
    config = Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = Server(config)
    asyncio.run(server.serve())
