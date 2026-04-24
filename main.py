import sys
import random
import threading

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtCore import QThread, pyqtSignal

from config import WAKE_WORD, USER_NAME
from memory import init_db
from jarvis import speak, listen, wait_for_wake_word, ask_groq, set_gui_bridge, memory
from actions import execute_action


from gui import JarvisDashboard    



class GuiBridge(QThread):
    status_signal = pyqtSignal(str, str)
    convo_signal  = pyqtSignal(str, str)
    cmd_signal    = pyqtSignal(str)
    resp_signal   = pyqtSignal(str)

bridge = GuiBridge()



def jarvis_loop():
    init_db()
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

            if any(w in command for w in [
                "stop jarvis", "exit", "bye jarvis",
                "shutdown jarvis", "goodbye jarvis"
            ]):
                speak(f"Goodbye {USER_NAME}! JARVIS shutting down!")
                import os; os._exit(0)

            try:
                response = ask_groq(command)
                print(f"Groq: {response}")
                execute_action(response, speak, listen, memory)
            except Exception as e:
                print(f"Error: {e}")
                speak("Something went wrong, try again!")



if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Dark palette
    palette = QPalette()
    palette.setColor(QPalette.Window,     QColor(10, 14, 26))
    palette.setColor(QPalette.WindowText, QColor(0, 212, 255))
    palette.setColor(QPalette.Base,       QColor(5, 8, 16))
    palette.setColor(QPalette.Text,       QColor(0, 255, 136))
    app.setPalette(palette)

    gui = JarvisDashboard()

    # Wire bridge signals → GUI slots
    bridge.status_signal.connect(gui.set_status)
    bridge.convo_signal.connect(gui.add_convo)
    bridge.cmd_signal.connect(gui.set_last_command)
    bridge.resp_signal.connect(gui.set_last_response)

    # Tell jarvis.py about the bridge so speak/listen can update GUI
    set_gui_bridge(bridge)

    # Start Jarvis loop in background (daemon = exits with app)
    jarvis_thread = threading.Thread(target=jarvis_loop, daemon=True)
    jarvis_thread.start()

    gui.show()
    sys.exit(app.exec_())