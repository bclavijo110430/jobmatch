# 💼 JobMatch — Smart Job Search

Plataforma inteligente de búsqueda de empleo que analiza tu CV, busca ofertas en múltiples portales colombianos, las filtra por relevancia usando IA local y te notifica automáticamente por Telegram.

## 🎯 Funcionalidades

| Feature | Descripción |
|---|---|
| 📄 **Análisis de CV** | Extrae skills, cargo objetivo, años de experiencia y nivel de inglés desde PDF |
| 🔍 **Búsqueda multi-proveedor** | Computrabajo + Elempleo Colombia (~40 ofertas por búsqueda) |
| 🤖 **Formateo con LLM** | IA estructura ofertas crudas → JSON (título, empresa, salario, modalidad, inglés, url) |
| 🎯 **Filtro por relevancia** | Solo las ofertas que coinciden con skills/cargo del CV pasan al LLM (ahorro de tokens) |
| 📋 **Filtros avanzados** | Palabra clave, modalidad, ubicación, salario mínimo, nivel de inglés, empresa, experiencia |
| ⭐ **Ofertas guardadas** | Base de datos SQLite para favoritos con fechas de publicación y guardado |
| 🎤 **Entrevista simulada** | LLM actúa como reclutador contextualizado al CV + oferta seleccionada |
| ⚡ **Automatización** | Búsqueda automática cada X minutos con IA + notificaciones por Telegram |
| 🧠 **Filtro IA por keyword** | La automatización usa el LLM para filtrar ofertas semánticamente por `AUTO_KEYWORD` (seniority, rol, stack) antes de notificar |
| 🔄 **Dual LLM backend** | Ollama (local) o FreeLLMAPI (28 proveedores cloud gratuitos) — switch en vivo desde la UI |

## 🛠 Stack

| Componente | Tecnología |
|---|---|
| UI | Python 3.12 + Streamlit |
| LLM | OpenAI-compatible (`/v1/chat/completions`) |
| Backends LLM | Ollama (`llama3.2:3b`) · FreeLLMAPI (`auto`) |
| PDF parsing | PyMuPDF |
| Scraping | requests + BeautifulSoup (Computrabajo, Elempleo) |
| Base de datos | SQLite (ofertas guardadas + notificadas) |
| Notificaciones | Telegram Bot API |
| Despliegue | Docker + Docker Compose |
| Orquestación | Makefile |

## 🚀 Quick Start

```bash
# Modo completo (ollama + freellmapi + app)
make start-all

# O solo modo básico (ollama + app)
make start
```

Abre `http://localhost:8501`.

### Makefile

| Comando | Descripción |
|---|---|
| `make start` | Levanta Ollama + app (1 solo comando) |
| `make start-all` | Levanta Ollama + FreeLLMAPI + app |
| `make stop` | Detiene todos los servicios |
| `make build` | Construye la imagen Docker |
| `make up` | Solo la app (ya debes tener Ollama corriendo) |
| `make down` | Detiene la app |
| `make logs` | Logs en tiempo real |
| `make shell` | Bash dentro del contenedor |
| `make run-local` | Streamlit sin Docker |
| `make ollama-pull` | Descarga `llama3.2:3b` |
| `make clean` | Limpia todo (imágenes, volúmenes) |

## ⚙️ Configuración (`.env`)

```env
# ========== Ollama (local) ==========
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.2:3b

# ========== FreeLLMAPI (cloud) ==========
FREELLMAPI_BASE_URL=http://localhost:3001/v1
FREELLMAPI_API_KEY=
FREELLMAPI_MODEL=auto

# ========== Telegram Notifications ==========
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# ========== Automatización ==========
AUTO_START=true
AUTO_INTERVAL=5
AUTO_KEYWORD=devops sr,devops,desecopsvops,intermedio,devops semi senior,SRE,mlops
NOTIFIED_TTL_MINUTES=1440

# ========== Legacy ==========
LLM_BASE_URL=http://localhost:3001/v1
LLM_API_KEY=freellmapi-xxxxxxxx
LLM_MODEL=auto
```

El selector de LLM en la barra lateral permite cambiar entre Ollama y FreeLLMAPI en tiempo real.

## 📁 Arquitectura

```
jobmatch/
├── app.py                  # UI Streamlit (5 pestañas)
├── entrypoint.sh           # Entrypoint Docker (auto-starter + Streamlit)
├── Dockerfile              # python:3.12-slim
├── docker-compose.yml      # app + freellmapi (profile)
├── Makefile                # Orquestación
├── requirements.txt        # streamlit, requests, bs4, lxml, pymupdf
├── .env.example
├── data/
│   └── mock_jobs.json      # 25 ofertas Colombia (fallback)
└── src/
    ├── __init__.py
    ├── llm.py              # Cliente OpenAI-compatible dual-backend
    ├── cv_parser.py        # PyMuPDF → extracción de texto del CV
    ├── cv_analyzer.py      # LLM extrae skills, cargo, experiencia, keywords
    ├── job_sources.py      # Scrapers: Computrabajo + Elempleo + mock fallback
    ├── formatter.py        # LLM normaliza ofertas crudas → JSON estructurado
    ├── filters.py          # Filtros: país, modalidad, salario, inglés, relevancia CV
    ├── english.py          # LLM estima nivel de inglés (candidato + ofertas)
    ├── interview.py        # Entrevista simulada con reclutador LLM
    ├── database.py         # SQLite: ofertas guardadas + notificadas
    ├── automation.py       # Background thread: búsqueda automática + filtro IA por keyword + Telegram
    └── auto_starter.py     # Proceso standalone para auto-start en Docker
```

## 🔄 Flujo de búsqueda

```
CV (PDF)
  │
  ├── cv_parser.py → texto
  ├── cv_analyzer.py → {skills, target_titles, years, education, keywords}
  └── english.py → nivel de inglés
        │
        ▼
job_sources.py → Computrabajo (20) + Elempleo (20) → ~40 ofertas crudas
        │
        ▼ (solo en automatización)
   automation.py →_ai_filter_by_keywords() → LLM compara con AUTO_KEYWORD → ~10-15 ofertas
        │
        ▼
   filters.py → filter_by_cv_relevance() → relevantes / no relevantes
        │                    │
        ▼                    ▼
  formatter.py (LLM)     sin procesar
  english.py              (datos básicos)
  filter_by_country()
        │
        ▼
  Ofertas formateadas → UI (pestaña Ofertas)
        │
        ├── ⭐ Guardar → SQLite (pestaña Favoritos)
        └── 🎤 Entrevista → LLM recruiter (pestaña Entrevista)
```

## 🤖 Automatización

La pestaña **Automatización** programa búsquedas periódicas con los criterios del CV y `AUTO_KEYWORD`:

1. Cada N minutos (mín. 1 min) busca en Computrabajo + Elempleo (~40 ofertas crudas)
2. **Filtro IA por keyword**: envía las ofertas en lotes de 20 al LLM con las keywords de `AUTO_KEYWORD` (p.ej. `devops sr`, `SRE`, `mlops`, `intermedio`). La IA devuelve los índices que coinciden semánticamente (entiende seniority `sr/semi senior/intermedio/junior`, rol y stack), más allá de coincidencias exactas de texto. Si la API falla, conserva el lote completo para no perder ofertas.
3. Filtra por skills/cargo del CV con `filter_by_cv_relevance()` (solo relevantes)
4. Formatea con LLM, enriquece nivel de inglés y filtra por país/modalidad
5. Envía por Telegram solo las **ofertas nuevas** (no notificadas antes)
6. Dedup con **TTL**: una URL no se re-notifica hasta que pasen `NOTIFIED_TTL_MINUTES` (default 1440 = 24 h). Pasado el TTL puede volver a notificarse.
7. Se inicia automáticamente con el contenedor si `AUTO_START=true`

### Variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `AUTO_START` | `false` | Arranca la automatización al levantar el contenedor |
| `AUTO_INTERVAL` | `30` | Minutos entre búsquedas (mín. 1) |
| `AUTO_KEYWORD` | — | keywords separadas por coma para el filtro IA |
| `NOTIFIED_TTL_MINUTES` | `1440` | minutos de TTL del dedup (24 h por defecto) |

### Controles en la UI

- **▶️ Iniciar / ⏹️ Detener**: arranca/para el thread en vivo.
- **🧹 Resetear**: borra el historial de URLs ya notificadas (para testing inmediato o forzar reenvío).
- **🔔 Probar notificación**: envía un mensaje de prueba a Telegram.

### Configurar Telegram

1. Crea un bot con [@BotFather](https://t.me/BotFather) → `/newbot`
2. Copia el token y pégalo en `.env` como `TELEGRAM_BOT_TOKEN`
3. Inicia chat con tu bot y envía un mensaje
4. Visita `https://api.telegram.org/bot<TOKEN>/getUpdates` para obtener tu `chat.id`
5. Pega el chat ID en `.env` como `TELEGRAM_CHAT_ID`

## 🎨 UI Design

- Tema oscuro monocromático (purple tones: `#3b1f8a` → `#7c5ce7`)
- Sticky navbar con glass effect (blur backdrop)
- Cards con hover glow morado
- Métricas con gradiente glass
- Botones pill redondeados con gradiente
- Scrollbar estilizada
- Selector de backend LLM en vivo desde la sidebar

## 📝 Notas

- Sin GPU: `llama3.2:3b` vs CPU (~5-15s por llamada). FreeLLMAPI es más rápido.
- El scraper puede ser bloqueado → fallback automático a `mock_jobs.json` (25 ofertas)
- La DB (`saved_jobs.db`) persiste en volumen Docker (`jobmatch-data`)
- `network_mode: host` para alcanzar Ollama y FreeLLMAPI del host
- Las ofertas no relevantes se muestran sin procesamiento LLM (ahorro de tokens)