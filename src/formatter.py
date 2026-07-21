from src.llm import chat_json
import time

SYSTEM = """You are a job offer parser. Given raw text scraped from job boards,
extract structured data. Return a JSON array. Each object must have:
  - title: string
  - company: string (if not found use "No disponible")
  - salary: string (include currency if found, otherwise "No disponible")
  - modality: one of "Remoto", "Híbrido", "Presencial", "No especificado"
  - location: string (city, department)
  - country: "Colombia" or the country mentioned
  - description_short: string (1-2 sentences, max 150 chars)
  - english_level: one of "Ninguno", "A1", "A2", "B1", "B2", "C1", "C2"
  - url: string (original link, if present)
  - source: string
  - created_at: string (ISO date YYYY-MM-DD if found in text, otherwise "Fecha desconocida")

If a field is missing use reasonable defaults. Output ONLY valid JSON."""


def format_jobs(raw_jobs: list[dict]) -> list[dict]:
    if not raw_jobs:
        return []
    batch_size = 5
    all_formatted = []
    for i in range(0, len(raw_jobs), batch_size):
        batch = raw_jobs[i : i + batch_size]
        prompt_lines = []
        for j, job in enumerate(batch):
            prompt_lines.append(
                f"--- OFFER {j+1} ---\nTitle: {job.get('title','')}\n"
                f"URL: {job.get('url','')}\nSource: {job.get('source','')}\n"
                f"Scraped date hint: {job.get('created_at','')}\n"
                f"Text: {job.get('raw_text','')[:1500]}"
            )
        prompt = "Format these job offers to JSON:\n\n" + "\n".join(prompt_lines)
        result = chat_json(prompt, SYSTEM)
        if isinstance(result, list):
            all_formatted.extend(result)
        elif isinstance(result, dict):
            all_formatted.append(result)
        time.sleep(0.5)
    return all_formatted
