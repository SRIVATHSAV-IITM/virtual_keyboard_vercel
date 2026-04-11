import pygame
import time
import random
import logging
from src.ui_elements import Button
from src.assets import IMAGE_PATHS, ENCOURAGEMENT_QUOTES

logger = logging.getLogger(__name__)

class WelcomeState:
    def __init__(self, manager):
        self.manager = manager
        self.screen = manager.screen
        self.gaze_tracker = manager.gaze_tracker
        self.font = pygame.font.SysFont(None, 80)
        self.small_font = pygame.font.SysFont(None, 48)
        self.state_start_time = time.time()
        self.dwell_time = 0.7
        self.gaze_activation_delay = 1.2
        logger.info("WelcomeState initialized.")

        # Load background image
        self.bg_image = pygame.image.load(IMAGE_PATHS["welcome_bg"])
        self.bg_image = pygame.transform.scale(self.bg_image, (self.screen.get_width(), self.screen.get_height()))

        self.buttons = []
        self.create_buttons()
        self.last_quote = random.choice(ENCOURAGEMENT_QUOTES)

    def create_buttons(self):
        screen_w = self.screen.get_width()
        screen_h = self.screen.get_height()
        button_w = int(screen_w * 0.4)
        button_h = int(screen_h * 0.25)
        spacing = int(screen_w * 0.07)
        center_x = screen_w // 2
        y = int(screen_h * 0.65)

        labels = ["Start", "Exit"]
        self.buttons = []
        for i, label in enumerate(labels):
            # Calculate left and right positions
            x = center_x - button_w - spacing//2 if i == 0 else center_x + spacing//2
            btn = Button(x, y, button_w, button_h, label, self.small_font)
            self.buttons.append(btn)


    def gaze_active(self):
        return (time.time() - self.state_start_time) > self.gaze_activation_delay

    def update(self):
        gaze_pos = self.gaze_tracker.get_gaze_point()
        logger.debug(f"Gaze position in WelcomeState update: {gaze_pos}")
        if gaze_pos == (None, None) or not self.gaze_active():
            for btn in self.buttons:
                btn.reset_hover()
            return

        for btn in self.buttons:
            btn.update_hover(gaze_pos, self.dwell_time)
            if btn.is_selected(self.dwell_time):
                label = btn.label.lower()
                self.manager.audio_manager.play_game_button_sound()
                if label == "start":
                    from src.level_select_state import LevelSelectState
                    self.manager.change_state(LevelSelectState(self.manager))
                elif label == "exit":
                    self.manager.running = False # Signal main loop to exit
                btn.reset_hover()
                break

    def render(self):
        self.screen.blit(self.bg_image, (0, 0))

        # Title
        title_rect = pygame.Rect(self.screen.get_width()*0.12, 40, self.screen.get_width()*0.76, 100)
        pygame.draw.rect(self.screen, (255,255,255), title_rect, border_radius=18)
        pygame.draw.rect(self.screen, (44, 120, 220), title_rect, 6, border_radius=18)
        title = self.font.render("Welcome to Space Confidence!", True, (44,120,220))
        self.screen.blit(title, title.get_rect(center=title_rect.center))

        # Encouragement/quote
        quote_rect = pygame.Rect(self.screen.get_width()*0.20, 180, self.screen.get_width()*0.60, 65)
        pygame.draw.rect(self.screen, (255, 250, 205), quote_rect, border_radius=12)
        quote = self.small_font.render(self.last_quote, True, (80,70,20))
        self.screen.blit(quote, quote.get_rect(center=quote_rect.center))

        # Draw all buttons
        for btn in self.buttons:
            btn.draw(self.screen)

        # Draw gaze point if available
        gaze_pos = self.gaze_tracker.get_gaze_point()
        if gaze_pos != (None, None):
            pygame.draw.circle(self.screen, (255, 0, 0), gaze_pos, 13)
