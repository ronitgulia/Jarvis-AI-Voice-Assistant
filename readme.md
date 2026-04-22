# JARVIS — Voice Controlled AI Assistant 

I got tired of using my keyboard and mouse for everything, so I built this.

JARVIS is a fully AI-powered voice assistant that runs on my laptop and controls literally everything through voice commands. No clicking, no typing — just talk.

---

## Why I built this

Started as a fun experiment to see if I could control my laptop hands-free. One feature led to another and before I knew it I had built something that actually replaced my keyboard and mouse for most tasks.

---

## What it does

**System Control**
- Opens any app on my system — automatically finds the path if it doesn't know it
- Controls volume and screen brightness
- Takes screenshots, locks screen, shuts down, restarts, sleeps

**File Management**
- Creates, deletes, moves, renames files and folders just by asking
- Remembers the last file/folder it touched so I can say "delete that" without repeating myself

**Browser & Web**
- Opens websites, searches Google, plays YouTube videos
- Opens new tabs, closes tabs, scrolls, zooms

**Communication**
- Sends emails — I just tell it who to send to, what subject, and dictate the body
- Sends WhatsApp messages to saved contacts

**AI Features**
- Powered by Groq's llama-3.3-70b model for natural language understanding
- No fixed commands — talks naturally and figures out what I mean
- Screen vision — can look at my screen and tell me what's on it
- Can click on things on screen by describing what to click

**Memory**
- Stores everything in SQLite — remembers past conversations, last actions, file paths
- Persists across sessions so it learns over time

**GUI Dashboard**
- Built a PyQt5 dashboard that shows live CPU, RAM, disk and battery stats
- Full conversation log with timestamps
- Shows persistent memory in real time

**Wake Word**
- Say "Hey JARVIS" and it wakes up
- Goes back to standby automatically if I stop talking

---

## Tech stack

- Python
- Groq API — llama-3.3-70b for AI understanding
- SpeechRecognition + PyAudio — voice input
- pyttsx3 — voice output  
- PyAutoGUI — keyboard and mouse automation
- PyQt5 — GUI dashboard
- psutil — system monitoring
- pycaw — volume control
- screen-brightness-control — brightness
- pywhatkit — WhatsApp
- SQLite — permanent memory
- Pillow — screen vision

---

## Setup

```bash
pip install groq SpeechRecognition pyttsx3 pyautogui psutil requests wikipedia screen-brightness-control pycaw pyaudio PyQt5 pywhatkit Pillow
```

Add your Groq API key and Gmail app password in the config section at the top of `assistant.py`, then:

```bash
python assistant.py
```

---

## How it works

Say "Hey JARVIS" → Wake word detected → Listen for command
→ SpeechRecognition converts speech to text
→ Groq AI understands intent and picks the right action
→ Python executes the action on the system
→ JARVIS speaks the response back
→ Everything logged to SQLite memory
---

## Challenges I faced

- Getting smooth voice recognition without lag took a lot of tuning
- The wake word detection needed to run in a loop without blocking everything else
- Threading TTS with PyQt5 GUI was tricky — had to use signal bridges
- Auto finding app paths across different system configurations
- WhatsApp confirmation flow — making sure JARVIS waits for speech before acting

---

## What I learned

- How to integrate large language models into real Python applications
- Threading and async patterns in Python
- PyQt5 for building desktop GUIs
- SQLite for persistent local storage
- Working with system-level APIs — audio, brightness, processes

---

## What's next

- Custom fine-tuned wake word model
- Facial recognition to know who's talking
- Multi-language support
- Mobile app to control laptop remotely

---

*This is part of my ongoing AIML learning journey. Built everything from scratch over a few sessions.*