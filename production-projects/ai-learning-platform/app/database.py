# app/database.py
import sqlite3, os

DB_PATH = os.environ.get("DB_PATH", "./data/learnai.db")


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS courses (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            topic TEXT NOT NULL,
            description TEXT,
            lesson_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS lessons (
            id TEXT PRIMARY KEY,
            course_id TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            order_index INTEGER NOT NULL,
            FOREIGN KEY (course_id) REFERENCES courses(id)
        );
        CREATE TABLE IF NOT EXISTS quizzes (
            id TEXT PRIMARY KEY,
            lesson_id TEXT NOT NULL,
            question TEXT NOT NULL,
            options TEXT,
            correct_answer TEXT,
            difficulty TEXT DEFAULT 'medium',
            FOREIGN KEY (lesson_id) REFERENCES lessons(id)
        );
        CREATE TABLE IF NOT EXISTS progress (
            user_id TEXT NOT NULL,
            lesson_id TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            score REAL DEFAULT 0,
            attempts INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, lesson_id)
        );
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()
