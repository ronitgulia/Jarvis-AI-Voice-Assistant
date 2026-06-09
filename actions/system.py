import os
import psutil
import pyautogui
import screen_brightness_control as sbc

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

def handle_volume_up(value, speak, listen, memory):
    for _ in range(5): pyautogui.press("volumeup")

def handle_volume_down(value, speak, listen, memory):
    for _ in range(5): pyautogui.press("volumedown")

def handle_volume_set(value, speak, listen, memory):
    set_volume_level(int(value))
    speak(f"Volume set to {value} percent!")

def handle_mute(value, speak, listen, memory):
    pyautogui.press("volumemute")

def handle_brightness_up(value, speak, listen, memory):
    try:
        sbc.set_brightness(min(100, sbc.get_brightness()[0] + 20))
        speak("Brightness increased!")
    except Exception:
        speak("Could not change brightness!")

def handle_brightness_down(value, speak, listen, memory):
    try:
        sbc.set_brightness(max(0, sbc.get_brightness()[0] - 20))
        speak("Brightness decreased!")
    except Exception:
        speak("Could not change brightness!")

def handle_brightness_set(value, speak, listen, memory):
    try:
        sbc.set_brightness(int(value))
        speak(f"Brightness set to {value} percent!")
    except Exception:
        speak("Could not set brightness!")

def handle_system_info(value, speak, listen, memory):
    cpu  = psutil.cpu_percent(interval=1)
    ram  = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    bat  = psutil.sensors_battery()
    bat_info = f"Battery at {int(bat.percent)}%." if bat else ""
    speak(f"CPU {cpu}%. RAM {ram.percent}%. Disk {disk.percent}%. {bat_info}")

def handle_battery_status(value, speak, listen, memory):
    bat = psutil.sensors_battery()
    if bat:
        status = "charging" if bat.power_plugged else "not charging"
        speak(f"Battery is at {int(bat.percent)}% and is {status}.")
    else:
        speak("Could not get battery info!")

def handle_cpu_usage(value, speak, listen, memory):
    speak(f"CPU usage is {psutil.cpu_percent(interval=1)}%.")

def handle_ram_usage(value, speak, listen, memory):
    ram = psutil.virtual_memory()
    speak(f"RAM {ram.percent}%. {ram.used//(1024**3)}GB of {ram.total//(1024**3)}GB used.")

def handle_disk_usage(value, speak, listen, memory):
    disk = psutil.disk_usage('/')
    speak(f"Disk {disk.percent}%. {disk.used//(1024**3)}GB of {disk.total//(1024**3)}GB used.")

def handle_lock(value, speak, listen, memory):
    os.system("rundll32.exe user32.dll,LockWorkStation")

def handle_shutdown(value, speak, listen, memory):
    speak("Shutting down in 5 seconds!")
    os.system("shutdown /s /t 5")

def handle_restart(value, speak, listen, memory):
    speak("Restarting in 5 seconds!")
    os.system("shutdown /r /t 5")

def handle_sleep(value, speak, listen, memory):
    speak("Going to sleep!")
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

def handle_hibernate(value, speak, listen, memory):
    speak("Hibernating!")
    os.system("shutdown /h")
