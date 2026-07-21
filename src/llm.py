import json
import os
import requests
import re

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

FREELLMAPI_BASE_URL = os.getenv("FREELLMAPI_BASE_URL", "http://localhost:3001/v1").rstrip("/")
FREELLMAPI_API_KEY = os.getenv("FREELLMAPI_API_KEY", "")
FREELLMAPI_MODEL = os.getenv("FREELLMAPI_MODEL", "auto")

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1").rstrip("/")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2:3b")

_backend = "ollama"
if "3001" in LLM_BASE_URL or "freellmapi" in LLM_BASE_URL.lower():
    _backend = "freellmapi"
elif "11434" in LLM_BASE_URL or "ollama" in LLM_BASE_URL.lower():
    _backend = "ollama"

BACKENDS = {
    "ollama": {
        "base_url": OLLAMA_BASE_URL,
        "api_key": "",
        "model": OLLAMA_MODEL,
        "label": "Ollama (local)",
        "icon": "🟢",
    },
    "freellmapi": {
        "base_url": FREELLMAPI_BASE_URL,
        "api_key": FREELLMAPI_API_KEY,
        "model": FREELLMAPI_MODEL,
        "label": "FreeLLMAPI (cloud)",
        "icon": "🔵",
    },
}

_ollama_changed = False
if LLM_BASE_URL != "http://localhost:11434/v1":
    cleaned = LLM_BASE_URL.lower().replace("https://", "").replace("http://", "")
    if "11434" in cleaned or "ollama" in cleaned:
        BACKENDS["ollama"]["base_url"] = LLM_BASE_URL
        _ollama_changed = True
    elif "3001" in cleaned or "freellmapi" in cleaned:
        BACKENDS["freellmapi"]["base_url"] = LLM_BASE_URL
if LLM_MODEL != "llama3.2:3b" and LLM_MODEL != "auto":
    BACKENDS["ollama"]["model"] = LLM_MODEL
    _ollama_changed = True
if LLM_API_KEY:
    if LLM_API_KEY.startswith("freellmapi-"):
        BACKENDS["freellmapi"]["api_key"] = LLM_API_KEY
    elif LLM_API_KEY.startswith("sk-"):
        BACKENDS["ollama"]["api_key"] = LLM_API_KEY
        _ollama_changed = True
if _ollama_changed:
    BACKENDS["ollama"]["label"] = "Ollama (custom)"


def configure(backend: str) -> None:
    global _backend
    if backend in BACKENDS:
        _backend = backend


def _cfg() -> dict:
    return BACKENDS[_backend]


def _headers() -> dict:
    h = {"Content-Type": "application/json"}
    key = _cfg()["api_key"]
    if key:
        h["Authorization"] = f"Bearer {key}"
    return h


def _call_llm(prompt: str, system: str = "", temperature: float = 0.1) -> str:
    cfg = _cfg()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": temperature,
        "stream": False,
    }
    try:
        resp = requests.post(
            f"{cfg['base_url']}/chat/completions",
            json=payload,
            headers=_headers(),
            timeout=180,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"ERROR: {e}"


def extract_json(text: str) -> dict | list | None:
    text = (text or "").strip()
    if not text:
        return None
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


def chat(prompt: str, system: str = "", temperature: float = 0.3) -> str:
    return _call_llm(prompt, system, temperature).strip()


def chat_json(prompt: str, system: str = "", temperature: float = 0.1) -> dict | list | None:
    full_system = system + "\n\nRespond ONLY with valid JSON. No explanations, no markdown."
    raw = _call_llm(prompt, full_system, temperature)
    return extract_json(raw)


def validate_connection(backend: str | None = None) -> dict:
    cfg = BACKENDS[backend or _backend]
    try:
        resp = requests.get(
            f"{cfg['base_url']}/models",
            headers={"Authorization": f"Bearer {cfg['api_key']}"} if cfg["api_key"] else {},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            model_list = []
            if "data" in data:
                model_list = [m.get("id", "") for m in data["data"][:5]]
            return {"ok": True, "models": model_list}
        return {"ok": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_available_backends() -> list[dict]:
    result = []
    for key, cfg in BACKENDS.items():
        result.append({
            "key": key,
            "label": cfg["label"],
            "icon": cfg["icon"],
            "model": cfg["model"],
            "base_url": cfg["base_url"],
            "has_key": bool(cfg["api_key"]),
            "active": _backend == key,
        })
    return result


def get_current_backend() -> str:
    return _backend


def get_provider_info() -> dict:
    cfg = _cfg()
    return {
        "backend": _backend,
        "label": f"{cfg['icon']} {cfg['label']}",
        "model": cfg["model"],
        "base_url": cfg["base_url"],
        "has_key": bool(cfg["api_key"]),
    }