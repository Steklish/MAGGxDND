"""
Request Tracing Module

Provides detailed logging for tracking requests from frontend to backend and back.
Each request gets a unique trace ID that follows it through the entire system.
"""
import time
import uuid
import json
import logging
from typing import Optional, Dict, Any, Callable
from functools import wraps
from contextvars import ContextVar

# Context variable to store current trace ID
trace_id_var: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)

# Setup logger
logger = logging.getLogger(__name__)


class TraceColors:
    """ANSI color codes for console logging"""
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def get_trace_id() -> str:
    """Get current trace ID or create new one"""
    trace_id = trace_id_var.get()
    if not trace_id:
        trace_id = str(uuid.uuid4())[:8]
        trace_id_var.set(trace_id)
    return trace_id


def set_trace_id(trace_id: str) -> None:
    """Set trace ID for current context"""
    trace_id_var.set(trace_id)


def clear_trace_id() -> None:
    """Clear trace ID from current context"""
    trace_id_var.set(None)


class RequestTracer:
    """
    Traces a request through the system
    
    Usage:
        with RequestTracer("endpoint_name", extra_data={"key": "value"}):
            # process request
            pass
    """
    
    def __init__(self, step: str, extra_data: Optional[Dict[str, Any]] = None):
        self.step = step
        self.extra_data = extra_data or {}
        self.trace_id = get_trace_id()
        self.start_time = None
        self.logger = logging.getLogger(f"trace.{step}")
    
    def __enter__(self):
        self.start_time = time.time()
        self._log_step_start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000 # type: ignore
        if exc_type:
            self._log_step_error(exc_val, duration_ms)
        else:
            self._log_step_complete(duration_ms)
        return False
    
    def _log_step_start(self):
        """Log step start"""
        data_str = json.dumps(self.extra_data, ensure_ascii=False)[:200] if self.extra_data else ""
        
        # Console output with colors
        console_msg = (
            f"{TraceColors.CYAN}┌{'─' * 60}{TraceColors.RESET}\n"
            f"{TraceColors.CYAN}│{TraceColors.RESET} 🔍 TRACE: {TraceColors.BOLD}{self.step}{TraceColors.RESET}\n"
            f"{TraceColors.CYAN}│{TraceColors.RESET}    ID: {TraceColors.YELLOW}{self.trace_id}{TraceColors.RESET}\n"
        )
        
        if data_str:
            console_msg += f"{TraceColors.CYAN}│{TraceColors.RESET}    Data: {TraceColors.BLUE}{data_str}{TraceColors.RESET}\n"
        
        console_msg += f"{TraceColors.CYAN}└{'─' * 60}{TraceColors.RESET}"
        print(console_msg)
        
        # Structured log
        self.logger.info(
            f"Step start: {self.step}",
            extra={
                'trace_id': self.trace_id,
                'step': self.step,
                'direction': 'start',
                **self.extra_data
            }
        )
    
    def _log_step_complete(self, duration_ms: float):
        """Log step completion"""
        # Console output
        console_msg = (
            f"{TraceColors.GREEN}✅ {self.step} completed{TraceColors.RESET} | "
            f"Trace: {TraceColors.YELLOW}{self.trace_id}{TraceColors.RESET} | "
            f"Duration: {TraceColors.GREEN}{duration_ms:.2f}ms{TraceColors.RESET}"
        )
        print(console_msg)
        
        # Structured log
        self.logger.info(
            f"Step complete: {self.step}",
            extra={
                'trace_id': self.trace_id,
                'step': self.step,
                'direction': 'complete',
                'duration_ms': round(duration_ms, 2),
                **self.extra_data
            }
        )
    
    def _log_step_error(self, error: Exception, duration_ms: float):
        """Log step error"""
        # Console output
        console_msg = (
            f"{TraceColors.RED}❌ {self.step} failed{TraceColors.RESET} | "
            f"Trace: {TraceColors.YELLOW}{self.trace_id}{TraceColors.RESET} | "
            f"Duration: {TraceColors.RED}{duration_ms:.2f}ms{TraceColors.RESET} | "
            f"Error: {TraceColors.RED}{str(error)}{TraceColors.RESET}"
        )
        print(console_msg)
        
        # Structured log
        self.logger.error(
            f"Step error: {self.step}",
            extra={
                'trace_id': self.trace_id,
                'step': self.step,
                'direction': 'error',
                'duration_ms': round(duration_ms, 2),
                'error': str(error),
                'error_type': type(error).__name__,
                **self.extra_data
            },
            exc_info=True
        )
    
    def log_data(self, label: str, data: Any, level: str = "info"):
        """Log intermediate data during step"""
        data_str = json.dumps(data, ensure_ascii=False, default=str)[:500]
        
        # Console
        print(f"{TraceColors.BLUE}   📦 {label}:{TraceColors.RESET} {data_str}")
        
        # Structured log
        log_func = getattr(self.logger, level, self.logger.info)
        log_func(
            f"{label}: {data_str}",
            extra={
                'trace_id': self.trace_id,
                'step': self.step,
                'label': label,
                'data': data
            }
        )


def trace_request(endpoint_name: str):
    """
    Decorator to trace a request endpoint
    
    Usage:
        @trace_request("create_session")
        async def create_session(...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            trace_id = get_trace_id()
            
            # Log function entry
            print(f"\n{TraceColors.MAGENTA}{'='*60}{TraceColors.RESET}")
            print(f"{TraceColors.MAGENTA}🚀 ENTERING: {endpoint_name}{TraceColors.RESET}")
            print(f"{TraceColors.MAGENTA}   Trace ID: {trace_id}{TraceColors.RESET}")
            print(f"{TraceColors.MAGENTA}{'='*60}{TraceColors.RESET}\n")
            
            try:
                result = await func(*args, **kwargs)
                
                # Log success
                print(f"\n{TraceColors.GREEN}{'='*60}{TraceColors.RESET}")
                print(f"{TraceColors.GREEN}✅ EXITING: {endpoint_name}{TraceColors.RESET}")
                print(f"{TraceColors.GREEN}   Trace ID: {trace_id}{TraceColors.RESET}")
                print(f"{TraceColors.GREEN}   Status: SUCCESS{TraceColors.RESET}")
                print(f"{TraceColors.GREEN}{'='*60}{TraceColors.RESET}\n")
                
                return result
                
            except Exception as e:
                # Log error
                print(f"\n{TraceColors.RED}{'='*60}{TraceColors.RESET}")
                print(f"{TraceColors.RED}❌ EXITING: {endpoint_name}{TraceColors.RESET}")
                print(f"{TraceColors.RED}   Trace ID: {trace_id}{TraceColors.RESET}")
                print(f"{TraceColors.RED}   Status: ERROR - {str(e)}{TraceColors.RESET}")
                print(f"{TraceColors.RED}{'='*60}{TraceColors.RESET}\n")
                raise
        
        return async_wrapper
    
    return decorator


class FrontendRequestLogger:
    """
    Logger for frontend requests (to be used in browser console)
    
    This creates log messages that will appear in browser console
    with a consistent format for easy tracking
    """
    
    @staticmethod
    def log_request(method: str, endpoint: str, data: Optional[Dict] = None):
        """Log outgoing request from frontend"""
        trace_id = get_trace_id()
        timestamp = time.strftime('%H:%M:%S')
        
        log_data = {
            'type': 'REQUEST',
            'trace_id': trace_id,
            'timestamp': timestamp,
            'method': method,
            'endpoint': endpoint,
            'data': data
        }
        
        # Browser console format
        print(f"\n{TraceColors.BLUE}{'='*60}{TraceColors.RESET}")
        print(f"{TraceColors.BLUE}📤 FRONTEND → BACKEND{TraceColors.RESET}")
        print(f"{TraceColors.BLUE}   Trace: {trace_id}{TraceColors.RESET}")
        print(f"{TraceColors.BLUE}   {method} {endpoint}{TraceColors.RESET}")
        if data:
            print(f"{TraceColors.BLUE}   Data: {json.dumps(data, ensure_ascii=False)[:300]}{TraceColors.RESET}")
        print(f"{TraceColors.BLUE}{'='*60}{TraceColors.RESET}\n")
        
        return trace_id
    
    @staticmethod
    def log_response(trace_id: str, status: int, data: Optional[Dict] = None, duration_ms: float = 0):
        """Log incoming response on frontend"""
        timestamp = time.strftime('%H:%M:%S')
        
        color = TraceColors.GREEN if status < 400 else TraceColors.RED
        
        print(f"\n{color}{'='*60}{TraceColors.RESET}")
        print(f"{color}📥 BACKEND → FRONTEND{TraceColors.RESET}")
        print(f"{color}   Trace: {trace_id}{TraceColors.RESET}")
        print(f"{color}   Status: {status}{TraceColors.RESET}")
        print(f"{color}   Duration: {duration_ms:.2f}ms{TraceColors.RESET}")
        if data:
            preview = json.dumps(data, ensure_ascii=False)[:300]
            print(f"{color}   Response: {preview}{TraceColors.RESET}")
        print(f"{color}{'='*60}{TraceColors.RESET}\n")
    
    @staticmethod
    def log_error(trace_id: str, error: str, endpoint: str):
        """Log error on frontend"""
        timestamp = time.strftime('%H:%M:%S')
        
        print(f"\n{TraceColors.RED}{'='*60}{TraceColors.RESET}")
        print(f"{TraceColors.RED}❌ REQUEST ERROR{TraceColors.RESET}")
        print(f"{TraceColors.RED}   Trace: {trace_id}{TraceColors.RESET}")
        print(f"{TraceColors.RED}   Endpoint: {endpoint}{TraceColors.RESET}")
        print(f"{TraceColors.RED}   Error: {error}{TraceColors.RESET}")
        print(f"{TraceColors.RED}{'='*60}{TraceColors.RESET}\n")


# Export main classes
__all__ = [
    'RequestTracer',
    'trace_request',
    'FrontendRequestLogger',
    'get_trace_id',
    'set_trace_id',
    'clear_trace_id',
]
