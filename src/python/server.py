from flask import Flask
import logging

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
app.config['PORT'] = 5000

if __name__ == '__main__': # pragma: no cover
    try:
        log.info("Attempting to Start Productivity App Server")
        app.run(port=app.config['PORT']) # pragma: no cover
    except Exception as e:
        log.critical("Failed to start server - Error: %s", str(e), exc_info=True)