import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY  = os.getenv("GROQ_API_KEY")
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASS = os.getenv("GMAIL_APP_PASS")
WAKE_WORD     = "hey jarvis"
USER_NAME     = "Boss"

CONTACTS = {
    "my":    "917404261074",
    "ronit": "919319333635",
}

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

APP_PATHS = {k: os.path.expandvars(v) for k, v in APP_PATHS.items()}