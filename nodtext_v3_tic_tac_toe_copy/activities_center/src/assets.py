# assets.py

import os

# Base path that auto-detects the MIRRA_v1 directory
BASE_PATH = os.path.dirname(os.path.abspath(__file__))  # This gives .../MIRRA_v1/src
BASE_DIR = os.path.abspath(os.path.join(BASE_PATH, os.pardir))  # Moves one level up to .../MIRRA_v1

AUDIO_PATHS = {
    "bg_music": os.path.join(BASE_DIR, "assets", "audio", "background_music.mp3"),
    "game_button": os.path.join(BASE_DIR, "assets", "audio", "game_button.mp3"),
    "other_button": os.path.join(BASE_DIR, "assets", "audio", "other_button.mp3"),
    "error_sound": os.path.join(BASE_DIR, "assets", "audio", "error_beep.mp3"),
}

IMAGE_PATHS = {
    "space_image": os.path.join(BASE_DIR, "assets", "images", "space_image.png"),
    "welcome_bg": os.path.join(BASE_DIR, "assets", "images", "welcome_bg.png"),
}


ENCOURAGEMENT_QUOTES = [
    "You did it, Priya! Keep shining!",
    "Great job! You're amazing!",
    "That’s correct! You have a strong will, Priya!",
    "Wonderful! You are unstoppable!",
    "Perfect! Every step you take is progress.",
    "Well done, Priya! You’re becoming stronger every day!"
]

TRY_AGAIN_QUOTES = [
    "Try again, Priya! You can do this!",
    "Don't give up! Your willpower is inspiring.",
    "Mistakes are proof that you are trying. Try again!",
    "Courage is not giving up. Go for it again!"
]
