import webbrowser
import pyautogui
import time

def handle_open_url(value, speak, listen, memory):
    if not value.startswith("http"):
        value = "https://" + value
    webbrowser.open(value)

def handle_search(value, speak, listen, memory):
    webbrowser.open(f"https://google.com/search?q={value.replace(' ', '+')}")

def handle_youtube(value, speak, listen, memory):
    webbrowser.open(f"https://youtube.com/results?search_query={value.replace(' ', '+')}")

def handle_new_tab(value, speak, listen, memory):
    pyautogui.hotkey('ctrl', 't')

def handle_close_tab(value, speak, listen, memory):
    pyautogui.hotkey('ctrl', 'w')

def handle_reopen_tab(value, speak, listen, memory):
    pyautogui.hotkey('ctrl', 'shift', 't')

def handle_next_tab(value, speak, listen, memory):
    pyautogui.hotkey('ctrl', 'tab')

def handle_prev_tab(value, speak, listen, memory):
    pyautogui.hotkey('ctrl', 'shift', 'tab')

def handle_refresh(value, speak, listen, memory):
    pyautogui.press('f5')

def handle_close_window(value, speak, listen, memory):
    pyautogui.hotkey('alt', 'f4')

def handle_minimize(value, speak, listen, memory):
    pyautogui.hotkey('win', 'down')

def handle_maximize(value, speak, listen, memory):
    pyautogui.hotkey('win', 'up')

def handle_switch_window(value, speak, listen, memory):
    pyautogui.hotkey('alt', 'tab')

def handle_zoom_in(value, speak, listen, memory):
    pyautogui.hotkey('ctrl', '+')

def handle_zoom_out(value, speak, listen, memory):
    pyautogui.hotkey('ctrl', '-')

def handle_zoom_reset(value, speak, listen, memory):
    pyautogui.hotkey('ctrl', '0')
