r"""
M7: Progress tracking in SQLite, plus the next-topic and difficulty choice (Algorithm 3).

SQLite is a whole database in ONE file (app/data/progress.db). It comes with Python, so there is
no server to install. Tables:
    runs      every time a learner runs code (status, tests passed)
    hints     every hint level a learner opens (and whether it came from the model or the template)
    results   one row when a learner FINISHES an exercise: help used, credit, mastery before/after
    mastery   one row per learner and topic: the current mastery score m (0 to 1) and how many done

The rules (methodology/METHODOLOGY_NOTES.md, section 3; Algorithms 2 and 3):
    credit c  = 1.0 / 0.75 / 0.5 / 0.25 for solving after 0 / 1 / 2 / 3 help levels, 0 for giving up
    mastery   m <- m + 0.3 * (c - m)          (starts at 0; recent exercises count more)
    next topic: an unseen topic first (curriculum order), else the weakest not-yet-mastered topic
    difficulty: m < 0.4 easy, m < 0.7 medium, otherwise hard
Each exercise changes mastery only the FIRST time a learner finishes it.

Quick test from the app folder:   ..\.venv\Scripts\python.exe -m tutor.progress
"""
import sqlite3
import time
from contextlib import contextmanager

import config

DB_FILE = config.DATA_DIR / "progress.db"

TABLES = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY, learner TEXT, time TEXT, task_id TEXT, topic TEXT, difficulty TEXT,
    source TEXT, status TEXT, passed INTEGER, total INTEGER, code TEXT);
CREATE TABLE IF NOT EXISTS hints (
    id INTEGER PRIMARY KEY, learner TEXT, time TEXT, task_id TEXT, level INTEGER,
    source TEXT, seconds REAL, blocked INTEGER);
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY, learner TEXT, time TEXT, task_id TEXT, name TEXT, topic TEXT,
    difficulty TEXT, outcome TEXT, help_used INTEGER, credit REAL, mastery_before REAL, mastery_after REAL);
CREATE TABLE IF NOT EXISTS mastery (
    learner TEXT, topic TEXT, mastery REAL, done INTEGER, PRIMARY KEY (learner, topic));
"""


@contextmanager
def _db():
    """Open the database file (creating the tables the first time), save the changes, close it."""
    connection = sqlite3.connect(DB_FILE)
    try:
        connection.executescript(TABLES)
        yield connection
        connection.commit()
    finally:
        connection.close()


def _now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def source_of(problem):
    return "practice" if problem["task_id"].startswith("gen_") else "course"


def log_run(learner, problem, result):
    with _db() as db:
        db.execute("INSERT INTO runs (learner, time, task_id, topic, difficulty, source, status, passed, total, code) "
                   "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   (learner, _now(), problem["task_id"], problem["topic"], problem["difficulty"], source_of(problem),
                    result["status"], result["passed"], result["total"], result.get("code", "")))


def log_hint(learner, task_id, level, feedback):
    with _db() as db:
        db.execute("INSERT INTO hints (learner, time, task_id, level, source, seconds, blocked) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (learner, _now(), task_id, level, feedback["source"], feedback["seconds"], len(feedback["blocked"])))


def get_mastery(learner):
    """{topic: (mastery, exercises done)} for every topic, 0 for topics not started."""
    with _db() as db:
        rows = dict(((t, (m, n)) for t, m, n in
                     db.execute("SELECT topic, mastery, done FROM mastery WHERE learner = ?", (learner,))))
    return {topic: rows.get(topic, (0.0, 0)) for topic in config.TOPICS}


def already_finished(learner, task_id):
    with _db() as db:
        return db.execute("SELECT 1 FROM results WHERE learner = ? AND task_id = ?", (learner, task_id)).fetchone() is not None


def finish(learner, problem, help_used, gave_up=False):
    """Algorithm 2, lines 18-20: credit for the help used, update the topic's mastery, save.
    Returns the saved result, or None if this learner already finished this exercise."""
    if already_finished(learner, problem["task_id"]):
        return None
    credit = 0.0 if gave_up else config.HINT_CREDIT[help_used]
    before, done = get_mastery(learner)[problem["topic"]]
    after = round(before + config.MASTERY_RATE * (credit - before), 3)
    with _db() as db:
        db.execute("INSERT INTO results (learner, time, task_id, name, topic, difficulty, outcome, help_used, credit, "
                   "mastery_before, mastery_after) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   (learner, _now(), problem["task_id"], problem["name"], problem["topic"], problem["difficulty"],
                    "gave up" if gave_up else "solved", help_used, credit, before, after))
        db.execute("INSERT OR REPLACE INTO mastery (learner, topic, mastery, done) VALUES (?, ?, ?, ?)",
                   (learner, problem["topic"], after, done + 1))
    return {"credit": credit, "before": before, "after": after, "gave_up": gave_up}


def difficulty_for(m):
    if m < config.EASY_BELOW:
        return "easy"
    return "medium" if m < config.MEDIUM_BELOW else "hard"


def next_step(learner):
    """Algorithm 3: the next topic and difficulty for this learner. Returns (topic, difficulty, why)."""
    scores = get_mastery(learner)
    unseen = [t for t in config.TOPICS if scores[t][1] == 0]
    if unseen:
        topic, why = unseen[0], "a topic you have not tried yet"
    else:
        open_topics = [t for t in config.TOPICS if scores[t][0] < config.MASTERED] or config.TOPICS
        topic = min(open_topics, key=lambda t: (scores[t][0], config.TOPICS.index(t)))   # ties: earlier topic
        why = "your weakest topic" if scores[topic][0] < config.MASTERED else "all topics mastered: keep practising"
    return topic, difficulty_for(scores[topic][0]), why


def history(learner, limit=20):
    with _db() as db:
        db.row_factory = sqlite3.Row
        return [dict(r) for r in db.execute(
            "SELECT time, name, topic, difficulty, outcome, help_used, credit, mastery_after FROM results "
            "WHERE learner = ? ORDER BY id DESC LIMIT ?", (learner, limit))]


def reset(learner):
    """Delete one learner's results and mastery (runs and hints stay, for the evaluation)."""
    with _db() as db:
        db.execute("DELETE FROM results WHERE learner = ?", (learner,))
        db.execute("DELETE FROM mastery WHERE learner = ?", (learner,))


if __name__ == "__main__":
    # Walk through Algorithm 3 with a made-up learner, then remove them again.
    who = "_selftest"
    reset(who)
    print("start:", next_step(who))
    for topic, help_used in [("loops", 0), ("lists", 2), ("functions", 3), ("built-ins", 1), ("sorting", 0)]:
        r = finish(who, {"task_id": f"t_{topic}", "name": topic, "topic": topic, "difficulty": "easy"}, help_used)
        print(f"finished {topic:9} with help {help_used}: credit {r['credit']}, mastery {r['before']} -> {r['after']}")
    print("same exercise again counts?", finish(who, {"task_id": "t_loops", "name": "x", "topic": "loops", "difficulty": "easy"}, 0))
    print("next:", next_step(who))
    for i in range(6):
        finish(who, {"task_id": f"f{i}", "name": "f", "topic": "functions", "difficulty": "easy"}, 0)
    print("after 6 more functions exercises without help:", {t: v[0] for t, v in get_mastery(who).items()})
    print("next:", next_step(who))
    reset(who)
    with _db() as db:
        db.execute("DELETE FROM runs WHERE learner = ?", (who,))
