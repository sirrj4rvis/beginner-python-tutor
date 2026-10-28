# Dataset: `beginner_bugs.csv`

59 real buggy Python attempts by beginners. Each comes with the real error, its bug type, two levels of hints, an explanation and a minimal fix.

## Where the data comes from
- **Student code:** the public **Refactory** dataset, released under the LGPL-3.0 licence (the licence is in `raw/refactory/LICENSE`).
- **Who wrote it:** 361 undergraduates in an introductory Python course at the National University of Singapore, across 5 programming assignments.
- **Cite it as:** Y. Hu, U. Z. Ahmed, S. Mechtaev, B. Leong, and A. Roychoudhury, "Re-factoring based program repair applied to programming assignments," in *Proc. 34th IEEE/ACM Int. Conf. Automated Softw. Eng. (ASE)*, 2019, pp. 388–398, doi: 10.1109/ASE.2019.00044.
- **Not included in the source:** the dataset authors removed attempts with syntax errors, so our rows contain runtime and logic bugs only.

## How the dataset was built (all steps are scripts in `scripts/`, and reruns give the same result)

| Step | Script | Result |
|---|---|---|
| 1. Run every real wrong attempt against its problem's test cases in a separate, time-limited process; record the real error or first failed test; label bug_type automatically or flag it | `build_candidates.py` (uses `runner.py`) | 1,783 attempts run → **1,722 really fail** a test (61 passed all tests and were dropped; 59 of those are sort_age attempts using `sort()`) |
| 2. Pick a varied sample: 12 per problem, ≤25 lines (≤40 for the 3-function problem), no duplicates, spread across error kinds, seed 42 | `select_rows.py` | 60 rows |
| 3. Draft hint_1, hint_2, explanation and fixed_code with an LLM (Claude), following `LABELING_RULES.md`; the authors then review and correct | `labels/*.json` → `merge_labels.py` | 59 rows (row 36 excluded: its approach can't be fixed with a small change) |
| 4. Validate: no empty cells; valid bug_type; fixed_code passes all course tests **and** matches the reference solution on 40 random inputs; student_code really fails; no leaks of the fix in hints; no duplicates; ≥30 rows | `validate_dataset.py` (uses `random_tests.py`) | **59 rows, 0 problems** |
| 5. Summary tables and charts | `dataset_stats.py` | `stats/` |

## Columns
`id, task_id, topic, difficulty, problem, student_code, error_message, bug_type, hint_1, hint_2, explanation, fixed_code, source_file`

- `task_id` replaces `mbpp_task_id`, because the problems come from Refactory.
- `source_file` points to the original student file, so every row can be traced back to its source.
- `problem` is our own description, written from the course's reference solution and test cases.
- `topic` and `difficulty` are our own judgement for beginners.

## Numbers for the report (59 rows)
| | |
|---|---|
| Topics | loops 12, functions 12, sorting 12, built-ins 12, lists 11 |
| Difficulty | easy 23, medium 24, hard 12 |
| Bug type | runtime 31, logic 28, syntax 0 |

The full tables are in `stats/summary.md`. The charts, sized for one IEEE column at 300 dpi, are `stats/by_topic.png`, `stats/by_difficulty.png` and `stats/by_bug_type.png`.

## Honest limitations (put these in the report)
- **Small:** 59 rows from only 5 problems, so topic variety is narrow.
- **No syntax bugs:** they were filtered out in the source data.
- **AI-drafted labels:** the labels were drafted by an LLM and reviewed by the authors. Say exactly this; do not call them "written by the authors".

## Editing a label
1. Change the row in `labels/refactory_qN.json`.
2. In `dataset/scripts`, run `python merge_labels.py`, then `python validate_dataset.py`, then `python dataset_stats.py`.
3. Read through `REVIEW.md`, which shows every row in an easy-to-read layout.
