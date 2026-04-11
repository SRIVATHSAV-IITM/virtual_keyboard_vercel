import sys
import os

# Add activities_center to the path to allow "from src..." imports
activities_center_dir = os.path.dirname(os.path.abspath(__file__))
if activities_center_dir not in sys.path:
    sys.path.append(activities_center_dir)

# Add parent directory to the path for logger_reporter
root_dir = os.path.abspath(os.path.join(activities_center_dir, '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Add shared_src to the path for gaze_tracker
shared_src_dir = os.path.join(root_dir, 'shared_src')
if shared_src_dir not in sys.path:
    sys.path.append(shared_src_dir)

import logging
import pygame
from src.welcome_state import WelcomeState
from gaze_tracker import GazeTracker
from src.audio_manager import AudioManager
from src import assets
from src.assets import AUDIO_PATHS
from logger_reporter import setup_logging

# Configure root logger
logger = setup_logging("activities_center")
logger.info("Activities Center application started.")

class ManagerContainer:
    def __init__(self, screen, gaze_tracker, audio_manager, rounds=3):
        self.screen = screen
        self.gaze_tracker = gaze_tracker
        self.audio_manager = audio_manager
        self.rounds = rounds
        self.selected_round = 0
        self.running = True # Add this flag
        logger.debug("ManagerContainer initialized with screen=%s, gaze_tracker=%s, audio_manager=%s, rounds=%d",
                     screen, gaze_tracker, audio_manager, rounds)

    def change_state(self, new_state):
        logger.info("ManagerContainer: changing state to %s", new_state.__class__.__name__)
        self.game_manager = new_state


def main():
    logger.info("Starting application")
    pygame.init()
    logger.debug("Pygame initialized")

    # Get screen dimensions from command line arguments
    if len(sys.argv) > 2:
        screen_width = int(sys.argv[1])
        screen_height = int(sys.argv[2])
        initial_gaze_x = int(float(sys.argv[3])) if len(sys.argv) > 3 and sys.argv[3] != 'None' else None
        initial_gaze_y = int(float(sys.argv[4])) if len(sys.argv) > 4 and sys.argv[4] != 'None' else None
    else:
        # Fallback if arguments are not provided (e.g., for direct testing)
        display_info = pygame.display.Info()
        screen_width, screen_height = display_info.current_w, display_info.current_h
        initial_gaze_x, initial_gaze_y = None, None
    logger.debug("Detected screen size: %dx%d", screen_width, screen_height)
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Eye-Gaze Sentence Builder")
    logger.info("Pygame window created")

    # Initialize GazeTracker
    logger.info("Initializing GazeTracker")
    gaze_tracker = GazeTracker(screen_width=screen_width, screen_height=screen_height)
    logger.debug("GazeTracker instance: %s", gaze_tracker)
    if initial_gaze_x is not None and initial_gaze_y is not None:
        gaze_tracker.set_initial_gaze(initial_gaze_x, initial_gaze_y)
        logger.info("Initial gaze set to (%d, %d)", initial_gaze_x, initial_gaze_y)


    # Initialize audio manager using assets.py paths
    logger.info("Initializing AudioManager with audio file paths")
    audio_manager = AudioManager()

    logger.debug("AudioManager instance: %s", audio_manager)

    audio_manager.play_bg_music()
    logger.info("Background music playback started")

    # Container for managers and state
    manager = ManagerContainer(screen, gaze_tracker, audio_manager, rounds=3)
    logger.debug("ManagerContainer created: %s", manager)

    # Set initial game state
    initial_state = WelcomeState(manager)
    manager.game_manager = initial_state
    logger.info("Initial game state set to %s", initial_state.__class__.__name__)

    clock = pygame.time.Clock()
    frame_count = 0

    logger.info("Entering main loop")
    try:
        while manager.running:
            frame_count += 1
            logger.debug("Frame %d start", frame_count)

            for event in pygame.event.get():
                logger.debug("Event polled: %s", event)
                if event.type == pygame.QUIT:
                    manager.running = False
                    logger.info("QUIT event received, exiting loop")

            # Update and render current state
            logger.debug("Updating state: %s", manager.game_manager.__class__.__name__)
            manager.game_manager.update()
            logger.debug("Rendering state: %s", manager.game_manager.__class__.__name__)
            manager.game_manager.render()

            # Update gaze_tracker in ManagerContainer
            if gaze_tracker:
                gaze_x, gaze_y = manager.gaze_tracker.get_gaze_point()
                # The gaze_x and gaze_y are already updated within the GazeTracker instance
                # No need to call a separate update method.

            pygame.display.flip()
            logger.debug("Display flipped")

            clock.tick(60)
            logger.debug("Tick complete (FPS limit applied)")
    except Exception as e:
        logger.exception("Unhandled exception in main loop: %s", e)
    finally:
        logger.info("Beginning cleanup")
        audio_manager.stop_bg_music()
        logger.debug("Background music stopped")
        audio_manager.quit()
        logger.debug("AudioManager quit")
        if 'gaze_tracker' in locals() and gaze_tracker:
            gaze_tracker.release()
            logger.debug("GazeTracker released")
        pygame.quit()
        logger.info("Pygame quit, application terminated")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical("Application failed to start or crashed: %s", e, exc_info=True)
