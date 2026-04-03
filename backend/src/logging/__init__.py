"""
Logging System for MAGGxDND
"""
from .config import (
    setup_logging,
    get_logger,
    LogContext,
    ColoredFormatter,
    JSONFormatter
)

from .request_tracing import (
    RequestTracer,
    trace_request,
    FrontendRequestLogger,
    get_trace_id,
    set_trace_id,
    clear_trace_id,
    TraceColors
)

__all__ = [
    # Core logging
    'setup_logging',
    'get_logger',
    'LogContext',
    'ColoredFormatter',
    'JSONFormatter',
    # Request tracing
    'RequestTracer',
    'trace_request',
    'FrontendRequestLogger',
    'get_trace_id',
    'set_trace_id',
    'clear_trace_id',
    'TraceColors'
]
