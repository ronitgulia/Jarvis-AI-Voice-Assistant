import re
import io
import base64
import smtplib
import time
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import pyautogui
from PIL import Image
from groq import Groq

from config import GROQ_API_KEY, GMAIL_ADDRESS, GMAIL_APP_PASS, CONTACTS
from memory import save_memory

client = Groq(api_key=GROQ_API_KEY)

# Confirm words used in both email & whatsapp flows
CONFIRM_WORDS = [
    "yes", "send", "haan", "ha", "han", "haa", "confirm",
    "do it", "sure", "ok", "okay", "bilkul", "kar do", "bhej do", "karo"
]


# ── Screen Vision ────────────────────────────────────────────

def get_screen_description(user_question="What is on the screen?"):
    try:
        screenshot = pyautogui.screenshot()
        if screenshot.width > 1280:
            ratio      = 1280 / screenshot.width
            screenshot = screenshot.resize(
                (1280, int(screenshot.height * ratio)), Image.LANCZOS
            )
        buf     = io.BytesIO()
        screenshot.save(buf, format="JPEG", quality=75)
        img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        resp = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                    {"type": "text",
                     "text": f"You are JARVIS analyzing a screen. {user_question} Be concise (2-3 sentences)."},
                ],
            }],
            max_tokens=300,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"Screen analysis failed: {e}"


def find_and_click_on_screen(target_description, speak_fn):
    try:
        screenshot = pyautogui.screenshot()
        sw, sh     = screenshot.size
        buf        = io.BytesIO()
        screenshot.save(buf, format="JPEG", quality=75)
        img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        prompt = (
            f"Screen resolution is {sw}x{sh}. "
            f"Find '{target_description}' on screen. "
            f"Reply ONLY with: X,Y (integer pixel coordinates of its center). "
            f"If not found reply: NOT_FOUND"
        )
        resp = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                    {"type": "text", "text": prompt},
                ],
            }],
            max_tokens=20,
        )
        coords_text = resp.choices[0].message.content.strip()
        if "NOT_FOUND" in coords_text.upper():
            speak_fn(f"I could not find {target_description} on screen.")
            return False

        coords = re.findall(r'\d+', coords_text)
        if len(coords) >= 2:
            x, y = int(coords[0]), int(coords[1])
            pyautogui.moveTo(x, y, duration=0.4)
            pyautogui.click()
            speak_fn(f"Clicked on {target_description}!")
            return True
        speak_fn("Could not determine coordinates.")
        return False
    except Exception as e:
        speak_fn(f"Screen click failed: {e}")
        return False


# ── Email ────────────────────────────────────────────────────

def send_email(to_address, subject, body, speak_fn, memory):
    try:
        msg            = MIMEMultipart()
        msg['From']    = GMAIL_ADDRESS
        msg['To']      = to_address
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
            server.sendmail(GMAIL_ADDRESS, to_address, msg.as_string())
        speak_fn(f"Email sent to {to_address}!")
        memory["last_action"] = f"sent email to {to_address}"
        save_memory("last_action", memory["last_action"])
    except Exception as e:
        speak_fn(f"Email failed: {e}")


def compose_email_flow(speak_fn, listen_fn, memory):
    speak_fn("Sure! Who should I send the email to? Say their email address or name.")
    recipient = listen_fn()
    if not recipient:
        speak_fn("Didn't catch the recipient. Cancelling.")
        return

    speak_fn(f"Got it — {recipient}. What's the subject?")
    subject = listen_fn() or "No Subject"

    speak_fn("Now tell me the message body.")
    body = listen_fn(timeout=15, phrase_limit=30)
    if not body:
        speak_fn("No message body heard. Cancelling.")
        return

    speak_fn(f"Ready to send email to {recipient} with subject '{subject}'. Say yes to confirm.")
    time.sleep(0.8)
    confirm = listen_fn(timeout=10)
    print(f"DEBUG confirm heard: '{confirm}'")

    if any(w in confirm for w in CONFIRM_WORDS):
        clean_email = (recipient
                       .replace(" at the rate ", "@").replace(" at ", "@")
                       .replace(" dot ", ".").replace(" ", "").lower())
        send_email(clean_email, subject, body, speak_fn, memory)
    else:
        speak_fn(f"Email cancelled. I heard: '{confirm or 'nothing'}'")


# ── WhatsApp ─────────────────────────────────────────────────

def send_whatsapp(phone_or_name, message, speak_fn, memory, wait_time=15):
    try:
        import pywhatkit as kit
        from datetime import datetime as dt

        phone = phone_or_name.strip()
        for name, num in CONTACTS.items():
            if name.lower() in phone.lower():
                phone = num
                break

        if not phone.startswith("+"):
            if not phone.startswith("91"):
                phone = "91" + phone
            phone = "+" + phone

        now         = dt.now()
        send_hour   = now.hour
        send_minute = now.minute + 2
        if send_minute >= 60:
            send_minute -= 60
            send_hour = (send_hour + 1) % 24

        kit.sendwhatmsg(phone, message, send_hour, send_minute,
                        wait_time=wait_time, tab_close=True, close_time=5)
        speak_fn(f"WhatsApp message scheduled for {phone}!")
        memory["last_action"] = f"sent WhatsApp to {phone}"
        save_memory("last_action", memory["last_action"])
    except Exception as e:
        speak_fn(f"WhatsApp failed: {e}")


def compose_whatsapp_flow(speak_fn, listen_fn, memory):
    speak_fn("Sure! Who should I WhatsApp? Say their name or number.")
    contact = listen_fn()
    if not contact:
        speak_fn("Didn't catch the contact. Cancelling.")
        return

    speak_fn(f"Got it — {contact}. What's the message?")
    message = listen_fn(timeout=15, phrase_limit=30)
    if not message:
        speak_fn("No message heard. Cancelling.")
        return

    speak_fn(f"Sending WhatsApp to {contact}: '{message}'. Say yes to confirm.")
    time.sleep(0.8)
    confirm = listen_fn(timeout=10)
    print(f"DEBUG confirm heard: '{confirm}'")

    if any(w in confirm for w in CONFIRM_WORDS):
        digits_only = re.sub(r'\D', '', contact)
        resolved    = digits_only if len(digits_only) >= 10 else contact
        send_whatsapp(resolved, message, speak_fn, memory)
    else:
        speak_fn(f"Confirm nahi hua, WhatsApp cancelled. I heard: {confirm or 'nothing'}")