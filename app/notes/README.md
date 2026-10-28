# Beginner notes (Concept Explanation mode)

The Concept Explanation mode answers questions **only** from the notes in this folder. This is RAG, in four steps:
1. `rag.py` cuts the notes into chunks.
2. ChromaDB stores each chunk with an embedding.
3. The chunks closest to the learner's question are retrieved.
4. Gemini answers from those chunks and cites them.

| File | Covers our topic(s) | Source |
|---|---|---|
| `introduction.md` | built-ins, lists (numbers, strings, lists) | Python Tutorial, ch. 3 |
| `controlflow.md` | loops, functions (if, for, range, break, def) | Python Tutorial, ch. 4 |
| `datastructures.md` | lists (list methods, tuples, sets, dicts, looping) | Python Tutorial, ch. 5 |
| `errors.md` | reading error messages, exceptions | Python Tutorial, ch. 8 |
| `sorting.md` | sorting (`sorted`, `key=`, `reverse=`) | Python Sorting HOWTO |

- **To rebuild the notes** from the official docs, run `..\.venv\Scripts\python.exe -m tutor.build_notes` from the `app` folder.
- **ChromaDB:** the app re-indexes automatically when a notes file changes.
- **Licence:** see `NOTICE.md`.
