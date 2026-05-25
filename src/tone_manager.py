from src.prompts import TONES


TONE_DESCRIPTIONS = {
    "Professional": "Balanced, courteous, and direct. Use clean business language without sounding stiff.",
    "Friendly": "Warm, helpful, and approachable. Use natural phrasing, a positive tone, and light warmth.",
    "Formal": "Polished, respectful, and precise. Use a more traditional business email style.",
    "Casual": "Relaxed, concise, and human. Keep it simple and conversational while staying respectful.",
    "Corporate": "Brand-safe, structured, and executive. Keep it concise, polished, and decision-ready.",
}


def get_tones() -> list[str]:
    return TONES


def describe_tone(tone: str) -> str:
    return TONE_DESCRIPTIONS.get(tone, TONE_DESCRIPTIONS["Professional"])
