"""
Test script to create a session and verify database persistence.
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_session_creation():
    # Step 1: Login to get token
    print("=" * 60)
    print("Step 1: Logging in...")
    
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    try:
        # Try to create a test user first (if not exists)
        print("Creating test user...")
        register_response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={
                "username": "testuser",
                "password": "testpass123"
            },
            timeout=5
        )
        print(f"Register response: {register_response.status_code}")
    except Exception as e:
        print(f"User creation failed or exists: {e}")
    
    # Login
    login_response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data=login_data,
        timeout=5
    )
    
    if login_response.status_code != 200:
        print(f"X Login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        print("\nNote: You may need to create a user first through the UI")
        return None
    
    token = login_response.json().get("access_token")
    print(f"OK Login successful! Token: {token[:50]}...")
    
    # Step 2: Create a session
    print("\n" + "=" * 60)
    print("Step 2: Creating session...")
    
    session_data = {
        "session_name": f"Test Session {__import__('time').time()}",
        "game_mode": "STORY",
        "max_players": 5,
        "description": "Test session for database persistence",
        "guide": None  # No guide to avoid AI generation
    }
    
    cookies = {"access_token": token}
    
    create_response = requests.post(
        f"{BASE_URL}/api/v1/sessions",
        json=session_data,
        cookies=cookies,
        timeout=60  # Increased timeout for AI generation
    )
    
    print(f"Create session status: {create_response.status_code}")
    
    if create_response.status_code != 201:
        print(f"X Session creation failed!")
        print(f"Response: {create_response.text}")
        return None
    
    session = create_response.json()
    print(f"OK Session created!")
    print(json.dumps(session, indent=2))
    
    session_id = session.get("session_id")
    
    # Step 3: Verify session is in database
    print("\n" + "=" * 60)
    print("Step 3: Verifying session in database...")
    
    # Get session from API
    get_response = requests.get(
        f"{BASE_URL}/api/v1/sessions/{session_id}",
        cookies=cookies,
        timeout=5
    )
    
    print(f"Get session status: {get_response.status_code}")
    
    if get_response.status_code != 200:
        print(f"X Failed to retrieve session!")
        print(f"Response: {get_response.text}")
        return None
    
    retrieved_session = get_response.json()
    print(f"OK Session retrieved from API:")
    print(json.dumps(retrieved_session, indent=2))
    
    # Step 4: List user's sessions
    print("\n" + "=" * 60)
    print("Step 4: Listing user's sessions...")
    
    list_response = requests.get(
        f"{BASE_URL}/api/v1/sessions",
        cookies=cookies,
        timeout=5
    )
    
    print(f"List sessions status: {list_response.status_code}")
    
    if list_response.status_code != 200:
        print(f"X Failed to list sessions!")
        print(f"Response: {list_response.text}")
        return None
    
    sessions_list = list_response.json()
    print(f"OK User sessions:")
    print(json.dumps(sessions_list, indent=2))
    
    # Step 5: Direct database check
    print("\n" + "=" * 60)
    print("Step 5: Direct database check...")
    
    import sqlite3
    conn = sqlite3.connect('maggxdnd.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM game_sessions WHERE session_uuid = ?", (session_id,))
    db_row = cursor.fetchone()
    
    if db_row:
        print(f"OK Session found in database!")
        print(f"   ID: {db_row['id']}")
        print(f"   UUID: {db_row['session_uuid']}")
        print(f"   Name: {db_row['session_name']}")
        print(f"   Owner ID: {db_row['owner_id']}")
        print(f"   Status: {db_row['status']}")
        print(f"   Created: {db_row['created_at']}")
    else:
        print(f"X Session NOT found in database!")
    
    # Check participants
    cursor.execute("""
        SELECT sp.*, u.username 
        FROM session_participants sp
        LEFT JOIN users u ON sp.user_id = u.id
        WHERE sp.session_id = (SELECT id FROM game_sessions WHERE session_uuid = ?)
    """, (session_id,))
    participants = cursor.fetchall()
    
    print(f"\nOK Participants ({len(participants)}):")
    for p in participants:
        print(f"   - {p['player_name']} (role: {p['role']}, user: {p['username']})")
    
    conn.close()
    
    return session_id

if __name__ == "__main__":
    print("MAGGxDND Session Persistence Test")
    print("=" * 60)
    
    try:
        session_id = test_session_creation()
        
        if session_id:
            print("\n" + "=" * 60)
            print("OK TEST PASSED: Session persisted successfully!")
            print(f"Session ID: {session_id}")
        else:
            print("\n" + "=" * 60)
            print("X TEST FAILED: Session was not persisted")
            
    except Exception as e:
        print(f"\nX ERROR: {e}")
        import traceback
        traceback.print_exc()
