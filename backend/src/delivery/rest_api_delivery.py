# type: ignore[reportGeneralTypeIssues, reportAttributeAccessIssue, reportArgumentType, reportUndefinedVariable, reportCallIssue, reportReturnType]
"""
REST API Delivery - bridges game engine with REST API endpoints.
Allows server to interact with game sessions through Delivery interface.
"""

from core.interface.delivery import Delivery, Request
from core.game.event_pool import SubscriberQueue
from logging import Logger
from typing import TYPE_CHECKING, Optional, Dict, Any
import asyncio
from queue import Queue

if TYPE_CHECKING:
    from core.entity.player import Player
    from core.game.engine import Session
    from core.schemas.in_game import Character


class RESTAPIDelivery(Delivery):
    """
    Delivery implementation for REST API interaction.
    Stores session state and provides methods for server to interact with game.
    """
    
    def __init__(self, event_queue: SubscriberQueue, logger: Logger, session_id: str):
        super().__init__(event_queue, logger)
        self.session_id = session_id
        self._session: Optional['Session'] = None
        self._last_dm_message: str = ""
        self._last_action_result: Dict[str, Any] = {}
        self._player_requests: Dict[str, Queue] = {}
    
    def set_session(self, session: 'Session'):
        """Set the session reference (called after creation)."""
        self._session = session
    
    @property
    def session(self) -> Optional['Session']:
        """Get the current session."""
        return self._session
    
    @property
    def last_dm_message(self) -> str:
        """Get the last DM message sent."""
        return self._last_dm_message
    
    @property
    def last_action_result(self) -> Dict[str, Any]:
        """Get the result of the last action processed."""
        return self._last_action_result
    
    def master_message(self, text: str, tag: Optional[str] = None) -> None:
        """
        Send a DM/master message.
        Stores the message for API retrieval.
        """
        self._last_dm_message = text
        self.logger.info(f"[{self.session_id}] DM: {text}")

        # Also emit as event
        from core.schemas.orchestration import Event, EventTypes
        event = Event(
            event_type=EventTypes.SYSTEM,
            event_initiator="DM",
            description=text,
        )
        self.game_event_queue.put(event)
    
    def player_request(self, character: 'Character') -> str:
        """
        Process a player request through the game engine.
        Returns the DM response.
        """
        self.logger.info(f"[{self.session_id}] Player request from {character.name}")
        
        # Wait for request from this player
        request = self.wait_for_request_from_player(character.name, timeout=30.0)
        
        if request:
            self.logger.info(f"[{self.session_id}] Request: {request.request_text}")
            return request.request_text
        else:
            self.logger.warning(f"[{self.session_id}] Timeout waiting for {character.name}")
            return ""
    
    def choose_player(self, session: 'Session') -> 'Player':
        """
        Choose which player acts next.
        For REST API, returns the first player.
        """
        if session.players:
            return session.players[0]
        raise ValueError("No players in session")
    
    def session_updated(self, session: 'Session') -> None:
        """
        Called when session state is updated.
        Stores updated state for API retrieval.
        """
        self._session = session
        self.logger.info(f"[{self.session_id}] Session updated")
    
    # === REST API Methods ===
    
    def process_player_action(self, character_name: str, action_text: str) -> Dict[str, Any]:
        """
        Process a player action through the game engine.
        This is the main entry point for REST API.
        
        Args:
            character_name: Name of the character performing the action
            action_text: The action description
            
        Returns:
            Dict with action result including DM response
        """
        if not self._session:
            return {
                "error": "Session not initialized",
                "status": "error"
            }
        
        # Find the player
        player = None
        for p in self._session.players:
            if hasattr(p, 'character') and p.character.name == character_name:
                player = p
                break
        
        if not player:
            return {
                "error": f"Character {character_name} not found",
                "status": "error"
            }
        
        try:
            # Add request to queue
            from datetime import datetime
            request = Request(
                player_id=character_name,
                request_text=action_text,
                timestamp=datetime.now().timestamp(),
                character=player.character
            )
            self.put_request(request)
            
            # Process through orchestrator
            orchestrator = self._session.orchestrator
            if not orchestrator:
                return {
                    "error": "Orchestrator not available",
                    "status": "error"
                }
            
            # Process request
            user_interaction = orchestrator.request(
                username=character_name,
                request_text=action_text
            )
            
            self.logger.info(f"[{self.session_id}] User interaction: {user_interaction}")
            
            # Process based on game mode
            if self._session.game_mode.value == "COMBAT":
                verdict = orchestrator.character_action_combat(
                    character=player,
                    request_text=action_text,
                    processed_interaction=user_interaction
                )
            else:
                verdict = orchestrator.character_action_story(
                    character=player,
                    request_text=action_text,
                    processed_interaction=user_interaction
                )
            
            self.logger.info(f"[{self.session_id}] Verdict: {verdict}")
            
            # Get DM response
            dm_response = verdict.details if verdict.details else "The DM considers your action..."
            
            self.logger.info(f"[{self.session_id}] DM Response: {dm_response}")
            
            # Send through delivery
            self.master_message(dm_response)
            
            # Store result
            self._last_action_result = {
                "character": character_name,
                "action": action_text,
                "verdict": str(verdict),
                "dm_response": dm_response,
                "status": "processed"
            }
            
            return self._last_action_result
            
        except Exception as e:
            self.logger.error(f"[{self.session_id}] Error processing action: {e}", exc_info=True)
            return {
                "error": str(e),
                "status": "error"
            }
    
    def get_session_state(self) -> Dict[str, Any]:
        """
        Get current session state for API.
        """
        if not self._session:
            return {"error": "Session not initialized"}
        
        return {
            "session_id": self.session_id,
            "session_name": self._session.session_name,
            "game_mode": self._session.game_mode.value if hasattr(self._session.game_mode, 'value') else str(self._session.game_mode),
            "current_scene": {
                "name": self._session.current_scene.name if self._session.current_scene else None,
                "description": self._session.current_scene.description if self._session.current_scene else None,
            } if self._session.current_scene else None,
            "players": [
                {
                    "name": p.character.name,
                    "hp": p.character.current_hp,
                    "max_hp": p.character.max_hp,
                }
                for p in self._session.players
                if hasattr(p, 'character')
            ],
            "npcs": [
                {
                    "name": n.character.name,
                    "hp": n.character.current_hp,
                    "current_scene": n.character.current_scene,
                }
                for n in self._session.npcs
                if hasattr(n, 'character')
            ],
            "last_dm_message": self._last_dm_message,
        }
