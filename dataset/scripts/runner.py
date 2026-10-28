"""
Runs a piece of student code against test cases, safely enough for a student project.

How it keeps things safe:
  1. Code that tries to use files, the OS or the network is refused before it runs.
  2. The code runs in a SEPARATE Python process (a "subprocess"), so a crash cannot
     break our program.
  3. That process is killed if it takes longer than TIME_LIMIT seconds
     (catches infinite loops).

Main function: run_tests(student_code, tests, global_code="") -> dict
  tests = [{"input": "search(5, (1, 5, 10))", "expected": "1"}, ...]
The result says whether the code passed, and if not, the first real error
or failed test, which becomes the error_message column of our dataset.
"""
import ast
import json
import re
import subprocess
import sys

TIME_LIMIT = 5  # seconds for the whole program (all tests together)

# Things a beginner's solution never needs. If we see them, we don't run the code.
UNSAFE_PATTERN = re.compile(
    r"\bimport\s+(os|sys|subprocess|shutil|socket|pathlib|ctypes|multiprocessing)\b"
    r"|\bfrom\s+(os|sys|subprocess|shutil|socket|pathlib|ctypes|multiprocessing)\b"
    r"|\bopen\s*\(|__import__|\beval\s*\(|\bexec\s*\(|\bcompile\s*\("
)

# This small program is what actually runs inside the separate process.
# It reads the job (code + tests) as JSON from stdin and prints the result as JSON.
HARNESS = r'''
import ast, io, json, sys, traceback

job = json.loads(sys.stdin.read())
real_stdout = sys.stdout
sys.stdin = io.StringIO("")          # input() gets nothing, so it fails fast instead of hanging

def student_line(tb):
    """Line number inside the student's code where the error happened (None if not in it)."""
    line = None
    for frame in traceback.extract_tb(tb):
        if frame.filename == "<student>":
            line = frame.lineno
    return line

def same(value, expected_text):
    try:
        return value == ast.literal_eval(expected_text)
    except Exception:
        return repr(value) == expected_text

result = {"compile_error": None, "define_error": None, "tests": []}
try:
    code_obj = compile(job["code"], "<student>", "exec")
except SyntaxError as e:              # includes IndentationError and TabError
    result["compile_error"] = {"type": type(e).__name__, "message": e.msg, "line": e.lineno}
else:
    namespace = {}
    sys.stdout = io.StringIO()        # hide the student's own print() output
    try:
        exec(job["global_code"], namespace)
        exec(code_obj, namespace)
    except BaseException as e:
        result["define_error"] = {"type": type(e).__name__, "message": str(e), "line": student_line(e.__traceback__)}
    else:
        for t in job["tests"]:
            entry = {"input": t["input"], "expected": t["expected"]}
            try:
                # eval is intended: t["input"] is OUR test call (e.g. "search(5, (1, 5, 10))"),
                # and this whole harness already runs in an isolated, time-limited process.
                value = eval(t["input"], namespace)
                entry["status"] = "pass" if same(value, t["expected"]) else "fail"
                entry["got"] = repr(value)
            except BaseException as e:
                entry.update(status="error", type=type(e).__name__, message=str(e),
                             line=student_line(e.__traceback__))
            result["tests"].append(entry)
    sys.stdout = real_stdout
real_stdout.write("@@RESULT@@" + json.dumps(result))
'''


def is_unsafe(code):
    return bool(UNSAFE_PATTERN.search(code))


def run_tests(code, tests, global_code="", time_limit=TIME_LIMIT, env=None):
    """Run the code against all tests. Returns a dict with 'status' plus details.

    env: environment variables for the separate process (None = inherit ours). The app passes a
    minimal one so the student's code can never see secrets such as the Gemini key.
    """
    if is_unsafe(code):
        return {"status": "skipped_unsafe"}
    job = json.dumps({"code": code, "tests": tests, "global_code": global_code})
    try:
        proc = subprocess.run([sys.executable, "-I", "-c", HARNESS], input=job, capture_output=True,
                              text=True, timeout=time_limit, encoding="utf-8", env=env)
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}
    if "@@RESULT@@" not in proc.stdout:
        return {"status": "crashed", "stderr": proc.stderr[-500:]}
    raw = json.loads(proc.stdout.split("@@RESULT@@", 1)[1])

    if raw["compile_error"]:
        return {"status": "syntax_error", **raw}
    if raw["define_error"]:
        return {"status": "define_error", **raw}
    statuses = {t["status"] for t in raw["tests"]}
    return {"status": "pass" if statuses == {"pass"} else "fail", **raw}


def error_message(result):
    """Turn a run result into the short, real error text we store in the dataset."""
    s = result["status"]
    if s == "syntax_error":
        e = result["compile_error"]
        return f"{e['type']}: {e['message']} (line {e['line']})"
    if s == "define_error":
        e = result["define_error"]
        where = f" (line {e['line']})" if e["line"] else ""
        return f"{e['type']}: {e['message']}{where}"
    if s == "timeout":
        return f"Timed out after {TIME_LIMIT} seconds (the code may have an infinite loop)"
    for t in result.get("tests", []):
        if t["status"] == "error":
            where = f" (line {t['line']})" if t["line"] else ""
            return f"Test: {t['input']}\n{t['type']}: {t['message']}{where}"
        if t["status"] == "fail":
            return f"Test: {t['input']}\nExpected: {t['expected']}\nGot: {t['got']}"
    return ""


if __name__ == "__main__":
    # Tiny self-check: one buggy and one correct version of the same function.
    tests = [{"input": "add(2, 3)", "expected": "5"}]
    print(error_message(run_tests("def add(a, b):\n    return a - b", tests)))
    print(run_tests("def add(a, b):\n    return a + b", tests)["status"])
    print(error_message(run_tests("def add(a, b)\n    return a + b", tests)))
    print(error_message(run_tests("def add(a, b):\n    return a + c", tests)))
    print(run_tests("def add(a, b):\n    while True: pass", tests)["status"])
    print(run_tests("import os\ndef add(a, b): return a + b", tests)["status"])
