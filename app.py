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

st.set_page_config(page_title="JobMatch - Smart Job Search", layout="wide", page_icon="💼")

st.markdown("""
<style>
    :root {
        --bg-deep: #0a0b14;
        --bg-card: #12141f;
        --bg-elevated: #181b2a;
        --border: #252838;
        --border-hover: #4a3f8a;
        --primary: #7c5ce7;
        --primary-light: #a78bfa;
        --primary-glow: rgba(124,92,231,0.25);
        --text: #d4d4e8;
        --text-muted: #8b8fa8;
        --text-bright: #f0f0ff;
    }
    .stApp { background: var(--bg-deep); }
    .stMarkdown, .stText, label { color: var(--text) !important; }
    h1,h2,h3,h4 { color: var(--text-bright) !important; font-weight: 600 !important; }

    .main-header {
        background: linear-gradient(135deg, #3b1f8a 0%, #5b3cc4 40%, #7c5ce7 100%);
        padding: 20px 32px; border-radius: 18px; margin-bottom: 6px;
        box-shadow: 0 8px 32px rgba(124,92,231,0.2);
    }
    .main-header h1 { color: #fff !important; margin: 0; font-size: 1.9rem; letter-spacing: -0.5px; }

    /* ---- sticky nav ---- */
    .sticky-nav {
        position: sticky; top: 0; z-index: 999;
        background: linear-gradient(180deg, rgba(10,11,20,0.98) 0%, rgba(10,11,20,0.92) 100%);
        backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
        padding: 10px 0 6px 0; margin: 0 -1rem 6px -1rem;
        border-bottom: 1px solid var(--border);
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0c0d19 0%, #12141f 100%) !important;
        border-right: 1px solid var(--border) !important;
    }
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 { color: var(--primary-light) !important; }

    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
        background: var(--bg-card); border: 1px solid var(--border);
        border-radius: 14px; padding: 18px; margin-bottom: 12px; transition: all 0.25s;
    }
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:hover {
        border-color: var(--border-hover); box-shadow: 0 6px 24px var(--primary-glow);
    }

    .stButton > button {
        border-radius: 10px !important; font-weight: 500 !important;
        transition: all 0.2s !important; padding: 8px 20px !important; letter-spacing: 0.2px;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #5b3cc4, var(--primary)) !important;
        border: none !important; color: #fff !important;
    }
    .stButton > button[kind="secondary"] {
        background: var(--bg-elevated) !important; color: var(--primary-light) !important;
        border: 1px solid var(--border) !important;
    }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px var(--primary-glow); }

    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, var(--bg-elevated), #1d2035);
        border: 1px solid var(--border); border-radius: 14px; padding: 14px 20px;
    }
    div[data-testid="stMetric"] label { color: var(--primary-light) !important; font-weight: 500 !important; }
    div[data-testid="stMetric"] div { color: var(--text-bright) !important; font-weight: 700 !important; }

    a { color: var(--primary-light) !important; text-decoration: none !important; }
    a:hover { color: var(--primary) !important; text-decoration: underline !important; }

    div[data-testid="stAlert"] {
        border-radius: 12px !important; border: 1px solid var(--border) !important;
        background: var(--bg-card) !important; color: var(--text) !important;
    }

    input, textarea, div[data-baseweb="input"] {
        background: var(--bg-elevated) !important; border: 1px solid var(--border) !important;
        border-radius: 10px !important; color: var(--text) !important;
    }
    input:focus, textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px var(--primary-glow) !important;
    }

    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-deep); }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--border-hover); }
</style>
""", unsafe_allow_html=True)

info = get_provider_info()
st.markdown(f"""
<div class="main-header">
    <h1>💼 JobMatch</h1>
    <p style="color:#e0d8ff; margin:4px 0 0 0; font-size:0.95rem;">
        {info['label']} · modelo <code>{info['model']}</code>
    </p>
</div>
""", unsafe_allow_html=True)

# --- session state ---
for key, default in [
    ("candidate_level", None),
    ("cv_text", ""),
    ("jobs", []),
    ("formatted_jobs", []),
    ("interview_history", []),
    ("interview_job", None),
    ("saved_urls", set()),
    ("cv_profile", {}),
    ("relevant_count", 0),
    ("other_count", 0),
    ("auto_interval", 30),
    ("auto_keyword", ""),
    ("auto_logs", []),
    ("automation_active", False),
    ("active_tab", "Ofertas"),
    ("llm_backend", get_available_backends()[0]["key"] if get_available_backends() else "ollama"),
]:
    if key not in st.session_state:
        st.session_state[key] = default

configure(st.session_state.llm_backend)

# --- sidebar ---
with st.sidebar:
    st.header("LLM")
    backends = get_available_backends()
    backend_keys = [b["key"] for b in backends]
    current_idx = backend_keys.index(st.session_state.llm_backend) if st.session_state.llm_backend in backend_keys else 0
    selected_idx = st.radio(
        "Proveedor",
        range(len(backends)),
        format_func=lambda i: f"{backends[i]['icon']} {backends[i]['label']}",
        index=current_idx,
        key="backend_selector",
    )
    if backends[selected_idx]["key"] != st.session_state.llm_backend:
        st.session_state.llm_backend = backends[selected_idx]["key"]
configure(st.session_state.llm_backend)

# --- auto-start detection (courtesy of src/auto_starter.py in Docker) ---
if os.getenv("AUTO_START", "false").lower() == "true":
    if "auto_started" not in st.session_state:
        st.session_state.auto_started = True
        st.session_state.automation_active = True
        st.session_state.auto_interval = int(os.getenv("AUTO_INTERVAL", "30"))
        st.session_state.auto_keyword = os.getenv("AUTO_KEYWORD", "")
        st.rerun()

    st.caption(f"modelo: `{backends[selected_idx]['model']}`")

    st.divider()
    st.header("Tu perfil")
    cv_file = st.file_uploader("Sube tu CV (PDF)", type=["pdf"])

    if cv_file is not None:
        with st.spinner("Analizando CV..."):
            pdf_bytes = cv_file.read()
            text = extract_text(pdf_bytes)
            st.session_state.cv_text = text
            level = estimate_candidate_level(text)
            st.session_state.candidate_level = level
            profile = analyze_cv(text)
            st.session_state.cv_profile = profile
        st.success(f"CV analizado. Nivel de inglés: **{level}**")
        profile = st.session_state.cv_profile
        if profile.get("skills"):
            st.caption(f"Skills: {', '.join(profile['skills'][:8])}")
        if profile.get("target_titles"):
            st.caption(f"Cargos: {', '.join(profile['target_titles'][:3])}")
        if profile.get("years_experience"):
            st.caption(f"Experiencia: {profile['years_experience']} años")
        if profile.get("search_keywords"):
            st.caption(f"Keywords: {', '.join(profile['search_keywords'][:5])}")
        if st.session_state.cv_text:
            with st.expander("Ver texto extraído del CV"):
                st.text(st.session_state.cv_text[:1500])

    st.divider()
    st.header("Búsqueda")
    manual_kw = st.text_input("Buscar en internet", placeholder="ej: Python, React, developer...")
    scrape_btn = st.button("Buscar ofertas", type="primary", use_container_width=True)

    if st.session_state.formatted_jobs:
        st.info(f"{len(st.session_state.formatted_jobs)} ofertas cargadas")
    saved_count = count_saved()
    if saved_count:
        st.info(f"⭐ {saved_count} ofertas guardadas")

    st.divider()
    st.header("Filtros")

    f_keyword = st.text_input("Palabra clave", placeholder="filtrar por texto...")

    available_modalities = ["Todas", "Remoto", "Híbrido", "Presencial", "No especificado"]
    f_modality = st.selectbox("Modalidad", available_modalities)

    available_locations = sorted(set(
        (j.get("location") or "").split(",")[0].strip()
        for j in st.session_state.formatted_jobs if (j.get("location") or "").strip()
    ))
    f_locations = st.multiselect("Ubicación", available_locations) if available_locations else []

    f_english = st.multiselect(
        "Nivel de inglés exigido", ["Ninguno", "A1-A2", "B1-B2", "C1-C2"]
    )

    available_companies = sorted(set(
        j.get("company") or "" for j in st.session_state.formatted_jobs
        if (j.get("company") or "").strip() and (j.get("company") or "") != "No disponible"
    ))
    f_companies = st.multiselect("Empresa", available_companies) if available_companies else []

    f_min_salary = st.number_input("Salario mínimo (COP)", min_value=0, value=0, step=500000, format="%d")
    f_max_exp = st.slider(
        "Experiencia máxima (años)", min_value=0, max_value=15, value=15, step=1,
        help="0 = incluir sin requisito explícito",
    )

# --- search / format ---
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

                st.session_state.formatted_jobs = all_formatted
                st.session_state.jobs = all_formatted
                st.session_state.relevant_count = len(relevant_raw)
                st.session_state.other_count = len(other_raw)
            else:
                st.error("No se encontraron ofertas. Intenta de nuevo.")

jobs = st.session_state.formatted_jobs
has_jobs = bool(jobs)
filtered = []
if has_jobs:
    filtered = filter_by_keyword(jobs, f_keyword)
    filtered = filter_by_modality(filtered, f_modality)
    filtered = filter_by_location(filtered, f_locations)
    filtered = filter_by_salary_min(filtered, float(f_min_salary))
    filtered = filter_by_english_level(filtered, f_english)
    filtered = filter_by_companies(filtered, f_companies)
    filtered = filter_by_experience(filtered, f_max_exp if f_max_exp < 15 else None)

def _sort_key_date(j):
    d = (j.get("created_at") or "").strip()
    if d and d != "Fecha desconocida":
        return d
    return "0000-00-00"
if has_jobs:
    filtered.sort(key=_sort_key_date, reverse=True)
    jobs.sort(key=_sort_key_date, reverse=True)

# --- tab navigation ---
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
        st.info(f"""
        ### Bienvenido a JobMatch

        1. **Sube tu CV** en PDF en la barra lateral
        2. Escribe una palabra clave y haz clic en **"Buscar ofertas"**
        3. Navega por las ofertas con sus respectivos links
        4. Guarda tus favoritas con el botón ⭐
        5. Simula una **entrevista** contextualizada

        *Backend: {info['label']}, modelo `{info['model']}`*
        """)
    else:
        if st.session_state.candidate_level:
            relevant = st.session_state.get("relevant_count", 0)
            other = st.session_state.get("other_count", 0)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Ofertas totales", len(jobs))
            c2.metric("Filtradas", len(filtered))
            match_count = sum(1 for j in filtered if j.get("english_match"))
            c3.metric("Match inglés", match_count)
            c4.metric("Tu nivel", st.session_state.candidate_level)
            if relevant:
                st.caption(
                    f"🎯 {relevant} relevantes (analizadas por IA) · "
                    f"📋 {other} adicionales sin procesar"
                )

        st.subheader(f"Ofertas encontradas ({len(filtered)})")

        for idx, j in enumerate(filtered):
            with st.container(border=True):
                cols = st.columns([5, 2, 1])
                url = j.get("url", "")
                title = j.get("title", "Sin título")
                if url:
                    cols[0].markdown(f"### [{title}]({url})", unsafe_allow_html=True)
                else:
                    cols[0].markdown(f"### {title}")
                cols[0].caption(
                    f"{j.get('company', 'No disponible')} · {j.get('location', 'N/A')}"
                )

                eng = j.get("english_level", "Ninguno")
                match = j.get("english_match", False)
                eng_label = f"{eng} ✅ Match" if match else f"{eng}"
                created = j.get("created_at", "")
                date_display = created[:10] if created and created != "Fecha desconocida" else ""
                cols[1].markdown(f"🕐 **{date_display}**" if date_display else "")
                cols[1].markdown(f"**{j.get('modality', 'N/A')}**")
                cols[1].markdown(f"**Inglés:** {eng_label}")

                salary = j.get("salary") or "No disponible"
                if salary != "No disponible":
                    cols[2].metric("Salario", salary.split("-")[0].strip() if "-" in salary else salary)
                else:
                    cols[2].markdown("💰 No especificado")

                dsc = j.get("description_short") or "Sin descripción"
                st.markdown(dsc)
                if url:
                    st.markdown(f"[🔗 Ver oferta original]({url})")

                ikey = f"interview_{idx}_{j.get('title','')}_{j.get('company','')}"
                job_url = j.get("url", "")
                saved = job_url and (job_url in st.session_state.saved_urls or is_saved(job_url))
                skey = f"save_{idx}_{j.get('title','')}"

                cbtn1, cbtn2 = st.columns(2)
                if cbtn1.button("Simular entrevista", key=ikey):
                    st.session_state.interview_job = j
                    st.session_state.interview_history = []
                    st.session_state.active_tab = "Entrevista"
                    st.rerun()
                if saved:
                    if cbtn2.button("💾 Quitar de favoritos", key=skey):
                        unsave_job(job_url)
                        st.session_state.saved_urls.discard(job_url)
                        st.rerun()
                else:
                    if cbtn2.button("⭐ Guardar oferta", key=skey):
                        j.setdefault("created_at", "Fecha desconocida")
                        save_job(j)
                        st.session_state.saved_urls.add(job_url)
                        st.rerun()

# ======================== TAB: Entrevista ========================
elif st.session_state.active_tab == "Entrevista":
    st.subheader("Entrevista simulada")

    if not st.session_state.cv_text:
        st.warning("Primero sube tu CV en la barra lateral.")
    elif not jobs:
        st.warning("Primero busca ofertas en la pestaña 'Ofertas'.")
    else:
        all_titles = [f"{j.get('title','')} - {j.get('company','')}" for j in jobs]
        selected_title = st.selectbox(
            "Selecciona una oferta para la entrevista", all_titles, index=0
        )

        selected_job = None
        if selected_title:
            for j in jobs:
                if f"{j.get('title','')} - {j.get('company','')}" == selected_title:
                    selected_job = j
                    break

        if st.session_state.interview_job:
            selected_job = st.session_state.interview_job

        if selected_job:
            st.info(
                f"**Entrevistando para:** {selected_job.get('title')} "
                f"en {selected_job.get('company')}"
            )

            if st.button("Iniciar / Reiniciar entrevista"):
                with st.spinner("Preparando entrevista..."):
                    first = start_interview(st.session_state.cv_text, selected_job)
                    st.session_state.interview_history = [
                        {"role": "assistant", "content": first}
                    ]
                    st.rerun()

            for msg in st.session_state.interview_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            if st.session_state.interview_history:
                user_answer = st.chat_input("Tu respuesta...")
                if user_answer:
                    st.session_state.interview_history.append(
                        {"role": "user", "content": user_answer}
                    )
                    with st.chat_message("user"):
                        st.markdown(user_answer)
                    with st.spinner("Procesando respuesta..."):
                        reply = continue_interview(
                            st.session_state.cv_text,
                            selected_job,
                            st.session_state.interview_history,
                        )
                        st.session_state.interview_history.append(
                            {"role": "assistant", "content": reply}
                        )
                    st.rerun()
        else:
            st.info("Selecciona una oferta de la lista para comenzar.")

# ======================== TAB: Favoritos ========================
elif st.session_state.active_tab == "Favoritos":
    st.subheader("⭐ Ofertas guardadas")

    saved = get_saved_jobs()
    if not saved:
        st.info(
            "No tienes ofertas guardadas. "
            "Usa el botón ⭐ en la pestaña 'Ofertas' para guardar las que te interesen."
        )
    else:
        st.caption(f"{len(saved)} oferta(s) guardada(s)")
        for s in saved:
            with st.container(border=True):
                cols = st.columns([5, 2, 1])
                url = s.get("url", "")
                title = s.get("title", "Sin título")
                if url:
                    cols[0].markdown(f"### [{title}]({url})", unsafe_allow_html=True)
                else:
                    cols[0].markdown(f"### {title}")
                cols[0].caption(
                    f"{s.get('company','N/A')} · {s.get('location','N/A')} · "
                    f"Publicada: {s.get('created_at','')[:10]}"
                )

                cols[1].markdown(f"**{s.get('modality','N/A')}**")
                cols[1].markdown(f"**Inglés:** {s.get('english_level','N/A')}")
                cols[1].caption(f"Guardada: {s.get('saved_at','')[:10]}")

                salary = s.get("salary") or "No disponible"
                if salary != "No disponible":
                    cols[2].metric(
                        "Salario",
                        salary.split("-")[0].strip() if "-" in salary else salary,
                    )
                else:
                    cols[2].markdown("💰 No especificado")

                dsc = s.get("description_short") or "Sin descripción"
                st.markdown(dsc)
                if url:
                    st.markdown(f"[🔗 Ver oferta original]({url})")

                cbtn1, cbtn2 = st.columns(2)
                if cbtn1.button("Simular entrevista", key=f"iv_saved_{s['id']}"):
                    st.session_state.interview_job = dict(s)
                    st.session_state.interview_history = []
                    st.session_state.active_tab = "Entrevista"
                    st.rerun()
                if cbtn2.button("🗑️ Eliminar de favoritos", key=f"del_saved_{s['id']}"):
                    unsave_job(url)
                    st.session_state.saved_urls.discard(url)
                    st.rerun()

# ======================== TAB: Automatización ========================
elif st.session_state.active_tab == "Automatización":
    st.subheader("⚡ Automatización de búsqueda")

    if not st.session_state.cv_profile or not st.session_state.cv_text:
        st.warning("Primero sube tu CV para configurar la automatización.")
    else:
        st.markdown("""
        La automatización busca ofertas periódicamente con los criterios de tu CV
        y te envía las ofertas nuevas por Telegram.
        """)

        with st.container(border=True):
            st.subheader("🔔 Notificaciones")
            col_tok, col_chat = st.columns(2)
            tg_token = col_tok.text_input(
                "Telegram Bot Token",
                type="password",
                value=os.getenv("TELEGRAM_BOT_TOKEN", ""),
                help="Crea un bot con @BotFather en Telegram",
                key="tg_token_input",
            )
            tg_chat = col_chat.text_input(
                "Telegram Chat ID",
                value=os.getenv("TELEGRAM_CHAT_ID", ""),
                help="Envía /start a tu bot y luego visita https://api.telegram.org/bot<TOKEN>/getUpdates",
                key="tg_chat_input",
            )
            col_test, col_empty = st.columns([1, 2])
            if col_test.button("🔔 Probar notificación", use_container_width=True):
                if automation.test_telegram(tg_token, tg_chat):
                    st.success("Notificación enviada. Revisa Telegram.")
                else:
                    st.error("Error al enviar. Verifica token y chat ID.")

        with st.container(border=True):
            st.subheader("📅 Intervalo")
            col_int, col_kw = st.columns(2)
            interval = col_int.number_input(
                "Minutos entre búsquedas",
                min_value=5, max_value=720, value=st.session_state.auto_interval,
                step=5, key="auto_interval_input",
            )
            auto_kw = col_kw.text_input(
                "Keyword adicional (opcional)",
                value=st.session_state.get("auto_keyword", ""),
                placeholder="ej: Python",
                key="auto_keyword_input",
            )

        st.divider()

        is_running = automation.is_automation_running() or os.path.exists("/app/data/auto_starter.pid")
        status_badge = "🟢 Corriendo" if is_running else "⚪ Detenida"
        st.caption(f"Estado: {status_badge}")
        if os.getenv("AUTO_START", "false").lower() == "true":
            st.caption(f"⏱ Búsqueda automática cada {st.session_state.auto_interval} min · keywords: {st.session_state.auto_keyword}")

        col_start, col_stop, _ = st.columns([1, 1, 3])
        if col_start.button("▶️ Iniciar automatización", type="primary",
                            use_container_width=True, disabled=is_running):
            if not tg_token or not tg_chat:
                st.error("Configura el token y chat ID de Telegram primero.")
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
                    profile=st.session_state.cv_profile,
                    keyword=auto_kw,
                    interval_minutes=interval,
                    log_callback=log,
                    telegram_token=tg_token,
                    telegram_chat_id=tg_chat,
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
            with st.expander(f"📋 Log ({len(st.session_state.auto_logs)} eventos)"):
                for log_line in reversed(st.session_state.auto_logs[-20:]):
                    st.text(log_line)

        st.divider()
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

    if st.session_state.cv_text:
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Nivel de inglés estimado",
                      st.session_state.candidate_level or "No analizado")
        with c2:
            st.metric("Ofertas disponibles", len(st.session_state.formatted_jobs))

        if st.session_state.formatted_jobs:
            match_count = sum(1 for j in st.session_state.formatted_jobs
                              if j.get("english_match"))
            st.progress(match_count / max(len(st.session_state.formatted_jobs), 1))
            st.caption(
                f"{match_count} de {len(st.session_state.formatted_jobs)} "
                "ofertas compatibles con tu nivel de inglés"
            )

            st.subheader("Distribución por nivel de inglés")
            levels_count = {}
            for j in st.session_state.formatted_jobs:
                lvl = j.get("english_level", "Ninguno")
                levels_count[lvl] = levels_count.get(lvl, 0) + 1
            for lvl in ["Ninguno", "A1", "A2", "B1", "B2", "C1", "C2"]:
                if lvl in levels_count:
                    st.markdown(f"- **{lvl}**: {levels_count[lvl]} ofertas")

            with st.expander("Ver texto completo del CV"):
                st.text(st.session_state.cv_text)
    else:
        st.info("Sube tu CV en la barra lateral para ver el resumen.")