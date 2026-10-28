"""
M3: run the learner's code safely against test cases and capture the real error.

The actual running is done by dataset/scripts/runner.py, the same code that built our dataset,
so the app produces error messages in exactly the format the model was trained on.

Safety layers (enough for a student project on Windows; NOT a security sandbox for strangers):
  1. Size limit: very long code is refused.
  2. Structure check (this file): we read the code's structure with Python's `ast` module and
     refuse imports outside a small safe list, dangerous built-ins (open, exec, eval, getattr...)
     and "dunder" tricks such as ().__class__.__subclasses__(), which can escape simple filters.
  3. runner.py's own word filter (os, sys, subprocess, open(...)).
  4. The code runs in a SEPARATE Python process in isolated mode (-I), with a minimal
     environment (so it cannot read our Gemini key), and is killed after 5 seconds.
Known limit: Windows has no simple per-process memory cap, so the size limit and the
5-second timeout are what stop memory-hungry code.

Quick test from the app folder:   ..\\.venv\\Scripts\\python.exe -m tutor.sandbox
"""
import ast
import os

import config  # also puts dataset/scripts on the import path
from runner import error_message, run_tests

MAX_CODE_CHARS = 5000
ALLOWED_IMPORTS = {"math", "random", "string", "collections", "itertools", "functools",
                   "heapq", "statistics", "re"}
BLOCKED_NAMES = {"open", "exec", "eval", "compile", "__import__", "globals", "locals", "vars",
                 "getattr", "setattr", "delattr", "breakpoint", "exit", "quit", "help"}
ALLOWED_DUNDERS = {"__name__", "__init__", "__str__", "__repr__"}   # common in beginner code

# The child process gets only what Python needs to start on Windows: no API keys, no PATH.
CLEAN_ENV = {k: v for k, v in os.environ.items() if k.upper() in {"SYSTEMROOT", "TEMP", "TMP"}}


def safety_problem(code):
    """Return a short reason if the code must not run, or None if it looks safe."""
    if len(code) > MAX_CODE_CHARS:
        return f"Your code is longer than {MAX_CODE_CHARS} characters. Beginner exercises need far less."
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None   # cannot run anyway; runner.py reports the syntax error without executing anything
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules = [alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            modules = [(node.module or "").split(".")[0]]
        else:
            modules = []
        for module in modules:
            if module not in ALLOWED_IMPORTS:
                return f"Importing '{module}' is not allowed here. Allowed: {', '.join(sorted(ALLOWED_IMPORTS))}."
        if isinstance(node, ast.Name) and node.id in BLOCKED_NAMES:
            return f"Using '{node.id}' is not allowed in this tutor."
        name = node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute) else ""
        if name.startswith("__") and name.endswith("__") and name not in ALLOWED_DUNDERS:
            return f"Special names like '{name}' are not allowed in this tutor."
    return None


def run_code(code, problem):
    """Run the learner's code against the problem's tests.

    problem: dict with "tests" (list of {"input", "expected"}) and optional "global_code".
    Returns a dict:
        status         pass | fail | syntax_error | define_error | timeout | blocked | crashed
        passed, total  how many tests passed
        tests          per-test details from runner.py (input, expected, got / error)
        error_message  the real error in the dataset format ("" if all passed); this is
                       what the fine-tuned model receives in M4
        headline       one friendly sentence for the learner
    """
    tests = problem["tests"]
    reason = safety_problem(code)
    if reason:
        return {"status": "blocked", "passed": 0, "total": len(tests), "tests": [],
                "error_message": "", "headline": reason}

    result = run_tests(code, tests, problem.get("global_code", ""),
                       time_limit=config.SANDBOX_TIME_LIMIT, env=CLEAN_ENV)
    status = result["status"]
    if status == "skipped_unsafe":    # runner.py's own filter caught something
        return {"status": "blocked", "passed": 0, "total": len(tests), "tests": [],
                "error_message": "", "headline": "This code uses files, the OS or the network, which is not allowed here."}

    test_rows = result.get("tests", [])
    passed = sum(t["status"] == "pass" for t in test_rows)
    headlines = {
        "pass": f"All {len(tests)} tests passed. Well done!",
        "fail": f"{passed} of {len(tests)} tests passed.",
        "syntax_error": "Python could not read your code (a syntax error), so no test ran.",
        "define_error": "Your code crashed before any test could run.",
        "timeout": f"Your code ran for more than {config.SANDBOX_TIME_LIMIT} seconds. Is there an infinite loop?",
        "crashed": "The code runner itself failed. Try again, or simplify the code.",
    }
    return {"status": status, "passed": passed, "total": len(tests), "tests": test_rows,
            "error_message": "" if status == "pass" else error_message(result),
            "headline": headlines.get(status, status)}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    add = {"tests": [{"input": "add(2, 3)", "expected": "5"}, {"input": "add(0, 0)", "expected": "0"}]}
    cases = {
        "correct":           "def add(a, b):\n    return a + b",
        "logic bug":         "def add(a, b):\n    return a - b",
        "runtime bug":       "def add(a, b):\n    return a + c",
        "syntax error":      "def add(a, b)\n    return a + b",
        "infinite loop":     "def add(a, b):\n    while True:\n        pass",
        "import os":         "import os\ndef add(a, b):\n    return a + b",
        "dunder escape":     "x = ().__class__.__base__.__subclasses__()\ndef add(a, b):\n    return a + b",
        "getattr trick":     "def add(a, b):\n    return getattr(a, 'real') + b",
        "allowed import":    "import math\ndef add(a, b):\n    return math.fsum([a, b])",
        "if __name__ ok":    "def add(a, b):\n    return a + b\nif __name__ == '__main__':\n    print(add(1, 2))",
        "read env (no os)":  "def add(a, b):\n    return a + b + len(__builtins__.__dict__)",
    }
    for label, code in cases.items():
        r = run_code(code, add)
        print(f"{label:17} {r['status']:13} {r['headline']}")
        if r["error_message"]:
            print("                  " + r["error_message"].replace("\n", " | "))
