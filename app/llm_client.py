"""Satu-satunya file yang tahu soal provider LLM (Gemini).

Kalau provider diganti (Groq/OpenAI), cukup file ini yang diubah.
"""
import asyncio
import os

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

load_dotenv()

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
TIMEOUT_SEC = float(os.getenv("LLM_TIMEOUT_SEC", "60"))


class LLMError(Exception):
    """Error dari sisi LLM, dengan status HTTP yang cocok untuk dikembalikan ke user."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


_client: genai.Client | None = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise LLMError("GEMINI_API_KEY belum diatur di file .env", status_code=500)
        _client = genai.Client(api_key=api_key)
    return _client


async def generate(system_prompt: str, user_prompt: str, response_schema=None) -> str:
    """Kirim prompt ke Gemini. Jika response_schema diberikan, Gemini dipaksa mengembalikan JSON sesuai schema."""
    config = types.GenerateContentConfig(system_instruction=system_prompt)
    if response_schema is not None:
        config.response_mime_type = "application/json"
        config.response_schema = response_schema

    try:
        response = await asyncio.wait_for(
            get_client().aio.models.generate_content(model=MODEL, contents=user_prompt, config=config),
            timeout=TIMEOUT_SEC,
        )
    except asyncio.TimeoutError as e:
        raise LLMError(f"LLM tidak merespons dalam {TIMEOUT_SEC:.0f} detik", status_code=504) from e
    except errors.APIError as e:
        if e.code == 429:
            raise LLMError("Kuota / rate limit Gemini habis, coba lagi beberapa saat", status_code=429) from e
        if e.code in (400, 404):
            raise LLMError(f"Request ke Gemini ditolak (cek nama model '{MODEL}'): {e.message}", status_code=502) from e
        raise LLMError(f"Gemini error {e.code}: {e.message}", status_code=502) from e

    text = response.text
    if not text:
        raise LLMError("Gemini mengembalikan respons kosong (kemungkinan diblokir safety filter)", status_code=502)
    return text
