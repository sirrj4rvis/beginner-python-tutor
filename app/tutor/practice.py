r"""
M6: Practice Generation. Gemini writes a NEW exercise as JSON; we check it before a learner sees it.

    topic + difficulty -> Gemini (JSON in a fixed shape, MBPP style)
        -> check 1: the JSON has the right shape        (pydantic, a data-checking library)
        -> check 2: the test cases are safe and sensible (only literal values; edge cases)
        -> check 3: Gemini's own solution passes all its tests in our sandbox
        -> if any check fails: ask again, telling Gemini what was wrong (at most 3 tries)

Why check 3 matters: a generated exercise can have a wrong test, and then a learner with a
correct answer would be told it is wrong. Running the solution against the tests catches that.
The solution is never shown; the guardrail uses it to block hints that give it away.

Every generation is logged to app/data/practice_log.jsonl (Prompt 7 reports how often the
first try was valid).

Quick test from the app folder:   ..\.venv\Scripts\python.exe -m tutor.practice loops easy
"""
import ast
import hashlib
import json
import keyword
import time

from pydantic import BaseModel, ValidationError

import config
from tutor.gemini_client import generate
from tutor.sandbox import run_code, safety_problem

MAX_TRIES = 3
LOG_FILE = config.DATA_DIR / "practice_log.jsonl"
MBPP_FILE = config.PROJECT_DIR / "dataset" / "problems.json"


class TestCase(BaseModel):
    input: str        # a call, e.g. "count_evens([1, 2, 4])"
    expected: str     # the correct result as a Python value, e.g. "2"


class Exercise(BaseModel):
    title: str
    description: str
    function_name: str
    solution: str
    tests: list[TestCase]


TOPIC_MEANING = {
    "loops": "for and while loops, counting, accumulating a total, stopping early",
    "lists": "creating, indexing, slicing, appending to and filtering lists",
    "functions": "writing a function with parameters and a return value, possibly calling a helper function",
    "built-ins": "built-in functions such as len, sum, min, max, abs, range, enumerate, zip, sorted",
    "sorting": "sorting with sorted() or list.sort(), the key= and reverse= arguments, or a simple sorting loop",
}
DIFFICULTY_MEANING = {
    "easy": "one loop or one condition; the solution is at most 8 lines",
    "medium": "a loop with a condition, or two simple steps; the solution is at most 15 lines",
    "hard": "nested loops or several steps; the solution is at most 25 lines",
}
SYSTEM_INSTRUCTION = (
    "You write short Python practice exercises for complete beginners, in the style of the MBPP "
    "benchmark: one function, a clear one-paragraph description and test cases. Rules:\n"
    "- The learner writes ONE function. No input(), no print(), no files, no classes.\n"
    "- Imports are allowed only from: math, random, string, collections, itertools, functools, heapq, statistics, re. Prefer none.\n"
    "- The description explains what the function must return and gives one example, "
    "but never explains how to solve it.\n"
    "- Give 5 or 6 tests. Each test input is ONE call to the function with literal values only "
    "(numbers, strings, lists, tuples, dicts, True/False/None), e.g. count_evens([1, 2, 4]). "
    "Include at least one edge case, such as an empty list.\n"
    "- Each expected value is the exact Python literal the call returns.\n"
    "- solution is a complete, correct Python solution that passes every test."
)


def mbpp_examples(topic, how_many=2):
    """Two MBPP problems to show Gemini the style (same topic if MBPP has it)."""
    problems = json.loads(MBPP_FILE.read_text(encoding="utf-8"))
    same_topic = [p for p in problems if p["topic"] == topic] or problems
    return "\n\n".join(f"Example (MBPP task {p['mbpp_task_id']}):\n{p['prompt']}\n" + "\n".join(p["test_list"][:3])
                       for p in same_topic[:how_many])


def check_exercise(text, topic, difficulty):
    """Checks 1-3. Returns (problem, None) if the exercise is usable, else (None, reason)."""
    try:                                                        # check 1: the JSON shape
        ex = Exercise.model_validate_json(text)
    except ValidationError as e:
        return None, f"the JSON does not have the required fields ({e.errors()[0]['msg']})"
    name = ex.function_name.strip()
    if not name.isidentifier() or keyword.iskeyword(name):
        return None, f"'{name}' is not a valid function name"
    if not 4 <= len(ex.tests) <= 8:
        return None, f"there are {len(ex.tests)} tests; 5 or 6 are needed"

    tests = []                                                  # check 2: safe, sensible tests
    for t in ex.tests:
        try:
            call = ast.parse(t.input.strip(), mode="eval").body
            ok_call = (isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == name
                       and not call.keywords)
            if ok_call:
                for arg in call.args:
                    ast.literal_eval(arg)                       # raises if not a plain literal value
            ast.literal_eval(t.expected.strip())
        except (SyntaxError, ValueError, TypeError):
            ok_call = False
        if not ok_call:
            return None, f"test '{t.input}' must be one call to {name}() with literal values, and its expected value a literal"
        tests.append({"input": t.input.strip(), "expected": t.expected.strip()})
    if len({t["input"] for t in tests}) < len(tests):
        return None, "two tests are the same"
    if len({t["expected"] for t in tests}) < 2:
        return None, "all tests expect the same result, so they do not check much"

    reason = safety_problem(ex.solution)                        # check 3: the solution really works
    if reason:
        return None, f"the solution is not allowed here: {reason}"
    try:
        defines = any(isinstance(n, ast.FunctionDef) and n.name == name for n in ast.parse(ex.solution).body)
    except SyntaxError as e:
        return None, f"the solution has a syntax error ({e.msg})"
    if not defines:
        return None, f"the solution does not define {name}()"
    problem = {
        "task_id": "gen_" + hashlib.sha1((ex.title + ex.solution).encode("utf-8")).hexdigest()[:8],
        "name": ex.title.strip(), "topic": topic, "difficulty": difficulty,
        "description": ex.description.strip(), "tests": tests, "global_code": "",
        "reference_code": ex.solution,
        "starter_code": "\n\n".join(
            f"def {n.name}({', '.join(a.arg for a in n.args.args)}):\n    pass\n"
            for n in ast.parse(ex.solution).body if isinstance(n, ast.FunctionDef) and n.name == name),
    }
    result = run_code(ex.solution, problem)
    if result["status"] != "pass":
        return None, f"the solution fails its own tests: {result['error_message'] or result['headline']}"
    return problem, None


def generate_exercise(topic, difficulty, avoid_titles=()):
    """Ask Gemini for a checked exercise. Returns (problem, info) where info has
    tries, problems (why earlier tries were rejected), model and seconds.
    problem is None if all tries failed. May raise GeminiUnavailable."""
    base_prompt = (
        f"Write one exercise.\nTopic: {topic} ({TOPIC_MEANING[topic]}).\n"
        f"Difficulty: {difficulty} ({DIFFICULTY_MEANING[difficulty]}).\n\n"
        f"Match the style of these MBPP problems, but write a NEW one:\n\n{mbpp_examples(topic)}\n")
    if avoid_titles:
        base_prompt += "\nDo not repeat these exercises: " + "; ".join(avoid_titles) + "\n"
    rejected, seconds, model, problem = [], 0.0, "", None
    for attempt in range(1, MAX_TRIES + 1):
        prompt = base_prompt
        if rejected:
            prompt += f"\nYour previous exercise was rejected because {rejected[-1]}. Write a corrected one.\n"
        text, model, took = generate(prompt, SYSTEM_INSTRUCTION, temperature=0.9, json_schema=Exercise)
        seconds += took
        problem, reason = check_exercise(text, topic, difficulty)
        if problem:
            break
        rejected.append(reason)
    info = {"tries": attempt, "problems": rejected, "model": model, "seconds": round(seconds, 1)}
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps({"time": time.strftime("%Y-%m-%d %H:%M:%S"), "topic": topic, "difficulty": difficulty,
                            "valid": problem is not None, **info,
                            "title": problem["name"] if problem else None}, ensure_ascii=False) + "\n")
    return problem, info


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    topic, difficulty = (sys.argv[1:3] + ["loops", "easy"][len(sys.argv[1:3]):])
    problem, info = generate_exercise(topic, difficulty)
    print(info)
    if problem:
        print(f"\n{problem['name']}  ({problem['task_id']})\n{problem['description']}\n")
        print(problem["starter_code"])
        for t in problem["tests"]:
            print(f"  {t['input']}  ->  {t['expected']}")
        print("\n(hidden) solution:\n" + problem["reference_code"])
