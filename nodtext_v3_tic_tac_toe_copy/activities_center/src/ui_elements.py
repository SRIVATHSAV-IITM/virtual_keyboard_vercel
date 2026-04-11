import logging
import pygame

logger = logging.getLogger(__name__)

class Button:
    """
    Represents a clickable or gaze-selectable button.
    """
    def __init__(self, x, y, width, height, label, font, base_color=(200, 200, 200), hover_color=(150, 220, 180)):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.font = font
        self.base_color = base_color
        self.hover_color = hover_color
        self.color = base_color
        self.hover_start = None
        self.hover_progress = 0
        self.selected = False
        logger.info("Button initialized: '%s' at (%d, %d, %d, %d)", label, x, y, width, height)

    def update_hover(self, gaze_pos, dwell_time):
        """
        Update button hover state and selection based on gaze position and dwell time.
        """
        logger.debug("Button '%s' update_hover called with gaze_pos=%s, dwell_time=%.2f", self.label, gaze_pos, dwell_time)
        if self.rect.collidepoint(gaze_pos):
            if self.hover_start is None:
                self.hover_start = pygame.time.get_ticks()
                logger.debug("Button '%s' hover started at tick=%d", self.label, self.hover_start)
            elapsed = (pygame.time.get_ticks() - self.hover_start) / 1000.0
            self.color = self.hover_color
            self.hover_progress = min(elapsed / dwell_time, 1.0)
            logger.debug("Button '%s' hover progress=%.2f", self.label, self.hover_progress)
            if elapsed >= dwell_time and not self.selected:
                self.selected = True
                logger.info("Button '%s' selected after dwelling %.2f seconds", self.label, elapsed)
        else:
            if self.hover_start is not None or self.selected:
                logger.debug("Button '%s' hover/reset triggered, resetting state", self.label)
            self.color = self.base_color
            self.hover_start = None
            self.hover_progress = 0
            self.selected = False

    def reset_hover(self):
        """
        Reset the hover state of the button.
        """
        logger.debug("Button '%s' reset_hover called", self.label)
        self.hover_start = None
        self.hover_progress = 0
        self.selected = False
        self.color = self.base_color

    def is_selected(self, dwell_time):
        logger.debug("Button '%s' is_selected check: %s", self.label, self.selected)
        return self.selected

    def draw(self, screen):
        logger.debug("Button '%s' draw called with color=%s", self.label, self.color)
        # Draw the base button
        pygame.draw.rect(screen, self.base_color, self.rect)

        # Draw the hover progress fill
        if self.hover_progress > 0:
            progress_width = int(self.rect.width * self.hover_progress)
            progress_rect = pygame.Rect(self.rect.left, self.rect.top, progress_width, self.rect.height)
            pygame.draw.rect(screen, self.hover_color, progress_rect)

        # Draw the button border
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 3)

        # Draw the button label
        text_surface = self.font.render(self.label, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    @staticmethod
    def centered(screen, width, height, label, font, base_color=(200,200,200), hover_color=(150,220,180)):
        """
        Utility: create a button centered on the screen.
        """
        sw, sh = screen.get_width(), screen.get_height()
        x = (sw - width) // 2
        y = (sh - height) // 2
        return Button(x, y, width, height, label, font, base_color, hover_color)


class WordBox:
    """
    Represents a draggable or gaze-selectable word box.
    """

    def __init__(self, x, y, width, height, label, font, base_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.font = font
        self.base_color = base_color
        self.hover_color = (min(base_color[0] + 30, 255), min(base_color[1] + 30, 255), min(base_color[2] + 30, 255))
        self.color = base_color
        self.hover_start = None
        self.hover_progress = 0
        self.selected = False
        self.is_error = False
        logger.info("WordBox initialized: '%s' at (%d, %d, %d, %d)", label, x, y, width, height)

    def update_hover(self, gaze_pos, dwell_time):
        logger.debug("WordBox '%s' update_hover with gaze_pos=%s, dwell_time=%.2f", self.label, gaze_pos, dwell_time)
        if self.rect.collidepoint(gaze_pos):
            if self.hover_start is None:
                self.hover_start = pygame.time.get_ticks()
                logger.debug("WordBox '%s' hover started at tick=%d", self.label, self.hover_start)
            elapsed = (pygame.time.get_ticks() - self.hover_start) / 1000.0
            self.color = self.hover_color
            self.hover_progress = min(elapsed / dwell_time, 1.0)
            logger.debug("WordBox '%s' hover progress=%.2f", self.label, self.hover_progress)
            if elapsed >= dwell_time and not self.selected:
                self.selected = True
                logger.info("WordBox '%s' selected after dwelling %.2f seconds", self.label, elapsed)
        else:
            if self.hover_start is not None or self.selected:
                logger.debug("WordBox '%s' hover/reset triggered, resetting state", self.label)
            self.color = self.base_color
            self.hover_start = None
            self.hover_progress = 0
            self.selected = False

    def reset_hover(self):
        logger.debug("WordBox '%s' reset_hover called", self.label)
        self.hover_start = None
        self.hover_progress = 0
        self.selected = False
        self.color = self.base_color

    def is_selected(self, dwell_time):
        logger.debug("WordBox '%s' is_selected check: %s", self.label, self.selected)
        return self.selected

    def draw(self, screen):
        # Show red color if error, else hover/base color
        color = (255, 80, 80) if self.is_error else (self.hover_color if self.hover_progress > 0 else self.base_color)
        logger.debug("WordBox '%s' draw called with color=%s", self.label, color)
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 3)
        text_surface = self.font.render(self.label, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        if self.hover_progress > 0:
            bar_height = 8
            progress_width = int(self.rect.width * self.hover_progress)
            bar_rect = pygame.Rect(self.rect.left, self.rect.bottom - bar_height, progress_width, bar_height)
            pygame.draw.rect(screen, (0, 180, 0), bar_rect)
            logger.debug("WordBox '%s' dwell bar drawn with progress_width=%d", self.label, progress_width)

    def set_error(self):
        self.is_error = True

    def color_reset(self):
        self.is_error = False
        self.color = self.base_color
