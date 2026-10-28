r"""
M2: talk to our fine-tuned model, which Ollama runs on this laptop.

Ollama is a small local server: we send it the chat messages as JSON over HTTP
(http://localhost:11434/api/chat) and it sends back the model's reply. Nothing leaves the laptop.

We build the messages with training/prompt_format.py, so the model sees exactly the same
system prompt and layout it was fine-tuned on. A different prompt would make it answer worse.

Quick test from the app folder:   ..\.venv\Scripts\python.exe -m tutor.ollama_client
"""
import json
import time
import urllib.request

import config  # also puts training/ on the import path
from prompt_format import SYSTEM_PROMPT, parse_reply, user_message


class TutorUnavailable(Exception):
    """Ollama is not running, or our model is missing."""


def ask_tutor(problem, student_code, error_message, temperature=0.0):
    """Ask the fine-tuned model for hints.

    Returns a dict:
        bug_type, hint_1, hint_2, explanation  (the 4 parts; "" if the model left one out)
        raw      the full reply text (the guardrail in M4 checks this)
        seconds  how long the laptop took
    """
    body = json.dumps({
        "model": config.TUTOR_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message(problem, student_code, error_message)},
        ],
        "stream": False,                        # wait for the whole reply
        "options": {"temperature": temperature},  # 0 = same answer every time
        "keep_alive": "30m",                    # keep the model in memory so later replies are faster
    }).encode("utf-8")
    request = urllib.request.Request(f"{config.OLLAMA_URL}/api/chat", data=body,
                                     headers={"Content-Type": "application/json"})
    start = time.time()
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            raw = json.loads(response.read())["message"]["content"]
    except OSError as e:
        raise TutorUnavailable(
            f"Could not reach the tutor model ({e}). Is the Ollama app running, "
            f"and does 'ollama list' show '{config.TUTOR_MODEL}'?") from e
    reply = {"bug_type": "", "hint_1": "", "hint_2": "", "explanation": ""}
    reply.update(parse_reply(raw))
    reply["raw"] = raw
    reply["seconds"] = round(time.time() - start, 1)
    return reply


def warm_up():
    """Load the model into memory now (an empty request), so the learner's FIRST hint is not slowed
    down by loading. Problems are ignored: the system check in the sidebar reports them."""
    body = json.dumps({"model": config.TUTOR_MODEL, "keep_alive": "30m"}).encode("utf-8")
    request = urllib.request.Request(f"{config.OLLAMA_URL}/api/generate", data=body,
                                     headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(request, timeout=120).read()
    except OSError:
        pass


if __name__ == "__main__":
    import sys
    from tutor.examples import load_test_rows
    sys.stdout.reconfigure(encoding="utf-8")
    row = load_test_rows()[0]
    print(f"Test row {row['id']} ({row['task_id']})\n{row['student_code']}\n{row['error_message']}\n")
    for key, value in ask_tutor(row["problem"], row["student_code"], row["error_message"]).items():
        print(f"{key}: {value}\n")
