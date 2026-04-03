from backend.src.logging import setup_logging, get_logger

print("Testing logging system...")
setup_logging()
logger = get_logger('test')
logger.info("Test message")
print("✓ Logging system works!")
