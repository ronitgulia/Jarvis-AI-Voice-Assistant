import re
import os
from datetime import datetime
import pyautogui
from memory import save_memory

# Import handlers
from .app import open_app
from .browser import (
    handle_open_url, handle_search, handle_youtube, handle_new_tab, handle_close_tab,
    handle_reopen_tab, handle_next_tab, handle_prev_tab, handle_refresh,
    handle_close_window, handle_minimize, handle_maximize, handle_switch_window,
    handle_zoom_in, handle_zoom_out, handle_zoom_reset
)
from .system import (
    handle_volume_up, handle_volume_down, handle_volume_set, handle_mute,
    handle_brightness_up, handle_brightness_down, handle_brightness_set,
    handle_system_info, handle_battery_status, handle_cpu_usage, handle_ram_usage,
    handle_disk_usage, handle_lock, handle_shutdown, handle_restart,
    handle_sleep, handle_hibernate
)
from .file_ops import (
    handle_create_folder, handle_create_file, handle_delete, handle_rename,
    handle_list_files, handle_move_file, handle_copy_file, handle_open_file
)
from .keyboard_mouse import (
    handle_scroll_up, handle_scroll_down, handle_scroll_up_fast, handle_scroll_down_fast,
    handle_click, handle_right_click, handle_double_click, handle_type, handle_press_key,
    handle_hotkey, handle_copy, handle_paste, handle_undo, handle_redo,
    handle_select_all, handle_find
)
from .misc import (
    handle_weather, handle_wikipedia, handle_calculate, handle_time, handle_date,
    handle_joke, handle_task_manager, handle_empty_recycle_bin
)
from .communication import handle_send_email, handle_send_whatsapp
from .vision import handle_screen_describe, handle_screen_click

def handle_screenshot(value, speak, listen, memory):
    filename = f"screenshot_{datetime.now().strftime('%H%M%S')}.png"
    path     = os.path.join(os.path.expanduser("~"), "Desktop", filename)
    pyautogui.screenshot().save(path)
    memory["last_file"]   = filename
    memory["last_action"] = f"took screenshot {filename}"
    save_memory("last_file",   filename)
    save_memory("last_action", memory["last_action"])
    speak(f"Screenshot saved as {filename}!")

ACTION_HANDLERS = {
    # App
    "OPEN_APP": open_app,
    
    # Browser
    "OPEN_URL": handle_open_url,
    "SEARCH": handle_search,
    "YOUTUBE": handle_youtube,
    "NEW_TAB": handle_new_tab,
    "CLOSE_TAB": handle_close_tab,
    "REOPEN_TAB": handle_reopen_tab,
    "NEXT_TAB": handle_next_tab,
    "PREV_TAB": handle_prev_tab,
    "REFRESH": handle_refresh,
    "CLOSE_WINDOW": handle_close_window,
    "MINIMIZE": handle_minimize,
    "MAXIMIZE": handle_maximize,
    "SWITCH_WINDOW": handle_switch_window,
    "ZOOM_IN": handle_zoom_in,
    "ZOOM_OUT": handle_zoom_out,
    "ZOOM_RESET": handle_zoom_reset,
    
    # System
    "VOLUME_UP": handle_volume_up,
    "VOLUME_DOWN": handle_volume_down,
    "VOLUME_SET": handle_volume_set,
    "MUTE": handle_mute,
    "BRIGHTNESS_UP": handle_brightness_up,
    "BRIGHTNESS_DOWN": handle_brightness_down,
    "BRIGHTNESS_SET": handle_brightness_set,
    "SYSTEM_INFO": handle_system_info,
    "BATTERY_STATUS": handle_battery_status,
    "CPU_USAGE": handle_cpu_usage,
    "RAM_USAGE": handle_ram_usage,
    "DISK_USAGE": handle_disk_usage,
    "LOCK": handle_lock,
    "SHUTDOWN": handle_shutdown,
    "RESTART": handle_restart,
    "SLEEP": handle_sleep,
    "HIBERNATE": handle_hibernate,
    "SCREENSHOT": handle_screenshot,
    
    # File Ops
    "CREATE_FOLDER": handle_create_folder,
    "CREATE_FILE": handle_create_file,
    "DELETE": handle_delete,
    "RENAME": handle_rename,
    "LIST_FILES": handle_list_files,
    "MOVE_FILE": handle_move_file,
    "COPY_FILE": handle_copy_file,
    "OPEN_FILE": handle_open_file,
    
    # Keyboard & Mouse
    "SCROLL_UP": handle_scroll_up,
    "SCROLL_DOWN": handle_scroll_down,
    "SCROLL_UP_FAST": handle_scroll_up_fast,
    "SCROLL_DOWN_FAST": handle_scroll_down_fast,
    "CLICK": handle_click,
    "RIGHT_CLICK": handle_right_click,
    "DOUBLE_CLICK": handle_double_click,
    "TYPE": handle_type,
    "PRESS_KEY": handle_press_key,
    "HOTKEY": handle_hotkey,
    "COPY": handle_copy,
    "PASTE": handle_paste,
    "UNDO": handle_undo,
    "REDO": handle_redo,
    "SELECT_ALL": handle_select_all,
    "FIND": handle_find,
    
    # Misc
    "WEATHER": handle_weather,
    "WIKIPEDIA": handle_wikipedia,
    "CALCULATE": handle_calculate,
    "TIME": handle_time,
    "DATE": handle_date,
    "JOKE": handle_joke,
    "TASK_MANAGER": handle_task_manager,
    "EMPTY_RECYCLE_BIN": handle_empty_recycle_bin,
    
    # Communication
    "SEND_EMAIL": handle_send_email,
    "SEND_WHATSAPP": handle_send_whatsapp,
    
    # Vision
    "SCREEN_DESCRIBE": handle_screen_describe,
    "SCREEN_CLICK": handle_screen_click,
}

def execute_action(response_text, speak, listen, memory):
    action_match   = re.search(r'\[([A-Z_]+)(?::([^\]]+))?\]', response_text)
    clean_response = re.sub(r'\[[^\]]+\]', '', response_text).strip()

    print(f"DEBUG full Groq response: {response_text}")

    if clean_response:
        speak(clean_response)

    if not action_match:
        print("DEBUG: No valid action tag found")
        return

    action = action_match.group(1)
    value  = action_match.group(2) if action_match.group(2) else ""
    print(f"DEBUG action={action!r}  value={value!r}")

    handler = ACTION_HANDLERS.get(action)
    if handler:
        handler(value, speak, listen, memory)
    else:
        print(f"DEBUG: No handler found for action {action}")
