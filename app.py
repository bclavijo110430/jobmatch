import streamlit as st
import os

from src.cv_parser import extract_text
from src.cv_analyzer import analyze_cv
from src.job_sources import get_jobs
from src.formatter import format_jobs
from src.filters import (
    filter_by_country, filter_by_modality, filter_by_keyword,
    filter_by_location, filter_by_salary_min, filter_by_english_level,
    filter_by_companies, filter_by_experience, add_match_flag,
    filter_by_cv_relevance,
)
from src.english import estimate_candidate_level, enrich_offers_with_english
from src.interview import start_interview, continue_interview
from src.llm import configure, get_available_backends, get_provider_info
from src.database import save_job, unsave_job, get_saved_jobs, is_saved, count_saved
from src import automation

st.set_page_config(page_title="JobMatch - Búsqueda Inteligente de Empleo", layout="wide", page_icon="💼")

# ======================== DESIGN SYSTEM ========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
    --jm-bg: #090B10;
    --jm-surface: #141723;
    --jm-surface-hover: #1A1E2C;
    --jm-card: #161A28;
    --jm-card-hover: #1C2132;
    --jm-elevated: #1E2335;
    --jm-border: #252A3A;
    --jm-border-light: #2E3347;
    --jm-border-accent: rgba(99, 102, 241, 0.35);
    --jm-primary: #6366F1;
    --jm-primary-hover: #5558E6;
    --jm-primary-light: #818CF8;
    --jm-primary-soft: rgba(99, 102, 241, 0.10);
    --jm-primary-ring: rgba(99, 102, 241, 0.30);
    --jm-success: #22C55E;
    --jm-success-soft: rgba(34, 197, 94, 0.10);
    --jm-warning: #F59E0B;
    --jm-warning-soft: rgba(245, 158, 11, 0.10);
    --jm-danger: #EF4444;
    --jm-danger-soft: rgba(239, 68, 68, 0.10);
    --jm-info: #38BDF8;
    --jm-info-soft: rgba(56, 189, 248, 0.10);
    --jm-text: #E2E4EC;
    --jm-text-secondary: #99A1B8;
    --jm-text-muted: #626880;
    --jm-text-bright: #F8FAFC;
    --jm-shadow-md: 0 4px 16px rgba(0,0,0,0.5);
    --jm-shadow-lg: 0 8px 32px rgba(0,0,0,0.6);
    --jm-radius-sm: 8px;
    --jm-radius-md: 12px;
    --jm-radius-lg: 14px;
    --jm-radius-xl: 18px;
    --jm-transition: 180ms cubic-bezier(0.4, 0, 0.2, 1);
    --jm-header-height: 70px;
    --jm-tabs-height: 52px;
}

.stApp {
    background: var(--jm-bg);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
.stApp * { font-family: inherit; }

.stMarkdown, .stText, label, .stCaption { color: var(--jm-text) !important; }
.stCaption { color: var(--jm-text-muted) !important; }

h1, h2, h3, h4, h5, h6 {
    color: var(--jm-text-bright) !important;
    font-weight: 600 !important; letter-spacing: -0.01em;
}
h1 { font-size: 1.5rem !important; }
h2 { font-size: 1.25rem !important; }
h3 { font-size: 1.05rem !important; }
h4 { font-size: 0.9rem !important; }

/* ---- header bar ---- */
.main-header {
    position: sticky; top: 0; z-index: 1000;
    background: linear-gradient(135deg, #1A1040 0%, #1E1A4A 30%, #1C2248 60%, #172036 100%);
    border: 1px solid var(--jm-border-light);
    padding: 14px 28px; border-radius: var(--jm-radius-xl);
    margin-bottom: 14px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3), 0 4px 24px rgba(99, 102, 241, 0.08);
    position: sticky; overflow: hidden;
    display: flex; align-items: center; justify-content: space-between; gap: 24px;
}
.main-header::before {
    content: ''; position: absolute; top: -40%; right: -10%;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(99, 102, 241, 0.12) 0%, transparent 70%);
    border-radius: 50%; pointer-events: none;
}
.jm-header-left { position: relative; z-index: 1; }
.jm-header-left h1 { color: #F0EEFF !important; margin: 0; font-size: 1.5rem !important; font-weight: 700 !important; letter-spacing: -0.02em; }
.jm-header-left p { color: #B5B0E6; margin: 2px 0 0 0; font-size: 0.82rem; opacity: 0.9; }
.jm-header-right { position: relative; z-index: 1; }

/* ---- sticky tabs ---- */
.sticky-nav {
    position: sticky; top: var(--jm-header-height); z-index: 999;
    background: linear-gradient(180deg, rgba(9,11,16,0.98) 0%, rgba(9,11,16,0.92) 100%);
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    padding: 5px 0 3px 0; margin: 0 -1rem 2px -1rem;
    border-bottom: 1px solid var(--jm-border);
}
div[data-testid="stHorizontalBlock"] .stButton > button {
    border-radius: var(--jm-radius-md) !important;
    font-weight: 500 !important; font-size: 0.82rem !important;
    padding: 7px 12px !important; letter-spacing: -0.01em;
    transition: all var(--jm-transition) !important;
    border: 1px solid transparent !important;
}
div[data-testid="stHorizontalBlock"] .stButton > button[kind="primary"] {
    background: var(--jm-primary-soft) !important;
    color: var(--jm-primary-light) !important;
    border-color: var(--jm-border-accent) !important;
    box-shadow: none !important;
}
div[data-testid="stHorizontalBlock"] .stButton > button[kind="secondary"] {
    background: transparent !important;
    color: var(--jm-text-muted) !important;
    border-color: transparent !important;
}
div[data-testid="stHorizontalBlock"] .stButton > button[kind="secondary"]:hover {
    color: var(--jm-text-secondary) !important;
    background: var(--jm-surface) !important;
}

/* ---- sidebar (minimal) ---- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0B0D16 0%, #0F111B 100%) !important;
    border-right: 1px solid var(--jm-border) !important;
}
section[data-testid="stSidebar"] label {
    color: var(--jm-text-secondary) !important;
    font-size: 0.75rem !important; font-weight: 500 !important;
    text-transform: uppercase !important; letter-spacing: 0.04em !important;
}
section[data-testid="stSidebar"] h3 {
    color: var(--jm-text-bright) !important;
    font-size: 0.85rem !important; font-weight: 600 !important;
}

/* ---- dashboard cards ---- */
div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
    background: var(--jm-card);
    border: 1px solid var(--jm-border);
    border-radius: var(--jm-radius-lg);
    padding: 18px 20px; margin-bottom: 10px;
    transition: all var(--jm-transition);
    position: relative;
}
div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:hover {
    border-color: var(--jm-border-light);
    background: var(--jm-card-hover);
    box-shadow: var(--jm-shadow-md);
    transform: translateY(-1px);
}

/* ---- card title utility ---- */
.jm-card-title {
    display: flex; align-items: center; gap: 8px;
    font-size: 0.9rem; font-weight: 600;
    color: var(--jm-text-bright);
    margin-bottom: 12px;
}

/* ---- buttons ---- */
.stButton > button {
    border-radius: var(--jm-radius-sm) !important;
    font-weight: 500 !important; font-size: 0.82rem !important;
    transition: all var(--jm-transition) !important;
    padding: 7px 16px !important; letter-spacing: -0.01em !important;
}
.stButton > button[kind="primary"] {
    background: var(--jm-primary) !important;
    border: 1px solid var(--jm-primary-hover) !important;
    color: #fff !important;
    box-shadow: 0 2px 8px rgba(99, 102, 241, 0.2);
}
.stButton > button[kind="primary"]:hover {
    background: var(--jm-primary-hover) !important;
    box-shadow: 0 4px 16px rgba(99, 102, 241, 0.35) !important;
    transform: translateY(-1px);
}
.stButton > button[kind="secondary"] {
    background: var(--jm-surface) !important;
    color: var(--jm-text-secondary) !important;
    border: 1px solid var(--jm-border) !important;
}
.stButton > button[kind="secondary"]:hover {
    color: var(--jm-text) !important;
    border-color: var(--jm-border-light) !important;
    background: var(--jm-surface-hover) !important;
}

/* ---- metrics ---- */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, var(--jm-surface), #181C2D);
    border: 1px solid var(--jm-border);
    border-radius: var(--jm-radius-md);
    padding: 12px 16px;
    transition: border-color var(--jm-transition);
}
div[data-testid="stMetric"]:hover { border-color: var(--jm-border-light); }
div[data-testid="stMetric"] label {
    color: var(--jm-text-muted) !important;
    font-weight: 500 !important;
    font-size: 0.7rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: var(--jm-text-bright) !important;
    font-weight: 700 !important;
    font-size: 1.2rem !important;
}

/* ---- links ---- */
a {
    color: var(--jm-primary-light) !important;
    text-decoration: none !important;
    transition: color var(--jm-transition);
}
a:hover { color: var(--jm-primary) !important; text-decoration: underline !important; }

/* ---- alerts ---- */
div[data-testid="stAlert"] {
    border-radius: var(--jm-radius-md) !important;
    border: 1px solid var(--jm-border) !important;
    background: var(--jm-surface) !important;
    color: var(--jm-text) !important;
    padding: 14px 18px !important;
}

/* ---- inputs ---- */
div[data-testid="stFileUploaderDropzone"] {
    background: var(--jm-surface) !important;
    border: 1px dashed var(--jm-border-light) !important;
    border-radius: var(--jm-radius-sm) !important;
    padding: 10px 14px !important;
}
span[data-testid="stFileUploaderDropzoneInstructions"] {
    display: none !important;
}
span[data-testid="stIconMaterial"] {
    display: none !important;
}
input, textarea, div[data-baseweb="input"], div[data-baseweb="select"] {
    background: var(--jm-surface) !important;
    border: 1px solid var(--jm-border) !important;
    border-radius: var(--jm-radius-sm) !important;
    color: var(--jm-text) !important;
    transition: all var(--jm-transition) !important;
}
input:focus, textarea:focus, div[data-baseweb="input"]:focus-within {
    border-color: var(--jm-primary) !important;
    box-shadow: 0 0 0 3px var(--jm-primary-ring) !important;
    outline: none !important;
}
div[data-baseweb="popover"] {
    background: var(--jm-elevated) !important;
    border: 1px solid var(--jm-border-light) !important;
    border-radius: var(--jm-radius-sm) !important;
}

/* ---- radio ---- */
div[role="radiogroup"] label {
    border: 1px solid var(--jm-border) !important;
    border-radius: var(--jm-radius-sm) !important;
    transition: all var(--jm-transition) !important;
}
div[role="radiogroup"] label[data-checked="true"] {
    border-color: var(--jm-border-accent) !important;
    background: var(--jm-primary-soft) !important;
}

/* ---- chat ---- */
div[data-testid="stChatMessage"] {
    border-radius: var(--jm-radius-md) !important;
    padding: 12px 16px !important;
}
div[data-testid="stChatMessage"][data-testid="stChatMessage"] {
    background: var(--jm-surface) !important;
    border: 1px solid var(--jm-border) !important;
}

/* ---- progress ---- */
div[data-testid="stProgress"] > div { background: var(--jm-primary-soft) !important; }
div[data-testid="stProgress"] > div > div { background: var(--jm-primary) !important; }

/* ---- expander ---- */
.stExpander {
    border: 1px solid var(--jm-border) !important;
    border-radius: var(--jm-radius-sm) !important;
    background: var(--jm-surface) !important;
}
.stExpander > div[role="button"] { color: var(--jm-text-secondary) !important; font-weight: 500 !important; }

/* ---- scrollbar ---- */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--jm-bg); }
::-webkit-scrollbar-thumb { background: var(--jm-border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--jm-border-light); }

/* ---- badges ---- */
.jm-badge {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 2px 9px; border-radius: 20px;
    font-size: 0.74rem; font-weight: 500;
    white-space: nowrap; line-height: 1.4;
}
.jm-badge-success { background: var(--jm-success-soft); color: var(--jm-success); border: 1px solid rgba(34, 197, 94, 0.2); }
.jm-badge-primary { background: var(--jm-primary-soft); color: var(--jm-primary-light); border: 1px solid rgba(99, 102, 241, 0.2); }
.jm-badge-warning { background: var(--jm-warning-soft); color: var(--jm-warning); border: 1px solid rgba(245, 158, 11, 0.2); }
.jm-badge-neutral { background: var(--jm-surface); color: var(--jm-text-muted); border: 1px solid var(--jm-border); }
.jm-badge-info { background: var(--jm-info-soft); color: var(--jm-info); border: 1px solid rgba(56, 189, 248, 0.2); }

/* ---- meta row ---- */
.jm-meta-row {
    display: flex; flex-wrap: wrap; gap: 10px;
    align-items: center; margin: 6px 0;
}
.jm-meta-item {
    display: inline-flex; align-items: center; gap: 4px;
    color: var(--jm-text-muted); font-size: 0.8rem;
}
.jm-divider {
    width: 100%; height: 1px;
    background: var(--jm-border); margin: 12px 0;
    border: none; opacity: 0.6;
}

/* ---- stat highlight ---- */
.jm-stat-highlight {
    font-size: 0.78rem; color: var(--jm-text-muted);
    display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
    margin: 4px 0 10px 0;
}
.jm-stat-highlight span { display: inline-flex; align-items: center; gap: 4px; }

/* ---- empty state ---- */
.jm-empty-state {
    text-align: center; padding: 40px 20px;
    border: 2px dashed var(--jm-border);
    border-radius: var(--jm-radius-xl);
    background: var(--jm-surface);
}
.jm-empty-state h3 { margin-bottom: 8px; }
.jm-empty-state p { color: var(--jm-text-muted); margin: 4px 0; }
.jm-empty-state .jm-step {
    display: inline-flex; align-items: center; justify-content: center;
    width: 26px; height: 26px;
    background: var(--jm-primary-soft);
    color: var(--jm-primary-light);
    border-radius: 50%; font-weight: 700; font-size: 0.82rem;
    margin-right: 8px;
}

/* ---- responsive ---- */
@media (max-width: 768px) {
    .main-header { padding: 12px 18px; }
    .main-header h1 { font-size: 1.2rem !important; }
    div[data-testid="stMetric"] label { font-size: 0.65rem !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { font-size: 1rem !important; }
}
</style>
""", unsafe_allow_html=True)

# ======================== SESSION STATE ========================
for key, default in [
    ("candidate_level", None), ("cv_text", ""), ("jobs", []),
    ("formatted_jobs", []), ("interview_history", []),
    ("interview_job", None), ("saved_urls", set()),
    ("cv_profile", {}), ("relevant_count", 0), ("other_count", 0),
    ("auto_interval", 30), ("auto_keyword", ""), ("auto_logs", []),
    ("automation_active", False), ("active_tab", "Ofertas"),
    ("llm_backend", "freellmapi" if any(b["key"] == "freellmapi" for b in get_available_backends()) else (get_available_backends()[0]["key"] if get_available_backends() else "ollama")),
]:
    if key not in st.session_state:
        st.session_state[key] = default

configure(st.session_state.llm_backend)

# --- auto-start detection ---
if os.getenv("AUTO_START", "false").lower() == "true":
    if "auto_started" not in st.session_state:
        st.session_state.auto_started = True
        st.session_state.automation_active = True
        st.session_state.auto_interval = int(os.getenv("AUTO_INTERVAL", "30"))
        st.session_state.auto_keyword = os.getenv("AUTO_KEYWORD", "")
        st.rerun()

# ======================== HEADER ========================
info = get_provider_info()
backends = get_available_backends()
backend_keys = [b["key"] for b in backends]
current_idx = backend_keys.index(st.session_state.llm_backend) if st.session_state.llm_backend in backend_keys else 0

st.markdown(f"""
<div class="main-header">
    <div class="jm-header-left">
        <h1>💼 JobMatch</h1>
        <p>Búsqueda inteligente de empleo · Backend: {info['label']} · Modelo: <code style="background:rgba(99,102,241,0.15);color:#A5B4FC;padding:2px 8px;border-radius:6px;font-size:0.78rem;">{info['model']}</code></p>
    </div>
    <div class="jm-header-right"></div>
</div>
""", unsafe_allow_html=True)

# --- LLM provider selector (minimal sidebar) ---
with st.sidebar:
    st.markdown("#### ⚙️ Configuración")
    selected_idx = st.radio(
        "Proveedor LLM",
        range(len(backends)),
        format_func=lambda i: f"{backends[i]['icon']} {backends[i]['label']}",
        index=current_idx,
        key="backend_selector",
    )
    if backends[selected_idx]["key"] != st.session_state.llm_backend:
        st.session_state.llm_backend = backends[selected_idx]["key"]
    configure(st.session_state.llm_backend)
    st.caption(f"Modelo: `{backends[selected_idx]['model']}`")

# ======================== DASHBOARD ROW 1: Perfil + Búsqueda ========================
col_profile, col_search = st.columns([1, 1])

# --- Perfil Card ---
with col_profile:
    with st.container(border=True):
        st.markdown('<div class="jm-card-title">👤 Tu Perfil</div>', unsafe_allow_html=True)
        cv_file = st.file_uploader("CV (PDF)", type=["pdf"], help="PDF con texto extraíble", label_visibility="collapsed", accept_multiple_files=False)
        if cv_file is not None:
            with st.spinner("Analizando CV..."):
                pdf_bytes = cv_file.read()
                text = extract_text(pdf_bytes)
                st.session_state.cv_text = text
                level = estimate_candidate_level(text)
                st.session_state.candidate_level = level
                profile = analyze_cv(text)
                st.session_state.cv_profile = profile
            st.success(f"✅ CV analizado · Nivel de inglés: **{level}**")
            profile = st.session_state.cv_profile
            if profile.get("skills"):
                st.caption(f"Habilidades: {', '.join(profile['skills'][:8])}")
            if profile.get("target_titles"):
                st.caption(f"Cargos: {', '.join(profile['target_titles'][:3])}")
            if profile.get("years_experience"):
                st.caption(f"Experiencia: {profile['years_experience']} años")
            if profile.get("search_keywords"):
                st.caption(f"Keywords: {', '.join(profile['search_keywords'][:5])}")

# --- Búsqueda Card ---
with col_search:
    with st.container(border=True):
        st.markdown('<div class="jm-card-title">🔍 Búsqueda</div>', unsafe_allow_html=True)
        manual_kw = st.text_input("Buscar en internet", placeholder="ej: Python, React, developer...", label_visibility="collapsed")
        scrape_btn = st.button("🔍 Buscar ofertas", type="primary", use_container_width=True)
        if st.session_state.formatted_jobs:
            st.caption(f"📋 {len(st.session_state.formatted_jobs)} ofertas cargadas")
        saved_count = count_saved()
        if saved_count:
            st.caption(f"⭐ {saved_count} ofertas guardadas")

# ======================== SEARCH LOGIC ========================
if scrape_btn or st.session_state.formatted_jobs:
    if scrape_btn:
        with st.spinner("Buscando ofertas en internet..."):
            profile = st.session_state.cv_profile or {}
            titles = list(profile.get("target_titles", []))
            keywords = list(profile.get("search_keywords", []))
            terms = titles + keywords
            if manual_kw.strip():
                terms.insert(0, manual_kw.strip())
            if not terms:
                terms = [manual_kw.strip()] if manual_kw.strip() else [""]
            search_term = terms[0]
            extra_terms = terms[1:] if len(terms) > 1 else []

            all_raw = get_jobs(search_term)
            if extra_terms and len(all_raw) < 30:
                for kw in extra_terms:
                    more = get_jobs(kw)
                    seen = {j.get("url", "") for j in all_raw if j.get("url")}
                    for j in more:
                        if j.get("url", "") not in seen:
                            all_raw.append(j)
                            seen.add(j.get("url", ""))

            if all_raw:
                relevant_raw, other_raw = filter_by_cv_relevance(all_raw, profile)
                formatted_relevant = format_jobs(relevant_raw) if relevant_raw else []
                formatted_relevant = enrich_offers_with_english(formatted_relevant)
                formatted_relevant = filter_by_country(formatted_relevant, "Colombia")
                formatted_relevant = add_match_flag(formatted_relevant, st.session_state.candidate_level)

                others = []
                for j in other_raw:
                    others.append({
                        "title": j.get("title", "Sin título"), "url": j.get("url", ""),
                        "company": "No disponible", "salary": "No disponible",
                        "modality": "No especificado", "location": "Colombia",
                        "country": "Colombia", "description_short": j.get("raw_text", "")[:150],
                        "english_level": "Ninguno", "source": j.get("source", ""),
                        "created_at": j.get("created_at", ""), "english_match": True,
                    })
                others = filter_by_country(others, "Colombia")
                all_formatted = formatted_relevant + others
                st.session_state.formatted_jobs = all_formatted
                st.session_state.jobs = all_formatted
                st.session_state.relevant_count = len(relevant_raw)
                st.session_state.other_count = len(other_raw)
            else:
                st.error("No se encontraron ofertas. Intenta de nuevo.")

jobs = st.session_state.formatted_jobs
has_jobs = bool(jobs)

# ======================== DASHBOARD ROW 2: Estadísticas + Filtros ========================
if has_jobs:
    # --- Stats strip ---
    if st.session_state.candidate_level:
        relevant = st.session_state.get("relevant_count", 0)
        other = st.session_state.get("other_count", 0)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Ofertas", len(jobs))
        match_count = sum(1 for j in jobs if j.get("english_match"))
        c2.metric("Match Inglés", match_count)
        c3.metric("Tu Nivel", st.session_state.candidate_level)
        c4.metric("Guardadas", count_saved())
        if relevant:
            st.markdown(f"""
            <div class="jm-stat-highlight">
                <span>🎯 <strong>{relevant}</strong> relevantes (IA)</span>
                <span>📋 <strong>{other}</strong> adicionales</span>
            </div>
            """, unsafe_allow_html=True)

    # --- Filters card (collapsible) ---
    with st.expander("🎯 Filtros avanzados", expanded=False):
        fcol1, fcol2, fcol3 = st.columns(3)
        f_keyword = fcol1.text_input("Palabra clave", placeholder="filtrar por título...")
        available_modalities = ["Todas", "Remoto", "Híbrido", "Presencial", "No especificado"]
        f_modality = fcol1.selectbox("Modalidad", available_modalities)
        available_locations = sorted(set(
            (j.get("location") or "").split(",")[0].strip()
            for j in st.session_state.formatted_jobs if (j.get("location") or "").strip()
        ))
        f_locations = fcol2.multiselect("Ubicación", available_locations) if available_locations else []
        f_english = fcol2.multiselect("Nivel de inglés", ["Ninguno", "A1-A2", "B1-B2", "C1-C2"])
        available_companies = sorted(set(
            j.get("company") or "" for j in st.session_state.formatted_jobs
            if (j.get("company") or "").strip() and (j.get("company") or "") != "No disponible"
        ))
        f_companies = fcol3.multiselect("Empresa", available_companies) if available_companies else []
        f_min_salary = fcol3.number_input("Salario mínimo (COP)", min_value=0, value=0, step=500000, format="%d")
        f_max_exp = fcol3.slider("Experiencia máx (años)", min_value=0, max_value=15, value=15, step=1, help="0 = incluir sin requisito")

    filtered = filter_by_keyword(jobs, f_keyword)
    filtered = filter_by_modality(filtered, f_modality)
    filtered = filter_by_location(filtered, f_locations)
    filtered = filter_by_salary_min(filtered, float(f_min_salary))
    filtered = filter_by_english_level(filtered, f_english)
    filtered = filter_by_companies(filtered, f_companies)
    filtered = filter_by_experience(filtered, f_max_exp if f_max_exp < 15 else None)
else:
    filtered = []

def _sort_key_date(j):
    d = (j.get("created_at") or "").strip()
    if d and d != "Fecha desconocida":
        return d
    return "0000-00-00"
if has_jobs:
    filtered.sort(key=_sort_key_date, reverse=True)
    jobs.sort(key=_sort_key_date, reverse=True)

# ======================== TAB NAVIGATION ========================
tab_labels = ["Ofertas", "Entrevista", "Favoritos", "Automatización", "Resumen"]
if st.session_state.active_tab not in tab_labels:
    st.session_state.active_tab = "Ofertas"

st.markdown('<div class="sticky-nav">', unsafe_allow_html=True)
tab_cols = st.columns(5)
for i, label in enumerate(tab_labels):
    btn_type = "primary" if st.session_state.active_tab == label else "secondary"
    with tab_cols[i]:
        if st.button(label, use_container_width=True, type=btn_type, key=f"tabbtn_{label}"):
            st.session_state.active_tab = label
            st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# ======================== TAB: Ofertas ========================
if st.session_state.active_tab == "Ofertas":
    if not has_jobs:
        st.markdown(f"""
        <div class="jm-empty-state">
            <h3>💼 Bienvenido a JobMatch</h3>
            <p>Encuentra las mejores ofertas laborales con IA. Sigue estos pasos:</p>
            <br>
            <p style="line-height:2;">
                <span class="jm-step">1</span><strong> Sube tu CV</strong> en PDF en la tarjeta superior<br>
                <span class="jm-step">2</span><strong> Escribe una palabra clave</strong> y haz clic en <em>Buscar ofertas</em><br>
                <span class="jm-step">3</span><strong> Explora las ofertas</strong> filtradas a tu perfil<br>
                <span class="jm-step">4</span><strong> Guarda favoritas</strong> y simula entrevistas
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"### 📋 Ofertas ({len(filtered)})")

        def _eng_badge(level, match):
            css_class = "jm-badge-neutral"
            if level in ("C1-C2", "C1", "C2"): css_class = "jm-badge-success"
            elif level in ("B1-B2", "B1", "B2"): css_class = "jm-badge-primary"
            elif level in ("A1-A2", "A1", "A2"): css_class = "jm-badge-warning"
            icon = "✅" if match else ""
            return f'<span class="jm-badge {css_class}">{icon} {level}</span>'

        def _mod_badge(m):
            if m in ("Remoto", "Remote"): return '<span class="jm-badge jm-badge-success">🏠 Remoto</span>'
            elif m in ("Híbrido", "Hybrid"): return '<span class="jm-badge jm-badge-primary">🔄 Híbrido</span>'
            elif m in ("Presencial", "On-site"): return '<span class="jm-badge jm-badge-neutral">🏢 Presencial</span>'
            return f'<span class="jm-badge jm-badge-neutral">📌 {m}</span>'

        for idx, j in enumerate(filtered):
            with st.container(border=True):
                url = j.get("url", "")
                title = j.get("title", "Sin título")
                company = j.get('company', 'No disponible')
                location = j.get('location', 'N/A')
                eng = j.get("english_level", "Ninguno")
                match = j.get("english_match", False)
                modality = j.get('modality', 'No especificado')
                created = j.get("created_at", "")
                date_display = created[:10] if created and created != "Fecha desconocida" else ""

                cols = st.columns([5, 2])
                if url:
                    cols[0].markdown(f"### [{title}]({url})", unsafe_allow_html=True)
                else:
                    cols[0].markdown(f"### {title}")

                st.markdown(f"""
                <div class="jm-meta-row">
                    <span class="jm-meta-item">🏢 {company}</span>
                    <span class="jm-meta-item">📍 {location}</span>
                    <span class="jm-meta-item">📅 {date_display}</span>
                    {_mod_badge(modality)}
                    {_eng_badge(eng, match)}
                </div>
                """, unsafe_allow_html=True)

                salary = j.get("salary") or "No disponible"
                if salary != "No disponible":
                    salary_val = salary.split("-")[0].strip() if "-" in salary else salary
                    cols[1].metric("Salario", salary_val)
                else:
                    cols[1].markdown("<span style='color:var(--jm-text-muted);font-size:0.8rem;'>💰 No especificado</span>", unsafe_allow_html=True)

                dsc = j.get("description_short") or "Sin descripción"
                st.markdown(dsc)
                if url:
                    st.markdown(f"[🔗 Ver oferta original]({url})")

                ikey = f"interview_{idx}_{j.get('title','')}_{j.get('company','')}"
                job_url = j.get("url", "")
                saved = job_url and (job_url in st.session_state.saved_urls or is_saved(job_url))
                skey = f"save_{idx}_{j.get('title','')}"

                cbtn1, cbtn2 = st.columns(2)
                if cbtn1.button("🎤 Simular entrevista", key=ikey, use_container_width=True):
                    st.session_state.interview_job = j
                    st.session_state.interview_history = []
                    st.session_state.active_tab = "Entrevista"
                    st.rerun()
                if saved:
                    if cbtn2.button("💾 Quitar de favoritos", key=skey, use_container_width=True):
                        unsave_job(job_url)
                        st.session_state.saved_urls.discard(job_url)
                        st.rerun()
                else:
                    if cbtn2.button("⭐ Guardar oferta", key=skey, use_container_width=True):
                        j.setdefault("created_at", "Fecha desconocida")
                        save_job(j)
                        st.session_state.saved_urls.add(job_url)
                        st.rerun()

# ======================== TAB: Entrevista ========================
elif st.session_state.active_tab == "Entrevista":
    st.markdown("### 🎤 Entrevista simulada")

    if not st.session_state.cv_text:
        st.warning("Primero sube tu CV en la tarjeta de Perfil (arriba).")
    elif not jobs:
        st.warning("Primero busca ofertas en la pestaña 'Ofertas'.")
    else:
        all_titles = [f"{j.get('title','')} — {j.get('company','')}" for j in jobs]
        with st.container(border=True):
            st.markdown('<div class="jm-card-title">📋 Selecciona una oferta</div>', unsafe_allow_html=True)
            selected_title = st.selectbox("Oferta para la entrevista", all_titles, index=0, label_visibility="collapsed")

            selected_job = None
            if selected_title:
                for j in jobs:
                    if f"{j.get('title','')} — {j.get('company','')}" == selected_title:
                        selected_job = j
                        break
            if st.session_state.interview_job:
                selected_job = st.session_state.interview_job

            if selected_job:
                st.info(f"🎯 **Entrevistando para:** {selected_job.get('title')} en {selected_job.get('company')}")
                if st.button("🔄 Iniciar / Reiniciar entrevista", use_container_width=True):
                    with st.spinner("Preparando entrevista..."):
                        first = start_interview(st.session_state.cv_text, selected_job)
                        st.session_state.interview_history = [{"role": "assistant", "content": first}]
                        st.rerun()

        if selected_job:
            for msg in st.session_state.interview_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
            if st.session_state.interview_history:
                st.markdown('<hr class="jm-divider">', unsafe_allow_html=True)
                user_answer = st.chat_input("Escribe tu respuesta aquí...")
                if user_answer:
                    st.session_state.interview_history.append({"role": "user", "content": user_answer})
                    with st.chat_message("user"):
                        st.markdown(user_answer)
                    with st.spinner("Procesando respuesta..."):
                        reply = continue_interview(
                            st.session_state.cv_text, selected_job,
                            st.session_state.interview_history,
                        )
                        st.session_state.interview_history.append({"role": "assistant", "content": reply})
                    st.rerun()

# ======================== TAB: Favoritos ========================
elif st.session_state.active_tab == "Favoritos":
    st.markdown("### ⭐ Ofertas guardadas")

    saved = get_saved_jobs()
    if not saved:
        st.markdown("""
        <div class="jm-empty-state">
            <h3>⭐ Sin favoritos aún</h3>
            <p>Usa el botón <strong>Guardar oferta</strong> en la pestaña Ofertas para añadirlas aquí.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="jm-stat-highlight"><span>📌 <strong>{len(saved)}</strong> oferta(s) guardada(s)</span></div>', unsafe_allow_html=True)

        def _eng_badge_s(level):
            c = "jm-badge-neutral"
            if level in ("C1-C2", "C1", "C2"): c = "jm-badge-success"
            elif level in ("B1-B2", "B1", "B2"): c = "jm-badge-primary"
            elif level in ("A1-A2", "A1", "A2"): c = "jm-badge-warning"
            return f'<span class="jm-badge {c}">{level}</span>'

        def _mod_badge_s(m):
            if m in ("Remoto", "Remote"): return '<span class="jm-badge jm-badge-success">🏠 Remoto</span>'
            elif m in ("Híbrido", "Hybrid"): return '<span class="jm-badge jm-badge-primary">🔄 Híbrido</span>'
            elif m in ("Presencial", "On-site"): return '<span class="jm-badge jm-badge-neutral">🏢 Presencial</span>'
            return f'<span class="jm-badge jm-badge-neutral">{m}</span>'

        for s in saved:
            with st.container(border=True):
                cols = st.columns([5, 2])
                url = s.get("url", "")
                title = s.get("title", "Sin título")
                if url:
                    cols[0].markdown(f"### [{title}]({url})", unsafe_allow_html=True)
                else:
                    cols[0].markdown(f"### {title}")

                st.markdown(f"""
                <div class="jm-meta-row">
                    <span class="jm-meta-item">🏢 {s.get('company','N/A')}</span>
                    <span class="jm-meta-item">📍 {s.get('location','N/A')}</span>
                    <span class="jm-meta-item">📅 {s.get('created_at','')[:10]}</span>
                    {_mod_badge_s(s.get('modality','N/A'))}
                    {_eng_badge_s(s.get('english_level','N/A'))}
                </div>
                """, unsafe_allow_html=True)

                salary = s.get("salary") or "No disponible"
                if salary != "No disponible":
                    cols[1].metric("Salario", salary.split("-")[0].strip() if "-" in salary else salary)
                else:
                    cols[1].markdown("<span style='color:var(--jm-text-muted);font-size:0.8rem;'>💰 No especificado</span>", unsafe_allow_html=True)

                st.markdown(s.get("description_short") or "Sin descripción")
                st.markdown(f'<span class="jm-meta-item" style="font-size:0.76rem;">📥 Guardada: {s.get("saved_at","")[:10]}</span>', unsafe_allow_html=True)
                if url:
                    st.markdown(f"[🔗 Ver oferta original]({url})")

                cbtn1, cbtn2 = st.columns(2)
                if cbtn1.button("🎤 Simular entrevista", key=f"iv_saved_{s['id']}", use_container_width=True):
                    st.session_state.interview_job = dict(s)
                    st.session_state.interview_history = []
                    st.session_state.active_tab = "Entrevista"
                    st.rerun()
                if cbtn2.button("🗑️ Eliminar", key=f"del_saved_{s['id']}", use_container_width=True):
                    unsave_job(url)
                    st.session_state.saved_urls.discard(url)
                    st.rerun()

# ======================== TAB: Automatización ========================
elif st.session_state.active_tab == "Automatización":
    st.markdown("### ⚡ Automatización de búsqueda")

    if not st.session_state.cv_profile or not st.session_state.cv_text:
        st.warning("Primero sube tu CV en la tarjeta Perfil para configurar la automatización.")
    else:
        ct1, ct2 = st.columns(2)
        with ct1:
            with st.container(border=True):
                st.markdown('<div class="jm-card-title">🔔 Telegram</div>', unsafe_allow_html=True)
                tg_token = st.text_input("Bot Token", type="password", value=os.getenv("TELEGRAM_BOT_TOKEN", ""),
                    help="Crea un bot con @BotFather", key="tg_token_input", placeholder="123456:ABC-DEF...")
                tg_chat = st.text_input("Chat ID", value=os.getenv("TELEGRAM_CHAT_ID", ""),
                    help="Visita https://api.telegram.org/bot<TOKEN>/getUpdates", key="tg_chat_input", placeholder="123456789")
                if st.button("🔔 Probar notificación", use_container_width=True):
                    if automation.test_telegram(tg_token, tg_chat):
                        st.success("Notificación enviada. Revisa Telegram.")
                    else:
                        st.error("Error al enviar. Verifica token y chat ID.")
        with ct2:
            with st.container(border=True):
                st.markdown('<div class="jm-card-title">📅 Programación</div>', unsafe_allow_html=True)
                interval = st.number_input("Minutos entre búsquedas", min_value=5, max_value=720,
                    value=st.session_state.auto_interval, step=5, key="auto_interval_input")
                auto_kw = st.text_input("Keyword adicional", value=st.session_state.get("auto_keyword", ""),
                    placeholder="ej: Python, React...", key="auto_keyword_input")

        with st.container(border=True):
            st.markdown('<div class="jm-card-title">▶️ Control</div>', unsafe_allow_html=True)
            is_running = automation.is_automation_running() or os.path.exists("/app/data/auto_starter.pid")
            status_badge = '<span class="jm-badge jm-badge-success">🟢 Activa</span>' if is_running else '<span class="jm-badge jm-badge-neutral">⚪ Detenida</span>'
            st.markdown(f'<div style="margin:4px 0 10px 0;">Estado: {status_badge}</div>', unsafe_allow_html=True)
            col_start, col_stop, _ = st.columns([1, 1, 3])
            if col_start.button("▶️ Iniciar", type="primary", use_container_width=True, disabled=is_running):
                if not tg_token or not tg_chat:
                    st.error("Configura token y chat ID de Telegram primero.")
                else:
                    st.session_state.auto_interval = interval
                    st.session_state.auto_keyword = auto_kw
                    os.environ["TELEGRAM_BOT_TOKEN"] = tg_token
                    os.environ["TELEGRAM_CHAT_ID"] = tg_chat

                    def log(msg):
                        st.session_state.auto_logs.append(msg)
                        if len(st.session_state.auto_logs) > 50:
                            st.session_state.auto_logs = st.session_state.auto_logs[-50:]

                    err = automation.start_automation(
                        profile=st.session_state.cv_profile, keyword=auto_kw,
                        interval_minutes=interval, log_callback=log,
                        telegram_token=tg_token, telegram_chat_id=tg_chat,
                    )
                    if err:
                        st.error(err)
                    else:
                        st.session_state.automation_active = True
                        st.success("Automatización iniciada.")
                        st.rerun()
            if col_stop.button("⏹️ Detener", use_container_width=True, disabled=not is_running):
                automation.stop_automation()
                st.session_state.automation_active = False
                st.success("Automatización detenida.")
                st.rerun()

        if st.session_state.auto_logs:
            with st.expander(f"📋 Registro ({len(st.session_state.auto_logs)} eventos)"):
                for log_line in reversed(st.session_state.auto_logs[-20:]):
                    st.text(log_line)

        st.info("""
        **¿Cómo configurar Telegram?**
        1. Abre [@BotFather](https://t.me/BotFather) en Telegram
        2. Envía `/newbot` y sigue las instrucciones
        3. Copia el **token** y pégalo arriba
        4. Inicia chat con tu bot y envía cualquier mensaje
        5. Visita `https://api.telegram.org/bot<TOKEN>/getUpdates` para obtener tu **chat ID**
        """)

# ======================== TAB: Resumen ========================
elif st.session_state.active_tab == "Resumen":
    st.markdown("### 📊 Resumen de tu perfil")

    if st.session_state.cv_text:
        r1, r2 = st.columns(2)
        with r1:
            with st.container(border=True):
                st.markdown('<div class="jm-card-title">🗣️ Nivel de Inglés</div>', unsafe_allow_html=True)
                st.metric("Tu nivel", st.session_state.candidate_level or "No analizado")
        with r2:
            with st.container(border=True):
                st.markdown('<div class="jm-card-title">💼 Ofertas Disponibles</div>', unsafe_allow_html=True)
                st.metric("Total", len(st.session_state.formatted_jobs))

        if st.session_state.formatted_jobs:
            match_count = sum(1 for j in st.session_state.formatted_jobs if j.get("english_match"))
            total = max(len(st.session_state.formatted_jobs), 1)
            pct = int(match_count / total * 100)

            with st.container(border=True):
                st.markdown(f'<div class="jm-card-title">✅ Compatibilidad de inglés: {pct}%</div>', unsafe_allow_html=True)
                st.progress(match_count / total)
                st.caption(f"{match_count} de {len(st.session_state.formatted_jobs)} ofertas compatibles con tu nivel")

            with st.container(border=True):
                st.markdown('<div class="jm-card-title">📊 Distribución por nivel de inglés</div>', unsafe_allow_html=True)
                levels_count = {}
                for j in st.session_state.formatted_jobs:
                    lvl = j.get("english_level", "Ninguno")
                    levels_count[lvl] = levels_count.get(lvl, 0) + 1
                for lvl in ["Ninguno", "A1", "A2", "B1", "B2", "C1", "C2"]:
                    if lvl in levels_count:
                        cnt = levels_count[lvl]
                        bar = "█" * min(cnt, 40)
                        st.markdown(f"**{lvl}** ({cnt}): `{bar}`")

            with st.expander("📄 Ver texto completo del CV"):
                st.text(st.session_state.cv_text)
    else:
        st.markdown("""
        <div class="jm-empty-state">
            <h3>📊 Sin datos del perfil</h3>
            <p>Sube tu CV en la tarjeta Perfil para ver tu resumen y estadísticas.</p>
        </div>
        """, unsafe_allow_html=True)