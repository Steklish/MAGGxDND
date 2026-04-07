"""
Verification script for database and architecture rework.

Checks that all critical components are properly integrated.
Run this before starting the server to catch import/link errors.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path("D:/Duty/MAGGxDND")
sys.path.insert(0, str(PROJECT_ROOT))

def check_import(module_path: str, description: str) -> bool:
    """Try to import a module and report status."""
    try:
        __import__(module_path)
        print(f"✅ {description}: {module_path}")
        return True
    except Exception as e:
        print(f"❌ {description}: {module_path}")
        print(f"   Error: {e}")
        return False


def check_file_exists(file_path: Path, description: str) -> bool:
    """Check if a file exists."""
    if file_path.exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} NOT FOUND")
        return False


def main():
    print("=" * 80)
    print("ARCHITECTURE VERIFICATION")
    print("=" * 80)
    print()
    
    all_passed = True
    
    # 1. Check database models
    print("\n📦 Database Models:")
    all_passed &= check_import("backend.src.models.user", "User model")
    all_passed &= check_import("backend.src.models.session", "Session model")
    
    # 2. Check routers
    print("\n🌐 API Routers:")
    all_passed &= check_file_exists(
        PROJECT_ROOT / "backend/src/api/routers/character.py",
        "Character router"
    )
    all_passed &= check_file_exists(
        PROJECT_ROOT / "backend/src/api/routers/profile.py",
        "Profile router"
    )
    all_passed &= check_import("backend.src.api.routers.session_router", "Session router")
    all_passed &= check_import("backend.src.api.routers.websocket_game", "WebSocket router")
    
    # 3. Check delivery
    print("\n📡 Delivery System:")
    all_passed &= check_import("backend.src.delivery.game_delivery", "Game delivery")
    
    # 4. Check repositories
    print("\n🗄️  Repositories:")
    all_passed &= check_import("backend.src.repositories.session_repository", "Session repository")
    
    # 5. Check game components
    print("\n🎮 Game Components:")
    all_passed &= check_import("backend.src.game.session_manager", "Session manager")
    all_passed &= check_import("backend.src.game.session_factory", "Session factory")
    
    # 6. Verify no old model imports
    print("\n🔍 Checking for removed model imports...")
    session_router_path = PROJECT_ROOT / "backend/src/api/routers/session_router.py"
    if session_router_path.exists():
        content = session_router_path.read_text(encoding='utf-8')
        
        removed_imports = [
            "SessionParticipant",
            "SessionSave",
            "SessionCharacter",
            "CharacterModel",
            "AIGameService"
        ]
        
        for removed in removed_imports:
            if removed in content:
                print(f"⚠️  Found reference to removed component: {removed}")
                all_passed = False
            else:
                print(f"✅ No reference to {removed}")
    
    # 7. Check database file
    print("\n💾 Database:")
    db_path = PROJECT_ROOT / "data/maggxdnd.db"
    if db_path.exists():
        print(f"⚠️  Old database exists: {db_path}")
        print(f"   Consider deleting it to recreate with new schema:")
        print(f"   del {db_path}")
    else:
        print(f"✅ No old database found (will be created on first run)")
    
    # 8. Summary
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALL CHECKS PASSED")
        print("=" * 80)
        print("\n🚀 Ready to start the server!")
        print("   python start.py")
        print("\n📝 Note: Delete old database if it exists before first run:")
        print("   del D:\\Duty\\MAGGxDND\\data\\maggxdnd.db")
    else:
        print("❌ SOME CHECKS FAILED")
        print("=" * 80)
        print("\n⚠️  Please fix the errors above before starting the server")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
