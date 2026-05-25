from src.llm import has_api_key, invoke_prompt
from src.prompts import SUMMARY_PROMPT
from src.utils import first_sentence


def summarize_email(email: str, temperature: float = 0.4) -> str:
    if has_api_key():
        return invoke_prompt(SUMMARY_PROMPT, email=email, temperature=temperature)
    return _summary_demo(email)


def _summary_demo(email: str) -> str:
    lead = first_sentence(email)
    if not lead:
        return "No email content was provided."

    return (
        f"Summary: {lead}\n\n"
        "Key points:\n"
        "- The sender is requesting attention or a response.\n"
        "- Important context should be confirmed before committing to next steps.\n\n"
        "Sender intent: Get a clear response and move the conversation forward."
    )
