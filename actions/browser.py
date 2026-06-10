import webbrowser
import pyautogui
import time

def handle_open_url(value, speak, listen, memory):
    if not value or not value.strip():
        speak("I didn't catch the URL.")
        return
    value = value.strip()
    if not value.startswith("http"):
        value = "https://" + value
    webbrowser.open(value)

def handle_search(value, speak, listen, memory):
    webbrowser.open(f"https://google.com/search?q={value.replace(' ', '+')}")

def handle_youtube(value, speak, listen, memory):
    webbrowser.open(f"https://youtube.com/results?search_query={value.replace(' ', '+')}")

def handle_new_tab(*args, **kwargs):
    pyautogui.hotkey('ctrl', 't')

def handle_close_tab(*args, **kwargs):
    pyautogui.hotkey('ctrl', 'w')

def handle_reopen_tab(*args, **kwargs):
    pyautogui.hotkey('ctrl', 'shift', 't')

def handle_next_tab(*args, **kwargs):
    pyautogui.hotkey('ctrl', 'tab')

def handle_prev_tab(*args, **kwargs):
    pyautogui.hotkey('ctrl', 'shift', 'tab')

def handle_refresh(*args, **kwargs):
    pyautogui.press('f5')

def handle_close_window(*args, **kwargs):
    pyautogui.hotkey('alt', 'f4')

def handle_minimize(*args, **kwargs):
    pyautogui.hotkey('win', 'down')

def handle_maximize(*args, **kwargs):
    pyautogui.hotkey('win', 'up')

def handle_switch_window(*args, **kwargs):
    pyautogui.hotkey('alt', 'tab')

def handle_zoom_in(*args, **kwargs):
    pyautogui.hotkey('ctrl', '=')

def handle_zoom_out(*args, **kwargs):
    pyautogui.hotkey('ctrl', '-')

def handle_zoom_reset(*args, **kwargs):
    pyautogui.hotkey('ctrl', '0')
