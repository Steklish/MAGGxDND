"""
API Request Logging Middleware
Logs all API requests with detailed information
"""
import time
import json
from datetime import datetime, timezone
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from backend.src.logging import get_logger

logger = get_logger('api')
request_logger = get_logger('api.requests')


class APILoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging all API requests and responses
    
    Features:
    - Request method, path, headers
    - Request body (for POST/PUT/PATCH)
    - Response status code
    - Response time
    - User information
    - Error details
    """
    
    def __init__(self, app, log_request_body: bool = True, log_response_body: bool = False):
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.request_count = 0
        self.error_count = 0
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        request_id = f"api_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{self.request_count}"
        self.request_count += 1
        
        # Extract request information
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        headers = dict(request.headers)
        client_host = request.client.host if request.client else "unknown"
        
        # Get user info if authenticated
        user_info = await self._get_user_info(request)
        
        # Log request start
        logger.info(
            f"📥 API Request [{request_id}]",
            extra={
                'request_id': request_id,
                'method': method,
                'path': path,
                'client_host': client_host,
                'user': user_info,
                'query_params': query_params if query_params else None
            }
        )
        
        # Read and log request body
        request_body = None
        if method in ['POST', 'PUT', 'PATCH'] and self.log_request_body:
            try:
                body = await request.body()
                if body:
                    request_body = body.decode('utf-8')
                    logger.debug(
                        f"Request body [{request_id}]",
                        extra={
                            'request_id': request_id,
                            'body_length': len(request_body),
                            'body_preview': request_body[:500]
                        }
                    )
            except Exception as e:
                logger.warning(
                    f"Failed to read request body [{request_id}]",
                    extra={'error': str(e)}
                )
        
        # Log to dedicated request log
        request_data = {
            'request_id': request_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'method': method,
            'path': path,
            'query_params': query_params,
            'headers': {k: v for k, v in headers.items() if k not in ['authorization', 'cookie']},
            'client_host': client_host,
            'user': user_info,
            'body': request_body
        }
        
        request_logger.info(json.dumps(request_data, ensure_ascii=False, indent=2))
        
        # Console output
        print(f"📥 [{method}] {path}")
        print(f"   ID: {request_id}")
        print(f"   Client: {client_host}")
        if user_info:
            print(f"   User: {user_info}")
        print()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"📤 API Response [{request_id}]",
                extra={
                    'request_id': request_id,
                    'status_code': response.status_code,
                    'processing_time_ms': round(processing_time * 1000, 2)
                }
            )
            
            # Log errors
            if response.status_code >= 400:
                self.error_count += 1
                logger.warning(
                    f"⚠️ API Error [{request_id}]",
                    extra={
                        'request_id': request_id,
                        'status_code': response.status_code,
                        'processing_time_ms': round(processing_time * 1000, 2)
                    }
                )
            
            # Console output
            status_color = "✅" if response.status_code < 400 else "❌"
            print(f"{status_color} [{response.status_code}] {method} {path}")
            print(f"   Time: {processing_time*1000:.2f}ms")
            print()
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.error_count += 1
            
            # Log exception
            logger.error(
                f"❌ API Exception [{request_id}]",
                extra={
                    'request_id': request_id,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'processing_time_ms': round(processing_time * 1000, 2)
                },
                exc_info=True
            )
            
            # Console output
            print(f"❌ [EXCEPTION] {method} {path}")
            print(f"   Error: {str(e)}")
            print(f"   Type: {type(e).__name__}")
            print()
            
            raise
    
    async def _get_user_info(self, request: Request) -> dict:
        """Extract user information from request"""
        try:
            # Try to get user from state (set by auth middleware)
            if hasattr(request.state, 'user'):
                user = request.state.user
                return {
                    'id': getattr(user, 'id', None),
                    'username': getattr(user, 'username', None),
                    'is_guest': getattr(user, 'is_guest', False)
                }
            
            # Try to get from headers
            auth_header = request.headers.get('authorization', '')
            if auth_header.startswith('Bearer '):
                return {'authenticated': True, 'type': 'bearer'}
            
            return {'authenticated': False}
            
        except Exception:
            return {'error': 'Failed to extract user info'}
    
    def get_stats(self) -> dict:
        """Get API statistics"""
        return {
            'total_requests': self.request_count,
            'total_errors': self.error_count,
            'error_rate': round(self.error_count / max(self.request_count, 1) * 100, 2)
        }


class SlowRequestMiddleware(BaseHTTPMiddleware):
    """
    Middleware to detect and log slow requests
    
    Logs requests that take longer than threshold
    """
    
    def __init__(self, app, threshold_seconds: float = 1.0):
        super().__init__(app)
        self.threshold = threshold_seconds
    
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        response = await call_next(request)
        processing_time = time.time() - start_time
        
        if processing_time > self.threshold:
            logger.warning(
                f"🐌 Slow Request Detected",
                extra={
                    'method': request.method,
                    'path': request.url.path,
                    'processing_time_ms': round(processing_time * 1000, 2),
                    'threshold_ms': round(self.threshold * 1000, 2)
                }
            )
        
        return response
