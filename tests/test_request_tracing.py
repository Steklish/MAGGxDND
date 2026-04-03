"""
Test script to demonstrate request tracing

Run this after starting the server to see request tracing in action.
"""
import requests
import json
import sys
from pathlib import Path

# Resolve paths relative to this script's directory
TESTS_DIR = Path(__file__).resolve().parent
TEST_DB_FILE = TESTS_DIR / "test_db.txt"

BASE_URL = "http://localhost:8000"

print("="*70)
print("MAGGxDND Request Tracing Demo")
print("="*70)
print()

# Test 1: Health Check (no auth required)
print("📤 TEST 1: Health Check")
print("-"*70)
try:
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"✅ Status: {response.status_code}")
    print(f"📦 Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("="*70)
print()

# Test 2: Register User
print("📤 TEST 2: Register New User")
print("-"*70)
test_user = {
    "username": f"testuser_{len(TEST_DB_FILE.read_text().splitlines()) if TEST_DB_FILE.exists() else 0}",
    "password": "testpass123"
}

try:
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json=test_user,
        timeout=5
    )
    print(f"✅ Status: {response.status_code}")
    if response.status_code == 200:
        print(f"📦 Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"⚠️  Response: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("="*70)
print()

# Test 3: Login
print("📤 TEST 3: Login")
print("-"*70)
try:
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={
            "username": test_user["username"],
            "password": test_user["password"]
        },
        timeout=5
    )
    print(f"✅ Status: {response.status_code}")
    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"🔑 Token: {token[:50]}...")
        
        # Save token for next tests
        with open("test_token.txt", "w") as f:
            f.write(token)
        print("💾 Token saved to test_token.txt")
    else:
        print(f"⚠️  Response: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("="*70)
print()

# Test 4: Create Session (requires auth)
print("📤 TEST 4: Create Session")
print("-"*70)
try:
    with open("test_token.txt", "r") as f:
        token = f.read().strip()
    
    cookies = {"access_token": token}
    
    session_data = {
        "session_name": f"Test Session {len(TEST_DB_FILE.read_text().splitlines()) if TEST_DB_FILE.exists() else 0}",
        "game_mode": "STORY",
        "max_players": 5,
        "description": "Test session for request tracing"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/sessions",
        json=session_data,
        cookies=cookies,
        timeout=60
    )
    
    print(f"✅ Status: {response.status_code}")
    if response.status_code == 201:
        print(f"📦 Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"⚠️  Response: {response.text}")
except FileNotFoundError:
    print("❌ No token found. Please run login test first.")
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("="*70)
print()

# Test 5: List Sessions
print("📤 TEST 5: List Sessions")
print("-"*70)
try:
    with open("test_token.txt", "r") as f:
        token = f.read().strip()
    
    cookies = {"access_token": token}
    
    response = requests.get(
        f"{BASE_URL}/api/v1/sessions",
        cookies=cookies,
        timeout=5
    )
    
    print(f"✅ Status: {response.status_code}")
    if response.status_code == 200:
        sessions = response.json()
        print(f"📦 Found {sessions.get('total', 0)} sessions")
        for session in sessions.get('sessions', []):
            print(f"   - {session['session_name']} (ID: {session['session_id'][:8]}...)")
    else:
        print(f"⚠️  Response: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("="*70)
print("Demo Complete!")
print("="*70)
print()
print("💡 Check the server console for detailed request tracing logs!")
print("   - Trace IDs")
print("   - Request/Response details")
print("   - Processing times")
print()
