r"""
The Streamlit web page: the only file you run.

    .venv\Scripts\python.exe -m streamlit run app\app.py

Streamlit re-runs this whole script from top to bottom every time the learner clicks
something. That is why it reads like a normal script and not like a web server.
The 4 modes: Guided Feedback (M1-M4), Concept Explanation (M5), Practice Generation (M6) and
My Progress (M7). Every finished exercise updates the learner's mastery in SQLite.
"""
import json
import sys
import threading
import urllib.request

# Streamlit re-runs this file on every click but keeps already-imported modules in memory, so
# after we change config.py or a tutor/ file, a refresh would mix old and new code (this caused
# an ImportError and an AttributeError). Forgetting OUR modules here makes every run use the
# current files. It costs a few milliseconds; installed packages (ChromaDB etc.) stay loaded.
for _name in [m for m in sys.modules if m in ("config", "prompt_format", "runner") or m.split(".")[0] == "tutor"]:
    del sys.modules[_name]

import streamlit as st
from code_editor import code_editor

import config
from tutor.examples import load_course_problems, load_test_rows
from tutor import progress, rag
from tutor.feedback import get_feedback
from tutor.gemini_client import GeminiUnavailable
from tutor.ollama_client import TutorUnavailable, warm_up
from tutor.practice import generate_exercise
from tutor.sandbox import run_code

st.set_page_config(page_title="Beginner Python Tutor", page_icon="🐍", layout="wide")


# The button shown in the bottom-right corner of the code editor; "submit" sends the code to the app.
RUN_BUTTON = [{"name": "Run my code", "feather": "Play", "primary": True, "hasText": True,
               "showWithIcon": True, "alwaysOn": True, "commands": ["submit"],
               "style": {"bottom": "0.5rem", "right": "0.5rem", "color": "white", "opacity": 1,
                         "backgroundColor": "#ff4b4b", "borderRadius": "0.5rem", "padding": "0.3rem 0.8rem"}}]


@st.cache_data
def course_problems():
    """Read the problem files once, not on every click."""
    return load_course_problems()


@st.cache_resource
def start_warm_up():
    """Runs once per app start: load the fine-tuned model in a background thread, so the page is
    not blocked and the learner's first hint is not slowed down by loading the model."""
    threading.Thread(target=warm_up, daemon=True).start()
    return True


@st.cache_resource
def notes_collection():
    """Open ChromaDB once per app start (it re-indexes by itself if the notes changed)."""
    return rag.get_collection()


def ollama_status():
    """Is Ollama running, and does it have our fine-tuned model? Returns (ok, message)."""
    try:
        with urllib.request.urlopen(f"{config.OLLAMA_URL}/api/tags", timeout=3) as response:
            names = [m["name"] for m in json.loads(response.read())["models"]]
    except OSError:
        return False, f"Ollama is not running at {config.OLLAMA_URL}. Start the Ollama app."
    if any(name.split(":")[0] == config.TUTOR_MODEL for name in names):
        return True, f"Ollama is running and has the model '{config.TUTOR_MODEL}'."
    return False, f"Ollama is running but has no model '{config.TUTOR_MODEL}'. Run: ollama create {config.TUTOR_MODEL} -f Modelfile"


def gemini_status():
    """Only checks that a key is present; the key itself is never shown on the page."""
    if config.GEMINI_API_KEY:
        return True, f"Gemini key found in .env (model: {config.GEMINI_MODEL})."
    return False, "No Gemini key yet. Put GEMINI_API_KEY=... in the .env file, then refresh."


HELP_NAMES = ["no help", "Hint 1", "Hint 2", "the explanation"]   # help level 0-3


def show_help(key, ask_for_feedback, on_new_level=None):
    """Progressive help for ONE failed run: Hint 1, then Hint 2, then the Explanation, each only
    when the learner asks. key names the run; ask_for_feedback() calls the tutor (with guardrail);
    on_new_level(level, feedback), if given, is called each time a new level opens (M7 logs it).
    Returns the help level reached (0 = no hint asked yet)."""
    state = st.session_state.setdefault("help", {}).setdefault(key, {"level": 0, "feedback": None})
    if state["level"] == 0:
        if st.button("💡 Get a hint", type="primary", key=f"hint_{key}"):
            with st.spinner("The tutor is reading your code (about 10–20 s on this laptop)..."):
                try:
                    state["feedback"], state["level"] = ask_for_feedback(), 1
                except TutorUnavailable as e:
                    st.error(str(e))
                    return 0
            if on_new_level:
                on_new_level(1, state["feedback"])
            st.rerun()   # draw the page again, now with Hint 1
        return 0

    feedback = state["feedback"]
    if feedback["source"] == "model":
        note = "fine-tuned model"
    else:
        note = "safe fallback hint: the guardrail blocked the tutor's reply because it gave too much away"
    st.caption(f"Bug type: **{feedback['bug_type'] or '?'}** · {note} · {feedback['seconds']} s")
    st.info(f"**Hint 1:** {feedback['hint_1']}")
    if state["level"] >= 2:
        st.warning(f"**Hint 2:** {feedback['hint_2']}")
    if state["level"] >= 3:
        st.success(f"**Explanation:** {feedback['explanation']}")
    if state["level"] < 3:
        if st.button("Show Hint 2" if state["level"] == 1 else "Show explanation", key=f"more_{key}"):
            state["level"] += 1
            if on_new_level:
                on_new_level(state["level"], feedback)
            st.rerun()
    return state["level"]


def show_try_it_yourself():
    """M3 + M4: the learner picks one of the 5 course problems and solves it."""
    problems = {f"{p['name']} · {p['topic']} · {p['difficulty']}": p for p in course_problems()}
    solve_problem(problems[st.selectbox("Choose a problem", problems)])


def solve_problem(problem):
    """The learner writes code for a problem (a course problem or a generated exercise), the
    sandbox runs it, and on a failure the fine-tuned model gives hints one level at a time
    (Algorithm 2). problem needs: task_id, description, tests, starter_code, reference_code."""
    task = problem["task_id"]
    st.markdown(problem["description"])

    # A real code editor (Ace): Tab indents by 4 spaces, with line numbers and colours.
    # The Run button sits INSIDE the editor (Ctrl+Enter does the same), so the code and the
    # "run" command reach the app together. One editor per problem (the key).
    st.markdown("**Your code** (Tab indents · Shift+Tab un-indents · Ctrl+Enter runs)")
    editor = code_editor(problem["starter_code"], lang="python", height=[12, 24],
                         key=f"editor_{task}", buttons=RUN_BUTTON,
                         # The default 15 px top margin shifts the line numbers after typing; turn it off.
                         props={"scrollMargin": [0, 0, 0, 0]},
                         # No auto-complete pop-ups: for beginners, Enter must always mean "new line".
                         # Line numbers matter: Hint 2 says things like "on line 6".
                         options={"tabSize": 4, "useSoftTabs": True, "showPrintMargin": False,
                                  "showGutter": True, "showLineNumbers": True,
                                  "enableLiveAutocompletion": False, "enableBasicAutocompletion": False,
                                  "enableSnippets": False})

    # The editor returns its last "submit" on EVERY re-run, each with an id. Run the code only
    # for a new id, and keep the result in session_state so it stays on screen after other clicks.
    learner = current_learner()
    runs = st.session_state.setdefault("runs", {})
    most_help = st.session_state.setdefault("most_help", {})   # highest help level before solving
    last = runs.get(task)
    if editor["type"] == "submit" and (last is None or last["id"] != editor["id"]):
        with st.spinner("Running your code against the tests..."):
            last = runs[task] = {"id": editor["id"], "code": editor["text"],
                                 "result": run_code(editor["text"], problem)}
        progress.log_run(learner, problem, {**last["result"], "code": editor["text"]})
        if last["result"]["status"] == "pass":   # solved: credit for the help used, update mastery (M7)
            last["help_used"] = most_help.pop(task, 0)
            last["saved"] = progress.finish(learner, problem, last["help_used"])
    if last is None:
        return
    result = last["result"]

    if result["status"] == "pass":
        st.success(f"{result['headline']} Help used: {HELP_NAMES[last['help_used']]}.")
        show_saved(last["saved"], problem["topic"])
    elif result["status"] == "blocked":
        st.warning(result["headline"])
    else:
        st.error(result["headline"])
        with st.expander("What Python reported (this is what the tutor reads)"):
            st.code(result["error_message"], language="text")
    if result["tests"]:
        st.dataframe(
            [{"Result": "✅" if t["status"] == "pass" else "❌",
              "Test": t["input"],
              "Expected": t["expected"],
              "Got": t.get("got") or f"{t.get('type')}: {t.get('message')}"} for t in result["tests"]],
            hide_index=True, width="stretch")

    if result["status"] not in ("pass", "blocked"):
        level = show_help(f"{task}:{last['id']}",
                          lambda: get_feedback(problem["description"], last["code"], result,
                                               [problem["reference_code"]], task),
                          on_new_level=lambda lvl, fb: progress.log_hint(learner, task, lvl, fb))
        most_help[task] = max(most_help.get(task, 0), level)
        if not progress.already_finished(learner, task):
            if st.button("🏳️ I give up on this one", key=f"giveup_{task}"):
                last["gave_up"] = progress.finish(learner, problem, most_help.pop(task, 0), gave_up=True)
                st.rerun()
        elif last.get("gave_up"):
            show_saved(last["gave_up"], problem["topic"])


def current_learner():
    """The name typed in the sidebar (each name has its own progress)."""
    return (st.session_state.get("learner") or "guest").strip()[:40] or "guest"


def go_practise(topic, difficulty):
    """Button callback: open Practice Generation with the suggested topic and difficulty.
    (Callbacks run before the page is drawn, so they may change widget values.)"""
    st.session_state.update(mode="Practice Generation", practice_topic=topic, practice_difficulty=difficulty)


def show_next_step(learner, key):
    """Algorithm 3: what to practise next, with a button that opens it."""
    topic, difficulty, why = progress.next_step(learner)
    left, right = st.columns([4, 1.4], vertical_alignment="center")
    left.info(f"**Next for you:** {topic} · {difficulty} ({why})")
    right.button("Practise it →", key=f"next_{key}", on_click=go_practise, args=(topic, difficulty),
                 width="stretch")


def show_saved(saved, topic):
    """What finishing this exercise did to the learner's progress."""
    if saved is None:
        st.caption("You finished this exercise before, so your progress did not change this time.")
        return
    what = "Not solved" if saved["gave_up"] else "Progress saved"
    st.caption(f"{what}: credit {saved['credit']} · {topic} mastery {saved['before']:.0%} → {saved['after']:.0%}")
    show_next_step(current_learner(), key=topic)


def show_test_row_demo():
    """M2 + M4: a real student attempt from our test rows, with the same guarded, step-by-step help."""
    rows = load_test_rows()
    labels = {f"Row {r['id']} · {r['topic']} · {r['difficulty']}": r for r in rows}
    row = labels[st.selectbox("Choose a real student attempt (test rows: the model never saw these)", labels)]

    st.markdown(f"**Problem**\n\n{row['problem']}")
    left, right = st.columns(2)
    left.markdown("**Student code**")
    left.code(row["student_code"], language="python", line_numbers=True)
    right.markdown("**What Python reported**")
    right.code(row["error_message"], language="text")

    reference = next(p["reference_code"] for p in course_problems() if p["task_id"] == row["task_id"])
    run_result = {"status": "timeout" if row["error_message"].startswith("Timed out") else "fail",
                  "error_message": row["error_message"]}
    level = show_help(f"row_{row['id']}", lambda: get_feedback(
        row["problem"], row["student_code"], run_result, [reference, row["fixed_code"]], row["task_id"]))

    if level:
        with st.expander("Compare with our dataset answer (for testing only)"):
            st.write(f"**Bug type:** {row['bug_type']}")
            st.write(f"**Hint 1:** {row['hint_1']}")
            st.write(f"**Hint 2:** {row['hint_2']}")
            st.write(f"**Explanation:** {row['explanation']}")
            st.markdown("**Raw model reply**")
            st.code(st.session_state["help"][f"row_{row['id']}"]["feedback"]["raw"], language="text")


def show_practice_generation():
    """M6: Gemini writes a new exercise for the chosen topic and level; it is checked (JSON shape,
    safe tests, solution passes its tests) and then solved with the same Guided Feedback."""
    st.write("Get a **new** exercise for your topic and level. Each one is checked before you see "
             "it: its hidden solution must pass all of its tests.")
    left, middle, right = st.columns([2, 2, 1.4], vertical_alignment="bottom")
    # Start on Algorithm 3's suggestion (M7); the learner can still choose anything.
    suggested_topic, suggested_difficulty, why = progress.next_step(current_learner())
    st.session_state.setdefault("practice_topic", suggested_topic)
    st.session_state.setdefault("practice_difficulty", suggested_difficulty)
    topic = left.selectbox("Topic", config.TOPICS, key="practice_topic")
    difficulty = middle.selectbox("Difficulty", ["easy", "medium", "hard"], key="practice_difficulty")
    st.caption(f"Suggested for you: {suggested_topic} · {suggested_difficulty} ({why})")
    practice = st.session_state.setdefault("practice", {"problem": None, "info": None, "titles": []})
    if right.button("✨ New exercise", type="primary", width="stretch"):
        with st.spinner("Gemini is writing an exercise and we are checking it (about 10–60 s)..."):
            try:
                problem, info = generate_exercise(topic, difficulty, avoid_titles=practice["titles"][-10:])
            except GeminiUnavailable as e:
                st.error(str(e))
                return
        if problem is None:
            st.error(f"Gemini could not write a valid exercise in {info['tries']} tries "
                     f"(last problem: {info['problems'][-1]}). Please try again.")
            return
        practice.update(problem=problem, info=info)
        practice["titles"].append(problem["name"])

    problem, info = practice["problem"], practice["info"]
    if problem is None:
        st.info("Choose a topic and difficulty, then click **✨ New exercise**.")
        return
    st.subheader(problem["name"])
    checked = f"checked: its solution passes all {len(problem['tests'])} tests"
    tries = "1st try" if info["tries"] == 1 else f"{info['tries']} tries"
    st.caption(f"{problem['topic']} · {problem['difficulty']} · {checked} · {info['model']}, {tries}, {info['seconds']} s")
    solve_problem(problem)


def show_my_progress():
    """M7: mastery per topic, recent exercises and the next suggestion, from SQLite."""
    learner = current_learner()
    st.write(f"Progress for **{learner}**. Mastery goes from 0% to 100%. Each finished exercise moves it "
             f"30% of the way towards the credit you earned: 1.0 with no hints, 0.75 after Hint 1, "
             f"0.5 after Hint 2, 0.25 after the explanation, 0 if you gave up.")
    scores = progress.get_mastery(learner)
    everything = progress.history(learner, limit=100_000)
    recent = everything[:20]
    first, second, third = st.columns(3)
    first.metric("Exercises finished", len(everything))
    second.metric("Solved without hints", sum(r["outcome"] == "solved" and r["help_used"] == 0 for r in everything))
    third.metric("Topics mastered", f"{sum(m >= config.MASTERED for m, _ in scores.values())} of {len(config.TOPICS)}")

    st.subheader("Mastery per topic")
    for topic in config.TOPICS:
        m, done = scores[topic]
        label = "mastered ✓" if m >= config.MASTERED else f"next level: {progress.difficulty_for(m)}"
        st.progress(m, text=f"**{topic}**: {m:.0%} · {done} done · {label}")
    show_next_step(learner, key="progress_page")

    st.subheader("Recent exercises")
    if not recent:
        st.caption("Nothing finished yet. Solve an exercise in Guided Feedback or Practice Generation.")
    else:
        st.dataframe([{"When": r["time"], "Exercise": r["name"], "Topic": r["topic"], "Level": r["difficulty"],
                       "Outcome": r["outcome"], "Help used": HELP_NAMES[r["help_used"]],
                       "Credit": r["credit"], "Mastery after": f"{r['mastery_after']:.0%}"} for r in recent],
                     hide_index=True, width="stretch")
    with st.expander("Start again"):
        if st.checkbox(f"Yes, delete all progress for '{learner}'"):
            if st.button("Delete my progress"):
                progress.reset(learner)
                st.rerun()


EXAMPLE_QUESTIONS = ["What does range(5) give me?", "How do I sort a list of tuples by the second item?",
                     "What does an IndexError mean?"]


def show_answer(turn):
    """One tutor answer: the text, then only the notes it actually cites, with links."""
    st.markdown(turn["answer"])
    st.caption(f"{turn['model']} · {turn['seconds']} s")
    cited = [(i, s) for i, s in enumerate(turn["sources"], 1) if i in rag.cited_numbers(turn["answer"])]
    if not cited:
        return
    with st.expander(f"Sources: {len(cited)} part(s) of the official Python docs"):
        for i, source in cited:
            st.markdown(f"**[{i}] [{source['section']}]({source['url']})**")
            with st.container(border=True):
                st.markdown(source["text"])   # the exact part of the notes Gemini was given


def show_concept_explanation():
    """M5: questions answered only from our notes (official Python docs) via RAG, with sources."""
    st.write("Ask about a Python idea. Answers come **only** from our notes (the official Python "
             "Tutorial and Sorting HOWTO), and show which parts they used.")
    try:
        collection = notes_collection()
    except Exception as e:
        st.error(f"Could not open the notes database ({type(e).__name__}: {e}).")
        return

    chat = st.session_state.setdefault("chat", [])   # this browser tab's questions and answers
    clicked = None
    for column, example in zip(st.columns(len(EXAMPLE_QUESTIONS)), EXAMPLE_QUESTIONS):
        if column.button(example, key=f"example_{example}", width="stretch"):
            clicked = example
    question = st.chat_input("Ask about loops, lists, functions, built-ins, sorting or errors...") or clicked

    for turn in chat:
        st.chat_message("user").write(turn["question"])
        with st.chat_message("assistant"):
            show_answer(turn)
    if not question:
        return
    st.chat_message("user").write(question)
    with st.chat_message("assistant"):
        with st.spinner("Looking in the notes and asking Gemini..."):
            try:
                turn = {"question": question, **rag.answer(collection, question)}
            except GeminiUnavailable as e:
                st.error(str(e))
                return
        show_answer(turn)
    chat.append(turn)


# --- Sidebar: choose a mode -------------------------------------------------
st.sidebar.title("🐍 Beginner Python Tutor")
# The name is also kept in the page address (?learner=...), so pressing F5 does not reset it to "guest".
if "learner" not in st.session_state:
    st.session_state["learner"] = st.query_params.get("learner", "guest")
st.sidebar.text_input("Your name", key="learner", max_chars=40,
                      help="Each name has its own progress. In the student study, use your participant code.")
st.query_params["learner"] = current_learner()
MODE_ICONS = {"Guided Feedback": "🛠️", "Concept Explanation": "📖", "Practice Generation": "✨", "My Progress": "📈"}
mode = st.sidebar.radio("Choose a mode", list(MODE_ICONS), key="mode",
                        format_func=lambda m: f"{MODE_ICONS[m]}  {m}")

checks = (ollama_status(), gemini_status())
all_ok = all(ok for ok, _ in checks)
with st.sidebar.expander("System check: all OK ✅" if all_ok else "System check: problem ⚠️", expanded=not all_ok):
    for ok, message in checks:
        (st.success if ok else st.error)(message)
if checks[0][0]:
    start_warm_up()   # load the fine-tuned model in the background, once per app start

st.sidebar.caption(
    "**About.** Hints come from our fine-tuned Qwen2.5-Coder-1.5B (LoRA), running on this laptop "
    "with Ollama. Explanations and new exercises come from Gemini. The notes are the official "
    "Python docs. MSRIT ISE · Aryan Raj, Ambrin RK · Guide: Dr. Evangeline D.")

# --- Main area: one section per mode ------------------------------------------
st.title(f"{MODE_ICONS[mode]} {mode}")

if mode == "Guided Feedback":
    st.write("Write your code, run it, and get hints step by step (never the full answer).")
    try_tab, examples_tab = st.tabs(["Try it yourself", "Examples from real students"])
    with try_tab:
        show_try_it_yourself()
    with examples_tab:
        show_test_row_demo()
elif mode == "Concept Explanation":
    show_concept_explanation()
elif mode == "Practice Generation":
    show_practice_generation()
else:
    show_my_progress()
