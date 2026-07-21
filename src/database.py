import sqlite3
import os
import json
from datetime import datetime, timezone

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "saved_jobs.db"))


def _get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS saved_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT,
            salary TEXT,
            modality TEXT,
            location TEXT,
            country TEXT,
            description_short TEXT,
            english_level TEXT,
            url TEXT,
            source TEXT,
            created_at TEXT NOT NULL,
            saved_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_job(job: dict) -> bool:
    init_db()
    url = (job.get("url") or "").strip()
    title = (job.get("title") or "").strip()
    conn = _get_conn()
    if url:
        existing = conn.execute("SELECT id FROM saved_jobs WHERE url = ?", (url,)).fetchone()
        if existing:
            conn.close()
            return False
    elif title:
        existing = conn.execute("SELECT id FROM saved_jobs WHERE title = ? AND COALESCE(url,'') = ''", (title,)).fetchone()
        if existing:
            conn.close()
            return False
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("""
        INSERT INTO saved_jobs
            (title, company, salary, modality, location, country,
             description_short, english_level, url, source, created_at, saved_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        title,
        job.get("company") or "",
        job.get("salary") or "",
        job.get("modality") or "",
        job.get("location") or "",
        job.get("country") or "Colombia",
        job.get("description_short") or "",
        job.get("english_level") or "",
        url,
        job.get("source") or "",
        job.get("created_at") or now,
        now,
    ))
    conn.commit()
    conn.close()
    return True


def unsave_job(url: str) -> bool:
    init_db()
    conn = _get_conn()
    cur = conn.execute("DELETE FROM saved_jobs WHERE url = ?", (url,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted


def get_saved_jobs() -> list[dict]:
    init_db()
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM saved_jobs ORDER BY saved_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def is_saved(url: str) -> bool:
    if not url:
        return False
    init_db()
    conn = _get_conn()
    row = conn.execute("SELECT id FROM saved_jobs WHERE url = ?", (url,)).fetchone()
    conn.close()
    return row is not None


def count_saved() -> int:
    init_db()
    conn = _get_conn()
    row = conn.execute("SELECT COUNT(*) as c FROM saved_jobs").fetchone()
    conn.close()
    return row["c"] if row else 0