import ast
import operator
import random
import requests
import subprocess
import wikipedia
from datetime import datetime

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


def handle_weather(value, speak, listen, memory):
    try:
        city = value.strip() if value else "Delhi"
        r    = requests.get(f"https://wttr.in/{city}?format=3", timeout=5)
        speak(f"Weather: {r.content.decode('utf-8').encode('ascii','ignore').decode('ascii').strip()}")
    except Exception:
        speak("Could not get weather info!")

def handle_wikipedia(value, speak, listen, memory):
    try:
        wikipedia.set_lang("en")
        try:
            result = wikipedia.summary(value, sentences=2, auto_suggest=False)
        except wikipedia.exceptions.DisambiguationError as e:
            result = wikipedia.summary(e.options[0], sentences=2, auto_suggest=False)
        speak(result)
    except Exception:
        speak(f"Could not find info about {value}!")

def handle_calculate(value, speak, listen, memory):
    try:
        result = _safe_eval(value)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        speak(f"The answer is {result}")
    except Exception as e:
        speak(f"Could not calculate that. {e}")

def handle_time(value, speak, listen, memory):
    speak(f"Current time is {datetime.now().strftime('%I:%M %p')}")

def handle_date(value, speak, listen, memory):
    speak(f"Today is {datetime.now().strftime('%B %d, %Y')}")

def handle_joke(value, speak, listen, memory):
    jokes = [
        "Why do programmers prefer dark mode? Because light attracts bugs!",
        "Why did the computer go to the doctor? Because it had a virus!",
        "What do you call a computer that sings? A Dell!",
        "Why was the JavaScript developer sad? Because he didn't know how to null his feelings!",
        "How many programmers does it take to change a light bulb? None, that is a hardware problem!",
    ]
    speak(random.choice(jokes))

def handle_task_manager(value, speak, listen, memory):
    subprocess.Popen("taskmgr.exe")
    speak("Opening Task Manager!")

def handle_empty_recycle_bin(value, speak, listen, memory):
    try:
        subprocess.run(
            'powershell -NoProfile -Command "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"',
            shell=True, timeout=15
        )
        speak("Recycle bin emptied!")
    except Exception:
        speak("Could not empty recycle bin!")
