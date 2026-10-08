# type: ignore[reportGeneralTypeIssues, reportAttributeAccessIssue, reportArgumentType, reportUndefinedVariable, reportCallIssue]
"""
WebSocket router для подключения игроков к игровым сессиям.

Эндпоинт: ws://localhost:8000/ws/{session_id}/{player_id}
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Optional
import asyncio
import json
import time
import logging
from datetime import datetime

try:
    from websockets.exceptions import ConnectionClosed
except ImportError:
    ConnectionClosed = WebSocketDisconnect  # fallback alias

from backend.src.game.session_manager import session_manager, SessionManager
from core.game.event_pool import SubscriberQueue
from core.schemas.orchestration import Event, EventTypes
from core.schemas.in_game import Character

logger = logging.getLogger(__name__)

router = APIRouter()


async def event_stream_sender(
    websocket: WebSocket,
    subscriber_queue: SubscriberQueue,
    session_id: str,
    player_id: str
):
    """
    Отправляет события из SubscriberQueue в WebSocket.

    Работает как отдельная асинхронная задача пока подключен игрок.
    """
    event_count = 0
    logger.debug(f"Event stream sender task started for player {player_id}")
    try:
        while True:
            # Ждём событие из очереди (неблокирующе)
            event = subscriber_queue.get()

            if event:
                event_count += 1

                # Handle special event types that need direct message format
                event_type_str = event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type)

                if event_type_str == "PLAYER_MESSAGE":
                    # Send as direct PLAYER_MESSAGE so frontend chat shows it properly
                    event_dict = {
                        "type": "PLAYER_MESSAGE",
                        "payload": {
                            "sender_name": event.event_initiator or "Player",
                            "text": event.description or "",
                            "timestamp": ""
                        }
                    }
                elif event_type_str == "DM_THINKING":
                    # Send as GAME_EVENT with DM_THINKING type so frontend shows thinking indicator
                    event_dict = {
                        "type": "GAME_EVENT",
                        "payload": {
                            "event": {
                                "event_type": event_type_str,
                                "event_initiator": event.event_initiator,
                                "event_subject": event.event_subject,
                                "event_target": event.event_target,
                                "description": event.description,
                            }
                        },
                    }
                else:
                    # Regular game event
                    event_dict = {
                        "type": "GAME_EVENT",
                        "payload": {
                            "event": {
                                "event_type": event_type_str,
                                "event_initiator": event.event_initiator,
                                "event_subject": event.event_subject,
                                "event_target": event.event_target,
                                "description": event.description,
                            }
                        },
                    }

                # Log event being sent to frontend
                logger.debug(
                    f"EVENT SENT TO FRONTEND [{event_count}] | "
                    f"Session: {session_id} | Player: {player_id} | "
                    f"Event Type: {event_type_str} | "
                    f"Description: {event.description[:100] if event.description else 'N/A'} | "
                    f"Journey: EventPool → WebSocket → Frontend"
                )

                await websocket.send_json(event_dict)
            else:
                # Если событий нет, ждём немного перед следующей проверкой
                await asyncio.sleep(0.1)

    except (WebSocketDisconnect, ConnectionClosed):
        logger.info(f"Player {player_id} disconnected from session {session_id}")
    except RuntimeError as e:
        # WebSocket was closed when trying to send — normal during disconnect
        logger.debug(f"Player {player_id} WebSocket closed during send: {e}")
    except Exception as e:
        logger.error(
            f"Error sending events to player {player_id}: {e}",
            exc_info=True
        )


async def event_receiver(
    websocket: WebSocket,
    session_id: str,
    player_id: str,
    session_manager: SessionManager
):
    """
    Receives player actions from the client and queues them for the game loop.

    The game loop (running as a background task) calls delivery.player_request()
    which blocks until a request arrives in the queue.  No processing here —
    just enqueuing, exactly like terminal input() feeding NativeTerminalDelivery.
    """
    logger.debug(f"Event receiver task started for player {player_id}")
    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("event_type", data.get("type", "UNKNOWN"))

            session = session_manager.get_session(session_id)
            if not session:
                await websocket.send_json({"type": "ERROR", "message": "Session not found"})
                continue

            if event_type in ["PLAYER_ACTION", "ACTION"]:
                # Extract character name and action text
                action_data = data.get("payload", data.get("data", data.get("action", {})))
                if not isinstance(action_data, dict):
                    action_data = {}

                # Robust character name extraction
                character_name = (
                    action_data.get("character_name")
                    or data.get("character_name")
                )
                if not character_name:
                    char_val = action_data.get("character") or data.get("character")
                    if isinstance(char_val, dict):
                        character_name = char_val.get("name")
                    elif isinstance(char_val, str):
                        character_name = char_val

                # Robust action text extraction
                action_text = (
                    action_data.get("request_text")
                    or action_data.get("action")
                    or action_data.get("text")
                    or data.get("action")
                    or data.get("request_text")
                    or data.get("text")
                    or ""
                )

                # Fallback: resolve character name from database participant or active player
                if not character_name:
                    from backend.src.repositories.session_repository import SessionRepository
                    from backend.src.database.session import SessionLocal
                    with SessionLocal() as db_ctx:
                        repo = SessionRepository(db_ctx)
                        participants = repo.get_session_participants(session_id)
                        p_match = next((p for p in participants if p.get("player_uuid") == player_id), None)
                        if p_match and p_match.get("character_name"):
                            character_name = p_match.get("character_name")

                if not character_name and session.players:
                    character_name = session.players[0].character.name

                if not character_name:
                    character_name = "Player"

                if not action_text:
                    logger.warning(f"Missing action text. Got: {data}")
                    await websocket.send_json({
                        "type": "ERROR",
                        "message": "Missing action description"
                    })
                    continue

                # 1. Prevent overlapping queries
                if session.delivery.has_requests():
                    is_ru = getattr(session, "language", "ru") == "ru"
                    logger.warning(f"Action rejected for {character_name}: previous query is still resolving.")
                    await websocket.send_json({
                        "type": "ERROR",
                        "message": "Мастер подземелий сейчас обдумывает предыдущее действие. Пожалуйста, подождите..." if is_ru else "The Dungeon Master is currently resolving a previous action. Please wait..."
                    })
                    continue

                # 2. Strict Combat Turn Enforcement
                mode_str = session.game_mode.value if hasattr(session.game_mode, 'value') else str(session.game_mode)
                if mode_str.upper() == "COMBAT" and hasattr(session, 'get_current_turn_character_name'):
                    active_combatant = session.get_current_turn_character_name()
                    if active_combatant and character_name.strip().lower() != active_combatant.strip().lower():
                        is_ru = getattr(session, "language", "ru") == "ru"
                        logger.warning(f"Out-of-turn action rejected: {character_name} tried to act while active turn is {active_combatant}")
                        await websocket.send_json({
                            "type": "ERROR",
                            "message": f"Сейчас не ваш ход! Текущий ход принадлежит: {active_combatant}." if is_ru else f"It is not your turn! Current turn belongs to {active_combatant}."
                        })
                        continue

                # Ensure player exists in session.players so engine can process turn
                if not any(hasattr(p, 'character') and p.character.name == character_name for p in session.players):
                    from backend.src.api.routers.session_router import procedural_gen
                    from core.entity.orchestrator import Orchestrator
                    char_obj = procedural_gen.generate_character(name=character_name, prompt="")
                    orchestrator = Orchestrator(
                        generator=session.generator,
                        logger=session.logger.getChild("player_orchestrator")
                    )
                    orchestrator.add_state(session)
                    p_inst = session._init_player(char_obj, orchestrator)
                    session.players.append(p_inst)
                    logger.info(f"[WS] Auto-registered player {character_name} in session.players")

                logger.info(
                    f"PLAYER ACTION QUEUED | "
                    f"Session: {session_id} | Player: {player_id} | "
                    f"Character: {character_name} | "
                    f"Action: {action_text[:100]} | "
                    f"Journey: Frontend → WebSocket → delivery queue → game loop"
                )

                # Enqueue the request — the game loop picks it up via player_request().
                from core.interface.delivery import Request
                import time
                request = Request(
                    player_id=character_name,
                    request_text=action_text,
                    timestamp=time.time(),
                    character=None,  # resolved by game loop via Player object
                )
                session.delivery.put_request(request)
                logger.debug(f"Request queued for {character_name}")

                # Ensure game loop is running for this session
                from backend.src.api.routers.session_router import _active_game_loops, _run_game_loop
                if session_id not in _active_game_loops:
                    logger.info(f"[WS] Restarting game loop for session {session_id} on incoming action")
                    asyncio.create_task(_run_game_loop(session_id, session))
                    _active_game_loops.add(session_id)

                # Notify ALL players (including sender) that DM is thinking so no one queues overlapping actions
                await session_manager.broadcast_to_session(
                    session_id=session_id,
                    event=Event(
                        event_type="DM_THINKING",
                        event_initiator=character_name,
                        description=f"{character_name} is waiting for DM response..."
                    )
                )

            elif event_type == "PLAYER_MESSAGE":
                # Player chat message - broadcast to other players
                payload = data.get("payload", {})
                sender_name = payload.get("sender_name", "Unknown")
                text = payload.get("text", "")
                
                logger.info(
                    f"PLAYER MESSAGE | "
                    f"Session: {session_id} | Player: {player_id} | "
                    f"Sender: {sender_name} | "
                    f"Text: {text[:100]}"
                )
                
                # Broadcast to other players via EventPool
                await session_manager.broadcast_to_session(
                    session_id=session_id,
                    event=Event(
                        event_type="PLAYER_MESSAGE",
                        event_initiator=sender_name,
                        description=text
                    ),
                    exclude_player_id=player_id
                )
                
                # Send acknowledgment to sender
                await websocket.send_json({
                    "type": "MESSAGE_SENT",
                    "payload": {"sender_name": sender_name, "text": text}
                })

            elif event_type in ["CHANGE_SCENE", "TRANSITION_LOCATION"]:
                payload = data.get("payload", data.get("data", {}))
                loc_name = payload.get("location_name") or payload.get("scene_name") or data.get("location_name")
                loc_desc = payload.get("description") or data.get("description")
                if loc_name:
                    logger.info(f"[WS] Transitioning location to '{loc_name}' for session {session_id}")
                    session.transition_to_location(loc_name, loc_desc)
                    await websocket.send_json({
                        "type": "LOCATION_TRANSITIONED",
                        "location_name": loc_name
                    })

            elif event_type in ["SET_GAME_MODE", "ENTER_COMBAT", "EXIT_COMBAT"]:
                payload = data.get("payload", data.get("data", {}))
                reason = payload.get("reason")
                if event_type == "ENTER_COMBAT":
                    session.enter_combat(reason=reason or "Combat started via player action")
                elif event_type == "EXIT_COMBAT":
                    session.exit_combat(reason=reason or "Combat concluded via player action")
                else:
                    mode = payload.get("mode") or data.get("mode", "STORY")
                    session.set_game_mode(mode, reason=reason)
                await websocket.send_json({
                    "type": "GAME_MODE_CHANGED",
                    "game_mode": session.game_mode.value
                })

            elif event_type in ["SET_LANGUAGE", "CHANGE_LANGUAGE"]:
                logger.info(f"[WS] Session language is locked for session {session_id}. Mid-game change rejected.")
                await websocket.send_json({
                    "type": "ERROR",
                    "message": "Session language is set when creating the adventure and locked afterwards."
                })

            elif event_type == "PING":
                await websocket.send_json({
                    "type": "PONG",
                    "timestamp": datetime.now().isoformat()
                })

            else:
                # Unknown event type — broadcast to other players
                event_data = data.get("data", {})
                event = Event(
                    event_type=event_type,
                    event_initiator=player_id,
                    description=data.get("description", json.dumps(event_data))
                )
                await session_manager.broadcast_to_session(
                    session_id=session_id, event=event, exclude_player_id=player_id
                )
                await websocket.send_json({
                    "type": "ACTION_CONFIRMED",
                    "event": {"event_type": event_type, "data": event_data}
                })

    except WebSocketDisconnect:
        logger.info(f"Player {player_id} disconnected from session {session_id}")
    except RuntimeError as e:
        # WebSocket was closed — normal during disconnect
        logger.debug(f"Player {player_id} WebSocket closed during receive: {e}")
    except Exception as e:
        logger.error(f"Error receiving events from player {player_id}: {e}", exc_info=True)


@router.websocket("/ws/{session_id}/{player_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    player_id: str
):
    """
    WebSocket эндпоинт для подключения игроков к игровой сессии.

    Подключение: ws://localhost:8000/ws/{session_id}/{player_id}

    Формат сообщений:
    - Клиент -> Сервер: {"event_type": "PLAYER_ACTION", "data": {...}}
    - Сервер -> Клиент: {"event_type": "...", "data": {...}, "source": "..."}
    """
    # Log connection
    logger.info(f"WebSocket connected: {player_id} → session {session_id}")

    # Проверяем существование сессии (восстанавливаем из БД если сервер перезапускался)
    if not session_manager.session_exists(session_id):
        from backend.src.api.routers.session_router import ensure_session_in_memory
        restored = ensure_session_in_memory(session_id)
        if not restored:
            logger.error(f"Session not found in DB or memory: {session_id}")
            await websocket.accept()
            await websocket.send_json({
                "error": "Session not found",
                "session_id": session_id
            })
            await websocket.close(code=4004, reason="Session not found")
            return
        logger.info(f"[WS] Session {session_id} successfully restored from database upon WebSocket connect")

    # Принимаем подключение
    await websocket.accept()

    try:
        # Регистрируем WebSocket
        await session_manager.register_player_websocket(
            session_id=session_id,
            player_id=player_id,
            websocket=websocket
        )

        # Подписываем игрока на события (исключаем его собственные события)
        subscriber_queue = session_manager.subscribe_player_to_events(
            session_id=session_id,
            player_id=player_id,
            exclude_self=True
        )

        if not subscriber_queue:
            try:
                await websocket.send_json({"error": "Failed to subscribe to events"})
                await websocket.close(code=4005, reason="Subscription failed")
            except (WebSocketDisconnect, ConnectionClosed, RuntimeError):
                pass
            return

        # Log successful subscription
        logger.debug(
            f"PLAYER SUBSCRIBED TO EVENTS | "
            f"Session: {session_id} | Player: {player_id} | "
            f"Queue ID: {id(subscriber_queue)} | "
            f"Journey: WebSocket Connected → Subscribed → Ready"
        )

        # ── Launch game loop on first connection ─────────────────────────
        from backend.src.api.routers.session_router import _active_game_loops, _run_game_loop
        if session_id not in _active_game_loops:
            session = session_manager.get_session(session_id)
            if session:
                logger.info(f"[WS] Launching game loop for session {session_id} (first player connected)")
                asyncio.create_task(_run_game_loop(session_id, session))
                _active_game_loops.add(session_id)

        # Отправляем приветственное сообщение
        try:
            await websocket.send_json({
                "type": "CONNECTED",
                "session_id": session_id,
                "player_id": player_id,
                "message": "Successfully connected to game session"
            })
        except (WebSocketDisconnect, ConnectionClosed, RuntimeError):
            logger.info(f"Player {player_id} disconnected during CONNECTED handshake")
            return

        # Activate human player control for assigned character
        active_sess = session_manager.get_session(session_id)
        if active_sess:
            char_name = None
            try:
                from backend.src.database.session import SessionLocal
                from backend.src.repositories.session_repository import SessionRepository
                with SessionLocal() as db_sess:
                    repo = SessionRepository(db_sess)
                    parts = repo.get_session_participants(session_id)
                    for part in parts:
                        if part.get("player_uuid") == player_id or str(part.get("user_id")) == str(player_id) or part.get("player_name") == player_id:
                            char_name = part.get("character_name")
                            break
            except Exception as e:
                logger.debug(f"Could not load participant for character link: {e}")

            for p in active_sess.players:
                if hasattr(p, 'character'):
                    if (
                        getattr(p.character, 'controlled_by_player_id', None) == player_id
                        or (char_name and getattr(p.character, 'name', None) == char_name)
                        or getattr(p.character, 'name', None) == player_id
                    ):
                        p.is_ai_controlled = False
                        p.character.is_ai_controlled = False
                        p.character.controlled_by_player_id = player_id
                        logger.info(f"[WS-CONNECT] Player {player_id} reclaimed character {p.character.name}")
                        from core.schemas.orchestration import Event, EventTypes
                        active_sess.event_pool.add_event(Event(
                            event_type=EventTypes.SYSTEM,
                            event_initiator="Game System",
                            description=f"{p.character.name} is now actively piloted by a connected player.",
                            event_subject=p.character.name,
                        ))
                        break

            # Send initial session state immediately so the frontend has up-to-date data
            try:
                await websocket.send_json({
                    "type": "SESSION_UPDATE",
                    "payload": {
                        "session": active_sess.get_session_state()
                    }
                })
            except (WebSocketDisconnect, ConnectionClosed, RuntimeError):
                logger.info(f"Player {player_id} disconnected during SESSION_UPDATE sync")
                return
            except Exception as init_err:
                logger.debug(f"Could not send initial session state: {init_err}")

        # Start send and receive tasks
        send_task = asyncio.create_task(
            event_stream_sender(websocket, subscriber_queue, session_id, player_id)
        )

        receive_task = asyncio.create_task(
            event_receiver(websocket, session_id, player_id, session_manager)
        )

        logger.debug(f"Both tasks created successfully for player {player_id}")
        await asyncio.sleep(0.05)

        done, pending = await asyncio.wait(
            [send_task, receive_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        for task in pending:
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, WebSocketDisconnect, ConnectionClosed, RuntimeError):
                pass

        for task in done:
            if not task.cancelled() and task.exception():
                exc = task.exception()
                if not isinstance(exc, (WebSocketDisconnect, ConnectionClosed, asyncio.CancelledError, RuntimeError)):
                    logger.warning(f"Task completed with error for player {player_id}: {exc}")

    except (WebSocketDisconnect, ConnectionClosed, RuntimeError) as disc:
        logger.info(f"Player {player_id} disconnected from session {session_id}")
    except Exception as e:
        logger.error(f"Unexpected WebSocket error for player {player_id}: {e}", exc_info=True)
    finally:
        # Check if the closed socket is the currently registered one
        was_current = session_manager.unregister_player_websocket(
            session_id=session_id,
            player_id=player_id,
            websocket=websocket
        )

        if was_current:
            # Player disconnected. Do not immediately strip control or wipe event queue!
            # Start a 30-second disconnect grace timeout so page reloads or brief connection drops
            # can reconnect seamlessly without losing character ownership.
            async def _grace_cleanup(s_id: str, p_id: str):
                try:
                    logger.info(f"[WS-GRACE] Player {p_id} disconnected from session {s_id}. Grace timeout started (30s).")
                    await asyncio.sleep(30.0)

                    logger.info(f"[WS-GRACE] Grace period expired for player {p_id} in session {s_id}. Transitioning character to AI companion.")
                    session_manager.unsubscribe_player_from_events(s_id, p_id)

                    sess_disc = session_manager.get_session(s_id)
                    if sess_disc:
                        disc_char_name = None
                        try:
                            from backend.src.database.session import SessionLocal
                            from backend.src.repositories.session_repository import SessionRepository
                            with SessionLocal() as db_sess:
                                repo = SessionRepository(db_sess)
                                parts = repo.get_session_participants(s_id)
                                for part in parts:
                                    if part.get("player_uuid") == p_id or str(part.get("user_id")) == str(p_id) or part.get("player_name") == p_id:
                                        disc_char_name = part.get("character_name")
                                        break
                        except Exception:
                            pass

                        for p in sess_disc.players:
                            if hasattr(p, 'character') and (
                                getattr(p.character, 'controlled_by_player_id', None) == p_id
                                or (disc_char_name and getattr(p.character, 'name', None) == disc_char_name)
                            ):
                                p.is_ai_controlled = True
                                p.character.is_ai_controlled = True
                                p.character.controlled_by_player_id = None
                                logger.info(f"[WS-DISCONNECT] Character {p.character.name} handed over to AI control after grace timeout")
                                from core.schemas.orchestration import Event, EventTypes
                                sess_disc.event_pool.add_event(Event(
                                    event_type=EventTypes.SYSTEM,
                                    event_initiator="Game System",
                                    description=f"{p.character.name}'s player timed out; character is now controlled by AI companion and open to join.",
                                    event_subject=p.character.name,
                                ))
                                if hasattr(sess_disc, "delivery") and sess_disc.delivery:
                                    sess_disc.delivery.session_updated(sess_disc)
                                break
                except asyncio.CancelledError:
                    logger.info(f"[WS-GRACE] Player {p_id} reconnected within grace period! AI handover cancelled.")

            grace_task = asyncio.create_task(_grace_cleanup(session_id, player_id))
            session_manager.schedule_disconnect_grace(session_id, player_id, grace_task)
        else:
            logger.info(f"WebSocket closed for player {player_id}, but a newer connection is already active. Preserving state.")


@router.get("/sessions/{session_id}/players")
async def get_session_players(session_id: str):
    """Получить список игроков в сессии."""
    session = session_manager.get_session(session_id)
    if not session:
        return {"error": "Session not found", "status_code": 404}
    
    websockets = session_manager.get_all_session_websockets(session_id)
    return {
        "session_id": session_id,
        "players": list(websockets.keys()),
        "player_count": len(websockets)
    }


@router.get("/sessions/{session_id}/info")
async def get_session_info(session_id: str):
    """Получить информацию о сессии."""
    info = session_manager.get_session_info(session_id)
    if not info:
        return {"error": "Session not found", "status_code": 404}
    
    return info
