import pygame, sys, random
import os
from pygame.math import Vector2
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'shared_src')))
from logger_reporter import setup_logging
from gaze_tracker import GazeTracker
import cv2
import numpy as np
import eel

# Global variable to store gaze coordinates received from main.py
global_gaze_x, global_gaze_y = None, None

@eel.expose
def update_gaze_coordinates(x, y):
    global global_gaze_x, global_gaze_y
    global_gaze_x, global_gaze_y = x, y

def main():
    logger = setup_logging("snake_game")
    logger.info("Snake Game application started.")
    pygame.init()

    # Get screen dimensions from command line arguments
    if len(sys.argv) > 4:
        global global_gaze_x, global_gaze_y
        screen_width = int(sys.argv[1])
        screen_height = int(sys.argv[2])
        global_gaze_x = int(float(sys.argv[3])) if sys.argv[3] != 'None' else None
        global_gaze_y = int(float(sys.argv[4])) if sys.argv[4] != 'None' else None
    else:
        # Fallback if arguments are not provided (e.g., for direct testing)
        screen_info = pygame.display.Info()
        screen_width = screen_info.current_w
        screen_height = screen_info.current_h
    
    # Initialize GazeTracker
    gaze_tracker = GazeTracker(screen_width=screen_width, screen_height=screen_height)

    # Fonts (using OpenCV's default font for simplicity)
    FONT = cv2.FONT_HERSHEY_SIMPLEX
    FONT_SCALE_TITLE = 2
    FONT_SCALE_SCORE = 1.5
    FONT_SCALE_BUTTON = 1
    FONT_THICKNESS = 2

    GREEN = (173, 204, 96)
    DARK_GREEN = (43, 51, 24)
    WHITE = (255, 255, 255)
    BUTTON_COLOR = (60, 179, 113) # MediumSeaGreen
    HOVER_COLOR = (50, 205, 50) # LimeGreen

    cell_size = 25  # Reduced cell size for more padding
    number_of_cells = 25
    
    # Calculate play zone dimensions (75% of screen height, centered horizontally)
    play_zone_height = int(screen_height * 0.75)
    play_zone_width = play_zone_height # Make it square
    play_zone_x = (screen_width - play_zone_width) // 2
    play_zone_y = (screen_height - play_zone_height) // 2
    play_zone_rect = pygame.Rect(play_zone_x, play_zone_y, play_zone_width, play_zone_height)

    # Adjust game board offsets to be relative to the play zone
    game_width = cell_size * number_of_cells
    game_height = cell_size * number_of_cells
    OFFSET_X = play_zone_x + (play_zone_width - game_width) // 2
    OFFSET_Y = play_zone_y + (play_zone_height - game_height) // 2

    # Initialize webcam and MediaPipe Face Mesh
    # cap = cv2.VideoCapture(0) # No longer needed, handled by GazeTracker
    # face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True) # No longer needed, handled by GazeTracker

    def resource_path(relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    class Food:
        def __init__(self, snake_body):
            self.position = self.generate_random_pos(snake_body)
            # Load food image as OpenCV image
            self.food_image = cv2.imread(resource_path("snake_game/Graphics/food.png"), cv2.IMREAD_UNCHANGED)
            if self.food_image is None:
                logger.error("Failed to load food image: %s", resource_path("snake_game/Graphics/food.png"))
            else:
                # Resize food image to cell_size
                self.food_image = cv2.resize(self.food_image, (cell_size, cell_size), interpolation=cv2.INTER_AREA)

        def draw(self, surface):
            x1 = OFFSET_X + int(self.position.x * cell_size)
            y1 = OFFSET_Y + int(self.position.y * cell_size)
            x2 = x1 + cell_size
            y2 = y1 + cell_size

            if self.food_image is not None:
                # Handle alpha channel if present
                if self.food_image.shape[2] == 4: # Has alpha channel
                    alpha_s = self.food_image[:, :, 3] / 255.0
                    alpha_l = 1.0 - alpha_s
                    for c in range(0, 3):
                        surface[y1:y2, x1:x2, c] = (alpha_s * self.food_image[:, :, c] + 
                                                    alpha_l * surface[y1:y2, x1:x2, c])
                else:
                    surface[y1:y2, x1:x2] = self.food_image

        def generate_random_cell(self):
            x = random.randint(0, number_of_cells - 1)
            y = random.randint(0, number_of_cells - 1)
            return Vector2(x, y)

        def generate_random_pos(self, snake_body):
            position = self.generate_random_cell()
            while position in snake_body:
                position = self.generate_random_cell()
            return position

    class Snake:
        def __init__(self):
            self.body = [Vector2(6, 9), Vector2(5, 9), Vector2(4, 9)]
            self.direction = Vector2(1, 0)
            self.add_segment = False
            pygame.mixer.init() # Initialize mixer for sounds
            self.eat_sound = pygame.mixer.Sound(resource_path("snake_game/Sounds/eat.mp3"))
            self.wall_hit_sound = pygame.mixer.Sound(resource_path("snake_game/Sounds/wall.mp3"))

        def draw(self, surface):
            for segment in self.body:
                x1 = OFFSET_X + int(segment.x * cell_size)
                y1 = OFFSET_Y + int(segment.y * cell_size)
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                cv2.rectangle(surface, (x1, y1), (x2, y2), (DARK_GREEN[2], DARK_GREEN[1], DARK_GREEN[0]), -1) # BGR
                cv2.rectangle(surface, (x1, y1), (x2, y2), (WHITE[2], WHITE[1], WHITE[0]), 2) # Border

        def update(self):
            self.body.insert(0, self.body[0] + self.direction)
            if self.add_segment:
                self.add_segment = False
            else:
                self.body = self.body[:-1]

        def reset(self):
            self.body = [Vector2(6, 9), Vector2(5, 9), Vector2(4, 9)]
            self.direction = Vector2(1, 0)

    class Game:
        def __init__(self):
            self.snake = Snake()
            self.food = Food(self.snake.body)
            self.state = "MENU" # Initial state is MENU
            self.score = 0
            self.selected_difficulty = None # New: to store selected difficulty
            self.last_action_button = None # New: to store the last button that performed an action

        def draw(self, surface):
            self.food.draw(surface)
            self.snake.draw(surface)

        def update(self):
            if self.state == "PLAYING": # Only update game logic if in PLAYING state
                self.snake.update()
                self.check_collision_with_food()
                self.check_collision_with_edges()
                self.check_collision_with_tail()

        def check_collision_with_food(self):
            if self.snake.body[0] == self.food.position:
                self.food.position = self.food.generate_random_pos(self.snake.body)
                self.snake.add_segment = True
                self.score += 1
                self.snake.eat_sound.play()

        def check_collision_with_edges(self):
            # Check collision with play zone boundaries
            head_x = OFFSET_X + self.snake.body[0].x * cell_size
            head_y = OFFSET_Y + self.snake.body[0].y * cell_size

            if not play_zone_rect.collidepoint(head_x, head_y):
                self.game_over()

        def game_over(self):
            self.state = "GAME_OVER" # New state for game over
            self.snake.wall_hit_sound.play()

        def reset_game(self):
            self.snake.reset()
            self.food.position = self.food.generate_random_pos(self.snake.body)
            self.score = 0

        def check_collision_with_tail(self):
            headless_body = self.snake.body[1:]
            if self.snake.body[0] in headless_body:
                self.game_over()

    # Initialize OpenCV window
    cv2.namedWindow("Retro Snake", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Retro Snake", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # Create a blank image for drawing (BGR format for OpenCV)
    game_display = np.zeros((screen_height, screen_width, 3), dtype=np.uint8)

    clock = pygame.time.Clock()

    game = Game()
    food_surface = pygame.image.load(resource_path("snake_game/Graphics/food.png"))

    # Difficulty levels (milliseconds per update)
    DIFFICULTY_LEVELS = {
        "Easy": 300,
        "Medium": 200,
        "Hard": 100,
        "Extreme": 50
    }
    current_difficulty_speed = DIFFICULTY_LEVELS["Medium"] # Default

    SNAKE_UPDATE = pygame.USEREVENT
    pygame.time.set_timer(SNAKE_UPDATE, current_difficulty_speed)

    # Dwell parameters
    DWELL_DURATION = 1.0 # seconds
    dwell_state = {
        "hover_button": None,
        "hover_start_time": None
    }

    running = True # Add this flag to control the main loop

    def draw_button(surface, rect, text, font_scale, font_thickness, is_active, is_dwelled_on, dwell_progress):
        color = BUTTON_COLOR
        text_color = WHITE
        
        # Convert rect to OpenCV coordinates (top-left, bottom-right)
        x1, y1, w, h = rect
        x2, y2 = x1 + w, y1 + h

        # Draw the base button
        cv2.rectangle(surface, (x1, y1), (x2, y2), (color[2], color[1], color[0]), -1) # BGR

        if is_dwelled_on: # Draw progress bar if dwelled on
            progress_rect_width = int(w * dwell_progress)
            cv2.rectangle(surface, (x1, y1), (x1 + progress_rect_width, y2), (HOVER_COLOR[2], HOVER_COLOR[1], HOVER_COLOR[0]), -1) # BGR
        
        # Center the text
        text_size = cv2.getTextSize(text, FONT, font_scale, font_thickness)[0]
        text_x = x1 + (w - text_size[0]) // 2
        text_y = y1 + (h + text_size[1]) // 2
        cv2.putText(surface, text, (text_x, text_y), FONT, font_scale, (text_color[2], text_color[1], text_color[0]), font_thickness, cv2.LINE_AA)

    # Define button dimensions and positions
    button_width, button_height = 180, 60
    button_spacing = 20

    # Difficulty buttons (above play zone)
    difficulty_buttons = []
    total_difficulty_button_width = len(DIFFICULTY_LEVELS) * button_width + (len(DIFFICULTY_LEVELS) - 1) * button_spacing
    start_x_difficulty = (screen_width - total_difficulty_button_width) // 2
    for i, (level, speed) in enumerate(DIFFICULTY_LEVELS.items()):
        rect = pygame.Rect(start_x_difficulty + i * (button_width + button_spacing), play_zone_y - button_height - button_spacing, button_width, button_height)
        difficulty_buttons.append({"label": level, "speed": speed, "rect": rect})

    # Main control buttons (below play zone)
    main_control_buttons = []
    main_button_labels = ["Restart", "Start Playzone", "Exit"]
    total_main_button_width = len(main_button_labels) * button_width + (len(main_button_labels) - 1) * button_spacing
    start_x_main_control = (screen_width - total_main_button_width) // 2
    for i, label in enumerate(main_button_labels):
        rect = pygame.Rect(start_x_main_control + i * (button_width + button_spacing), play_zone_y + play_zone_height + button_spacing, button_width, button_height)
        main_control_buttons.append({"label": label, "rect": rect})

    # Exit Playzone button (inside play zone)
    exit_playzone_button_rect = pygame.Rect(play_zone_x + play_zone_width - button_width - 10, play_zone_y + 10, button_width, button_height)

    while running:
        gaze_x, gaze_y = gaze_tracker.get_gaze_point()
        logger.debug(f"Gaze coordinates: ({gaze_x}, {gaze_y})")
        current_gaze = (gaze_x, gaze_y) # Store as tuple for convenience

        # --- Centralized Dwell Processing --- 
        hovered_button_label = None

        # Gaze control for snake movement
        if game.state == "PLAYING" and current_gaze[0] is not None and current_gaze[1] is not None:
            # Calculate grid cell dimensions
            cell_w = play_zone_rect.width // 3
            cell_h = play_zone_rect.height // 3

            # Determine which cell the gaze is in
            col = (current_gaze[0] - play_zone_x) // cell_w
            row = (current_gaze[1] - play_zone_y) // cell_h

            # Clamp values to valid range (0-2)
            col = max(0, min(2, col))
            row = max(0, min(2, row))

            # Map gaze to snake direction
            if row == 0 and col == 1: # Top-middle (Up)
                if game.snake.direction.y != 1: # Prevent 180 degree turn
                    game.snake.direction = Vector2(0, -1)
            elif row == 2 and col == 1: # Bottom-middle (Down)
                if game.snake.direction.y != -1: # Prevent 180 degree turn
                    game.snake.direction = Vector2(0, 1)
            elif row == 1 and col == 0: # Middle-left (Left)
                if game.snake.direction.x != 1: # Prevent 180 degree turn
                    game.snake.direction = Vector2(-1, 0)
            elif row == 1 and col == 2: # Middle-right (Right)
                if game.snake.direction.x != -1: # Prevent 180 degree turn
                    game.snake.direction = Vector2(1, 0)

        if current_gaze[0] is not None and current_gaze[1] is not None:
            # Check difficulty buttons (always check if game is not PLAYING)
            if game.state != "PLAYING":
                for button in difficulty_buttons:
                    if button["rect"].collidepoint(current_gaze):
                        hovered_button_label = button["label"]
                        break
                if hovered_button_label is None: # Check main control buttons if no difficulty button is hovered
                    for button in main_control_buttons:
                        if button["rect"].collidepoint(current_gaze):
                            hovered_button_label = button["label"]
                            break
            
            # Check Exit Playzone button (only if in PLAYING state)
            if game.state == "PLAYING":
                if exit_playzone_button_rect.collidepoint(current_gaze):
                    hovered_button_label = "Exit Playzone"

        # Update dwell_state based on hovered_button_label
        if hovered_button_label is not None:
            if dwell_state["hover_button"] != hovered_button_label:
                dwell_state["hover_button"] = hovered_button_label
                dwell_state["hover_start_time"] = pygame.time.get_ticks()
            
            elapsed_time = pygame.time.get_ticks() - dwell_state["hover_start_time"]
            if elapsed_time >= DWELL_DURATION * 1000:
                # Button dwelled successfully, perform action
                dwelled_button_label = dwell_state["hover_button"]
                dwell_state["hover_button"] = None # Reset dwell state
                dwell_state["hover_start_time"] = None

                if dwelled_button_label == "Exit":
                    running = False
                elif dwelled_button_label == "Restart":
                    game.reset_game()
                    game.state = "PLAYING"
                elif dwelled_button_label == "Start Playzone":
                    game.state = "PLAYING"
                elif dwelled_button_label == "Exit Playzone":
                    game.state = "PAUSED"
                else: # Difficulty buttons
                    for button in difficulty_buttons:
                        if button["label"] == dwelled_button_label:
                            current_difficulty_speed = button["speed"]
                            pygame.time.set_timer(SNAKE_UPDATE, current_difficulty_speed)
                            game.reset_game()
                            game.state = "PAUSED"
                            break
        else: # No button is currently hovered
            dwell_state["hover_button"] = None
            dwell_state["hover_start_time"] = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == SNAKE_UPDATE:
                game.update()

        # Drawing
        game_display[:] = (GREEN[2], GREEN[1], GREEN[0]) # Fill background with BGR color

        # Draw play zone border
        cv2.rectangle(game_display, (play_zone_rect.x, play_zone_rect.y), (play_zone_rect.x + play_zone_rect.width, play_zone_rect.y + play_zone_rect.height), (DARK_GREEN[2], DARK_GREEN[1], DARK_GREEN[0]), 5) # BGR

        # Draw difficulty buttons
        for button in difficulty_buttons:
            is_dwelled_on = (dwell_state["hover_button"] == button["label"])
            dwell_progress = (pygame.time.get_ticks() - dwell_state["hover_start_time"]) / (DWELL_DURATION * 1000) if is_dwelled_on and dwell_state["hover_start_time"] is not None else 0
            draw_button(game_display, (button["rect"].x, button["rect"].y, button["rect"].width, button["rect"].height), button["label"], FONT_SCALE_BUTTON, FONT_THICKNESS, game.state == "MENU" or game.state == "PAUSED" or game.state == "GAME_OVER", is_dwelled_on, dwell_progress)

        # Draw main control buttons
        for button in main_control_buttons:
            is_dwelled_on = (dwell_state["hover_button"] == button["label"])
            dwell_progress = (pygame.time.get_ticks() - dwell_state["hover_start_time"]) / (DWELL_DURATION * 1000) if is_dwelled_on and dwell_state["hover_start_time"] is not None else 0
            draw_button(game_display, (button["rect"].x, button["rect"].y, button["rect"].width, button["rect"].height), button["label"], FONT_SCALE_BUTTON, FONT_THICKNESS, game.state == "MENU" or game.state == "PAUSED" or game.state == "GAME_OVER", is_dwelled_on, dwell_progress)

        if game.state == "PLAYING" or game.state == "PAUSED" or game.state == "GAME_OVER":
            # Draw game elements within play zone
            cv2.rectangle(game_display, (OFFSET_X - 5, OFFSET_Y - 5), (OFFSET_X - 5 + game_width + 10, OFFSET_Y - 5 + game_height + 10), (DARK_GREEN[2], DARK_GREEN[1], DARK_GREEN[0]), 5) # BGR
            game.draw(game_display)
            
            # Render title and score using OpenCV
            cv2.putText(game_display, "Retro Snake", (OFFSET_X - 5, OFFSET_Y - 70), FONT, FONT_SCALE_TITLE, (DARK_GREEN[2], DARK_GREEN[1], DARK_GREEN[0]), FONT_THICKNESS, cv2.LINE_AA)
            cv2.putText(game_display, str(game.score), (OFFSET_X - 5, OFFSET_Y + game_height + 10 + 40), FONT, FONT_SCALE_SCORE, (DARK_GREEN[2], DARK_GREEN[1], DARK_GREEN[0]), FONT_THICKNESS, cv2.LINE_AA)

            # Draw Exit Playzone button (only if in PLAYING state)
            is_dwelled_on = (dwell_state["hover_button"] == "Exit Playzone")
            dwell_progress = (pygame.time.get_ticks() - dwell_state["hover_start_time"]) / (DWELL_DURATION * 1000) if is_dwelled_on and dwell_state["hover_start_time"] is not None else 0
            draw_button(game_display, (exit_playzone_button_rect.x, exit_playzone_button_rect.y, exit_playzone_button_rect.width, exit_playzone_button_rect.height), "Exit Playzone", FONT_SCALE_BUTTON, FONT_THICKNESS, game.state == "PLAYING", is_dwelled_on, dwell_progress)

            if game.state == "GAME_OVER":
                game_over_text = "GAME OVER"
                text_size = cv2.getTextSize(game_over_text, FONT, FONT_SCALE_TITLE, FONT_THICKNESS)[0]
                text_x = (screen_width - text_size[0]) // 2
                text_y = (screen_height + text_size[1]) // 2
                cv2.putText(game_display, game_over_text, (text_x, text_y), FONT, FONT_SCALE_TITLE, (DARK_GREEN[2], DARK_GREEN[1], DARK_GREEN[0]), FONT_THICKNESS, cv2.LINE_AA)

        # Draw gaze pointer
        if gaze_x is not None and gaze_y is not None:
            cv2.circle(game_display, (gaze_x, gaze_y), 10, (255, 0, 0), -1) # Red circle

        cv2.imshow("Retro Snake", game_display)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            running = False

    cv2.destroyAllWindows()
    logger.info("Snake Game application terminated.")
    gaze_tracker.release()

if __name__ == '__main__':
    main()