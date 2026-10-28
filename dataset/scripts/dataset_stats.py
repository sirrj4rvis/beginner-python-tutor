"""
Step 5: summary numbers and charts of the finished dataset, for the report.

Writes to dataset/stats/:
  summary.md          tables: rows per topic, per difficulty, per bug type, and topic x bug type
  summary.csv         the same counts in one CSV (category, value, rows)
  by_topic.png, by_difficulty.png, by_bug_type.png   bar charts (300 dpi, one IEEE column wide)

Run:  python dataset_stats.py            (uses beginner_bugs.csv)
"""
import csv
import sys
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")                      # draw to files, no window needed
import matplotlib.pyplot as plt

DATASET_DIR = Path(__file__).resolve().parent.parent
OUT = DATASET_DIR / "stats"

BAR = "#2a78d6"                            # one colour: each chart has a single series
INK, INK_SOFT, GRID = "#0b0b0b", "#52514e", "#e4e3df"
ORDER = {"difficulty": ["easy", "medium", "hard"], "bug_type": ["syntax", "runtime", "logic"]}
TITLES = {"topic": "Rows per topic", "difficulty": "Rows per difficulty", "bug_type": "Rows per bug type"}


def ordered(column, counts):
    keys = ORDER.get(column) or sorted(counts, key=lambda k: (-counts[k], k))
    return [(k, counts.get(k, 0)) for k in keys]


def bar_chart(column, pairs, path):
    labels, values = [p[0] for p in pairs], [p[1] for p in pairs]
    fig, ax = plt.subplots(figsize=(3.5, 2.2), dpi=300)    # 3.5 in = one IEEE column
    bars = ax.bar(labels, values, width=0.6, color=BAR, edgecolor="white", linewidth=1.5, zorder=3)
    for b, v in zip(bars, values):                        # few bars, so a label on each is readable
        ax.text(b.get_x() + b.get_width() / 2, v, str(v), ha="center", va="bottom", fontsize=7, color=INK)
    ax.set_title(TITLES[column], fontsize=8, color=INK, loc="left")
    ax.set_ylabel("Rows", fontsize=7, color=INK_SOFT)
    ax.tick_params(labelsize=7, colors=INK_SOFT, length=0)
    ax.set_ylim(0, max(values) * 1.18 + 1)
    ax.grid(axis="y", color=GRID, linewidth=0.6, zorder=0)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(INK_SOFT)
    fig.tight_layout()
    fig.savefig(path, facecolor="white")
    plt.close(fig)


def md_table(title, header, pairs, total):
    lines = [f"### {title}", "", f"| {header} | Rows | % |", "|---|---:|---:|"]
    lines += [f"| {k} | {v} | {100 * v / total:.1f} |" for k, v in pairs]
    lines += [f"| **Total** | **{total}** | 100 |", ""]
    return lines


def main(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    total = len(rows)
    OUT.mkdir(exist_ok=True)
    md = [f"# Dataset summary ({total} rows)", ""]
    csv_rows = []
    for column in ("topic", "difficulty", "bug_type"):
        pairs = ordered(column, Counter(r[column] for r in rows))
        md += md_table(TITLES[column], column, pairs, total)
        csv_rows += [(column, k, v) for k, v in pairs]
        bar_chart(column, pairs, OUT / f"by_{column}.png")

    # Cross table: which kinds of bugs appear in which topic.
    bug_types = [k for k, _ in ordered("bug_type", Counter(r["bug_type"] for r in rows))]
    topics = [k for k, _ in ordered("topic", Counter(r["topic"] for r in rows))]
    md += ["### Topic x bug type", "", "| topic | " + " | ".join(bug_types) + " | total |",
           "|---|" + "---:|" * (len(bug_types) + 1)]
    for t in topics:
        counts = [sum(r["topic"] == t and r["bug_type"] == b for r in rows) for b in bug_types]
        md.append(f"| {t} | " + " | ".join(map(str, counts)) + f" | {sum(counts)} |")

    (OUT / "summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    with open(OUT / "summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["category", "value", "rows"])
        w.writerows(csv_rows)
    print("\n".join(md))
    print(f"\nCharts and tables saved in {OUT}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else DATASET_DIR / "beginner_bugs.csv")
