from src.llm import chat_json

SYSTEM = """You are a CV/resume analyzer. Given a CV text, extract a structured
professional profile. Return ONLY valid JSON:

{
  "skills": ["skill1", "skill2", ...],
  "target_titles": ["job title 1", "job title 2", ...],
  "years_experience": number,
  "education": "Bachiller|Tecnico|Tecnologo|Profesional|Especializacion|Maestria|Doctorado",
  "search_keywords": ["kw1", "kw2", "kw3"]
}

Rules:
- skills: max 10 most relevant technical/professional skills (language, framework, tool names)
- target_titles: 2-4 job titles the candidate would apply for (e.g. "Desarrollador Backend Python")
- years_experience: estimate total professional experience in years (integer)
- education: highest level completed
- search_keywords: 3-5 broad terms for searching job portals (e.g. "python", "react", "backend")
- If a field cannot be determined, use an empty array/0/default"""


def analyze_cv(cv_text: str) -> dict:
    if not cv_text.strip():
        return _empty_profile()

    prompt = f"CV:\n{cv_text[:4000]}\n\nExtract the professional profile as JSON."
    result = chat_json(prompt, SYSTEM, temperature=0.1)

    if not isinstance(result, dict):
        return _empty_profile()

    profile = {
        "skills": _ensure_list(result.get("skills"), []),
        "target_titles": _ensure_list(result.get("target_titles"), []),
        "years_experience": _ensure_int(result.get("years_experience"), 0),
        "education": result.get("education", "Profesional"),
        "search_keywords": _ensure_list(result.get("search_keywords"), []),
    }
    return profile


def _empty_profile() -> dict:
    return {
        "skills": [],
        "target_titles": [],
        "years_experience": 0,
        "education": "Profesional",
        "search_keywords": [],
    }


def _ensure_list(val, default):
    return val if isinstance(val, list) else default


def _ensure_int(val, default):
    try:
        return int(val)
    except (TypeError, ValueError):
        return default
