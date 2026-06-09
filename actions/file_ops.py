import os
import shutil
from memory import save_memory

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

def handle_create_folder(value, speak, listen, memory):
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

def handle_create_file(value, speak, listen, memory):
    try:
        parts     = value.split("/")
        base      = get_path(parts[0]) if len(parts) >= 2 else get_path("desktop")
        file_name = "/".join(parts[1:]) if len(parts) >= 2 else value
        file_path = os.path.join(base, file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w'):
            pass
        memory["last_file"]   = file_name
        memory["last_action"] = f"created file {file_name}"
        save_memory("last_file",   file_name)
        save_memory("last_action", memory["last_action"])
        speak(f"File {file_name} created!")
    except Exception:
        speak("Could not create file!")

def handle_delete(value, speak, listen, memory):
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

def handle_rename(value, speak, listen, memory):
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

def handle_list_files(value, speak, listen, memory):
    try:
        files = os.listdir(get_path(value))
        if files:
            speak(f"Found {len(files)} items in {value}.")
            for f in files[:10]: print(f"  - {f}")
        else:
            speak(f"{value} is empty!")
    except Exception:
        speak("Could not list files!")

def handle_move_file(value, speak, listen, memory):
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

def handle_copy_file(value, speak, listen, memory):
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

def handle_open_file(value, speak, listen, memory):
    try:
        file_path = os.path.join(get_path("desktop"), value)
        os.startfile(file_path)
        memory["last_file"] = value
        save_memory("last_file", value)
        speak(f"Opening {value}!")
    except Exception:
        speak("Could not open file!")
