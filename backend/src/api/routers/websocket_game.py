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
    print(f"{Colors.GREEN}   [event_stream_sender] Task started for player {player_id}{Colors.RESET}")
    print(f"{Colors.CYAN}   [event_stream_sender] Entering main loop{Colors.RESET}")
    try:
        while True:
            # Ждём событие из очереди (неблокирующе)
            event = subscriber_queue.get()
            
            # Debug: log first few iterations
            # if event_count < 3:
                # print(f"{Colors.CYAN}   [event_stream_sender] Loop iteration, event={event is not None}{Colors.RESET}")

            if event:
                event_count += 1

                # Сериализуем событие и отправляем клиенту
                event_dict = {
                    "event_type": event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type),
                    "event_initiator": event.event_initiator,
                    "event_subject": event.event_subject,
                    "event_target": event.event_target,
                    "description": event.description,
                }
                
                # Log event being sent to frontend
                print(f"\n{Colors.CYAN}┌{'─' * 90}{Colors.RESET}")
                print(f"{Colors.CYAN}│{Colors.RESET} 📤 EVENT SENT TO FRONTEND [{event_count}]")
                print(f"{Colors.CYAN}│{Colors.RESET}    Session: {session_id}")
                print(f"{Colors.CYAN}│{Colors.RESET}    Player: {player_id}")
                print(f"{Colors.CYAN}│{Colors.RESET}    Event Type: {Colors.YELLOW}{event_dict['event_type']}{Colors.RESET}")
                print(f"{Colors.CYAN}│{Colors.RESET}    Description: {event_dict.get('description', 'N/A')[:100]}")
                print(f"{Colors.CYAN}│{Colors.RESET}    Journey: EventPool → WebSocket → Frontend")
                print(f"{Colors.CYAN}└{'─' * 90}{Colors.RESET}\n")
                
                await websocket.send_json(event_dict)
            else:
                # Если событий нет, ждём немного перед следующей проверкой
                await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        print(f"\n{Colors.YELLOW}⚠️  Player {player_id} disconnected from session {session_id}{Colors.RESET}\n")
    except RuntimeError as e:
        # WebSocket was closed when trying to send
        print(f"\n{Colors.YELLOW}⚠️  Player {player_id} WebSocket runtime error: {e}{Colors.RESET}\n")
    except Exception as e:
        import traceback
        print(f"\n{Colors.RED}❌ Error sending events to player {player_id}: {e}{Colors.RESET}")
        print(f"{Colors.RED}   Traceback:{Colors.RESET}")
        print(f"{Colors.RED}{traceback.format_exc()}{Colors.RESET}\n")
        raise  # Re-raise to see the full error


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
    print(f"{Colors.GREEN}   [event_receiver] Task started for player {player_id}{Colors.RESET}")
    print(f"{Colors.YELLOW}   [event_receiver] Entering main loop, waiting for first message...{Colors.RESET}")
    try:
        while True:
            # Receive message from client
            print(f"{Colors.YELLOW}   [event_receiver] Calling receive_json()...{Colors.RESET}")
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
                    # Extract action data - handle multiple formats
                    # Frontend sends: {type: "PLAYER_ACTION", payload: {request_text, character}}
                    # Also support: {type: "PLAYER_ACTION", data: {character_name, action}}
                    action_data = data.get("payload", data.get("data", data.get("action", {})))
                    character_name = action_data.get("character_name", 
                        data.get("character_name",
                        action_data.get("character", {}).get("name", "")))
                    action_text = action_data.get("request_text", 
                        action_data.get("action", 
                        action_data.get("text", "")))

                    if not character_name or not action_text:
                        print(f"{Colors.RED}   [event_receiver] Missing character_name or action. Got: {data}{Colors.RESET}")
                        await websocket.send_json({
                            "type": "ERROR",
                            "message": f"Missing character_name or action in request. Received: {json.dumps(data)[:200]}"
                        })
                        continue

                    # Log received player action
                    print(f"\n{Colors.GREEN}┌{'─' * 90}{Colors.RESET}")
                    print(f"{Colors.GREEN}│{Colors.RESET} 📥 PLAYER ACTION RECEIVED VIA WEBSOCKET")
                    print(f"{Colors.GREEN}│{Colors.RESET}    Session: {session_id}")
                    print(f"{Colors.GREEN}│{Colors.RESET}    Player: {player_id}")
                    print(f"{Colors.GREEN}│{Colors.RESET}    Character: {Colors.YELLOW}{character_name}{Colors.RESET}")
                    print(f"{Colors.GREEN}│{Colors.RESET}    Action: {action_text[:100]}")
                    print(f"{Colors.GREEN}│{Colors.RESET}    Journey: Frontend → WebSocket → Backend")
                    print(f"{Colors.GREEN}└{'─' * 90}{Colors.RESET}\n")

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
                    event = Event(
                        event_type=event_type,
                        event_initiator=player_id,
                        description=data.get("description", json.dumps(event_data))
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
                event = Event(
                    event_type=event_type,
                    event_initiator=player_id,
                    description=data.get("description", json.dumps(event_data))
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
    except RuntimeError as e:
        # WebSocket was closed when trying to send
        print(f"\n{Colors.YELLOW}⚠️  Player {player_id} WebSocket runtime error: {e}{Colors.RESET}\n")
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

    # Log successful subscription
    print(f"\n{Colors.CYAN}┌{'─' * 90}{Colors.RESET}")
    print(f"{Colors.CYAN}│{Colors.RESET} 🔔 PLAYER SUBSCRIBED TO EVENTS")
    print(f"{Colors.CYAN}│{Colors.RESET}    Session: {session_id}")
    print(f"{Colors.CYAN}│{Colors.RESET}    Player: {player_id}")
    print(f"{Colors.CYAN}│{Colors.RESET}    Queue ID: {id(subscriber_queue)}")
    print(f"{Colors.CYAN}│{Colors.RESET}    Journey: WebSocket Connected → Subscribed → Ready")
    print(f"{Colors.CYAN}└{'─' * 90}{Colors.RESET}\n")
    
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

        print(f"{Colors.GREEN}   [websocket_endpoint] Both tasks created successfully{Colors.RESET}")

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
                print(f"{Colors.RED}   [websocket_endpoint] Task completed with exception: {task.exception()}{Colors.RESET}")
                import traceback
                print(f"{Colors.RED}   {traceback.format_exc()}{Colors.RESET}")
            else:
                print(f"{Colors.GREEN}   [websocket_endpoint] Task completed normally{Colors.RESET}")

        # Отменяем оставшиеся задачи
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                print(f"{Colors.YELLOW}   [websocket_endpoint] Task cancelled successfully{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}   [websocket_endpoint] Exception in task management: {e}{Colors.RESET}")
        import traceback
        print(f"{Colors.RED}   {traceback.format_exc()}{Colors.RESET}")
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
