from src.llm import chat

SYSTEM_INTERVIEWER = """You are a professional recruiter conducting a job interview.
You have the candidate's CV and the job offer details. Ask relevant technical and
behavioral questions one at a time. After the candidate answers, give brief feedback
and ask the next question. Keep questions concise. Do NOT answer for the candidate.
After 5 questions, wrap up and give a final assessment.

IMPORTANT: Respond naturally, do NOT use JSON. Just talk like a real recruiter."""


def build_interview_context(cv_text: str, job: dict) -> str:
    return (
        f"CANDIDATE CV:\n{cv_text[:2000]}\n\n"
        f"JOB OFFER:\n"
        f"Title: {job.get('title', 'N/A')}\n"
        f"Company: {job.get('company', 'N/A')}\n"
        f"Description: {job.get('description_short', 'N/A')}\n"
        f"Modality: {job.get('modality', 'N/A')}\n"
        f"Location: {job.get('location', 'N/A')}\n"
        f"Salary: {job.get('salary', 'N/A')}\n"
        f"English required: {job.get('english_level', 'N/A')}\n"
        f"URL: {job.get('url', 'N/A')}"
    )


def start_interview(cv_text: str, job: dict) -> str:
    ctx = build_interview_context(cv_text, job)
    prompt = (
        f"{ctx}\n\n"
        "Begin the interview. Greet the candidate and ask your first question."
    )
    return chat(prompt, SYSTEM_INTERVIEWER, temperature=0.7)


def continue_interview(cv_text: str, job: dict, history: list[dict]) -> str:
    ctx = build_interview_context(cv_text, job)
    history_text = "\n".join(
        [f"{'Interviewer' if m['role']=='assistant' else 'Candidate'}: {m['content']}"
         for m in history[-6:]]
    )
    prompt = (
        f"{ctx}\n\nINTERVIEW SO FAR:\n{history_text}\n\n"
        f"Continue the interview. Respond to the candidate's last answer "
        f"and ask the next question if appropriate."
    )
    return chat(prompt, SYSTEM_INTERVIEWER, temperature=0.7)
