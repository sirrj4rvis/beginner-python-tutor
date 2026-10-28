"""
Checks one labels file before it is merged into the dataset.

A labels file is a JSON list like:
  [{"id": 25, "bug_type": "runtime", "hint_1": "...", "hint_2": "...",
    "explanation": "...", "fixed_code": "def remove_extras(lst): ..."}, ...]

For each row it checks: all fields are filled in, bug_type is valid, fixed_code passes every test,
and no hint or explanation leaks the fixed code (same rules as validate_dataset.py).

Run:  python check_labels.py ../labels/refactory_q3.json
"""
import csv
import json
import sys
from pathlib import Path

from runner import error_message, run_tests
from validate_dataset import BUG_TYPES, DATASET_DIR, leaked_lines

FIELDS = ["bug_type", "hint_1", "hint_2", "explanation", "fixed_code"]


def main(path):
    labels = json.loads(Path(path).read_text(encoding="utf-8"))
    problems = {p["task_id"]: p for p in json.loads((DATASET_DIR / "refactory_problems.json").read_text(encoding="utf-8"))}
    rows = {r["id"]: r for r in csv.DictReader(open(DATASET_DIR / "dataset_unlabeled.csv", encoding="utf-8"))}
    bad = 0
    for lab in labels:
        rid = str(lab["id"])
        row = {**rows[rid], **{k: lab.get(k, "") for k in FIELDS}}
        problems_found = [f"empty {k}" for k in FIELDS if not str(row[k]).strip()]
        if row["bug_type"] not in BUG_TYPES:
            problems_found.append(f"bug_type '{row['bug_type']}' is not syntax/runtime/logic")
        p = problems[row["task_id"]]
        result = run_tests(row["fixed_code"], p["tests"], p["global_code"], time_limit=20)
        if result["status"] != "pass":
            problems_found.append("fixed_code fails: " + error_message(result).replace("\n", " | "))
        problems_found += leaked_lines(row)
        if problems_found:
            bad += 1
            print(f"row {rid}: FAIL")
            for msg in problems_found:
                print("    -", msg)
        else:
            print(f"row {rid}: ok")
    print(f"{len(labels)} labels checked, {bad} with problems.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
