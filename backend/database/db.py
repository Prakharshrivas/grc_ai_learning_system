"""SQLite database initialization and connection management."""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DATABASE_PATH

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS workflows (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    purpose TEXT,
    video_url TEXT,
    video_duration INTEGER,
    roles TEXT,
    status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'approved', 'archived')),
    version INTEGER DEFAULT 1,
    approved_by TEXT,
    approved_at TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS workflow_steps (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    step_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    start_time INTEGER,
    end_time INTEGER,
    navigation TEXT,
    on_screen TEXT,
    action TEXT,
    narration TEXT,
    important_notes TEXT,
    FOREIGN KEY (workflow_id) REFERENCES workflows(id)
);

CREATE TABLE IF NOT EXISTS workflow_faqs (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    related_step INTEGER,
    FOREIGN KEY (workflow_id) REFERENCES workflows(id)
);

CREATE TABLE IF NOT EXISTS interaction_log (
    id TEXT PRIMARY KEY,
    user_id TEXT DEFAULT 'anonymous',
    workflow_id TEXT NOT NULL,
    session_id TEXT,
    user_question TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    cited_steps TEXT,
    video_position INTEGER,
    timestamp TEXT DEFAULT (datetime('now')),
    feedback TEXT CHECK(feedback IN ('helpful', 'not_helpful', NULL)),
    FOREIGN KEY (workflow_id) REFERENCES workflows(id)
);

CREATE TABLE IF NOT EXISTS user_workflow_progress (
    user_id TEXT NOT NULL,
    workflow_id TEXT NOT NULL,
    steps_watched TEXT DEFAULT '[]',
    steps_confirmed TEXT DEFAULT '[]',
    questions_asked INTEGER DEFAULT 0,
    completion_pct REAL DEFAULT 0.0,
    started_at TEXT DEFAULT (datetime('now')),
    completed_at TEXT,
    status TEXT DEFAULT 'not_started' CHECK(status IN ('not_started', 'in_progress', 'completed')),
    PRIMARY KEY (user_id, workflow_id),
    FOREIGN KEY (workflow_id) REFERENCES workflows(id)
);

CREATE INDEX IF NOT EXISTS idx_steps_workflow ON workflow_steps(workflow_id, step_number);
CREATE INDEX IF NOT EXISTS idx_faqs_workflow ON workflow_faqs(workflow_id);
CREATE INDEX IF NOT EXISTS idx_interaction_session ON interaction_log(session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_interaction_workflow ON interaction_log(workflow_id);
CREATE INDEX IF NOT EXISTS idx_progress_user ON user_workflow_progress(user_id);
"""


def get_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DATABASE_PATH), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()
    print(f"Database initialized at: {DATABASE_PATH}")


if __name__ == "__main__":
    init_db()
