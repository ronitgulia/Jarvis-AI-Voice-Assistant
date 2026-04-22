import speech_recognition as sr
import pyttsx3
import subprocess
import pyautogui
import os
import webbrowser
import shutil
from groq import Groq
from datetime import datetime
import psutil
import requests
import wikipedia
import screen_brightness_control as sbc
import re
import random
import time
import smtplib
import base64
import threading
import sqlite3
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pywhatkit as kit
from PIL import Image
import io

# ============================================================
#  PyQt5 GUI IMPORTS
# ============================================================
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QFrame, QProgressBar, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QBrush, QLinearGradient, QPalette
import sys

# ============================================================
#  CONFIG
# ============================================================
GROQ_API_KEY    = "API_Key"
GMAIL_ADDRESS   = "ronitgulia3@gmail.com"
GMAIL_APP_PASS  = "xxxx xxxx xxxx xxxx"
WAKE_WORD       = "hey jarvis"
USER_NAME       = "Boss"

CONTACTS = {
    "my":    "917404261074",
    "ronit": "919319333635",
}

# ============================================================
#  SQLITE PERMANENT MEMORY
# ============================================================
DB_PATH = os.path.join(os.path.expanduser("~"), "jarvis_memory.db")

def init_db():
    """Create tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Key-value store for preferences & facts
    c.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            key   TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT
        )
    """)
    # Full conversation history (permanent)
    c.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            role       TEXT,
            content    TEXT,
            created_at TEXT
        )
    """)
    # Command history log
    c.execute("""
        CREATE TABLE IF NOT EXISTS command_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            command    TEXT,
            response   TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_memory(key, value):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO memory (key, value, updated_at) VALUES (?, ?, ?)",
        (key, str(value), datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_memory(key, default=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        result = conn.execute("SELECT value FROM memory WHERE key=?", (key,)).fetchone()
        conn.close()
        return result[0] if result else default
    except:
        return default

def save_conversation_to_db(role, content):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO conversations (role, content, created_at) VALUES (?, ?, ?)",
        (role, content, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def log_command(command, response):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO command_log (command, response, created_at) VALUES (?, ?, ?)",
        (command, response, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_last_n_conversations(n=10):
    """Load last N conversations from DB for context."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?", (n,)
    ).fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

def get_recent_commands(n=5):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT command, created_at FROM command_log ORDER BY id DESC LIMIT ?", (n,)
    ).fetchall()
    conn.close()
    return rows

# ============================================================
#  APP REGISTRY
# ============================================================
APP_PATHS = {
    "chrome":        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "google chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox":       r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "edge":          r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "brave":         r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    "spotify":       r"C:\Users\%USERNAME%\AppData\Roaming\Spotify\Spotify.exe",
    "vlc":           r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "word":          r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel":         r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    "powerpoint":    r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
    "outlook":       r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE",
    "vscode":        r"C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "vs code":       r"C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "pycharm":       r"C:\Program Files\JetBrains\PyCharm Community Edition\bin\pycharm64.exe",
    "notepad++":     r"C:\Program Files\Notepad++\notepad++.exe",
    "notepad":       "notepad.exe",
    "cmd":           "cmd.exe",
    "powershell":    "powershell.exe",
    "discord":       r"C:\Users\%USERNAME%\AppData\Local\Discord\Update.exe",
    "telegram":      r"C:\Users\%USERNAME%\AppData\Roaming\Telegram Desktop\Telegram.exe",
    "whatsapp":      r"C:\Users\%USERNAME%\AppData\Local\WhatsApp\WhatsApp.exe",
    "zoom":          r"C:\Users\%USERNAME%\AppData\Roaming\Zoom\bin\Zoom.exe",
    "teams":         r"C:\Users\%USERNAME%\AppData\Local\Microsoft\Teams\current\Teams.exe",
    "slack":         r"C:\Users\%USERNAME%\AppData\Local\slack\slack.exe",
    "calculator":    "calc.exe",
    "calc":          "calc.exe",
    "paint":         "mspaint.exe",
    "explorer":      "explorer.exe",
    "file explorer": "explorer.exe",
    "control panel": "control.exe",
    "task manager":  "taskmgr.exe",
    "snipping tool": "snippingtool.exe",
    "steam":         r"C:\Program Files (x86)\Steam\steam.exe",
    "obs":           r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
    "obs studio":    r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
    "notion":        r"C:\Users\%USERNAME%\AppData\Local\Programs\Notion\Notion.exe",
    "figma":         r"C:\Users\%USERNAME%\AppData\Local\Figma\Figma.exe",
    "postman":       r"C:\Users\%USERNAME%\AppData\Local\Postman\Postman.exe",
}


def find_exe_on_system(app_name):
    search_dirs = [
        os.environ.get("PROGRAMFILES", r"C:\Program Files"),
        os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
        os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Local"),
        os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Roaming"),
        r"C:\Windows\System32",
    ]
    app_clean = app_name.lower().replace(" ","").replace("-","").replace("_","")
    candidates = []
    for base in search_dirs:
        if not base or not os.path.exists(base):
            continue
        try:
            for root, dirs, files in os.walk(base):
                if root.replace(base,"").count(os.sep) > 4:
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


def open_app(app_name):
    """5 fallback methods — auto finds app anywhere on system."""
    app_lower = app_name.lower().strip()
    username  = os.environ.get("USERNAME", "User")
    print(f"DEBUG open_app: '{app_lower}'")

    # Method 1: Known APP_PATHS dict + saved DB paths
    path = APP_PATHS.get(app_lower) or get_memory(f"app_path_{app_lower}")
    if path:
        path = path.replace("%USERNAME%", username)
        exe_path = path.split(" --")[0].strip()
        if os.path.exists(exe_path):
            try:
                subprocess.Popen(exe_path, shell=True)
                speak(f"Opening {app_name}!")
                return
            except Exception as e:
                print(f"Method 1 failed: {e}")

    # Method 2: 'where' command — multiple name variations
    for variant in [app_lower, app_lower.replace(" ",""), app_lower.replace(" ","_")]:
        try:
            result = subprocess.run(f"where {variant}.exe",
                shell=True, capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                exe = result.stdout.strip().splitlines()[0].strip()
                if os.path.exists(exe):
                    subprocess.Popen(exe, shell=True)
                    speak(f"Opening {app_name}!")
                    return
        except Exception as e:
            print(f"Method 2 ({variant}) failed: {e}")

    # Method 3: PowerShell Start Menu (UWP / Store apps)
    try:
        ps_cmd = f'powershell -NoProfile -Command "$a=Get-StartApps|Where-Object{{$_.Name -like \'*{app_name}*\'}}|Select-Object -First 1;if($a){{Start-Process $a.AppID;Write-Output $a.Name}}else{{Write-Output NOT_FOUND}}"'
        res = subprocess.run(ps_cmd, shell=True, capture_output=True, text=True, timeout=8)
        out = res.stdout.strip()
        print(f"Method 3 output: {out}")
        if out and "NOT_FOUND" not in out:
            speak(f"Opening {app_name}!")
            return
    except Exception as e:
        print(f"Method 3 failed: {e}")

    # Method 4: Filesystem auto-scan + remember for next time
    speak(f"Searching your system for {app_name}, one moment...")
    found = find_exe_on_system(app_lower)
    if found:
        print(f"Method 4 found: {found}")
        try:
            subprocess.Popen(found, shell=True)
            APP_PATHS[app_lower] = found
            save_memory(f"app_path_{app_lower}", found)
            speak(f"Found {app_name} and opening it! I will remember this path next time.")
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
#  GROQ CLIENT
# ============================================================
client = Groq(api_key=GROQ_API_KEY)

# ============================================================
#  TTS  — dedicated thread so speech never blocks actions
# ============================================================
engine = pyttsx3.init()
engine.setProperty('rate', 170)
engine.setProperty('volume', 1.0)

_tts_lock = threading.Lock()

def _tts_worker(text):
    with _tts_lock:
        engine.say(text)
        engine.runAndWait()

# ============================================================
#  SESSION MEMORY (runtime, backed by SQLite)
# ============================================================
init_db()

memory = {
    "last_file":   get_memory("last_file"),
    "last_folder": get_memory("last_folder"),
    "last_action": get_memory("last_action"),
    "user_name":   get_memory("user_name", USER_NAME),
}
conversation_history = get_last_n_conversations(10)

# ============================================================
#  GUI — JARVIS DASHBOARD
# ============================================================
class JarvisDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("J.A.R.V.I.S  — Just A Rather Very Intelligent System")
        self.setMinimumSize(900, 600)
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #0a0e1a;
                color: #00d4ff;
                font-family: 'Consolas', 'Courier New', monospace;
            }
            QLabel { color: #00d4ff; }
            QTextEdit {
                background-color: #050810;
                color: #00ff88;
                border: 1px solid #00d4ff30;
                border-radius: 6px;
                padding: 8px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
            QProgressBar {
                background-color: #050810;
                border: 1px solid #00d4ff40;
                border-radius: 4px;
                height: 8px;
                text-align: center;
                color: transparent;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00d4ff, stop:1 #0088ff);
                border-radius: 4px;
            }
            QFrame#card {
                background-color: #0d1424;
                border: 1px solid #00d4ff25;
                border-radius: 8px;
            }
            QScrollBar:vertical {
                background: #050810;
                width: 6px;
            }
            QScrollBar::handle:vertical {
                background: #00d4ff40;
                border-radius: 3px;
            }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(10)

        # ── HEADER ──
        header = QLabel("◈  J.A.R.V.I.S  CONTROL INTERFACE  ◈")
        header.setFont(QFont("Consolas", 14, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #00d4ff; letter-spacing: 3px; padding: 6px;")
        main_layout.addWidget(header)

        # ── STATUS BAR ──
        status_frame = QFrame()
        status_frame.setObjectName("card")
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(12, 8, 12, 8)

        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("color: #00ff88; font-size: 14px;")
        self.status_label = QLabel("STANDBY — Waiting for wake word")
        self.status_label.setStyleSheet("color: #00ff88; font-size: 12px; letter-spacing: 1px;")

        self.time_label = QLabel()
        self.time_label.setStyleSheet("color: #00d4ff80; font-size: 11px;")
        self.time_label.setAlignment(Qt.AlignRight)

        status_layout.addWidget(self.status_dot)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.time_label)
        main_layout.addWidget(status_frame)

        # ── MIDDLE ROW ──
        mid_layout = QHBoxLayout()
        mid_layout.setSpacing(10)

        # Left — Conversation log
        left_frame = QFrame()
        left_frame.setObjectName("card")
        left_v = QVBoxLayout(left_frame)
        left_v.setContentsMargins(10, 8, 10, 8)
        left_v.setSpacing(6)
        left_v.addWidget(self._section_label("CONVERSATION LOG"))
        self.convo_log = QTextEdit()
        self.convo_log.setReadOnly(True)
        self.convo_log.setMinimumHeight(250)
        left_v.addWidget(self.convo_log)
        mid_layout.addWidget(left_frame, 3)

        # Right — Stats + Memory
        right_v = QVBoxLayout()
        right_v.setSpacing(10)

        # System stats card
        stats_frame = QFrame()
        stats_frame.setObjectName("card")
        stats_v = QVBoxLayout(stats_frame)
        stats_v.setContentsMargins(10, 8, 10, 8)
        stats_v.setSpacing(8)
        stats_v.addWidget(self._section_label("SYSTEM STATUS"))

        self.cpu_bar  = self._stat_row(stats_v, "CPU")
        self.ram_bar  = self._stat_row(stats_v, "RAM")
        self.disk_bar = self._stat_row(stats_v, "DISK")

        self.battery_label = QLabel("⚡ Battery: --")
        self.battery_label.setStyleSheet("color: #00d4ff80; font-size: 11px;")
        stats_v.addWidget(self.battery_label)
        right_v.addWidget(stats_frame)

        # Memory card
        mem_frame = QFrame()
        mem_frame.setObjectName("card")
        mem_v = QVBoxLayout(mem_frame)
        mem_v.setContentsMargins(10, 8, 10, 8)
        mem_v.setSpacing(6)
        mem_v.addWidget(self._section_label("PERSISTENT MEMORY"))
        self.memory_display = QTextEdit()
        self.memory_display.setReadOnly(True)
        self.memory_display.setMaximumHeight(120)
        mem_v.addWidget(self.memory_display)
        right_v.addWidget(mem_frame)

        mid_layout.addLayout(right_v, 2)
        main_layout.addLayout(mid_layout)

        # ── LAST COMMAND + RESPONSE ──
        bottom_frame = QFrame()
        bottom_frame.setObjectName("card")
        bottom_h = QHBoxLayout(bottom_frame)
        bottom_h.setContentsMargins(12, 8, 12, 8)
        bottom_h.setSpacing(16)

        cmd_v = QVBoxLayout()
        cmd_v.addWidget(self._section_label("LAST COMMAND"))
        self.last_cmd = QLabel("—")
        self.last_cmd.setStyleSheet("color: #ffaa00; font-size: 12px; padding: 4px 0;")
        self.last_cmd.setWordWrap(True)
        cmd_v.addWidget(self.last_cmd)
        bottom_h.addLayout(cmd_v, 1)

        resp_v = QVBoxLayout()
        resp_v.addWidget(self._section_label("JARVIS RESPONSE"))
        self.last_resp = QLabel("Awaiting command...")
        self.last_resp.setStyleSheet("color: #00ff88; font-size: 12px; padding: 4px 0;")
        self.last_resp.setWordWrap(True)
        resp_v.addWidget(self.last_resp)
        bottom_h.addLayout(resp_v, 2)

        main_layout.addWidget(bottom_frame)

        # ── TIMERS ──
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)

        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_stats)
        self.stats_timer.start(3000)

        self.mem_timer = QTimer()
        self.mem_timer.timeout.connect(self._update_memory_display)
        self.mem_timer.start(5000)

        self._update_clock()
        self._update_stats()
        self._update_memory_display()

    def _section_label(self, text):
        lbl = QLabel(f"▸ {text}")
        lbl.setStyleSheet("color: #00d4ff60; font-size: 10px; letter-spacing: 2px;")
        lbl.setFont(QFont("Consolas", 9))
        return lbl

    def _stat_row(self, layout, label):
        row = QHBoxLayout()
        lbl = QLabel(f"{label}:")
        lbl.setStyleSheet("color: #00d4ff80; font-size: 11px;")
        lbl.setFixedWidth(38)
        bar = QProgressBar()
        bar.setRange(0, 100)
        val = QLabel("0%")
        val.setStyleSheet("color: #00d4ff; font-size: 10px;")
        val.setFixedWidth(32)
        row.addWidget(lbl)
        row.addWidget(bar)
        row.addWidget(val)
        layout.addLayout(row)
        return bar, val

    def _update_clock(self):
        self.time_label.setText(datetime.now().strftime("%d %b %Y  |  %H:%M:%S"))

    def _update_stats(self):
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent

        self.cpu_bar[0].setValue(int(cpu))
        self.cpu_bar[1].setText(f"{int(cpu)}%")
        self.ram_bar[0].setValue(int(ram))
        self.ram_bar[1].setText(f"{int(ram)}%")
        self.disk_bar[0].setValue(int(disk))
        self.disk_bar[1].setText(f"{int(disk)}%")

        bat = psutil.sensors_battery()
        if bat:
            plug = "⚡ Charging" if bat.power_plugged else "🔋"
            self.battery_label.setText(f"{plug}  {int(bat.percent)}%")

    def _update_memory_display(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            rows = conn.execute(
                "SELECT key, value, updated_at FROM memory ORDER BY updated_at DESC LIMIT 8"
            ).fetchall()
            conn.close()
            text = ""
            for k, v, t in rows:
                short_t = t[11:16] if t else "--"
                text += f"[{short_t}] {k}: {v}\n"
            self.memory_display.setText(text or "No memories yet.")
        except:
            pass

    # ── PUBLIC METHODS (called from main thread via signals) ──

    def set_status(self, text, color="#00ff88"):
        self.status_label.setText(text)
        self.status_dot.setStyleSheet(f"color: {color}; font-size: 14px;")
        self.status_label.setStyleSheet(f"color: {color}; font-size: 12px; letter-spacing: 1px;")

    def add_convo(self, role, text):
        ts = datetime.now().strftime("%H:%M")
        if role == "user":
            line = f'<span style="color:#ffaa00">[{ts}] YOU » </span><span style="color:#ffffff">{text}</span>'
        else:
            line = f'<span style="color:#00d4ff">[{ts}] JARVIS » </span><span style="color:#00ff88">{text}</span>'
        self.convo_log.append(line)
        self.convo_log.verticalScrollBar().setValue(
            self.convo_log.verticalScrollBar().maximum()
        )

    def set_last_command(self, cmd):
        self.last_cmd.setText(cmd)

    def set_last_response(self, resp):
        self.last_resp.setText(resp)


# ============================================================
#  GLOBAL GUI REFERENCE  (set after QApplication created)
# ============================================================
gui: JarvisDashboard = None


# ============================================================
#  GUI SIGNAL BRIDGE  (thread-safe updates)
# ============================================================
class GuiBridge(QThread):
    status_signal   = pyqtSignal(str, str)
    convo_signal    = pyqtSignal(str, str)
    cmd_signal      = pyqtSignal(str)
    resp_signal     = pyqtSignal(str)

bridge = GuiBridge()

def gui_status(text, color="#00ff88"):
    if gui: bridge.status_signal.emit(text, color)

def gui_convo(role, text):
    if gui: bridge.convo_signal.emit(role, text)

def gui_cmd(text):
    if gui: bridge.cmd_signal.emit(text)

def gui_resp(text):
    if gui: bridge.resp_signal.emit(text)


# ============================================================
#  SPEAK  — non-blocking TTS so actions always execute
# ============================================================
_tts_lock = threading.Lock()

def _tts_worker(text):
    with _tts_lock:
        engine.say(text)
        engine.runAndWait()

def speak(text):
    print(f"JARVIS: {text}")
    gui_resp(text)
    gui_convo("jarvis", text)
    # Run TTS in separate thread — returns immediately so caller continues
    t = threading.Thread(target=_tts_worker, args=(text,), daemon=True)
    t.start()
    t.join()  # wait for speech to finish before next action starts

# ============================================================
#  LISTEN
# ============================================================
def listen(timeout=8, phrase_limit=12):
    r = sr.Recognizer()
    r.energy_threshold = 150           # 300 se 150 — halki awaaz bhi sunега
    r.dynamic_energy_threshold = True
    r.dynamic_energy_adjustment_damping = 0.10  # quickly adapts to room noise
    r.pause_threshold = 0.6            # 0.8 default se kam — shorter pauses accepted
    r.phrase_threshold = 0.2           # phrases quickly recognized
    gui_status("LISTENING...", "#ffaa00")
    with sr.Microphone() as source:
        print("\n🎤 Listening...")
        r.adjust_for_ambient_noise(source, duration=1.0)  # 0.5 se 1.0 — better calibration
        try:
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
            command = r.recognize_google(audio).lower()
            print(f"You said: {command}")
            gui_convo("user", command)
            gui_cmd(command)
            gui_status("PROCESSING...", "#00aaff")
            return command
        except sr.UnknownValueError:
            gui_status("ACTIVE — Ready", "#00ff88")
            return ""
        except sr.WaitTimeoutError:
            gui_status("STANDBY — Waiting for wake word", "#00d4ff")
            return ""
        except sr.RequestError:
            speak("Internet connection needed!")
            return ""

# ============================================================
#  WAKE WORD
# ============================================================
def wait_for_wake_word():
    r = sr.Recognizer()
    r.energy_threshold = 250
    r.dynamic_energy_threshold = True
    print(f"\n😴 Waiting for wake word: '{WAKE_WORD}' ...")
    gui_status("STANDBY — Say 'Hey Jarvis'", "#00d4ff60")
    while True:
        try:
            with sr.Microphone() as source:
                audio = r.listen(source, timeout=3, phrase_time_limit=4)
            text = r.recognize_google(audio).lower()
            if WAKE_WORD in text:
                print("✅ Wake word detected!")
                gui_status("WAKE WORD DETECTED!", "#00ff88")
                return True
        except Exception:
            pass

# ============================================================
#  SCREEN VISION
# ============================================================
def get_screen_description(user_question="What is on the screen?"):
    try:
        screenshot = pyautogui.screenshot()
        max_w = 1280
        if screenshot.width > max_w:
            ratio = max_w / screenshot.width
            screenshot = screenshot.resize(
                (max_w, int(screenshot.height * ratio)), Image.LANCZOS
            )
        buffer = io.BytesIO()
        screenshot.save(buffer, format="JPEG", quality=75)
        img_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                    {"type": "text", "text": f"You are JARVIS analyzing a screen for the user. {user_question} Be concise (2-3 sentences max)."},
                ],
            }],
            max_tokens=300,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Screen analysis failed: {e}"


def find_and_click_on_screen(target_description):
    try:
        screenshot = pyautogui.screenshot()
        sw, sh = screenshot.size
        buffer = io.BytesIO()
        screenshot.save(buffer, format="JPEG", quality=75)
        img_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        prompt = (
            f"Screen resolution is {sw}x{sh}. "
            f"Find '{target_description}' on screen. "
            f"Reply ONLY with: X,Y  (integer pixel coordinates of its center). "
            f"If not found reply: NOT_FOUND"
        )
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                    {"type": "text", "text": prompt},
                ],
            }],
            max_tokens=20,
        )
        coords_text = response.choices[0].message.content.strip()
        if "NOT_FOUND" in coords_text.upper():
            speak(f"I could not find {target_description} on screen.")
            return False
        coords = re.findall(r'\d+', coords_text)
        if len(coords) >= 2:
            x, y = int(coords[0]), int(coords[1])
            pyautogui.moveTo(x, y, duration=0.4)
            pyautogui.click()
            speak(f"Clicked on {target_description}!")
            return True
        else:
            speak("Could not determine coordinates.")
            return False
    except Exception as e:
        speak(f"Screen click failed: {e}")
        return False

# ============================================================
#  EMAIL
# ============================================================
def send_email(to_address, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From']    = GMAIL_ADDRESS
        msg['To']      = to_address
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
            server.sendmail(GMAIL_ADDRESS, to_address, msg.as_string())
        speak(f"Email sent to {to_address}!")
        memory["last_action"] = f"sent email to {to_address}"
        save_memory("last_action", memory["last_action"])
    except Exception as e:
        speak(f"Email failed: {e}")


def compose_email_flow():
    speak("Sure! Who should I send the email to? Say their email address or name.")
    recipient = listen()
    if not recipient:
        speak("Didn't catch the recipient. Cancelling.")
        return
    speak(f"Got it — {recipient}. What's the subject?")
    subject = listen()
    if not subject:
        subject = "No Subject"
    speak("Now tell me the message body.")
    body = listen(timeout=15, phrase_limit=30)
    if not body:
        speak("No message body heard. Cancelling.")
        return
    speak(f"Ready to send email to {recipient} with subject '{subject}'. Say yes to confirm.")
    time.sleep(0.8)                    # TTS finish hone do
    confirm = listen(timeout=10)
    print(f"DEBUG confirm heard: '{confirm}'")
    confirm_words = ["yes", "send", "haan", "ha", "han", "haa", "confirm", "do it",
                     "sure", "ok", "okay", "bilkul", "kar do", "bhej do", "karo", "bejo"]
    if any(w in confirm for w in confirm_words):
        clean_email = (recipient
                       .replace(" at the rate ", "@").replace(" at ", "@")
                       .replace(" dot ", ".").replace(" ", "").lower())
        send_email(clean_email, subject, body)
    else:
        speak("Email cancelled.")

# ============================================================
#  WHATSAPP
# ============================================================
def send_whatsapp(phone_or_name, message, wait_time=15):
    try:
        phone = phone_or_name.strip()
        for name, num in CONTACTS.items():
            if name.lower() in phone.lower():
                phone = num
                break
        if not phone.startswith("+"):
            if not phone.startswith("91"):
                phone = "91" + phone
            phone = "+" + phone
        now = datetime.now()
        send_hour   = now.hour
        send_minute = now.minute + 2
        if send_minute >= 60:
            send_minute -= 60
            send_hour = (send_hour + 1) % 24
        kit.sendwhatmsg(phone, message, send_hour, send_minute,
                        wait_time=wait_time, tab_close=True, close_time=5)
        speak(f"WhatsApp message scheduled for {phone}!")
        memory["last_action"] = f"sent WhatsApp to {phone}"
        save_memory("last_action", memory["last_action"])
    except Exception as e:
        speak(f"WhatsApp failed: {e}")


def compose_whatsapp_flow():
    speak("Sure! Who should I WhatsApp? Say their name or number.")
    contact = listen()
    if not contact:
        speak("Didn't catch the contact. Cancelling.")
        return
    speak(f"Got it — {contact}. What's the message?")
    message = listen(timeout=15, phrase_limit=30)
    if not message:
        speak("No message heard. Cancelling.")
        return
    speak(f"Sending WhatsApp to {contact}: '{message}'. Say yes to confirm.")
    time.sleep(0.8)                    # TTS finish hone do pehle mic khule
    confirm = listen(timeout=10)       # 6 se 10 — zyada time milega bolne ko
    print(f"DEBUG confirm heard: '{confirm}'")
    confirm_words = ["yes", "send", "haan", "ha", "han", "haa", "confirm", "do it",
                     "sure", "ok", "okay", "bilkul", "kar do", "bhej do", "karo", "bejo"]
    if any(w in confirm for w in confirm_words):
        digits_only = re.sub(r'\D', '', contact)
        resolved = digits_only if len(digits_only) >= 10 else contact
        send_whatsapp(resolved, message)
    else:
        speak(f"Confirm nahi hua, WhatsApp cancelled. I heard: {confirm or 'nothing'}")

# ============================================================
#  VOLUME
# ============================================================
def set_volume_level(level):
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from comtypes import CLSCTX_ALL
        from ctypes import cast, POINTER
        import comtypes
        devices   = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume    = cast(interface, POINTER(IAudioEndpointVolume))
        scalar    = max(0.0, min(1.0, level / 100))
        volume.SetMasterVolumeLevelScalar(scalar, None)
    except Exception as e:
        print(f"Volume error (pycaw): {e} — using keypress fallback")
        for _ in range(50): pyautogui.press("volumedown")
        for _ in range(int(level / 2)): pyautogui.press("volumeup")

# ============================================================
#  GROQ AI  (with persistent conversation context)
# ============================================================
def ask_groq(user_input):
    memory_context = f"""
    Last file: {memory['last_file'] or 'none'}
    Last folder: {memory['last_folder'] or 'none'}
    Last action: {memory['last_action'] or 'none'}
    User name: {memory['user_name']}
    """

    system_prompt = """You are JARVIS, an extremely intelligent and friendly laptop assistant like from Iron Man.
    Understand what the user wants naturally and respond with a short friendly reply + ONE action tag.
    Use memory context for references like "that file", "it", "the folder" etc.

    Available actions:
    [OPEN_APP:appname]
    [OPEN_URL:url]
    [SEARCH:query]
    [YOUTUBE:query]
    [VOLUME_UP] [VOLUME_DOWN] [VOLUME_SET:0-100] [MUTE]
    [SCREENSHOT]
    [SCROLL_UP] [SCROLL_DOWN] [SCROLL_UP_FAST] [SCROLL_DOWN_FAST]
    [CLICK] [RIGHT_CLICK] [DOUBLE_CLICK]
    [TYPE:text] [PRESS_KEY:keyname] [HOTKEY:key1+key2]
    [COPY] [PASTE] [UNDO] [REDO] [SELECT_ALL] [FIND:text]
    [NEW_TAB] [CLOSE_TAB] [REOPEN_TAB] [NEXT_TAB] [PREV_TAB]
    [REFRESH] [CLOSE_WINDOW] [MINIMIZE] [MAXIMIZE] [SWITCH_WINDOW]
    [ZOOM_IN] [ZOOM_OUT] [ZOOM_RESET]
    [BRIGHTNESS_UP] [BRIGHTNESS_DOWN] [BRIGHTNESS_SET:0-100]
    [CREATE_FOLDER:location/foldername] [CREATE_FILE:location/filename]
    [DELETE:location/name] [RENAME:oldname|newname]
    [LIST_FILES:location] [MOVE_FILE:filename|destination]
    [COPY_FILE:filename|destination] [OPEN_FILE:filename]
    [SYSTEM_INFO] [BATTERY_STATUS] [CPU_USAGE] [RAM_USAGE] [DISK_USAGE]
    [WEATHER:city]
    [WIKIPEDIA:topic]
    [CALCULATE:expression]
    [TIME] [DATE] [JOKE]
    [SEND_EMAIL]
    [SEND_WHATSAPP]
    [SCREEN_DESCRIBE:question]
    [SCREEN_CLICK:target]
    [LOCK] [SHUTDOWN] [RESTART] [SLEEP] [HIBERNATE]
    [EMPTY_RECYCLE_BIN] [TASK_MANAGER]
    [NONE]

    RULES:
    - Locations: Desktop, Documents, Downloads, Pictures, Music, Videos only
    - Use exact filenames with extensions
    - "that file" = last_file from memory
    - "that folder" = last_folder from memory
    - Max 2 sentence reply
    - Be witty and smart like JARVIS!
    - Never say you can't do something, always try
    - For email/whatsapp requests use [SEND_EMAIL] or [SEND_WHATSAPP]
    - For "what's on screen" or "what do you see" use [SCREEN_DESCRIBE:question]
    - For "click on X" use [SCREEN_CLICK:X]
    - For "play song / play music / chalao" ALWAYS use [YOUTUBE:song name] — never [NONE]
    - For "open app" use [OPEN_APP:appname] — e.g. spotify, vlc, winamp
    - EVERY command must end with ONE action tag, NEVER just reply without a tag
    - If unsure which action, default to [SEARCH:query] — never use [NONE] for media requests"""

    conversation_history.append({
        "role": "user",
        "content": f"Memory:\n{memory_context}\nUser: {user_input}"
    })
    # Save to DB
    save_conversation_to_db("user", user_input)

    if len(conversation_history) > 20:
        conversation_history.pop(0)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            *conversation_history
        ],
        max_tokens=250
    )

    reply = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": reply})
    save_conversation_to_db("assistant", reply)
    log_command(user_input, reply)
    return reply

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
#  EXECUTE ACTION
# ============================================================
def execute_action(response_text):
    action_match   = re.search(r'\[([A-Z_]+)(?::([^\]]+))?\]', response_text)
    clean_response = re.sub(r'\[[^\]]+\]', '', response_text).strip()

    print(f"DEBUG full Groq response: {response_text}")

    if clean_response:
        speak(clean_response)

    if not action_match:
        print("DEBUG: No valid action tag found — Groq returned NONE or bad tag")
        return

    action = action_match.group(1)
    value  = action_match.group(2) if action_match.group(2) else ""
    print(f"DEBUG action={action!r}  value={value!r}")

    if action == "SEND_EMAIL":
        compose_email_flow()

    elif action == "SEND_WHATSAPP":
        compose_whatsapp_flow()

    elif action == "SCREEN_DESCRIBE":
        question = value if value else "What is on the screen?"
        speak("Let me take a look at your screen...")
        description = get_screen_description(question)
        speak(description)

    elif action == "SCREEN_CLICK":
        speak(f"Looking for {value} on screen...")
        find_and_click_on_screen(value)

    elif action == "OPEN_APP":
        app = value.lower().replace(" ", "")
        subprocess.Popen(f"{app}.exe", shell=True)
        import time
        time.sleep(2)

    elif action == "OPEN_URL":
        if not value.startswith("http"):
            value = "https://" + value
        webbrowser.open(value)
        import time
        time.sleep(2)

    elif action == "CLOSE_WINDOW":
        import time
        pyautogui.hotkey('alt', 'tab')
        time.sleep(0.5)
        pyautogui.hotkey('alt', 'f4')
        
    elif action == "SEARCH":
        webbrowser.open(f"https://google.com/search?q={value.replace(' ', '+')}")

    elif action == "YOUTUBE":
        webbrowser.open(f"https://youtube.com/results?search_query={value.replace(' ', '+')}")

    elif action == "VOLUME_UP":
        for _ in range(5): pyautogui.press("volumeup")

    elif action == "VOLUME_DOWN":
        for _ in range(5): pyautogui.press("volumedown")

    elif action == "VOLUME_SET":
        set_volume_level(int(value))
        speak(f"Volume set to {value} percent!")

    elif action == "MUTE":
        pyautogui.press("volumemute")

    elif action == "SCREENSHOT":
        filename = f"screenshot_{datetime.now().strftime('%H%M%S')}.png"
        path = os.path.join(os.path.expanduser("~"), "Desktop", filename)
        pyautogui.screenshot().save(path)
        memory["last_file"]   = filename
        memory["last_action"] = f"took screenshot {filename}"
        save_memory("last_file", filename)
        save_memory("last_action", memory["last_action"])
        speak(f"Screenshot saved as {filename}!")

    elif action == "SCROLL_UP":           pyautogui.scroll(5)
    elif action == "SCROLL_DOWN":         pyautogui.scroll(-5)
    elif action == "SCROLL_UP_FAST":      pyautogui.scroll(15)
    elif action == "SCROLL_DOWN_FAST":    pyautogui.scroll(-15)
    elif action == "CLICK":               pyautogui.click()
    elif action == "RIGHT_CLICK":         pyautogui.rightClick()
    elif action == "DOUBLE_CLICK":        pyautogui.doubleClick()

    elif action == "TYPE":
        pyautogui.typewrite(value, interval=0.05)

    elif action == "PRESS_KEY":
        pyautogui.press(value)

    elif action == "HOTKEY":
        keys = value.split("+")
        pyautogui.hotkey(*keys)

    elif action == "COPY":       pyautogui.hotkey('ctrl', 'c')
    elif action == "PASTE":      pyautogui.hotkey('ctrl', 'v')
    elif action == "UNDO":       pyautogui.hotkey('ctrl', 'z')
    elif action == "REDO":       pyautogui.hotkey('ctrl', 'y')
    elif action == "SELECT_ALL": pyautogui.hotkey('ctrl', 'a')

    elif action == "FIND":
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(0.5)
        pyautogui.typewrite(value, interval=0.05)

    elif action == "NEW_TAB":       pyautogui.hotkey('ctrl', 't')
    elif action == "CLOSE_TAB":     pyautogui.hotkey('ctrl', 'w')
    elif action == "REOPEN_TAB":    pyautogui.hotkey('ctrl', 'shift', 't')
    elif action == "NEXT_TAB":      pyautogui.hotkey('ctrl', 'tab')
    elif action == "PREV_TAB":      pyautogui.hotkey('ctrl', 'shift', 'tab')
    elif action == "REFRESH":       pyautogui.press('f5')
    elif action == "CLOSE_WINDOW":  pyautogui.hotkey('alt', 'f4')
    elif action == "MINIMIZE":      pyautogui.hotkey('win', 'down')
    elif action == "MAXIMIZE":      pyautogui.hotkey('win', 'up')
    elif action == "SWITCH_WINDOW": pyautogui.hotkey('alt', 'tab')
    elif action == "ZOOM_IN":       pyautogui.hotkey('ctrl', '+')
    elif action == "ZOOM_OUT":      pyautogui.hotkey('ctrl', '-')
    elif action == "ZOOM_RESET":    pyautogui.hotkey('ctrl', '0')

    elif action == "BRIGHTNESS_UP":
        try:
            current = sbc.get_brightness()[0]
            sbc.set_brightness(min(100, current + 20))
            speak("Brightness increased!")
        except: speak("Could not change brightness!")

    elif action == "BRIGHTNESS_DOWN":
        try:
            current = sbc.get_brightness()[0]
            sbc.set_brightness(max(0, current - 20))
            speak("Brightness decreased!")
        except: speak("Could not change brightness!")

    elif action == "BRIGHTNESS_SET":
        try:
            sbc.set_brightness(int(value))
            speak(f"Brightness set to {value} percent!")
        except: speak("Could not set brightness!")

    elif action == "CREATE_FOLDER":
        try:
            parts = value.split("/")
            base  = get_path(parts[0]) if len(parts) == 2 else get_path("desktop")
            folder_name = parts[1] if len(parts) == 2 else value
            os.makedirs(os.path.join(base, folder_name), exist_ok=True)
            memory["last_folder"] = folder_name
            memory["last_action"] = f"created folder {folder_name}"
            save_memory("last_folder", folder_name)
            save_memory("last_action", memory["last_action"])
            speak(f"Folder {folder_name} created!")
        except: speak("Could not create folder!")

    elif action == "CREATE_FILE":
        try:
            parts = value.split("/")
            base  = get_path(parts[0]) if len(parts) >= 2 else get_path("desktop")
            file_name = "/".join(parts[1:]) if len(parts) >= 2 else value
            file_path = os.path.join(base, file_name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f: f.write("")
            memory["last_file"]   = file_name
            memory["last_action"] = f"created file {file_name}"
            save_memory("last_file", file_name)
            save_memory("last_action", memory["last_action"])
            speak(f"File {file_name} created!")
        except: speak("Could not create file!")

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
        except: speak("Could not delete. Check the name!")

    elif action == "RENAME":
        try:
            old, new = value.split("|")
            desktop  = get_path("desktop")
            os.rename(os.path.join(desktop, old.strip()), os.path.join(desktop, new.strip()))
            memory["last_file"]   = new.strip()
            memory["last_action"] = f"renamed to {new.strip()}"
            save_memory("last_file", new.strip())
            save_memory("last_action", memory["last_action"])
            speak(f"Renamed to {new.strip()}!")
        except: speak("Could not rename!")

    elif action == "LIST_FILES":
        try:
            path  = get_path(value)
            files = os.listdir(path)
            if files:
                speak(f"Found {len(files)} items in {value}.")
                for f in files[:10]: print(f"  - {f}")
            else:
                speak(f"{value} is empty!")
        except: speak("Could not list files!")

    elif action == "MOVE_FILE":
        try:
            filename, destination = value.split("|")
            shutil.move(os.path.join(get_path("desktop"), filename.strip()), get_path(destination.strip()))
            memory["last_action"] = f"moved {filename} to {destination}"
            save_memory("last_action", memory["last_action"])
            speak(f"Moved {filename.strip()} to {destination.strip()}!")
        except: speak("Could not move file!")

    elif action == "COPY_FILE":
        try:
            filename, destination = value.split("|")
            shutil.copy2(os.path.join(get_path("desktop"), filename.strip()), get_path(destination.strip()))
            memory["last_action"] = f"copied {filename} to {destination}"
            save_memory("last_action", memory["last_action"])
            speak(f"Copied {filename.strip()} to {destination.strip()}!")
        except: speak("Could not copy file!")

    elif action == "OPEN_FILE":
        try:
            file_path = os.path.join(get_path("desktop"), value)
            os.startfile(file_path)
            memory["last_file"] = value
            save_memory("last_file", value)
            speak(f"Opening {value}!")
        except: speak("Could not open file!")

    elif action == "SYSTEM_INFO":
        cpu     = psutil.cpu_percent(interval=1)
        ram     = psutil.virtual_memory()
        disk    = psutil.disk_usage('/')
        battery = psutil.sensors_battery()
        bat_info = f"Battery at {int(battery.percent)}%." if battery else ""
        speak(f"CPU is at {cpu}%. RAM is at {ram.percent}%. Disk is at {disk.percent}%. {bat_info}")

    elif action == "BATTERY_STATUS":
        battery = psutil.sensors_battery()
        if battery:
            status = "charging" if battery.power_plugged else "not charging"
            speak(f"Battery is at {int(battery.percent)}% and is {status}.")
        else: speak("Could not get battery info!")

    elif action == "CPU_USAGE":
        speak(f"CPU usage is {psutil.cpu_percent(interval=1)}%.")

    elif action == "RAM_USAGE":
        ram = psutil.virtual_memory()
        speak(f"RAM usage is {ram.percent}%. {ram.used//(1024**3)}GB used out of {ram.total//(1024**3)}GB.")

    elif action == "DISK_USAGE":
        disk = psutil.disk_usage('/')
        speak(f"Disk usage is {disk.percent}%. {disk.used//(1024**3)}GB used out of {disk.total//(1024**3)}GB.")

    elif action == "WEATHER":
        try:
            city = value.strip() if value else "Delhi"
            r    = requests.get(f"https://wttr.in/{city}?format=3", timeout=5)
            speak(f"Weather: {r.content.decode('utf-8').encode('ascii','ignore').decode('ascii').strip()}")
        except: speak("Could not get weather info!")

    elif action == "WIKIPEDIA":
        try:
            wikipedia.set_lang("en")
            try:
                result = wikipedia.summary(value, sentences=2, auto_suggest=False)
            except wikipedia.exceptions.DisambiguationError as e:
                result = wikipedia.summary(e.options[0], sentences=2, auto_suggest=False)
            speak(result)
        except: speak(f"Could not find info about {value}!")

    elif action == "CALCULATE":
        try:
            speak(f"The answer is {eval(value)}")
        except: speak("Could not calculate that!")

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

    elif action == "TASK_MANAGER":
        subprocess.Popen("taskmgr.exe")
        speak("Opening Task Manager!")

    elif action == "EMPTY_RECYCLE_BIN":
        try:
            subprocess.Popen("cmd /c rd /s /q %systemdrive%\\$Recycle.bin", shell=True)
            speak("Recycle bin emptied!")
        except: speak("Could not empty recycle bin!")

    elif action == "LOCK":     os.system("rundll32.exe user32.dll,LockWorkStation")
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

# ============================================================
#  JARVIS MAIN LOOP — runs in background thread
# ============================================================
def jarvis_loop():
    speak(f"JARVIS online! All systems ready. Say '{WAKE_WORD}' anytime to wake me up, {USER_NAME}!")

    while True:
        wait_for_wake_word()

        speak(random.choice([
            "Yes Boss?",
            "At your service!",
            "How can I help?",
            "Online and ready!",
            "Listening, Boss.",
        ]))
        gui_status("ACTIVE — Ready for command", "#00ff88")

        idle_count = 0
        while True:
            command = listen()

            if not command:
                idle_count += 1
                if idle_count >= 2:
                    speak("Going back to standby. Say 'Hey Jarvis' to wake me!")
                    break
                continue

            idle_count = 0

            if any(w in command for w in ["stop jarvis", "exit", "bye jarvis", "shutdown jarvis", "goodbye jarvis"]):
                speak(f"Goodbye {USER_NAME}! JARVIS shutting down!")
                os._exit(0)

            try:
                response = ask_groq(command)
                print(f"Groq: {response}")
                execute_action(response)
            except Exception as e:
                print(f"Error: {e}")
                speak("Something went wrong, try again!")

# ============================================================
#  ENTRY POINT
# ============================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Dark palette for native widgets
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(10, 14, 26))
    palette.setColor(QPalette.WindowText, QColor(0, 212, 255))
    palette.setColor(QPalette.Base, QColor(5, 8, 16))
    palette.setColor(QPalette.Text, QColor(0, 255, 136))
    app.setPalette(palette)

    gui = JarvisDashboard()

    # Connect bridge signals to GUI slots
    bridge.status_signal.connect(gui.set_status)
    bridge.convo_signal.connect(gui.add_convo)
    bridge.cmd_signal.connect(gui.set_last_command)
    bridge.resp_signal.connect(gui.set_last_response)

    # Start Jarvis in background thread (daemon = exits with app)
    jarvis_thread = threading.Thread(target=jarvis_loop, daemon=True)
    jarvis_thread.start()

    gui.show()
    sys.exit(app.exec_())
