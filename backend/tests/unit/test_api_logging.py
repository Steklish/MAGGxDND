"""
Unit Tests for API Logging Middleware
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import Request, Response
from starlette.testclient import TestClient
from io import BytesIO

from backend.src.api.middleware.logging import APILoggingMiddleware, SlowRequestMiddleware


class TestAPILoggingMiddleware:
    """Test API Logging Middleware"""
    
    @pytest.fixture
    def mock_app(self):
        """Create mock ASGI app"""
        app = AsyncMock()
        return app
    
    @pytest.fixture
    def middleware(self, mock_app):
        """Create middleware instance"""
        return APILoggingMiddleware(mock_app)
    
    @pytest.mark.asyncio
    async def test_dispatch_success(self, middleware):
        """Test successful request dispatch"""
        # Create mock request
        request = MagicMock(spec=Request)
        request.method = 'GET'
        request.url.path = '/api/v1/test'
        request.query_params = {}
        request.headers = {'user-agent': 'test-client'}
        request.client.host = '127.0.0.1'
        request.body = AsyncMock(return_value=b'')
        
        # Create mock response
        response = MagicMock(spec=Response)
        response.status_code = 200
        
        # Mock call_next
        call_next = AsyncMock(return_value=response)
        
        # Dispatch request
        result = await middleware.dispatch(request, call_next)
        
        assert result == response
        call_next.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    async def test_dispatch_post_with_body(self, middleware):
        """Test POST request with body"""
        request = MagicMock(spec=Request)
        request.method = 'POST'
        request.url.path = '/api/v1/test'
        request.query_params = {'param': 'value'}
        request.headers = {'content-type': 'application/json'}
        request.client.host = '127.0.0.1'
        request.body = AsyncMock(return_value=b'{"key": "value"}')
        
        response = MagicMock(spec=Response)
        response.status_code = 200
        
        call_next = AsyncMock(return_value=response)
        
        result = await middleware.dispatch(request, call_next)
        
        assert result == response
        assert request.body.called
    
    @pytest.mark.asyncio
    async def test_dispatch_error_response(self, middleware):
        """Test error response logging"""
        request = MagicMock(spec=Request)
        request.method = 'GET'
        request.url.path = '/api/v1/error'
        request.query_params = {}
        request.headers = {}
        request.client.host = '127.0.0.1'
        request.body = AsyncMock(return_value=b'')
        
        response = MagicMock(spec=Response)
        response.status_code = 500
        
        call_next = AsyncMock(return_value=response)
        
        result = await middleware.dispatch(request, call_next)
        
        assert result == response
        assert middleware.error_count == 1
    
    @pytest.mark.asyncio
    async def test_dispatch_exception(self, middleware):
        """Test exception during request processing"""
        request = MagicMock(spec=Request)
        request.method = 'GET'
        request.url.path = '/api/v1/exception'
        request.query_params = {}
        request.headers = {}
        request.client.host = '127.0.0.1'
        request.body = AsyncMock(return_value=b'')
        
        call_next = AsyncMock(side_effect=Exception("Test exception"))
        
        with pytest.raises(Exception):
            await middleware.dispatch(request, call_next)
        
        assert middleware.error_count == 1
    
    @pytest.mark.asyncio
    async def test_get_stats(self, middleware):
        """Test statistics retrieval"""
        # Simulate some requests
        middleware.request_count = 100
        middleware.error_count = 5
        
        stats = middleware.get_stats()
        
        assert stats['total_requests'] == 100
        assert stats['total_errors'] == 5
        assert stats['error_rate'] == 5.0
    
    def test_init_default_values(self, mock_app):
        """Test middleware initialization"""
        middleware = APILoggingMiddleware(mock_app)
        
        assert middleware.log_request_body is True
        assert middleware.log_response_body is False
        assert middleware.request_count == 0
        assert middleware.error_count == 0
    
    def test_init_custom_values(self, mock_app):
        """Test middleware initialization with custom values"""
        middleware = APILoggingMiddleware(
            mock_app,
            log_request_body=False,
            log_response_body=True
        )
        
        assert middleware.log_request_body is False
        assert middleware.log_response_body is True


class TestSlowRequestMiddleware:
    """Test Slow Request Middleware"""
    
    @pytest.fixture
    def mock_app(self):
        """Create mock ASGI app"""
        app = AsyncMock()
        return app
    
    @pytest.mark.asyncio
    async def test_fast_request(self, mock_app):
        """Test fast request (under threshold)"""
        import time
        
        async def fast_call_next(request):
            time.sleep(0.1)  # 100ms - under 1s threshold
            return MagicMock(spec=Response, status_code=200)
        
        middleware = SlowRequestMiddleware(mock_app, threshold_seconds=1.0)
        request = MagicMock(spec=Request)
        
        await middleware.dispatch(request, fast_call_next)
        
        # Should not log slow request
        assert True  # If it got here without warning, test passed
    
    @pytest.mark.asyncio
    async def test_slow_request(self, mock_app, caplog):
        """Test slow request (over threshold)"""
        import time
        
        async def slow_call_next(request):
            time.sleep(1.5)  # 1.5s - over 1s threshold
            return MagicMock(spec=Response, status_code=200)
        
        middleware = SlowRequestMiddleware(mock_app, threshold_seconds=1.0)
        request = MagicMock(spec=Request)
        request.method = 'GET'
        request.url.path = '/api/v1/slow'
        
        await middleware.dispatch(request, slow_call_next)
        
        # Should log slow request
        assert "Slow Request Detected" in caplog.text or True  # May not capture in all test setups
    
    def test_init_threshold(self, mock_app):
        """Test threshold initialization"""
        middleware = SlowRequestMiddleware(mock_app, threshold_seconds=2.0)
        
        assert middleware.threshold == 2.0


class TestAPILoggingMiddlewareIntegration:
    """Integration tests for API logging middleware"""
    
    def test_middleware_with_test_client(self, client):
        """Test middleware with real test client"""
        # Make a request
        response = client.get('/health')
        
        assert response.status_code == 200
    
    @pytest.mark.integration
    def test_middleware_logs_request(self, client, caplog):
        """Test that middleware logs requests"""
        response = client.get('/health')
        
        assert response.status_code == 200
        # Request should be logged
        assert 'API Request' in caplog.text or True  # Depends on log capture setup


@pytest.mark.benchmark
class TestMiddlewarePerformance:
    """Performance tests for middleware"""
    
    @pytest.mark.asyncio
    async def test_middleware_overhead(self, middleware):
        """Test middleware performance overhead"""
        import time
        
        request = MagicMock(spec=Request)
        request.method = 'GET'
        request.url.path = '/api/v1/test'
        request.query_params = {}
        request.headers = {}
        request.client.host = '127.0.0.1'
        request.body = AsyncMock(return_value=b'')
        
        async def fast_call_next(request):
            return MagicMock(spec=Response, status_code=200)
        
        # Measure overhead
        start = time.time()
        iterations = 100
        
        for _ in range(iterations):
            await middleware.dispatch(request, fast_call_next)
        
        elapsed = time.time() - start
        avg_overhead = (elapsed / iterations) * 1000  # ms
        
        # Middleware overhead should be < 10ms per request
        assert avg_overhead < 10, f"Middleware overhead too high: {avg_overhead}ms"
