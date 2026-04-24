import os
import re
import ast
import time
import random
import shutil
import operator
import subprocess
import webbrowser
from datetime import datetime

import psutil
import pyautogui
import requests
import wikipedia
import screen_brightness_control as sbc

from config import APP_PATHS
from memory import save_memory, get_memory

# All flows + screen vision now live in utils.py
from utils import (
    compose_email_flow, compose_whatsapp_flow,
    get_screen_description, find_and_click_on_screen
)

# speak, listen, memory are injected via execute_action() parameters
# to avoid circular import with jarvis.py


# ============================================================
#  SAFE CALCULATOR  (replaces dangerous eval())
# ============================================================
_SAFE_OPS = {
    ast.Add:  operator.add,
    ast.Sub:  operator.sub,
    ast.Mult: operator.mul,
    ast.Div:  operator.truediv,
    ast.Pow:  operator.pow,
    ast.Mod:  operator.mod,
    ast.USub: operator.neg,
}

def _safe_eval(expr):
    """Evaluate a math expression safely without using eval()."""
    def _eval(node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Only numbers allowed")
        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in _SAFE_OPS:
                raise ValueError(f"Unsupported operator: {op_type}")
            return _SAFE_OPS[op_type](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in _SAFE_OPS:
                raise ValueError(f"Unsupported operator: {op_type}")
            return _SAFE_OPS[op_type](_eval(node.operand))
        else:
            raise ValueError(f"Unsupported node: {type(node)}")
    tree = ast.parse(expr, mode='eval')
    return _eval(tree.body)


# ============================================================
#  PATH HELPER
# ============================================================
def get_path(location):
    home  = os.path.expanduser("~")
    paths = {
        "desktop":   os.path.join(home, "Desktop"),
        "documents": os.path.join(home, "Documents"),
        "downloads": os.path.join(home, "Downloads"),
        "pictures":  os.path.join(home, "Pictures"),
        "music":     os.path.join(home, "Music"),
        "videos":    os.path.join(home, "Videos"),
    }
    for key, path in paths.items():
        if key in location.lower():
            return path
    return os.path.join(home, "Desktop", location)


# ============================================================
#  VOLUME
# ============================================================
def set_volume_level(level):
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from comtypes import CLSCTX_ALL
        from ctypes import cast, POINTER
        devices   = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume    = cast(interface, POINTER(IAudioEndpointVolume))
        scalar    = max(0.0, min(1.0, level / 100))
        volume.SetMasterVolumeLevelScalar(scalar, None)
    except Exception as e:
        print(f"Volume error (pycaw): {e} — keypress fallback")
        for _ in range(50):
            pyautogui.press("volumedown")
        for _ in range(int(level / 2)):
            pyautogui.press("volumeup")


# ============================================================
#  APP OPENER  (5-method fallback)
# ============================================================
def find_exe_on_system(app_name):
    search_dirs = [
        os.environ.get("PROGRAMFILES", r"C:\Program Files"),
        os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
        os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Local"),
        os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Roaming"),
        r"C:\Windows\System32",
    ]
    app_clean  = app_name.lower().replace(" ", "").replace("-", "").replace("_", "")
    candidates = []
    for base in search_dirs:
        if not base or not os.path.exists(base):
            continue
        try:
            for root, dirs, files in os.walk(base):
                if root.replace(base, "").count(os.sep) > 4:
                    dirs.clear()
                    continue
                for f in files:
                    if f.lower().endswith(".exe"):
                        fname = f.lower().replace(".exe","").replace(" ","").replace("-","").replace("_","")
                        if app_clean in fname or fname in app_clean:
                            candidates.append(os.path.join(root, f))
        except PermissionError:
            continue
    candidates.sort(key=lambda x: len(x))
    return candidates[0] if candidates else None


def open_app(app_name, speak):
    app_lower = app_name.lower().strip()
    username  = os.environ.get("USERNAME", "User")
    print(f"DEBUG open_app: '{app_lower}'")

    # Method 1: Known paths dict
    path = APP_PATHS.get(app_lower) or get_memory(f"app_path_{app_lower}")
    if path:
        path     = path.replace("%USERNAME%", username)
        exe_path = path.split(" --")[0].strip()
        if os.path.exists(exe_path):
            try:
                subprocess.Popen(exe_path, shell=True)
                speak(f"Opening {app_name}!")
                return
            except Exception as e:
                print(f"Method 1 failed: {e}")

    # Method 2: 'where' command
    for variant in [app_lower, app_lower.replace(" ", ""), app_lower.replace(" ", "_")]:
        try:
            result = subprocess.run(
                f"where {variant}.exe",
                shell=True, capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                exe = result.stdout.strip().splitlines()[0].strip()
                if os.path.exists(exe):
                    subprocess.Popen(exe, shell=True)
                    speak(f"Opening {app_name}!")
                    return
        except Exception as e:
            print(f"Method 2 ({variant}) failed: {e}")

    # Method 3: PowerShell Start Menu (UWP/Store apps)
    try:
        ps_cmd = (
            f'powershell -NoProfile -Command "'
            f'$a=Get-StartApps|Where-Object{{$_.Name -like \'*{app_name}*\'}}|Select-Object -First 1;'
            f'if($a){{Start-Process $a.AppID;Write-Output $a.Name}}else{{Write-Output NOT_FOUND}}"'
        )
        res = subprocess.run(ps_cmd, shell=True, capture_output=True, text=True, timeout=8)
        out = res.stdout.strip()
        print(f"Method 3 output: {out}")
        if out and "NOT_FOUND" not in out:
            speak(f"Opening {app_name}!")
            return
    except Exception as e:
        print(f"Method 3 failed: {e}")

    # Method 4: Filesystem auto-scan + remember path
    speak(f"Searching your system for {app_name}, one moment...")
    found = find_exe_on_system(app_lower)
    if found:
        print(f"Method 4 found: {found}")
        try:
            subprocess.Popen(found, shell=True)
            APP_PATHS[app_lower] = found
            save_memory(f"app_path_{app_lower}", found)
            speak(f"Found {app_name} and opening it! I'll remember this next time.")
            return
        except Exception as e:
            print(f"Method 4 launch failed: {e}")

    # Method 5: os.startfile last resort
    try:
        os.startfile(app_lower)
        speak(f"Opening {app_name}!")
        return
    except Exception:
        pass

    speak(f"Sorry Boss, I could not find {app_name} on your system!")


# ============================================================
#  EXECUTE ACTION
# ============================================================
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

    # ── Communication ────────────────────────────────────────
    if action == "SEND_EMAIL":
        compose_email_flow(speak, listen, memory)

    elif action == "SEND_WHATSAPP":
        compose_whatsapp_flow(speak, listen, memory)

    # ── Screen Vision ─────────────────────────────────────────
    elif action == "SCREEN_DESCRIBE":
        speak("Let me take a look at your screen...")
        speak(get_screen_description(value or "What is on the screen?"))

    elif action == "SCREEN_CLICK":
        speak(f"Looking for {value} on screen...")
        find_and_click_on_screen(value, speak)

    # ── Apps & URLs ───────────────────────────────────────────
    elif action == "OPEN_APP":
        open_app(value, speak)
        time.sleep(2)

    elif action == "OPEN_URL":
        if not value.startswith("http"):
            value = "https://" + value
        webbrowser.open(value)

    elif action == "SEARCH":
        webbrowser.open(f"https://google.com/search?q={value.replace(' ', '+')}")

    elif action == "YOUTUBE":
        webbrowser.open(f"https://youtube.com/results?search_query={value.replace(' ', '+')}")

    # ── Volume ────────────────────────────────────────────────
    elif action == "VOLUME_UP":
        for _ in range(5): pyautogui.press("volumeup")

    elif action == "VOLUME_DOWN":
        for _ in range(5): pyautogui.press("volumedown")

    elif action == "VOLUME_SET":
        set_volume_level(int(value))
        speak(f"Volume set to {value} percent!")

    elif action == "MUTE":
        pyautogui.press("volumemute")

    # ── Screenshot ────────────────────────────────────────────
    elif action == "SCREENSHOT":
        filename = f"screenshot_{datetime.now().strftime('%H%M%S')}.png"
        path     = os.path.join(os.path.expanduser("~"), "Desktop", filename)
        pyautogui.screenshot().save(path)
        memory["last_file"]   = filename
        memory["last_action"] = f"took screenshot {filename}"
        save_memory("last_file",   filename)
        save_memory("last_action", memory["last_action"])
        speak(f"Screenshot saved as {filename}!")

    # ── Scroll ────────────────────────────────────────────────
    elif action == "SCROLL_UP":           pyautogui.scroll(5)
    elif action == "SCROLL_DOWN":         pyautogui.scroll(-5)
    elif action == "SCROLL_UP_FAST":      pyautogui.scroll(15)
    elif action == "SCROLL_DOWN_FAST":    pyautogui.scroll(-15)

    # ── Mouse ─────────────────────────────────────────────────
    elif action == "CLICK":               pyautogui.click()
    elif action == "RIGHT_CLICK":         pyautogui.rightClick()
    elif action == "DOUBLE_CLICK":        pyautogui.doubleClick()

    # ── Keyboard ──────────────────────────────────────────────
    elif action == "TYPE":
        pyautogui.typewrite(value, interval=0.05)

    elif action == "PRESS_KEY":
        pyautogui.press(value)

    elif action == "HOTKEY":
        pyautogui.hotkey(*value.split("+"))

    elif action == "COPY":       pyautogui.hotkey('ctrl', 'c')
    elif action == "PASTE":      pyautogui.hotkey('ctrl', 'v')
    elif action == "UNDO":       pyautogui.hotkey('ctrl', 'z')
    elif action == "REDO":       pyautogui.hotkey('ctrl', 'y')
    elif action == "SELECT_ALL": pyautogui.hotkey('ctrl', 'a')

    elif action == "FIND":
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(0.5)
        pyautogui.typewrite(value, interval=0.05)

    # ── Tabs / Windows ────────────────────────────────────────
    elif action == "NEW_TAB":       pyautogui.hotkey('ctrl', 't')
    elif action == "CLOSE_TAB":     pyautogui.hotkey('ctrl', 'w')
    elif action == "REOPEN_TAB":    pyautogui.hotkey('ctrl', 'shift', 't')
    elif action == "NEXT_TAB":      pyautogui.hotkey('ctrl', 'tab')
    elif action == "PREV_TAB":      pyautogui.hotkey('ctrl', 'shift', 'tab')
    elif action == "REFRESH":       pyautogui.press('f5')

    elif action == "CLOSE_WINDOW":
        pyautogui.hotkey('alt', 'tab')
        time.sleep(0.5)
        pyautogui.hotkey('alt', 'f4')

    elif action == "MINIMIZE":      pyautogui.hotkey('win', 'down')
    elif action == "MAXIMIZE":      pyautogui.hotkey('win', 'up')
    elif action == "SWITCH_WINDOW": pyautogui.hotkey('alt', 'tab')
    elif action == "ZOOM_IN":       pyautogui.hotkey('ctrl', '+')
    elif action == "ZOOM_OUT":      pyautogui.hotkey('ctrl', '-')
    elif action == "ZOOM_RESET":    pyautogui.hotkey('ctrl', '0')

    # ── Brightness ────────────────────────────────────────────
    elif action == "BRIGHTNESS_UP":
        try:
            sbc.set_brightness(min(100, sbc.get_brightness()[0] + 20))
            speak("Brightness increased!")
        except Exception:
            speak("Could not change brightness!")

    elif action == "BRIGHTNESS_DOWN":
        try:
            sbc.set_brightness(max(0, sbc.get_brightness()[0] - 20))
            speak("Brightness decreased!")
        except Exception:
            speak("Could not change brightness!")

    elif action == "BRIGHTNESS_SET":
        try:
            sbc.set_brightness(int(value))
            speak(f"Brightness set to {value} percent!")
        except Exception:
            speak("Could not set brightness!")

    # ── File Operations ───────────────────────────────────────
    elif action == "CREATE_FOLDER":
        try:
            parts       = value.split("/")
            base        = get_path(parts[0]) if len(parts) == 2 else get_path("desktop")
            folder_name = parts[1] if len(parts) == 2 else value
            os.makedirs(os.path.join(base, folder_name), exist_ok=True)
            memory["last_folder"] = folder_name
            memory["last_action"] = f"created folder {folder_name}"
            save_memory("last_folder", folder_name)
            save_memory("last_action", memory["last_action"])
            speak(f"Folder {folder_name} created!")
        except Exception:
            speak("Could not create folder!")

    elif action == "CREATE_FILE":
        try:
            parts     = value.split("/")
            base      = get_path(parts[0]) if len(parts) >= 2 else get_path("desktop")
            file_name = "/".join(parts[1:]) if len(parts) >= 2 else value
            file_path = os.path.join(base, file_name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            # FIX: use 'with' to properly close the file handle
            with open(file_path, 'w'):
                pass
            memory["last_file"]   = file_name
            memory["last_action"] = f"created file {file_name}"
            save_memory("last_file",   file_name)
            save_memory("last_action", memory["last_action"])
            speak(f"File {file_name} created!")
        except Exception:
            speak("Could not create file!")

    elif action == "DELETE":
        try:
            parts  = value.split("/")
            base   = get_path(parts[0]) if len(parts) == 2 else get_path("desktop")
            name   = parts[1] if len(parts) == 2 else value
            target = os.path.join(base, name)
            shutil.rmtree(target) if os.path.isdir(target) else os.remove(target)
            memory["last_action"] = f"deleted {name}"
            save_memory("last_action", memory["last_action"])
            speak(f"Deleted {name}!")
        except Exception:
            speak("Could not delete. Check the name!")

    elif action == "RENAME":
        try:
            old, new = value.split("|")
            desktop  = get_path("desktop")
            os.rename(
                os.path.join(desktop, old.strip()),
                os.path.join(desktop, new.strip())
            )
            memory["last_file"]   = new.strip()
            memory["last_action"] = f"renamed to {new.strip()}"
            save_memory("last_file",   new.strip())
            save_memory("last_action", memory["last_action"])
            speak(f"Renamed to {new.strip()}!")
        except Exception:
            speak("Could not rename!")

    elif action == "LIST_FILES":
        try:
            files = os.listdir(get_path(value))
            if files:
                speak(f"Found {len(files)} items in {value}.")
                for f in files[:10]: print(f"  - {f}")
            else:
                speak(f"{value} is empty!")
        except Exception:
            speak("Could not list files!")

    elif action == "MOVE_FILE":
        try:
            filename, destination = value.split("|")
            shutil.move(
                os.path.join(get_path("desktop"), filename.strip()),
                get_path(destination.strip())
            )
            memory["last_action"] = f"moved {filename} to {destination}"
            save_memory("last_action", memory["last_action"])
            speak(f"Moved {filename.strip()} to {destination.strip()}!")
        except Exception:
            speak("Could not move file!")

    elif action == "COPY_FILE":
        try:
            filename, destination = value.split("|")
            shutil.copy2(
                os.path.join(get_path("desktop"), filename.strip()),
                get_path(destination.strip())
            )
            memory["last_action"] = f"copied {filename} to {destination}"
            save_memory("last_action", memory["last_action"])
            speak(f"Copied {filename.strip()} to {destination.strip()}!")
        except Exception:
            speak("Could not copy file!")

    elif action == "OPEN_FILE":
        try:
            file_path = os.path.join(get_path("desktop"), value)
            os.startfile(file_path)
            memory["last_file"] = value
            save_memory("last_file", value)
            speak(f"Opening {value}!")
        except Exception:
            speak("Could not open file!")

    # ── System Info ───────────────────────────────────────────
    elif action == "SYSTEM_INFO":
        cpu  = psutil.cpu_percent(interval=1)
        ram  = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        bat  = psutil.sensors_battery()
        bat_info = f"Battery at {int(bat.percent)}%." if bat else ""
        speak(f"CPU {cpu}%. RAM {ram.percent}%. Disk {disk.percent}%. {bat_info}")

    elif action == "BATTERY_STATUS":
        bat = psutil.sensors_battery()
        if bat:
            status = "charging" if bat.power_plugged else "not charging"
            speak(f"Battery is at {int(bat.percent)}% and is {status}.")
        else:
            speak("Could not get battery info!")

    elif action == "CPU_USAGE":
        speak(f"CPU usage is {psutil.cpu_percent(interval=1)}%.")

    elif action == "RAM_USAGE":
        ram = psutil.virtual_memory()
        speak(f"RAM {ram.percent}%. {ram.used//(1024**3)}GB of {ram.total//(1024**3)}GB used.")

    elif action == "DISK_USAGE":
        disk = psutil.disk_usage('/')
        speak(f"Disk {disk.percent}%. {disk.used//(1024**3)}GB of {disk.total//(1024**3)}GB used.")

    # ── Weather / Wiki / Calc ─────────────────────────────────
    elif action == "WEATHER":
        try:
            city = value.strip() if value else "Delhi"
            r    = requests.get(f"https://wttr.in/{city}?format=3", timeout=5)
            speak(f"Weather: {r.content.decode('utf-8').encode('ascii','ignore').decode('ascii').strip()}")
        except Exception:
            speak("Could not get weather info!")

    elif action == "WIKIPEDIA":
        try:
            wikipedia.set_lang("en")
            try:
                result = wikipedia.summary(value, sentences=2, auto_suggest=False)
            except wikipedia.exceptions.DisambiguationError as e:
                result = wikipedia.summary(e.options[0], sentences=2, auto_suggest=False)
            speak(result)
        except Exception:
            speak(f"Could not find info about {value}!")

    elif action == "CALCULATE":
        # FIX: replaced dangerous eval() with safe AST-based evaluator
        try:
            result = _safe_eval(value)
            # Clean up float display: show int if result is whole number
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            speak(f"The answer is {result}")
        except Exception as e:
            speak(f"Could not calculate that. {e}")

    # ── Time / Date / Joke ────────────────────────────────────
    elif action == "TIME":
        speak(f"Current time is {datetime.now().strftime('%I:%M %p')}")

    elif action == "DATE":
        speak(f"Today is {datetime.now().strftime('%B %d, %Y')}")

    elif action == "JOKE":
        jokes = [
            "Why do programmers prefer dark mode? Because light attracts bugs!",
            "Why did the computer go to the doctor? Because it had a virus!",
            "What do you call a computer that sings? A Dell!",
            "Why was the JavaScript developer sad? Because he didn't know how to null his feelings!",
            "How many programmers does it take to change a light bulb? None, that is a hardware problem!",
        ]
        speak(random.choice(jokes))

    # ── Misc ──────────────────────────────────────────────────
    elif action == "TASK_MANAGER":
        subprocess.Popen("taskmgr.exe")
        speak("Opening Task Manager!")

    elif action == "EMPTY_RECYCLE_BIN":
        # FIX: replaced unsafe rd /s /q command with PowerShell safe method
        try:
            subprocess.run(
                'powershell -NoProfile -Command "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"',
                shell=True, timeout=15
            )
            speak("Recycle bin emptied!")
        except Exception:
            speak("Could not empty recycle bin!")

    # ── Power ─────────────────────────────────────────────────
    elif action == "LOCK":
        os.system("rundll32.exe user32.dll,LockWorkStation")

    elif action == "SHUTDOWN":
        speak("Shutting down in 5 seconds!")
        os.system("shutdown /s /t 5")

    elif action == "RESTART":
        speak("Restarting in 5 seconds!")
        os.system("shutdown /r /t 5")

    elif action == "SLEEP":
        speak("Going to sleep!")
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

    elif action == "HIBERNATE":
        speak("Hibernating!")
        os.system("shutdown /h")