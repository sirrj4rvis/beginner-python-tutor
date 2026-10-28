"""
One place to call Gemini (used by Concept Explanation in M5 and Practice Generation in M6).

The free Gemini API sometimes answers "503: high demand" or "429: quota used up" for a while.
So every call:
  1. tries the main model (GEMINI_MODEL in .env) twice, with a short pause in between;
  2. then tries the lighter fallback model (GEMINI_FALLBACK_MODEL) twice;
  3. then gives up with a clear message for the page (GeminiUnavailable).
"""
import time

from google import genai
from google.genai import errors, types

import config

TRY_AGAIN_CODES = {429, 500, 503, 504}   # busy, quota, server hiccup, timeout
TRIES_PER_MODEL = 2


class GeminiUnavailable(Exception):
    """No key, no internet, or Gemini is busy / out of free quota right now."""


def generate(prompt, system_instruction, temperature=0.3, json_schema=None):
    """Ask Gemini. Returns (text, model_used, seconds).
    json_schema: if given, Gemini must reply with JSON of that shape (used in M6)."""
    if not config.GEMINI_API_KEY:
        raise GeminiUnavailable("No Gemini key: put GEMINI_API_KEY=... in the .env file and restart the app.")
    client = genai.Client(api_key=config.GEMINI_API_KEY,
                          http_options=types.HttpOptions(timeout=60_000))   # milliseconds
    settings = types.GenerateContentConfig(system_instruction=system_instruction, temperature=temperature)
    if json_schema is not None:
        settings.response_mime_type = "application/json"
        settings.response_schema = json_schema

    start, last_problem = time.time(), "unknown problem"
    for model in dict.fromkeys([config.GEMINI_MODEL, config.GEMINI_FALLBACK_MODEL]):   # no duplicates
        for attempt in range(TRIES_PER_MODEL):
            try:
                reply = client.models.generate_content(model=model, contents=prompt, config=settings)
                return (reply.text or "").strip(), model, round(time.time() - start, 1)
            except errors.APIError as e:
                last_problem = f"{e.code} {e.status}"
                if e.code not in TRY_AGAIN_CODES:      # e.g. wrong key: retrying will not help
                    raise GeminiUnavailable(f"Gemini refused the request ({last_problem}).") from e
            except Exception as e:                      # no internet, timeout...
                last_problem = type(e).__name__
            time.sleep(2 * (attempt + 1))
    raise GeminiUnavailable(f"Gemini is busy or unreachable right now ({last_problem}). "
                            "Please try again in a minute.")
