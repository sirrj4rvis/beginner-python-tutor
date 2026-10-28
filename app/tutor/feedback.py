"""
M4: Guided Feedback, the part of Algorithm 2 (methodology/algorithms.tex) that turns a failed
run into safe hints:

    ask the fine-tuned model -> guardrail check -> if blocked, ask once more (temperature 0.7)
    -> if still blocked, use a safe template hint built from the error -> log every block

The page (app.py) then shows Hint 1, Hint 2 and the Explanation one at a time, on request.
"""
import config
from tutor.guardrail import check_reply, log_block, template_hint
from tutor.ollama_client import ask_tutor


def get_feedback(problem_text, code, run_result, solutions, task_id=""):
    """Hints for a failed run.

    problem_text  the problem description shown to the learner
    code          the learner's code
    run_result    what tutor.sandbox.run_code returned (must not be "pass" or "blocked")
    solutions     correct solutions for the guardrail (never shown)
    Returns the 4 parts plus:
        source    "model" (fine-tuned model) or "template" (safe fallback)
        blocked   the guardrail's reasons for any replies it blocked
        seconds   total model time
    May raise ollama_client.TutorUnavailable (Ollama not running).
    """
    blocked, seconds = [], 0.0
    for attempt in range(config.MAX_MODEL_TRIES):
        temperature = 0.0 if attempt == 0 else config.RETRY_TEMPERATURE
        reply = ask_tutor(problem_text, code, run_result["error_message"], temperature=temperature)
        seconds += reply["seconds"]
        reason = check_reply(reply, solutions, code)
        if reason is None:
            return {**reply, "source": "model", "blocked": blocked, "seconds": round(seconds, 1)}
        blocked.append(reason)
        log_block(task_id, reason, reply["raw"])
    return {**template_hint(run_result), "source": "template", "blocked": blocked, "seconds": round(seconds, 1)}
