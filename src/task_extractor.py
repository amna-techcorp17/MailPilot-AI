import re

from src.llm import has_api_key, invoke_prompt
from src.prompts import TASK_PROMPT
from src.utils import bulletize


def extract_tasks(email: str, temperature: float = 0.4) -> str:
    if has_api_key():
        return invoke_prompt(TASK_PROMPT, email=email, temperature=temperature)
    return _tasks_demo(email)


def _tasks_demo(email: str) -> str:
    text = email.strip()
    candidates = []

    deadline_match = re.search(
        r"\b(by|before|on|next|this)\s+([A-Z]?[a-z]+day|week|month|\d{1,2}(?:st|nd|rd|th)?)",
        text,
        flags=re.IGNORECASE,
    )
    if deadline_match:
        candidates.append(f"Confirm deadline around {deadline_match.group(0)}.")

    if re.search(r"\b(schedule|meeting|call|available|calendar)\b", text, flags=re.IGNORECASE):
        candidates.append("Schedule or confirm the meeting time.")

    if re.search(r"\b(send|share|provide|attach|proposal|timeline|update)\b", text, flags=re.IGNORECASE):
        candidates.append("Prepare and send the requested information or update.")

    if re.search(r"\b(order|refund|issue|problem|support)\b", text, flags=re.IGNORECASE):
        candidates.append("Investigate the issue and respond with a clear resolution path.")

    return bulletize(candidates)
