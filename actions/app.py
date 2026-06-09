import os
import subprocess
from config import APP_PATHS
from memory import save_memory, get_memory

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


def open_app(value, speak, listen, memory):
    app_name = value
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
            f'$a=Get-StartApps|Where-Object{{$_.Name -like \\\'*{app_name}*\\\'}}|Select-Object -First 1;'
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
