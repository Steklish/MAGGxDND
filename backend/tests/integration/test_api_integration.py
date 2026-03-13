"""
Integration Tests for Authentication API
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.tests.conftest import create_test_user, cleanup_test_data


@pytest.mark.integration
class TestAuthAPIIntegration:
    """Integration tests for authentication endpoints"""
    
    def test_register_user(self, client: TestClient, test_user_data: dict):
        """Test user registration"""
        response = client.post('/api/v1/auth/register', json=test_user_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'access_token' in data
        assert 'user_id' in data
        assert data['username'] == test_user_data['username']
        assert 'token_type' in data
    
    def test_register_duplicate_username(self, client: TestClient, test_user_data: dict):
        """Test registration with duplicate username"""
        # First registration
        client.post('/api/v1/auth/register', json=test_user_data)
        
        # Second registration with same username
        response = client.post('/api/v1/auth/register', json=test_user_data)
        
        assert response.status_code == 400
        assert 'already taken' in response.json()['detail']
    
    def test_login_success(self, client: TestClient, test_user_data: dict):
        """Test successful login"""
        # Register user first
        client.post('/api/v1/auth/register', json=test_user_data)
        
        # Login
        response = client.post('/api/v1/auth/login/json', json={
            'username': test_user_data['username'],
            'password': test_user_data['password'],
            'remember_me': False
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'access_token' in data
        assert data['username'] == test_user_data['username']
        assert data['is_guest'] is False
    
    def test_login_wrong_password(self, client: TestClient, test_user_data: dict):
        """Test login with wrong password"""
        # Register user
        client.post('/api/v1/auth/register', json=test_user_data)
        
        # Try login with wrong password
        response = client.post('/api/v1/auth/login/json', json={
            'username': test_user_data['username'],
            'password': 'WrongPassword123',
            'remember_me': False
        })
        
        assert response.status_code == 401
        assert 'Incorrect username or password' in response.json()['detail']
    
    def test_guest_login(self, client: TestClient):
        """Test guest login"""
        response = client.post('/api/v1/auth/guest')
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'access_token' in data
        assert data['is_guest'] is True
    
    def test_logout(self, client: TestClient, test_user_data: dict, auth_headers: dict):
        """Test logout"""
        response = client.post('/api/v1/auth/logout')
        
        assert response.status_code == 200
        assert 'Successfully logged out' in response.json()['detail']
    
    def test_get_current_user(self, client: TestClient, auth_headers: dict):
        """Test getting current user info"""
        response = client.get('/api/v1/auth/me', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'username' in data
        assert 'is_guest' in data
    
    def test_get_current_user_unauthorized(self, client: TestClient):
        """Test getting current user without auth"""
        response = client.get('/api/v1/auth/me')
        
        assert response.status_code == 401


@pytest.mark.integration
class TestCharacterAPIIntegration:
    """Integration tests for character endpoints"""
    
    def test_create_character(self, client: TestClient, auth_headers: dict, test_character_data: dict):
        """Test character creation"""
        response = client.post(
            '/api/v1/characters/',
            json=test_character_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['name'] == test_character_data['name']
        assert data['race'] == test_character_data['race']
        assert data['char_class'] == test_character_data['char_class']
        assert 'id' in data
    
    def test_get_user_characters(self, client: TestClient, auth_headers: dict, test_character_data: dict):
        """Test getting user's characters"""
        # Create character
        client.post('/api/v1/characters/', json=test_character_data, headers=auth_headers)
        
        # Get characters
        response = client.get('/api/v1/characters/user/1', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(char['name'] == test_character_data['name'] for char in data)
    
    def test_get_character_by_id(self, client: TestClient, auth_headers: dict, test_character_data: dict):
        """Test getting character by ID"""
        # Create character
        create_response = client.post(
            '/api/v1/characters/',
            json=test_character_data,
            headers=auth_headers
        )
        character_id = create_response.json()['id']
        
        # Get character
        response = client.get(f'/api/v1/characters/{character_id}', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['id'] == character_id
        assert data['name'] == test_character_data['name']
    
    def test_update_character(self, client: TestClient, auth_headers: dict, test_character_data: dict):
        """Test character update"""
        # Create character
        create_response = client.post(
            '/api/v1/characters/',
            json=test_character_data,
            headers=auth_headers
        )
        character_id = create_response.json()['id']
        
        # Update character
        update_data = {'level': 5, 'current_hp': 50}
        response = client.put(
            f'/api/v1/characters/{character_id}',
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['level'] == 5
        assert data['current_hp'] == 50
    
    def test_delete_character(self, client: TestClient, auth_headers: dict, test_character_data: dict):
        """Test character deletion"""
        # Create character
        create_response = client.post(
            '/api/v1/characters/',
            json=test_character_data,
            headers=auth_headers
        )
        character_id = create_response.json()['id']
        
        # Delete character
        response = client.delete(
            f'/api/v1/characters/{character_id}',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert 'deleted successfully' in response.json()['message'].lower()
        
        # Verify deletion
        get_response = client.get(f'/api/v1/characters/{character_id}', headers=auth_headers)
        assert get_response.status_code == 404
    
    def test_create_character_unauthorized(self, client: TestClient, test_character_data: dict):
        """Test character creation without auth"""
        response = client.post('/api/v1/characters/', json=test_character_data)
        
        assert response.status_code == 401


@pytest.mark.integration
class TestSessionAPIIntegration:
    """Integration tests for session endpoints"""
    
    def test_create_session(self, client: TestClient, auth_headers: dict):
        """Test session creation"""
        session_data = {
            'session_name': 'Test Session',
            'game_mode': 'STORY',
            'description': 'Test session for integration testing',
            'max_players': 5
        }
        
        response = client.post(
            '/api/v1/sessions/',
            json=session_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['session_name'] == session_data['session_name']
        assert data['game_mode'] == session_data['game_mode']
        assert 'session_id' in data
    
    def test_list_sessions(self, client: TestClient, auth_headers: dict):
        """Test listing sessions"""
        # Create session
        client.post('/api/v1/sessions/', json={
            'session_name': 'Test Session',
            'game_mode': 'STORY'
        }, headers=auth_headers)
        
        # List sessions
        response = client.get('/api/v1/sessions/', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'sessions' in data
        assert isinstance(data['sessions'], list)
    
    def test_join_session(self, client: TestClient, auth_headers: dict):
        """Test joining a session"""
        # Create session
        create_response = client.post('/api/v1/sessions/', json={
            'session_name': 'Join Test',
            'game_mode': 'STORY',
            'max_players': 5
        }, headers=auth_headers)
        
        session_id = create_response.json()['session_id']
        
        # Join session
        response = client.post(
            f'/api/v1/sessions/{session_id}/players',
            json={'player_name': 'TestPlayer'},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'player_id' in data
    
    def test_leave_session(self, client: TestClient, auth_headers: dict):
        """Test leaving a session"""
        # Create and join session
        create_response = client.post('/api/v1/sessions/', json={
            'session_name': 'Leave Test',
            'game_mode': 'STORY'
        }, headers=auth_headers)
        
        session_id = create_response.json()['session_id']
        
        join_response = client.post(
            f'/api/v1/sessions/{session_id}/players',
            json={'player_name': 'TestPlayer'},
            headers=auth_headers
        )
        
        player_id = join_response.json()['player_id']
        
        # Leave session
        response = client.delete(
            f'/api/v1/sessions/{session_id}/players/{player_id}',
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_get_session_info(self, client: TestClient, auth_headers: dict):
        """Test getting session info"""
        # Create session
        create_response = client.post('/api/v1/sessions/', json={
            'session_name': 'Info Test',
            'game_mode': 'STORY'
        }, headers=auth_headers)
        
        session_id = create_response.json()['session_id']
        
        # Get session info
        response = client.get(f'/api/v1/sessions/{session_id}', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['session_id'] == session_id
        assert data['session_name'] == 'Info Test'


@pytest.mark.integration
class TestHealthEndpoints:
    """Integration tests for health check endpoints"""
    
    def test_health_check(self, client: TestClient):
        """Test basic health check"""
        response = client.get('/health')
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['status'] == 'healthy'
        assert 'version' in data
        assert 'timestamp' in data
    
    def test_health_ready(self, client: TestClient):
        """Test readiness check"""
        response = client.get('/health/ready')
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['status'] == 'ready'
        assert data['database'] == 'connected'
    
    def test_health_live(self, client: TestClient):
        """Test liveness check"""
        response = client.get('/health/live')
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['status'] == 'alive'


@pytest.mark.slow
class TestLoadScenarios:
    """Load testing scenarios"""
    
    def test_multiple_concurrent_registrations(self, client: TestClient):
        """Test multiple concurrent user registrations"""
        import concurrent.futures
        
        def register_user(username):
            return client.post('/api/v1/auth/register', json={
                'username': username,
                'password': 'TestPassword123!'
            })
        
        usernames = [f'testuser_{i}' for i in range(10)]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(register_user, username) for username in usernames]
            results = [f.result() for f in futures]
        
        # All should succeed
        assert all(r.status_code == 200 for r in results)
    
    def test_rapid_api_requests(self, client: TestClient, auth_headers: dict):
        """Test rapid API requests"""
        import time
        
        start = time.time()
        
        # Make 100 requests
        for i in range(100):
            response = client.get('/health', headers=auth_headers)
            assert response.status_code == 200
        
        elapsed = time.time() - start
        
        # Should complete in reasonable time (< 10 seconds)
        assert elapsed < 10, f"Too slow: {elapsed}s for 100 requests"
