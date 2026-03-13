import requests
import json

BASE_URL = "http://localhost:8000"

print("Testing Auth API from Browser Perspective...")
print("="*60)

# Test registration with new user
print("\n1. Testing Registration (new user)...")
try:
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"username": "newusertest", "password": "testpass123"},
        timeout=5
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Success! User ID: {data.get('user_id')}, Username: {data.get('username')}")
        print(f"   Token: {data.get('access_token')[:50]}...")
    else:
        print(f"   ❌ Error: {response.text}")
except Exception as e:
    print(f"   ❌ Exception: {e}")

# Test login
print("\n2. Testing Login...")
try:
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login/json",
        json={"username": "newusertest", "password": "testpass123", "remember_me": False},
        timeout=5
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Success! Token: {data.get('access_token')[:50]}...")
    else:
        print(f"   ❌ Error: {response.text}")
except Exception as e:
    print(f"   ❌ Exception: {e}")

# Test health
print("\n3. Testing Health...")
try:
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"   ❌ Exception: {e}")

print("\n" + "="*60)
print("API Test Complete!")
print("\n📝 NOTE: If API works here but not in browser, try:")
print("   1. Hard refresh: Ctrl+F5")
print("   2. Clear browser cache")
print("   3. Check browser console for errors")
