import os
import warnings

# Suppress specific deprecation warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")
warnings.filterwarnings("ignore", category=UserWarning, module="google.protobuf.symbol_database")
warnings.filterwarnings("ignore", message=".*pkg_resources is deprecated.*")
warnings.filterwarnings("ignore", message=".*SymbolDatabase.GetPrototype.*")

# Set TensorFlow logging level to suppress info/warning messages
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # 0=all, 1=filter INFO, 2=filter WARNING, 3=filter ERROR
os.environ['GLOG_minloglevel'] = '2'  # Suppress GLOG warnings from MediaPipe

# Suppress SDL2 duplicate library warnings from pygame and opencv-python
os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'

import eel
import sys
import subprocess
import pygame
import logging
import threading
import time
from logger_reporter import setup_logging
from gaze_tracker import GazeTracker # Import the shared GazeTracker

# Setup logging
logger = setup_logging("main", "main_application")

# Initialize Eel
eel.init('web')

# Get screen dimensions
pygame.init()
display_info = pygame.display.Info()
screen_width, screen_height = display_info.current_w, display_info.current_h
pygame.quit()

gaze_tracker_instance = None
gaze_x, gaze_y = None, None

def gaze_tracking_thread():
    global gaze_x, gaze_y, gaze_tracker_instance
    gaze_tracker_instance = GazeTracker(screen_width=screen_width, screen_height=screen_height)
    while True:
        if gaze_tracker_instance:
            gaze_x, gaze_y = gaze_tracker_instance.get_gaze_point()
        else:
            gaze_x, gaze_y = None, None # Or some default values
        # Add a small delay to prevent busy-waiting and reduce CPU usage
        pygame.time.wait(10) # Wait for 10 milliseconds

@eel.expose
def get_gaze_coordinates():
    return gaze_x, gaze_y

active_process = None
active_eel_processes = []

def run_subprocess(script_path, *args):
    global active_process, gaze_tracker_instance, active_eel_processes

    # Stop gaze tracking in main process before launching sub-process
    if gaze_tracker_instance:
        logger.info("Releasing GazeTracker in main process.")
        gaze_tracker_instance.release()
        gaze_tracker_instance = None # Clear the instance
        logger.info("GazeTracker instance set to None.")
        time.sleep(1) # Add 1-second delay

    if active_process and active_process.poll() is None:
        logger.info(f"Terminating previously running process: {active_process.args}")
        active_process.terminate()
        try:
            active_process.wait(timeout=5) # Wait for process to terminate
        except subprocess.TimeoutExpired:
            logger.warning(f"Process {active_process.args} did not terminate, killing it.")
            active_process.kill()

    try:
        command = [sys.executable, script_path] + list(args)
        # Add the current directory to PYTHONPATH for subprocesses
        env = os.environ.copy()
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = os.path.abspath('.') + os.pathsep + env['PYTHONPATH']
        else:
            env['PYTHONPATH'] = os.path.abspath('.')

        logger.info(f"Attempting to launch: {' '.join(command)}")
        process = subprocess.Popen(command, env=env)

        # Determine if the subprocess is an Eel application
        is_eel_app = script_path.endswith('activities_center/main.py') or \
                     script_path.endswith('tic_tac_toe/launch_game.py') or \
                     script_path.endswith('virtual_keyboard_web/launch_keyboard.py')

        if not is_eel_app:
            active_process = process # Store the new active process only if we wait for it
            # Wait for the sub-process to complete only if it's not an Eel app
            process.wait()
            logger.info(f"Sub-process {script_path} finished with exit code {process.returncode}")
            # Re-initialize gaze tracker in main process after sub-process finishes
            logger.info("Re-initializing GazeTracker in main process.")
            gaze_tracker_instance = GazeTracker(screen_width=screen_width, screen_height=screen_height)
        else:
            active_eel_processes.append(process) # Add Eel app to monitored list
            logger.info(f"Launched Eel app {script_path} in background. PID: {process.pid}")

    except Exception as e:
        logger.exception(f"Failed to launch {script_path}")

@eel.expose
def launch_snake_game():
    run_subprocess('snake_game/snake.py', str(screen_width), str(screen_height), str(gaze_x), str(gaze_y))

@eel.expose
def launch_virtual_keyboard():
    run_subprocess('virtual_keyboard/keyboard.py', str(screen_width), str(screen_height), str(gaze_x), str(gaze_y))

@eel.expose
def launch_virtual_keyboard_web():
    run_subprocess('virtual_keyboard_web/launch_keyboard.py', str(screen_width), str(screen_height))

@eel.expose
def launch_activities_center():
    run_subprocess('activities_center/main.py', str(screen_width), str(screen_height))

@eel.expose
def launch_tic_tac_toe():
    run_subprocess('tic_tac_toe/launch_game.py', str(screen_width), str(screen_height))

# Start the application
logger.info("Starting Eel application")

# Start gaze tracking thread
gaze_thread = threading.Thread(target=gaze_tracking_thread, daemon=True)
gaze_thread.start()

def monitor_eel_processes():
    global gaze_tracker_instance, active_eel_processes
    while True:
        logger.debug(f"Monitor: active_eel_processes: {[p.pid for p in active_eel_processes if p.poll() is None]}, gaze_tracker_instance is None: {gaze_tracker_instance is None}")
        # Check for terminated Eel processes
        terminated_processes = []
        for process in active_eel_processes:
            if process.poll() is not None: # Process has terminated
                logger.info(f"Background Eel process {process.args} (PID: {process.pid}) terminated with exit code {process.returncode}")
                terminated_processes.append(process)

        for process in terminated_processes:
            active_eel_processes.remove(process)

        if terminated_processes and gaze_tracker_instance is None:
            # If any Eel process terminated and gaze tracker is not active, re-initialize
            logger.info("Re-initializing GazeTracker in main process after Eel app termination.")
            gaze_tracker_instance = GazeTracker(screen_width=screen_width, screen_height=screen_height)
            logger.info("GazeTracker re-initialized.")

        time.sleep(2) # Check every 2 seconds

# Start Eel process monitor thread
monitor_thread = threading.Thread(target=monitor_eel_processes, daemon=True)
monitor_thread.start()

eel.start('main.html', size=(screen_width, screen_height), port=8000)
logger.info("Eel application finished.")

# Release gaze tracker resources when Eel app closes
if gaze_tracker_instance:
    gaze_tracker_instance.release()