"""
Test script for developer endpoints.

This script tests all the new dev endpoints to ensure they work correctly.
Run this while the server is running to verify the endpoints.
"""

import requests
import json
from typing import Optional

BASE_URL = "http://localhost:8000"


def test_dev_endpoints(token: Optional[str] = None):
    """
    Test all dev endpoints.
    
    Args:
        token: Optional access token. If not provided, will try to use cookies.
    """
    
    headers = {}
    cookies = {}
    
    # No auth needed for dev endpoints!
    print("=" * 80)
    print("DEVELOPER ENDPOINTS TEST")
    print("=" * 80)
    print("Note: No authentication required for dev endpoints!\n")
    
    # Test 1: Get all sessions
    print("\n1. Testing GET /api/v1/test/sessions")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/test/sessions", headers=headers, cookies=cookies)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Success: {data['total_sessions']} sessions found")
            if data['sessions']:
                print(f"   Sample session: {json.dumps(data['sessions'][0], indent=2)}")
        else:
            print(f"   ✗ Failed: {response.text}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 2: Get summary
    print("\n2. Testing GET /api/v1/test/summary")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/test/summary", headers=headers, cookies=cookies)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Success: {data['total_active_sessions']} sessions, {data['total_players_connected']} players")
        else:
            print(f"   ✗ Failed: {response.text}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # If we have sessions, test session-specific endpoints
    try:
        response = requests.get(f"{BASE_URL}/api/v1/test/sessions", headers=headers, cookies=cookies)
        if response.status_code == 200:
            sessions_data = response.json()
            if sessions_data['sessions']:
                session_id = sessions_data['sessions'][0]['session_id']
                
                # Test 3: Get session detail
                print(f"\n3. Testing GET /api/v1/test/sessions/{session_id}")
                try:
                    response = requests.get(f"{BASE_URL}/api/v1/test/sessions/{session_id}", headers=headers, cookies=cookies)
                    print(f"   Status: {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        print(f"   ✓ Success: {data['session_name']}")
                        print(f"   - Players: {data['player_count']}")
                        print(f"   - NPCs: {data['npc_count']}")
                        print(f"   - Messages: {data['message_count']}")
                        print(f"   - Events: {data['event_pool_size']}")
                    else:
                        print(f"   ✗ Failed: {response.text}")
                except Exception as e:
                    print(f"   ✗ Error: {e}")
                
                # Test 4: Get session players
                print(f"\n4. Testing GET /api/v1/test/sessions/{session_id}/players")
                try:
                    response = requests.get(f"{BASE_URL}/api/v1/test/sessions/{session_id}/players", headers=headers, cookies=cookies)
                    print(f"   Status: {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        print(f"   ✓ Success: {data['total_players']} players ({data['connected_players']} connected)")
                    else:
                        print(f"   ✗ Failed: {response.text}")
                except Exception as e:
                    print(f"   ✗ Error: {e}")
                
                # Test 5: Get session NPCs
                print(f"\n5. Testing GET /api/v1/test/sessions/{session_id}/npcs")
                try:
                    response = requests.get(f"{BASE_URL}/api/v1/test/sessions/{session_id}/npcs", headers=headers, cookies=cookies)
                    print(f"   Status: {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        print(f"   ✓ Success: {data['total_npcs']} NPCs")
                    else:
                        print(f"   ✗ Failed: {response.text}")
                except Exception as e:
                    print(f"   ✗ Error: {e}")
                
                # Test 6: Get session scene
                print(f"\n6. Testing GET /api/v1/test/sessions/{session_id}/scene")
                try:
                    response = requests.get(f"{BASE_URL}/api/v1/test/sessions/{session_id}/scene", headers=headers, cookies=cookies)
                    print(f"   Status: {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        print(f"   ✓ Success: {data['current_location']}")
                        print(f"   - Locations: {data['all_locations_count']}")
                    else:
                        print(f"   ✗ Failed: {response.text}")
                except Exception as e:
                    print(f"   ✗ Error: {e}")
                
                # Test 7: Get session messages
                print(f"\n7. Testing GET /api/v1/test/sessions/{session_id}/messages")
                try:
                    response = requests.get(f"{BASE_URL}/api/v1/test/sessions/{session_id}/messages", headers=headers, cookies=cookies)
                    print(f"   Status: {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        print(f"   ✓ Success: {data['messages_returned']} messages (of {data['total_messages']} total)")
                    else:
                        print(f"   ✗ Failed: {response.text}")
                except Exception as e:
                    print(f"   ✗ Error: {e}")
                
                # Test 8: Get session turn queue
                print(f"\n8. Testing GET /api/v1/test/sessions/{session_id}/turn-queue")
                try:
                    response = requests.get(f"{BASE_URL}/api/v1/test/sessions/{session_id}/turn-queue", headers=headers, cookies=cookies)
                    print(f"   Status: {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        print(f"   ✓ Success: Game mode = {data['game_mode']}")
                    else:
                        print(f"   ✗ Failed: {response.text}")
                except Exception as e:
                    print(f"   ✗ Error: {e}")
                
                # Test 9: Get session full state
                print(f"\n9. Testing GET /api/v1/test/sessions/{session_id}/full-state")
                try:
                    response = requests.get(f"{BASE_URL}/api/v1/test/sessions/{session_id}/full-state", headers=headers, cookies=cookies)
                    print(f"   Status: {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        print(f"   ✓ Success: Full state retrieved")
                    else:
                        print(f"   ✗ Failed: {response.text}")
                except Exception as e:
                    print(f"   ✗ Error: {e}")
                
                # Test 10: Get session event pool
                print(f"\n10. Testing GET /api/v1/test/sessions/{session_id}/event-pool")
                try:
                    response = requests.get(f"{BASE_URL}/api/v1/test/sessions/{session_id}/event-pool", headers=headers, cookies=cookies)
                    print(f"   Status: {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        print(f"   ✓ Success: {data['event_count']} events, {data['subscriber_count']} subscribers")
                    else:
                        print(f"   ✗ Failed: {response.text}")
                except Exception as e:
                    print(f"   ✗ Error: {e}")
                
                # Test 11: Non-existent session (should return 404)
                print(f"\n11. Testing GET /api/v1/test/sessions/non-existent (should 404)")
                try:
                    response = requests.get(f"{BASE_URL}/api/v1/test/sessions/non-existent", headers=headers, cookies=cookies)
                    print(f"   Status: {response.status_code}")
                    if response.status_code == 404:
                        print(f"   ✓ Success: Correctly returned 404")
                    else:
                        print(f"   ✗ Unexpected: {response.status_code}")
                except Exception as e:
                    print(f"   ✗ Error: {e}")
    
    except Exception as e:
        print(f"\n✗ Could not fetch sessions for testing: {e}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print("\nYou can also view interactive documentation at:")
    print(f"  - Swagger UI: {BASE_URL}/docs")
    print(f"  - ReDoc: {BASE_URL}/redoc")


if __name__ == "__main__":
    print("Starting dev endpoint tests...")
    print("Make sure the server is running first!")
    print("Start with: python start.py")
    print()
    
    # You can optionally pass a token here
    test_dev_endpoints(token=None)
