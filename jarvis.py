import speech_recognition as sr
import pyttsx3
import threading
import queue
import time
from collections import deque
from datetime import datetime
from groq import Groq

from config import GROQ_API_KEY, WAKE_WORD, USER_NAME
from memory import (
    get_memory, save_memory, save_conversation_to_db,
    get_last_n_conversations, log_command
)

# NOTE: compose_email_flow, compose_whatsapp_flow, get_screen_description,
# and find_and_click_on_screen have been moved to utils.py to break the
# circular import that existed between jarvis.py and actions.py.

client = Groq(api_key=GROQ_API_KEY)

# ── TTS — Queue-based so speaks never overlap ─────────────────
engine = pyttsx3.init()
engine.setProperty('rate', 170)
engine.setProperty('volume', 1.0)
_tts_queue = queue.Queue()

def _tts_worker():
    """Background thread: drains the TTS queue one utterance at a time."""
    while True:
        text = _tts_queue.get()
        if text is None:
            break
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"TTS error: {e}")
        finally:
            _tts_queue.task_done()

_tts_thread = threading.Thread(target=_tts_worker, daemon=True)
_tts_thread.start()

# ── Memory ────────────────────────────────────────────────────
memory = {
    "last_file":   get_memory("last_file"),
    "last_folder": get_memory("last_folder"),
    "last_action": get_memory("last_action"),
    "user_name":   get_memory("user_name", USER_NAME),
}

conversation_history = deque(get_last_n_conversations(10), maxlen=20)

# ── GUI Bridge ────────────────────────────────────────────────
_gui_bridge = None

def set_gui_bridge(bridge):
    global _gui_bridge
    _gui_bridge = bridge

def _gui_status(text, color="#00ff88"):
    if _gui_bridge:
        _gui_bridge.status_signal.emit(text, color)

def _gui_convo(role, text):
    if _gui_bridge:
        _gui_bridge.convo_signal.emit(role, text)

def _gui_cmd(text):
    if _gui_bridge:
        _gui_bridge.cmd_signal.emit(text)

def _gui_resp(text):
    if _gui_bridge:
        _gui_bridge.resp_signal.emit(text)


# ── Speak ─────────────────────────────────────────────────────
def speak(text):
    """Queue text for TTS — returns immediately, never blocks GUI thread."""
    print(f"JARVIS: {text}")
    _gui_resp(text)
    _gui_convo("jarvis", text)
    _tts_queue.put(text)


# ── Listen ────────────────────────────────────────────────────
def listen(timeout=8, phrase_limit=12):
    r = sr.Recognizer()
    r.energy_threshold                  = 150
    r.dynamic_energy_threshold          = True
    r.dynamic_energy_adjustment_damping = 0.10
    r.pause_threshold                   = 0.6
    r.phrase_threshold                  = 0.2

    _gui_status("LISTENING...", "#ffaa00")
    with sr.Microphone() as source:
        print("\n Listening...")
        r.adjust_for_ambient_noise(source, duration=1.0)
        try:
            audio   = r.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
            command = r.recognize_google(audio).lower()
            print(f"You said: {command}")
            _gui_convo("user", command)
            _gui_cmd(command)
            _gui_status("PROCESSING...", "#00aaff")
            return command
        except sr.UnknownValueError:
            _gui_status("ACTIVE — Ready", "#00ff88")
            return ""
        except sr.WaitTimeoutError:
            _gui_status("STANDBY — Waiting for wake word", "#00d4ff")
            return ""
        except sr.RequestError:
            speak("Internet connection needed!")
            return ""


# ── Wake Word ─────────────────────────────────────────────────
def wait_for_wake_word():
    r = sr.Recognizer()
    r.energy_threshold         = 250
    r.dynamic_energy_threshold = True
    print(f"\n Waiting for wake word: '{WAKE_WORD}' ...")
    _gui_status("STANDBY — Say 'Hey Jarvis'", "#00d4ff60")

    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=1.0)
        while True:
            try:
                audio = r.listen(source, timeout=3, phrase_time_limit=4)
                text  = r.recognize_google(audio).lower()
                if WAKE_WORD in text:
                    print(" Wake word detected!")
                    _gui_status("WAKE WORD DETECTED!", "#00ff88")
                    return True
            except Exception:
                pass


# ── Groq AI ───────────────────────────────────────────────────
def ask_groq(user_input):
    memory_context = f"""
    Last file:   {memory['last_file']   or 'none'}
    Last folder: {memory['last_folder'] or 'none'}
    Last action: {memory['last_action'] or 'none'}
    User name:   {memory['user_name']}
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
    - "that file" = last_file from memory, "that folder" = last_folder from memory
    - Max 2 sentence reply, be witty and smart like JARVIS!
    - Never say you can't do something, always try
    - For email/whatsapp use [SEND_EMAIL] or [SEND_WHATSAPP]
    - For "what's on screen" use [SCREEN_DESCRIBE:question]
    - For "click on X" use [SCREEN_CLICK:X]
    - For play/music/song ALWAYS use [YOUTUBE:song name]
    - EVERY command must end with ONE action tag"""

    conversation_history.append({
        "role": "user",
        "content": f"Memory:\n{memory_context}\nUser: {user_input}"
    })
    save_conversation_to_db("user", user_input)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            *list(conversation_history)
        ],
        max_tokens=250
    )

    reply = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": reply})
    save_conversation_to_db("assistant", reply)
    log_command(user_input, reply)
    return reply