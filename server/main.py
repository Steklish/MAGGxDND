import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import os

# Get the directory of the current file (e.g., D:\...\MAGGxDND\server)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (the project root, e.g., D:\...\MAGGxDND)
project_root = os.path.dirname(current_dir)
# Add the project root to the Python path
sys.path.append(project_root)

# Now you can import from the project root
from game.engine import Session
from websocket.manager import ConnectionManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("server")

app = FastAPI(title="MAGGxDND Game Server")

# As per the documentation, add CORS middleware
# to allow connections from the Vite dev server.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import session_manager
manager = ConnectionManager()

@app.get("/")
async def read_root():
    return {"message": "MAGGxDND Game Server is running."}

from fastapi import WebSocket, WebSocketDisconnect
from websocket.handlers import handle_websocket_message, listen_for_events
import asyncio

# ... (inside main.py)

@app.websocket("/ws/{session_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, player_id: str):
    """Handle WebSocket connections for a specific player in a specific session."""
    client_id = f"{session_id}:{player_id}"
    await manager.connect(websocket, client_id)

    if session_id not in session_manager.sessions:
        logger.warning(f"Player {player_id} tried to connect to non-existent session {session_id}")
        await websocket.close(code=4004, reason="Session not found")
        return

    session = session_manager.sessions[session_id]
    delivery = session.delivery
    
    # Each player needs to subscribe to the event pool to get their own event queue
    event_queue = session.event_pool.subscribe(player_id)
    
    # Start the event listener as a background task
    listener_task = asyncio.create_task(
        listen_for_events(websocket, event_queue, client_id)
    )

    try:
        # Send initial session state upon connection
        delivery.session_updated(session)

        # Loop to process incoming messages from this client
        while True:
            data = await websocket.receive_json()
            await handle_websocket_message(
                data=data,
                session=session,
                delivery=delivery,
                player_id=player_id,
            )
    except WebSocketDisconnect:
        logger.info(f"Player {player_id} disconnected from session {session_id}")
    except Exception as e:
        logger.error(f"Error in WebSocket for {client_id}: {e}")
    finally:
        # Clean up on disconnect
        listener_task.cancel()
        manager.disconnect(client_id)
        session.event_pool.unsubscribe(player_id)
        logger.info(f"Cleaned up resources for {client_id}")


from routes import sessions as session_router

# REST API routers will be added here later.
app.include_router(session_router.router)


# To run the server, use the following command in your terminal
# in the D:\Lectures\SDLC\MAGGxDND\UI\server directory:
# uvicorn main:app --reload --port 8000
