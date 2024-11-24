from main import app
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
log = logging.getLogger(__name__)

if __name__ == '__main__':
    log.info("Starting Flask server...")
    app.run(port=5000)
