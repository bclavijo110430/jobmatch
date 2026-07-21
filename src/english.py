from src.llm import chat_json


SYSTEM_CANDIDATE = """You analyze CVs. Determine the candidate's English level.
Return JSON: {"english_level": "Ninguno"|"A1"|"A2"|"B1"|"B2"|"C1"|"C2", "reason": "short justification"}"""

SYSTEM_OFFER = """You analyze job descriptions. Determine the minimum English level required.
Return JSON: {"english_level": "Ninguno"|"A1"|"A2"|"B1"|"B2"|"C1"|"C2", "confidence": "high"|"medium"|"low"}
If English is not mentioned or not required, return "Ninguno".""" 

LEVELS = ["Ninguno", "A1", "A2", "B1", "B2", "C1", "C2"]


def estimate_candidate_level(cv_text: str) -> str:
    if not cv_text.strip():
        return "Ninguno"
    prompt = f"CV:\n{cv_text[:3000]}\n\nWhat is the candidate's English level?"
    result = chat_json(prompt, SYSTEM_CANDIDATE)
    if isinstance(result, dict):
        lvl = result.get("english_level", "Ninguno")
        return lvl if lvl in LEVELS else "Ninguno"
    return "Ninguno"


def estimate_offer_level(description_short: str = "", title: str = "") -> str:
    description_short = (description_short or "")
    title = title or ""
    text = f"Title: {title}\nDescription: {description_short[:1500]}"
    prompt = f"Job:\n{text}\n\nWhat minimum English level is required?"
    result = chat_json(prompt, SYSTEM_OFFER)
    if isinstance(result, dict):
        lvl = result.get("english_level", "Ninguno")
        return lvl if lvl in LEVELS else "Ninguno"
    return "Ninguno"


def enrich_offers_with_english(jobs: list[dict]) -> list[dict]:
    for j in jobs:
        english_level = j.get("english_level")
        if english_level is None or english_level == "No especificado":
            lvl = estimate_offer_level(
                j.get("description_short") or "",
                j.get("title") or ""
            )
            j["english_level"] = lvl
    return jobs
