from flask import Flask
import logging
import os
import signal
import sys
from python.logging_config import setup_logging

os.makedirs("logs", exist_ok=True)

setup_logging(__name__)

log = logging.getLogger(__name__)

app = Flask(__name__)
app.config.update(
    PORT=5000,
    ENV='development',
    DEBUG=True
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
    """Basic health check endpoint"""
    log.debug("Health check requested")
    return {'status': 'healthy'}, 200


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
