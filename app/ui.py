"""
The app's look: one small design system, so every page uses the same pieces.

- Colours, fonts and corner radius for Streamlit's own widgets are in .streamlit/config.toml.
- This file adds the rest: a style sheet (CSS) and small HTML building blocks such as the page
  header, cards, tags, the test-results table and the hint stepper.
- Every piece of text that comes from a learner, the model or Gemini goes through esc() (HTML
  escaping), so it is always shown as text and can never add its own HTML to the page.
"""
import html
import re

import streamlit as st

# Design tokens: the same names in both themes, different values.
TOKENS = {
    "light": {"ink": "#1B1B1F", "muted": "#5F5B53", "faint": "#8A857B", "paper": "#FAF8F3",
              "surface": "#FFFFFF", "sunken": "#F1EDE4", "line": "#E3DDD0", "accent": "#8A5F12",
              "accent_soft": "#F3E9D4", "primary": "#1F3A68", "on_primary": "#FFFFFF",
              "tint": "#E3E8F1",
              "good": "#2F6B3F", "good_soft": "#E6F0E6", "bad": "#9B2C2C", "bad_soft": "#F6E5E2",
              "warn": "#8A5F12", "warn_soft": "#F3E9D4", "shadow_near": "rgba(27,27,31,.04)", "shadow_far": "rgba(27,27,31,.05)"},
    "dark": {"ink": "#ECE9E2", "muted": "#A9A498", "faint": "#7D796F", "paper": "#111214",
             "surface": "#17181C", "sunken": "#1D1E23", "line": "#2B2C32", "accent": "#D9B26A",
             "accent_soft": "#2A2416", "primary": "#E8E2D4", "on_primary": "#15161A",
             "tint": "#1F2A3D",
             "good": "#8CC79A", "good_soft": "#16241A", "bad": "#E99A92", "bad_soft": "#2B1715",
             "warn": "#D9B26A", "warn_soft": "#2A2416", "shadow_near": "rgba(0,0,0,.30)", "shadow_far": "rgba(0,0,0,.25)"},
}

# A few line icons (Lucide style, 1.75 stroke) drawn as SVG, instead of emoji.
ICONS = {
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "x": '<path d="M18 6 6 18M6 6l12 12"/>',
    "alert": '<path d="M12 9v4M12 17h.01"/><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/>',
    "lock": '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "shield": '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/><path d="m9 12 2 2 4-4"/>',
    "spark": '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8"/>',
    "book": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z"/><path d="M4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "dot": '<circle cx="12" cy="12" r="4" fill="currentColor" stroke="none"/>',
}


def icon(name, size=16):
    return (f'<svg class="bt-ic" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')


def esc(text):
    """Show text as text (never as HTML)."""
    return html.escape(str(text), quote=True)


def esc_inline(text):
    """Escape, then show `code` as small code (the tutor's hints use backticks)."""
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", esc(text))


def _both(light, dark):
    """CSS that picks the light or dark value in the browser, from the theme Streamlit is showing.
    Streamlit sets `color-scheme: light | dark` on the app and changes it instantly when the
    learner switches theme in the menu, so no page re-run is needed."""
    return light if light == dark else f"light-dark({light}, {dark})"


def apply_style():
    """Add the style sheet once per page run."""
    variables = "".join(f"--bt-{k.replace('_', '-')}:{_both(TOKENS['light'][k], TOKENS['dark'][k])};"
                        for k in TOKENS["light"])
    variables += "--bt-shadow:0 1px 2px var(--bt-shadow-near), 0 6px 20px var(--bt-shadow-far);"
    st.html(f"<style>:root{{{variables}}}{CSS}</style>")


CSS = """
/* ---------- page frame ---------- */
.block-container { max-width: 1180px; padding-top: 5.2rem; padding-bottom: 4rem; }
[data-testid="stSidebarContent"] { padding-top: 0.4rem; }
h1, h2, h3 { letter-spacing: -0.01em; }
.bt-ic { display: inline-block; vertical-align: -3px; flex: none; }
code { font-size: 0.88em; }

/* ---------- Streamlit widgets, refined ---------- */
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {
    font-weight: 500; letter-spacing: 0.005em; padding: 0.45rem 1.05rem; min-height: 2.6rem;
    transition: background-color .18s ease, border-color .18s ease, transform .18s ease, box-shadow .18s ease; }
.stButton > button[kind="primary"] { background: var(--bt-primary); border-color: var(--bt-primary); color: var(--bt-on-primary); }
.stButton > button[kind="primary"]:hover { filter: brightness(1.08); box-shadow: var(--bt-shadow); }
.stButton > button[kind="secondary"] { background: var(--bt-surface); border-color: var(--bt-line); }
.stButton > button:active { transform: translateY(1px); }
[data-testid="stExpander"] details { border-color: var(--bt-line); border-radius: 0.6rem; background: var(--bt-surface); }
[data-testid="stExpander"] summary p { font-weight: 500; }
[data-testid="stTabs"] [role="tab"] p { font-weight: 500; font-size: 0.95rem; }
/* st.container(key="bt_box_...") becomes a card like the HTML ones */
[class*="st-key-bt_box"] { background: var(--bt-surface); border: 1px solid var(--bt-line); border-radius: 0.9rem;
    padding: 1.1rem 1.3rem 1.7rem; box-shadow: var(--bt-shadow); margin-bottom: 0.4rem; }
[data-testid="stChatMessage"] { background: transparent; padding: 0.4rem 0; }
[data-testid="stChatInput"] textarea { font-size: 0.95rem; }
[data-testid="stCaptionContainer"] { color: var(--bt-muted); }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }

/* ---------- brand (sidebar) ---------- */
.bt-brand { display: flex; gap: 0.75rem; align-items: center; margin: 0.3rem 0 1.4rem; }
.bt-mark { width: 2.4rem; height: 2.4rem; border-radius: 0.7rem; background: var(--bt-primary); color: var(--bt-on-primary);
    display: grid; place-items: center; font-family: 'JetBrains Mono', monospace; font-weight: 500; font-size: 0.85rem; }
.bt-brand-name { font-family: 'Fraunces', serif; font-weight: 600; font-size: 1.12rem; line-height: 1.15; color: var(--bt-ink); }
.bt-brand-sub { font-size: 0.78rem; color: var(--bt-muted); margin-top: 0.1rem; }
.bt-side-label { font-size: 0.7rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--bt-faint);
    font-weight: 600; margin: 1.3rem 0 0.45rem; }
.bt-status { display: flex; align-items: center; gap: 0.55rem; font-size: 0.85rem; padding: 0.3rem 0; color: var(--bt-ink); }
.bt-dot { width: 8px; height: 8px; border-radius: 999px; flex: none; }
.bt-status.ok .bt-dot { background: var(--bt-good); box-shadow: 0 0 0 3px var(--bt-good-soft); }
.bt-status.bad .bt-dot { background: var(--bt-bad); box-shadow: 0 0 0 3px var(--bt-bad-soft); }
.bt-status span.v { margin-left: auto; color: var(--bt-muted); font-size: 0.78rem; }
.bt-colophon { font-size: 0.76rem; line-height: 1.55; color: var(--bt-faint); margin-top: 1.6rem;
    border-top: 1px solid var(--bt-line); padding-top: 0.9rem; }

/* ---------- page header ---------- */
.bt-hero { margin: 0.2rem 0 1.6rem; max-width: 760px; }
.bt-eyebrow { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; letter-spacing: 0.16em; text-transform: uppercase;
    color: var(--bt-accent); font-weight: 500; margin-bottom: 0.55rem; }
.bt-title { font-family: 'Fraunces', serif; font-weight: 600; font-size: 2.35rem; line-height: 1.12; color: var(--bt-ink);
    letter-spacing: -0.02em; margin: 0; }
.bt-lead { font-size: 1.02rem; line-height: 1.6; color: var(--bt-muted); margin: 0.9rem 0 0; }

/* ---------- cards, tags ---------- */
.bt-card { background: var(--bt-surface); border: 1px solid var(--bt-line); border-radius: 0.9rem; padding: 1.25rem 1.4rem;
    box-shadow: var(--bt-shadow); margin-bottom: 1rem; }
.bt-card h3 { font-family: 'Fraunces', serif; font-weight: 600; font-size: 1.3rem; margin: 0 0 0.5rem; color: var(--bt-ink); }
.bt-card p { line-height: 1.6; margin: 0; color: var(--bt-ink); }
.bt-card .bt-sub { color: var(--bt-muted); font-size: 0.88rem; margin-top: 0.8rem; }
.bt-tags { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 0.8rem; }
.bt-tag { display: inline-flex; align-items: center; gap: 0.35rem; font-size: 0.75rem; font-weight: 500; padding: 0.18rem 0.6rem;
    border-radius: 999px; border: 1px solid var(--bt-line); color: var(--bt-muted); background: var(--bt-sunken); }
.bt-tag.accent { color: var(--bt-accent); background: var(--bt-accent-soft); border-color: transparent; }
.bt-tag.good { color: var(--bt-good); background: var(--bt-good-soft); border-color: transparent; }
.bt-tag.bad { color: var(--bt-bad); background: var(--bt-bad-soft); border-color: transparent; }
.bt-section { font-family: 'Fraunces', serif; font-weight: 600; font-size: 1.25rem; color: var(--bt-ink); margin: 1.8rem 0 0.7rem; }
.bt-label { font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--bt-faint); font-weight: 600; margin: 1.2rem 0 0.4rem; }

/* ---------- test results ---------- */
.bt-result { display: flex; gap: 1rem; align-items: center; }
.bt-result-icon { width: 2.5rem; height: 2.5rem; border-radius: 999px; display: grid; place-items: center; flex: none; }
.bt-result.good .bt-result-icon { background: var(--bt-good-soft); color: var(--bt-good); }
.bt-result.bad .bt-result-icon { background: var(--bt-bad-soft); color: var(--bt-bad); }
.bt-result.warn .bt-result-icon { background: var(--bt-warn-soft); color: var(--bt-warn); }
.bt-result-title { font-weight: 600; font-size: 1.02rem; color: var(--bt-ink); }
.bt-result-sub { font-size: 0.86rem; color: var(--bt-muted); margin-top: 0.1rem; }
.bt-result-score { margin-left: auto; text-align: right; font-variant-numeric: tabular-nums; }
.bt-result-score b { font-family: 'Fraunces', serif; font-size: 1.6rem; font-weight: 600; color: var(--bt-ink); }
.bt-result-score span { color: var(--bt-muted); font-size: 0.85rem; }
.bt-meter { height: 6px; border-radius: 999px; background: var(--bt-sunken); overflow: hidden; margin-top: 1rem; }
.bt-meter > div { height: 100%; border-radius: 999px; background: var(--bt-good); }
.bt-meter.bad > div { background: var(--bt-bad); }
.bt-table { width: 100%; border-collapse: collapse; font-size: 0.86rem; margin-top: 0.4rem; }
.bt-table th { text-align: left; font-weight: 600; font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--bt-faint); padding: 0.55rem 0.6rem; border-bottom: 1px solid var(--bt-line); }
.bt-table td { padding: 0.55rem 0.6rem; border-bottom: 1px solid var(--bt-line); vertical-align: top; color: var(--bt-ink); }
.bt-table tr:last-child td { border-bottom: none; }
.bt-table td.mono { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; word-break: break-word; }
.bt-table td.st { width: 2rem; }
.bt-table .ok { color: var(--bt-good); } .bt-table .no { color: var(--bt-bad); }

/* ---------- hint stepper ---------- */
.bt-tutor-head { display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap; margin-bottom: 1rem; }
.bt-tutor-head .bt-tutor-title { font-family: 'Fraunces', serif; font-weight: 600; font-size: 1.2rem; color: var(--bt-ink); margin-right: 0.3rem; }
.bt-steps { position: relative; }
.bt-step { display: grid; grid-template-columns: 2rem 1fr; gap: 0.9rem; padding-bottom: 1.1rem; position: relative; }
.bt-step:not(:last-child)::before { content: ""; position: absolute; left: calc(1rem - 1px); top: 2.1rem; bottom: 0.15rem;
    width: 2px; background: var(--bt-line); }
.bt-step-num { width: 2rem; height: 2rem; border-radius: 999px; display: grid; place-items: center; font-weight: 600; font-size: 0.85rem;
    border: 1.5px solid var(--bt-line); color: var(--bt-faint); background: var(--bt-surface); }
.bt-step.open .bt-step-num { background: var(--bt-primary); border-color: var(--bt-primary); color: var(--bt-on-primary); }
.bt-step-name { font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase; font-weight: 600; color: var(--bt-faint); margin-top: 0.4rem; }
.bt-step.open .bt-step-name { color: var(--bt-accent); }
.bt-step-text { line-height: 1.6; margin-top: 0.3rem; color: var(--bt-ink); }
.bt-step.locked .bt-step-text { color: var(--bt-faint); font-size: 0.88rem; display: flex; gap: 0.4rem; align-items: center; }

/* ---------- next step ---------- */
.bt-next { display: flex; align-items: center; gap: 1rem; }
.bt-next-topic { font-family: 'Fraunces', serif; font-weight: 600; font-size: 1.15rem; color: var(--bt-ink); }
.bt-next-why { color: var(--bt-muted); font-size: 0.86rem; }

/* ---------- progress ---------- */
.bt-kpis { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 0.5rem; }
.bt-kpi { background: var(--bt-surface); border: 1px solid var(--bt-line); border-radius: 0.9rem; padding: 1.1rem 1.3rem; box-shadow: var(--bt-shadow); }
.bt-kpi-label { font-size: 0.75rem; letter-spacing: 0.1em; text-transform: uppercase; font-weight: 600; color: var(--bt-faint); }
.bt-kpi-value { font-family: 'Fraunces', serif; font-weight: 600; font-size: 2.1rem; color: var(--bt-ink); margin-top: 0.25rem;
    font-variant-numeric: tabular-nums; }
.bt-kpi-value small { font-family: 'Inter', sans-serif; font-size: 0.9rem; color: var(--bt-muted); font-weight: 500; }
.bt-mastery { display: grid; grid-template-columns: 9rem 1fr 3.5rem 8.5rem; gap: 1rem; align-items: center; padding: 0.75rem 0;
    border-bottom: 1px solid var(--bt-line); font-size: 0.92rem; }
.bt-mastery:last-child { border-bottom: none; }
.bt-mastery .name { font-weight: 600; color: var(--bt-ink); }
.bt-mastery .bar { height: 8px; border-radius: 999px; background: var(--bt-sunken); overflow: hidden; }
.bt-mastery .bar > div { height: 100%; background: var(--bt-primary); border-radius: 999px; }
.bt-mastery .pct { text-align: right; font-variant-numeric: tabular-nums; font-weight: 600; color: var(--bt-ink); }
.bt-mastery .lvl { text-align: right; }
@media (max-width: 760px) { .bt-kpis { grid-template-columns: 1fr; } .bt-mastery { grid-template-columns: 6rem 1fr 3rem; }
    .bt-mastery .lvl { display: none; } .bt-title { font-size: 1.85rem; } }

/* ---------- concept chat ---------- */
.bt-source { border: 1px solid var(--bt-line); border-radius: 0.7rem; padding: 0.7rem 0.9rem; margin-top: 0.5rem;
    background: var(--bt-surface); font-size: 0.86rem; display: flex; gap: 0.7rem; align-items: baseline; }
.bt-source b { font-family: 'JetBrains Mono', monospace; color: var(--bt-accent); font-weight: 500; }
.bt-source a { color: var(--bt-ink); text-decoration: none; border-bottom: 1px solid var(--bt-line); }
.bt-source a:hover { border-color: var(--bt-ink); }
.bt-meta { font-size: 0.78rem; color: var(--bt-faint); margin-top: 0.4rem; }

/* ---------- footer ---------- */
.bt-footer { margin-top: 3.5rem; padding-top: 1.1rem; border-top: 1px solid var(--bt-line); font-size: 0.78rem; color: var(--bt-faint);
    display: flex; flex-wrap: wrap; gap: 0.4rem 1.2rem; }
"""


# ---------- building blocks ----------

def html_block(markup):
    st.markdown(markup, unsafe_allow_html=True)


def page_header(eyebrow, title, lead):
    html_block(f'<div class="bt-hero"><div class="bt-eyebrow">{esc(eyebrow)}</div>'
               f'<div class="bt-title" role="heading" aria-level="1">{esc(title)}</div>'
               f'<p class="bt-lead">{lead}</p></div>')


def section(title):
    html_block(f'<div class="bt-section" role="heading" aria-level="2">{esc(title)}</div>')


def label(text):
    html_block(f'<div class="bt-label">{esc(text)}</div>')


def tag(text, tone=""):
    return f'<span class="bt-tag {tone}">{esc(text)}</span>'


def problem_card(name, description, tags, footnote=""):
    """A problem or exercise: title, tags (topic, level...), the description."""
    sub = f'<div class="bt-sub">{footnote}</div>' if footnote else ""
    html_block(f'<div class="bt-card"><div class="bt-tags">{"".join(tags)}</div><h3>{esc(name)}</h3>'
               f'<p>{esc_inline(description)}</p>{sub}</div>')


def result_summary(result, extra=""):
    """The headline of a code run: icon, sentence, score and a bar."""
    status, passed, total = result["status"], result["passed"], result["total"]
    tone, glyph = ("good", "check") if status == "pass" else ("warn", "shield") if status == "blocked" else ("bad", "x")
    if status == "timeout":
        glyph = "clock"
    score = (f'<div class="bt-result-score"><b>{passed}</b><span> / {total} tests</span></div>' if status != "blocked" else "")
    meter = ""
    if total and status != "blocked":
        meter = f'<div class="bt-meter {"bad" if status != "pass" else ""}"><div style="width:{100 * passed / total:.0f}%"></div></div>'
    sub = f'<div class="bt-result-sub">{extra}</div>' if extra else ""
    html_block(f'<div class="bt-card"><div class="bt-result {tone}"><div class="bt-result-icon">{icon(glyph, 20)}</div>'
               f'<div><div class="bt-result-title">{esc(result["headline"])}</div>{sub}</div>{score}</div>{meter}</div>')


def tests_table(tests):
    rows = []
    for t in tests:
        ok = t["status"] == "pass"
        got = t.get("got") if "got" in t else f"{t.get('type')}: {t.get('message')}"
        rows.append(f'<tr><td class="st {"ok" if ok else "no"}" aria-label="{"passed" if ok else "failed"}">'
                    f'{icon("check" if ok else "x")}</td><td class="mono">{esc(t["input"])}</td>'
                    f'<td class="mono">{esc(t["expected"])}</td><td class="mono">{esc(got)}</td></tr>')
    html_block('<table class="bt-table"><thead><tr><th></th><th>Test</th><th>Expected</th><th>Got</th></tr></thead>'
               f'<tbody>{"".join(rows)}</tbody></table>')


STEP_NAMES = ["Hint 1", "Hint 2", "Explanation"]


def hint_steps(feedback, level):
    """The three levels of help as a vertical stepper; unopened levels are shown locked."""
    head = [f'<span class="bt-tutor-title">Tutor</span>']
    if feedback:
        head.append(tag(f"Bug type: {feedback['bug_type'] or 'unknown'}", "accent"))
        if feedback["source"] == "model":
            head.append(tag(f"Fine-tuned Qwen2.5-Coder · {feedback['seconds']} s"))
        else:
            head.append(tag("Safe fallback hint · guardrail blocked the reply", "bad"))
    texts = [feedback["hint_1"], feedback["hint_2"], feedback["explanation"]] if feedback else ["", "", ""]
    steps = []
    for i, (name, text) in enumerate(zip(STEP_NAMES, texts), 1):
        if i <= level:
            body = f'<div class="bt-step-text">{esc_inline(text)}</div>'
            cls = "open"
        else:
            body = f'<div class="bt-step-text">{icon("lock", 14)} Opens when you ask for it</div>'
            cls = "locked"
        steps.append(f'<div class="bt-step {cls}"><div class="bt-step-num">{i}</div>'
                     f'<div><div class="bt-step-name">{name}</div>{body}</div></div>')
    html_block(f'<div class="bt-card"><div class="bt-tutor-head">{"".join(head)}</div>'
               f'<div class="bt-steps">{"".join(steps)}</div></div>')


def kpis(items):
    """items: [(label, value, small)]"""
    cards = "".join(f'<div class="bt-kpi"><div class="bt-kpi-label">{esc(l)}</div>'
                    f'<div class="bt-kpi-value">{esc(v)} <small>{esc(s)}</small></div></div>' for l, v, s in items)
    html_block(f'<div class="bt-kpis">{cards}</div>')


def mastery_rows(rows):
    """rows: [(topic, mastery 0-1, done, level text, mastered?)]"""
    out = []
    for topic, m, done, level, mastered in rows:
        badge = tag("Mastered", "good") if mastered else tag(f"Next: {level}")
        out.append(f'<div class="bt-mastery"><div class="name">{esc(topic[:1].upper() + topic[1:])} '
                   f'<span class="bt-next-why">· {done} done</span></div>'
                   f'<div class="bar" role="progressbar" aria-valuenow="{m * 100:.0f}" aria-valuemin="0" aria-valuemax="100">'
                   f'<div style="width:{m * 100:.0f}%"></div></div><div class="pct">{m:.0%}</div><div class="lvl">{badge}</div></div>')
    html_block(f'<div class="bt-card">{"".join(out)}</div>')


def sources(cited):
    """cited: [(number, source dict)] -> small citation rows with a link to the docs."""
    rows = "".join(f'<div class="bt-source"><b>[{i}]</b><span><a href="{esc(s["url"])}" target="_blank" rel="noopener">'
                   f'{esc(s["section"])}</a></span></div>' for i, s in cited)
    html_block(rows)


def sidebar_brand():
    st.sidebar.markdown('<div class="bt-brand"><div class="bt-mark">py</div><div><div class="bt-brand-name">Beginner Python Tutor</div>'
                        '<div class="bt-brand-sub">Hints, not answers</div></div></div>', unsafe_allow_html=True)


def sidebar_label(text):
    st.sidebar.markdown(f'<div class="bt-side-label">{esc(text)}</div>', unsafe_allow_html=True)


def sidebar_status(rows):
    """rows: [(ok, name, value)]"""
    st.sidebar.markdown("".join(f'<div class="bt-status {"ok" if ok else "bad"}"><span class="bt-dot"></span>{esc(name)}'
                                f'<span class="v">{esc(value)}</span></div>' for ok, name, value in rows),
                        unsafe_allow_html=True)


def sidebar_colophon():
    st.sidebar.markdown(
        '<div class="bt-colophon">Hints come from our fine-tuned Qwen2.5-Coder-1.5B (LoRA), which runs on this laptop '
        'through Ollama. Explanations and new exercises come from Gemini, grounded in the official Python docs.'
        '</div>', unsafe_allow_html=True)


def footer():
    html_block('<div class="bt-footer"><span>Fine-tuned Qwen2.5-Coder-1.5B · LoRA · Ollama (local CPU)</span>'
               '<span>RAG over the official Python 3.13 docs</span><span>Dataset: Refactory (Hu et al., ASE 2019)</span></div>')
