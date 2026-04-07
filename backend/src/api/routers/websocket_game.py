"""
WebSocket router для подключения игроков к игровым сессиям.

Эндпоинт: ws://localhost:8000/ws/{session_id}/{player_id}
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Optional
import asyncio
import json
import time
from datetime import datetime

from backend.src.game.session_manager import session_manager, SessionManager
from core.game.event_pool import SubscriberQueue
from core.schemas.orchestration import Event, EventTypes

# ANSI color codes for console
class Colors:
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

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
    try:
        while True:
            # Ждём событие из очереди (неблокирующе)
            event = subscriber_queue.get()

            if event:
                event_count += 1

                # Сериализуем событие и отправляем клиенту
                event_dict = {
                    "event_type": event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type),
                    "data": event.data,
                    "source": event.source,
                    "timestamp": event.timestamp.isoformat() if hasattr(event, 'timestamp') and event.timestamp else None
                }
                await websocket.send_json(event_dict)
            else:
                # Если событий нет, ждём немного перед следующей проверкой
                await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        print(f"\n{Colors.YELLOW}⚠️  Player {player_id} disconnected from session {session_id}{Colors.RESET}\n")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error sending events to player {player_id}: {e}{Colors.RESET}\n")


async def event_receiver(
    websocket: WebSocket,
    session_id: str,
    player_id: str,
    session_manager: SessionManager
):
    """
    Receives events from client (player actions) and processes them through the game engine.
    
    Input pipeline: WebSocket -> Delivery.orchestrator -> Manipulator -> Events -> WebSocket
    """
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            # Log received WebSocket message (reduced verbosity)
            event_type = data.get("event_type", data.get("type", "UNKNOWN"))
            
            # Get the session
            session = session_manager.get_session(session_id)
            if not session:
                await websocket.send_json({
                    "type": "ERROR",
                    "message": "Session not found"
                })
                continue

            # Route through delivery for processing
            if hasattr(session, 'delivery') and session.delivery:
                # Handle different message types
                if event_type in ["PLAYER_ACTION", "ACTION"]:
                    # Extract action data
                    action_data = data.get("data", data.get("action", {}))
                    character_name = action_data.get("character_name", data.get("character_name", ""))
                    action_text = action_data.get("action", action_data.get("text", ""))
                    
                    if not character_name or not action_text:
                        await websocket.send_json({
                            "type": "ERROR",
                            "message": "Missing character_name or action in request"
                        })
                        continue
                    
                    # Process through delivery (which routes through orchestrator)
                    result = await session.delivery.process_player_action(
                        character_name=character_name,
                        action_text=action_text,
                        player_id=player_id
                    )
                    
                    # Send result back to player
                    await websocket.send_json({
                        "type": "ACTION_RESULT",
                        "success": result.get("success", False),
                        "dm_response": result.get("dm_response", ""),
                        "game_state": result.get("game_state", {}),
                        "error": result.get("error")
                    })
                    
                elif event_type == "PING":
                    # Heartbeat - respond with PONG
                    await websocket.send_json({
                        "type": "PONG",
                        "timestamp": datetime.now().isoformat()
                    })
                    
                else:
                    # Unknown event type - create event and broadcast to other players only
                    event_data = data.get("data", {})
                    from core.game.event_pool import Event
                    event = Event(
                        event_type=event_type,
                        data=event_data,
                        source=player_id
                    )

                    # Publish event to other players in session
                    await session_manager.broadcast_to_session(
                        session_id=session_id,
                        event=event,
                        exclude_player_id=player_id
                    )

                    # Send confirmation to sender
                    await websocket.send_json({
                        "type": "ACTION_CONFIRMED",
                        "event": {
                            "event_type": event_type,
                            "data": event_data
                        }
                    })
            else:
                # No delivery available - fallback to simple broadcast
                event_data = data.get("data", {})
                from core.game.event_pool import Event
                event = Event(
                    event_type=event_type,
                    data=event_data,
                    source=player_id
                )

                await session_manager.broadcast_to_session(
                    session_id=session_id,
                    event=event,
                    exclude_player_id=player_id
                )

                await websocket.send_json({
                    "type": "ERROR",
                    "message": "Delivery not available for action processing"
                })

    except WebSocketDisconnect:
        print(f"\n{Colors.YELLOW}⚠️  Player {player_id} disconnected from session {session_id}{Colors.RESET}\n")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error receiving events from player {player_id}: {e}{Colors.RESET}\n")


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
    print(f"\n{Colors.GREEN}🔌 WebSocket connected: {player_id} → session {session_id}{Colors.RESET}")
    
    # Проверяем существование сессии
    if not session_manager.session_exists(session_id):
        print(f"{Colors.RED}❌ Session not found: {session_id}{Colors.RESET}\n")
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
    send_task = asyncio.create_task(
        event_stream_sender(websocket, subscriber_queue, session_id, player_id)
    )
    
    receive_task = asyncio.create_task(
        event_receiver(websocket, session_id, player_id, session_manager)
    )
    
    # Ждём завершения любой из задач (обычно при отключении)
    done, pending = await asyncio.wait(
        [send_task, receive_task],
        return_when=asyncio.FIRST_COMPLETED
    )
    
    # Отменяем оставшиеся задачи
    for task in pending:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    
    # Отключаем игрока
    session_manager.unregister_player_websocket(
        session_id=session_id,
        player_id=player_id
    )
    
    session_manager.unsubscribe_player_from_events(
        session_id=session_id,
        player_id=player_id
    )
    
    print(f"Игрок {player_id} отключён от сессии {session_id}")


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
