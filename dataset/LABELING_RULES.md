# Labelling rules for `beginner_bugs.csv`

Each row is a real wrong attempt by a beginner, taken from the Refactory dataset. The `student_code` and `error_message` columns are never edited. Only these columns are written:

| Column | What it is | Rules |
|---|---|---|
| `bug_type` | The kind of bug | **syntax**: Python can't read the code at all (SyntaxError or IndentationError). **runtime**: the code starts, then crashes on some test (TypeError, IndexError, NameError, and so on). **logic**: the code runs without crashing but gives the wrong answer, or never stops (infinite loop). For rows marked "FLAG", choose the type of the **main** mistake, i.e. the one you would fix first. |
| `hint_1` | A gentle nudge | 1–2 sentences. Points to the **idea** that is wrong, not the line. **No code at all**: no variable names in code style, no snippets. Often a question, e.g. "What should happen when the list is empty?" |
| `hint_2` | A more specific hint | 1–2 sentences. Points to **the exact line or part** (e.g. "Look at the condition in your `for` loop on line 4") and says what is wrong there. Names from the student's own code are fine. **Must not contain the corrected line or any fixed code.** |
| `explanation` | Why it is wrong | 2–4 short sentences in simple words a first-year student understands: what the code does now, why that gives the error shown, and the general rule to remember. No fixed code. |
| `fixed_code` | The corrected code | The student's own code with the **smallest change** that makes all tests pass. Keep their variable names, style and approach. Don't rewrite it as the reference solution. Fix only this bug; leave harmless oddities alone. |

## Style
- Write for a beginner: short sentences, no jargon. If a term is needed, explain it ("an *index* is the position of an item").
- Be kind and encouraging. Never say "wrong" about the student. Talk about the code ("this line…").
- The hints are what our model learns to say, so keep a consistent voice across rows.
- If a row has two bugs, the hints and explanation focus on the first one to fix. The `fixed_code` fixes all of them, because it must pass every test.

## What `validate_dataset.py` checks automatically
- No empty cells, and bug_type is syntax, runtime or logic.
- `fixed_code` passes every test, and `student_code` fails at least one.
- No hint or explanation contains a line of the fixed code, a code block, or a `def`.
- No duplicate rows, and at least 30 rows.

## Example rows (real rows from the dataset)

### Row 25: runtime bug (`refactory_q3`, remove_extras)
```python
def remove_extras(lst):
    new_list = []
    for item in list:
        if new_list.count(item) == 0:
            new_list.append(item)
    return new_list
```
- **error_message:** `Test: remove_extras([1, 1, 1, 2, 3])` → `TypeError: 'type' object is not iterable (line 3)`
- **bug_type:** runtime
- **hint_1:** Which list is your loop really going through? Make sure it walks over the list that was given to the function.
- **hint_2:** On line 3 the loop uses `list`, which is Python's built-in list type, not your parameter `lst`.
- **explanation:** In Python, `list` is the name of the built-in list type, so the loop tries to go through the type itself instead of your data. That is why Python says a 'type' object is not iterable. Your input is called `lst`, so the loop has to use that name. Always loop over the parameter you were given, and avoid naming your own variables after built-ins like list, str or max.
- **fixed_code:** the same code with line 3 changed so the loop goes over `lst`.

### Row 26: logic bug (`refactory_q3`, remove_extras)
```python
def remove_extras(lst):
    lst2 = []
    for x in lst:
        if lst.count(x) < 1:
            lst2.append(x)
    return lst2
```
- **error_message:** `Test: remove_extras([1, 1, 1, 2, 3])` / `Expected: [1, 2, 3]` / `Got: []`
- **bug_type:** logic
- **hint_1:** Think about what count gives for an item you took from that very same list. Can it ever be less than 1?
- **hint_2:** On line 4 you count `x` inside `lst`, the input list, which always contains `x`. Check the list you are building, `lst2`, instead.
- **explanation:** Every `x` comes from `lst`, so counting it in `lst` always gives at least 1, and the condition is never true. That is why nothing is added and an empty list comes back. To keep only the first copy of each item, check the list you are building, because it only holds the items you have already kept.
- **fixed_code:** the same code with line 4 counting `x` in `lst2` instead of `lst`.
