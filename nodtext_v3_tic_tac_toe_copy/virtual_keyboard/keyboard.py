import pyttsx3
import pyautogui
import time
import os
import sys
import cv2
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'shared_src')))
from logger_reporter import setup_logging
from gaze_tracker import GazeTracker
import eel

# Global variable to store gaze coordinates received from main.py
global_gaze_x, global_gaze_y = None, None

@eel.expose
def update_gaze_coordinates(x, y):
    global global_gaze_x, global_gaze_y
    global_gaze_x, global_gaze_y = x, y

def main():
    logger = setup_logging("virtual_keyboard")
    logger.info("Virtual Keyboard application started.")
    # TTS Setup
    engine = pyttsx3.init()
    # (Optional: engine.setProperty('rate', 150))

    # Global mode variables:
    # mode "edit" is the normal text-editing mode,
    # mode "save" is active when prompting the user for a filename.
    mode = "edit"
    save_file_name = ""  # Used in save mode to collect filename input.
    running = True # Add this flag to control the main loop

    # Get screen dimensions from command line arguments
    if len(sys.argv) > 4:
        global global_gaze_x, global_gaze_y
        screen_width = int(sys.argv[1])
        screen_height = int(sys.argv[2])
        global_gaze_x = int(float(sys.argv[3])) if sys.argv[3] != 'None' else None
        global_gaze_y = int(float(sys.argv[4])) if sys.argv[4] != 'None' else None
    else:
        # Fallback if arguments are not provided (e.g., for direct testing)
        screen_width, screen_height = pyautogui.size()

    # Initialize GazeTracker
    gaze_tracker = GazeTracker(screen_width=screen_width, screen_height=screen_height)

    cursor_visible = True
    last_toggle = time.time()
    BLINK_RATE = 1.5  # Cursor blink rate in seconds
    # Colors for groups (B, G, R format)
    COLOR_GROUP1 = (220, 220, 250)  # Group 1: Space, Speak, Save, Clear (light periwinkle)
    COLOR_GROUP2 = (250, 220, 220)  # Group 2: Enter (light pink)
    COLOR_GROUP3 = (220, 250, 220)  # Group 3: Backspace (light green)
    COLOR_GROUP4 = (250, 250, 200)  # Group 4: Left, Up, Down, Right, Exit (light yellow)

    # ----------------- Smoothing Setup ----------------- #
    # prev_gaze_x, prev_gaze_y = None, None # No longer needed, handled by GazeTracker
    # smoothing_factor = 0.1  # Adjust between 0 and 1 (lower = more smoothing) # No longer needed, handled by GazeTracker

    def snap_to_button(gaze_x, gaze_y, key, threshold=30):
        """
        Returns the center of the key if the gaze is within threshold distance.
        Otherwise, returns the original gaze coordinates.
        """
        center_x = (key['x1'] + key['x2']) // 2
        center_y = (key['y1'] + key['y2']) // 2
        distance = ((gaze_x - center_x)**2 + (gaze_y - center_y)**2)**0.5
        if distance < threshold:
            return center_x, center_y
        return gaze_x, gaze_y


    # def get_smoothed_gaze(gaze_x, gaze_y): # No longer needed, handled by GazeTracker
    #     """Smooth the gaze coordinates using an exponential moving average (EMA)."""
    #     nonlocal prev_gaze_x, prev_gaze_y
    #     if prev_gaze_x is None or prev_gaze_y is None:
    #         prev_gaze_x, prev_gaze_y = gaze_x, gaze_y
    #     else:
    #         prev_gaze_x = smoothing_factor * gaze_x + (1 - smoothing_factor) * prev_gaze_x
    #         prev_gaze_y = smoothing_factor * gaze_y + (1 - smoothing_factor) * prev_gaze_y
    #     return int(prev_gaze_x), int(prev_gaze_y)

    # Support Functions
    try:
        import nltk
        nltk.download('words', quiet=True)
        nltk.download(corpus for corpus in ['brown', 'gutenberg', 'webtext'])
        from nltk.corpus import words
        DICTIONARY_WORDS = list(set(words.words()))
    except Exception as e:
        DICTIONARY_WORDS = []

    def build_bigram_model():
        try:
            import nltk
            from nltk.corpus import brown
            bigrams = nltk.bigrams(brown.words())
            freq_dist = {}
            for (w1, w2) in bigrams:
                w1 = w1.lower()
                w2 = w2.lower()
                freq_dist.setdefault(w1, {})
                freq_dist[w1][w2] = freq_dist[w1].get(w2, 0) + 1
            for w in freq_dist:
                sorted_preds = sorted(freq_dist[w].items(), key=lambda x: x[1], reverse=True)
                freq_dist[w] = [word for word, count in sorted_preds]
            return freq_dist
        except Exception as e:
            return {}

    bigram_model = build_bigram_model()

    def build_frequency_model():
        try:
            from nltk.corpus import brown
            freq = {}
            for w in brown.words():
                w = w.lower()
                freq[w] = freq.get(w, 0) + 1
            return freq
        except Exception as e:
            return {}

    freq_model = build_frequency_model()

    def get_suggestions(text):
        words_in_text = text.split()
        prefix = words_in_text[-1] if words_in_text else ""
        # Trigger suggestions after 2 characters have been typed in the current word.
        if len(prefix) < 2:
            return []
        suggestions = []
        if len(words_in_text) >= 2:
            prev_word = words_in_text[-2].lower()
            if prev_word in bigram_model:
                suggestions = [w for w in bigram_model[prev_word] if w.startswith(prefix.lower())]
        if not suggestions:
            suggestions = [w for w in DICTIONARY_WORDS if w.lower().startswith(prefix.lower())]
            suggestions = sorted(suggestions, key=lambda w: -freq_model.get(w.lower(), 0))
        return suggestions[:5]

    # ----------------- Global Configuration & Variables ----------------- #
    UI_WIDTH  = screen_width
    UI_HEIGHT = screen_height

    # Layout configuration
    TEXT_AREA_HEIGHT = 300      
    SUGGESTION_BAR_HEIGHT = 50  
    KEYBOARD_AREA_HEIGHT = UI_HEIGHT - TEXT_AREA_HEIGHT - SUGGESTION_BAR_HEIGHT

    DWELL_DURATION = 0.8  # Seconds to dwell.
    SENSITIVITY = 6       # Sensitivity multiplier

    # Colors (B, G, R)
    COLOR_BACKGROUND      = (245, 245, 245)
    COLOR_TEXT_AREA       = (200, 220, 255)
    COLOR_TEXT            = (50, 50, 50)
    COLOR_SUGGESTION_BAR  = (230, 230, 250)
    COLOR_KEYBOARD        = (210, 235, 210)
    COLOR_CURSOR          = (255, 50, 50)
    COLOR_PROGRESS_BAR    = (50, 200, 50)
    COLOR_KEY_HIGHLIGHT   = (100, 180, 255)
    COLOR_SENTENCE_TEXT = (211, 211, 211)

    # Use a formal font.
    FONT = cv2.FONT_HERSHEY_COMPLEX

    BASE_COLOR = (245, 245, 255)
    def adjust_color(base_color, adjustment_factor):
        b, g, r = base_color
        return (max(min(255, b + adjustment_factor), 0),
                max(min(255, g + adjustment_factor), 0),
                max(min(255, r + adjustment_factor), 0))
    COLOR_LETTERS       = adjust_color(BASE_COLOR, -10)
    COLOR_NUMBERS       = adjust_color(BASE_COLOR, 10)
    COLOR_SYMBOLS       = adjust_color(BASE_COLOR, -20)
    COLOR_FUNCTION_KEYS = adjust_color(BASE_COLOR, -30)
    COLOR_KEY_BORDER    = (220, 220, 220)

    # Revised keyboard layout with a new "Save" key.
    keyboard_layout = [
        ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "Backspace"],
        ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "[", "]", ""],
        ["CapsLock", "a", "s", "d", "f", "g", "h", "j", "k", "l", ";", "'", "Enter"],
        ["z", "x", "c", "v", "b", "n", "m", ",", ".", "/"],
        ["Space", "Speak", "Save", "Clear"],
        ["Left", "Up", "Down", "Right", "Exit"]  # <- Added Exit here
    ]


    typed_text = ""
    cursor_index = 0
    text_scroll_offset = 0
    caps_lock = False

    dwell_state = {
        'hover_key': None,
        'hover_key_start': None,
        'hover_suggestion': None,
        'hover_suggestion_start': None,
        'hover_text_area': None
    }

    engine = pyttsx3.init()

    # Gaze Tracking using MediaPipe.
    # face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True) # No longer needed, handled by GazeTracker
    # LEFT_IRIS_INDEXES  = [468, 469, 470, 471, 472] # No longer needed, handled by GazeTracker
    # RIGHT_IRIS_INDEXES = [473, 474, 475, 476, 477] # No longer needed, handled by GazeTracker
    cursor_visible = True
    last_toggle = time.time()
    BLINK_RATE = 0.3

    # cap = cv2.VideoCapture(0) # No longer needed, handled by GazeTracker

    # ----------------- Helper Functions ----------------- #
    def key_multiplier(key):
        if key in ["Backspace", "Enter", "CapsLock"]:
            return 2
        elif key == "Space":
            return 6
        elif key in ["Speak", "Clear", "Save", "Left", "Right", "Up", "Down"]:
            return 2
        else:
            return 1

    def compute_keys():
        keys = []
        keyboard_top = TEXT_AREA_HEIGHT + SUGGESTION_BAR_HEIGHT
        keyboard_height = KEYBOARD_AREA_HEIGHT
        num_keyboard_rows = len(keyboard_layout)
        row_height = keyboard_height / num_keyboard_rows
        for row_index, row in enumerate(keyboard_layout):
            total_multiplier = sum(key_multiplier(k) for k in row)
            standard_key_width = UI_WIDTH / total_multiplier
            x_offset = 0
            for key in row:
                width = standard_key_width * key_multiplier(key)
                x1 = int(x_offset)
                y1 = int(keyboard_top + row_index * row_height)
                x2 = int(x_offset + width)
                y2 = int(keyboard_top + (row_index + 1) * row_height)
                keys.append({'label': key, 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2})
                x_offset += width
        return keys

    keys = compute_keys()

    # def get_iris_center(landmarks, indices, frame_w, frame_h): # No longer needed, handled by GazeTracker
    #     x, y = 0, 0
    #     for idx in indices:
    #         x += landmarks[idx].x
    #         y += landmarks[idx].y
    #     return int((x / len(indices)) * frame_w), int((y / len(indices)) * frame_h)

    # def get_gaze_position(frame): # No longer needed, handled by GazeTracker
    #     frame = cv2.flip(frame, 1)
    #     frame_h, frame_w, _ = frame.shape
    #     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    #     results = face_mesh.process(rgb_frame)
    #     gaze_x, gaze_y = None, None
    #     if results.multi_face_landmarks:
    #         for face_landmarks in results.multi_face_landmarks:
    #             landmarks = face_landmarks.landmark
    #             left_center  = get_iris_center(landmarks, LEFT_IRIS_INDEXES, frame_w, frame_h)
    #             right_center = get_iris_center(landmarks, RIGHT_IRIS_INDEXES, frame_w, frame_h)
    #             avg_x = (left_center[0] + right_center[0]) / 2
    #             avg_y = (left_center[1] + right_center[1]) / 2
    #             norm_x = avg_x / frame_w
    #             norm_y = avg_y / frame_h
    #             norm_x = 0.5 + (norm_x - 0.5) * SENSITIVITY
    #             norm_y = 0.5 + (norm_y - 0.5) * SENSITIVITY
    #             norm_x = np.clip(norm_x, 0, 1)
    #             norm_y = np.clip(norm_y, 0, 1)
    #             gaze_x = int(norm_x * UI_WIDTH)
    #             gaze_y = int(norm_y * UI_HEIGHT)
    #             break
    #     return gaze_x, gaze_y

    def insert_text(original, index, new_char):
        return original[:index] + new_char + original[index:]

    def delete_text(original, index):
        if index > 0:
            return original[:index-1] + original[index:]
        return original

    def get_cursor_line_col(text, index):
        lines = text.split('\n')
        count = 0
        for i, line in enumerate(lines):
            if count + len(line) >= index:
                return i, index - count
            count += len(line) + 1
        return len(lines) - 1, len(lines[-1])

    def get_cursor_index_from_line_col(text, line, col):
        lines = text.split('\n')
        index = 0
        for i in range(line):
            index += len(lines[i]) + 1
        return index + min(col, len(lines[line]))

    def get_precise_col(line_text, gaze_x, margin, font, font_scale, thickness):
        cumulative_width = 0
        for i, ch in enumerate(line_text):
            (w, _), _ = cv2.getTextSize(ch, font, font_scale, thickness)
            if margin + cumulative_width + w/2 >= gaze_x:
                return i
            cumulative_width += w
        return len(line_text)

    # ----------------- UI Drawing Functions ----------------- #
    def draw_text_area(ui, text, cursor_index, text_scroll_offset):
        margin = 10
        font_scale = 1
        thickness = 2
        line_height = 30
        lines = text.split('\n')
        total_lines = len(lines)
        max_lines_visible = (TEXT_AREA_HEIGHT - 2 * margin) // line_height
        start_line = text_scroll_offset
        display_lines = lines[start_line:start_line + max_lines_visible]
        
        cv2.rectangle(ui, (0, 0), (UI_WIDTH, TEXT_AREA_HEIGHT), COLOR_TEXT_AREA, -1)
        
        for i, line in enumerate(display_lines):
            display_text = line if line.strip() != "" else " "
            y = margin + (i + 1) * line_height
            cv2.putText(ui, display_text, (margin, y), FONT, font_scale, COLOR_TEXT, thickness)
        
        current_line, current_col = get_cursor_line_col(text, cursor_index)
        if start_line <= current_line < start_line + max_lines_visible:
            relative_line = current_line - start_line
            line_text = lines[current_line]
            text_before_cursor = line_text[:current_col]
            (w, _), _ = cv2.getTextSize(text_before_cursor, FONT, font_scale, thickness)
            cursor_x = margin + w
            cursor_y_top = margin + (relative_line + 1) * line_height - line_height + 5
            cursor_y_bottom = cursor_y_top + line_height - 10
            nonlocal cursor_visible, last_toggle
            if time.time() - last_toggle > BLINK_RATE:
                cursor_visible = not cursor_visible
                last_toggle = time.time()
            if cursor_visible:
                cv2.line(ui, (cursor_x, cursor_y_top), (cursor_x, cursor_y_bottom), COLOR_CURSOR, thickness)
        
        if total_lines > max_lines_visible:
            bar_width = 20
            bar_x = UI_WIDTH - bar_width - 5
            bar_y = margin
            bar_height = TEXT_AREA_HEIGHT - 2 * margin
            cv2.rectangle(ui, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (200, 200, 200), 2)
            max_offset = max(total_lines - max_lines_visible, 1)
            indicator_height = max(int(bar_height * max_lines_visible / total_lines), 20)
            indicator_y = bar_y + int((text_scroll_offset / max_offset) * (bar_height - indicator_height))
            cv2.rectangle(ui, (bar_x, indicator_y), (bar_x + bar_width, indicator_y + indicator_height), COLOR_PROGRESS_BAR, -1)

    def draw_suggestions(ui, text):
        suggestions = get_suggestions(text)
        suggestion_boxes = []
        num_suggestions = len(suggestions)
        if num_suggestions > 0:
            suggestion_width = UI_WIDTH / num_suggestions
            for i, suggestion in enumerate(suggestions):
                s_x1 = int(i * suggestion_width)
                s_y1 = TEXT_AREA_HEIGHT
                s_x2 = int((i + 1) * suggestion_width)
                s_y2 = TEXT_AREA_HEIGHT + SUGGESTION_BAR_HEIGHT
                suggestion_boxes.append({'label': suggestion, 'x1': s_x1, 'y1': s_y1, 'x2': s_x2, 'y2': s_y2})
                cv2.rectangle(ui, (s_x1, s_y1), (s_x2, s_y2), COLOR_SUGGESTION_BAR, -1)
                (txt_w, txt_h), _ = cv2.getTextSize(suggestion, FONT, 1, 2)
                txt_x = s_x1 + (suggestion_width - txt_w) // 2
                txt_y = s_y1 + (SUGGESTION_BAR_HEIGHT + txt_h) // 2
                cv2.putText(ui, suggestion, (int(txt_x), int(txt_y)), FONT, 1, COLOR_TEXT, 2)
        return suggestion_boxes

    def draw_filled_rounded_rect(ui, top_left, bottom_right, color, radius=10):
        top_left = (int(top_left[0]), int(top_left[1]))
        bottom_right = (int(bottom_right[0]), int(bottom_right[1]))
        x, y = top_left
        w, h = bottom_right[0] - x, bottom_right[1] - y
        cv2.rectangle(ui, (x + radius, y), (x + w - radius, y + h), color, -1)
        cv2.rectangle(ui, (x, y + radius), (x + w, y + h - radius), color, -1)
        cv2.ellipse(ui, (x + radius, y + radius), (radius, radius), 180, 0, 90, color, -1)
        cv2.ellipse(ui, (x + w - radius, y + radius), (radius, radius), 270, 0, 90, color, -1)
        cv2.ellipse(ui, (x + radius, y + h - radius), (radius, radius), 90, 0, 90, color, -1)
        cv2.ellipse(ui, (x + w - radius, y + h - radius), (radius, radius), 0, 0, 90, color, -1)

    def draw_rounded_rect(ui, top_left, bottom_right, color, border_color, radius=10, border_thickness=2):
        top_left = (int(top_left[0]), int(top_left[1]))
        bottom_right = (int(bottom_right[0]), int(bottom_right[1]))
        x, y = top_left
        w, h = bottom_right[0] - x, bottom_right[1] - y
        draw_filled_rounded_rect(ui, (x, y), (x + w, y + h), color, radius)
        inner_top_left = (x + border_thickness, y + border_thickness)
        inner_bottom_right = (x + w - border_thickness, y + h - border_thickness)
        draw_filled_rounded_rect(ui, inner_top_left, inner_bottom_right, border_color, radius)

    def draw_keyboard(ui, keys):
        nonlocal caps_lock
        for key in keys:
            # Assign custom colors based on the group of key labels.
            if key['label'] in ["Space", "Speak", "Save", "Clear"]:
                key_color = COLOR_GROUP1
            elif key['label'] == "Enter":
                key_color = COLOR_GROUP2
            elif key['label'] == "Backspace":
                key_color = COLOR_GROUP3
            elif key['label'] in ["Left", "Up", "Down", "Right", "Exit"]:
                key_color = COLOR_GROUP4
            elif key['label'] == "CapsLock":
                # Retain the original behavior for CapsLock.
                key_color = (0, 255, 0) if caps_lock else COLOR_FUNCTION_KEYS
            elif key['label'].isdigit():
                key_color = COLOR_NUMBERS
            elif key['label'].isalpha():
                key_color = COLOR_LETTERS
            else:
                key_color = COLOR_SYMBOLS

            # Draw the key using the rounded rect function.
            draw_rounded_rect(ui, (key['x1'], key['y1']), (key['x2'], key['y2']),
                              key_color, COLOR_KEY_BORDER, radius=15, border_thickness=2)

            # Draw the hover progress fill
            if dwell_state['hover_key'] and dwell_state['hover_key']['label'] == key['label']:
                elapsed = time.time() - dwell_state['hover_key_start']
                progress = min(elapsed / DWELL_DURATION, 1.0)
                progress_width = int((key['x2'] - key['x1']) * progress)
                progress_rect_top_left = (key['x1'], key['y1'])
                progress_rect_bottom_right = (key['x1'] + progress_width, key['y2'])
                draw_filled_rounded_rect(ui, progress_rect_top_left, progress_rect_bottom_right, COLOR_KEY_HIGHLIGHT, radius=15)

            # Center the key label on the key.
            text = key['label']
            (text_w, text_h), _ = cv2.getTextSize(text, FONT, 1, 2)
            text_x = key['x1'] + (key['x2'] - key['x1'] - text_w) // 2
            text_y = key['y1'] + (key['y2'] - key['y1'] + text_h) // 2 + text_h // 4
            cv2.putText(ui, text, (int(text_x), int(text_y)), FONT, 1, COLOR_TEXT, 2)

    def draw_gaze_pointer(ui, gaze_x, gaze_y):
        if gaze_x is not None and gaze_y is not None:
            cv2.circle(ui, (gaze_x, gaze_y), 10, (255, 0, 0), -1)

    def draw_file_save_prompt(ui, current_save_file_name):
        prompt_text = "Enter file name: " + current_save_file_name
        prompt_box_width = UI_WIDTH // 2
        prompt_box_height = 100
        # Shift the prompt to be inside the text area instead of the center of the entire UI
        prompt_box_x = (UI_WIDTH - prompt_box_width) // 2
        prompt_box_y = (TEXT_AREA_HEIGHT - prompt_box_height) // 2  # Previously centered in UI; now up in the text area
        cv2.rectangle(ui, (prompt_box_x, prompt_box_y), (prompt_box_x + prompt_box_width, prompt_box_y + prompt_box_height), (220,220,220), -1)
        cv2.rectangle(ui, (prompt_box_x, prompt_box_y), (prompt_box_x + prompt_box_width, prompt_box_y + prompt_box_height), (0,0,0), 2)
        (txt_w, txt_h), _ = cv2.getTextSize(prompt_text, FONT, 1, 2)
        txt_x = prompt_box_x + (prompt_box_width - txt_w) // 2
        txt_y = prompt_box_y + (prompt_box_height + txt_h) // 2
        cv2.putText(ui, prompt_text, (txt_x, txt_y), FONT, 1, (0,0,0), 2)

    # ----------------- Dwell Processing Functions ----------------- #
    def process_text_area_dwell(ui, gaze_x, gaze_y, text, cursor_index, text_scroll_offset, dwell_state):
        margin = 10
        line_height = 30
        in_scroll_bar = gaze_x >= UI_WIDTH - 20
        if in_scroll_bar:
            if (dwell_state.get('hover_text_area') is None or 
                dwell_state['hover_text_area'].get('type') != 'scroll'):
                dwell_state['hover_text_area'] = {'type': 'scroll', 'start': time.time()}
            else:
                elapsed = time.time() - dwell_state['hover_text_area']['start']
                progress = min(elapsed / DWELL_DURATION, 1.0)
                bar_width = 20
                bar_x = UI_WIDTH - bar_width - 5
                bar_y = margin
                bar_height = TEXT_AREA_HEIGHT - 2 * margin
                cv2.rectangle(ui, (bar_x, bar_y),
                              (bar_x + int(bar_width * progress), bar_y + bar_height), (0, 255, 0), -1)
                if elapsed >= DWELL_DURATION:
                    ratio = (gaze_y - margin) / (bar_height)
                    lines = text.split('\n')
                    total_lines = len(lines)
                    max_visible = (TEXT_AREA_HEIGHT - 2 * margin) // line_height
                    max_offset = max(total_lines - max_visible, 0)
                    text_scroll_offset = int(ratio * max_offset)
                    dwell_state['hover_text_area'] = None
        else:
            if (dwell_state.get('hover_text_area') is None or 
                dwell_state['hover_text_area'].get('type') != 'edit'):
                dwell_state['hover_text_area'] = {'type': 'edit', 'start': time.time()}
            else:
                elapsed = time.time() - dwell_state['hover_text_area']['start']
                if elapsed >= DWELL_DURATION:
                    target_line = (gaze_y - margin) // line_height + text_scroll_offset
                    lines = text.split('\n')
                    if target_line >= len(lines):
                        target_line = len(lines) - 1
                    col = get_precise_col(lines[target_line], gaze_x, margin, FONT, 1, 2)
                    cursor_index = get_cursor_index_from_line_col(text, target_line, col)
                    dwell_state['hover_text_area'] = None
        return cursor_index, text_scroll_offset, dwell_state

    def process_suggestion_dwell(ui, gaze_x, gaze_y, suggestion_boxes, dwell_state, text, cursor_index):
        hovered_suggestion = None
        for box in suggestion_boxes:
            if box['x1'] <= gaze_x <= box['x2'] and box['y1'] <= gaze_y <= box['y2']:
                hovered_suggestion = box
                cv2.rectangle(ui, (box['x1'], box['y1']),
                              (box['x2'], box['y2']), (0, 0, 255), 4)
                break
        if hovered_suggestion:
            if (dwell_state.get('hover_suggestion') is None or 
                hovered_suggestion['label'] != dwell_state.get('hover_suggestion')['label']):
                dwell_state['hover_suggestion'] = hovered_suggestion
                dwell_state['hover_suggestion_start'] = time.time()
            else:
                elapsed = time.time() - dwell_state['hover_suggestion_start']
                progress = min(elapsed / DWELL_DURATION, 1.0)
                bar_height = 5
                bar_width = int((hovered_suggestion['x2'] - hovered_suggestion['x1']) * progress)
                cv2.rectangle(ui, (hovered_suggestion['x1'], hovered_suggestion['y2'] - bar_height),
                              (hovered_suggestion['x1'] + bar_width, hovered_suggestion['y2']),
                              (0, 255, 0), -1)
                if elapsed >= DWELL_DURATION:
                    lines = text.split('\n')
                    current_line_idx, _ = get_cursor_line_col(text, cursor_index)
                    current_line = lines[current_line_idx]
                    line_words = current_line.split()
                    if line_words:
                        line_words[-1] = hovered_suggestion['label']
                        new_line = " ".join(line_words) + " "
                        lines[current_line_idx] = new_line
                        text = "\n".join(lines)
                        cursor_index = get_cursor_index_from_line_col(text, current_line_idx, len(new_line))
                    else:
                        lines[current_line_idx] = hovered_suggestion['label']
                        text = "\n".join(lines)
                        cursor_index = get_cursor_index_from_line_col(text, current_line_idx, len(hovered_suggestion['label']))
                    dwell_state['hover_suggestion'] = None
                    dwell_state['hover_suggestion_start'] = None
                    time.sleep(0.3)
        else:
            dwell_state['hover_suggestion'] = None
            dwell_state['hover_suggestion_start'] = None
        return text, dwell_state, cursor_index

    import os  # make sure this is near your top-level imports

    def process_keyboard_dwell(ui, gaze_x, gaze_y, keys, dwell_state, text, cursor_index, text_scroll_offset):
        nonlocal caps_lock, mode, save_file_name, typed_text, running
        hovered_key = None
        for key in keys:
            if key['x1'] <= gaze_x <= key['x2'] and key['y1'] <= gaze_y <= key['y2']:
                hovered_key = key
                cv2.rectangle(ui, (key['x1'], key['y1']), (key['x2'], key['y2']), (0, 0, 255), 4)
                break
        if hovered_key:
            # Snap the gaze to the center of the button if within threshold
            gaze_x, gaze_y = snap_to_button(gaze_x, gaze_y, hovered_key, threshold=30)
            
            if (dwell_state.get('hover_key') is None or 
                hovered_key['label'] != dwell_state.get('hover_key')['label']):
                dwell_state['hover_key'] = hovered_key
                dwell_state['hover_key_start'] = time.time()
            else:
                elapsed = time.time() - dwell_state['hover_key_start']
                progress = min(elapsed / DWELL_DURATION, 1.0)
                bar_height = 5
                bar_width = int((hovered_key['x2'] - hovered_key['x1']) * progress)
                cv2.rectangle(ui, (hovered_key['x1'], hovered_key['y2'] - bar_height),
                              (hovered_key['x1'] + bar_width, hovered_key['y2']),
                              (0, 255, 0), -1)
                if elapsed >= DWELL_DURATION:
                    key_label = hovered_key['label']
                    if key_label == "Backspace":
                        if cursor_index > 0:
                            text = delete_text(text, cursor_index)
                            cursor_index -= 1
                    elif key_label == "Enter":
                        text = insert_text(text, cursor_index, "\n")
                        cursor_index += 1
                        lines = text.split('\n')
                        max_visible = (TEXT_AREA_HEIGHT - 20) // 30
                        if len(lines) - text_scroll_offset > max_visible:
                            text_scroll_offset = len(lines) - max_visible
                    elif key_label == "Space":
                        text = insert_text(text, cursor_index, " ")
                        cursor_index += 1
                    elif key_label == "CapsLock":
                        caps_lock = not caps_lock
                    elif key_label == "Speak":
                        engine.say(text)
                        engine.runAndWait()
                    elif key_label == "Clear":
                        text = ""
                        cursor_index = 0
                    elif key_label == "Save":
                        mode = "save"
                        save_file_name = ""
                    elif key_label == "Exit":
                        running = False  # Signal main loop to exit
                    elif key_label in ["Left", "Right", "Up", "Down"]:
                        if key_label == "Left":
                            cursor_index = max(0, cursor_index - 1)
                        elif key_label == "Right":
                            cursor_index = min(len(text), cursor_index + 1)
                        elif key_label == "Up":
                            line, col = get_cursor_line_col(text, cursor_index)
                            if line > 0:
                                new_line = line - 1
                                cursor_index = get_cursor_index_from_line_col(text, new_line, col)
                        elif key_label == "Down":
                            line, col = get_cursor_line_col(text, cursor_index)
                            lines_list = text.split('\n')
                            if line < len(lines_list) - 1:
                                new_line = line + 1
                                cursor_index = get_cursor_index_from_line_col(text, new_line, col)
                    else:
                        char_to_insert = key_label
                        if key_label.isalpha():
                            char_to_insert = key_label.upper() if caps_lock else key_label.lower()
                        text = insert_text(text, cursor_index, char_to_insert)
                        cursor_index += len(char_to_insert)
                    dwell_state['hover_key'] = None
                    dwell_state['hover_key_start'] = None
                    time.sleep(0.3)
        else:
            dwell_state['hover_key'] = None
            dwell_state['hover_key_start'] = None
        return text, dwell_state, cursor_index, text_scroll_offset

    import os  # Ensure this import is at the top of your script

    def process_save_keyboard_dwell(ui, gaze_x, gaze_y, keys, dwell_state, current_save_file_name):
        nonlocal mode, typed_text, caps_lock, save_file_name
        hovered_key = None
        for key in keys:
            if key['x1'] <= gaze_x <= key['x2'] and key['y1'] <= gaze_y <= key['y2']:
                hovered_key = key
                cv2.rectangle(ui, (key['x1'], key['y1']), (key['x2'], key['y2']), (0, 0, 255), 4)
                break
        if hovered_key:
            if (dwell_state.get('hover_key') is None or 
                hovered_key['label'] != dwell_state.get('hover_key')['label']):
                dwell_state['hover_key'] = hovered_key
                dwell_state['hover_key_start'] = time.time()
            else:
                elapsed = time.time() - dwell_state['hover_key_start']
                progress = min(elapsed / DWELL_DURATION, 1.0)
                bar_height = 5
                bar_width = int((hovered_key['x2'] - hovered_key['x1']) * progress)
                cv2.rectangle(ui, (hovered_key['x1'], hovered_key['y2'] - bar_height),
                              (hovered_key['x1'] + bar_width, hovered_key['y2']),
                              (0, 255, 0), -1)
                if elapsed >= DWELL_DURATION:
                    key_label = hovered_key['label']
                    if key_label == "Backspace":
                        current_save_file_name = current_save_file_name[:-1]
                    elif key_label == "Enter":
                        file_name = current_save_file_name
                        if not file_name.endswith(".txt"):
                            file_name += ".txt"
                        # Create a folder called "notes" in the same directory as the script
                        notes_folder = "notes"
                        if not os.path.exists(notes_folder):
                            os.makedirs(notes_folder)
                        file_path = os.path.join(notes_folder, file_name)
                        try:
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(typed_text)
                            engine.say("File saved")
                            engine.runAndWait()
                        except Exception as e:
                            engine.say("Error saving file")
                            engine.runAndWait()
                        current_save_file_name = ""
                        mode = "edit"
                    elif key_label == "Clear":
                        current_save_file_name = ""
                        mode = "edit"
                    elif key_label == "CapsLock":
                        caps_lock = not caps_lock
                    elif key_label == "Space":
                        current_save_file_name += " "
                    else:
                        char_to_insert = key_label
                        if char_to_insert.isalpha():
                            char_to_insert = char_to_insert.upper() if caps_lock else char_to_insert.lower()
                        current_save_file_name += char_to_insert
                    dwell_state['hover_key'] = None
                    dwell_state['hover_key_start'] = None
                    time.sleep(0.3)
        else:
            dwell_state['hover_key'] = None
            dwell_state['hover_key_start'] = None
        return current_save_file_name, dwell_state

    cv2.namedWindow("Interactive Gaze-Controlled Editor", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Interactive Gaze-Controlled Editor", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # ----------------- Main Loop ----------------- #
    while running:
        gaze_x, gaze_y = gaze_tracker.get_gaze_point()

        ui = np.ones((UI_HEIGHT, UI_WIDTH, 3), dtype=np.uint8) * 255

        if mode == "save":
            # In save mode, draw the keyboard and overlay the file save prompt.
            draw_keyboard(ui, keys)
            save_file_name, dwell_state = process_save_keyboard_dwell(ui, gaze_x, gaze_y, keys, dwell_state, save_file_name)
            draw_file_save_prompt(ui, save_file_name)
        else:
            # In edit mode, draw text area, suggestions, and keyboard.
            draw_text_area(ui, typed_text, cursor_index, text_scroll_offset)
            suggestion_boxes = draw_suggestions(ui, typed_text)
            draw_keyboard(ui, keys)
        
            if gaze_x is not None and gaze_y is not None:
                if gaze_y < TEXT_AREA_HEIGHT:
                    cursor_index, text_scroll_offset, dwell_state = process_text_area_dwell(
                        ui, gaze_x, gaze_y, typed_text, cursor_index, text_scroll_offset, dwell_state)
                elif TEXT_AREA_HEIGHT <= gaze_y < TEXT_AREA_HEIGHT + SUGGESTION_BAR_HEIGHT and suggestion_boxes:
                    typed_text, dwell_state, cursor_index = process_suggestion_dwell(
                        ui, gaze_x, gaze_y, suggestion_boxes, dwell_state, typed_text, cursor_index)
                elif gaze_y >= TEXT_AREA_HEIGHT + SUGGESTION_BAR_HEIGHT:
                    typed_text, dwell_state, cursor_index, text_scroll_offset = process_keyboard_dwell(
                        ui, gaze_x, gaze_y, keys, dwell_state, typed_text, cursor_index, text_scroll_offset)
                else:
                    dwell_state['hover_key'] = None
                    dwell_state['hover_key_start'] = None
                    dwell_state['hover_suggestion'] = None
                    dwell_state['hover_suggestion_start'] = None
                    dwell_state['hover_text_area'] = None

        draw_gaze_pointer(ui, gaze_x, gaze_y)
        cv2.imshow("Interactive Gaze-Controlled Editor", ui)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            running = False

    cv2.destroyAllWindows()
    logger.info("Virtual Keyboard application terminated.")
    gaze_tracker.release()

if __name__ == '__main__':
    main()
    # No gaze_tracker.release() here as it's managed by main.py