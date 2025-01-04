import logging
import os
import time
from functools import wraps
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler
from typing import Optional

LOG_FILE = os.path.join('logs', 'productivity.log')

def clear_log_file():
    """Clear the log file contents."""
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, 'w') as f:
            f.write('')  # Clear file contents
    except Exception as e:
        print(f"Error clearing log file: {e}")

# Create logs directory
os.makedirs("logs", exist_ok=True)


def setup_logging(logger_name, log_file=None):
    """
    Setup logging configuration.

    Args:
        logger_name (str): Name of the logger
        log_file (str, optional): Custom log file path

    Returns:
        logging.Logger: Configured logger instance
    """
    # Clear log file on initialization
    if logger_name == '__main__':
        clear_log_file()

    logger = logging.getLogger(logger_name)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    if log_file is None:
        log_file = os.path.join("logs", "productivity.log")
        
    handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    return logger


def log_execution_time(logger):
    """Decorator to log function execution time"""
    def decorator(func):
        """
        Inner decorator function that wraps the target function to log its execution time.

        Args:
            func: The function to be wrapped.

        Returns:
            wrapper: The wrapped function that includes timing and logging functionality.

        The decorator will:
        - Log the start of function execution
        - Time the function execution
        - Log successful completion with execution time
        - Log any errors that occur during execution
        """
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
        logger.error("Error details", exc_info=True)
        raise
