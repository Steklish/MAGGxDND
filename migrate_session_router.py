"""
Migration script to update session_router.py for new database schema.

This script will:
1. Replace all participant attribute accesses with dict .get() calls
2. Remove AIGameService references and replace with delivery calls
3. Update session creation to use new simplified schema

Run this script from the project root:
python migrate_session_router.py
"""

import re
from pathlib import Path

SESSION_ROUTER_PATH = Path("D:/Duty/MAGGxDND/backend/src/api/routers/session_router.py")

def fix_participant_attribute_accesses(content: str) -> str:
    """Replace participant.attribute with participant.get('attribute')"""
    
    # Pattern to match participant attribute access
    # Matches: p.player_uuid, p.player_name, p.is_connected, etc.
    participant_attrs = [
        'player_uuid', 'player_name', 'is_connected', 'user_id', 
        'character_name', 'role', 'character_id', 'joined_at', 
        'last_active_at'
    ]
    
    for attr in participant_attrs:
        # Match patterns like: p.attr, participant.attr
        # But NOT: p.get('attr'), participant.get('attr')
        pattern = rf'(\w+)\.{attr}(?!\s*\()'
        replacement = rf"\1.get('{attr}')"
        content = re.sub(pattern, replacement, content)
    
    return content


def remove_ai_game_service(content: str) -> str:
    """Remove AIGameService imports and usage"""
    
    # Remove import
    content = re.sub(
        r'\s*from backend\.src\.services\.ai_game_service import AIGameService\n',
        '',
        content
    )
    
    # Replace ai_service = AIGameService(game_session)
    content = re.sub(
        r'\s*ai_service = AIGameService\(game_session\)',
        '\n        # Using delivery directly for game communication\n        pass',
        content
    )
    
    return content


def update_session_creation(content: str) -> str:
    """Update session creation to use new simplified schema"""
    
    # Replace repository.create_session calls that use old fields
    # Remove: max_players, description, guide, gemini_model from DB create
    # These should be in session_data JSON instead
    
    # Find and update the create_session call in create_session endpoint
    old_create = r'''repository\.create_session\(
            session_uuid=session_uuid,
            session_name=request\.session_name,
            owner_id=current_user\.id,
            game_mode=request\.game_mode,
            max_players=request\.max_players,
            description=request\.description,
            guide=request\.guide,
            gemini_model=request\.gemini_model
        \)'''
    
    new_create = '''repository.create_session(
            session_uuid=session_uuid,
            session_name=request.session_name,
            owner_id=current_user.id,
            game_mode=request.game_mode,
            session_data={
                "max_players": request.max_players,
                "description": request.description,
                "guide": request.guide,
                "gemini_model": request.gemini_model,
                "participants": []
            }
        )'''
    
    content = re.sub(old_create, new_create, content, flags=re.MULTILINE)
    
    return content


def update_session_update_endpoint(content: str) -> str:
    """Update session update to use session_data JSON"""
    
    # Replace direct field updates with session_data updates
    old_updates = [
        (r'db_session\.max_players = request\.max_players', 
         '# max_players now in session_data'),
        (r'db_session\.description = request\.description',
         '# description now in session_data'),
        (r'db_session\.guide = request\.guide',
         '# guide now in session_data'),
        (r'db_session\.is_public = request\.is_public',
         '# is_public now in session_data'),
    ]
    
    for old, new in old_updates:
        content = re.sub(old, new, content)
    
    return content


def main():
    print("=" * 80)
    print("MIGRATION SCRIPT: session_router.py")
    print("=" * 80)
    
    if not SESSION_ROUTER_PATH.exists():
        print(f"❌ File not found: {SESSION_ROUTER_PATH}")
        return
    
    print(f"📄 Reading: {SESSION_ROUTER_PATH}")
    content = SESSION_ROUTER_PATH.read_text(encoding='utf-8')
    original_content = content
    
    # Apply fixes
    print("\n🔧 Applying fixes...")
    
    print("  1. Fixing participant attribute accesses...")
    content = fix_participant_attribute_accesses(content)
    
    print("  2. Removing AIGameService references...")
    content = remove_ai_game_service(content)
    
    print("  3. Updating session creation...")
    content = update_session_creation(content)
    
    print("  4. Updating session update endpoint...")
    content = update_session_update_endpoint(content)
    
    # Check if changes were made
    if content == original_content:
        print("\n⚠️  No changes detected. File may already be migrated.")
        return
    
    # Write backup
    backup_path = SESSION_ROUTER_PATH.with_suffix('.py.bak')
    print(f"\n💾 Creating backup: {backup_path}")
    backup_path.write_text(original_content, encoding='utf-8')
    
    # Write updated file
    print(f"✍️  Writing updated file: {SESSION_ROUTER_PATH}")
    SESSION_ROUTER_PATH.write_text(content, encoding='utf-8')
    
    print("\n" + "=" * 80)
    print("✅ MIGRATION COMPLETE")
    print("=" * 80)
    print("\n⚠️  IMPORTANT: Review the changes before running the server!")
    print("   - Check that all participant accesses use .get() method")
    print("   - Verify session creation uses session_data JSON")
    print("   - Test endpoints manually after migration")
    print("\n📝 A backup was created at:")
    print(f"   {backup_path}")


if __name__ == "__main__":
    main()
