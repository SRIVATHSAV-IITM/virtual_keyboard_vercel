import os
import warnings

# Suppress TensorFlow and MediaPipe warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['GLOG_minloglevel'] = '2'
os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'  # Suppress SDL2 duplicate library warnings
warnings.filterwarnings("ignore", category=UserWarning, module="google.protobuf.symbol_database")

import logging
import cv2
import mediapipe as mp
import numpy as np

logger = logging.getLogger(__name__)

class GazeTracker:
    """
    Tracks user's gaze using MediaPipe FaceMesh and maps to screen coordinates.
    """
    def __init__(self, screen_width=1280, screen_height=720, sensitivity=6, smoothing_factor=0.1, camera_index=0):
        logger.info("Initializing GazeTracker")
        self.cap = None
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                self.cap = cap
                logger.info(f"Successfully opened camera with index {i}")
                break
        if self.cap is None:
            logger.error("Failed to open any camera. Please ensure a camera is connected and not in use by another application.")

        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(refine_landmarks=True)
        self.LEFT_IRIS = [468, 469, 470, 471]
        self.RIGHT_IRIS = [473, 474, 475, 476]
        self.sensitivity = sensitivity
        self.smoothing_factor = smoothing_factor
        self.prev_gaze_x = None
        self.prev_gaze_y = None
        self.screen_width = screen_width
        self.screen_height = screen_height
        logger.debug("GazeTracker initialized with screen size: %dx%d", screen_width, screen_height)

    def get_iris_center(self, landmarks, indices, frame_w, frame_h):
        """
        Compute the center of the iris using landmark indices.
        """
        logger.debug("Calculating iris center for indices: %s", indices)
        x = int(np.mean([landmarks[i].x for i in indices]) * frame_w)
        y = int(np.mean([landmarks[i].y for i in indices]) * frame_h)
        logger.debug("Iris center calculated at: (%d, %d)", x, y)
        return x, y

    def get_smoothed_gaze(self, gaze_x, gaze_y):
        """
        Applies smoothing to gaze coordinates.
        """
        logger.debug("Smoothing gaze: raw=(%d, %d)", gaze_x, gaze_y)
        if self.prev_gaze_x is None or self.prev_gaze_y is None:
            self.prev_gaze_x, self.prev_gaze_y = gaze_x, gaze_y
            logger.debug("Initial smoothing state set")
        else:
            alpha = self.smoothing_factor
            self.prev_gaze_x = alpha * gaze_x + (1 - alpha) * self.prev_gaze_x
            self.prev_gaze_y = alpha * gaze_y + (1 - alpha) * self.prev_gaze_y
            logger.debug("Smoothed gaze: (%.1f, %.1f)", self.prev_gaze_x, self.prev_gaze_y)
        return int(self.prev_gaze_x), int(self.prev_gaze_y)

    def get_gaze_point(self):
        """
        Captures a camera frame and returns the mapped screen gaze coordinates.
        """
        logger.debug("Capturing frame from camera")
        ret, frame = self.cap.read()
        if not ret:
            logger.warning("Failed to capture frame from camera")
            return None, None

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        if results.multi_face_landmarks:
            logger.debug("Face landmarks detected")
            landmarks = results.multi_face_landmarks[0].landmark
            lx, ly = self.get_iris_center(landmarks, self.LEFT_IRIS, w, h)
            rx, ry = self.get_iris_center(landmarks, self.RIGHT_IRIS, w, h)

            avg_x = (lx + rx) / 2
            avg_y = (ly + ry) / 2
            logger.debug("Averaged iris center: (%.2f, %.2f)", avg_x, avg_y)

            norm_x = 0.5 + (avg_x / w - 0.5) * self.sensitivity
            norm_y = 0.5 + (avg_y / h - 0.5) * self.sensitivity

            norm_x = np.clip(norm_x, 0, 1)
            norm_y = np.clip(norm_y, 0, 1)

            gaze_x = int(norm_x * self.screen_width)
            gaze_y = int(norm_y * self.screen_height)
            logger.debug("Mapped gaze to screen: (%d, %d)", gaze_x, gaze_y)

            gaze_x, gaze_y = self.get_smoothed_gaze(gaze_x, gaze_y)
            logger.info("Final gaze coordinates: (%d, %d)", gaze_x, gaze_y)
            return gaze_x, gaze_y

        logger.debug("No face landmarks detected")
        return None, None

    def release(self):
        """
        Release the camera resource.
        """
        logger.info("Releasing camera resource")
        self.cap.release()

    def __del__(self):
        # Auto-release when object is deleted (safety)
        if hasattr(self, 'cap') and self.cap and self.cap.isOpened():
            self.cap.release()