# Mirra v2 Project Overview

This document provides a detailed overview of the Mirra v2 project, its current state, the issues addressed, and the remaining tasks.

## Project Purpose
Mirra v2 is an eye-gaze controlled application designed to provide an accessible interface for various activities, including a snake game, a virtual keyboard, and an activities center. The core functionality relies on a `GazeTracker` to interpret eye movements for navigation and interaction.

## Current Project Structure
The project is structured into a main application (`main.py`) that uses `eel` for its web-based UI, and several sub-applications located in dedicated directories (`snake_game/`, `virtual_keyboard/`, `activities_center/`). A shared `gaze_tracker.py` module is used for eye-gaze tracking functionality. Logging is handled by `logger_reporter.py`.

## Issues Addressed So Far

1.  **`ModuleNotFoundError: No module named 'gaze_tracker'`**:
    *   **Problem**: Sub-applications were unable to import the `GazeTracker` module due to incorrect `sys.path` configurations.
    *   **Solution**: Corrected `sys.path.append` statements in `activities_center/main.py`, `snake_game/snake.py`, and `virtual_keyboard/keyboard.py` to correctly point to the `shared_src` directory.

2.  **`NameError: name 'GazeTracker' is not defined`**:
    *   **Problem**: Sub-applications were missing explicit import statements for `GazeTracker`.
    *   **Solution**: Added `from gaze_tracker import GazeTracker` to the relevant sub-application files.

3.  **`AttributeError: 'NoneType' object has no attribute 'get_gaze_point'`**:
    *   **Problem**: The `gaze_tracker_instance` in `main.py` was being set to `None` while the gaze tracking thread was still attempting to use it.
    *   **Solution**: Implemented a check (`if gaze_tracker_instance:`) before calling `get_gaze_point()` in `main.py`'s `gaze_tracking_thread`.

4.  **Inconsistent Logging (`main_application.log`)**:
    *   **Problem**: An older log file (`main_application.log`) was present, suggesting potential misconfiguration or redundant logging.
    *   **Solution**: Confirmed that `main.py` correctly logs to `main_application_main.log` and removed the redundant `main_application.log`.

5.  **GazeTracker Persistence Across Sub-applications**:
    *   **Problem**: The `GazeTracker` instance in `main.py` was not being properly released and re-initialized when launching and exiting sub-applications, leading to camera and gaze pointer issues.
    *   **Solution**: Modified `main.py`'s `run_subprocess` function to:
        *   Release `gaze_tracker_instance` before launching a sub-process.
        *   Introduce a `time.sleep(1)` delay after releasing the `GazeTracker`.
        *   Re-initialize `gaze_tracker_instance` in the `finally` block after the sub-process completes.
    *   Modified sub-applications to manage their own `GazeTracker` instances, initializing them on startup and releasing them on exit.
    *   Removed passing of `gaze_x` and `gaze_y` as command-line arguments to sub-applications, as they now handle their own gaze data.

6.  **`NameError: name 'time' is not defined`**:
    *   **Problem**: The `time.sleep(1)` call in `main.py` was missing the `import time` statement.
    *   **Solution**: Added `import time` to `main.py`.

## Remaining Tasks

1.  **Button Dwell Color Filling in Snake Game**:
    *   **Problem**: The dwell green color filling is not happening for the first three buttons in the Snake Game menu; it only works for the exit button.
    *   **Action**: Investigate the `draw_button` function and button rendering logic in `snake_game/snake.py` to ensure consistent dwell feedback for all buttons.

2.  **Gaze Pointer Movement in Snake Game**:
    *   **Problem**: The blue gaze pointer is visible in the Snake Game but does not move, indicating that gaze data is not being continuously updated within the game.
    *   **Action**: Verify that the `GazeTracker` in `snake_game/snake.py` is actively providing updated gaze coordinates to the game loop.

3.  **Implement Gaze Tracking for Virtual Keyboard and Activities Center**:
    *   **Problem**: Gaze tracking functionality needs to be fully implemented and verified for the Virtual Keyboard and Activities Center, similar to the Snake Game.
    *   **Action**: Ensure these applications correctly initialize, use, and release their `GazeTracker` instances, and that their UI elements respond to gaze input as intended.

4.  **General Code Review and Refinement**:
    *   **Problem**: General code quality, adherence to best practices, and potential optimizations.
    *   **Action**: Conduct a thorough review of the entire codebase for consistency, efficiency, and maintainability.