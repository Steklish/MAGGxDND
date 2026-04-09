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

from backend.src.game.session_manager import session_manager, SessionManager
from core.game.event_pool import SubscriberQueue
from core.schemas.orchestration import Event, EventTypes

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

                event_dict = {
                    "type": "GAME_EVENT",
                    "payload": {
                        "event": {
                            "event_type": event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type),
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
                    f"Event Type: {event_dict['event_type']} | "
                    f"Description: {event_dict.get('description', 'N/A')[:100]} | "
                    f"Journey: EventPool → WebSocket → Frontend"
                )

                await websocket.send_json(event_dict)
            else:
                # Если событий нет, ждём немного перед следующей проверкой
                await asyncio.sleep(0.1)

    except WebSocketDisconnect:
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
                character_name = action_data.get("character_name",
                    data.get("character_name",
                    action_data.get("character", {}).get("name", "")))
                action_text = action_data.get("request_text",
                    action_data.get("action",
                    action_data.get("text", "")))

                if not character_name or not action_text:
                    logger.warning(f"Missing character_name or action. Got: {data}")
                    await websocket.send_json({
                        "type": "ERROR",
                        "message": f"Missing character_name or action"
                    })
                    continue

                logger.info(
                    f"PLAYER ACTION QUEUED | "
                    f"Session: {session_id} | Player: {player_id} | "
                    f"Character: {character_name} | "
                    f"Action: {action_text[:100]} | "
                    f"Journey: Frontend → WebSocket → delivery queue → game loop"
                )

                # Enqueue the request — the game loop picks it up via player_request().
                # player_id here is the CHARACTER NAME so wait_for_request_from_player(name) finds it.
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

    # Проверяем существование сессии
    if not session_manager.session_exists(session_id):
        logger.error(f"Session not found: {session_id}")
        await websocket.accept()
        await websocket.send_json({
            "error": "Session not found",
            "session_id": session_id
        })
        await websocket.close(code=4004, reason="Session not found")
        return

    # Принимаем подключение
    await websocket.accept()

    
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
        await websocket.send_json({"error": "Failed to subscribe to events"})
        await websocket.close(code=4005, reason="Subscription failed")
        return

    # Log successful subscription
    logger.debug(
        f"PLAYER SUBSCRIBED TO EVENTS | "
        f"Session: {session_id} | Player: {player_id} | "
        f"Queue ID: {id(subscriber_queue)} | "
        f"Journey: WebSocket Connected → Subscribed → Ready"
    )

    # ── Launch game loop on first connection ─────────────────────────
    # The game loop must not start until a player is connected; otherwise
    # it cycles through NPCs forever and burns AI calls.
    from backend.src.api.routers.session_router import _active_game_loops, _run_game_loop
    if session_id not in _active_game_loops:
        session = session_manager.get_session(session_id)
        if session:
            logger.info(f"[WS] Launching game loop for session {session_id} (first player connected)")
            asyncio.create_task(_run_game_loop(session_id, session))
            _active_game_loops.add(session_id)

    # Отправляем приветственное сообщение
    await websocket.send_json({
        "type": "CONNECTED",
        "session_id": session_id,
        "player_id": player_id,
        "message": "Successfully connected to game session"
    })
    
    # Запускаем две параллельные задачи:
    # 1. Отправка событий клиенту
    # 2. Получение действий от клиента
    try:
        send_task = asyncio.create_task(
            event_stream_sender(websocket, subscriber_queue, session_id, player_id)
        )

        receive_task = asyncio.create_task(
            event_receiver(websocket, session_id, player_id, session_manager)
        )

        logger.debug(f"Both tasks created successfully for player {player_id}")

        # Give tasks a moment to initialize
        await asyncio.sleep(0.1)

        # Ждём завершения любой из задач (обычно при отключении)
        done, pending = await asyncio.wait(
            [send_task, receive_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        # Log which task completed
        for task in done:
            if task.exception():
                logger.error(f"Task completed with exception: {task.exception()}", exc_info=True)
            else:
                logger.debug("Task completed normally")

        # Отменяем оставшиеся задачи
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.debug("Task cancelled successfully")
    except Exception as e:
        logger.error(f"Exception in task management: {e}", exc_info=True)
        raise
    
    # Отключаем игрока
    session_manager.unregister_player_websocket(
        session_id=session_id,
        player_id=player_id
    )
    
    session_manager.unsubscribe_player_from_events(
        session_id=session_id,
        player_id=player_id
    )

    logger.info(f"Player {player_id} disconnected from session {session_id}")


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
