import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_groq import ChatGroq


load_dotenv()

DEFAULT_MODEL = "llama-3.3-70b-versatile"


def get_api_key() -> str:
    return os.getenv("GROQ_API_KEY", "").strip()


def has_api_key() -> bool:
    return bool(get_api_key())


@lru_cache(maxsize=4)
def get_llm(model_name: str = DEFAULT_MODEL, temperature: float = 0.4) -> ChatGroq:
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing. Add it to your .env file.")

    return ChatGroq(
        groq_api_key=api_key,
        model=model_name,
        temperature=temperature,
    )


def invoke_prompt(prompt_template, temperature: float = 0.4, **kwargs) -> str:
    prompt = prompt_template.format(**kwargs)
    response = get_llm(temperature=temperature).invoke(prompt)
    return getattr(response, "content", str(response)).strip()
