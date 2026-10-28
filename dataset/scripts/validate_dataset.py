"""
Step 4: check the finished dataset before we train on it.

Checks (each problem is printed with its row id):
  1. Every cell is filled in.
  2. bug_type is one of syntax / runtime / logic (no leftover "FLAG: ..." values).
  3. fixed_code passes ALL test cases for its problem, AND gives the same answers as the
     instructor's reference solution on 40 random inputs (random_tests.py), so a "fix" that only
     happens to pass the few course tests is caught.
  4. student_code really fails at least one test (it is a real bug).
  5. No hint or explanation contains the fixed code: no line of code that was added or
     changed by the fix appears in hint_1, hint_2 or explanation, and no code block at all.
  6. No duplicate rows (same student_code twice).
  7. At least MIN_ROWS rows.

Run:  python validate_dataset.py            (checks beginner_bugs.csv)
      python validate_dataset.py other.csv
Exit code 0 means everything passed.
"""
import csv
import json
import re
import sys
from pathlib import Path

from random_tests import make_random_tests
from runner import error_message, run_tests

MIN_ROWS = 30
DATASET_DIR = Path(__file__).resolve().parent.parent
REQUIRED = ["id", "task_id", "topic", "difficulty", "problem", "student_code", "error_message",
            "bug_type", "hint_1", "hint_2", "explanation", "fixed_code"]
BUG_TYPES = {"syntax", "runtime", "logic"}


def code_lines(code):
    """Meaningful code lines, without spaces, so 'x = 1' and 'x=1' count as the same."""
    return {re.sub(r"\s+", "", l) for l in code.splitlines() if l.strip() and not l.strip().startswith("#")}


def leaked_lines(row):
    """Lines that the fix added or changed and that also appear in a hint or the explanation."""
    new_lines = code_lines(row["fixed_code"]) - code_lines(row["student_code"])
    # Very short lines like "return" or "else:" are normal words in a hint, not a leak.
    new_lines = {l for l in new_lines if len(l) >= 12}
    leaks = []
    for col in ("hint_1", "hint_2", "explanation"):
        text = re.sub(r"\s+", "", row[col])
        leaks += [f"{col} contains fixed line '{l}'" for l in new_lines if l in text]
        if "```" in row[col] or "def " in row[col]:
            leaks.append(f"{col} contains a code block or a function definition")
    return leaks


def main(path):
    problems = {p["task_id"]: p for p in json.loads((DATASET_DIR / "refactory_problems.json").read_text(encoding="utf-8"))}
    random_tests = {t: make_random_tests(t) for t in problems}
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    errors = []

    missing_cols = [c for c in REQUIRED if c not in (rows[0] if rows else {})]
    if missing_cols:
        sys.exit(f"Missing columns: {missing_cols}")

    seen = {}
    for row in rows:
        rid = row["id"]
        empty = [c for c in REQUIRED if not row[c].strip()]
        if empty:
            errors.append(f"row {rid}: empty cells {empty}")
            continue
        if row["bug_type"] not in BUG_TYPES:
            errors.append(f"row {rid}: bug_type '{row['bug_type']}' is not syntax/runtime/logic")
        p = problems.get(row["task_id"])
        if not p:
            errors.append(f"row {rid}: unknown task_id {row['task_id']}")
            continue
        fixed = run_tests(row["fixed_code"], p["tests"], p["global_code"], time_limit=20)
        if fixed["status"] != "pass":
            errors.append(f"row {rid}: fixed_code does not pass all tests (status: {fixed['status']})")
        else:
            extra = run_tests(row["fixed_code"], random_tests[row["task_id"]], p["global_code"], time_limit=20)
            if extra["status"] != "pass":
                errors.append(f"row {rid}: fixed_code passes the course tests but not the random tests: "
                              + error_message(extra).replace("\n", " | "))
        student = run_tests(row["student_code"], p["tests"], p["global_code"], time_limit=20)
        if student["status"] == "pass":
            errors.append(f"row {rid}: student_code passes all tests, so it is not a bug")
        errors += [f"row {rid}: {msg}" for msg in leaked_lines(row)]
        key = re.sub(r"\s+", "", row["student_code"])
        if key in seen:
            errors.append(f"row {rid}: duplicate of row {seen[key]}")
        seen[key] = rid

    if len(rows) < MIN_ROWS:
        errors.append(f"only {len(rows)} rows; need at least {MIN_ROWS}")

    for e in errors:
        print("FAIL", e)
    print(f"\n{len(rows)} rows checked, {len(errors)} problem(s) found.")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else DATASET_DIR / "beginner_bugs.csv"))
