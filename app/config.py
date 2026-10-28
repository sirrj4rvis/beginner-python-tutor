"""
All settings for the app, in one place.

- Secrets and model names come from the .env file in the project folder (never hard-coded).
- The tutoring rules (time limit, hint credits, mastery update, difficulty bands) are the
  ones fixed in methodology/METHODOLOGY_NOTES.md, section 3. Change them only there and here.
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# --- Folders ---------------------------------------------------------------
APP_DIR = Path(__file__).resolve().parent          # D:\GEN AI\app
PROJECT_DIR = APP_DIR.parent                       # D:\GEN AI
DATA_DIR = APP_DIR / "data"                        # SQLite DB and ChromaDB store (created on first run)
NOTES_DIR = APP_DIR / "notes"                      # beginner notes for RAG (milestone M5)
DATA_DIR.mkdir(exist_ok=True)

# Reuse code we already wrote and tested, instead of copying it:
#   training/prompt_format.py  -> the exact prompt the model was trained on
#   dataset/scripts/runner.py  -> the safe, time-limited code runner
sys.path.insert(0, str(PROJECT_DIR / "training"))
sys.path.insert(0, str(PROJECT_DIR / "dataset" / "scripts"))

# --- Secrets and models (from .env) -----------------------------------------
load_dotenv(PROJECT_DIR / ".env")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash").strip()
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite").strip()   # used when the main one is busy
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
TUTOR_MODEL = os.getenv("TUTOR_MODEL", "beginner-tutor").strip()

# --- Tutoring rules (METHODOLOGY_NOTES.md, section 3) -------------------------
SANDBOX_TIME_LIMIT = 5                 # seconds per run of the learner's code
MAX_MODEL_TRIES = 2                    # ask the model again once if the guardrail blocks a reply
RETRY_TEMPERATURE = 0.7                # the 2nd try is less "fixed", so it gives a different reply
HINT_CREDIT = [1.0, 0.75, 0.5, 0.25]   # credit when solved after 0, 1, 2 or 3 help levels
MASTERY_RATE = 0.3                     # m <- m + 0.3 * (credit - m)
MASTERED = 0.8                         # topic counts as mastered at or above this
EASY_BELOW, MEDIUM_BELOW = 0.4, 0.7    # difficulty bands for the next exercise
TOPICS = ["loops", "lists", "functions", "built-ins", "sorting"]   # curriculum order
