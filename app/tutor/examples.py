"""
Loads our real data for the app:
  - load_course_problems(): the 5 Refactory course problems (our description + course test cases),
    so a learner can try them with their own code.
  - load_test_rows(): the 12 TEST rows (listed in training_outputs/split.json). The model never
    saw them during training, so they show how it does on new code, not on code it memorised.
"""
import ast
import csv
import json

import config

DATASET_CSV = config.PROJECT_DIR / "dataset" / "beginner_bugs.csv"
PROBLEMS_JSON = config.PROJECT_DIR / "dataset" / "refactory_problems.json"
REFACTORY_DATA = config.PROJECT_DIR / "dataset" / "raw" / "refactory" / "data"
SPLIT_JSON = config.PROJECT_DIR / "training_outputs" / "split.json"


def load_test_rows():
    """The 12 test rows as dicts (columns of beginner_bugs.csv), in id order."""
    test_ids = set(json.loads(SPLIT_JSON.read_text(encoding="utf-8"))["test"])
    with open(DATASET_CSV, encoding="utf-8", newline="") as f:
        return [row for row in csv.DictReader(f) if int(row["id"]) in test_ids]


def load_course_problems():
    """The 5 course problems. Each dict has task_id, name, topic, difficulty, description, tests,
    global_code, plus:
        starter_code    the empty function header(s), e.g. "def search(x, seq):\\n    pass"
        reference_code  the course's model solution: never shown to the learner; the guardrail
                        (M4) uses it to spot a reply that gives the solution away
    """
    problems = json.loads(PROBLEMS_JSON.read_text(encoding="utf-8"))
    for problem in problems:
        number = problem["task_id"].removeprefix("refactory_q")
        reference_file = REFACTORY_DATA / f"question_{number}" / "code" / "reference" / "reference.py"
        reference = reference_file.read_text(encoding="utf-8")
        # Read the function headers from the reference solution's structure (it is not run).
        headers = [f"def {node.name}({', '.join(a.arg for a in node.args.args)}):\n    pass\n"
                   for node in ast.parse(reference).body if isinstance(node, ast.FunctionDef)]
        problem["starter_code"] = "\n\n".join(headers)
        problem["reference_code"] = reference
    return problems
