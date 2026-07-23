from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Any, Optional
import os
import sys
import datetime

# Ensure src/ is importable when running from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cv_parser import extract_text
from src.cv_analyzer import analyze_cv
from src.english import estimate_candidate_level, enrich_offers_with_english
from src.job_sources import get_jobs
from src.formatter import format_jobs
from src.filters import (
    filter_by_country,
    filter_by_modality,
    filter_by_keyword,
    filter_by_location,
    filter_by_salary_min,
    filter_by_english_level,
    filter_by_companies,
    filter_by_experience,
    add_match_flag,
    filter_by_cv_relevance,
)
from src.llm import configure, get_available_backends, get_current_backend, get_provider_info
from src.database import (
    save_job,
    unsave_job,
    get_saved_jobs,
    delete_app_state,
    load_all_app_state,
    save_app_state,
    get_discovered_jobs,
    clear_discovered_jobs,
    delete_discovered_job,
    save_discovered_job,
)
from src import automation
from src.interview import start_interview, continue_interview


app = FastAPI(
    title="JobMatch API",
    description="Backend API for the JobMatch Astro UI",
    version="1.0.0",
)

# CORS — allow the Astro dev server and any production origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ======================== Pydantic models ========================

class LLMConfigureRequest(BaseModel):
    backend: str


class SearchRequest(BaseModel):
    keyword: str = ""
    modality: Optional[str] = None
    location: Optional[list[str]] = None
    english_levels: Optional[list[str]] = None
    companies: Optional[list[str]] = None
    min_salary: float = 0
    max_experience: Optional[int] = None
    keyword_filter: str = ""


class JobPayload(BaseModel):
    job: dict[str, Any]


class InterviewStartRequest(BaseModel):
    job: dict[str, Any]


class InterviewContinueRequest(BaseModel):
    job: dict[str, Any]
    history: list[dict[str, Any]]


class AutomationStartRequest(BaseModel):
    telegram_token: str
    telegram_chat_id: str
    interval_minutes: int = Field(30, ge=1)
    keyword: str = ""
    modality: Optional[str] = None


class TestTelegramRequest(BaseModel):
    telegram_token: str
    telegram_chat_id: str


# ======================== Helpers ========================

def _load_profile() -> dict:
    persisted = load_all_app_state()
    profile = persisted.get("cv_profile")
    if isinstance(profile, dict):
        return profile
    return {}


def _load_cv_text() -> str:
    persisted = load_all_app_state()
    cv_text = persisted.get("cv_text", "")
    return cv_text if isinstance(cv_text, str) else ""


def _log_callback(msg: str):
    persisted = load_all_app_state()
    logs = persisted.get("auto_logs", [])
    if not isinstance(logs, list):
        logs = []
    logs.append(msg)
    logs = logs[-50:]
    save_app_state("auto_logs", logs)


def _save_auto_config(interval: int, keyword: str):
    save_app_state("auto_interval", interval)
    save_app_state("auto_keyword", keyword)


def _run_search(manual_kw: str = "", profile: Optional[dict] = None) -> list[dict]:
    if profile is None:
        profile = _load_profile()

    titles = list(profile.get("target_titles", []))
    keywords = list(profile.get("search_keywords", []))
    terms = titles + keywords
    if manual_kw.strip():
        terms.insert(0, manual_kw.strip())
    if not terms:
        terms = [manual_kw.strip()] if manual_kw.strip() else [""]

    all_raw = []
    for term in terms[:5]:
        try:
            raw = get_jobs(term)
            seen = {j.get("url", "") for j in all_raw if j.get("url")}
            for j in raw:
                if j.get("url", "") not in seen:
                    all_raw.append(j)
                    seen.add(j.get("url", ""))
        except Exception:
            continue

    if not all_raw:
        return []

    relevant_raw, other_raw = filter_by_cv_relevance(all_raw, profile)
    formatted_relevant = format_jobs(relevant_raw) if relevant_raw else []
    formatted_relevant = enrich_offers_with_english(formatted_relevant)
    formatted_relevant = filter_by_country(formatted_relevant, "Colombia")

    candidate_level = load_all_app_state().get("candidate_level")
    formatted_relevant = add_match_flag(formatted_relevant, candidate_level)

    others = []
    for j in other_raw:
        others.append({
            "title": j.get("title", "Sin título"),
            "url": j.get("url", ""),
            "company": "No disponible",
            "salary": "No disponible",
            "modality": "No especificado",
            "location": "Colombia",
            "country": "Colombia",
            "description_short": j.get("raw_text", "")[:150],
            "english_level": "Ninguno",
            "source": j.get("source", ""),
            "created_at": j.get("created_at", ""),
            "english_match": True,
        })
    others = filter_by_country(others, "Colombia")

    all_formatted = formatted_relevant + others
    return all_formatted


def _apply_filters(jobs: list[dict], req: SearchRequest) -> list[dict]:
    filtered = filter_by_keyword(jobs, req.keyword_filter)
    if req.modality:
        filtered = filter_by_modality(filtered, req.modality)
    if req.location:
        filtered = filter_by_location(filtered, req.location)
    if req.english_levels:
        filtered = filter_by_english_level(filtered, req.english_levels)
    if req.companies:
        filtered = filter_by_companies(filtered, req.companies)
    if req.min_salary > 0:
        filtered = filter_by_salary_min(filtered, req.min_salary)
    if req.max_experience is not None and req.max_experience > 0:
        filtered = filter_by_experience(filtered, req.max_experience)
    return filtered


# ======================== Endpoints ========================

@app.get("/api/health")
def health():
    return {"status": "ok", "backend": get_current_backend()}


@app.get("/api/llm/backends")
def list_llm_backends():
    return {
        "backends": get_available_backends(),
        "current": get_current_backend(),
        "info": get_provider_info(),
    }


@app.post("/api/llm/configure")
def set_llm_backend(req: LLMConfigureRequest):
    configure(req.backend)
    return {"backend": get_current_backend(), "info": get_provider_info()}


@app.get("/api/profile")
def get_profile():
    persisted = load_all_app_state()
    return {
        "cv_text": persisted.get("cv_text", ""),
        "cv_profile": persisted.get("cv_profile", {}),
        "candidate_level": persisted.get("candidate_level"),
        "auto_interval": persisted.get("auto_interval", 30),
        "auto_keyword": persisted.get("auto_keyword", ""),
        "auto_logs": persisted.get("auto_logs", []),
        "llm_backend": get_current_backend(),
    }


@app.post("/api/profile")
def upload_profile(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Se requiere un archivo PDF")
    try:
        pdf_bytes = file.file.read()
        text = extract_text(pdf_bytes)
        level = estimate_candidate_level(text)
        profile = analyze_cv(text)
        save_app_state("cv_text", text)
        save_app_state("candidate_level", level)
        save_app_state("cv_profile", profile)
        return {
            "cv_text": text,
            "candidate_level": level,
            "cv_profile": profile,
        }
    except Exception as e:
        raise HTTPException(500, f"Error analizando CV: {e}")


@app.delete("/api/profile")
def delete_profile():
    delete_app_state("cv_text")
    delete_app_state("cv_profile")
    delete_app_state("candidate_level")
    return {"ok": True}


@app.post("/api/search")
def search_jobs(req: SearchRequest):
    try:
        jobs = _run_search(req.keyword)
        filtered = _apply_filters(jobs, req)
        filtered.sort(key=lambda j: (j.get("created_at") or "0000-00-00"), reverse=True)
        return {
            "jobs": filtered,
            "total": len(jobs),
            "filtered": len(filtered),
        }
    except Exception as e:
        raise HTTPException(500, f"Error en búsqueda: {e}")


@app.get("/api/jobs/saved")
def saved_jobs():
    return {"jobs": get_saved_jobs()}


@app.post("/api/jobs/saved")
def save_job_endpoint(payload: JobPayload):
    job = payload.job
    job.setdefault("created_at", "Fecha desconocida")
    saved = save_job(job)
    return {"ok": saved, "saved": saved}


@app.delete("/api/jobs/saved/{job_id}")
def delete_saved_job_endpoint(job_id: int):
    from src.database import _get_conn
    conn = _get_conn()
    row = conn.execute("SELECT url FROM saved_jobs WHERE id = ?", (job_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Favorito no encontrado")
    url = row["url"]
    conn.execute("DELETE FROM saved_jobs WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()
    return {"ok": True, "url": url}


@app.get("/api/jobs/discovered")
def discovered_jobs():
    return {"jobs": get_discovered_jobs()}


@app.delete("/api/jobs/discovered")
def clear_discovered():
    deleted = clear_discovered_jobs()
    return {"deleted": deleted}


@app.delete("/api/jobs/discovered/{job_id}")
def delete_discovered(job_id: int):
    ok = delete_discovered_job(job_id)
    if not ok:
        raise HTTPException(404, "Oferta detectada no encontrada")
    return {"ok": True}


@app.post("/api/interview/start")
def interview_start(req: InterviewStartRequest):
    cv_text = _load_cv_text()
    if not cv_text:
        raise HTTPException(400, "Primero sube tu CV")
    try:
        first = start_interview(cv_text, req.job)
        return {"message": first}
    except Exception as e:
        raise HTTPException(500, f"Error iniciando entrevista: {e}")


@app.post("/api/interview/continue")
def interview_continue(req: InterviewContinueRequest):
    cv_text = _load_cv_text()
    if not cv_text:
        raise HTTPException(400, "Primero sube tu CV")
    try:
        reply = continue_interview(cv_text, req.job, req.history)
        return {"message": reply}
    except Exception as e:
        raise HTTPException(500, f"Error continuando entrevista: {e}")


@app.get("/api/automation/status")
def automation_status():
    return {
        "running": automation.is_automation_running(),
        "status": automation.get_automation_status(),
    }


@app.post("/api/automation/start")
def start_automation_endpoint(req: AutomationStartRequest):
    profile = _load_profile()
    cv_text = _load_cv_text()
    if not cv_text:
        raise HTTPException(400, "Primero sube tu CV")

    os.environ["TELEGRAM_BOT_TOKEN"] = req.telegram_token
    os.environ["TELEGRAM_CHAT_ID"] = req.telegram_chat_id

    _save_auto_config(req.interval_minutes, req.keyword)

    err = automation.start_automation(
        profile=profile,
        keyword=req.keyword,
        interval_minutes=req.interval_minutes,
        log_callback=_log_callback,
        telegram_token=req.telegram_token,
        telegram_chat_id=req.telegram_chat_id,
        modality=req.modality or "",
    )
    if err:
        raise HTTPException(400, err)
    return {"ok": True, "running": True}


@app.post("/api/automation/stop")
def stop_automation_endpoint():
    automation.stop_automation()
    return {"ok": True, "running": False}


@app.post("/api/automation/reset")
def reset_automation_endpoint():
    automation.reset_notified_jobs()
    _log_callback(
        f"[{datetime.datetime.now().strftime('%H:%M')}] Historial de notificadas reseteado"
    )
    return {"ok": True}


@app.post("/api/automation/test-telegram")
def test_telegram_endpoint(req: TestTelegramRequest):
    ok = automation.test_telegram(req.telegram_token, req.telegram_chat_id)
    if not ok:
        raise HTTPException(400, "Error enviando mensaje de prueba. Verifica token y chat ID.")
    return {"ok": True}


@app.get("/api/automation/logs")
def automation_logs():
    persisted = load_all_app_state()
    logs = persisted.get("auto_logs", [])
    if not isinstance(logs, list):
        logs = []
    return {"logs": logs[-20:][::-1]}


# Mount built Astro UI at the end so API routes take precedence
ui_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui", "dist")
if os.path.isdir(ui_dist):
    app.mount("/", StaticFiles(directory=ui_dist, html=True), name="ui")

# If running directly, expose app for uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8501")))
