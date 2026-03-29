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
                timestamp = datetime.now().strftime('%H:%M:%S')

                # Log event being sent with journey info
                print(f"\n{Colors.GREEN}┌{'─' * 90}{Colors.RESET}")
                print(f"{Colors.GREEN}│{Colors.RESET} 📤 {Colors.BOLD}EVENT JOURNEY: STAGE 4/5{Colors.RESET}")
                print(f"{Colors.GREEN}├{'─' * 90}{Colors.RESET}")
                print(f"{Colors.GREEN}│{Colors.RESET}    Timestamp: {timestamp}")
                print(f"{Colors.GREEN}│{Colors.RESET}    Session: {session_id}")
                print(f"{Colors.GREEN}│{Colors.RESET}    Player: {player_id}")
                print(f"{Colors.GREEN}│{Colors.RESET}    Event Type: {Colors.YELLOW}{event.event_type}{Colors.RESET}")
                print(f"{Colors.GREEN}│{Colors.RESET}    Event Count: #{event_count}")
                print(f"{Colors.GREEN}│{Colors.RESET}    Journey Stage: {Colors.MAGENTA}Core Engine → EventPool → WebSocket{Colors.RESET}")
                print(f"{Colors.GREEN}│{Colors.RESET}    Next: {Colors.CYAN}WebSocket → Frontend{Colors.RESET}")
                print(f"{Colors.GREEN}└{'─' * 90}{Colors.RESET}\n")

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
    Получает события от клиента (действия игрока) и публикует их в EventPool.
    """
    try:
        while True:
            # Получаем сообщение от клиента
            data = await websocket.receive_json()

            # Log received WebSocket message with journey info
            timestamp = datetime.now().strftime('%H:%M:%S')
            event_type = data.get("event_type", "UNKNOWN")

            print(f"\n{Colors.CYAN}┌{'─' * 90}{Colors.RESET}")
            print(f"{Colors.CYAN}│{Colors.RESET} 📥 {Colors.BOLD}WS MESSAGE RECEIVED: STAGE 2/5{Colors.RESET}")
            print(f"{Colors.CYAN}├{'─' * 90}{Colors.RESET}")
            print(f"{Colors.CYAN}│{Colors.RESET}    Timestamp: {timestamp}")
            print(f"{Colors.CYAN}│{Colors.RESET}    Session: {session_id}")
            print(f"{Colors.CYAN}│{Colors.RESET}    Player: {player_id}")
            print(f"{Colors.CYAN}│{Colors.RESET}    Event Type: {Colors.YELLOW}{event_type}{Colors.RESET}")
            print(f"{Colors.CYAN}│{Colors.RESET}    Data: {Colors.BLUE}{json.dumps(data.get('data', {}), ensure_ascii=False)[:200]}{Colors.RESET}")
            print(f"{Colors.CYAN}│{Colors.RESET}    Journey Stage: {Colors.MAGENTA}Frontend → WebSocket → Backend{Colors.RESET}")
            print(f"{Colors.CYAN}│{Colors.RESET}    Next: {Colors.CYAN}Backend → Core Engine{Colors.RESET}")
            print(f"{Colors.CYAN}└{'─' * 90}{Colors.RESET}\n")

            # Создаём событие из действия игрока
            event_data = data.get("data", {})

            event = Event(
                event_type=event_type,
                data=event_data,
                source=player_id
            )

            # Публикуем событие другим игрокам в сессии
            await session_manager.broadcast_to_session(
                session_id=session_id,
                event=event,
                exclude_player_id=player_id
            )

            # Log broadcast with journey info
            print(f"\n{Colors.GREEN}┌{'─' * 90}{Colors.RESET}")
            print(f"{Colors.GREEN}│{Colors.RESET} 📤 {Colors.BOLD}EVENT PUBLISHED: STAGE 3/5{Colors.RESET}")
            print(f"{Colors.GREEN}├{'─' * 90}{Colors.RESET}")
            print(f"{Colors.GREEN}│{Colors.RESET}    Session: {session_id}")
            print(f"{Colors.GREEN}│{Colors.RESET}    Event Type: {Colors.YELLOW}{event_type}{Colors.RESET}")
            print(f"{Colors.GREEN}│{Colors.RESET}    Journey Stage: {Colors.MAGENTA}Backend → Core Engine → EventPool{Colors.RESET}")
            print(f"{Colors.GREEN}│{Colors.RESET}    Next: {Colors.CYAN}EventPool → WebSocket{Colors.RESET}")
            print(f"{Colors.GREEN}└{'─' * 90}{Colors.RESET}\n")

            # Также отправляем подтверждение отправителю
            await websocket.send_json({
                "type": "ACTION_CONFIRMED",
                "event": {
                    "event_type": event_type,
                    "data": event_data
                }
            })

            # Log confirmation sent
            print(f"\n{Colors.GREEN}│{Colors.RESET}    ✅ Confirmation sent to player {player_id}{Colors.RESET}\n")

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
    timestamp = datetime.now().strftime('%H:%M:%S')

    # Log connection attempt with journey info
    print(f"\n{Colors.MAGENTA}{'='*90}{Colors.RESET}")
    print(f"{Colors.MAGENTA}🔌 {Colors.BOLD}WEBSOCKET CONNECTION ATTEMPT: STAGE 1/5{Colors.RESET}")
    print(f"{Colors.MAGENTA}{'='*90}{Colors.RESET}")
    print(f"{Colors.MAGENTA}   Timestamp: {timestamp}{Colors.RESET}")
    print(f"{Colors.MAGENTA}   Session: {session_id}{Colors.RESET}")
    print(f"{Colors.MAGENTA}   Player: {player_id}{Colors.RESET}")
    print(f"{Colors.MAGENTA}   Journey: {Colors.CYAN}Frontend → WebSocket Server (START){Colors.RESET}")
    print(f"{Colors.MAGENTA}   Stage: {Colors.GREEN}1/5{Colors.RESET}")
    print(f"{Colors.MAGENTA}{'='*90}{Colors.RESET}\n")
    
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
    print(f"\n{Colors.GREEN}┌{'─' * 90}{Colors.RESET}")
    print(f"{Colors.GREEN}│{Colors.RESET} ✅ {Colors.BOLD}WEBSOCKET CONNECTED{Colors.RESET}")
    print(f"{Colors.GREEN}├{'─' * 90}{Colors.RESET}")
    print(f"{Colors.GREEN}│{Colors.RESET}    Player {player_id} CONNECTED to session {session_id}")
    print(f"{Colors.GREEN}│{Colors.RESET}    Journey Stage: {Colors.MAGENTA}Frontend → WebSocket → Backend (COMPLETE){Colors.RESET}")
    print(f"{Colors.GREEN}└{'─' * 90}{Colors.RESET}\n")
    
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
