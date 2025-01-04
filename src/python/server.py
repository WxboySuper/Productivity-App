from flask import Flask
import logging
import os
import signal
import sys
from python.logging_config import setup_logging
import psutil
import time

os.makedirs("logs", exist_ok=True)

setup_logging(__name__)

log = logging.getLogger(__name__)

app = Flask(__name__)
app.config.update(
    PORT=5000,
    ENV='development',
    DEBUG=True,
    START_TIME=time.time()  # Add startup time to track uptime
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


@app.route('/health')
def health_check():
    """Comprehensive health check endpoint"""
    log.debug("Health check requested")
    
    # Calculate uptime
    uptime = time.time() - app.config['START_TIME']
    
    # Get system metrics
    memory = psutil.virtual_memory()
    load = psutil.getloadavg()
    
    # Simulate DB check (replace with actual DB check in production)
    db_status = "connected"  # This should be an actual DB connection check
    
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
        'database': db_status
    }
    
    # Set response status based on metrics
    is_healthy = (
        memory.percent < 90 and  # Less than 90% memory usage
        load[0] < 5 and         # Load average below 5
        db_status == "connected"
    )
    
    health_data['status'] = 'healthy' if is_healthy else 'degraded'
    status_code = 200 if is_healthy else 503
    
    return health_data, status_code


if __name__ == '__main__':  # pragma: no cover
    # Coverage Skip: I have no clue how to test this
    try:
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        log.info("Starting Productivity App Server")
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
