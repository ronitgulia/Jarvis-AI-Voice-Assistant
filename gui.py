import sqlite3
import psutil
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QFrame, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from memory import DB_PATH


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

    # ── HELPERS ──────────────────────────────────────────────

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

    # ── TIMER CALLBACKS ───────────────────────────────────────

    def _update_clock(self):
        self.time_label.setText(datetime.now().strftime("%d %b %Y  |  %H:%M:%S"))

    def _update_stats(self):
        cpu  = psutil.cpu_percent(interval=None)
        ram  = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent

        self.cpu_bar[0].setValue(int(cpu));  self.cpu_bar[1].setText(f"{int(cpu)}%")
        self.ram_bar[0].setValue(int(ram));  self.ram_bar[1].setText(f"{int(ram)}%")
        self.disk_bar[0].setValue(int(disk)); self.disk_bar[1].setText(f"{int(disk)}%")

        bat = psutil.sensors_battery()
        if bat:
            plug = " Charging" if bat.power_plugged else ""
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

    # ── PUBLIC SLOTS (called via Qt signals from bg thread) ───

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