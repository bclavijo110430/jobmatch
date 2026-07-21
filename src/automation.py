import os
import requests
import threading
import time
from datetime import datetime, timezone

from src.job_sources import get_jobs
from src.formatter import format_jobs
from src.filters import filter_by_cv_relevance, filter_by_country, filter_by_modality
from src.english import enrich_offers_with_english
from src import database

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def _ensure_notified_table():
    conn = database._get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notified_jobs (
            url TEXT PRIMARY KEY,
            notified_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def _already_notified(url: str) -> bool:
    if not url:
        return False
    _ensure_notified_table()
    conn = database._get_conn()
    row = conn.execute("SELECT url FROM notified_jobs WHERE url = ?", (url,)).fetchone()
    conn.close()
    return row is not None


def _mark_notified(url: str):
    if not url:
        return
    _ensure_notified_table()
    conn = database._get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO notified_jobs (url, notified_at) VALUES (?, ?)",
        (url, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


# ====================== Telegram ======================
def send_telegram(text: str) -> bool:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
            },
            timeout=15,
        )
        return resp.status_code == 200
    except Exception:
        return False


def _format_job_telegram(job: dict) -> str:
    title = (job.get("title") or "Sin título").replace("<", "&lt;")
    company = (job.get("company") or "?").replace("<", "&lt;")
    salary = job.get("salary") or "No disponible"
    modality = job.get("modality") or "N/A"
    location = job.get("location") or "N/A"
    url = job.get("url") or ""
    eng = job.get("english_level") or "Ninguno"
    desc = (job.get("description_short") or "Sin descripción")[:200]

    lines = [
        f"🔔 <b>{title}</b>",
        f"🏢 {company} · 📍 {location}",
        f"💰 {salary} · 🏠 {modality} · 🗣 {eng}",
        f"📝 {desc}",
    ]
    if url:
        lines.append(f"🔗 <a href=\"{url}\">Ver oferta original</a>")
    return "\n".join(lines)


# ====================== Automation ======================
_automation_thread = None
_automation_stop = threading.Event()


def _search_and_notify(profile: dict, keyword: str = "", modality: str = ""):
    terms = list(profile.get("target_titles", [])) + list(profile.get("search_keywords", []))
    for kw in (keyword or "").split(","):
        kw = kw.strip()
        if kw:
            terms.append(kw)
    if not terms:
        return 0

    all_raw = []
    for t in terms[:5]:
        try:
            raw = get_jobs(t)
            seen = {j.get("url", "") for j in all_raw if j.get("url")}
            for j in raw:
                if j.get("url", "") not in seen:
                    all_raw.append(j)
        except Exception:
            pass

    relevant, _ = filter_by_cv_relevance(all_raw, profile)
    if not relevant:
        return 0

    formatted = format_jobs(relevant[:10])
    formatted = enrich_offers_with_english(formatted)
    formatted = filter_by_country(formatted, "Colombia")
    if modality:
        formatted = filter_by_modality(formatted, modality)

    new_count = 0
    for j in formatted:
        url = j.get("url", "")
        if url and not _already_notified(url):
            if send_telegram(_format_job_telegram(j)):
                _mark_notified(url)
                new_count += 1
            time.sleep(1)

    return new_count


def _automation_loop(profile: dict, keyword: str, interval_minutes: int, log_callback, modality: str = ""):
    interval_secs = max(interval_minutes, 1) * 60
    while not _automation_stop.is_set():
        dt = datetime.now().strftime("%H:%M")
        log_callback(f"[{dt}] Buscando...")
        try:
            count = _search_and_notify(profile, keyword, modality)
            if count:
                log_callback(f"[{dt}] {count} ofertas nuevas enviadas por Telegram")
            else:
                log_callback(f"[{dt}] Sin ofertas nuevas")
        except Exception as e:
            log_callback(f"[{dt}] Error: {e}")
        next_run = time.time() + interval_secs
        while time.time() < next_run and not _automation_stop.is_set():
            time.sleep(5)


def start_automation(profile: dict, keyword: str = "", interval_minutes: int = 30,
                     log_callback=None, notifications_enabled: bool = True,
                     telegram_token: str = "", telegram_chat_id: str = "",
                     modality: str = "") -> str | None:
    global _automation_thread, _automation_stop, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

    if _automation_thread and _automation_thread.is_alive():
        return "La automatización ya está corriendo."

    if notifications_enabled:
        TELEGRAM_TOKEN = telegram_token or TELEGRAM_TOKEN or os.getenv("TELEGRAM_BOT_TOKEN", "")
        TELEGRAM_CHAT_ID = telegram_chat_id or TELEGRAM_CHAT_ID or os.getenv("TELEGRAM_CHAT_ID", "")
        if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
            return "Falta token o chat ID de Telegram."

    _automation_stop.clear()
    _automation_thread = threading.Thread(
        target=_automation_loop,
        args=(profile, keyword, max(interval_minutes, 5), log_callback or print, modality),
        daemon=True,
    )
    _automation_thread.start()
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        try:
            send_telegram(f"🚀 JobMatch: automatización iniciada. Buscando cada {interval_minutes} minutos.")
        except Exception:
            pass
    return None


def stop_automation() -> bool:
    global _automation_thread, _automation_stop
    _automation_stop.set()
    if _automation_thread and _automation_thread.is_alive():
        _automation_thread.join(timeout=3)
    _automation_thread = None
    return True


def is_automation_running() -> bool:
    return _automation_thread is not None and _automation_thread.is_alive()


def get_automation_status() -> str:
    if not is_automation_running():
        return "detenida"
    return "corriendo"


def test_telegram(token: str, chat_id: str) -> bool:
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": "✅ JobMatch: notificación de prueba exitosa"},
            timeout=10,
        )
        return resp.status_code == 200
    except Exception:
        return False