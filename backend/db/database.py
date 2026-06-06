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

        CREATE TABLE IF NOT EXISTS user_profiles (
            uid              TEXT PRIMARY KEY,
            email            TEXT NOT NULL DEFAULT '',
            name             TEXT NOT NULL DEFAULT '',
            picture          TEXT NOT NULL DEFAULT '',
            level            TEXT NOT NULL DEFAULT 'beginner',
            institution      TEXT NOT NULL DEFAULT '',
            year_of_study    TEXT NOT NULL DEFAULT '',
            areas_of_interest TEXT NOT NULL DEFAULT '[]',
            created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS feedback (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         TEXT NOT NULL DEFAULT 'anonymous',
            message_id      TEXT,
            session_id      TEXT,
            feedback_type   TEXT NOT NULL,
            comment         TEXT NOT NULL DEFAULT '',
            query           TEXT NOT NULL DEFAULT '',
            response        TEXT NOT NULL DEFAULT '',
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS shared_chats (
            share_id    TEXT PRIMARY KEY,
            user_id     TEXT NOT NULL DEFAULT 'anonymous',
            title       TEXT NOT NULL DEFAULT '',
            messages    TEXT NOT NULL DEFAULT '[]',
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
