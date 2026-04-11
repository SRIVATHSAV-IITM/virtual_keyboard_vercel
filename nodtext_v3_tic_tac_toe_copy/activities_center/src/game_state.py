import logging
import time
import random
import pygame
from src.ui_elements import Button, WordBox
from src.assets import IMAGE_PATHS, ENCOURAGEMENT_QUOTES

logger = logging.getLogger(__name__)

class GameplayState:
    def __init__(self, manager):
        self.manager = manager
        self.screen = manager.screen
        self.gaze_tracker = manager.gaze_tracker
        self.dwell_time = 0.6
        self.gaze_activation_delay = 2.0
        self.state_start_time = time.time()
        self.round_index = manager.selected_round  # 0/1/2 depending on level
        self.selected_words = []
        self.box_error_flags = [False]*9  # max 9 boxes
        self.error_flash_time = [0]*9
        self.flash_duration = 0.5  # seconds
        self.show_feedback = False
        self.feedback_is_correct = False
        self.feedback_msg = ""
        self.next_button = None

        logger.info("GameplayState initialized for round %d", self.round_index+1)

        self.bg_image = pygame.image.load(IMAGE_PATHS["space_image"])
        self.bg_image = pygame.transform.scale(self.bg_image, (self.screen.get_width(), self.screen.get_height()))
        logger.debug("Background image loaded and scaled")

        # Levels: increase word count per round!
        self.level_sentences = [
            ["My", "name", "is", "Priya"],  # 4 words (Level 1)
            ["I", "always", "try", "my", "best", "level"],  # 6 words (Level 2)
            ["Learning", "new", "things", "makes", "me", "stronger", "and", "happier", "!"],  # 9 words (Level 3)
        ]
        self.target_sentence = self.level_sentences[self.round_index]

        # --- LAYOUT: Fixed word-box area (center) ---
        self.area_rect = pygame.Rect(
            int(self.screen.get_width() * 0.05),
            int(self.screen.get_height() * 0.22),
            int(self.screen.get_width() * 0.90),
            int(self.screen.get_height() * 0.52)
        )

        # Fonts: Fixed for top bars and popup, responsive for word boxes
        self.top_font = pygame.font.SysFont(None, 62)
        self.popup_font = pygame.font.SysFont(None, 54)
        self.popup_btn_font = pygame.font.SysFont(None, 72)

        self.create_word_boxes()
        self.create_control_buttons()

    def create_word_boxes(self):
        words = self.target_sentence.copy()
        n = len(words)
        random.shuffle(words)
        if n == 4:
            rows, cols = 2, 2
        elif n == 6:
            rows, cols = 2, 3
        elif n == 9:
            rows, cols = 3, 3
        else:
            rows, cols = 1, n  # fallback

        area_w, area_h = self.area_rect.width, self.area_rect.height
        spacing_x, spacing_y = 34, 34
        box_w = int((area_w - (cols-1)*spacing_x) / cols)
        box_h = int((area_h - (rows-1)*spacing_y) / rows)

        # Dynamic font size for boxes
        if n == 4:
            box_font_size = int(min(box_w, box_h) * 0.63)
        elif n == 6:
            box_font_size = int(min(box_w, box_h) * 0.54)
        elif n == 9:
            box_font_size = int(min(box_w, box_h) * 0.44)
        else:
            box_font_size = int(min(box_w, box_h) * 0.48)
        self.box_font = pygame.font.SysFont(None, max(30, box_font_size))

        self.word_boxes = []
        positions = []
        for i in range(n):
            row = i // cols
            col = i % cols
            x = self.area_rect.x + col * (box_w + spacing_x)
            y = self.area_rect.y + row * (box_h + spacing_y)
            positions.append((x, y))
        base_colors = [
            (135, 206, 235), (144, 238, 144), (255, 182, 193),
            (255, 250, 205), (255, 160, 122), (221, 160, 221),
            (255, 218, 185), (240, 230, 140), (152, 251, 152),
        ]
        for i, word in enumerate(words):
            color = base_colors[i % len(base_colors)]
            wb = WordBox(positions[i][0], positions[i][1], box_w, box_h, word, self.box_font, color)
            wb.is_error = False
            self.word_boxes.append(wb)

    def create_control_buttons(self):
        # Large, pushed up from screen bottom
        screen_w = self.screen.get_width()
        screen_h = self.screen.get_height()
        button_w = int(screen_w * 0.20)
        button_h = int(screen_h * 0.13)
        spacing = int(screen_w * 0.033)
        margin_bottom = int(screen_h * 0.19)  # Push up from bottom
        start_x = (screen_w - (button_w * 4 + spacing * 3)) // 2
        y = screen_h - margin_bottom

        labels = ["Backspace", "Try Again", "Next", "Exit"]
        self.control_buttons = []
        btn_font = pygame.font.SysFont(None, 58)
        for i, label in enumerate(labels):
            x = start_x + i * (button_w + spacing)
            btn = Button(x, y, button_w, button_h, label, btn_font)
            self.control_buttons.append(btn)

    def gaze_active(self):
        return (time.time() - self.state_start_time) > self.gaze_activation_delay

    def check_sentence(self):
        return self.selected_words == self.target_sentence

    def update(self):
        gaze_pos = self.gaze_tracker.get_gaze_point()
        now = time.time()
        for i, wb in enumerate(self.word_boxes):
            if wb.is_error and now - self.error_flash_time[i] > self.flash_duration:
                wb.is_error = False
                wb.color_reset()

        if gaze_pos == (None, None) or not self.gaze_active():
            for wb in self.word_boxes:
                wb.reset_hover()
            for btn in self.control_buttons:
                btn.reset_hover()
            return

        # Select word box
        if len(self.selected_words) < len(self.target_sentence):
            for i, wb in enumerate(self.word_boxes):
                wb.update_hover(gaze_pos, self.dwell_time)
                if wb.is_selected(self.dwell_time):
                    expected_word = self.target_sentence[len(self.selected_words)]
                    if wb.label.strip() == expected_word.strip():
                        self.selected_words.append(wb.label)
                        self.word_boxes.pop(i)
                        self.manager.audio_manager.play_game_button_sound()
                        break
                    else:
                        wb.is_error = True
                        self.error_flash_time[i] = now
                        self.manager.audio_manager.play_error_sound()
                        break

            for btn in self.control_buttons:
                btn.update_hover(gaze_pos, self.dwell_time)
                if btn.is_selected(self.dwell_time):
                    label = btn.label.lower()
                    self.manager.audio_manager.play_other_button_sound()
                    if label == "backspace" and self.selected_words:
                        self.selected_words.pop()
                        self.create_word_boxes()
                    elif label == "try again":
                        self.selected_words.clear()
                        self.create_word_boxes()
                    elif label == "next":
                        next_round = (self.round_index + 1) % len(self.level_sentences)
                        self.manager.selected_round = next_round
                        from src.game_state import GameplayState
                        self.manager.change_state(GameplayState(self.manager))
                    elif label == "exit":
                        self.manager.running = False
                    btn.reset_hover()
                    break

        # Show feedback overlay only ONCE
        if not self.show_feedback and len(self.selected_words) == len(self.target_sentence):
            if self.check_sentence():
                self.feedback_is_correct = True
                self.feedback_msg = random.choice(ENCOURAGEMENT_QUOTES)
                self.show_feedback = True
                # Overlay button inside overlay box
                overlay_width = 700
                overlay_height = 320
                overlay_x = self.screen.get_width()//2 - overlay_width//2
                overlay_y = self.screen.get_height()//2 - overlay_height//2
                btn_w, btn_h = 360, 108
                btn_x = self.screen.get_width()//2 - btn_w//2
                btn_y = overlay_y + overlay_height - btn_h - 34
                self.next_button = Button(btn_x, btn_y, btn_w, btn_h, "Next Round", self.popup_btn_font)
            else:
                self.feedback_is_correct = False
                self.feedback_msg = "Try Again! You're learning every time."
                self.show_feedback = True
                overlay_width = 700
                overlay_height = 320
                overlay_x = self.screen.get_width()//2 - overlay_width//2
                overlay_y = self.screen.get_height()//2 - overlay_height//2
                btn_w, btn_h = 360, 108
                btn_x = self.screen.get_width()//2 - btn_w//2
                btn_y = overlay_y + overlay_height - btn_h - 34
                self.next_button = Button(btn_x, btn_y, btn_w, btn_h, "Try Again", self.popup_btn_font)

        # Handle feedback overlay and next
        if self.show_feedback:
            if gaze_pos == (None, None) or not self.gaze_active():
                if self.next_button: self.next_button.reset_hover()
                return
            self.next_button.update_hover(gaze_pos, self.dwell_time)
            if self.next_button.is_selected(self.dwell_time):
                if self.feedback_is_correct:
                    next_round = (self.round_index + 1) % len(self.level_sentences)
                    self.manager.selected_round = next_round
                from src.game_state import GameplayState
                self.manager.change_state(GameplayState(self.manager))
                self.show_feedback = False
                self.selected_words.clear()
                self.create_word_boxes()
                self.next_button.reset_hover()

    def render(self):
        self.screen.blit(self.bg_image, (0, 0))
        screen_w = self.screen.get_width()

        # --- Fixed Target and Current bars at top ---
        fixed_bar_width = int(self.screen.get_width() * 0.9)
        fixed_bar_height = 72
        fixed_bar_x = int(self.screen.get_width() * 0.05)
        target_rect = pygame.Rect(fixed_bar_x, 22, fixed_bar_width, fixed_bar_height)
        current_rect = pygame.Rect(fixed_bar_x, 112, fixed_bar_width, fixed_bar_height)
        pygame.draw.rect(self.screen, (144, 238, 144), target_rect, border_radius=13)
        pygame.draw.rect(self.screen, (0,0,0), target_rect, 3, border_radius=13)
        pygame.draw.rect(self.screen, (173, 216, 230), current_rect, border_radius=10)
        pygame.draw.rect(self.screen, (0,0,0), current_rect, 3, border_radius=10)
        target_text = self.top_font.render(f"Target: {' '.join(self.target_sentence)}", True, (0, 100, 0))
        self.screen.blit(target_text, target_text.get_rect(center=target_rect.center))
        current_text_str = " ".join(self.selected_words) if self.selected_words else ""
        current_text = self.top_font.render(f"Current: {current_text_str}", True, (0, 0, 0))
        self.screen.blit(current_text, current_text.get_rect(center=current_rect.center))

        # --- Fixed middle area for word boxes ---
        pygame.draw.rect(self.screen, (220, 220, 220), self.area_rect, border_radius=22)
        pygame.draw.rect(self.screen, (100, 100, 100), self.area_rect, 4, border_radius=22)

        for wb in self.word_boxes:
            wb.draw(self.screen)

        for btn in self.control_buttons:
            btn.draw(self.screen)

        # Feedback Overlay
        if self.show_feedback:
            overlay_width = 700
            overlay_height = 320
            overlay_x = self.screen.get_width()//2 - overlay_width//2
            overlay_y = self.screen.get_height()//2 - overlay_height//2
            overlay_rect = pygame.Rect(overlay_x, overlay_y, overlay_width, overlay_height)
            pygame.draw.rect(self.screen, (255,255,255), overlay_rect, border_radius=28)
            pygame.draw.rect(self.screen, (0,150,0) if self.feedback_is_correct else (200,50,50),
                             overlay_rect, 6, border_radius=28)
            feedback = self.popup_font.render(self.feedback_msg, True,
                                              (20,90,20) if self.feedback_is_correct else (200,50,50))
            feedback_rect = feedback.get_rect(center=(self.screen.get_width()//2, overlay_y + 100))
            self.screen.blit(feedback, feedback_rect)
            if self.next_button:
                self.next_button.draw(self.screen)

        gaze_pos = self.gaze_tracker.get_gaze_point()
        if gaze_pos != (None, None):
            pygame.draw.circle(self.screen, (255, 0, 0), gaze_pos, 12)
