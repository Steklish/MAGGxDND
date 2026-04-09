"""
API Request Logging Middleware
Logs all API requests with detailed information including trace ID from frontend
Tracks the complete journey: Frontend → Backend → Core Engine → Response
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
core_logger = get_logger('core.tracing')


# ANSI color codes for console
class Colors:
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class APILoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging API requests and responses

    Features:
    - Request method, path, headers
    - Request body (for POST/PUT/PATCH)
    - Response status code
    - Response time
    - User information
    - Error details
    
    Note: Reduced verbosity - only logs errors and slow requests to console
    """

    def __init__(self, app, log_request_body: bool = True, log_response_body: bool = False, verbose: bool = False):
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.verbose = verbose  # Set True for detailed logging
        self.request_count = 0
        self.error_count = 0
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Skip logging for health check endpoints (reduces spam)
        path = request.url.path
        is_health_check = path in ['/health', '/health/live', '/favicon.ico']
        
        if is_health_check:
            # Just process the request without logging
            response = await call_next(request)
            return response
        
        request_id = f"api_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{self.request_count}"
        self.request_count += 1

        # Extract trace ID from frontend if available
        trace_id = request.headers.get('x-trace-id', None)
        trace_info = f"{Colors.YELLOW}{trace_id}{Colors.RESET}" if trace_id else f"{Colors.MAGENTA}N/A{Colors.RESET}"

        # Extract request information
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        headers = dict(request.headers)
        client_host = request.client.host if request.client else "unknown"

        # Get user info if authenticated
        user_info = await self._get_user_info(request)

        # Log request start with trace ID
        logger.info(
            f"📥 API Request [{request_id}]",
            extra={
                'request_id': request_id,
                'trace_id': trace_id,
                'method': method,
                'path': path,
                'client_host': client_host,
                'user': user_info,
                'query_params': query_params if query_params else None,
                'journey_stage': '1/5: Frontend → Backend API'
            }
        )

        # Track request journey
        journey_start = time.time()
        request.state.request_journey = {
            'start_time': journey_start,
            'trace_id': trace_id,
            'request_id': request_id,
            'stages': ['Frontend → Backend API']
        }

        # Console output with trace ID and journey info (only in verbose mode)
        if self.verbose:
            request_logger.debug(
                f"REQUEST JOURNEY START | "
                f"Trace ID: {trace_info} | Request ID: {request_id} | "
                f"Method: {method} | Path: {path} | Client: {client_host} | "
                f"User: {user_info or 'anonymous'} | "
                f"Query: {query_params or 'none'} | "
                f"Journey: Frontend → Backend API (START) | Stage: 1/5"
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
        
        # Log to dedicated request log (reduced verbosity - no full body dump)
        request_data = {
            'request_id': request_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'method': method,
            'path': path,
            'query_params': query_params if query_params else None,
            'client_host': client_host,
            'user': user_info,
            'has_body': request_body is not None,
            'body_length': len(request_body) if request_body else 0
        }

        request_logger.info(json.dumps(request_data, ensure_ascii=False))

        try:
            # Process request
            response = await call_next(request)

            # Calculate processing time
            processing_time = time.time() - start_time

            # Get journey info if available
            journey_info = getattr(request.state, 'request_journey', None)
            journey_stages = journey_info.get('stages', []) if journey_info else []
            journey_start = journey_info.get('start_time', start_time) if journey_info else start_time
            total_journey_time = (time.time() - journey_start) * 1000

            # Log response with trace ID
            logger.info(
                f"📤 API Response [{request_id}]",
                extra={
                    'request_id': request_id,
                    'trace_id': trace_id,
                    'status_code': response.status_code,
                    'processing_time_ms': round(processing_time * 1000, 2),
                    'journey_stages': journey_stages,
                    'journey_stage': '5/5: Backend → Frontend'
                }
            )

            # Add trace ID to response headers
            if trace_id:
                response.headers['X-Trace-ID'] = trace_id

            # Log errors
            if response.status_code >= 400:
                self.error_count += 1
                logger.warning(
                    f"⚠️ API Error [{request_id}]",
                    extra={
                        'request_id': request_id,
                        'trace_id': trace_id,
                        'status_code': response.status_code,
                        'processing_time_ms': round(processing_time * 1000, 2),
                        'journey_stage': '5/5: Backend → Frontend (ERROR)'
                    }
                )

            # Console output with trace ID and journey info (only in verbose mode or errors)
            status_color = f"{Colors.GREEN}✅{Colors.RESET}" if response.status_code < 400 else f"{Colors.RED}❌{Colors.RESET}"
            journey_log = ""
            if journey_stages:
                journey_log = f"\n{Colors.CYAN}│{Colors.RESET}    Journey Path: {Colors.YELLOW}{' → '.join(journey_stages)}{Colors.RESET}"
            
            # Only print detailed response logging in verbose mode or on errors
            if self.verbose or response.status_code >= 400:
                request_logger.debug(
                    f"REQUEST JOURNEY COMPLETE | "
                    f"Trace ID: {trace_info} | Request ID: {request_id} | "
                    f"Status: {response.status_code} | "
                    f"Method: {method} | Path: {path} | "
                    f"Processing Time: {processing_time*1000:.2f}ms | "
                    f"Total Journey Time: {total_journey_time:.2f}ms | "
                    f"Journey: Backend → Frontend (COMPLETE) | Stage: 5/5"
                )

            return response

        except Exception as e:
            processing_time = time.time() - start_time
            
            # Get journey info
            journey_info = getattr(request.state, 'request_journey', None)
            journey_start = journey_info.get('start_time', start_time) if journey_info else start_time
            total_journey_time = (time.time() - journey_start) * 1000

            # Log exception with trace ID
            logger.error(
                f"❌ API Exception [{request_id}]",
                extra={
                    'request_id': request_id,
                    'trace_id': trace_id,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'processing_time_ms': round(processing_time * 1000, 2),
                    'journey_stage': '5/5: Backend → Frontend (EXCEPTION)'
                },
                exc_info=True
            )

            # Console output (always show exceptions)
            request_logger.error(
                f"REQUEST JOURNEY FAILED | "
                f"Trace ID: {trace_info} | Request ID: {request_id} | "
                f"Method: {method} | Path: {path} | "
                f"Error: {str(e)} | Type: {type(e).__name__} | "
                f"Processing Time: {processing_time*1000:.2f}ms | "
                f"Total Journey Time: {total_journey_time:.2f}ms | "
                f"Journey: Backend → Frontend (FAILED)",
                exc_info=True
            )

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
    Note: Only logs to file, not console (reduces spam)
    """

    def __init__(self, app, threshold_seconds: float = 1.0):
        super().__init__(app)
        self.threshold = threshold_seconds

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        response = await call_next(request)
        processing_time = time.time() - start_time

        # Only log slow requests to logger (not console)
        if processing_time > self.threshold:
            logger.warning(
                f"🐌 Slow Request: {request.method} {request.url.path} took {processing_time*1000:.2f}ms (threshold: {self.threshold*1000:.0f}ms)"
            )

        return response
