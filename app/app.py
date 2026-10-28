r"""
The Streamlit web page: the only file you run.

    .venv\Scripts\python.exe -m streamlit run app\app.py

Streamlit re-runs this whole script from top to bottom every time the learner clicks
something. That is why it reads like a normal script and not like a web server.
The 4 pages (top navigation): Guided Feedback, Concepts, Practice and Progress.
The look (fonts, colours, cards, hint stepper) lives in ui.py and .streamlit/config.toml.
"""
import json
import sys
import threading
import urllib.request

# Streamlit re-runs this file on every click but keeps already-imported modules in memory, so
# after we change config.py or a tutor/ file, a refresh would mix old and new code (this caused
# an ImportError and an AttributeError). Forgetting OUR modules here makes every run use the
# current files. It costs a few milliseconds; installed packages (ChromaDB etc.) stay loaded.
for _name in [m for m in sys.modules if m in ("config", "prompt_format", "runner", "ui") or m.split(".")[0] == "tutor"]:
    del sys.modules[_name]

import streamlit as st
from code_editor import code_editor

import config
import ui
from tutor import progress, rag
from tutor.examples import load_course_problems, load_test_rows
from tutor.feedback import get_feedback
from tutor.gemini_client import GeminiUnavailable
from tutor.ollama_client import TutorUnavailable, warm_up
from tutor.practice import generate_exercise
from tutor.sandbox import run_code

st.set_page_config(page_title="Beginner Python Tutor", page_icon=":material/school:", layout="wide")
ui.apply_style()

HELP_NAMES = ["no help", "Hint 1", "Hint 2", "the explanation"]   # help level 0-3
LEVELS = ["easy", "medium", "hard"]


# ======================================================================== shared helpers ====

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
    """Is Ollama running, and does it have our fine-tuned model? Returns (ok, short, message)."""
    try:
        with urllib.request.urlopen(f"{config.OLLAMA_URL}/api/tags", timeout=3) as response:
            names = [m["name"] for m in json.loads(response.read())["models"]]
    except OSError:
        return False, "offline", f"Ollama is not running at {config.OLLAMA_URL}. Start the Ollama app."
    if any(name.split(":")[0] == config.TUTOR_MODEL for name in names):
        return True, "ready", f"Ollama is running and has the model '{config.TUTOR_MODEL}'."
    return False, "missing", f"Ollama has no model '{config.TUTOR_MODEL}'. Run: ollama create {config.TUTOR_MODEL} -f Modelfile"


def gemini_status():
    """Only checks that a key is present; the key itself is never shown on the page."""
    if config.GEMINI_API_KEY:
        return True, config.GEMINI_MODEL.replace("gemini-", "Gemini "), "Gemini key found in .env."
    return False, "no key", "No Gemini key yet. Put GEMINI_API_KEY=... in the .env file, then refresh."


def current_learner():
    """The name typed in the sidebar (each name has its own progress)."""
    return (st.session_state.get("learner") or "guest").strip()[:40] or "guest"


def open_practice(topic, difficulty):
    """Go to the Practice page with the suggested topic and difficulty already chosen."""
    st.session_state.update(practice_topic=topic, practice_difficulty=difficulty)
    st.switch_page(PAGES["practice"])


# ===================================================================== guided feedback ====

# The button in the bottom-right corner of the code editor; "submit" sends the code to the app.
# The editor sits in its own frame and draws the text in the theme's primary colour itself, so the
# button uses a see-through style that looks right in both light and dark mode.
def run_button():
    return [{"name": "Run code", "feather": "Play", "primary": True, "hasText": True, "showWithIcon": True,
             "alwaysOn": True, "commands": ["submit"],
             "style": {"bottom": "0.6rem", "right": "0.6rem", "opacity": 1, "backgroundColor": "rgba(127,140,170,0.14)",
                       "border": "1px solid rgba(127,140,170,0.35)", "borderRadius": "0.5rem", "padding": "0.35rem 0.9rem"}}]


def show_help(key, ask_for_feedback, on_new_level=None, extra_button=None):
    """Progressive help for ONE failed run: Hint 1, then Hint 2, then the Explanation, each only
    when the learner asks. key names the run; ask_for_feedback() calls the tutor (with guardrail);
    on_new_level(level, feedback), if given, is called each time a new level opens (M7 logs it);
    extra_button(column), if given, draws one more button next to the hint button.
    Returns the help level reached (0 = no hint asked yet)."""
    state = st.session_state.setdefault("help", {}).setdefault(key, {"level": 0, "feedback": None})
    ui.hint_steps(state["feedback"], state["level"])
    left, right, _ = st.columns([1.3, 1.3, 3])
    if state["level"] < 3:
        text = ["Get a hint", "Reveal Hint 2", "Reveal explanation"][state["level"]]
        if left.button(text, type="primary", icon=":material/lightbulb:", key=f"more_{key}", width="stretch"):
            if state["level"] == 0:
                with st.spinner("The tutor is reading your code. This takes about 10–20 s on this laptop."):
                    try:
                        state["feedback"] = ask_for_feedback()
                    except TutorUnavailable as e:
                        st.error(str(e))
                        return 0
            state["level"] += 1
            if on_new_level:
                on_new_level(state["level"], state["feedback"])
            st.rerun()
    if extra_button:
        extra_button(right)
    return state["level"]


def solve_problem(problem, tags):
    """The learner writes code for a problem (a course problem or a generated exercise), the
    sandbox runs it, and on a failure the fine-tuned model gives hints one level at a time
    (Algorithm 2). problem needs: task_id, name, description, tests, starter_code, reference_code."""
    task = problem["task_id"]
    function = problem["starter_code"].split("\n", 1)[0].removeprefix("def ").rstrip(":")
    ui.problem_card(problem["name"], problem["description"], tags,
                    f"Write <code>{ui.esc(function)}</code> · checked against {len(problem['tests'])} tests")

    ui.label("Your code")
    # A real code editor (Ace): Tab indents by 4 spaces, with line numbers and colours.
    # The Run button sits INSIDE the editor (Ctrl+Enter does the same), so the code and the
    # "run" command reach the app together. One editor per problem (the key).
    editor = code_editor(problem["starter_code"], lang="python", height=[12, 22], key=f"editor_{task}",
                         buttons=run_button(),
                         # The default 15 px top margin shifts the line numbers after typing; turn it off.
                         props={"scrollMargin": [0, 0, 0, 0], "style": {"borderRadius": "0.7rem"}},
                         # No auto-complete pop-ups: for beginners, Enter must always mean "new line".
                         # Line numbers matter: Hint 2 says things like "on line 6".
                         options={"tabSize": 4, "useSoftTabs": True, "showPrintMargin": False,
                                  "showGutter": True, "showLineNumbers": True, "fontSize": 14,
                                  "enableLiveAutocompletion": False, "enableBasicAutocompletion": False,
                                  "enableSnippets": False})
    st.caption("Tab indents · Shift+Tab un-indents · Ctrl+Enter runs")

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

    ui.label("Result")
    if result["status"] == "pass":
        ui.result_summary(result, f"Help used: {HELP_NAMES[last['help_used']]}")
    elif result["status"] == "blocked":
        ui.result_summary(result, "Nothing was run. Remove that part and try again.")
    else:
        ui.result_summary(result, "Ask the tutor for a hint below, or fix it yourself and run again.")
    if result["tests"]:
        with st.expander(f"Test details · {result['passed']} of {result['total']} passed"):
            ui.tests_table(result["tests"])
    if result["status"] not in ("pass", "blocked") and result["error_message"]:
        with st.expander("What Python reported (this is what the tutor reads)"):
            st.code(result["error_message"], language="text")

    if result["status"] == "pass":
        show_saved(last["saved"], problem["topic"])
        return
    if result["status"] == "blocked":
        return

    def give_up_button(column):
        if progress.already_finished(learner, task):
            return
        if column.button("I give up", icon=":material/flag:", key=f"giveup_{task}", width="stretch"):
            last["gave_up"] = progress.finish(learner, problem, most_help.pop(task, 0), gave_up=True)
            st.rerun()

    ui.label("Help")
    level = show_help(f"{task}:{last['id']}",
                      lambda: get_feedback(problem["description"], last["code"], result,
                                           [problem["reference_code"]], task),
                      on_new_level=lambda lvl, fb: progress.log_hint(learner, task, lvl, fb),
                      extra_button=give_up_button)
    most_help[task] = max(most_help.get(task, 0), level)
    if last.get("gave_up"):
        show_saved(last["gave_up"], problem["topic"])


def show_saved(saved, topic):
    """What finishing this exercise did to the learner's progress, then what to do next."""
    if saved is None:
        st.caption("You finished this exercise before, so your progress did not change this time.")
        return
    what = "Recorded as not solved" if saved["gave_up"] else "Progress saved"
    st.caption(f"{what} · credit {saved['credit']} · {topic} mastery {saved['before']:.0%} → {saved['after']:.0%}")
    show_next_step(current_learner(), key=topic)


def show_next_step(learner, key):
    """Algorithm 3: what to practise next, with a button that opens it."""
    topic, difficulty, why = progress.next_step(learner)
    with st.container(key=f"bt_box_next_{key}"):
        left, right = st.columns([4, 1.5], vertical_alignment="center")
        left.markdown(f'<div class="bt-label" style="margin-top:0">Recommended next</div>'
                      f'<div class="bt-next-topic">{ui.esc(topic.capitalize())} · {ui.esc(difficulty)}</div>'
                      f'<div class="bt-next-why">{ui.esc(why.capitalize())}</div>', unsafe_allow_html=True)
        if right.button("Practise this", icon=":material/arrow_forward:", key=f"next_{key}", width="stretch"):
            open_practice(topic, difficulty)


def page_guided_feedback():
    ui.page_header("Guided feedback", "Fix your code, one hint at a time",
                   "Write a solution and run it against real test cases. When it fails, our fine-tuned "
                   "tutor gives a gentle hint, then a more specific one, then an explanation. "
                   "It never writes the answer for you.")
    own_tab, examples_tab = st.tabs(["Course problems", "Real student attempts"])
    with own_tab:
        problems = {p["name"]: p for p in course_problems()}
        name = st.selectbox("Problem", list(problems), label_visibility="collapsed")
        problem = problems[name]
        solve_problem(problem, [ui.tag(problem["topic"].capitalize(), "accent"), ui.tag(problem["difficulty"].capitalize()),
                                ui.tag("Course problem")])
    with examples_tab:
        show_real_attempts()
    ui.footer()


def show_real_attempts():
    """A real student attempt from our 12 test rows (the model never saw them), with the same help."""
    rows = load_test_rows()
    labels = {f"Attempt {r['id']} · {r['topic']} · {r['difficulty']}": r for r in rows}
    row = labels[st.selectbox("Attempt", list(labels), label_visibility="collapsed")]
    ui.problem_card(f"Attempt {row['id']}", row["problem"],
                    [ui.tag(row["topic"].capitalize(), "accent"), ui.tag(row["difficulty"].capitalize()),
                     ui.tag("Held-out test row")],
                    "A real wrong attempt from the Refactory dataset. The model never saw it during training.")
    left, right = st.columns(2)
    with left:
        ui.label("Student code")
        st.code(row["student_code"], language="python", line_numbers=True)
    with right:
        ui.label("What Python reported")
        st.code(row["error_message"], language="text")

    reference = next(p["reference_code"] for p in course_problems() if p["task_id"] == row["task_id"])
    run_result = {"status": "timeout" if row["error_message"].startswith("Timed out") else "fail",
                  "error_message": row["error_message"]}
    ui.label("Help")
    level = show_help(f"row_{row['id']}", lambda: get_feedback(
        row["problem"], row["student_code"], run_result, [reference, row["fixed_code"]], row["task_id"]))
    if level:
        with st.expander("Compare with our dataset answer (for checking the model)"):
            st.markdown(f"**Bug type:** {row['bug_type']}\n\n**Hint 1:** {row['hint_1']}\n\n"
                        f"**Hint 2:** {row['hint_2']}\n\n**Explanation:** {row['explanation']}")
            st.code(st.session_state["help"][f"row_{row['id']}"]["feedback"]["raw"], language="text")


# ============================================================================= concepts ====

EXAMPLE_QUESTIONS = ["What does range(5) give me?", "How do I sort a list of tuples by the second item?",
                     "What does an IndexError mean?", "When should I use a while loop?"]


def pick_example():
    """Pills callback: turn the clicked suggestion into the next question, then clear the pill."""
    st.session_state["pending_question"] = st.session_state["example_pick"]
    st.session_state["example_pick"] = None


def show_answer(turn):
    """One tutor answer: the text, then only the notes it actually cites, with links."""
    st.markdown(turn["answer"])
    cited = [(i, s) for i, s in enumerate(turn["sources"], 1) if i in rag.cited_numbers(turn["answer"])]
    if cited:
        ui.sources(cited)
        with st.expander("Show the exact passages"):
            for i, source in cited:
                st.markdown(f"**[{i}] {source['section']}**")
                st.markdown(source["text"])
    ui.html_block(f'<div class="bt-meta">{ui.esc(turn["model"])} · {turn["seconds"]} s · '
                  f'{len(cited)} source{"s" if len(cited) != 1 else ""}</div>')


def page_concepts():
    ui.page_header("Concept explanation", "Ask about any Python idea",
                   "Answers come only from the official Python Tutorial and Sorting HOWTO. Each one shows "
                   "the passages it used, and the tutor says so when the docs do not cover a question.")
    try:
        collection = notes_collection()
    except Exception as e:
        st.error(f"Could not open the notes database ({type(e).__name__}: {e}).")
        return
    chat = st.session_state.setdefault("chat", [])   # this browser tab's questions and answers
    st.pills("Try asking", EXAMPLE_QUESTIONS, key="example_pick", on_change=pick_example)
    question = st.chat_input("Ask about loops, lists, functions, built-ins, sorting or errors")
    question = question or st.session_state.pop("pending_question", None)

    for turn in chat:
        st.chat_message("user", avatar=":material/person:").write(turn["question"])
        with st.chat_message("assistant", avatar=":material/school:"):
            show_answer(turn)
    if question:
        st.chat_message("user", avatar=":material/person:").write(question)
        with st.chat_message("assistant", avatar=":material/school:"):
            with st.spinner("Searching the notes and writing an answer..."):
                try:
                    turn = {"question": question, **rag.answer(collection, question)}
                except GeminiUnavailable as e:
                    st.error(str(e))
                    return
            show_answer(turn)
        chat.append(turn)
    ui.footer()


# ============================================================================= practice ====

def page_practice():
    ui.page_header("Practice generation", "A new exercise, made for your level",
                   "Gemini writes a fresh exercise in the style of the MBPP benchmark. Before you see it, "
                   "we check that its hidden solution passes every one of its tests.")
    # Start on Algorithm 3's suggestion (M7); the learner can still choose anything.
    suggested_topic, suggested_difficulty, why = progress.next_step(current_learner())
    st.session_state.setdefault("practice_topic", suggested_topic)
    st.session_state.setdefault("practice_difficulty", suggested_difficulty)
    with st.container(key="bt_box_practice"):
        left, right = st.columns([3, 2])
        topic = left.segmented_control("Topic", config.TOPICS, key="practice_topic",
                                       format_func=str.capitalize, width="stretch")
        difficulty = right.segmented_control("Difficulty", LEVELS, key="practice_difficulty",
                                             format_func=str.capitalize, width="stretch")
        info_col, button_col = st.columns([3, 1.3], vertical_alignment="center")
        info_col.caption(f"Recommended for you: {suggested_topic} · {suggested_difficulty} ({why})")
        create = button_col.button("Create exercise", type="primary", icon=":material/auto_awesome:",
                                   width="stretch", disabled=not (topic and difficulty))

    practice = st.session_state.setdefault("practice", {"problem": None, "info": None, "titles": []})
    if create:
        with st.spinner("Writing an exercise and checking its solution. This takes about 10–60 s."):
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
        st.caption("Choose a topic and a difficulty, then create an exercise.")
        ui.footer()
        return
    tries = "first try" if info["tries"] == 1 else f"{info['tries']} tries"
    solve_problem(problem, [ui.tag(problem["topic"].capitalize(), "accent"), ui.tag(problem["difficulty"].capitalize()),
                            ui.tag(f"Verified · solution passes {len(problem['tests'])}/{len(problem['tests'])} tests", "good"),
                            ui.tag(f"{info['model']} · {tries} · {info['seconds']} s")])
    ui.footer()


# ============================================================================= progress ====

def page_progress():
    learner = current_learner()
    ui.page_header("Your progress", f"Learning record for {learner}",
                   "Each finished exercise moves a topic's mastery 30% of the way towards the credit you earned: "
                   "1.0 without hints, 0.75 after Hint 1, 0.5 after Hint 2, 0.25 after the explanation, "
                   "and 0 if you gave up.")
    scores = progress.get_mastery(learner)
    everything = progress.history(learner, limit=100_000)
    solo = sum(r["outcome"] == "solved" and r["help_used"] == 0 for r in everything)
    mastered = sum(m >= config.MASTERED for m, _ in scores.values())
    ui.kpis([("Exercises finished", len(everything), ""), ("Solved without hints", solo, ""),
             ("Topics mastered", mastered, f"of {len(config.TOPICS)}")])

    ui.section("Mastery by topic")
    ui.mastery_rows([(t, scores[t][0], scores[t][1], progress.difficulty_for(scores[t][0]),
                      scores[t][0] >= config.MASTERED) for t in config.TOPICS])
    show_next_step(learner, key="progress_page")

    ui.section("Recent exercises")
    if not everything:
        st.caption("Nothing finished yet. Solve an exercise in Guided Feedback or Practice to start your record.")
    else:
        st.dataframe([{"When": r["time"], "Exercise": r["name"], "Topic": r["topic"], "Level": r["difficulty"],
                       "Outcome": r["outcome"], "Help used": HELP_NAMES[r["help_used"]], "Credit": r["credit"],
                       "Mastery after": r["mastery_after"]} for r in everything[:20]],
                     hide_index=True, width="stretch",
                     column_config={"Mastery after": st.column_config.ProgressColumn(format="percent", min_value=0, max_value=1),
                                    "Credit": st.column_config.NumberColumn(format="%.2f")})
    with st.expander("Start again"):
        if st.checkbox(f"Yes, delete all progress for '{learner}'"):
            if st.button("Delete my progress", icon=":material/delete:"):
                progress.reset(learner)
                st.rerun()
    ui.footer()


# ======================================================================== navigation =======

PAGES = {
    "feedback": st.Page(page_guided_feedback, title="Guided Feedback", icon=":material/terminal:", default=True),
    "concepts": st.Page(page_concepts, title="Concepts", icon=":material/menu_book:", url_path="concepts"),
    "practice": st.Page(page_practice, title="Practice", icon=":material/auto_awesome:", url_path="practice"),
    "progress": st.Page(page_progress, title="Progress", icon=":material/insights:", url_path="progress"),
}
navigation = st.navigation(list(PAGES.values()), position="top")

# --- Sidebar: brand, learner, system status ---------------------------------------------------
ui.sidebar_brand()
# The name is kept in two places so it is never lost: the page address (?learner=..., survives F5)
# and a plain session value "_learner" (survives page changes, which can reset a widget's value).
if "learner" not in st.session_state:
    st.session_state["learner"] = st.session_state.get("_learner") or st.query_params.get("learner", "guest")
st.sidebar.text_input("Learner", key="learner", max_chars=40,
                      help="Each name has its own progress. In the student study, use your participant code.")
st.session_state["_learner"] = current_learner()
st.query_params["learner"] = current_learner()

ollama_ok, ollama_short, ollama_message = ollama_status()
gemini_ok, gemini_short, gemini_message = gemini_status()
ui.sidebar_label("System")
ui.sidebar_status([(ollama_ok, "Tutor model", ollama_short), (gemini_ok, "Gemini", gemini_short)])
for ok, message in ((ollama_ok, ollama_message), (gemini_ok, gemini_message)):
    if not ok:
        st.sidebar.error(message)
if ollama_ok:
    start_warm_up()   # load the fine-tuned model in the background, once per app start
ui.sidebar_colophon()

navigation.run()
