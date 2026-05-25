from src.llm import has_api_key, invoke_prompt
from src.prompts import REPLY_PROMPT
from src.tone_manager import describe_tone


def generate_reply(email: str, summary: str, tone: str, temperature: float = 0.4) -> str:
    if has_api_key():
        return invoke_prompt(
            REPLY_PROMPT,
            email=email,
            summary=summary,
            tone=tone,
            tone_guidance=describe_tone(tone),
            temperature=temperature,
        )
    return _reply_demo(tone)


def _reply_demo(tone: str) -> str:
    greeting = "Hi,"
    closing = "Best regards,"
    if tone == "Formal":
        greeting = "Dear Sender,"
        closing = "Sincerely,"
    elif tone == "Casual":
        greeting = "Hi there,"
        closing = "Thanks,"
    elif tone == "Corporate":
        greeting = "Hello,"
        closing = "Kind regards,"

    return (
        f"{greeting}\n\n"
        "Thank you for reaching out. I appreciate the context and will review the details carefully.\n\n"
        "I will follow up with the appropriate next steps shortly. If there is a specific deadline or "
        "additional information I should consider, please send it over so I can prioritize accordingly.\n\n"
        f"{closing}\n"
        "MailPilot AI"
    )
