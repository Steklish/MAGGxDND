# type: ignore[reportGeneralTypeIssues, reportAttributeAccessIssue, reportArgumentType, reportUndefinedVariable, reportCallIssue, reportReturnType]
"""
GameDelivery - Implementation of abstract Delivery class for WebSocket.

Binds game engine to player WebSocket connections.
IMPORTANT: GameDelivery holds a direct reference to Session for immediate access.
All methods are async-compatible and work properly within FastAPI context.
"""
from typing import TYPE_CHECKING, Optional
import asyncio
from logging import Logger
from core.interface.delivery import Delivery
from core.game.event_pool import SubscriberQueue

if TYPE_CHECKING:
    from core.game.engine import Session
    from core.entity.player import Player
    from core.schemas.in_game import Character


class GameDelivery(Delivery):
    """
    Delivery implementation for sending messages via WebSocket.
    
    Holds direct reference to Session for immediate state access.
    All WebSocket sends are fully async and FastAPI-compatible.
    """

    def __init__(
        self,
        session_id: str,
        session: 'Session',
        event_queue: SubscriberQueue,
        logger: Logger
    ):
        """
        Initialize GameDelivery for a specific session.

        Args:
            session_id: ID of the game session
            session: Direct reference to Session (for immediate access)
            event_queue: Event queue for receiving events from EventPool
            logger: Logger for delivery
        """
        # Call base class constructor
        super().__init__(event_queue, logger)

        self.session_id = session_id
        self.session = session  # Direct reference to Session!

    async def _send_to_websocket(self, player_id: str, message: dict) -> None:
        """
        Send message to specific player via WebSocket.

        Args:
            player_id: ID of the player
            message: Message to send
        """
        from backend.src.game.session_manager import session_manager

        websocket = session_manager.get_player_websocket(self.session_id, player_id)
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception as e:
                self.logger.debug(f"Error sending message to player {player_id}: {e}")
        else:
            self.logger.debug(f"WebSocket for player {player_id} not found")

    async def _broadcast_to_session(self, message: dict, exclude_player: Optional[str] = None) -> None:
        """
        Send message to all players in session.

        Args:
            message: Message to send
            exclude_player: Player ID to exclude (sender)
        """
        from backend.src.game.session_manager import session_manager

        websockets = session_manager.get_all_session_websockets(self.session_id)
        if not websockets:
            self.logger.debug(f"No connected players in session {self.session_id}")
            return

        for player_id, websocket in websockets.items():
            if exclude_player and player_id == exclude_player:
                continue
            try:
                await websocket.send_json(message)
                self.logger.debug(f"Sent to player {player_id}: {message.get('type', 'unknown')}")
            except Exception as e:
                self.logger.debug(f"Error sending message to player {player_id}: {e}")

    def master_message(self, text: str, tag: Optional[str] = None) -> None:
        """
        Display message from GM (narration, description).
        
        Immediately sends message to all players and logs to Session.
        This method is sync but schedules async work properly in FastAPI context.

        Args:
            text: Message text
            tag: Optional tag for categorization
        """
        message = {
            "type": "MASTER_MESSAGE",
            "text": text,
            "tag": tag
        }

        # Log to Session (immediate access)
        self.session.logger.info(f"[MASTER] {text}")

        # Schedule async broadcast
        asyncio.create_task(self._broadcast_to_session(message))

        # Add message to Session history (immediate access)
        from core.schemas.orchestration import Message
        self.session.messages.append(
            Message(sender_name="GM", text=text, tag=tag or "narration")
        )

        # Limit history
        if len(self.session.messages) > 20:
            self.session.messages = self.session.messages[-20:]

    def player_request(self, character: "Character") -> str:
        """
        Request action from player.
        
        In WebSocket implementation, this is non-blocking
        and triggers waiting for message from client.

        Args:
            character: Player character

        Returns:
            Empty string (action comes via WebSocket)
        """
        message = {
            "type": "PLAYER_REQUEST",
            "character_id": character.id,
            "character_name": character.name
        }

        # Log to Session
        self.session.logger.debug(f"[PLAYER_REQUEST] {character.name}")

        # Schedule async broadcast
        asyncio.create_task(self._broadcast_to_session(message))

        return ""

    def choose_player(self, session: "Session") -> "Player":
        """
        Select next player to take turn.

        Args:
            session: Game session

        Returns:
            Player whose turn it is
        """
        if session.players:
            active_player = session.players[0]

            message = {
                "type": "TURN_UPDATE",
                "active_player_id": active_player.id,
                "active_player_name": active_player.character.name
            }

            # Log to Session
            session.logger.info(f"[TURN] Player turn: {active_player.character.name}")

            # Schedule async broadcast
            asyncio.create_task(self._broadcast_to_session(message))

            return active_player

        raise ValueError("No players in session")

    def session_updated(self, session: "Session") -> None:
        """
        Notify about session state update.
        
        Immediately sends update to all players.

        Args:
            session: Updated session
        """
        # Log the update
        session.logger.debug(f"[SESSION_UPDATE] {session.session_name}")

        # Serialize important state for clients
        message = {
            "type": "SESSION_UPDATE",
            "data": {
                "session_name": session.session_name,
                "game_mode": session.game_mode.value,
                "scene_name": session.current_scene.name if session.current_scene else None,
                "player_count": len(session.players),
                "npc_count": len(session.npcs),
                "turn_queue": [
                    {
                        "entity_id": entity.id if hasattr(entity, 'id') else str(entity),
                        "entity_type": "player" if isinstance(entity, session.players[0].__class__) else "npc"
                    }
                    for entity, _, _ in session.turn_queue
                ] if session.turn_queue else []
            }
        }

        # Schedule async broadcast
        asyncio.create_task(self._broadcast_to_session(message))

    async def get_next_message(self) -> dict:
        """
        Get next message from queue.

        Returns:
            Message from queue
        """
        # This method is not used in current implementation
        # Events are streamed via WebSocket through event_stream_sender
        pass

    def send_to_player(self, player_id: str, message: dict) -> None:
        """
        Send message to specific player.

        Args:
            player_id: ID of player
            message: Message
        """
        self.session.logger.debug(f"[SEND_TO_PLAYER] {player_id}: {message.get('type', 'unknown')}")

        # Schedule async send
        asyncio.create_task(self._send_to_websocket(player_id, message))

    def send_character_update(
        self,
        character_id: str,
        updates: dict,
        exclude_player: Optional[str] = None
    ) -> None:
        """
        Send character state update.

        Args:
            character_id: ID of character
            updates: Update data
            exclude_player: Exclude player (sender)
        """
        message = {
            "type": "CHARACTER_UPDATE",
            "character_id": character_id,
            "updates": updates
        }

        self.session.logger.debug(f"[CHARACTER_UPDATE] {character_id}: {updates}")

        # Schedule async broadcast
        asyncio.create_task(self._broadcast_to_session(message, exclude_player))

    def send_scene_update(self, scene_data: dict) -> None:
        """
        Send scene update.

        Args:
            scene_data: Scene data
        """
        message = {
            "type": "SCENE_UPDATE",
            "scene": scene_data
        }

        self.session.logger.debug(f"[SCENE_UPDATE] {scene_data.get('name', 'unknown')}")

        # Schedule async broadcast
        asyncio.create_task(self._broadcast_to_session(message))

    def send_combat_event(self, event_data: dict) -> None:
        """
        Send combat event.

        Args:
            event_data: Combat event data
        """
        message = {
            "type": "COMBAT_EVENT",
            "data": event_data
        }

        self.session.logger.info(f"[COMBAT_EVENT] {event_data}")

        # Schedule async broadcast
        asyncio.create_task(self._broadcast_to_session(message))

    async def process_player_action(self, character_name: str, action_text: str, player_id: Optional[str] = None) -> dict:
        """
        Process a player action through the orchestrator.
        
        This is the main input pipeline: Action -> Orchestrator -> Manipulator -> Events
        
        Args:
            character_name: Name of the character performing action
            action_text: Action description
            player_id: Optional player ID for exclusion
            
        Returns:
            Dict with DM response and events
        """
        from core.schemas.orchestration import Event
        
        self.session.logger.info(f"[PLAYER_ACTION] {character_name}: {action_text}")
        
        try:
            # Find the player in session
            player = None
            for p in self.session.players:
                if hasattr(p, 'character') and p.character.name == character_name:
                    player = p
                    break
            
            if not player:
                error_msg = f"Character '{character_name}' not found in session"
                self.session.logger.warning(f"[PLAYER_ACTION] {error_msg}")
                
                # Send error via WebSocket
                error_message = {
                    "type": "ERROR",
                    "message": error_msg
                }
                asyncio.create_task(self._broadcast_to_session(error_message, player_id))
                
                return {
                    "success": False,
                    "error": error_msg,
                    "dm_response": "",
                    "events": []
                }
            
            # Put request in delivery queue
            from core.interface.delivery import Request
            import time
            request = Request(
                player_id=player_id or character_name,
                request_text=action_text,
                timestamp=time.time(),
                character=player.character
            )
            self.put_request(request)

            # Process through orchestrator
            if hasattr(self.session, 'orchestrator'):
                orchestrator = self.session.orchestrator

                # First, classify the interaction using orchestrator.request()
                processed_interaction = orchestrator.request(
                    username=character_name,
                    request_text=action_text
                )

                # Determine game mode and process accordingly
                if self.session.game_mode.value == "COMBAT":
                    verdict = orchestrator.character_action_combat(
                        character=player,
                        request_text=action_text,
                        processed_interaction=processed_interaction
                    )
                else:
                    verdict = orchestrator.character_action_story(
                        character=player,
                        request_text=action_text,
                        processed_interaction=processed_interaction
                    )

                # Handle verdict based on type (mimics terminal delivery flow)
                dm_response = ""
                from core.schemas.orchestration import OrchestrationVerdictType
                
                if verdict.verdict_type == OrchestrationVerdictType.CLAIRIFICATION_NEEDED:
                    # Clarification needed - ask player for clarification
                    if hasattr(self.session, 'game_master') and self.session.game_master:
                        dm_response = self.session.game_master.clarify_user_request(
                            correction_question=verdict.details if verdict.details else "Action needs clarification"
                        )
                    else:
                        dm_response = verdict.details if verdict.details else "Could you clarify what you mean?"
                    
                    self.session.logger.info(f"[PLAYER_ACTION] Clarification needed: {dm_response}")

                elif verdict.verdict_type == OrchestrationVerdictType.ILLEGAL_PLAYER_ACTION:
                    # Illegal action - explain why and request new action
                    if hasattr(self.session, 'game_master') and self.session.game_master:
                        dm_response = self.session.game_master.illegal_action_comment(
                            prompt=action_text,
                            name=character_name,
                            reasoning=verdict.details if verdict.details else "Action is not allowed"
                        )
                    else:
                        dm_response = f"[Illegal action] {verdict.details if verdict.details else 'Action not allowed'}"
                    
                    self.session.logger.info(f"[PLAYER_ACTION] Illegal action: {dm_response}")

                elif verdict.verdict_type == OrchestrationVerdictType.ALLOWED_PLAYER_ACTION:
                    # Allowed action - execute through manipulator, then get MAGG narrative
                    # Step 1: Execute events through manipulator (like terminal's run_story)
                    events = []
                    if hasattr(self.session, 'manipulator') and self.session.manipulator:
                        # Execute the action through manipulator (creates events)
                        action_events = self.session.manipulator._external_action_as_an_entity(
                            verdict.details if verdict.details else action_text,
                            player
                        )
                        # Execute events (triggers side effects, publishes to EventPool)
                        events = self.session.manipulator.execute_events(action_events)
                        self.session.logger.info(f"[PLAYER_ACTION] Executed {len(events)} events")

                    # Step 2: Call MAGG.handle_events() to generate AI narrative
                    # This is what terminal delivery does in game_loop line 1091
                    if hasattr(self.session, 'game_master') and self.session.game_master:
                        # handle_events() is async, so we need to await it
                        try:
                            # Try to run async MAGG in sync context
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                # Create task and await
                                import concurrent.futures
                                # Can't await in running loop, use run_coroutine_threadsafe
                                future = asyncio.run_coroutine_threadsafe(
                                    self.session.game_master.handle_events(),
                                    loop
                                )
                                dm_response = future.result(timeout=30.0)
                            else:
                                # No running loop, can use asyncio.run
                                dm_response = asyncio.run(self.session.game_master.handle_events())
                        except Exception as magg_error:
                            self.session.logger.warning(f"[PLAYER_ACTION] MAGG handle_events failed: {magg_error}, using fallback")
                            # Fallback: call comment() directly with events
                            if hasattr(self.session.game_master, 'comment'):
                                dm_response = self.session.game_master.comment(events)
                            else:
                                dm_response = verdict.details if verdict.details else action_text
                    else:
                        # No MAGG available - use verdict details as fallback
                        dm_response = verdict.details if verdict.details else action_text
                    
                    self.session.logger.info(f"[PLAYER_ACTION] AI narrative generated: {len(dm_response)} chars")
                else:
                    # Unknown verdict type - fallback to details
                    dm_response = verdict.details if verdict.details else ""

                # Broadcast DM response to all players
                if dm_response:
                    self.master_message(dm_response)

                # Send session update
                self.session_updated(self.session)

                result = {
                    "success": True,
                    "dm_response": dm_response if dm_response else "",
                    "events": [],  # Events are already published to EventPool
                    "game_state": {
                        "scene": self.session.current_scene.name if self.session.current_scene else None,
                        "players": len(self.session.players),
                        "npcs": len(self.session.npcs)
                    }
                }

                self.session.logger.info(f"[PLAYER_ACTION] Success: {character_name}")
                return result
            else:
                error_msg = "No orchestrator available in session"
                self.session.logger.error(f"[PLAYER_ACTION] {error_msg}")
                
                return {
                    "success": False,
                    "error": error_msg,
                    "dm_response": "",
                    "events": []
                }
                
        except Exception as e:
            error_msg = f"Error processing action: {str(e)}"
            self.session.logger.error(f"[PLAYER_ACTION] {error_msg}", exc_info=True)
            
            # Send error via WebSocket
            error_message = {
                "type": "ERROR",
                "message": error_msg
            }
            asyncio.create_task(self._broadcast_to_session(error_message, player_id))
            
            return {
                "success": False,
                "error": error_msg,
                "dm_response": "",
                "events": []
            }
