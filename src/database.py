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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS discovered_jobs (
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
            created_at TEXT,
            detected_at TEXT NOT NULL,
            match_keywords TEXT,
            UNIQUE(url)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_state (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# ====================== Saved jobs (user favorites) ======================
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


# ====================== Discovered jobs (auto-detected) ======================
def save_discovered_job(job: dict, match_keywords: str = "") -> bool:
    init_db()
    url = (job.get("url") or "").strip()
    title = (job.get("title") or "").strip()
    if not title and not url:
        return False
    conn = _get_conn()
    if url:
        existing = conn.execute("SELECT id FROM discovered_jobs WHERE url = ?", (url,)).fetchone()
        if existing:
            conn.close()
            return False
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("""
        INSERT OR IGNORE INTO discovered_jobs
            (title, company, salary, modality, location, country,
             description_short, english_level, url, source, created_at,
             detected_at, match_keywords)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        job.get("created_at") or "",
        now,
        match_keywords,
    ))
    conn.commit()
    conn.close()
    return True


def get_discovered_jobs(limit: int | None = None) -> list[dict]:
    init_db()
    conn = _get_conn()
    q = "SELECT * FROM discovered_jobs ORDER BY detected_at DESC"
    if limit:
        q += f" LIMIT {int(limit)}"
    rows = conn.execute(q).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def count_discovered() -> int:
    init_db()
    conn = _get_conn()
    row = conn.execute("SELECT COUNT(*) as c FROM discovered_jobs").fetchone()
    conn.close()
    return row["c"] if row else 0


def clear_discovered_jobs() -> int:
    init_db()
    conn = _get_conn()
    cur = conn.execute("DELETE FROM discovered_jobs")
    conn.commit()
    deleted = cur.rowcount
    conn.close()
    return deleted


def delete_discovered_job(discovered_id: int) -> bool:
    init_db()
    conn = _get_conn()
    cur = conn.execute("DELETE FROM discovered_jobs WHERE id = ?", (discovered_id,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted


# ====================== Generic app state (KV) ======================
def save_app_state(key: str, value):
    init_db()
    v = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    conn = _get_conn()
    conn.execute("""
        INSERT INTO app_state (key, value, updated_at) VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
    """, (key, v, datetime.now(timezone.utc).isoformat()))
    conn.commit()
    conn.close()


def load_app_state(key: str, default=None):
    init_db()
    conn = _get_conn()
    row = conn.execute("SELECT value FROM app_state WHERE key = ?", (key,)).fetchone()
    conn.close()
    if row is None:
        return default
    raw = row["value"]
    if raw is None:
        return default
    if raw.startswith(("{", "[")):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
    return raw


def load_all_app_state() -> dict:
    init_db()
    conn = _get_conn()
    rows = conn.execute("SELECT key, value FROM app_state").fetchall()
    conn.close()
    out = {}
    for r in rows:
        raw = r["value"]
        if raw is not None and raw.startswith(("{", "[")):
            try:
                out[r["key"]] = json.loads(raw)
                continue
            except json.JSONDecodeError:
                pass
        out[r["key"]] = raw
    return out


def delete_app_state(key: str) -> bool:
    init_db()
    conn = _get_conn()
    cur = conn.execute("DELETE FROM app_state WHERE key = ?", (key,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted