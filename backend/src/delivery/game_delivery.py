# type: ignore[reportGeneralTypeIssues, reportAttributeAccessIssue, reportArgumentType]
"""
GameDelivery — thin WebSocket bridge between Session and the frontend.

Implements the same Delivery interface as NativeTerminalDelivery:
  master_message()    → broadcast GM narration to all players
  player_request()    → wait for a player action from the WebSocket queue
  choose_player()     → notify frontend whose turn it is, return selected player
  session_updated()   → broadcast full session state to all players
  put_request()       → queue an incoming player action (inherited from base)
  wait_for_request()  → block until the game loop can dequeue a request

All game logic (orchestrator, manipulator, MAGG) lives in Session / Player.
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
    """WebSocket delivery layer — pure I/O, no game logic."""

    def __init__(
        self,
        session_id: str,
        session: "Session",
        event_queue: SubscriberQueue,
        logger: Logger,
    ):
        super().__init__(event_queue, logger)
        self.session_id = session_id
        self.session = session

    # ── Internal WebSocket helpers ──────────────────────────────────────

    async def _send_to_websocket(self, player_id: str, message: dict) -> None:
        """Send a JSON message to one specific player."""
        from backend.src.game.session_manager import session_manager

        ws = session_manager.get_player_websocket(self.session_id, player_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception as exc:
                self.logger.debug(f"Send failed for {player_id}: {exc}")
        else:
            self.logger.debug(f"No WebSocket for {player_id}")

    async def _broadcast_to_session(self, message: dict, exclude_player: Optional[str] = None) -> None:
        """Broadcast a JSON message to all connected players."""
        from backend.src.game.session_manager import session_manager

        websockets = session_manager.get_all_session_websockets(self.session_id)
        if not websockets:
            self.logger.debug(f"No connected players in session {self.session_id}")
            return

        for pid, ws in websockets.items():
            if exclude_player and pid == exclude_player:
                continue
            try:
                await ws.send_json(message)
                self.logger.debug(f"→ {pid}: {message.get('type', '?')}")
            except Exception as exc:
                self.logger.debug(f"Send failed for {pid}: {exc}")

    # ── Abstract Delivery methods (same contract as NativeTerminalDelivery)

    def master_message(self, text: str, tag: Optional[str] = None) -> None:
        """Broadcast a GM narration to all connected players."""
        message = {"type": "MASTER_MESSAGE", "text": text, "tag": tag}
        self.session.logger.info(f"[MASTER] {text}")
        asyncio.create_task(self._broadcast_to_session(message))

        # Keep a copy in session history
        from core.schemas.orchestration import Message
        self.session.messages.append(Message(sender_name="GM", text=text, tag=tag or "narration"))
        if len(self.session.messages) > 100:
            self.session.messages = self.session.messages[-100:]

    def player_request(self, character: "Character") -> str:
        """
        Non-blocking check for player input.

        In COMBAT mode the caller loops until a non-empty result is returned.
        In STORY mode a single call is made; if no input is queued we return
        ``""`` so the game loop can continue cycling.
        """
        # Check if a request is already waiting in the queue (non-blocking)
        req = self.get_first_request_by_player(character.name)
        if req:
            self.session.logger.info(f"[PLAYER_REQUEST] Got queued input from {character.name}")
            return req.request_text

        # No input yet — signal frontend to prompt the player
        asyncio.create_task(self._broadcast_to_session({
            "type": "PLAYER_REQUEST",
            "character_id": getattr(character, "id", None),
            "character_name": character.name,
        }))
        return ""

    def choose_player(self, session: "Session") -> "Player":
        """
        Return the Player who has queued input.  Inspects the queue without
        consuming requests so that player_request() can pick them up normally.
        Falls back to the first player if no input is queued yet.
        """
        if not session.players:
            raise ValueError("No players in session")

        # Peek into the queue to find which player sent input
        best_player = session.players[0]
        temp: list = []
        found = False

        while not self.request_queue.empty():
            try:
                req = self.request_queue.get_nowait()
                temp.append(req)
                if not found:
                    # Match request to a player by character name
                    for p in session.players:
                        pname = p.character.name if hasattr(p, "character") else None
                        if pname and req.player_id == pname:
                            best_player = p
                            found = True
                            break
            except Exception:
                break

        # Put all requests back
        for req in temp:
            self.request_queue.put(req)

        name = best_player.character.name if hasattr(best_player, "character") else str(best_player)
        self.session.logger.info(f"[TURN] Player turn: {name}")
        asyncio.create_task(self._broadcast_to_session({
            "type": "TURN_UPDATE",
            "active_player_id": getattr(best_player, "id", None),
            "active_player_name": name,
        }))
        return best_player

    def session_updated(self, session: "Session") -> None:
        """Broadcast serialised session state to all players."""
        session.logger.debug(f"[SESSION_UPDATE] {session.session_name}")
        # Frontend expects format: {"type": "SESSION_UPDATE", "payload": {"session": {...}}}
        message = {
            "type": "SESSION_UPDATE",
            "payload": {
                "session": session.get_session_state()
            }
        }
        try:
            asyncio.get_running_loop()
            asyncio.create_task(self._broadcast_to_session(message))
        except RuntimeError:
            self.session.logger.debug("[SESSION_UPDATE] Deferred (no running loop)")

    async def get_next_message(self) -> dict:
        """Unused — events are streamed via event_stream_sender in websocket_game.py."""
        pass
