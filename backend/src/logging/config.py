"""
Advanced Logging System for MAGGxDND
Provides comprehensive logging for API, AI, database, and game interactions
"""
import logging
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


def setup_logging(
    log_dir: str = './logs',
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    max_bytes: int = 10*1024*1024,  # 10MB
    backup_count: int = 5,
    enable_json_logs: bool = True
):
    """
    Setup comprehensive logging system
    
    Args:
        log_dir: Directory for log files
        console_level: Logging level for console
        file_level: Logging level for files
        max_bytes: Max size before rotation
        backup_count: Number of backup files to keep
        enable_json_logs: Enable JSON formatted logs
    """
    
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories for different log types
    subdirs = ['api', 'ai', 'database', 'game', 'errors', 'websocket']
    for subdir in subdirs:
        (log_path / subdir).mkdir(exist_ok=True)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all levels
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Main file handler (rotating)
    main_log_file = log_path / 'application.log'
    file_handler = RotatingFileHandler(
        main_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(file_level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(module)s.%(funcName)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # JSON file handler for structured logging
    if enable_json_logs:
        json_log_file = log_path / 'application.json'
        json_handler = RotatingFileHandler(
            json_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        json_handler.setLevel(file_level)
        json_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(json_handler)
    
    # Error file handler (separate file for errors)
    error_log_file = log_path / 'errors.log'
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # Specialized loggers for different components
    setup_specialized_loggers(log_path, file_level, max_bytes, backup_count)
    
    # Log startup
    root_logger.info("="*80)
    root_logger.info("MAGGxDND Logging System Initialized")
    root_logger.info(f"Log directory: {log_path.absolute()}")
    root_logger.info(f"Console level: {logging.getLevelName(console_level)}")
    root_logger.info(f"File level: {logging.getLevelName(file_level)}")
    root_logger.info("="*80)


def setup_specialized_loggers(
    log_path: Path,
    file_level: int,
    max_bytes: int,
    backup_count: int
):
    """Setup specialized loggers for different components"""
    
    # API Logger
    api_logger = logging.getLogger('api')
    api_logger.setLevel(logging.DEBUG)
    api_handler = RotatingFileHandler(
        log_path / 'api' / 'api.log',
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    api_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(module)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    api_logger.addHandler(api_handler)
    
    # AI Logger
    ai_logger = logging.getLogger('ai')
    ai_logger.setLevel(logging.DEBUG)
    
    # AI requests log
    ai_request_handler = TimedRotatingFileHandler(
        log_path / 'ai' / 'requests.log',
        when='D',
        interval=1,
        backupCount=backup_count,
        encoding='utf-8'
    )
    ai_request_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    ai_logger.addHandler(ai_request_handler)
    
    # AI responses log
    ai_response_handler = TimedRotatingFileHandler(
        log_path / 'ai' / 'responses.log',
        when='D',
        interval=1,
        backupCount=backup_count,
        encoding='utf-8'
    )
    ai_response_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    ai_logger.addHandler(ai_response_handler)
    
    # Database Logger
    db_logger = logging.getLogger('database')
    db_logger.setLevel(logging.DEBUG)
    db_handler = RotatingFileHandler(
        log_path / 'database' / 'database.log',
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    db_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(module)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    db_logger.addHandler(db_handler)
    
    # Game Logger
    game_logger = logging.getLogger('game')
    game_logger.setLevel(logging.DEBUG)
    game_handler = RotatingFileHandler(
        log_path / 'game' / 'game.log',
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    game_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(module)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    game_logger.addHandler(game_handler)
    
    # WebSocket Logger
    ws_logger = logging.getLogger('websocket')
    ws_logger.setLevel(logging.DEBUG)
    ws_handler = RotatingFileHandler(
        log_path / 'websocket' / 'websocket.log',
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    ws_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(module)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    ws_logger.addHandler(ws_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name
    
    Args:
        name: Logger name (e.g., 'api.users', 'ai.generator')
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LogContext:
    """Context manager for adding extra context to logs"""
    
    def __init__(self, logger: logging.Logger, **kwargs):
        self.logger = logger
        self.context = kwargs
        self.old_factory = None
    
    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            if not hasattr(record, 'extra_data'):
                record.extra_data = {}
            record.extra_data.update(self.context)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.old_factory:
            logging.setLogRecordFactory(self.old_factory)


# Example usage and testing
if __name__ == '__main__':
    # Setup logging
    setup_logging()
    
    # Get logger
    logger = get_logger('test')
    
    # Test basic logging
    logger.debug('Debug message')
    logger.info('Info message')
    logger.warning('Warning message')
    logger.error('Error message')
    logger.critical('Critical message')
    
    # Test with context
    with LogContext(logger, user_id=123, action='test_action'):
        logger.info('Message with context')
    
    # Test exception logging
    try:
        raise ValueError('Test error')
    except Exception:
        logger.exception('An exception occurred')
    
    print("✓ Logging system test completed!")
