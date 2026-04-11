import eel
import sys
import os
import logging
import time
import pyttsx3
import numpy as np
import threading

# Add shared_src and parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'shared_src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from gaze_tracker import GazeTracker
from logger_reporter import setup_logging

# Setup logging
logger = setup_logging("virtual_keyboard_web")

# --- Ported Logic from original keyboard.py ---

# NLTK Setup
DICTIONARY_WORDS = []
bigram_model = {}
freq_model = {}

def setup_nltk():
    global DICTIONARY_WORDS, bigram_model, freq_model
    try:
        import nltk
        nltk.download('words', quiet=True)
        nltk.download('brown', quiet=True)
        nltk.download('gutenberg', quiet=True)
        nltk.download('webtext', quiet=True)
        from nltk.corpus import words, brown
        
        DICTIONARY_WORDS = list(set(words.words()))
        
        # Bigram model
        bigrams = nltk.bigrams(brown.words())
        freq_dist = {}
        for (w1, w2) in bigrams:
            w1, w2 = w1.lower(), w2.lower()
            freq_dist.setdefault(w1, {})
            freq_dist[w1][w2] = freq_dist[w1].get(w2, 0) + 1
        for w in freq_dist:
            sorted_preds = sorted(freq_dist[w].items(), key=lambda x: x[1], reverse=True)
            bigram_model[w] = [word for word, count in sorted_preds]
            
        # Frequency model
        for w in brown.words():
            w = w.lower()
            freq_model[w] = freq_model.get(w, 0) + 1
            
        logger.info("NLTK models loaded successfully.")
    except Exception as e:
        logger.error(f"NLTK setup failed: {e}")

setup_nltk()

@eel.expose
def get_suggestions(text):
    words_in_text = text.split()
    prefix = words_in_text[-1] if words_in_text else ""
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

@eel.expose
def speak_text(text):
    if not text.strip():
        return
    try:
        # Initialize locally for each call to ensure fresh state
        local_engine = pyttsx3.init()
        local_engine.say(text)
        local_engine.runAndWait()
        # Explicitly stop to be safe
        local_engine.stop()
        # Small sleep allows audio hardware to reset
        time.sleep(0.1)
    except Exception as e:
        logger.error(f"TTS error: {e}")

# --- End Ported Logic ---

# Initialize Eel to serve the current directory
eel.init(os.path.dirname(os.path.abspath(__file__)))

# Get screen dimensions from command line arguments
screen_width = int(sys.argv[1]) if len(sys.argv) > 1 else 1920
screen_height = int(sys.argv[2]) if len(sys.argv) > 2 else 1080

# Initialize GazeTracker
gaze_tracker = GazeTracker(screen_width=screen_width, screen_height=screen_height)

@eel.expose
def get_gaze_coordinates():
    if gaze_tracker:
        return gaze_tracker.get_gaze_point()
    return None, None

@eel.expose
def save_file(filename, content):
    if not filename.endswith(".txt"):
        filename += ".txt"
    notes_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "notes")
    if not os.path.exists(notes_folder):
        os.makedirs(notes_folder)
    file_path = os.path.join(notes_folder, filename)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"File saved: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        return False

def delayed_exit():
    time.sleep(1)
    logger.info("Background thread: Final exit.")
    sys.exit()

@eel.expose
def close_keyboard():
    logger.info("Close keyboard requested.")
    if gaze_tracker:
        gaze_tracker.release()
    threading.Thread(target = delayed_exit).start()
    return True

logger.info(f"Launching Virtual Keyboard Web on port 0 with size {screen_width}x{screen_height}")

# Start the Eel application
eel.start('index.html', size=(screen_width, screen_height), suppress_error=True, port=0)
