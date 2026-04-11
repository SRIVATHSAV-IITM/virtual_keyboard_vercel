import eel
import sys
import os
import logging

# Setup logging for launch_game.py
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Eel to serve the tic_tac_toe directory
eel.init(os.path.dirname(os.path.abspath(__file__)))

# Get screen dimensions from command line arguments
screen_width = int(sys.argv[1]) if len(sys.argv) > 1 else 800
screen_height = int(sys.argv[2]) if len(sys.argv) > 2 else 600

logger.info(f"Launching Tic-Tac-Toe game on port 8001 with size {screen_width}x{screen_height}")

@eel.expose
def close_game():
    logger.info("Close game requested. Terminating.")
    sys.exit()

# Start the Eel application, serving index.html
eel.start('index.html', size=(screen_width, screen_height), suppress_error=True, port=0)

@eel.on_close
def _eel_close(route, websockets):
    logger.info(f"Eel window closed. Route: {route}, WebSockets: {websockets}")
    sys.exit()