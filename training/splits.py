"""
Balanced ("stratified") splits of the dataset, with a fixed random seed.

Stratified means: every group of rows with the same (difficulty, bug_type) is split in the same
proportion, so the test set has the same mix of easy/medium/hard and runtime/logic as the whole
dataset. A random split could, by bad luck, put all the hard rows in training.

The notebook copies this file's code, so if you change it here, rebuild the notebook
(python build_notebook.py).
"""
import random
from collections import defaultdict


def _groups(rows, seed):
    rng = random.Random(seed)
    groups = defaultdict(list)
    for r in rows:
        groups[(r["difficulty"], r["bug_type"])].append(r)
    for key in sorted(groups):
        rng.shuffle(groups[key])
    return {k: groups[k] for k in sorted(groups)}


def stratified_split(rows, test_fraction=0.2, seed=42):
    """Return (train_rows, test_rows). The test size is round(len(rows) * test_fraction)."""
    groups = _groups(rows, seed)
    total_test = round(len(rows) * test_fraction)
    # Each group gets its fair share; leftover places go to the groups with the biggest remainder.
    exact = {k: len(g) * test_fraction for k, g in groups.items()}
    take = {k: int(v) for k, v in exact.items()}
    for k in sorted(groups, key=lambda k: exact[k] - take[k], reverse=True)[: total_test - sum(take.values())]:
        take[k] += 1
    train, test = [], []
    for k, g in groups.items():
        test += g[: take[k]]
        train += g[take[k]:]
    return sorted(train, key=lambda r: int(r["id"])), sorted(test, key=lambda r: int(r["id"]))


def stratified_kfold(rows, k=5, seed=42):
    """Return a list of k lists of row ids. Each row is in exactly one fold; folds are balanced."""
    folds = [[] for _ in range(k)]
    next_fold = 0
    for g in _groups(rows, seed).values():
        for r in g:                      # deal rows out like cards, continuing where the last group stopped
            folds[next_fold].append(int(r["id"]))
            next_fold = (next_fold + 1) % k
    return [sorted(f) for f in folds]
