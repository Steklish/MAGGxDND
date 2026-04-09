"""
Test script to verify personality_traits parsing fix.
"""
import json
from backend.src.schema.character_profile import CharacterProfileResponse
from datetime import datetime

# Test case 1: JSON string (dict format) - this was causing the error
test_data_1 = {
    "id": 1,
    "user_id": 1,
    "name": "Test Character",
    "race": "Human",
    "char_class": "Fighter",
    "level": 1,
    "backstory_summary": "A brave warrior",
    "personality_traits": '{"trait":"fs","ideal":"f","bond":"sf","flaw":"sf"}',
    "appearance_description": "Tall and strong",
    "background": "Soldier",
    "alignment": "Lawful Good",
    "max_hp": 12,
    "armor_class": 16,
    "speed": 30,
    "is_favorite": False,
    "character_data": None,
    "created_at": datetime.now(),
    "updated_at": datetime.now()
}

print("Test 1: JSON string (dict format)")
try:
    profile1 = CharacterProfileResponse(**test_data_1)
    print(f"  ✅ Success!")
    print(f"  personality_traits: {profile1.personality_traits}")
    assert isinstance(profile1.personality_traits, list), "Should be a list"
    assert "trait: fs" in profile1.personality_traits[0], "Should contain formatted trait"
    print(f"  ✅ Validation passed!")
except Exception as e:
    print(f"  ❌ Failed: {e}")

# Test case 2: JSON string (list format)
test_data_2 = test_data_1.copy()
test_data_2["id"] = 2
test_data_2["personality_traits"] = '["Brave", "Honest", "Loyal"]'

print("\nTest 2: JSON string (list format)")
try:
    profile2 = CharacterProfileResponse(**test_data_2)
    print(f"  ✅ Success!")
    print(f"  personality_traits: {profile2.personality_traits}")
    assert profile2.personality_traits == ["Brave", "Honest", "Loyal"], "Should parse list correctly"
    print(f"  ✅ Validation passed!")
except Exception as e:
    print(f"  ❌ Failed: {e}")

# Test case 3: Already a list (from ORM)
test_data_3 = test_data_1.copy()
test_data_3["id"] = 3
test_data_3["personality_traits"] = ["Courageous", "Wise"]

print("\nTest 3: Already a list")
try:
    profile3 = CharacterProfileResponse(**test_data_3)
    print(f"  ✅ Success!")
    print(f"  personality_traits: {profile3.personality_traits}")
    assert profile3.personality_traits == ["Courageous", "Wise"], "Should keep list as-is"
    print(f"  ✅ Validation passed!")
except Exception as e:
    print(f"  ❌ Failed: {e}")

# Test case 4: None value
test_data_4 = test_data_1.copy()
test_data_4["id"] = 4
test_data_4["personality_traits"] = None

print("\nTest 4: None value")
try:
    profile4 = CharacterProfileResponse(**test_data_4)
    print(f"  ✅ Success!")
    print(f"  personality_traits: {profile4.personality_traits}")
    assert profile4.personality_traits is None, "Should be None"
    print(f"  ✅ Validation passed!")
except Exception as e:
    print(f"  ❌ Failed: {e}")

# Test case 5: Invalid JSON (fallback)
test_data_5 = test_data_1.copy()
test_data_5["id"] = 5
test_data_5["personality_traits"] = "Just a plain text trait"

print("\nTest 5: Invalid JSON (fallback to single-item list)")
try:
    profile5 = CharacterProfileResponse(**test_data_5)
    print(f"  ✅ Success!")
    print(f"  personality_traits: {profile5.personality_traits}")
    assert profile5.personality_traits == ["Just a plain text trait"], "Should wrap in list"
    print(f"  ✅ Validation passed!")
except Exception as e:
    print(f"  ❌ Failed: {e}")

print("\n" + "="*60)
print("All tests passed! ✅")
print("="*60)
