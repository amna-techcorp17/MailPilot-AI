import re

from src.llm import has_api_key, invoke_prompt
from src.prompts import CLASSIFICATION_PROMPT, EMAIL_CATEGORIES, URGENCY_LEVELS, URGENCY_PROMPT
from src.utils import normalize_label


def classify_email(email: str) -> str:
    if has_api_key():
        result = invoke_prompt(CLASSIFICATION_PROMPT, email=email)
        return normalize_label(result, EMAIL_CATEGORIES, "Support Request")
    return _classify_demo(email)


def detect_urgency(email: str) -> str:
    if has_api_key():
        result = invoke_prompt(URGENCY_PROMPT, email=email)
        return normalize_label(result, URGENCY_LEVELS, "Medium")
    return _urgency_demo(email)


def _classify_demo(email: str) -> str:
    text = email.lower()
    if any(word in text for word in ["complaint", "angry", "unacceptable", "refund", "not arrived", "broken"]):
        return "Complaint"
    if any(word in text for word in ["meeting", "call", "schedule", "calendar", "available"]):
        return "Meeting Request"
    if any(word in text for word in ["pricing", "quote", "demo", "proposal", "interested", "buy"]):
        return "Sales Inquiry"
    if any(word in text for word in ["following up", "follow up", "checking in", "reminder"]):
        return "Follow-up"
    if any(word in text for word in ["issue", "help", "support", "problem", "update"]):
        return "Support Request"
    return "Casual"


def _urgency_demo(email: str) -> str:
    text = email.lower()
    urgent_patterns = [
        r"\burgent\b",
        r"\burgently\b",
        r"\basap\b",
        r"\bimmediately\b",
        r"\btoday\b",
        r"\bcritical\b",
        r"\bemergency\b",
        r"\bdeadline\b",
    ]
    if any(re.search(pattern, text) for pattern in urgent_patterns):
        return "Urgent"
    if any(word in text for word in ["soon", "this week", "tomorrow", "next business day"]):
        return "Medium"
    return "Low Priority"
