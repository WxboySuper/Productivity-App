import logging
import os
import time
from functools import wraps
from contextlib import contextmanager

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
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        '[%(levelname)s] [%(asctime)s] %(name)s - %(message)s [%(filename)s:%(lineno)d]',
        datefmt='%Y-%m-%d %H:%M:%S.%f'
    )

    # Setup file handler
    if log_file is None:
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "productivity.log")
    else:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024, backupCount=5)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

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
