from utils import get_screen_description, find_and_click_on_screen

def handle_screen_describe(value, speak, listen, memory):
    speak("Let me take a look at your screen...")
    speak(get_screen_description(value or "What is on the screen?"))

def handle_screen_click(value, speak, listen, memory):
    speak(f"Looking for {value} on screen...")
    find_and_click_on_screen(value, speak)
