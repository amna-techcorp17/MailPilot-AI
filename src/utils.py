import re

from pydantic import BaseModel


class EmailAnalysis(BaseModel):
    category: str
    urgency: str
    summary: str
    reply: str
    followup: str
    tasks: str
    demo_mode: bool = False


def normalize_label(value: str, allowed: list[str], fallback: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z ]", "", value or "").strip().lower()
    for label in allowed:
        if cleaned == label.lower():
            return label
        if label.lower() in cleaned:
            return label
    return fallback


def compact_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def first_sentence(value: str, max_chars: int = 190) -> str:
    text = compact_text(value)
    if not text:
        return ""
    match = re.search(r"(.+?[.!?])(?:\s|$)", text)
    sentence = match.group(1) if match else text
    if len(sentence) > max_chars:
        return sentence[: max_chars - 3].rstrip() + "..."
    return sentence


def bulletize(items: list[str]) -> str:
    clean_items = [compact_text(item) for item in items if compact_text(item)]
    if not clean_items:
        return "- No clear action items found."
    return "\n".join(f"- {item}" for item in clean_items)
