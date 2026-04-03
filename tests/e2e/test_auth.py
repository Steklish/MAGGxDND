import requests
import json

BASE_URL = "http://localhost:8000"

print("Testing Auth Endpoints...")
print("="*50)

# Test registration
print("\n1. Testing Registration...")
try:
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"username": "testuser123", "password": "testpass123"},
        timeout=5
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test login
print("\n2. Testing Login...")
try:
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login/json",
        json={"username": "testuser123", "password": "testpass123", "remember_me": False},
        timeout=5
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test health
print("\n3. Testing Health Check...")
try:
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*50)
print("Testing complete!")
