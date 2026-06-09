import pyautogui
import time

def handle_scroll_up(value, speak, listen, memory):
    pyautogui.scroll(5)

def handle_scroll_down(value, speak, listen, memory):
    pyautogui.scroll(-5)

def handle_scroll_up_fast(value, speak, listen, memory):
    pyautogui.scroll(15)

def handle_scroll_down_fast(value, speak, listen, memory):
    pyautogui.scroll(-15)

def handle_click(value, speak, listen, memory):
    pyautogui.click()

def handle_right_click(value, speak, listen, memory):
    pyautogui.rightClick()

def handle_double_click(value, speak, listen, memory):
    pyautogui.doubleClick()

def handle_type(value, speak, listen, memory):
    pyautogui.typewrite(value, interval=0.05)

def handle_press_key(value, speak, listen, memory):
    pyautogui.press(value)

def handle_hotkey(value, speak, listen, memory):
    pyautogui.hotkey(*value.split("+"))

def handle_copy(value, speak, listen, memory):
    pyautogui.hotkey('ctrl', 'c')

def handle_paste(value, speak, listen, memory):
    pyautogui.hotkey('ctrl', 'v')

def handle_undo(value, speak, listen, memory):
    pyautogui.hotkey('ctrl', 'z')

def handle_redo(value, speak, listen, memory):
    pyautogui.hotkey('ctrl', 'y')

def handle_select_all(value, speak, listen, memory):
    pyautogui.hotkey('ctrl', 'a')

def handle_find(value, speak, listen, memory):
    pyautogui.hotkey('ctrl', 'f')
    time.sleep(0.5)
    pyautogui.typewrite(value, interval=0.05)
