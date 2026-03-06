"""
Test script for MAGGxDND Full Stack
Tests the real game session creation
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test server health."""
    print("\n=== Testing Health ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_create_user():
    """Create a test user."""
    print("\n=== Creating User ===")
    response = requests.post(
        f"{BASE_URL}/api/v1/users",
        json={"username": "testplayer", "password": "test123"}
    )
    print(f"Status: {response.status_code}")
    if response.status_code in [200, 400]:  # 400 = user exists
        print(f"Response: {response.json()}")
        return True
    return False

def test_login():
    """Login and get token."""
    print("\n=== Logging In ===")
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={"username": "testplayer", "password": "test123"}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Token: {data['access_token'][:50]}...")
        return data['access_token']
    return None

def test_start_real_game():
    """Start a REAL game session."""
    print("\n=== Starting REAL Game Session ===")
    
    # Get API key from environment or use placeholder
    import os
    gemini_api_key = os.getenv("GEMINI_API_KEY", "NO_KEY")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/sessions/start_real_game",
        json={
            "session_name": "Test Adventure",
            "game_mode": "STORY",
            "scene_prompt": "A cozy tavern called 'The Sleeping Dragon' with a warm fireplace and friendly bartender",
            "character_prompts": [
                "A human wizard named Gandor with a long beard and blue robes, knows fireball spell",
                "A dwarf fighter named Thorin Ironforge with battle axe and shield, brave warrior"
            ],
            "npc_prompts": [
                "A mysterious hooded figure sitting in the corner, watching everyone"
            ],
            "gemini_api_key": gemini_api_key
        }
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n✓ GAME STARTED!")
        print(f"  Session ID: {data['session_id']}")
        print(f"  Session Name: {data['session_name']}")
        print(f"  Scene: {data['scene']}")
        print(f"  Players: {', '.join(data['players'])}")
        print(f"  NPCs: {', '.join(data['npcs'])}")
        print(f"  Status: {data['status']}")
        return data
    else:
        print(f"Error: {response.text}")
        return None

def test_websocket(session_id, player_name):
    """Test WebSocket connection."""
    print(f"\n=== Testing WebSocket ===")
    print(f"Connecting to: ws://localhost:8000/ws/{session_id}/{player_name}")
    print("WebSocket testing requires manual verification or websockets library")
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("MAGGxDND Full Stack Test Suite")
    print("=" * 60)
    
    # Test 1: Health check
    if not test_health():
        print("\n[FAIL] Server health check failed!")
        print("Make sure the server is running:")
        print("  python server\\run_fullstack.py")
        return
    
    print("\n[OK] Server is healthy")
    
    # Test 2: Create user
    test_create_user()
    
    # Test 3: Login
    token = test_login()
    if not token:
        print("\n[FAIL] Login failed!")
        return
    
    print("\n[OK] Login successful")
    
    # Test 4: Start real game
    game_data = test_start_real_game()
    if not game_data:
        print("\n[FAIL] Failed to start game!")
        print("\nPossible issues:")
        print("  - GEMINI_API_KEY not set")
        print("  - Game engine initialization error")
        print("\nCheck logs: log\\fullstack_runner.log")
        return
    
    print("\n[OK] Real game session created!")
    
    # Test 5: WebSocket (info only)
    if game_data['players']:
        test_websocket(game_data['session_id'], game_data['players'][0])
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("[OK] Server health check passed")
    print("[OK] User authentication working")
    print("[OK] Real game session created with:")
    print(f"    - {len(game_data['players'])} player characters")
    print(f"    - {len(game_data['npcs'])} NPCs")
    print(f"    - Scene: {game_data['scene']}")
    print("\nGame loop is running in background!")
    print("\nNext steps:")
    print("  1. Open http://localhost:8000 in browser")
    print("  2. Login with: testplayer / test123")
    print("  3. Join the session or create new character")
    print("  4. Watch the game master narrate the story!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to server!")
        print("\nMake sure the server is running:")
        print("  cd C:\\VS_Code\\MAGGxDND\\UI")
        print("  python server\\run_fullstack.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
