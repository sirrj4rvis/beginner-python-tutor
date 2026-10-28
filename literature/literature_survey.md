# Introduction & Literature Survey: working notes

**For the team only.** These are points and facts. Write all report text yourselves.

- **Verified:** every DOI below was resolved on 28 Oct 2026. Authors, title, venue, year and pages come from the official Crossref/DataCite records.
- **"(verify)"** marks a detail recalled from the paper (a number, dataset or model) that I could not check against the record. Check it in the PDF before using it.
- **Numbering** follows the order of first citation in the Introduction outline (Part 4), then the Literature Survey. If you change the order in which you cite them, renumber.

---

## Part 1: The 25 papers

### Generative AI in programming education
**[1] Becker et al., SIGCSE 2023: "Programming Is Hard – Or at Least It Used to Be"** *(abstract ref)*
- **Did:** a position paper on AI code generators (Codex, Copilot) in intro programming.
- **Data:** none (discussion plus examples).
- **Found:** the tools solve typical CS1 tasks. Opportunities include examples, explanations and exercises. Risks include academic integrity, over-reliance and wrong or biased code.
- **Limitation:** no system built and no evaluation.

**[2] Prather et al., ITiCSE-WGR 2023: "The Robots Are Here"**
- **Did:** a working-group report combining a literature review, surveys of instructors and students, and interviews.
- **Data:** survey and interview responses from several countries (sample size: verify).
- **Found:** mixed instructor attitudes, with worries about over-reliance and cheating. Recommends changing assessment and teaching.
- **Limitation:** self-reported views, a 2023 snapshot.

**[3] Hellas et al., ICER 2023: "Exploring the Responses of LLMs to Beginner Programmers' Help Requests"**
- **Did:** gave real student help requests (code + question) to Codex and GPT-3.5 and analysed the answers.
- **Data:** help requests from an online intro programming course (count and course: verify).
- **Found:** GPT-3.5 found real issues in most requests but often **included model-solution code even when told not to**, and sometimes reported issues that did not exist.
- **Limitation:** no learners used the responses, and the models are older.

**[4] Kiesler, Lohr & Keuning, FIE 2023: "Exploring the Potential of LLMs to Generate Formative Programming Feedback"**
- **Did:** gave real student submissions to ChatGPT and classified its feedback by feedback type.
- **Data:** student solutions from an intro programming course (language and count: verify).
- **Found:** feedback was often useful (what is wrong, how to proceed) but sometimes misleading, and **sometimes gave the full solution**.
- **Limitation:** small sample, one model (ChatGPT-3.5), no learner study.

### Deployed tutors and assistants
**[5] Liffiton, Sheese, Savelka & Denny, Koli Calling 2023: "CodeHelp"** *(abstract ref)*
- **Did:** built an LLM assistant for programming classes with **prompt-level guardrails** that block solution code.
- **Data:** a deployment in an undergraduate course (number of students and queries: verify). Uses OpenAI GPT-3.5 (verify).
- **Found:** students used it mostly for debugging and found it helpful. Instructors valued the guardrails.
- **Limitation:** closed, paid API. Guardrails depend on prompting. One course only.

**[6] Liu et al., SIGCSE 2024: "Teaching CS50 with AI"**
- **Did:** Harvard CS50's AI "duck" tutor, built on OpenAI models (GPT-4: verify), with system prompts so it guides rather than solves. Some features use course material such as lecture content (verify whether this is retrieval).
- **Data:** large-scale deployment on campus and online (numbers: verify), with student surveys.
- **Found:** students found it helpful, approaching a 1:1 tutor ratio.
- **Limitation:** closed model and cost; evaluation mostly by survey.

**[7] Kazemitabaar et al., CHI 2024: "CodeAid"**
- **Did:** an LLM programming assistant that avoids giving direct code. It uses pseudo-code, annotated explanations and help with fixing code.
- **Data:** a semester-long deployment in a large class (≈700 students: verify), usage logs, and interviews with students and educators.
- **Found:** helpful for concepts and debugging, but sometimes wrong. Educators worry about over-reliance.
- **Limitation:** closed model, one course, no fine-tuning.

### Error-message explanation
**[8] Leinonen et al., SIGCSE 2023: "Using LLMs to Enhance Programming Error Messages"** *(abstract ref)*
- **Did:** gave Python error messages plus the buggy code to Codex, asking for a plain-English explanation and a fix.
- **Data:** Python error messages and programs (source: verify).
- **Found:** explanations were mostly understandable, but **suggested fixes were correct less often**.
- **Limitation:** Codex has since been retired. No learner study.

**[9] Taylor et al., SIGCSE 2024: "dcc --help"**
- **Did:** added an LLM to the C compiler used in CS1/CS2, giving context-aware explanations of compile-time and runtime errors and told not to give solutions.
- **Data:** a large number of real student error events in university courses (count: verify).
- **Found:** explanations were mostly correct and rarely gave solutions (exact %: verify).
- **Limitation:** C only, closed model, no adaptation to the learner.

### Open and small models for feedback
**[10] Koutcheme et al., ITiCSE 2024: "Open Source Language Models Can Provide Feedback"**
- **Did:** compared open-source LLMs with proprietary ones for feedback on student programs, using GPT-4 as an automatic judge.
- **Data:** buggy student programs from an intro course (source: verify).
- **Found:** some open models are competitive with proprietary ones.
- **Limitation:** an LLM judge can be biased, and the open models were not fine-tuned for tutoring (verify).

**[11] Kotalwar, Gotovos & Singla, NeurIPS 2024 (Datasets & Benchmarks): "Hints-In-Browser"**
- **Did:** benchmarked LLMs for Python programming feedback on quality, cost, time and data privacy. **Fine-tuned small open models** to run inside the web browser.
- **Data:** buggy Python programs. Fine-tuning data was **generated by GPT-4** (verify).
- **Found:** fine-tuned small models improved a lot and run locally (exact gap to GPT-4: verify).
- **Limitation:** training targets are written by AI, not by humans for real student bugs. **This is the closest work to ours, so read it fully.**

### Dataset, method and adaptation foundations
**[12] Austin et al., arXiv 2021: "Program Synthesis with Large Language Models" (MBPP)** *(abstract ref)*
- **Did:** introduced the MBPP benchmark and tested LLMs on it.
- **Data:** about 974 crowd-sourced entry-level Python problems, each with 3 test asserts (verify; we use the "sanitized" subset).
- **Found:** performance grows with model size.
- **Limitation:** written by crowd workers, not students; only 3 tests per problem. We found some reference solutions are buggy but still pass.

**[13] Hu et al., ICLR 2022: "LoRA"** *(abstract ref)*
- **Did:** freeze the pretrained weights and train only small low-rank matrices added to each layer.
- **Data:** standard NLP benchmarks (e.g., GLUE, E2E, WikiSQL: verify).
- **Found:** matches or beats full fine-tuning with far fewer trainable parameters (up to 10,000× fewer for GPT-3: verify), and adds no extra delay when generating answers.
- **Limitation:** the rank must be chosen; not studied for education.

**[14] Lewis et al., NeurIPS 2020: "Retrieval-Augmented Generation (RAG)"** *(abstract ref)*
- **Did:** combined a text generator with a retriever that fetches relevant passages and passes them to the generator.
- **Data:** Wikipedia, open-domain question answering.
- **Found:** answers are more factual and specific than generation alone.
- **Limitation:** quality is limited by retrieval; general domain only.

**[15] Abdelrahman, Wang & Nunes, ACM Computing Surveys 2023: "Knowledge Tracing: A Survey"**
- **Did:** surveyed knowledge-tracing models, which estimate what a learner has mastered from their past answers, from classic BKT to deep models.
- **Data:** reviews public datasets (e.g., ASSISTments: verify).
- **Found:** a taxonomy of models and open challenges.
- **Limitation:** not specific to programming. Use it to justify the Progress Tracking design.

### Exercise and explanation generation
**[16] Sarsa, Denny, Hellas & Leinonen, ICER 2022: "Automatic Generation of Programming Exercises and Code Explanations"** *(abstract ref)*
- **Did:** used Codex to generate exercises (with solutions and tests) and code explanations.
- **Data:** a sample of generated exercises and explanations, analysed by the authors.
- **Found:** most exercises were sensible and new, but tests and solutions were not always correct.
- **Limitation:** no students used the material.

**[17] MacNeil et al., SIGCSE 2023: "Code Explanations … in a Web Software Development E-Book"**
- **Did:** embedded GPT-3 code explanations (line-by-line, summary, concepts) in an online textbook.
- **Data:** student interactions and ratings in a web-development course.
- **Found:** students found them useful, and different explanation types got different engagement.
- **Limitation:** learning gains were not measured (verify).

### Hints and feedback
**[18] Phung et al., LAK 2024: "Automating Human Tutor-Style Programming Feedback"**
- **Did:** GPT-4 writes hints for buggy Python programs, using failing tests and a fixed program. GPT-3.5 acts as a simulated student to check each hint before it is shown.
- **Data:** real buggy Python programs (source: verify).
- **Found:** high-precision hints, approaching human tutors.
- **Limitation:** two closed models, so costly. Some bugs get no hint (lower coverage).

**[19] Al-Hossami et al., SIGCSE 2024: "Can Language Models Employ the Socratic Method?"**
- **Did:** created a **hand-written dataset of buggy beginner programs paired with Socratic tutoring dialogues**, then tested LLMs.
- **Data:** a small manually written benchmark (size: verify).
- **Found:** GPT-4 did best but was still below human instructors.
- **Limitation:** small dataset; evaluates single turns only (verify). Most similar *dataset idea* to ours.

**[20] Kargupta et al., EMNLP Findings 2024: "Instruct, Not Assist" (TreeInstruct)**
- **Did:** an LLM instructor that plans multi-turn Socratic questions to guide debugging without giving the fix.
- **Data:** a new multi-bug debugging dataset plus the [19] benchmark (verify); a small study with students (verify).
- **Found:** beat baseline prompting at guiding students to fix bugs themselves.
- **Limitation:** relies on large closed models (GPT-4: verify).

### Intelligent tutoring systems
**[21] Schmucker, Xia, Azaria & Mitchell, AIED 2024: "Ruffle&Riley"**
- **Did:** an LLM-based conversational tutoring system that generates a tutoring script from lesson text automatically. Two agents (a "student" and a "professor") make the learner teach.
- **Data:** user studies with online participants (N: verify).
- **Found:** good learner experience, with learning comparable to other conditions (verify).
- **Limitation:** not for programming; short sessions.

### RAG in education
**[22] Taneja et al., AIED 2024: "Jill Watson: A Virtual Teaching Assistant Powered by ChatGPT"**
- **Did:** a virtual TA that answers student questions **grounded in course documents** (syllabus, textbook) through retrieval, with safety checks.
- **Data:** course materials and student questions from real courses (verify).
- **Found:** more accurate and safer answers than the plain model (verify).
- **Limitation:** closed model; course Q&A, not programming hints.

### Parameter-efficient fine-tuning
**[23] Dettmers et al., NeurIPS 2023: "QLoRA"**
- **Did:** LoRA on top of a 4-bit quantized frozen model, which means the base model's weights are stored with fewer bits so it uses much less memory.
- **Data:** instruction-tuning datasets (e.g., OASST1: verify).
- **Found:** fine-tunes very large models on a single GPU with little quality loss.
- **Limitation:** quantization can slightly reduce quality. This is relevant because it is how training fits on a free Colab T4.

**[24] Xu et al., IEEE TPAMI 2026: "PEFT Methods for Pretrained Language Models: A Critical Review and Assessment"**
- **Did:** reviewed and compared parameter-efficient fine-tuning (PEFT) families: additive, selective, reparameterized (LoRA) and hybrid.
- **Data:** experiments on standard benchmarks (verify).
- **Found:** LoRA-style methods give a strong balance of accuracy and memory (verify).
- **Limitation:** general NLP, not education or code.

### Real student code datasets
**[25] de Freitas et al., SIGCSE 2023: "FalconCode"**
- **Did:** released a multi-year dataset of Python code from an intro CS course.
- **Data:** a large set of student submissions with problem info (size and institution: verify).
- **Found:** a resource for studying how novices write code.
- **Limitation:** one institution; no hand-written hints or explanations. This shows real beginner code exists, but hint-labelled data does not.

---

## Part 2: Comparison table (draft; check every cell)

`?` = check in the paper. `–` = not applicable (not a system).

| Ref | Year | Approach / Model | Dataset | Fine-tuned | Hints w/o full solution | Runs code | Adapts to learner | RAG | Evaluation | Limitation |
|---|---|---|---|---|---|---|---|---|---|---|
| [1] | 2023 | Position paper | – | – | – | – | – | – | – | No system |
| [2] | 2023 | Review + surveys | Surveys, interviews | – | – | – | – | – | Qualitative | Self-reported |
| [3] | 2023 | Codex, GPT-3.5 answers | Real help requests | N | N (leaks) | N | N | N | Manual analysis | No learners |
| [4] | 2023 | ChatGPT feedback | Student submissions | N | Partly (leaks) | N | N | N | Feedback classification | Small, 1 model |
| [5] | 2023 | CodeHelp, GPT API + guardrails | Course deployment | N | Y (prompt) | N? | N | N | Usage + surveys | Closed, 1 course |
| [6] | 2024 | CS50 duck, GPT-4? | Course deployment | N | Y (prompt) | N | N | ? | Surveys | Closed, cost |
| [7] | 2024 | CodeAid, GPT | 700? students | N | Y (pseudo-code) | N? | N | N | Logs + interviews | Closed |
| [8] | 2023 | Codex error explanations | Python errors | N | N (gives fix) | Y (errors) | N | N | Manual rating | Fixes unreliable |
| [9] | 2024 | dcc --help, GPT? | C errors at scale | N | Y (prompt) | Y | N | N | Manual rating | C only, closed |
| [10] | 2024 | Open LLMs vs GPT-4 | Student programs | N? | ? | ? | N | N | GPT-4 judge | Judge bias |
| [11] | 2024 | Small open LLMs in browser | Python programs | **Y** | Y | Y? | N | N | Benchmark | AI-written training data |
| [12] | 2021 | MBPP benchmark | 974 crowd problems | – | – | Y (tests) | – | – | pass@k | Not student code |
| [13] | 2022 | LoRA | NLP benchmarks | Y | – | – | – | – | Benchmarks | Not education |
| [14] | 2020 | RAG (retriever + generator) | Wikipedia QA | Y | – | – | – | Y | QA benchmarks | General domain |
| [15] | 2023 | KT survey | Public KT datasets | – | – | – | Y | – | Review | Not programming |
| [16] | 2022 | Codex exercise + explanation gen. | Generated samples | N | – | Y (tests) | N | N | Expert analysis | No learners |
| [17] | 2023 | GPT-3 explanations in e-book | Course usage | N | – | N | N | N | Engagement, ratings | No learning gain? |
| [18] | 2024 | GPT-4 hints + GPT-3.5 validator | Buggy Python | N | Y | Y | N | N | Expert rating | Costly, closed |
| [19] | 2024 | Socratic debugging benchmark | Hand-written dialogues | N | Y (questions) | N | N | N | Metrics + manual | Small dataset |
| [20] | 2024 | TreeInstruct, GPT-4? | Multi-bug dataset | N | Y (Socratic) | ? | Partly | N | Benchmark + students? | Large closed LLM |
| [21] | 2024 | LLM conversational ITS | Online studies | N | – | N | Partly | N | User study | Not programming |
| [22] | 2024 | Jill Watson, ChatGPT + course docs | Course material | N | – | N | N | **Y** | Accuracy, safety | Closed, Q&A only |
| [23] | 2023 | QLoRA (4-bit + LoRA) | Instruction data | Y | – | – | – | – | Benchmarks | Not education |
| [24] | 2026 | PEFT review | Benchmarks | Y | – | – | – | – | Review + experiments | General NLP |
| [25] | 2023 | FalconCode dataset | Student Python code | – | – | – | – | – | Dataset paper | No hint labels |
| **Ours** | 2026 | Qwen2.5-Coder-1.5B + LoRA, local | Real beginner bugs (Refactory) + LLM-drafted, author-reviewed hints | **Y** | **Y (trained)** | **Y (sandbox)** | **Y** | **Y** | Leakage, bug-type, hint quality, pre/post + SUS | Small dataset, style not knowledge |

---

## Part 3: Gaps our system fills
1. **Closed and cloud-only.** Almost every tutor ([5]–[9], [18], [20], [22]) depends on large closed models through paid APIs. Only [10] and [11] study small open models, and [11] trains on GPT-4-written hints rather than human-written hints for real student bugs.
2. **"No full solution" is enforced only by prompting.** Prompt guardrails still leak solutions ([3], [4]). Hardly any work trains the model itself to give hints instead of answers.
3. **The pieces are not combined.** Running the code, using the real error, giving a hint, explaining concepts with RAG and tracking progress usually exist in separate works. Few systems join them for Python beginners, and none on a laptop CPU with an open model.
4. **Weak evaluation of leakage and learning.** Most work uses surveys or LLM judges. Few measure solution leakage directly, or do so together with pre/post learning scores.

---

## Part 4: Introduction outline (points only)

**Problem**
- Beginners struggle with abstract concepts and confusing error messages, and get little personal feedback outside class.
- LLM code tools now solve typical intro tasks easily [1], [2].

**Why it matters**
- Students use general chatbots, which often hand out full or near-full solutions even when asked not to [3], [4]. That leads to copying instead of learning.
- Instructors worry about over-reliance and academic integrity [2].

**What existing tools lack**
- Guardrailed tutors exist, such as CodeHelp, CS50 duck and CodeAid [5]–[7], and LLM error explainers [8], [9]. They rely on closed, paid, cloud models and on prompts alone.
- Open, small models can give feedback [10], [11], but they are rarely trained on human-written hints for real beginner mistakes.
- Few tools combine running the code, hints, concept explanation and progress tracking.

**Our contributions (3–4)**
1. A dataset of real beginner Python mistakes on MBPP problems [12]: the buggy attempt, the actual error, and hints and explanations written by the authors.
2. A small open code model fine-tuned with LoRA [13] to give step-by-step hints instead of solutions, running locally on a CPU.
3. A four-mode learning system: guided feedback with a sandbox, concept explanation with RAG [14], practice generation, and progress-based topic selection [15].
4. An evaluation comparing the fine-tuned model with its base model and a general chatbot (solution leakage, bug-type identification, hint quality), plus a small pre-test/post-test study.

**Paper organization**
- Section II: Literature Survey.
- Section III: Methodology (dataset, fine-tuning, architecture, algorithm).
- Section IV: Results and Discussion.
- Section V: Conclusion and Future Work.

**Literature Survey flow**
Background [1]–[4] → generating exercises and explanations [16], [17] → error explanation [8], [9] → hints and feedback [18]–[20], [10], [11] → tutoring systems [5]–[7], [21], [15] → RAG in education [14], [22] → PEFT [13], [23], [24] → datasets [12], [25] → comparison table → gaps.

---

## Part 5: References (IEEE format, numbered by first citation)

Rules used: list all authors up to six; with more than six, give the first author followed by "et al."

[1] B. A. Becker, P. Denny, J. Finnie-Ansley, A. Luxton-Reilly, J. Prather, and E. A. Santos, "Programming is hard – or at least it used to be: Educational opportunities and challenges of AI code generation," in *Proc. 54th ACM Tech. Symp. Comput. Sci. Educ. (SIGCSE)*, 2023, pp. 500–506, doi: 10.1145/3545945.3569759.

[2] J. Prather *et al.*, "The robots are here: Navigating the generative AI revolution in computing education," in *Proc. Working Group Rep. Innov. Technol. Comput. Sci. Educ. (ITiCSE-WGR)*, 2023, pp. 108–159, doi: 10.1145/3623762.3633499.

[3] A. Hellas, J. Leinonen, S. Sarsa, C. Koutcheme, L. Kujanpää, and J. Sorva, "Exploring the responses of large language models to beginner programmers' help requests," in *Proc. ACM Conf. Int. Comput. Educ. Res. (ICER)*, 2023, pp. 93–105, doi: 10.1145/3568813.3600139.

[4] N. Kiesler, D. Lohr, and H. Keuning, "Exploring the potential of large language models to generate formative programming feedback," in *Proc. IEEE Frontiers Educ. Conf. (FIE)*, 2023, pp. 1–5, doi: 10.1109/FIE58773.2023.10343457.

[5] M. Liffiton, B. E. Sheese, J. Savelka, and P. Denny, "CodeHelp: Using large language models with guardrails for scalable support in programming classes," in *Proc. 23rd Koli Calling Int. Conf. Comput. Educ. Res.*, 2023, pp. 1–11, doi: 10.1145/3631802.3631830.

[6] R. Liu, C. Zenke, C. Liu, A. Holmes, P. Thornton, and D. J. Malan, "Teaching CS50 with AI: Leveraging generative artificial intelligence in computer science education," in *Proc. 55th ACM Tech. Symp. Comput. Sci. Educ. (SIGCSE)*, 2024, pp. 750–756, doi: 10.1145/3626252.3630938.

[7] M. Kazemitabaar *et al.*, "CodeAid: Evaluating a classroom deployment of an LLM-based programming assistant that balances student and educator needs," in *Proc. CHI Conf. Human Factors Comput. Syst.*, 2024, pp. 1–20, doi: 10.1145/3613904.3642773.

[8] J. Leinonen *et al.*, "Using large language models to enhance programming error messages," in *Proc. 54th ACM Tech. Symp. Comput. Sci. Educ. (SIGCSE)*, 2023, pp. 563–569, doi: 10.1145/3545945.3569770.

[9] A. Taylor, A. Vassar, J. Renzella, and H. Pearce, "dcc --help: Transforming the role of the compiler by generating context-aware error explanations with large language models," in *Proc. 55th ACM Tech. Symp. Comput. Sci. Educ. (SIGCSE)*, 2024, pp. 1314–1320, doi: 10.1145/3626252.3630822.

[10] C. Koutcheme, N. Dainese, S. Sarsa, A. Hellas, J. Leinonen, and P. Denny, "Open source language models can provide feedback: Evaluating LLMs' ability to help students using GPT-4-as-a-judge," in *Proc. Conf. Innov. Technol. Comput. Sci. Educ. (ITiCSE)*, 2024, pp. 52–58, doi: 10.1145/3649217.3653612.

[11] N. Kotalwar, A. Gotovos, and A. Singla, "Hints-in-browser: Benchmarking language models for programming feedback generation," in *Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 37, 2024, pp. 29864–29877, doi: 10.52202/079017-0940.

[12] J. Austin *et al.*, "Program synthesis with large language models," 2021, *arXiv:2108.07732*, doi: 10.48550/arXiv.2108.07732.

[13] E. J. Hu *et al.*, "LoRA: Low-rank adaptation of large language models," in *Proc. Int. Conf. Learn. Represent. (ICLR)*, 2022, doi: 10.48550/arXiv.2106.09685.

[14] P. Lewis *et al.*, "Retrieval-augmented generation for knowledge-intensive NLP tasks," in *Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 33, 2020, pp. 9459–9474, doi: 10.48550/arXiv.2005.11401.

[15] G. Abdelrahman, Q. Wang, and B. Nunes, "Knowledge tracing: A survey," *ACM Comput. Surv.*, vol. 55, no. 11, pp. 1–37, 2023, doi: 10.1145/3569576.

[16] S. Sarsa, P. Denny, A. Hellas, and J. Leinonen, "Automatic generation of programming exercises and code explanations using large language models," in *Proc. ACM Conf. Int. Comput. Educ. Res. (ICER)*, 2022, pp. 27–43, doi: 10.1145/3501385.3543957.

[17] S. MacNeil *et al.*, "Experiences from using code explanations generated by large language models in a web software development e-book," in *Proc. 54th ACM Tech. Symp. Comput. Sci. Educ. (SIGCSE)*, 2023, pp. 931–937, doi: 10.1145/3545945.3569785.

[18] T. Phung *et al.*, "Automating human tutor-style programming feedback: Leveraging GPT-4 tutor model for hint generation and GPT-3.5 student model for hint validation," in *Proc. 14th Learn. Analytics Knowl. Conf. (LAK)*, 2024, pp. 12–23, doi: 10.1145/3636555.3636846.

[19] E. Al-Hossami, R. Bunescu, J. Smith, and R. Teehan, "Can language models employ the Socratic method? Experiments with code debugging," in *Proc. 55th ACM Tech. Symp. Comput. Sci. Educ. (SIGCSE)*, 2024, pp. 53–59, doi: 10.1145/3626252.3630799.

[20] P. Kargupta, I. Agarwal, D. Hakkani-Tür, and J. Han, "Instruct, not assist: LLM-based multi-turn planning and hierarchical questioning for Socratic code debugging," in *Findings Assoc. Comput. Linguistics: EMNLP*, 2024, pp. 9475–9495, doi: 10.18653/v1/2024.findings-emnlp.553.

[21] R. Schmucker, M. Xia, A. Azaria, and T. Mitchell, "Ruffle&Riley: Insights from designing and evaluating a large language model-based conversational tutoring system," in *Proc. Int. Conf. Artif. Intell. Educ. (AIED)*, LNCS, vol. 14829 (verify), 2024, pp. 75–90, doi: 10.1007/978-3-031-64302-6_6.

[22] K. Taneja, P. Maiti, S. Kakar, P. Guruprasad, S. Rao, and A. K. Goel, "Jill Watson: A virtual teaching assistant powered by ChatGPT," in *Proc. Int. Conf. Artif. Intell. Educ. (AIED)*, LNCS, vol. 14829 (verify), 2024, pp. 324–337, doi: 10.1007/978-3-031-64302-6_23.

[23] T. Dettmers, A. Pagnoni, A. Holtzman, and L. Zettlemoyer, "QLoRA: Efficient finetuning of quantized LLMs," in *Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 36, 2023, pp. 10088–10115, doi: 10.52202/075280-0441.

[24] L. Xu, H. Xie, S. J. Qin, X. Tao, and F. L. Wang, "Parameter-efficient fine-tuning methods for pretrained language models: A critical review and assessment," *IEEE Trans. Pattern Anal. Mach. Intell.*, vol. 48, no. 6, pp. 6107–6126, 2026, doi: 10.1109/TPAMI.2026.3657354.

[25] A. de Freitas, J. Coffman, M. de Freitas, J. Wilson, and T. Weingart, "FalconCode: A multiyear dataset of Python code samples from an introductory computer science course," in *Proc. 54th ACM Tech. Symp. Comput. Sci. Educ. (SIGCSE)*, 2023, pp. 938–944, doi: 10.1145/3545945.3569822.

**Added for Methodology (28 Oct 2026; all DOIs verified via Crossref/DataCite).** They are numbered in the order the Methodology outline cites them. If your text cites them in a different order, renumber.

[26] Y. Hu, U. Z. Ahmed, S. Mechtaev, B. Leong, and A. Roychoudhury, "Re-factoring based program repair applied to programming assignments," in *Proc. 34th IEEE/ACM Int. Conf. Automated Softw. Eng. (ASE)*, 2019, pp. 388–398, doi: 10.1109/ASE.2019.00044. *(Source of our dataset: the Refactory dataset.)*

[27] B. Hui *et al.*, "Qwen2.5-Coder technical report," 2024, *arXiv:2409.12186*, doi: 10.48550/arXiv.2409.12186. *(Our base model.)*

[28] T. Wolf *et al.*, "Transformers: State-of-the-art natural language processing," in *Proc. Conf. Empirical Methods Natural Lang. Process.: Syst. Demonstrations (EMNLP)*, 2020, pp. 38–45, doi: 10.18653/v1/2020.emnlp-demos.6. *(The training library.)*

**Still to add, for Results:**
- J. Brooke, "SUS: A 'quick and dirty' usability scale," in *Usability Evaluation in Industry*, 1996. (Not DOI-verified; find the exact citation yourselves.)
- **Software:** cite Unsloth, llama.cpp/GGUF, Ollama, ChromaDB and Streamlit as footnotes with their GitHub/website URLs, not as numbered papers. IEEE allows this for software.

**Notes on the IEEE format**
- Some IEEE templates also want the conference city. Add it from each paper's ACM/IEEE page if your guide asks.
- For ACM papers listed as "pp. 1–11" or "pp. 1–20" ([5], [7]), ACM uses an article number. Check the ACM page and write "Art. no. X" if your guide prefers.

---

## Spares (all DOIs verified)
- J. Finnie-Ansley *et al.*, "The robots are coming: Exploring the implications of OpenAI Codex on introductory programming," ACE 2022, doi: 10.1145/3511861.3511863. Codex beat most students on CS1 exam questions.
- M. Kazemitabaar *et al.*, "Studying the effect of AI code generators on supporting novice learners in introductory programming," CHI 2023, doi: 10.1145/3544548.3580919.
- W. Lyu *et al.*, "Evaluating the effectiveness of LLMs in introductory computer science education: A semester-long field study," L@S 2024, doi: 10.1145/3657604.3662036. A controlled semester study, useful for pre/post design.
- B. Sheese *et al.*, "Patterns of student help-seeking when using a large language model-powered programming assistant," ACE 2024, doi: 10.1145/3636243.3636249.
- B. Jury *et al.*, "Evaluating LLM-generated worked examples in an introductory programming course," ACE 2024, doi: 10.1145/3636243.3636252.
- A. Ghosh, N. Heffernan, and A. S. Lan, "Context-aware attentive knowledge tracing," KDD 2020, doi: 10.1145/3394486.3403282. A deep knowledge-tracing model.
- T. Phung *et al.*, "Generative AI for programming education: Benchmarking ChatGPT, GPT-4, and human tutors," ICER 2023 (Vol. 2), doi: 10.1145/3568812.3603476.
- P. Denny *et al.*, "Computing education in the era of generative AI," *Commun. ACM*, 2024, doi: 10.1145/3624720.
