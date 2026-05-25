from src.llm import has_api_key, invoke_prompt
from src.prompts import FOLLOWUP_PROMPT


def generate_followup(email: str, summary: str, temperature: float = 0.4) -> str:
    if has_api_key():
        return invoke_prompt(FOLLOWUP_PROMPT, email=email, summary=summary, temperature=temperature)
    return (
        "If there is no response within 2-3 business days, send a concise reminder that references "
        "the original request and asks for confirmation on the next step."
    )
