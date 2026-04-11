import pyttsx3
import sys

def test_speak():
    print("Initializing TTS engine...")
    try:
        engine = pyttsx3.init()
        text = "This is a test of the virtual keyboard text to speech system."
        print(f"Attempting to speak: '{text}'")
        engine.say(text)
        engine.runAndWait()
        print("TTS test completed successfully.")
    except Exception as e:
        print(f"TTS test failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_speak()
