import logging
import pygame
from src.assets import AUDIO_PATHS  # <-- Centralized paths!

logger = logging.getLogger(__name__)

class AudioManager:
    def __init__(self):
        logger.info("Initializing AudioManager with asset paths")
        try:
            pygame.mixer.init()
            logger.debug("Pygame mixer initialized successfully")
        except Exception as e:
            logger.exception("Failed to initialize pygame mixer: %s", e)

        self.bg_music_path = AUDIO_PATHS["bg_music"]

        try:
            self.game_button_sound = pygame.mixer.Sound(AUDIO_PATHS["game_button"])
            logger.debug("Loaded game button sound from %s", AUDIO_PATHS["game_button"])
        except Exception as e:
            logger.exception("Failed to load game button sound: %s", e)
            self.game_button_sound = None

        try:
            self.other_button_sound = pygame.mixer.Sound(AUDIO_PATHS["other_button"])
            logger.debug("Loaded other button sound from %s", AUDIO_PATHS["other_button"])
        except Exception as e:
            logger.exception("Failed to load other button sound: %s", e)
            self.other_button_sound = None

        # Error sound for wrong answer
        try:
            self.error_sound = pygame.mixer.Sound(AUDIO_PATHS["error_sound"])
            logger.debug("Loaded error sound from %s", AUDIO_PATHS["error_sound"])
        except Exception as e:
            logger.exception("Failed to load error sound: %s", e)
            self.error_sound = None

    def play_bg_music(self):
        logger.debug("Loading and playing background music: %s", self.bg_music_path)
        try:
            pygame.mixer.music.load(self.bg_music_path)
            pygame.mixer.music.play(-1)  # loop indefinitely
            logger.info("Background music started")
        except Exception as e:
            logger.exception("Failed to play background music: %s", e)

    def stop_bg_music(self):
        logger.debug("Stopping background music")
        try:
            pygame.mixer.music.stop()
            logger.info("Background music stopped")
        except Exception as e:
            logger.exception("Failed to stop background music: %s", e)

    def play_game_button_sound(self):
        logger.debug("Playing game button sound")
        if self.game_button_sound:
            try:
                self.game_button_sound.play()
                logger.info("Game button sound played")
            except Exception as e:
                logger.exception("Failed to play game button sound: %s", e)
        else:
            logger.warning("Game button sound is not loaded; cannot play")

    def play_other_button_sound(self):
        logger.debug("Playing other button sound")
        if self.other_button_sound:
            try:
                self.other_button_sound.play()
                logger.info("Other button sound played")
            except Exception as e:
                logger.exception("Failed to play other button sound: %s", e)
        else:
            logger.warning("Other button sound is not loaded; cannot play")

    def play_error_sound(self):
        logger.debug("Playing error sound")
        if self.error_sound:
            try:
                self.error_sound.play()
                logger.info("Error sound played")
            except Exception as e:
                logger.exception("Failed to play error sound: %s", e)
        else:
            logger.warning("Error sound is not loaded; cannot play")

    def quit(self):
        logger.debug("Quitting AudioManager and shutting down mixer")
        try:
            pygame.mixer.quit()
            logger.info("Pygame mixer quit successfully")
        except Exception as e:
            logger.exception("Failed to quit pygame mixer: %s", e)
