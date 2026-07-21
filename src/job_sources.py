import json
import os
import re
import requests
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup


MOCK_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "mock_jobs.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )
}
SCRAPE_TIMEOUT = 15
_TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _extract_date(text: str) -> str:
    patterns = [
        (r"hoy", 0),
        (r"ayer", 1),
        (r"hace\s+(\d+)\s+d[ií]as?", lambda m: int(m.group(1))),
        (r"publicad[oa].*?(\d{1,2}\s+(?:ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\w*\s+\d{4})", None),
    ]
    for pattern, offset_fn in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if offset_fn is None:
                return match.group(1)
            days = offset_fn(match) if callable(offset_fn) else offset_fn
            dt = datetime.now(timezone.utc)
            if isinstance(days, int):
                dt = dt - timedelta(days=days)
            return dt.strftime("%Y-%m-%d")
    return _TODAY


# ============================================================
#  Scraper: Computrabajo Colombia
# ============================================================
def _scrape_computrabajo(keyword: str = "") -> list[dict]:
    url = f"https://www.computrabajo.com.co/ofertas-de-trabajo/?q={keyword or ''}"
    raw = []
    resp = requests.get(url, headers=HEADERS, timeout=SCRAPE_TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    cards = soup.select("article") or soup.select("a.js-o-link")
    for card in cards[:25]:
        try:
            title_el = card.select_one("a.js-o-link")
            if title_el is None and card.name == "a" and "js-o-link" in (card.get("class") or []):
                title_el = card
            if title_el is None:
                title_el = card.find("a")
            if title_el is None:
                continue
            title = title_el.get_text(strip=True)
            if not title:
                continue
            link = title_el.get("href", "")
            if link and not link.startswith("http"):
                link = "https://www.computrabajo.com.co" + link
            text = card.get_text(separator=" ", strip=True)
            raw.append({
                "title": title,
                "raw_text": text[:2000],
                "url": link,
                "source": "computrabajo.com.co",
                "created_at": _extract_date(text),
            })
        except Exception:
            continue
    return raw


# ============================================================
#  Scraper: ElEmpleo.com Colombia
# ============================================================
def _scrape_elempleo(keyword: str = "") -> list[dict]:
    url = f"https://www.elempleo.com/co/ofertas-empleo/?q={keyword or ''}"
    raw = []
    resp = requests.get(url, headers=HEADERS, timeout=SCRAPE_TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    links = soup.find_all("a", href=True)
    seen = set()
    for a in links:
        try:
            href = a.get("href", "")
            title = a.get_text(strip=True)
            if "/co/ofertas-trabajo/" not in href or not title:
                continue
            if title == "Ver oferta" or "whatsapp" in href.lower():
                continue
            if href in seen:
                continue
            seen.add(href)
            if not href.startswith("http"):
                href = "https://www.elempleo.com" + href
            parent = a.find_parent(["div", "article", "li"])
            raw_text = parent.get_text(separator=" ", strip=True) if parent else title
            raw.append({
                "title": title,
                "raw_text": raw_text[:2000],
                "url": href,
                "source": "elempleo.com",
                "created_at": _extract_date(raw_text),
            })
        except Exception:
            continue
        if len(raw) >= 20:
            break
    return raw


# ============================================================
#  Aggregator
# ============================================================
PROVIDERS = [
    ("computrabajo", _scrape_computrabajo),
    ("elempleo", _scrape_elempleo),
]


def get_jobs(keyword: str = "") -> list[dict]:
    raw = []
    for name, scraper in PROVIDERS:
        try:
            results = scraper(keyword)
            print(f"[scraper] {name}: {len(results)} jobs")
            raw.extend(results)
        except Exception as e:
            print(f"[scraper] {name}: FAILED ({e})")
    if not raw:
        raw = _load_mock()
    return raw


def _load_mock() -> list[dict]:
    if not os.path.exists(MOCK_PATH):
        return []
    with open(MOCK_PATH, "r") as f:
        data = json.load(f)
    for d in data:
        d.setdefault("url", "")
        d.setdefault("source", "mock")
        d.setdefault("created_at", _TODAY)
    return data