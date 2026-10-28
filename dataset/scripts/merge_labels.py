"""
Step 3: put the labels into the dataset.

Reads dataset_unlabeled.csv plus every labels/*.json file and writes:
  beginner_bugs.csv   the final dataset (only rows that have labels)
  REVIEW.md           the same rows in an easy-to-read layout, for the authors to skim and correct

If you correct a label, edit the JSON file in labels/ and run this script again.
Run:  python merge_labels.py
"""
import csv
import json
from pathlib import Path

DATASET_DIR = Path(__file__).resolve().parent.parent
FIELDS = ["bug_type", "hint_1", "hint_2", "explanation", "fixed_code"]


def main():
    labels = {}
    for f in sorted((DATASET_DIR / "labels").glob("*.json")):
        for lab in json.loads(f.read_text(encoding="utf-8")):
            labels[str(lab["id"])] = lab

    with open(DATASET_DIR / "dataset_unlabeled.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        columns, rows = reader.fieldnames, list(reader)

    final, missing, excluded = [], [], []
    for row in rows:
        lab = labels.get(row["id"])
        if not lab:
            missing.append(row["id"])
            continue
        if "exclude_reason" in lab:          # a row we decided to leave out, with the reason recorded
            excluded.append(f"row {row['id']}: {lab['exclude_reason']}")
            continue
        final.append({**row, **{k: lab[k] for k in FIELDS}})

    with open(DATASET_DIR / "beginner_bugs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(final)

    md = ["# Dataset review", "",
          "Skim each row. If something is off, edit that row in `labels/<task>.json`, then run "
          "`python merge_labels.py` and `python validate_dataset.py` in `dataset/scripts`.", ""]
    for r in final:
        md += [f"## Row {r['id']}: {r['task_id']} ({r['topic']}, {r['difficulty']}): {r['bug_type']}", "",
               "**Student code**", "```python", r["student_code"].rstrip(), "```",
               "**Error**", "```", r["error_message"], "```",
               f"- **Hint 1:** {r['hint_1']}", f"- **Hint 2:** {r['hint_2']}",
               f"- **Explanation:** {r['explanation']}", "",
               "**Fixed code**", "```python", r["fixed_code"].rstrip(), "```", "", "---", ""]
    (DATASET_DIR / "REVIEW.md").write_text("\n".join(md), encoding="utf-8")

    print(f"{len(final)} labelled rows -> beginner_bugs.csv and REVIEW.md")
    for e in excluded:
        print("Excluded", e)
    if missing:
        print(f"Rows without labels yet: {', '.join(missing)}")


if __name__ == "__main__":
    main()
