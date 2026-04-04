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
            role        TEXT NOT NULL,
            content     TEXT NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()
    print("[DB] Tables initialised.")
