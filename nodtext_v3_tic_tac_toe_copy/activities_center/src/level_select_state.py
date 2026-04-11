import pygame
import time
from src.ui_elements import Button
from src.assets import IMAGE_PATHS

class LevelSelectState:
    def __init__(self, manager):
        self.manager = manager
        self.screen = manager.screen
        self.gaze_tracker = manager.gaze_tracker
        self.font = pygame.font.SysFont(None, 75)
        self.small_font = pygame.font.SysFont(None, 48)
        self.state_start_time = time.time()
        self.dwell_time = 0.7
        self.gaze_activation_delay = 1.0

        self.bg_image = pygame.image.load(IMAGE_PATHS["welcome_bg"])
        self.bg_image = pygame.transform.scale(self.bg_image, (self.screen.get_width(), self.screen.get_height()))

        self.create_level_buttons()

    def create_level_buttons(self):
        screen_w = self.screen.get_width()
        screen_h = self.screen.get_height()
        button_w = int(screen_w * 0.22)
        button_h = int(screen_h * 0.15)
        spacing = int(screen_h * 0.07)
        base_y = int(screen_h * 0.35)
        center_x = screen_w // 2

        self.level_buttons = []
        levels = [("Level 1", 0), ("Level 2", 1), ("Level 3", 2)]
        for i, (label, round_idx) in enumerate(levels):
            x = center_x - button_w // 2
            y = base_y + i * (button_h + spacing)
            btn = Button(x, y, button_w, button_h, label, self.small_font)
            btn.level_index = round_idx
            self.level_buttons.append(btn)

    def gaze_active(self):
        return (time.time() - self.state_start_time) > self.gaze_activation_delay

    def update(self):
        gaze_pos = self.gaze_tracker.get_gaze_point()
        if gaze_pos == (None, None) or not self.gaze_active():
            for btn in self.level_buttons:
                btn.reset_hover()
            return

        for btn in self.level_buttons:
            btn.update_hover(gaze_pos, self.dwell_time)
            if btn.is_selected(self.dwell_time):
                self.manager.audio_manager.play_game_button_sound()
                self.manager.selected_round = btn.level_index
                from src.game_state import GameplayState
                self.manager.change_state(GameplayState(self.manager))
                btn.reset_hover()
                break

    def render(self):
        self.screen.blit(self.bg_image, (0, 0))
        # Title
        title_rect = pygame.Rect(self.screen.get_width()*0.20, 60, self.screen.get_width()*0.60, 80)
        pygame.draw.rect(self.screen, (255,255,255), title_rect, border_radius=16)
        pygame.draw.rect(self.screen, (44, 120, 220), title_rect, 4, border_radius=16)
        title = self.font.render("Select Your Level", True, (44,120,220))
        self.screen.blit(title, title.get_rect(center=title_rect.center))

        for btn in self.level_buttons:
            btn.draw(self.screen)

        # Draw gaze point if available
        gaze_pos = self.gaze_tracker.get_gaze_point()
        if gaze_pos != (None, None):
            pygame.draw.circle(self.screen, (255, 0, 0), gaze_pos, 13)
