"""
Extra test cases made from random inputs.

The original course has only 5-17 tests per problem, so a "fixed" program can pass them and
still be wrong on other inputs. Here we make random inputs and get the correct answer from the
instructor's reference solution (raw/refactory/data/question_N/code/reference/reference.py).
A fixed_code must give the same answers.

make_random_tests(task_id) -> list of {"input": "...", "expected": "..."} (same format as the real tests)
"""
import random
from pathlib import Path

DATASET_DIR = Path(__file__).resolve().parent.parent
RAW = DATASET_DIR / "raw" / "refactory" / "data"
MONTHS = ["May", "June", "July", "August"]
DAYS = [str(d) for d in range(14, 20)]


def _inputs(task_id, rng):
    if task_id == "refactory_q1":
        seq = sorted(rng.sample(range(-20, 20), rng.randint(0, 8)))
        seq = tuple(seq) if rng.random() < 0.5 else seq
        return [f"search({rng.randint(-25, 25)}, {seq!r})"]
    if task_id == "refactory_q2":
        pairs = rng.sample([(m, d) for m in MONTHS for d in DAYS], rng.randint(0, 8))
        b = repr(tuple(pairs))
        return [f"unique_day({rng.choice(DAYS)!r}, {b})",
                f"unique_month({rng.choice(MONTHS)!r}, {b})",
                f"contains_unique_day({rng.choice(MONTHS)!r}, {b})"]
    if task_id == "refactory_q3":
        return [f"remove_extras({[rng.randint(0, 5) for _ in range(rng.randint(0, 10))]!r})"]
    if task_id == "refactory_q4":
        ages = rng.sample(range(10, 70), rng.randint(0, 7))     # distinct ages: the order is then unique
        return [f"sort_age({[(rng.choice('MF'), a) for a in ages]!r})"]
    if task_id == "refactory_q5":
        lst = [rng.randint(0, 9) for _ in range(rng.randint(1, 9))]
        return [f"top_k({lst!r}, {rng.randint(0, len(lst))})"]
    raise ValueError(task_id)


def make_random_tests(task_id, n=40, seed=0):
    q = task_id.rsplit("q", 1)[1]
    namespace = {}
    global_file = RAW / f"question_{q}" / "code" / "global.py"
    if global_file.exists():
        exec(global_file.read_text(encoding="utf-8"), namespace)
    # The reference solution is the instructor's trusted code, so we run it directly.
    exec((RAW / f"question_{q}" / "code" / "reference" / "reference.py").read_text(encoding="utf-8"), namespace)
    rng = random.Random(seed)
    tests = []
    while len(tests) < n:
        # eval is safe here: expr is a call WE generated from random numbers/strings (see _inputs),
        # run against the instructor's reference solution, never against student code.
        for expr in _inputs(task_id, rng):
            tests.append({"input": expr, "expected": repr(eval(expr, namespace))})
    return tests
