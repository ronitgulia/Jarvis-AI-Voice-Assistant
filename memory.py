import sqlite3
import os
from datetime import datetime


DB_PATH = os.path.join(os.path.expanduser("~"), "jarvis_memory.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Key-value store — preferences & last actions
    c.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            key        TEXT PRIMARY KEY,
            value      TEXT,
            updated_at TEXT
        )
    """)

    # Full conversation history (permanent)
    c.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            role       TEXT,
            content    TEXT,
            created_at TEXT
        )
    """)

    # Command log
    c.execute("""
        CREATE TABLE IF NOT EXISTS command_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            command    TEXT,
            response   TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_memory(key, value):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO memory (key, value, updated_at) VALUES (?, ?, ?)",
        (key, str(value), datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_memory(key, default=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        result = conn.execute(
            "SELECT value FROM memory WHERE key=?", (key,)
        ).fetchone()
        conn.close()
        return result[0] if result else default
    except Exception:
        return default


def get_all_memory(limit=8):
    """Returns last `limit` memory rows for GUI display."""
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute(
            "SELECT key, value, updated_at FROM memory ORDER BY updated_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        conn.close()
        return rows
    except Exception:
        return []


def save_conversation_to_db(role, content):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO conversations (role, content, created_at) VALUES (?, ?, ?)",
        (role, content, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_last_n_conversations(n=10):
    """Load last N conversations from DB for AI context."""
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute(
            "SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?", (n,)
        ).fetchall()
        conn.close()
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]
    except Exception:
        return []


def log_command(command, response):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO command_log (command, response, created_at) VALUES (?, ?, ?)",
        (command, response, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_recent_commands(n=5):
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute(
            "SELECT command, created_at FROM command_log ORDER BY id DESC LIMIT ?", (n,)
        ).fetchall()
        conn.close()
        return rows
    except Exception:
        return []