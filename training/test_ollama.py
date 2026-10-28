"""
Quick laptop test: send one dataset row to our fine-tuned model running in Ollama.

It uses the same system prompt and message layout as training (prompt_format.py), then prints
the reply, the parsed parts and how long the CPU took.

Run (after `ollama create beginner-tutor -f Modelfile`):
    python test_ollama.py          # uses row 1 of the dataset
    python test_ollama.py 37       # uses row 37
"""
import csv
import json
import sys
import time
import urllib.request
from pathlib import Path

from prompt_format import SYSTEM_PROMPT, parse_reply, user_message

MODEL = "beginner-tutor"
OLLAMA_URL = "http://localhost:11434/api/chat"
DATASET = Path(__file__).resolve().parent.parent / "dataset" / "beginner_bugs.csv"


def ask_tutor(problem, student_code, error_message):
    body = json.dumps({
        "model": MODEL, "stream": False, "options": {"temperature": 0},
        "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                     {"role": "user", "content": user_message(problem, student_code, error_message)}],
    }).encode("utf-8")
    request = urllib.request.Request(OLLAMA_URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.loads(response.read())["message"]["content"]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    row_id = sys.argv[1] if len(sys.argv) > 1 else "1"
    row = next(r for r in csv.DictReader(open(DATASET, encoding="utf-8")) if r["id"] == row_id)
    print(f"Row {row_id} ({row['task_id']}). Student code:\n{row['student_code']}\nError:\n{row['error_message']}\n")
    start = time.time()
    try:
        reply = ask_tutor(row["problem"], row["student_code"], row["error_message"])
    except OSError as e:
        sys.exit(f"Could not reach Ollama at {OLLAMA_URL} ({e}). Is Ollama running, and did you create '{MODEL}'?")
    print(f"--- Tutor reply ({time.time() - start:.1f} s on this computer) ---\n{reply}\n")
    print("--- Parsed ---")
    for key, value in parse_reply(reply).items():
        print(f"{key}: {value}")
    print(f"\n(Our written answer: bug type '{row['bug_type']}'; hint 1: {row['hint_1']})")
