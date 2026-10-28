"""
Step 2: pick a varied sample of buggy attempts to label.

From candidates.csv we pick ROWS_PER_TASK attempts per problem so that:
  - attempts are short enough for a beginner to read (MAX_LINES)
  - no two picked attempts are the same code (ignoring spaces and comments)
  - different kinds of mistakes are covered: we group attempts by "signature"
    (bug type + error type + which test failed first) and take one from each group in turn
The random seed is fixed, so running this again gives exactly the same rows.

Output: dataset_unlabeled.csv with the final columns; the hint and explanation columns are empty.
Run:  python select_rows.py
"""
import csv
import io
import json
import random
import re
import tokenize
from collections import defaultdict
from pathlib import Path

SEED = 42
ROWS_PER_TASK = 12
MAX_LINES = {"refactory_q2": 40}   # q2 has three functions, so allow longer code
DEFAULT_MAX_LINES = 25

DATASET_DIR = Path(__file__).resolve().parent.parent
COLUMNS = ["id", "task_id", "topic", "difficulty", "problem", "student_code", "error_message",
           "bug_type", "hint_1", "hint_2", "explanation", "fixed_code", "source_file"]


def normalise(code):
    """Code without comments and whitespace, used to spot duplicates."""
    try:
        tokens = [t.string for t in tokenize.generate_tokens(io.StringIO(code).readline)
                  if t.type not in (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT)]
        return " ".join(tokens)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return re.sub(r"\s+", "", code)


def signature(row):
    first = row["error_message"].splitlines()
    kind = row["bug_type"] or "flagged"
    if len(first) > 1 and first[1].startswith("Expected"):
        detail = "wrong output on " + first[0]
    else:
        detail = (first[-1].split(":")[0] if first else "") + " " + (first[0] if first else "")
    return kind, detail


def main():
    random.seed(SEED)
    problems = {p["task_id"]: p for p in json.loads((DATASET_DIR / "refactory_problems.json").read_text(encoding="utf-8"))}
    rows = list(csv.DictReader(open(DATASET_DIR / "candidates.csv", encoding="utf-8")))

    picked = []
    for task_id in problems:
        seen, groups = set(), defaultdict(list)
        pool = [r for r in rows if r["task_id"] == task_id
                and int(r["lines"]) <= MAX_LINES.get(task_id, DEFAULT_MAX_LINES)]
        random.shuffle(pool)
        for r in pool:
            key = normalise(r["student_code"])
            if key not in seen:
                seen.add(key)
                groups[signature(r)].append(r)
        # Round-robin over the groups so every kind of mistake gets a turn.
        order = sorted(groups, key=lambda g: (-len(groups[g]), g))
        chosen = []
        while len(chosen) < ROWS_PER_TASK and any(groups.values()):
            for g in order:
                if groups[g] and len(chosen) < ROWS_PER_TASK:
                    chosen.append(groups[g].pop())
        picked += chosen

    with open(DATASET_DIR / "dataset_unlabeled.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for i, r in enumerate(picked, 1):
            p = problems[r["task_id"]]
            w.writerow({"id": i, "task_id": r["task_id"], "topic": p["topic"], "difficulty": p["difficulty"],
                        "problem": p["description"], "student_code": r["student_code"],
                        "error_message": r["error_message"], "bug_type": r["bug_type"] or "FLAG: " + r["flag"],
                        "hint_1": "", "hint_2": "", "explanation": "", "fixed_code": "",
                        "source_file": r["source_file"]})
    print(f"Picked {len(picked)} rows -> dataset_unlabeled.csv")


if __name__ == "__main__":
    main()
