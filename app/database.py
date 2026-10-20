"""Connection lifecycle and schema. A connection is never shared across requests."""
import sqlite3
from contextlib import contextmanager


@contextmanager
def connect(path):
    connection = sqlite3.connect(path, timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA foreign_keys = ON')
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize(path):
    with connect(path) as db:
        db.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL CHECK(length(trim(title)) BETWEEN 1 AND 200),
                description TEXT NOT NULL CHECK(length(trim(description)) BETWEEN 1 AND 10000),
                status TEXT NOT NULL CHECK(status IN ('Open','In Progress','Resolved','Closed')),
                priority TEXT NOT NULL CHECK(priority IN ('Low','Medium','High','Critical')),
                assignee_id INTEGER NOT NULL REFERENCES users(id),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS issues_status_id ON issues(status, id);
        ''')
        db.executemany('INSERT OR IGNORE INTO users(id, name) VALUES (?, ?)',
                       [(1, 'Alzayed Alhassan'), (2, 'Alex Morgan'), (3, 'Sam Taylor')])
