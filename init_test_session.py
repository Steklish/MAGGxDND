"""
Script to initialize a test session with real data
Run this after starting the server to create a playable session
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def create_test_session():
    # Create session
    print("Creating session...")
    response = requests.post(
        f"{BASE_URL}/sessions",
        json={
            "session_name": "Test Adventure",
            "game_mode": "STORY",
            "max_players": 5
        }
    )
    session_data = response.json()
    session_id = session_data["session_id"]
    print(f"Session created: {session_id}")
    
    # Start session with initial data
    print("Starting session with characters and scene...")
    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/start",
        json={
            "scene_prompt": "A dark tavern called 'The Drunken Dragon'. Dim candlelight flickers across worn wooden tables. The air smells of ale and roasted meat. A few patrons sit in the corners, whispering among themselves.",
            "character_prompts": [
                "Ogorek, a human wizard seeking ancient knowledge. Intelligent and curious.",
                "Notman, a dwarf fighter with a mysterious past. Stoic and loyal."
            ],
            "npc_prompts": [
                "Worm, an aberration peasant lurking in the shadows. Evil and cunning."
            ]
        }
    )
    
    if response.status_code == 200:
        print(f"Session started successfully!")
        print(f"Session ID: {session_id}")
        
        # Get session info
        response = requests.get(f"{BASE_URL}/sessions/{session_id}")
        print(f"Session info: {json.dumps(response.json(), indent=2)}")
        
        # Join as player
        print("\nJoining as player...")
        response = requests.post(
            f"{BASE_URL}/sessions/{session_id}/players",
            json={
                "player_name": "TestPlayer",
                "character_name": "Ogorek"
            }
        )
        player_data = response.json()
        player_id = player_data["player_id"]
        print(f"Player ID: {player_id}")
        
        print(f"\n=== CONNECTION INFO ===")
        print(f"Session ID: {session_id}")
        print(f"Player ID: {player_id}")
        print(f"WebSocket: ws://localhost:8000/ws/{session_id}/{player_id}")
        print(f"UI: http://localhost:8000")
        print("========================\n")
        
        return session_id, player_id
    else:
        print(f"Error starting session: {response.text}")
        return None, None

if __name__ == "__main__":
    create_test_session()
