"""
Live integration test for MAGGxDND server:
- Combat mode switching (STORY <-> COMBAT)
- Scene transitions (location_graph & transition_to_location)
- Multi-player concurrent WebSocket synchronization
"""
import asyncio
import json
import httpx
import websockets

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"


async def run_live_test():
    print("=" * 60)
    print("MAGGxDND LIVE INTEGRATION TEST")
    print("=" * 60)

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # 1. Login / Auth
        print("\n1. Authenticating as test user...")
        # Try login or register test user
        username = "tester_multimode"
        password = "TestPassword123!"
        reg_resp = await client.post("/api/v1/auth/register", json={
            "username": username,
            "email": "tester_multimode@example.com",
            "password": password
        })
        if reg_resp.status_code in [200, 201]:
            token = reg_resp.json().get("access_token")
            user_id = reg_resp.json().get("id")
        else:
            # Login if already registered
            login_resp = await client.post("/api/v1/auth/token", data={
                "username": username,
                "password": password
            })
            if login_resp.status_code != 200:
                # Fallback to guest login
                guest_resp = await client.post("/api/v1/auth/guest", json={"username": username})
                token = guest_resp.json()["access_token"]
                user_id = guest_resp.json().get("user_id") or guest_resp.json().get("id", 1)
            else:
                token = login_resp.json()["access_token"]
                user_id = login_resp.json().get("user_id", 1)

        headers = {"Authorization": f"Bearer {token}"}
        print(f"✓ Authenticated. User ID: {user_id}")

        # 2. Create or find game session
        print("\n2. Setting up test session...")
        session_id = None
        list_resp = await client.get("/api/v1/sessions", headers=headers, timeout=10.0)
        if list_resp.status_code == 200:
            sessions = list_resp.json().get("sessions", [])
            if sessions:
                session_id = sessions[0]["session_id"]
                session_name = sessions[0]["session_name"]
                print(f"✓ Reusing existing active session: {session_id} - '{session_name}'")

        if not session_id:
            create_resp = await client.post("/api/v1/sessions", headers=headers, timeout=120.0, json={
                "session_name": "Tactical Multi-Player Chamber",
                "game_mode": "STORY",
                "language": "en",
                "description": "An ancient subterranean dungeon with heavy stone arches.",
                "max_players": 4
            })
            assert create_resp.status_code in [200, 201], f"Failed to create session: {create_resp.text}"
            session_data = create_resp.json()
            session_id = session_data["session_id"]
            print(f"✓ Session created: {session_id} - '{session_data['session_name']}'")

        # 3. Add or retrieve two players in the session
        print("\n3. Setting up two characters for the session roster...")
        # Check existing participants
        detail_resp = await client.get(f"/api/v1/sessions/{session_id}", headers=headers, timeout=10.0)
        existing_players = []
        if detail_resp.status_code == 200:
            existing_players = detail_resp.json().get("players", [])

        if len(existing_players) >= 2:
            p1_id = existing_players[0].get("player_uuid") or str(existing_players[0].get("id"))
            p1_char = existing_players[0].get("character_name") or existing_players[0].get("name") or "Player 1"
            p2_id = existing_players[1].get("player_uuid") or str(existing_players[1].get("id"))
            p2_char = existing_players[1].get("character_name") or existing_players[1].get("name") or "Player 2"
            print(f"✓ Using existing participant 1: {p1_id} ({p1_char})")
            print(f"✓ Using existing participant 2: {p2_id} ({p2_char})")
        else:
            p1_resp = await client.post(f"/api/v1/sessions/{session_id}/players/random", headers=headers, timeout=60.0, json={
                "player_name": "Valeros"
            })
            assert p1_resp.status_code in [200, 201], f"Failed to add player 1: {p1_resp.text}"
            p1_id = p1_resp.json()["player_uuid"]
            p1_char = p1_resp.json()["character_name"]
            print(f"✓ Player 1 enrolled: UUID {p1_id}, Character: {p1_char}")

            p2_resp = await client.post(f"/api/v1/sessions/{session_id}/players/random", headers=headers, timeout=60.0, json={
                "player_name": "Kyra"
            })
            assert p2_resp.status_code in [200, 201], f"Failed to add player 2: {p2_resp.text}"
            p2_id = p2_resp.json()["player_uuid"]
            p2_char = p2_resp.json()["character_name"]
            print(f"✓ Player 2 enrolled: UUID {p2_id}, Character: {p2_char}")

        # 4. Multi-Player Concurrent WebSocket Connections
        print("\n4. Connecting both players concurrently via WebSocket...")
        p1_ws_url = f"{WS_URL}/ws/{session_id}/{p1_id}"
        p2_ws_url = f"{WS_URL}/ws/{session_id}/{p2_id}"

        async with websockets.connect(p1_ws_url) as ws1, websockets.connect(p2_ws_url) as ws2:
            print("✓ Both WebSocket connections established!")

            # Receive initial messages on ws1
            msg1 = json.loads(await ws1.recv())
            assert msg1.get("type") in ["CONNECTED", "SESSION_UPDATE"]
            print(f"✓ Player 1 handshake received: {msg1.get('type')}")

            msg2 = json.loads(await ws2.recv())
            assert msg2.get("type") in ["CONNECTED", "SESSION_UPDATE"]
            print(f"✓ Player 2 handshake received: {msg2.get('type')}")

            # Check session state update on ws1
            session_state = None
            for _ in range(3):
                raw = await ws1.recv()
                data = json.loads(raw)
                if data.get("type") == "SESSION_UPDATE":
                    session_state = data.get("payload", {}).get("session") or data.get("session")
                    break

            if session_state:
                print(f"✓ Initial Game Mode: {session_state.get('game_mode')}")
                assert session_state.get("game_mode") == "STORY", "Initial mode should be STORY"
                
                # Check turn_queue schema normalization
                tq = session_state.get("turn_queue", [])
                print(f"✓ Turn queue received: {len(tq)} entries")
                if tq:
                    sample = tq[0]
                    assert isinstance(sample, dict), f"Turn queue entry should be dict, got {type(sample)}"
                    assert "character" in sample, "Turn queue entry must contain 'character' field"
                    assert "next_turn" in sample, "Turn queue entry must contain 'next_turn' field"
                    print(f"✓ Turn queue schema verified: character='{sample['character']}', next_turn={sample['next_turn']}")

            # 5. Test Multi-Player Chat Broadcast
            print("\n5. Testing Multi-Player real-time chat broadcast...")
            chat_text = "I stand by your side with shield raised!"
            await ws1.send(json.dumps({
                "type": "PLAYER_MESSAGE",
                "payload": {
                    "sender_name": p1_char,
                    "text": chat_text
                }
            }))
            print(f"✓ Player 1 ({p1_char}) sent chat message")

            # Player 2 must receive it
            received_chat = False
            for _ in range(5):
                raw = await asyncio.wait_for(ws2.recv(), timeout=5.0)
                data = json.loads(raw)
                if data.get("type") == "PLAYER_MESSAGE" and data.get("payload", {}).get("text") == chat_text:
                    received_chat = True
                    print(f"✓ Player 2 ({p2_char}) received broadcast from {data.get('payload', {}).get('sender_name')}: '{chat_text}'")
                    break
            assert received_chat, "Player 2 failed to receive chat broadcast from Player 1!"

            # 6. Test Combat Mode Switching (STORY -> COMBAT -> STORY)
            print("\n6. Testing Combat Mode Switching...")
            # Trigger combat mode
            await ws1.send(json.dumps({
                "type": "ENTER_COMBAT",
                "payload": {
                    "reason": "Hostile guardians attack from the shadows!"
                }
            }))
            print("✓ Player 1 sent ENTER_COMBAT packet")

            # Check Player 1 received confirmation
            mode_changed_p1 = False
            for _ in range(5):
                raw = await asyncio.wait_for(ws1.recv(), timeout=5.0)
                data = json.loads(raw)
                if data.get("type") == "GAME_MODE_CHANGED":
                    assert data.get("game_mode") == "COMBAT"
                    mode_changed_p1 = True
                    print("✓ Player 1 received GAME_MODE_CHANGED: COMBAT")
                    break
            assert mode_changed_p1, "Player 1 did not receive GAME_MODE_CHANGED"

            # Check Player 2 received combat announcement or session update
            mode_changed_p2 = False
            for _ in range(5):
                raw = await asyncio.wait_for(ws2.recv(), timeout=5.0)
                data = json.loads(raw)
                if data.get("type") == "SESSION_UPDATE":
                    curr_mode = (data.get("payload", {}).get("session") or data.get("session", {})).get("game_mode")
                    if curr_mode == "COMBAT":
                        mode_changed_p2 = True
                        print("✓ Player 2 received SESSION_UPDATE reflecting COMBAT mode!")
                        break
                elif data.get("type") == "MASTER_MESSAGE" and "COMBAT" in (data.get("payload", {}).get("text") or data.get("text", "")):
                    mode_changed_p2 = True
                    print("✓ Player 2 received Master combat broadcast!")
                    break

            # Now return to story mode
            await ws1.send(json.dumps({
                "type": "EXIT_COMBAT",
                "payload": {
                    "reason": "Threats neutralized"
                }
            }))
            print("✓ Player 1 sent EXIT_COMBAT packet")

            mode_restored = False
            for _ in range(5):
                raw = await asyncio.wait_for(ws1.recv(), timeout=5.0)
                data = json.loads(raw)
                if data.get("type") == "GAME_MODE_CHANGED":
                    assert data.get("game_mode") == "STORY"
                    mode_restored = True
                    print("✓ Player 1 received GAME_MODE_CHANGED: STORY")
                    break
            assert mode_restored, "Player 1 did not receive STORY mode restoration"

            # 7. Test Scene / Location Transitions
            print("\n7. Testing Scene / Location Transition Mechanism...")
            target_scene = "Sunken Crypt of Elders"
            target_desc = "A flooded sepulcher with weathered sarcophagi reflecting blue phosphorescent moss."
            await ws1.send(json.dumps({
                "type": "TRANSITION_LOCATION",
                "payload": {
                    "location_name": target_scene,
                    "description": target_desc
                }
            }))
            print(f"✓ Player 1 sent TRANSITION_LOCATION to '{target_scene}'")

            # Check location transition acknowledgment on ws1
            loc_trans_ack = False
            for _ in range(5):
                raw = await asyncio.wait_for(ws1.recv(), timeout=10.0)
                data = json.loads(raw)
                if data.get("type") == "LOCATION_TRANSITIONED":
                    assert data.get("location_name") == target_scene
                    loc_trans_ack = True
                    print(f"✓ Player 1 received LOCATION_TRANSITIONED: {target_scene}")
                    break
            assert loc_trans_ack, "Player 1 did not receive LOCATION_TRANSITIONED"

            # Check Player 2 received SESSION_UPDATE or SCENE_UPDATE with new scene
            p2_scene_synced = False
            for _ in range(5):
                raw = await asyncio.wait_for(ws2.recv(), timeout=10.0)
                data = json.loads(raw)
                if data.get("type") == "SESSION_UPDATE":
                    curr_loc = (data.get("payload", {}).get("session") or data.get("session", {})).get("current_location_name")
                    if curr_loc == target_scene:
                        p2_scene_synced = True
                        print(f"✓ Player 2 received SESSION_UPDATE: current_location_name = '{curr_loc}'")
                        break
                elif data.get("type") == "MASTER_MESSAGE" and target_scene in (data.get("payload", {}).get("text") or data.get("text", "")):
                    p2_scene_synced = True
                    print(f"✓ Player 2 received DM narration for transition to '{target_scene}'")
                    break

            assert p2_scene_synced, "Player 2 failed to synchronize to the new scene!"

    print("\n" + "=" * 60)
    print("🎉 ALL LIVE INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_live_test())
