import logging
import logging.handlers
import os
import time
from functools import wraps
from contextlib import contextmanager

# Create logs directory
os.makedirs("logs", exist_ok=True)

def setup_logging(name, level=logging.INFO):
    """Configure logging with rotation and formatting"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename='logs/productivity.log',
        maxBytes=10485760,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )

    # Stream handler for console output
    console_handler = logging.StreamHandler()

    # Formatter
    formatter = logging.Formatter(
        '%(levelname)s [%(asctime)s] %(name)s - %(message)s [%(filename)s:%(lineno)d]',
        datefmt='%Y-%m-%d %H:%M:%S.%f'
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def log_execution_time(logger):
    """Decorator to log function execution time"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.debug(
                    "Function '%s' executed in %.2f seconds", 
                    func.__name__, execution_time
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    "Function '%s' failed after %.2f seconds - Error: %s",
                    func.__name__, execution_time, str(e),
                    exc_info=True
                )
                raise
        return wrapper
    return decorator

@contextmanager
def log_context(logger, operation, **context):
    """Context manager for operation logging with context"""
    op_id = context.get('operation_id', str(time.time()))
    logger.info("Starting %s [OperationID: %s]", operation, op_id)
    logger.debug("Context: %s", context)
    
    try:
        yield op_id
        logger.info("Completed %s [OperationID: %s]", operation, op_id)
    except Exception as e:
        logger.error(
            "Failed %s [OperationID: %s] - Error: %s",
            operation, op_id, str(e),
            exc_info=True
        )
        raise
