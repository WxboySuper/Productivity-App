from flask import Flask
import logging
import os
import signal
import sys

# TODO: Implement a basic health check configuration
# TODO: Implement a cleanup process for cleanup senarios

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s [%(asctime)s] %(name)s - %(message)s [%(filename)s:%(lineno)d]',
    datefmt='%Y-%m-%d %H:%M:%S.%f',
    handlers=[
        logging.FileHandler('logs/productivity.log'),
        logging.StreamHandler()
    ]
)

log = logging.getLogger(__name__)

app = Flask(__name__)
app.config.update(
    PORT=5000,
    ENV='development',
    DEBUG=True
)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    log.info("Received shutdown signal")
    log.info("Cleaning up resources...")
    log.debug("No current cleanup implementation")
    log.info("Server shutdown complete")
    sys.exit(0)

@app.before_first_request
def before_first_request():
    """Log when the server handles its first request"""
    log.info("Handling first request to the server")
    log.debug("Server configuration: %s", app.config)

@app.route('/health')
def health_check():
    """Basic health check endpoint"""
    log.debug("Health check requested")
    return {'status': 'healthy'}, 200

if __name__ == '__main__': # pragma: no cover
    try:
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        log.info("Starting Productivity App Server")
        log.info("Environment: %s", app.config['ENV'])
        log.info("Debug mode: %s", app.config['DEBUG'])
        log.info("Server port: %s", app.config['PORT'])
        
        app.run(
            host='localhost',
            port=app.config['PORT']
        )
    except Exception as e:
        log.critical(
            "Failed to start server - Error: %s", 
            str(e), 
            exc_info=True,
            stack_info=True
        )
        sys.exit(1)