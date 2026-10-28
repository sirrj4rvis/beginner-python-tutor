"""
Step 1 of building our dataset.

Takes every real wrong attempt from the Refactory dataset (raw/refactory/data/question_N/code/wrong),
runs it against that question's test cases (using runner.py), and writes candidates.csv with:
  - the real error message or the first failed test
  - an automatic bug_type (syntax / runtime / logic) when it's obvious
  - a flag explaining why when it's NOT obvious, so a human decides
Attempts that pass every test are dropped (they are not buggy).

It also writes refactory_problems.json: the 5 problems with our plain-English descriptions,
topic, difficulty and all test cases (used later by the app and the training notebook).

Run:  python build_candidates.py
"""
import csv
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from runner import error_message, run_tests

DATASET_DIR = Path(__file__).resolve().parent.parent
RAW = DATASET_DIR / "raw" / "refactory" / "data"

# Our own descriptions, written from each reference solution and its tests.
# Topic and difficulty are our judgement for beginners.
PROBLEMS = {
    1: {"name": "Sequential search", "function": "search", "topic": "loops", "difficulty": "easy",
        "description": "Write a function search(x, seq) that takes a value x and a sorted list or tuple seq. "
                       "Return the index where x should be inserted to keep seq sorted: the position of the "
                       "first element that is greater than or equal to x, or len(seq) if x is larger than every "
                       "element. An empty seq returns 0."},
    2: {"name": "Unique dates/months", "function": "unique_day, unique_month, contains_unique_day",
        "topic": "functions", "difficulty": "medium",
        "description": "Birthdays are given as a tuple of (month, day) string pairs, e.g. (('May', '15'), ('June', '17')). "
                       "Write three functions: unique_day(day, possible_birthdays) returns True if exactly one "
                       "birthday has that day; unique_month(month, possible_birthdays) returns True if exactly one "
                       "birthday has that month; contains_unique_day(month, possible_birthdays) returns True if that "
                       "month has at least one birthday whose day is unique."},
    3: {"name": "Duplicate elimination", "function": "remove_extras", "topic": "lists", "difficulty": "easy",
        "description": "Write a function remove_extras(lst) that returns a new list with duplicate elements removed, "
                       "keeping only the first occurrence of each element and the original order."},
    4: {"name": "Sorting tuples by age", "function": "sort_age", "topic": "sorting", "difficulty": "hard",
        "description": "Write a function sort_age(lst) that takes a list of (gender, age) tuples, e.g. [('M', 23), ('F', 19)], "
                       "and returns the list sorted by age from oldest to youngest."},
    5: {"name": "Top-k elements", "function": "top_k", "topic": "built-ins", "difficulty": "medium",
        "description": "Write a function top_k(lst, k) that returns a list of the k largest numbers in lst, from largest "
                       "to smallest. Repeated numbers count separately, so top_k([9, 9, 4], 2) is [9, 9]."},
}


def load_tests(q):
    ans = RAW / f"question_{q}" / "ans"
    tests = []
    for inp in sorted(ans.glob("input_*.txt")):
        out = ans / inp.name.replace("input_", "output_")
        tests.append({"input": inp.read_text(encoding="utf-8").strip(),
                      "expected": out.read_text(encoding="utf-8").strip()})
    return tests


def load_global(q):
    g = RAW / f"question_{q}" / "code" / "global.py"
    return g.read_text(encoding="utf-8") if g.exists() else ""


def classify(result):
    """Return (bug_type, flag). bug_type is '' when a human should decide; flag says why."""
    s = result["status"]
    if s == "syntax_error":
        return "syntax", ""
    if s == "timeout":
        return "", "timeout: probably an infinite loop (logic), but check"
    if s == "define_error":
        return "runtime", ""
    tests = result["tests"]
    errors = [t for t in tests if t["status"] == "error"]
    fails = [t for t in tests if t["status"] == "fail"]
    if errors and any(t["type"] == "NameError" and "is not defined" in t["message"]
                      and t["line"] is None for t in errors):
        return "", "a required function is missing or misnamed"
    if errors and fails:
        return "", "mixed: some tests crash, others give wrong output"
    if errors:
        return "runtime", ""
    return "logic", ""


def main():
    problems_out, rows = [], []
    for q, info in PROBLEMS.items():
        tests, global_code = load_tests(q), load_global(q)
        if not tests:
            raise SystemExit(f"No test cases found for question_{q}; is the raw data complete?")
        problems_out.append({"task_id": f"refactory_q{q}", **info, "global_code": global_code, "tests": tests})
        files = sorted((RAW / f"question_{q}" / "code" / "wrong").glob("*.py"))

        def work(path):
            code = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
            return path, code, run_tests(code, tests, global_code)

        def recheck(path, code, result):
            # With 8 programs running at once, Windows can be slow to start Python and a normal
            # program may hit the time limit. Re-run timeouts alone with a longer limit.
            if result["status"] == "timeout":
                result = run_tests(code, tests, global_code, time_limit=20)
            return path, code, result

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(work, files))
        for path, code, result in (recheck(*r) for r in results):
            if result["status"] in ("pass", "skipped_unsafe", "crashed"):
                continue
            bug_type, flag = classify(result)
            rows.append({"task_id": f"refactory_q{q}", "source_file": str(path.relative_to(DATASET_DIR)).replace("\\", "/"),
                         "status": result["status"], "student_code": code, "error_message": error_message(result),
                         "bug_type": bug_type, "flag": flag, "lines": code.count("\n") + 1})
        print(f"question_{q}: {len(files)} wrong attempts checked, {sum(r['task_id'] == f'refactory_q{q}' for r in rows)} kept as buggy")

    (DATASET_DIR / "refactory_problems.json").write_text(json.dumps(problems_out, indent=2), encoding="utf-8")
    with open(DATASET_DIR / "candidates.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"Total buggy candidates: {len(rows)} -> candidates.csv")


if __name__ == "__main__":
    main()
