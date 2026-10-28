r"""
M5: Concept Explanation with RAG (Retrieval-Augmented Generation).

    notes (app/notes/*.md) -> chunks -> embeddings -> ChromaDB      (done once, then reused)
    question -> embedding -> the closest chunks -> Gemini answers ONLY from them, citing [1], [2]

Words for the viva:
- chunk:      a short piece of the notes (one section, at most about 1,200 characters),
              small enough that a retrieved piece is about one idea.
- embedding:  a list of numbers that captures what a text means; texts with similar meaning
              get similar numbers. ChromaDB's built-in model (all-MiniLM-L6-v2) makes them
              locally, on this laptop; no API is needed for this step.
- ChromaDB:   a small database that stores the chunks with their embeddings and quickly finds
              the chunks closest to a question's embedding.
- grounding:  Gemini is told to answer only from the retrieved chunks and to say so when they
              do not contain the answer. That makes made-up answers less likely, and the
              sources can be shown.

Quick test from the app folder:   ..\.venv\Scripts\python.exe -m tutor.rag "What does range do?"
"""
import hashlib
import re

import chromadb

import config
from tutor.gemini_client import generate

CHROMA_DIR = config.DATA_DIR / "chroma"
COLLECTION = "beginner_notes"
MAX_CHUNK_CHARS = 1200
TOP_K = 4
NOTE_FILES = ["introduction", "controlflow", "datastructures", "errors", "sorting"]

SYSTEM_INSTRUCTION = (
    "You are a friendly tutor for complete beginners learning Python. "
    "Answer the question using ONLY the numbered notes you are given. "
    "If the notes do not contain the answer, say that these notes do not cover it, "
    "and do not answer from your own knowledge. "
    "Do not greet; start with the answer. "
    "Use simple words and short sentences, and give at most one small code example. "
    "After each fact, cite the note it came from, like [1] or [2]."
)


def read_chunks():
    """Cut every notes file into chunks. Each chunk keeps its page title, section and web address."""
    chunks = []
    for name in NOTE_FILES:
        text = (config.NOTES_DIR / f"{name}.md").read_text(encoding="utf-8")
        title = re.search(r"<!-- title: (.*?) -->", text).group(1)
        url = re.search(r"<!-- source: (.*?) -->", text).group(1)
        headings, paragraph, section_parts, in_code = [], [], [], False

        def end_paragraph():
            if paragraph:
                section_parts.append("\n".join(paragraph).strip())
                paragraph.clear()

        def end_section():
            end_paragraph()
            current = ""
            for part in section_parts:            # join paragraphs until a chunk is full
                if current and len(current) + len(part) > MAX_CHUNK_CHARS:
                    chunks.append({"text": current, "title": title, "section": " › ".join(headings) or title, "url": url})
                    current = ""
                current = f"{current}\n\n{part}" if current else part
            if current.strip():
                chunks.append({"text": current, "title": title, "section": " › ".join(headings) or title, "url": url})
            section_parts.clear()

        for line in text.splitlines():
            if line.startswith("<!--"):
                continue
            if line.startswith("```"):
                in_code = not in_code
                paragraph.append(line)
                if not in_code:                   # keep a whole code example in one paragraph
                    end_paragraph()
                continue
            heading = None if in_code else re.match(r"^(#{1,4}) (.*)", line)
            if heading:                           # a new section starts
                end_section()
                level = len(heading.group(1))
                headings[:] = headings[:level - 1] + [heading.group(2).replace("`", "")]
            elif not line.strip() and not in_code:
                end_paragraph()
            else:
                paragraph.append(line)
        end_section()
    return chunks


def _notes_fingerprint():
    """Changes whenever any notes file changes, so we know when to rebuild the index."""
    digest = hashlib.sha256()
    for name in NOTE_FILES:
        digest.update((config.NOTES_DIR / f"{name}.md").read_bytes())
    return digest.hexdigest()[:16]


def get_collection():
    """Open the ChromaDB collection, (re)building it if the notes changed since last time."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    fingerprint = _notes_fingerprint()
    try:
        collection = client.get_collection(COLLECTION)
        if collection.metadata.get("notes") == fingerprint and collection.count() > 0:
            return collection
        client.delete_collection(COLLECTION)
    except Exception:                             # collection does not exist yet
        pass
    collection = client.create_collection(COLLECTION, metadata={"notes": fingerprint, "hnsw:space": "cosine"})
    chunks = read_chunks()
    collection.add(
        ids=[f"chunk_{i}" for i in range(len(chunks))],
        # The section name is part of the embedded text, so "for Statements" helps find loop questions.
        documents=[f"{c['section']}\n\n{c['text']}" for c in chunks],
        metadatas=[{"title": c["title"], "section": c["section"], "url": c["url"]} for c in chunks],
    )
    return collection


def retrieve(collection, question, k=TOP_K):
    """The k chunks closest in meaning to the question (smallest distance first)."""
    result = collection.query(query_texts=[question], n_results=k)
    # Each stored document is "section name\n\nchunk text"; give back only the chunk text.
    return [{"text": doc.split("\n\n", 1)[-1], **meta, "distance": round(dist, 3)}
            for doc, meta, dist in zip(result["documents"][0], result["metadatas"][0], result["distances"][0])]


def answer(collection, question):
    """Retrieve notes for the question and let Gemini answer from them.
    Returns {"answer", "sources", "model", "seconds"}. May raise GeminiUnavailable."""
    sources = retrieve(collection, question)
    notes = "\n\n".join(f"[{i}] ({s['section']})\n{s['text']}" for i, s in enumerate(sources, 1))
    prompt = f"Notes:\n\n{notes}\n\nQuestion from a beginner: {question}"
    text, model, seconds = generate(prompt, SYSTEM_INSTRUCTION, temperature=0.3)
    return {"answer": text, "sources": sources, "model": model, "seconds": seconds}


def cited_numbers(answer_text):
    """Which notes the answer cites: "[1]", "[3, 4]" -> {1, 3, 4}. Only these are shown as sources."""
    found = set()
    for group in re.findall(r"\[(\d+(?:\s*,\s*\d+)*)\]", answer_text):
        found.update(int(n) for n in group.split(","))
    return found


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    question = " ".join(sys.argv[1:]) or "What does range(5) give me in a for loop?"
    collection = get_collection()
    print(f"{collection.count()} chunks in ChromaDB\n")
    result = answer(collection, question)
    print(f"Q: {question}\n\n{result['answer']}\n\n({result['model']}, {result['seconds']} s)\nSources:")
    for i, s in enumerate(result["sources"], 1):
        print(f"  [{i}] {s['section']}  (distance {s['distance']})  {s['url']}")
