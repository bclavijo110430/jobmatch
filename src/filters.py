import re

LEVELS = ["Ninguno", "A1", "A2", "B1", "B2", "C1", "C2"]


def filter_by_country(jobs: list[dict], country: str = "Colombia") -> list[dict]:
    c = country.lower()
    return [
        j for j in jobs
        if c in (j.get("country") or "").lower()
        or c in (j.get("location") or "").lower()
    ]


def filter_by_modality(jobs: list[dict], modality: str | None = None) -> list[dict]:
    if not modality or modality == "Todas":
        return jobs
    modalities = [m.strip().lower() for m in modality.split(",")]
    return [j for j in jobs if (j.get("modality") or "").lower() in modalities]


def filter_by_keyword(jobs: list[dict], keyword: str = "") -> list[dict]:
    if not keyword:
        return jobs
    kw = keyword.lower()
    result = []
    for j in jobs:
        if kw in (j.get("title") or "").lower():
            result.append(j)
            continue
        if kw in (j.get("description_short") or "").lower():
            result.append(j)
            continue
        if kw in (j.get("company") or "").lower():
            result.append(j)
    return result


def filter_by_location(jobs: list[dict], locations: list[str] | None = None) -> list[dict]:
    if not locations:
        return jobs
    locs_lower = [l.lower().strip() for l in locations if l.strip()]
    if not locs_lower:
        return jobs
    return [j for j in jobs
            if any(loc in (j.get("location") or "").lower() for loc in locs_lower)]


def _parse_salary_min(salary_str: str) -> float:
    if not salary_str or salary_str == "No disponible":
        return 0.0
    numbers = re.findall(r"[\d.]+", salary_str.replace(",", ""))
    if not numbers:
        return 0.0
    raw = numbers[0]
    if raw.count(".") > 1:
        raw = raw.replace(".", "")
    try:
        return float(raw)
    except ValueError:
        return 0.0


def filter_by_salary_min(jobs: list[dict], min_salary: float = 0) -> list[dict]:
    if min_salary <= 0:
        return jobs
    return [j for j in jobs if _parse_salary_min(j.get("salary") or "") >= min_salary]


def filter_by_english_level(jobs: list[dict], selected_levels: list[str] | None = None) -> list[dict]:
    if not selected_levels:
        return jobs
    expanded = set()
    groups = {"A1-A2": ["A1", "A2"], "B1-B2": ["B1", "B2"], "C1-C2": ["C1", "C2"]}
    for lvl in selected_levels:
        if lvl in groups:
            expanded.update(groups[lvl])
        else:
            expanded.add(lvl)
    return [j for j in jobs if (j.get("english_level") or "Ninguno") in expanded]


def filter_by_companies(jobs: list[dict], companies: list[str] | None = None) -> list[dict]:
    if not companies:
        return jobs
    comps_lower = [c.lower().strip() for c in companies if c.strip()]
    if not comps_lower:
        return jobs
    return [j for j in jobs
            if any(c in (j.get("company") or "").lower() for c in comps_lower)]


def filter_by_experience(jobs: list[dict], max_years: int | None = None) -> list[dict]:
    if max_years is None or max_years <= 0:
        return jobs
    result = []
    for j in jobs:
        text = ((j.get("description_short") or "") + " " + (j.get("title") or "")).lower()
        years = re.findall(r"(\d+)\+?\s*(?:años|years)", text)
        if not years:
            result.append(j)
            continue
        try:
            y = int(years[0])
            if y <= max_years:
                result.append(j)
        except ValueError:
            result.append(j)
    return result


def add_match_flag(jobs: list[dict], candidate_english: str | None) -> list[dict]:
    if candidate_english not in LEVELS:
        candidate_english = "Ninguno"
    cand_idx = LEVELS.index(candidate_english)
    for j in jobs:
        req = j.get("english_level") or "Ninguno"
        if req not in LEVELS:
            req = "Ninguno"
        req_idx = LEVELS.index(req)
        j["english_match"] = cand_idx >= req_idx
    return jobs


def filter_by_cv_relevance(jobs: list[dict], profile: dict) -> tuple[list[dict], list[dict]]:
    skills = [s.lower().strip() for s in (profile.get("skills") or []) if s.strip()]
    titles = [t.lower().strip() for t in (profile.get("target_titles") or []) if t.strip()]
    keywords = [k.lower().strip() for k in (profile.get("search_keywords") or []) if k.strip()]

    has_profile = bool(skills or titles or keywords)
    if not has_profile:
        return list(jobs), []

    relevant = []
    other = []
    for j in jobs:
        text = ((j.get("title") or "") + " " + (j.get("raw_text") or "")).lower()
        score = 0
        if any(t in text for t in titles):
            score += 3
        if any(s in text for s in skills):
            score += 2
        if any(k in text for k in keywords):
            score += 1
        if score > 0:
            j["_relevance_score"] = score
            relevant.append(j)
        else:
            other.append(j)
    relevant.sort(key=lambda j: j.get("_relevance_score", 0), reverse=True)
    return relevant, other
