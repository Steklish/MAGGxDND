import pytest
import asyncio
from unittest.mock import MagicMock
from backend.src.game.session_manager import SessionManager


@pytest.mark.asyncio
async def test_session_manager_disconnect_grace():
    sm = SessionManager()
    session_id = "test-grace-session"
    player_id = "test-player-1"

    # Mock Session
    mock_session = MagicMock()
    mock_session.session_name = "Grace Test Session"
    sm.register_session(session_id, mock_session)

    # Initial registration
    ws1 = MagicMock()
    await sm.register_player_websocket(session_id, player_id, ws1)
    assert sm.get_player_websocket(session_id, player_id) is ws1

    # Simulate player reconnecting with a new socket before the old socket finishes closing
    ws2 = MagicMock()
    await sm.register_player_websocket(session_id, player_id, ws2)
    assert sm.get_player_websocket(session_id, player_id) is ws2

    # Now the old socket finally cleans up, passing ws1
    # It must NOT unregister ws2!
    unreg_old = sm.unregister_player_websocket(session_id, player_id, websocket=ws1)
    assert unreg_old is False
    assert sm.get_player_websocket(session_id, player_id) is ws2

    # When ws2 unregisters, it should succeed
    unreg_new = sm.unregister_player_websocket(session_id, player_id, websocket=ws2)
    assert unreg_new is True
    assert sm.get_player_websocket(session_id, player_id) is None


@pytest.mark.asyncio
async def test_session_manager_grace_task_cancellation():
    sm = SessionManager()
    session_id = "test-grace-cancel-session"
    player_id = "test-player-2"

    mock_session = MagicMock()
    mock_session.session_name = "Grace Cancel Session"
    sm.register_session(session_id, mock_session)

    # Schedule a grace task
    grace_cancelled = False

    async def dummy_grace():
        nonlocal grace_cancelled
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            grace_cancelled = True
            raise

    task = asyncio.create_task(dummy_grace())
    await asyncio.sleep(0.01)
    sm.schedule_disconnect_grace(session_id, player_id, task)
    assert sm.is_player_in_grace(session_id, player_id) is True

    # Reconnect player -> should cancel the grace task
    ws3 = MagicMock()
    await sm.register_player_websocket(session_id, player_id, ws3)

    await asyncio.sleep(0.01)
    assert sm.is_player_in_grace(session_id, player_id) is False
    assert grace_cancelled is True
    assert task.cancelled() is True
