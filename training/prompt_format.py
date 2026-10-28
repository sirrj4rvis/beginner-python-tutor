"""
The ONE place that defines how we talk to the tutor model.

Training (the Colab notebook) and the app (Guided Feedback) must use exactly the same
system prompt and message layout; otherwise the fine-tuned model sees something new in the app
and behaves worse. The notebook copies this file's code, so if you change it here,
rebuild the notebook (python build_notebook.py).

Input  (user message): problem + student code + the real error message
Output (assistant reply), always in this fixed format:
    Bug type: <syntax | runtime | logic>
    Hint 1: <gentle nudge, no code>
    Hint 2: <points to the exact line, no fixed code>
    Explanation: <why it is wrong, in simple words>
"""
import re

SYSTEM_PROMPT = (
    "You are a patient Python tutor for beginners. A student's code has a bug. "
    "Never write the corrected code or a full solution. "
    "Reply in exactly this format:\n"
    "Bug type: <syntax, runtime or logic>\n"
    "Hint 1: <a gentle nudge about the idea, with no code>\n"
    "Hint 2: <point to the exact line and what is wrong there, without the fix>\n"
    "Explanation: <why the code fails, in simple words>"
)


def user_message(problem, student_code, error_message):
    return (f"Problem:\n{problem}\n\n"
            f"Student code:\n```python\n{student_code.rstrip()}\n```\n\n"
            f"Error or failed test:\n{error_message}")


def assistant_message(bug_type, hint_1, hint_2, explanation):
    return (f"Bug type: {bug_type}\n"
            f"Hint 1: {hint_1}\n"
            f"Hint 2: {hint_2}\n"
            f"Explanation: {explanation}")


def build_messages(row, with_answer=True):
    """Chat messages for one dataset row (a dict with the CSV columns)."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message(row["problem"], row["student_code"], row["error_message"])}]
    if with_answer:
        messages.append({"role": "assistant", "content": assistant_message(
            row["bug_type"], row["hint_1"], row["hint_2"], row["explanation"])})
    return messages


def parse_reply(text):
    """Split a model reply back into its parts. Missing parts come back as ''."""
    parts = {"bug_type": "", "hint_1": "", "hint_2": "", "explanation": ""}
    labels = {"Bug type": "bug_type", "Hint 1": "hint_1", "Hint 2": "hint_2", "Explanation": "explanation"}
    pattern = re.compile(r"^(Bug type|Hint 1|Hint 2|Explanation)\s*:\s*", re.MULTILINE)
    matches = list(pattern.finditer(text))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        parts[labels[m.group(1)]] = text[m.end():end].strip()
    parts["bug_type"] = parts["bug_type"].lower().strip(" .")
    return parts
