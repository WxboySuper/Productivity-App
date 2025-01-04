from flask import Flask, jsonify, request
import logging
import os
import signal
import sys
from logging_config import setup_logging, clear_log_file, LOG_FILE
import psutil
import time
import sqlite3
from typing import Dict, Any
import concurrent.futures
from todo import TodoList

os.makedirs("logs", exist_ok=True)

setup_logging(__name__)

log = logging.getLogger(__name__)
app = Flask(__name__)
todo_list = TodoList()
app.config.update(
    PORT=5000,
    ENV='development',  # Only include ENV once
    DEBUG=os.environ.get("FLASK_DEBUG", False),
    START_TIME=time.time(),  # Add startup time to track uptime
    DB_TIMEOUT=os.environ.get("DB_TIMEOUT", 1.0)  # Add configurable timeout
)


class AppContext:
    """Context manager for Flask app cleanup"""

    def __init__(self, flask_app):
        self.app = flask_app
        self.cleanup_handlers = []

    def register_cleanup(self, handler):
        """Register a cleanup handler"""
        self.cleanup_handlers.append(handler)

    def cleanup(self):
        """Execute all cleanup handlers"""
        for handler in self.cleanup_handlers:
            try:
                handler()
            except Exception as e:
                log.error("Cleanup handler failed: %s", str(e))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


# Create app context
app_context = AppContext(app)


def signal_handler(_signum, _frame):
    """Handle shutdown signals gracefully"""
    log.info("Received shutdown signal")
    log.info("Cleaning up resources...")
    app_context.cleanup()
    log.info("Server shutdown complete")
    sys.exit(0)


@app.before_request
def before_request():
    """Log when the server handles its first request"""
    if not app.config.get('handled_first_request'):
        log.info("Handling first request to the server")
        log.debug("Server configuration: %s", app.config)
        app.config['handled_first_request'] = True


def check_database_health(timeout: float = None) -> Dict[str, Any]:
    """Check database connection health with timeout"""
    if timeout is None:
        timeout = float(app.config.get('DB_TIMEOUT', 1.0))

    if timeout <= 0:
        raise ValueError("Timeout must be a positive number")

    db_health = {
        "status": "disconnected",
        "response_time": None,
        "error": None
    }

    def check_connection():
        """Attempt to establish and verify database connection.

        Establishes connection to SQLite database, executes a simple query
        to verify connection is working, and properly closes resources.

        Raises:
            sqlite3.OperationalError: If database connection fails
            sqlite3.Error: For other SQLite-related errors
            Exception: For unexpected errors during connection attempt
        """
        conn = None
        try:
            # Cap connection timeout at 5 seconds as a safety measure
            conn = sqlite3.connect('productivity.db', timeout=min(timeout, 5.0))
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            cursor.fetchone()
            cursor.close()
        finally:
            if conn:
                conn.close()

    try:
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(check_connection)
            future.result(timeout=timeout)  # This will raise TimeoutError if it takes too long

        response_time = time.time() - start_time
        db_health.update({
            "status": "connected",
            "response_time": round(response_time * 1000, 2),  # Convert to milliseconds
            "error": None
        })
    except concurrent.futures.TimeoutError:
        db_health["error"] = "Connection timed out"
        log.error("Database connection timed out")
    except sqlite3.OperationalError as e:
        db_health["error"] = f"Database error: {str(e)}"
        log.error("SQLite operational error: %s", e)
    except Exception as e:
        db_health["error"] = f"Unexpected error: {str(e)}"
        log.error("Unexpected error during database health check")

    return db_health


@app.route('/health')
def health_check():
    """Comprehensive health check endpoint

    Returns:
        tuple: A tuple containing:
            - dict: Health check data with the following structure:
                - status (str): 'healthy' or 'degraded'
                - uptime_seconds (float): Server uptime in seconds
                - memory (dict): Memory statistics
                    - total (int): Total memory in bytes
                    - available (int): Available memory in bytes
                    - percent (float): Memory usage percentage
                - system_load (dict): System load averages
                    - 1min (float): 1-minute load average
                    - 5min (float): 5-minute load average
                    - 15min (float): 15-minute load average
                - database (dict): Database health information
                    - status (str): 'connected' or 'disconnected'
                    - response_time (float|None): Response time in milliseconds
                    - error (str|None): Error message if any
            - int: HTTP status code (200 for healthy, 503 for degraded)
    """
    log.debug("Health check requested")

    # Calculate uptime
    uptime = time.time() - app.config['START_TIME']

    # Get system metrics
    memory = psutil.virtual_memory()
    load = psutil.getloadavg()

    # Perform database health check
    db_health = check_database_health()

    health_data = {
        'status': 'healthy',
        'uptime_seconds': round(uptime, 2),
        'memory': {
            'total': memory.total,
            'available': memory.available,
            'percent': memory.percent
        },
        'system_load': {
            '1min': load[0],
            '5min': load[1],
            '15min': load[2]
        },
        'database': db_health
    }

    # Get thresholds from config with defaults
    memory_threshold = float(app.config.get('HEALTH_CHECK_MEMORY_THRESHOLD', 90))
    load_threshold = float(app.config.get('HEALTH_CHECK_LOAD_THRESHOLD', 5))
    log.debug("Health check thresholds - Memory: %s%%, Load: %s", memory_threshold, load_threshold)

    # Set response status based on metrics
    is_healthy = (
        memory.percent < memory_threshold and  # Changed back to < for strict comparison
        load[0] < load_threshold and  # Changed back to < for strict comparison
        db_health['status'] == "connected"
    )

    health_data['status'] = 'healthy' if is_healthy else 'degraded'
    status_code = 200 if is_healthy else 503

    return health_data, status_code


@app.route('/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks."""
    try:
        tasks = todo_list.get_tasks() if hasattr(todo_list, 'get_tasks') else todo_list.tasks
        return jsonify(tasks)
    except Exception as e:
        log.error("Failed to get tasks", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/tasks', methods=['POST'])
def create_task():
    """Create a new task"""
    try:
        data = request.get_json()
        if not data or 'title' not in data:
            return jsonify({'error': 'Title is required'}), 400

        task = todo_list.add_task(
            title=data['title'],
            deadline=data.get('deadline'),
            category=data.get('category'),
            priority=data.get('priority')
        )
        
        log.info("Task created successfully: %s", task['title'])
        return jsonify(task), 201
    except Exception as e:
        log.error("Failed to create task - Error: %s", str(e), exc_info=True)
        return jsonify({'error': 'Internal Server Error'}), 500


if __name__ == '__main__':  # pragma: no cover
    # Clear and initialize logging
    clear_log_file()
    log = setup_logging(__name__)
    
    log.info("Starting Productivity App Server")
    try:
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        log.info("Environment: %s", app.config['ENV'])
        log.info("Debug mode: %s", app.config['DEBUG'])
        log.info("Server port: %s", app.config['PORT'])

        # Example cleanup handler registration
        app_context.register_cleanup(lambda: log.info("Closing database connections..."))
        app_context.register_cleanup(lambda: log.info("Closing file handles..."))

        with app_context:
            app.run(
                host='localhost',
                port=app.config['PORT']
            )
    except Exception as e:
        log.critical(
            "Failed to start server - Error: %s",
            str(e),
            exc_info=True
        )
        sys.exit(1)

# Add more detailed startup logging
@app.before_first_request
def before_first_request():
    """Log detailed server initialization"""
    log.info({
        "message": "Server initialization details",
        "python_version": sys.version,
        "flask_version": Flask.__version__,
        "environment": app.config['ENV'],
        "debug_mode": app.config['DEBUG'],
        "database_path": os.path.abspath(todo_list.db.db_file),
        "log_path": os.path.abspath(LOG_FILE)
    })
