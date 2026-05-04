import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "legal.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS glossary (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            term    TEXT UNIQUE NOT NULL,
            definition TEXT NOT NULL,
            example TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS cases (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            citation    TEXT NOT NULL,
            facts       TEXT,
            issue       TEXT,
            judgment    TEXT,
            principle   TEXT,
            snippet     TEXT
        );

        CREATE TABLE IF NOT EXISTS statutes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            citation    TEXT NOT NULL,
            description TEXT,
            snippet     TEXT
        );

        CREATE TABLE IF NOT EXISTS chat_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL,
            user_id     TEXT NOT NULL DEFAULT 'anonymous',
            role        TEXT NOT NULL,
            content     TEXT NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Migrate: add user_id column if it was added after initial creation
    try:
        cur.execute("ALTER TABLE chat_history ADD COLUMN user_id TEXT NOT NULL DEFAULT 'anonymous'")
    except Exception:
        pass  # Column already exists

    conn.commit()
    conn.close()
    print("[DB] Tables initialised.")
