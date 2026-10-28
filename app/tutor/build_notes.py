r"""
M5, step 1 (run once): build our beginner notes from the OFFICIAL Python documentation.

Why the official docs: they are accurate, citable and free to reuse (PSF License v2, see
app/notes/NOTICE.md). We picked the 5 pages that cover our 5 topics:

    introduction    numbers, strings, lists (built-ins, lists)
    controlflow     if, for, range, break, functions (loops, functions)
    datastructures  list methods, tuples, sets, dictionaries, looping (lists)
    errors          error messages and exceptions (reading errors)
    sorting         the Sorting HOWTO (sorting)

The docs are written in reStructuredText (.rst). This script downloads each page from the
CPython 3.13 docs, removes the markup Sphinx needs but a reader does not, and saves a plain
Markdown file in app/notes/. rag.py then cuts those files into chunks for ChromaDB.

Run from the app folder:   ..\.venv\Scripts\python.exe -m tutor.build_notes
"""
import re
import urllib.request

import config

DOCS_BRANCH = "3.13"
PAGES = {   # file name -> (path in CPython's Doc/ folder, page title, web address)
    "introduction": ("tutorial/introduction", "Python Tutorial: An Informal Introduction to Python", "tutorial/introduction.html"),
    "controlflow": ("tutorial/controlflow", "Python Tutorial: More Control Flow Tools", "tutorial/controlflow.html"),
    "datastructures": ("tutorial/datastructures", "Python Tutorial: Data Structures", "tutorial/datastructures.html"),
    "errors": ("tutorial/errors", "Python Tutorial: Errors and Exceptions", "tutorial/errors.html"),
    "sorting": ("howto/sorting", "Python HOWTO: Sorting Techniques", "howto/sorting.html"),
}
SOURCE_URL = "https://raw.githubusercontent.com/python/cpython/{branch}/Doc/{path}.rst"
WEB_URL = "https://docs.python.org/{branch}/{page}"
UNDERLINE = re.compile(r"^([=\-~*^\"'#+])\1{2,}\s*$")   # a line like ===== or -----


def clean_inline(text):
    """:func:`len` -> `len`;  :ref:`text <label>` -> text;  ``code`` -> `code`."""
    text = re.sub(r":\w+(?::\w+)?:`[~!]?([^`<]+?)\s*<[^`>]+>`", r"\1", text)   # role with a target
    text = re.sub(r":ref:`(?:tut-)?([^`]+)`",                                   # link to a docs section
                  lambda m: "the section on " + m.group(1).replace("-", " "), text)
    text = re.sub(r":\w+(?::\w+)?:`[~!]?([^`]+)`", r"`\1`", text)              # plain role
    text = re.sub(r"``([^`]+)``", r"`\1`", text)
    text = re.sub(r"`([^`<]+?)\s*<https?://[^>]+>`_+", r"\1", text)          # web links
    return text.replace("\\ ", "")


def rst_to_markdown(rst):
    """Convert one .rst page to Markdown: headings, paragraphs and code examples only."""
    lines, out = rst.splitlines(), []
    heading_chars = []      # the order of underline characters gives the heading level
    skip_below = None       # indentation of a directive we are dropping (index, labels, ...)
    code = None             # inside a code example: {"base": indent of its intro, "cut": spaces to remove, "doctest": bool}

    def close_code():
        nonlocal code
        while out and not out[-1].strip():
            out.pop()
        out.extend(["```", ""])
        code = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        nxt = lines[i + 1] if i + 1 < len(lines) else ""

        if code is not None:                      # 1. inside a code example
            if code["doctest"]:                   # ">>>" examples end at a blank line
                if stripped:
                    out.append(line.rstrip())
                    continue
                close_code()
                continue
            if not stripped or indent > code["base"]:   # "::" blocks end when indentation drops
                if code["cut"] is None:
                    if not stripped:                    # skip blank lines before the first code line
                        continue
                    code["cut"] = indent
                out.append(line[code["cut"]:].rstrip() if stripped else "")
                continue
            close_code()

        if skip_below is not None:                # 2. inside a dropped directive
            if stripped and indent <= skip_below:
                skip_below = None
            else:
                continue

        if UNDERLINE.match(line):                 # 3. underline/overline of a heading
            continue
        if stripped and UNDERLINE.match(nxt) and indent == 0 and len(nxt.strip()) >= len(stripped):
            char = nxt.strip()[0]
            if char not in heading_chars:
                heading_chars.append(char)
            out += ["", "#" * min(heading_chars.index(char) + 1, 4) + " " + clean_inline(stripped), ""]
            continue

        if stripped.startswith(".. "):            # 4. directives
            directive = stripped[3:]
            if directive.startswith(("code-block::", "doctest::", "testcode::")):
                out.append("```python")
                code = {"base": indent, "cut": None, "doctest": False}
            elif directive.startswith(("note::", "tip::", "seealso::", "warning::", "important::")):
                kind, _, rest = directive.partition("::")
                out.append(f"**{kind.capitalize()}:** {clean_inline(rest.strip())}")
            else:                                 # index, labels (.. _name:), versionadded, testsetup...
                skip_below = indent
            continue

        if stripped.startswith(">>>"):            # 5. a ">>>" example
            out += ["```python", line[indent:].rstrip()]
            code = {"base": indent, "cut": indent, "doctest": True}
            continue

        if stripped.endswith("::"):               # 6. "Example::" introduces a code block
            text = stripped[:-2].rstrip()
            if text:
                out.append(clean_inline(text + ":"))
            out.append("```python")
            code = {"base": indent, "cut": None, "doctest": False}
            continue

        out.append(clean_inline(stripped))       # 7. ordinary text
    if code is not None:
        close_code()
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip() + "\n"


def build():
    config.NOTES_DIR.mkdir(exist_ok=True)
    for name, (path, title, page) in PAGES.items():
        url = SOURCE_URL.format(branch=DOCS_BRANCH, path=path)
        with urllib.request.urlopen(url, timeout=30) as response:
            rst = response.read().decode("utf-8")
        body = rst_to_markdown(rst)
        header = (f"<!-- source: {WEB_URL.format(branch=DOCS_BRANCH, page=page)} -->\n"
                  f"<!-- title: {title} -->\n"
                  f"<!-- Copyright (c) Python Software Foundation; PSF License v2 (see NOTICE.md) -->\n\n")
        (config.NOTES_DIR / f"{name}.md").write_text(header + body, encoding="utf-8")
        print(f"{name:15} {len(body):>6} characters  <- {url}")


if __name__ == "__main__":
    build()
