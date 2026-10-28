# Methodology: working notes (Prompt 5)

> **AI-score rule:** these are points and facts for you to understand and defend. Write the report text yourselves, in your own words. Don't paste these lines in.

## Files in this folder
| File | What it is |
|---|---|
| `diagrams/training_pipeline.mmd` | Fig. (a): the training pipeline, as Mermaid code |
| `diagrams/app_architecture.mmd` | Fig. (b): the app architecture, as Mermaid code |
| `algorithms.tex` | Algorithms 1–3 in IEEE LaTeX (`algorithm` + `algpseudocode`), if you use Overleaf |
| `METHODOLOGY_NOTES.md` | This file: block explanations, algorithms, tables, outline, draw.io tips |

**To preview a diagram:** open https://mermaid.live and paste the `.mmd` file.

**Change from your prompt:** the first block of Fig. (a) is **Refactory dataset**, not "Google Form collection", because we switched data source on 28 Oct. The labelling block says **LLM-drafted labels → author review**. Keep exactly that wording in the report.

---

## 1. Each block in simple words (for you, not for pasting)

### Fig. (a): Training pipeline
| Block | What it does | Why |
|---|---|---|
| **Refactory dataset** | 1,783 real wrong Python attempts by NUS first-year students, across 5 assignments [26]. | Real beginner mistakes. We did not invent the bugs. |
| **Sandboxed test runner** | Runs each attempt in a separate Python process with a time limit; unsafe code (file, OS, network access) is blocked. | We need the *real* error a student would see, and bad code must not hang or damage the laptop. |
| **Keep failing attempts** | Keeps the 1,722 attempts that really fail a test. Records the first error or failed test, and labels runtime vs logic automatically. | "Buggy" must mean "fails a test", not "the source said so". 61 attempts passed and were dropped. |
| **Stratified sampling** | Picks 12 short, different attempts per problem (60 in total), with seed 42. | Balanced topics. Short code fits the model. The seed makes it repeatable. |
| **LLM-drafted labels** | An LLM writes hint 1, hint 2, the explanation and a minimal fix, following our labelling rules. | Fast, consistent drafts. |
| **Author review** | We read and correct every row (`dataset/REVIEW.md`). | Humans stay responsible for the labels. |
| **Validation** | The fix must pass the course tests **and** match the reference solution on 40 random inputs. The hints must not contain the fix. No duplicates. | Catches wrong fixes and leaked answers automatically. Row 36 was dropped this way. |
| **beginner_bugs.csv** | The final 59 rows. | The teacher's "real CSV, ≥30 rows". |
| **Prompt formatting** | Each row becomes a chat: system rule + (problem, code, error) → fixed 4-line answer. | The model learns one exact input and output shape, and the app uses the same shape. |
| **Stratified split** | Train 40 / validation 7 / test 12, balanced by difficulty × bug type, plus 5-fold cross-validation. | The test rows are never seen in training. Cross-validation checks the result isn't luck. |
| **LoRA fine-tuning** | Trains small add-on matrices (0.59% of the weights) on Qwen2.5-Coder-1.5B-Instruct [27], [13], using a free T4. | Full fine-tuning would need far more memory and data. |
| **Best checkpoint** | Keeps the version with the lowest validation loss. | Protects against overfitting. |
| **GGUF export, Q4_K_M** | Merges LoRA into the model and stores the weights in about 4 bits: 3.1 GB → 986 MB. | Small enough to run on a laptop CPU. |
| **Ollama** | A local program that serves the model at `localhost:11434`. | No GPU, no internet and no cost at demo time. Student code stays on the laptop. |

### Fig. (b): App
| Block | What it does | Why |
|---|---|---|
| **Streamlit UI** | A Python library that turns a script into a web page with buttons and text boxes. | No HTML or JavaScript needed. |
| **Tutor Controller** | Plain Python that decides which mode handles the learner's action and passes data between parts. | Keeps the modes separate and simple. |
| **1 · Concept Explanation (RAG)** | Our beginner notes are cut into small chunks, and each chunk becomes an **embedding** (a list of numbers capturing its meaning), stored in **ChromaDB** (a local vector database). For a question, the closest chunks are retrieved, and Gemini must answer only from them and show their source [14]. | The answers are grounded in our notes, which reduces made-up facts. |
| **2 · Practice Generation** | Gemini writes a new exercise as JSON (description, function name, test cases, a solution). We check the JSON shape **and** run the solution against its own tests in the sandbox, retrying if either fails. | Generated exercises are sometimes broken, and this catches them before a learner sees them. |
| **3 · Guided Feedback** | Runs the learner's code in the sandbox. On failure, it sends the real error to **our fine-tuned model**. The **guardrail** blocks any reply that leaks the solution. Hints are shown one level at a time. | This is where the trained model is used. Hints come before answers. |
| **Guardrail** | A rule-based check on every model reply (details in Section 3). | The model is small and can still slip. Leakage is our main metric. |
| **4 · Progress Tracking** | SQLite (one local database file) stores every attempt and a **mastery score** per topic. The selector picks the next topic and difficulty. | This is the "adapts to the learner" part. No server is needed. |

---

## 2. LoRA in one equation (viva favourite)
**W = W₀ + (α / r) · B · A**
- W₀ is frozen.
- **B** (d × r) and **A** (r × k) are trained, with r = 8 and α = 16.
- With r = 8, each adapted matrix gets only 8·(d + k) new numbers instead of d·k.
- In total: 9,232,384 trainable parameters out of 1,552,946,688 (**0.59%**).

---

## 3. Design decisions fixed here (the app in Prompt 6 must use exactly these)
| Item | Value | Why |
|---|---|---|
| Sandbox time limit | 5 s per run | Same as dataset building. |
| Guardrail check 1 | The reply contains ` ``` ` or `def ` → blocked. | A code block or function definition means a solution. Same rule as `validate_dataset.py`. |
| Guardrail check 2 | Any line of the reference solution (≥ 12 characters, spaces normalised) that the learner hasn't already written appears in the reply → blocked. | Catches a leaked fix line. Same idea as `leaked_lines()`. |
| Guardrail check 2: evidence (M4 test, 28 Oct) | On the 12 test rows, the model had 0 blocks. A stricter variant (keywords and colon stripped, ≥ 8 characters) gave 2 false alarms on the harmless phrase `len(seq)`, so we kept the ≥ 12-character whole-line rule. For dataset example rows, the row's `fixed_code` is checked too, as well as the reference solution. | Data-backed choice (viva). |
| Guardrail check 3 | The reply doesn't parse into the 4 parts → blocked. | The app needs Hint 1 / Hint 2 / Explanation separately. |
| When blocked | Ask the model again (at most 2 tries in total, the 2nd at temperature 0.7). If still blocked, show a safe template hint built from the error ("Look at line N: Python reports <ErrorType>. What value does that variable have there?"). | The learner never sees a leaked answer. Every block is logged, and the block rate goes in Prompt 7's results. |
| Hint credit *c(h)* | Solved with no hint → 1.0; after Hint 1 → 0.75; after Hint 2 → 0.5; after Explanation → 0.25; gave up → 0 | More help means less evidence of mastery. |
| Mastery update | **m ← m + α_m (c − m)**, α_m = 0.3, start m = 0 | An exponential moving average: recent exercises count more. Simple to explain. |
| Difficulty rule | m < 0.4 → easy; 0.4 ≤ m < 0.7 → medium; m ≥ 0.7 → hard | Three bands, matching the dataset's difficulty labels. |
| "Mastered" | m ≥ 0.8 | The topic is then only revisited when every topic is mastered. |
| RAG notes (M5) | The official Python 3.13 docs: Tutorial ch. 3, 4, 5 and 8, plus the Sorting HOWTO (PSF License v2), converted by `build_notes.py`. Cut into 129 chunks of at most about 1,200 characters (median 930), one section each. | Accurate and citable, and they cover all 5 topics. We didn't write the notes ourselves. |
| RAG retrieval (M5) | ChromaDB with its built-in local embedding model all-MiniLM-L6-v2, cosine distance, top-k = 4. The section name is embedded along with the chunk. | Free, offline, no API quota. |
| RAG generation (M5) | `gemini-3.5-flash`, temperature 0.3, falling back to `gemini-3.5-flash-lite` on 503/429. "Answer only from the numbered notes, cite [n], say so if not covered." Only cited notes are shown as sources. | Grounded answers. An off-topic test question (Django) was correctly refused. |
| Practice generation (M6) | Gemini JSON mode with a fixed schema (title, description, function_name, solution, tests), temperature 0.9, 2 MBPP problems as style examples [12]. The exercise is accepted only if: (1) the JSON matches the schema; (2) it has 4–8 tests, each a call to the function with literal arguments, literal expected values, no duplicates and ≥ 2 different expected values; (3) the hidden solution passes the safety check and **all its own tests** in the sandbox. Up to 3 tries, each retry telling Gemini the reason. | A wrong test would mark a correct learner wrong. Literal-only tests matter because the sandbox runs (eval) the test inputs. The first-try validity rate is logged for Results. |
| Progress DB (M7) | SQLite file `app/data/progress.db`, 4 tables: `runs` (every code run), `hints` (every hint level opened: model or template, seconds, blocks), `results` (one row per finished exercise: help used, credit, mastery before and after), `mastery` (learner × topic: m, number done). | One file, built into Python, no server. `runs` and `hints` are the raw data for the student study. |
| Counting rule (M7) | An exercise changes mastery only the **first** time a learner finishes it (solved or gave up). A learner is identified by the name typed in the sidebar, which is kept in the page address so a refresh keeps it. | Re-running a solved problem can't inflate mastery. Study participants use their participant code. |
| Topic order | loops → lists → functions → built-ins → sorting | A beginner curriculum order, and the same 5 topics as the dataset. |

**Viva point:** this is a rule-based adaptive method, not trained knowledge tracing. Knowledge tracing [15] learns these updates from data; we have far too little data for that. Say so honestly.

---

## 4. Algorithms (IEEE style; the LaTeX versions are in `algorithms.tex`)

```
Algorithm 1: Dataset preparation and LoRA fine-tuning
Input : wrong attempts A; problems P, each with tests T_p and reference solution R_p;
        base model M0; seed s = 42
Output: fine-tuned tutor model M* (GGUF, Q4_K_M)
 1: D ← ∅
 2: for each attempt a ∈ A of problem p do
 3:     r ← RunSandbox(a, T_p, τ = 5 s)
 4:     if r.status ≠ PASS then
 5:         e ← ErrorMessage(r);  b ← AutoBugType(r)
 6:         D ← D ∪ {(p, a, e, b)}
 7: S ← StratifiedSample(D, 12 per problem, s)        ▷ short, no duplicates
 8: for each row x = (p, a, e, b) ∈ S do
 9:     (h1, h2, ex, f) ← LLMDraft(x);  authors review and correct
10:     if not Pass(f, T_p) or not Agree(f, R_p, 40 random inputs) or Leaks(f; h1, h2, ex) then
11:         fix the row or drop it
12: (D_tr, D_val, D_te) ← StratifiedSplit(S, difficulty × bug type, 40/7/12, s)
13: for each row: input ← ChatTemplate(SYSTEM, p, a, e);  target ← Format(b, h1, h2, ex)
14:     set the labels of the input tokens to −100           ▷ loss on the answer only
15: M ← M0 + LoRA(r = 8, α = 16) on q, k, v, o, gate, up, down;  freeze M0
16: for epoch = 1 to 3 do
17:     for each batch B of 4 examples in D_tr do
18:         θ_LoRA ← AdamW(θ_LoRA, ∇L(B), η = 2e-4)
19:         every 5 steps: compute L_val on D_val; keep the checkpoint with the lowest L_val
20: M* ← Quantize(Merge(best checkpoint), Q4_K_M)
21: return M*
(5-fold CV: repeat lines 15–19 for each fold; report the mean ± std of L_val.)
```

```
Algorithm 2: Guided Feedback loop
Input : problem p (description, tests T_p, reference solution R_p); learner code C;
        mastery m_t of topic t
Output: highest hint level h shown; explanation ex; updated mastery m_t
 1: h ← 0
 2: loop
 3:     r ← RunSandbox(C, T_p, τ = 5 s)
 4:     if r.status = PASS then break
 5:     if r.status = UNSAFE then tell the learner which code is blocked; C ← new code; continue
 6:     e ← ErrorMessage(r);  show the failing test
 7:     if the learner asks for a hint then                   ▷ help only on request
 8:         for k = 1 to 2 do                                 ▷ at most 2 tries
 9:             y ← FineTunedModel(SYSTEM, p, C, e)           ▷ via Ollama, same prompt as training
10:             if Guardrail(y, R_p, C) = OK then break
11:         if Guardrail(y, R_p, C) ≠ OK then y ← TemplateHint(e);  log the block
12:         (b, h1, h2, ex) ← Parse(y)
13:         show h1;  h ← max(h, 1)
14:         if the learner asks for more then show h2;  h ← max(h, 2)
15:         if the learner asks again then show ex;  h ← 3
16:     if the learner gives up then c ← 0; go to line 19
17:     C ← the learner's edited code
18: c ← (1.0, 0.75, 0.5, 0.25)[h]                            ▷ credit for hints used
19: m_t ← m_t + 0.3 · (c − m_t)
20: save (t, p, h, c, m_t, time) to SQLite
21: return h, ex, m_t
(h is the most help used across all attempts at this problem. A new error starts again at Hint 1.)
```

```
Algorithm 3: Next-topic and difficulty selection
Input : topics T in curriculum order; mastery m_t and attempt count n_t for each t ∈ T
Output: next topic t*, difficulty d*
1: U ← {t ∈ T : n_t = 0}
2: if U ≠ ∅ then t* ← first topic of U in curriculum order
3: else
4:     W ← {t ∈ T : m_t < 0.8}                ▷ topics not yet mastered
5:     if W = ∅ then W ← T
6:     t* ← argmin over t ∈ W of m_t           ▷ ties → earlier in the curriculum
7: d* ← easy if m_t* < 0.4; medium if m_t* < 0.7; else hard
8: return (t*, d*)
```

---

## 5. Tables (real numbers; Table I is the comparison table in the Literature Survey)

**Table II: Dataset description** (sources: `dataset/README.md`, `dataset/stats/summary.md`)

| Property | Value |
|---|---|
| Source | Refactory dataset [26], intro Python course at NUS, LGPL-3.0 |
| Wrong attempts run / really failing | 1,783 / 1,722 |
| Rows sampled / kept | 60 / 59 (1 dropped: the fix failed the random-input check) |
| Problems | 5 (search, unique dates/months, remove_extras, sort_age, top_k), 11–12 rows each |
| Topics | loops 12, functions 12, sorting 12, built-ins 12, lists 11 |
| Difficulty | easy 23, medium 24, hard 12 |
| Bug type | runtime 31, logic 28, syntax 0 (syntax errors were removed by the source) |
| Error shown to the model | wrong output 25, NameError 10, IndexError 8, TypeError 7, ValueError 3, time limit 3, UnboundLocalError 2, AttributeError 1 |
| Code length | 5–32 lines (median 10) |
| Columns | id, task_id, topic, difficulty, problem, student_code, error_message, bug_type, hint_1, hint_2, explanation, fixed_code, source_file |
| Labels | Drafted with an LLM, reviewed and corrected by the authors |
| Validation | Fix passes the course tests + matches the reference on 40 random inputs; no fix in the hints; no duplicates (0 problems) |
| Split | Train 40 / validation 7 / test 12 (stratified, seed 42) + 5-fold CV |

**Table III: Training settings** (copied from `training_outputs/training_settings.md`; don't retype or round differently)

| Setting | Value |
|---|---|
| Base model | Qwen2.5-Coder-1.5B-Instruct [27] |
| Method | LoRA [13] on a 16-bit base (Unsloth + Hugging Face Transformers [28]) |
| LoRA r / α / dropout | 8 / 16 / 0.05 |
| Target modules | q, k, v, o, gate, up, down projections |
| Trainable parameters | 9,232,384 of 1,552,946,688 (0.59%) |
| Epochs / steps | 3 / 30 |
| Learning rate / scheduler / warmup | 2 × 10⁻⁴ / linear / 3 steps |
| Batch size × gradient accumulation | 2 × 2 = 4 |
| Optimizer / weight decay | AdamW / 0.01 |
| Max sequence length (longest example) | 1,024 (791 tokens) |
| Loss on | answer tokens only |
| Seed | 42 |
| Hardware / training time | Tesla T4 16 GB (free Colab) / 0.8 min |
| Export | GGUF Q4_K_M, 986 MB, served by Ollama on CPU |

**Training results:** these could go here or in Results; your choice, but don't use them in both places.
- Validation loss: 1.845 (step 5) → **1.535** (step 30, the best).
- Average training loss: 1.563.
- 5-fold CV validation loss: **1.486 ± 0.088**.

The "final training loss 1.4067" in the settings file is the **last step only**. If you show it, call it "last-step training loss".

---

## 6. Methodology section outline (≈ 1.5–2 IEEE pages)
- **A. System overview**
  - Fig. 1 (b), the app architecture.
  - Two phases: offline training, then online tutoring.
  - What runs locally vs in the cloud (only Gemini).
- **B. Dataset construction**
  - Fig. 1 (a), data stage.
  - Source [26] and why we chose real attempts.
  - Running the attempts in the sandbox; "buggy = fails a test", and the 61 that passed (mostly `sort()` in sort_age).
  - Sampling rule.
  - Labelling rules (hint 1 / hint 2 / explanation / fix), plus the honest "LLM-drafted, author-reviewed" statement.
  - Automatic validation, and row 36 as an example of a caught error.
  - Table II, and optionally the 3 small bar charts from `dataset/stats/`.
- **C. Prompt and answer format**
  - System rule ("never write the fix").
  - User = problem + code + real error.
  - Fixed 4-line answer, and why a fixed format helps both training and measuring bug-type accuracy.
- **D. LoRA fine-tuning**
  - Why parameter-efficient fine-tuning [13], [24], and the LoRA equation.
  - Why a 1.5B coder model [27] (fits a free T4 and a laptop).
  - Loss on the answer only.
  - Split, cross-validation and best checkpoint.
  - Algorithm 1, Table III, and possibly the loss curve.
- **E. Local deployment**
  - Merge, 4-bit GGUF quantization (contrast with QLoRA [23], which quantizes *during* training), Ollama.
  - Why local: privacy of student code, free, offline demo.
- **F. Tutoring modes**
  - (1) RAG concept explanation [14].
  - (2) Practice generation with JSON + solution check [16].
  - (3) Guided Feedback: Algorithm 2, guardrail rules, progressive hints.
  - (4) Progress tracking: mastery update, Algorithm 3, honest note vs knowledge tracing [15].
- **G. Evaluation setup**
  - Optional here, or at the start of Results.
  - Which systems are compared, the metrics, the student study design (filled in from Prompt 7).

**Figure and table numbering:** IEEE numbers them in order of first mention. A likely order:
- Table I: comparison (Literature Survey)
- Fig. 1: architecture
- Table II: dataset
- Table III: training
- Fig. 2: loss curve

---

## 7. Redrawing the diagrams in draw.io for the IEEE report
1. **Import:**
   - Go to https://app.diagrams.net and choose **Arrange → Insert → Advanced → Mermaid**.
   - Paste the `.mmd` file and click Insert.
   - If the result is one locked image, use it only as a guide and redraw on top with native shapes (Steps 2–3), which is cleaner anyway.
2. **Shapes with a fixed meaning:**
   - rounded rectangle = process
   - cylinder = data store (CSV, ChromaDB, SQLite)
   - diamond = decision
   - parallelogram = input document (notes)
   - stick figure or ellipse = learner

   Add a tiny legend if you use more than these.
3. **Style for IEEE:**
   - **Font:** Times New Roman, 8–9 pt (the same as the figure captions).
   - **Colour:** black outlines and white or light-grey fills only. IEEE papers are often printed in black and white, so don't rely on colour.
   - **Lines and arrows:** 1 pt lines; *Waypoints: Orthogonal*, so arrows bend at right angles.
   - Turn on **View → Grid** and use **Arrange → Align / Distribute** so the boxes line up.
   - Group each stage in a dashed container labelled "Data preparation", "Fine-tuning (Colab T4)", "Laptop (CPU)", and the 4 app modes.
4. **Size:**
   - One column is **3.5 in (8.9 cm)** wide; across both columns is **7.16 in (18.2 cm)**.
   - Fig. (b) has 4 modes side by side, so it needs the full width: use `figure*` in LaTeX, or a 2-column section break in Word.
   - Fig. (a) fits one column if drawn top-to-bottom.
5. **Export:**
   - Choose **File → Export as → PDF** (best for LaTeX) or **PNG at 300 dpi** with "Transparent background" unticked, for Word.
   - Turn on "Crop" so there is no white border.
6. **Captions:**
   - In IEEE, figure captions go *below* the figure ("Fig. 1. …") and table captions go *above* the table ("TABLE II").
   - Write the captions yourselves.
7. **Make it your own:** redrawing it yourselves (not pasting the Mermaid render) also keeps the figure clearly your work.

---

## 8. Likely viva questions (check you can answer them)
- **Why not use the Google Form data?** It would have needed many students' time. Refactory has 1,783 real attempts and a citable source. We kept the "real beginner code" requirement.
- **Why do the labels come from an LLM?** For time and consistency. Every row was reviewed by us and automatically validated (40 random inputs, leak check). We say so in the paper.
- **Why LoRA and not full fine-tuning?** 0.59% of the weights, it fits a free T4, and there is less overfitting risk on 40 rows.
- **How do you know it didn't overfit?** Validation loss fell at every check, and the best checkpoint was the last one. The 5-fold CV losses are close to each other (std 0.088).
- **What does Q4_K_M mean?** 4-bit weights, using llama.cpp's "K-quant, medium" mix. It's about 3× smaller with a small quality loss.
- **What if the model still leaks the answer?** The guardrail blocks it, regenerates once, and otherwise shows a template hint. We report the block rate.
- **Is the mastery score machine learning?** No. It's a transparent moving-average rule (see Section 3).
