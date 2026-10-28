"""
M4: the guardrail. A rule-based check on EVERY reply from the fine-tuned model, so the
learner never sees the solution. The rules are fixed in methodology/METHODOLOGY_NOTES.md (section 3):

  1. A code block (```) or a function definition ("def ") means the reply wrote code -> blocked.
  2. A line of the solution (12+ characters) that the learner has NOT written yet appears in the
     reply -> blocked (the model gave the fix away).
  3. The reply is missing one of the 4 parts (Bug type, Hint 1, Hint 2, Explanation) -> blocked.

If the model keeps failing the check, template_hint() builds a safe hint from the error itself.
Every block is logged to app/data/guardrail_log.jsonl (Prompt 7 reports the block rate).
"""
import json
import re
import time

import config

MIN_LINE_CHARS = 12
LOG_FILE = config.DATA_DIR / "guardrail_log.jsonl"


def _normalise(text):
    """Ignore spacing and backticks, so 'x  =  1' and '`x = 1`' count as the same text."""
    return re.sub(r"\s+", " ", text.replace("`", "")).strip()


def check_reply(parts, solutions, learner_code):
    """parts: the parsed reply (bug_type, hint_1, hint_2, explanation, raw).
    solutions: correct solutions we know (the reference solution; for dataset rows also the fix).
    Returns None if the reply is safe, otherwise a short reason."""
    raw = parts["raw"]
    if "```" in raw:
        return "contains a code block"
    if "def " in raw:
        return "contains a function definition"
    reply = _normalise(raw)
    written = {_normalise(line) for line in learner_code.splitlines()}
    for solution in solutions:
        for line in solution.splitlines():
            line = _normalise(line)
            if len(line) >= MIN_LINE_CHARS and line not in written and line in reply:
                return f"gives away a solution line: {line}"
    missing = [name for name in ("bug_type", "hint_1", "hint_2", "explanation") if not parts[name]]
    if missing:
        return "missing " + ", ".join(missing)
    return None


def log_block(task_id, reason, raw):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps({"time": time.strftime("%Y-%m-%d %H:%M:%S"), "task_id": task_id,
                            "reason": reason, "reply": raw}, ensure_ascii=False) + "\n")


# Simple words for the most common beginner errors (used only by the safe template hint).
ERROR_MEANINGS = {
    "NameError": "Python met a name (a variable or function) that does not exist at that moment.",
    "TypeError": "an operation got a value of the wrong type, like adding a number to a string or calling something that is not a function.",
    "IndexError": "the code asked for a position that is outside the list or string.",
    "KeyError": "the code asked a dictionary for a key it does not have.",
    "ValueError": "a function got a value of the right type but an unsuitable value.",
    "AttributeError": "the code used a method or attribute that this kind of value does not have.",
    "UnboundLocalError": "a variable was used inside the function before it was given a value there.",
    "ZeroDivisionError": "the code divided by zero.",
    "RecursionError": "a function kept calling itself without stopping.",
}


def template_hint(run_result):
    """A safe fallback built only from the sandbox result (it can never contain the solution)."""
    status, message = run_result["status"], run_result["error_message"]
    line = re.search(r"\(line (\d+)\)", message)
    where = f"line {line.group(1)}" if line else "the line Python points to"
    error_type = re.search(r"^(\w+(?:Error|Exception))", message, re.MULTILINE)

    if status == "syntax_error":
        parts = {"bug_type": "syntax",
                 "hint_1": "Python could not read your code, so it did not run at all. Look for a typing slip.",
                 "hint_2": f"Look closely at {where} and the line just before it: a missing colon, bracket or quote is common.",
                 "explanation": "A syntax error means the code breaks Python's grammar rules, so Python stops before running anything."}
    elif status == "timeout":
        parts = {"bug_type": "logic",
                 "hint_1": "Your code never finished. Is there a loop that can run forever?",
                 "hint_2": "Check each loop: does something inside it change, so that the loop's condition eventually becomes false?",
                 "explanation": f"The code ran for more than {config.SANDBOX_TIME_LIMIT} seconds, which usually means a loop never reaches its end."}
    elif error_type:
        name = error_type.group(1)
        parts = {"bug_type": "runtime",
                 "hint_1": f"Python stopped with a {name}. Read the message slowly: what is it telling you?",
                 "hint_2": f"Look at {where}. Which value does each variable have when that line runs for the failing test?",
                 "explanation": f"A {name} means {ERROR_MEANINGS.get(name, 'Python hit a problem while running that line.')}"}
    else:
        test = re.search(r"^Test: (.*)$", message, re.MULTILINE)
        test_text = test.group(1) if test else "the failing test"
        parts = {"bug_type": "logic",
                 "hint_1": f"Your code runs but gives the wrong answer for {test_text}. Work through that test by hand.",
                 "hint_2": "Compare the expected value with what your code returned, and find the first step where your value goes wrong.",
                 "explanation": "This is a logic bug: Python found no error, but the steps do not do what the problem asks."}
    parts["raw"] = "\n".join(f"{k}: {v}" for k, v in parts.items())
    return parts
