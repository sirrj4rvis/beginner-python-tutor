"""
Builds train_tutor.ipynb (the Colab notebook) and Modelfile (for Ollama).

The notebook pastes in prompt_format.py and splits.py, so training and the app always use
the same prompt and the same split. Run this again after changing either file:
    python build_notebook.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
prompt_format_code = (HERE / "prompt_format.py").read_text(encoding="utf-8")
splits_code = (HERE / "splits.py").read_text(encoding="utf-8")
namespace = {}
exec(prompt_format_code, namespace)
SYSTEM_PROMPT = namespace["SYSTEM_PROMPT"]

MODELFILE = f'''# Ollama recipe for our fine-tuned tutor. Keep this file next to the .gguf file.
FROM ./beginner-tutor-Q4_K_M.gguf

# Qwen2.5 chat format (the same one used in training).
TEMPLATE """{{{{ if .System }}}}<|im_start|>system
{{{{ .System }}}}<|im_end|>
{{{{ end }}}}{{{{ if .Prompt }}}}<|im_start|>user
{{{{ .Prompt }}}}<|im_end|>
{{{{ end }}}}<|im_start|>assistant
{{{{ .Response }}}}<|im_end|>
"""

# Exactly the system prompt used in training.
SYSTEM """{SYSTEM_PROMPT}"""

PARAMETER stop "<|im_end|>"
PARAMETER stop "<|endoftext|>"
PARAMETER temperature 0
PARAMETER num_ctx 2048
'''

cells = []


def md(text):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": text.strip("\n")})


def code(text):
    cells.append({"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
                  "source": text.strip("\n")})


md("""
# Fine-tuning our beginner tutor (Qwen2.5-Coder-1.5B + LoRA)

This notebook teaches a small code model to answer a beginner's buggy code with **hints and a simple
explanation instead of the full solution**. It trains on our dataset `beginner_bugs.csv`.

**Before you start**
1. In Colab, open **Runtime → Change runtime type → T4 GPU**.
2. In your Google Drive, create a folder `GEN_AI` and put `beginner_bugs.csv` in it.
   (If it isn't there, the notebook asks you to upload it.)
3. Click **Runtime → Run all**. When asked, allow access to Google Drive.

**Time:** about 30–45 minutes for the main training and export. The optional 5-fold
cross-validation (Step 15) adds about 30–60 minutes. These are rough estimates.

**Everything it produces** goes to `MyDrive/GEN_AI/training_outputs/`:

| File | What it is |
|---|---|
| `split.json` | which rows are train / validation / test, and the 5 folds |
| `base_outputs.csv` | answers of the original model, before training |
| `test_outputs_side_by_side.csv` | base model vs fine-tuned model on the 12 test rows |
| `loss_curve.png`, `loss_history.csv` | training and validation loss |
| `lora_adapter/` | the small trained LoRA weights |
| `beginner-tutor-Q4_K_M.gguf`, `Modelfile` | the model for Ollama on your laptop |
| `training_settings.csv` / `.md` | all settings and timings, for the report |
| `cv_outputs.csv`, `cv_losses.csv` | 5-fold cross-validation results (optional step) |
""")

md("""
## Step 1: Check the GPU
A GPU is a graphics card that does the maths of training much faster than a normal processor.
Free Colab gives us an NVIDIA **T4** with about 15 GB of memory. The table below should say "Tesla T4".
If it says "command not found", go back and pick the T4 GPU runtime.
""")
code("!nvidia-smi")

md("""
## Step 2: Install Unsloth
**Unsloth** is a free library that makes fine-tuning about 2× faster and lighter on small GPUs.
It also has a one-line export to GGUF, the file format Ollama runs. It installs PyTorch, Hugging Face
Transformers and PEFT (the LoRA library) as well. This takes 2–4 minutes.
If this cell ends in an error, click **Runtime → Restart session** and run it again.
""")
code("""
%%capture
!pip install unsloth
""")

md("""
## Step 3: All settings in one place
These are the "knobs" of training. Here is what each one means and why we keep them small:

| Setting | Our value | What it means | Why this value for ~47 training rows |
|---|---|---|---|
| **LoRA rank `r`** | 8 | LoRA trains two small extra matrices beside each big weight matrix instead of changing the whole model. `r` is how "wide" those small matrices are, i.e. how much the model is allowed to change. | We only need to change the model's *style* (hints, fixed format, no solutions), not teach it lots of new knowledge. A small rank means fewer trainable numbers, so there is less risk of memorising 47 examples. |
| **LoRA alpha** | 16 | A scaling factor for how strongly the LoRA change is applied (strength = alpha / r = 2). | alpha = 2 × r is the usual safe default. |
| **LoRA dropout** | 0.05 | During training, 5% of the LoRA signals are randomly switched off at each step. | It acts like a small amount of noise that stops the model from relying on any one detail, which helps with tiny datasets. |
| **Learning rate** | 2e-4 | How big a step the weights take after each batch. | 2e-4 is the standard LoRA learning rate. Much higher can make training unstable; much lower barely learns in so few steps. |
| **Epochs** | 3 | One epoch = the model sees every training row once. | With few rows, 2–4 epochs is enough. More epochs start memorising (overfitting); Step 12 shows how to spot it. |
| **Batch size × gradient accumulation** | 2 × 2 = 4 | The model looks at 2 examples at a time and updates its weights after every 2 batches, so effectively every 4 examples. | Small batches fit in T4 memory and give more update steps (about 10 per epoch) from a small dataset. |
| **Warmup steps** | 3 | For the first 3 steps the learning rate climbs from 0 to 2e-4. | Avoids a big, careless first step. |
| **Max sequence length** | 1024 tokens | The longest example (prompt + answer) we allow. A *token* is a piece of a word. | Step 7 checks that our longest row fits. |
| **Seed** | 42 | Fixes all randomness (split, LoRA start values, data order). | Running again gives the same result, so our numbers are reproducible. |
""")
code("""
SEED = 42
BASE_MODEL = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
MAX_SEQ_LENGTH = 1024

LORA_R = 8
LORA_ALPHA = 16
LORA_DROPOUT = 0.05
TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

LEARNING_RATE = 2e-4
EPOCHS = 3
BATCH_SIZE = 2
GRAD_ACCUM = 2
WARMUP_STEPS = 3
WEIGHT_DECAY = 0.01
EVAL_EVERY_STEPS = 5          # measure validation loss every 5 training steps

TEST_FRACTION = 0.2           # 80/20 train/test split
VAL_FRACTION = 0.15           # part of the training rows kept aside to watch for overfitting
N_FOLDS = 5
RUN_CV = True                 # set to False to skip the 5-fold cross-validation (Step 15)
MAX_NEW_TOKENS = 320          # longest reply the model may write

DRIVE_DIR = "/content/drive/MyDrive/GEN_AI"
OUT_DIR = DRIVE_DIR + "/training_outputs"
""")

md("""
## Step 4: Connect Google Drive and load the dataset
We save every result to Google Drive, because Colab deletes its own files when the session ends.
""")
code("""
import os
import pandas as pd
from google.colab import drive, files

drive.mount("/content/drive")
os.makedirs(OUT_DIR, exist_ok=True)

csv_path = DRIVE_DIR + "/beginner_bugs.csv"
if not os.path.exists(csv_path):
    print("beginner_bugs.csv not found in Drive/GEN_AI, so please upload it now.")
    uploaded = files.upload()
    csv_path = "/content/" + next(iter(uploaded))

df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
rows = df.to_dict("records")
print(len(rows), "rows loaded")
print(df.groupby(["difficulty", "bug_type"]).size())
""")

md("""
## Step 5: Turn each row into a chat example
Chat models are trained on conversations with three roles:
- **system**: the standing instructions (be a tutor, never give the fix, use this format),
- **user**: the problem + the student's code + the real error,
- **assistant**: the answer we want: bug type, hint 1, hint 2 and an explanation, always in the same fixed format.

The fixed format lets the app show Hint 1 first and Hint 2 only when the student asks.
The code below is the same as `training/prompt_format.py` in our project, and the app uses it too.
""")
code(prompt_format_code + """

example = build_messages(rows[0])
for m in example:
    print(f"----- {m['role']} -----")
    print(m["content"])
""")

md("""
## Step 6: Split the data (80/20 + validation + 5 folds)
- **Test set (20% = 12 rows):** never used for training. We only use it at the end to compare the base model with our fine-tuned model.
- **Validation set (15% of the remaining rows = 7 rows):** also not trained on. We measure the loss on it during training to see whether the model is learning or just memorising, and we keep the checkpoint with the lowest validation loss. Using the test set for this would be cheating, because we would be choosing the model with the test data.
- **Training set:** the remaining 40 rows.
- **Stratified:** each split has the same mix of difficulty (easy/medium/hard) and bug type (runtime/logic) as the whole dataset.
- **5-fold cross-validation:** the rows are dealt into 5 groups. In Step 15 we train 5 times, each time holding out one group, so that *every* row gets an answer from a model that never saw it. With only 59 rows, one 12-row test set is a small sample; 5 folds give a fairer picture.
""")
code(splits_code + """

import json
train_all, test_rows = stratified_split(rows, TEST_FRACTION, SEED)
train_rows, val_rows = stratified_split(train_all, VAL_FRACTION, SEED)
folds = stratified_kfold(rows, N_FOLDS, SEED)

print(f"train {len(train_rows)}, validation {len(val_rows)}, test {len(test_rows)}")
print("fold sizes:", [len(f) for f in folds])
mix = pd.DataFrame([{"split": name, "difficulty": r["difficulty"], "bug_type": r["bug_type"]}
                    for name, part in [("train", train_rows), ("val", val_rows), ("test", test_rows)] for r in part])
display(pd.crosstab([mix.difficulty, mix.bug_type], mix.split))

with open(OUT_DIR + "/split.json", "w") as f:
    json.dump({"seed": SEED, "train": [int(r["id"]) for r in train_rows], "val": [int(r["id"]) for r in val_rows],
               "test": [int(r["id"]) for r in test_rows], "folds": folds}, f, indent=2)
""")

md("""
## Step 7: Load the base model
We load **Qwen2.5-Coder-1.5B-Instruct**: 1.5 billion numbers ("parameters"), already trained on code and on
following instructions. In 16-bit form it needs about 3 GB of GPU memory, which fits easily on the T4, so we do
**not** compress it to 4-bit for training. That keeps full quality. (Compressing a model is called
*quantization*; we only do it at the very end, for the laptop.)

We also check that every example fits within the maximum length.
""")
code("""
from unsloth import FastLanguageModel     # import Unsloth before Transformers so it can speed things up
import gc, time, torch

def load_base():
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL, max_seq_length=MAX_SEQ_LENGTH, dtype=None, load_in_4bit=False)
    return model, tokenizer

def free_gpu():
    gc.collect()
    torch.cuda.empty_cache()

model, tokenizer = load_base()
lengths = [len(tokenizer(tokenizer.apply_chat_template(build_messages(r), tokenize=False),
                         add_special_tokens=False)["input_ids"]) for r in rows]
print(f"Longest example: {max(lengths)} tokens (limit {MAX_SEQ_LENGTH}); average {sum(lengths) / len(lengths):.0f}")
assert max(lengths) <= MAX_SEQ_LENGTH, "Increase MAX_SEQ_LENGTH"
""")

md("""
## Step 8: Answers from the base model (before training)
To prove that training helped, we first record what the original model says for the same inputs.
We use **greedy decoding** (the model always picks its most likely next word), so the answers are repeatable.
If `RUN_CV` is on, we do this for all 59 rows (they are needed for the cross-validation comparison later);
otherwise only for the 12 test rows. Each answer takes a few seconds on the T4.
""")
code("""
def generate_reply(model, tokenizer, row):
    prompt = tokenizer.apply_chat_template(build_messages(row, with_answer=False), tokenize=False,
                                           add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt", add_special_tokens=False).to("cuda")
    start = time.time()
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=False,
                             pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id)
    seconds = time.time() - start
    reply = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
    return reply, seconds

FastLanguageModel.for_inference(model)
base_rows = rows if RUN_CV else test_rows
base_records = []
for i, r in enumerate(base_rows, 1):
    reply, sec = generate_reply(model, tokenizer, r)
    base_records.append({"id": int(r["id"]), "base_output": reply, "base_seconds": round(sec, 2)})
    print(f"{i}/{len(base_rows)} done", end="\\r")
base_df = pd.DataFrame(base_records)
base_df.to_csv(OUT_DIR + "/base_outputs.csv", index=False)
print("\\nExample base answer for row", base_records[0]["id"], ":\\n", base_records[0]["base_output"][:600])

del model; free_gpu()
""")

md("""
## Step 9: Add the LoRA adapters
**LoRA (Low-Rank Adaptation)** freezes all 1.5 billion original numbers and adds small trainable matrices to
the attention and feed-forward layers (the `TARGET_MODULES`). Only these small matrices learn, which is usually
well under 1% of the model. That is why training fits on a free GPU and why the result is a small "adapter" file.
""")
code("""
def add_lora(model):
    return FastLanguageModel.get_peft_model(
        model, r=LORA_R, lora_alpha=LORA_ALPHA, lora_dropout=LORA_DROPOUT, target_modules=TARGET_MODULES,
        bias="none", use_gradient_checkpointing="unsloth", random_state=SEED)

model, tokenizer = load_base()
model = add_lora(model)
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
total = sum(p.numel() for p in model.parameters())
print(f"Trainable parameters: {trainable:,} of {total:,} ({100 * trainable / total:.2f}%)")
""")

md("""
## Step 10: Prepare the examples for training ("train only on the answer")
The model reads text as numbers (**token ids**). For each example we also make **labels**: the tokens the model
should learn to produce. We set the labels of the system and user part to `-100`, which means "ignore".
So the model is graded **only on writing the tutor's answer**, not on repeating the question.
""")
code("""
from datasets import Dataset

def tokenize_row(row):
    messages = build_messages(row)
    full = tokenizer.apply_chat_template(messages, tokenize=False)
    prompt = tokenizer.apply_chat_template(messages[:-1], tokenize=False, add_generation_prompt=True)
    assert full.startswith(prompt)
    ids = tokenizer(full, add_special_tokens=False)["input_ids"]
    n_prompt = len(tokenizer(prompt, add_special_tokens=False)["input_ids"])
    return {"input_ids": ids, "attention_mask": [1] * len(ids), "labels": [-100] * n_prompt + ids[n_prompt:]}

def to_dataset(part):
    return Dataset.from_list([tokenize_row(r) for r in part])

train_ds, val_ds = to_dataset(train_rows), to_dataset(val_rows)
print(train_ds)
""")

md("""
## Step 11: Train
- Every **step** the model sees a batch, measures how wrong its answer is (the **loss**; lower is better) and nudges the LoRA weights.
- Every 5 steps it also measures the loss on the **validation** rows, which it never trains on.
- At the end we keep the checkpoint with the **lowest validation loss** (`load_best_model_at_end`). This protects us
  if the last epoch started to overfit.
""")
code("""
import inspect
from transformers import Trainer, TrainingArguments, DataCollatorForSeq2Seq
from unsloth import is_bfloat16_supported

def training_args(output_dir, eval_strategy, keep_best):
    args = dict(
        output_dir=output_dir, seed=SEED, num_train_epochs=EPOCHS, learning_rate=LEARNING_RATE,
        per_device_train_batch_size=BATCH_SIZE, per_device_eval_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUM, warmup_steps=WARMUP_STEPS, weight_decay=WEIGHT_DECAY,
        lr_scheduler_type="linear", optim="adamw_torch", logging_steps=1, report_to="none",
        fp16=not is_bfloat16_supported(), bf16=is_bfloat16_supported(), remove_unused_columns=False,
        eval_strategy=eval_strategy, eval_steps=EVAL_EVERY_STEPS)
    if keep_best:
        args.update(save_strategy=eval_strategy, save_steps=EVAL_EVERY_STEPS, save_total_limit=2,
                    load_best_model_at_end=True, metric_for_best_model="eval_loss", greater_is_better=False)
    else:
        args.update(save_strategy="no")
    if "eval_strategy" not in inspect.signature(TrainingArguments.__init__).parameters:
        args["evaluation_strategy"] = args.pop("eval_strategy")      # older Transformers versions
    return TrainingArguments(**args)

collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, padding=True, label_pad_token_id=-100)
trainer = Trainer(model=model, args=training_args("/content/checkpoints", "steps", keep_best=True),
                  train_dataset=train_ds, eval_dataset=val_ds, data_collator=collator)

start = time.time()
train_result = trainer.train()
train_minutes = (time.time() - start) / 60
history = pd.DataFrame(trainer.state.log_history)
history.to_csv(OUT_DIR + "/loss_history.csv", index=False)
best_val = trainer.state.best_metric
print(f"Training took {train_minutes:.1f} min, {trainer.state.global_step} steps. "
      f"Best validation loss {best_val:.4f} at {trainer.state.best_model_checkpoint}")
""")

md("""
## Step 12: Plot the loss curves, and how to spot overfitting
- **Training loss** (solid blue): how well the model fits the rows it trains on. It should go down.
- **Validation loss** (dashed orange): how well it does on 7 rows it never trains on.

How to read it:
- **Both go down:** the model is learning the general pattern. Good.
- **Training keeps going down but validation stops falling and starts to rise:** that is **overfitting**. The model
  is memorising the training rows instead of learning the general skill. The lowest point of the validation curve
  is the best moment to stop, and that checkpoint is the one we keep.
- **A big, growing gap between the two curves** is also a sign of overfitting.
- If validation rises from the start: lower `EPOCHS` or `LEARNING_RATE`, or raise `LORA_DROPOUT`, then run again.

The training loss jumps around because each step sees only 4 examples. Look at the overall trend.
""")
code("""
import matplotlib.pyplot as plt

def plot_losses(history, path, title):
    train = history.dropna(subset=["loss"]) if "loss" in history else history.iloc[0:0]
    val = history.dropna(subset=["eval_loss"])
    fig, ax = plt.subplots(figsize=(3.5, 2.4), dpi=300)             # one IEEE column wide
    ax.plot(train["epoch"], train["loss"], color="#2a78d6", linewidth=1.2, label="Training loss")
    ax.plot(val["epoch"], val["eval_loss"], color="#eb6834", linewidth=1.2, linestyle="--",
            marker="o", markersize=3, label="Validation loss")
    for series, col, color in [(train, "loss", "#2a78d6"), (val, "eval_loss", "#eb6834")]:
        if len(series):
            ax.annotate(f"{series[col].iloc[-1]:.2f}", (series["epoch"].iloc[-1], series[col].iloc[-1]),
                        textcoords="offset points", xytext=(4, 0), fontsize=6, color="#0b0b0b", va="center")
    ax.set_title(title, fontsize=8, loc="left", color="#0b0b0b")
    ax.set_xlabel("Epoch", fontsize=7, color="#52514e")
    ax.set_ylabel("Loss", fontsize=7, color="#52514e")
    ax.tick_params(labelsize=6, colors="#52514e", length=0)
    ax.grid(color="#e4e3df", linewidth=0.5)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(fontsize=6, frameon=False)
    fig.tight_layout()
    fig.savefig(path, facecolor="white")
    plt.show()

plot_losses(history, OUT_DIR + "/loss_curve.png", "Training and validation loss")
""")

md("""
## Step 13: Base model vs fine-tuned model on the 12 test rows
Now the fine-tuned model (the best checkpoint) answers the **test rows** it has never seen. We save a CSV with
our own written answer, the base model's answer and the fine-tuned answer side by side. The `parsed_*` columns
split each answer into bug type, hint 1, hint 2 and explanation, ready for the evaluation in Prompt 7.
Times here are on the Colab GPU; laptop CPU times are measured later in the app.
""")
code("""
FastLanguageModel.for_inference(model)
records = []
for i, r in enumerate(test_rows, 1):
    reply, sec = generate_reply(model, tokenizer, r)
    parsed = parse_reply(reply)
    records.append({"id": int(r["id"]), "task_id": r["task_id"], "difficulty": r["difficulty"],
                    "gold_bug_type": r["bug_type"], "gold_hint_1": r["hint_1"], "gold_hint_2": r["hint_2"],
                    "gold_explanation": r["explanation"], "finetuned_output": reply, "finetuned_seconds": round(sec, 2),
                    **{f"parsed_ft_{k}": v for k, v in parsed.items()}})
    print(f"{i}/{len(test_rows)} done", end="\\r")

side = pd.DataFrame(records).merge(base_df, on="id", how="left")
for k in ["bug_type", "hint_1", "hint_2", "explanation"]:
    side[f"parsed_base_{k}"] = side["base_output"].map(lambda t: parse_reply(t)[k])
side.to_csv(OUT_DIR + "/test_outputs_side_by_side.csv", index=False)
print("\\nSaved", len(side), "rows")
display(side[["id", "gold_bug_type", "parsed_base_bug_type", "parsed_ft_bug_type"]])
print("\\n=== Row", side.id[0], "fine-tuned ===\\n", side.finetuned_output[0])
print("\\n=== Row", side.id[0], "base ===\\n", side.base_output[0][:800])
""")

md("""
## Step 14: Save the adapter and export to GGUF (Q4_K_M) for Ollama
- `lora_adapter/` holds only the small trained LoRA matrices. Keep it as a backup.
- **GGUF** is a single-file model format that Ollama and llama.cpp run on a normal CPU.
- **Q4_K_M** is a quantization level: each number is stored in about 4 bits instead of 16. That makes the file about
  4× smaller (roughly 1 GB) and fast on a laptop, with only a small loss in quality. "K_M" is a well-balanced variant.
- Unsloth first merges the LoRA weights into the model, then converts and compresses it. This takes about 5–10
  minutes, because it builds the llama.cpp tools the first time.
""")
code(f'''
import glob, shutil

model.save_pretrained(OUT_DIR + "/lora_adapter")
tokenizer.save_pretrained(OUT_DIR + "/lora_adapter")

gguf_path = None
try:
    model.save_pretrained_gguf("/content/gguf_model", tokenizer, quantization_method="q4_k_m")
    found = [p for p in glob.glob("/content/**/*.gguf", recursive=True) if "q4_k_m" in p.lower()]
    gguf_path = OUT_DIR + "/beginner-tutor-Q4_K_M.gguf"
    shutil.copy(found[0], gguf_path)
    print("GGUF saved:", gguf_path, f"({{os.path.getsize(gguf_path) / 1e6:.0f}} MB)")
except Exception as e:
    print("GGUF export failed:", e)
    print("Fallback: saving the merged 16-bit model instead (see TRAINING_GUIDE.md, 'If the GGUF export fails').")
    model.save_pretrained_merged(OUT_DIR + "/merged_16bit", tokenizer, save_method="merged_16bit")

MODELFILE = {MODELFILE!r}
with open(OUT_DIR + "/Modelfile", "w") as f:
    f.write(MODELFILE)
print("Modelfile saved next to it.")
''')

md("""
## Step 15 (optional): 5-fold cross-validation
With only 12 test rows, one lucky or unlucky split could change our results a lot. Cross-validation trains
**5 separate models**. Each one trains on 4 of the folds and answers the 5th fold it has never seen. Together they
give an "unseen" fine-tuned answer for **every** row, and a validation loss per fold.
- Every fold uses exactly the same settings, with a fixed number of epochs (no "best checkpoint" choice, because
  the held-out fold is what we evaluate on).
- Takes roughly 6–12 minutes per fold. Set `RUN_CV = False` in Step 3 to skip it.
- The answers (`cv_outputs.csv`) are used in Prompt 7, together with the base answers from Step 8.
""")
code("""
cv_outputs, cv_losses = [], []
if RUN_CV:
    del trainer, model; free_gpu()
    for k, fold_ids in enumerate(folds, 1):
        held_out = [r for r in rows if int(r["id"]) in fold_ids]
        fold_train = [r for r in rows if int(r["id"]) not in fold_ids]
        model, tokenizer = load_base()
        model = add_lora(model)
        fold_trainer = Trainer(model=model, args=training_args(f"/content/cv_fold{k}", "epoch", keep_best=False),
                               train_dataset=to_dataset(fold_train), eval_dataset=to_dataset(held_out),
                               data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer, padding=True, label_pad_token_id=-100))
        start = time.time()
        fold_trainer.train()
        minutes = (time.time() - start) / 60
        fold_hist = pd.DataFrame(fold_trainer.state.log_history)
        final_val = fold_hist["eval_loss"].dropna().iloc[-1]
        final_train = fold_hist["loss"].dropna().iloc[-1]
        cv_losses.append({"fold": k, "train_rows": len(fold_train), "held_out_rows": len(held_out),
                          "final_train_loss": final_train, "final_val_loss": final_val, "minutes": round(minutes, 1)})
        FastLanguageModel.for_inference(model)
        for r in held_out:
            reply, sec = generate_reply(model, tokenizer, r)
            cv_outputs.append({"fold": k, "id": int(r["id"]), "finetuned_output": reply, "finetuned_seconds": round(sec, 2),
                               **{f"parsed_ft_{c}": v for c, v in parse_reply(reply).items()}})
        print(f"Fold {k}: validation loss {final_val:.4f}, {minutes:.1f} min")
        del fold_trainer, model; free_gpu()

    cv_loss_df = pd.DataFrame(cv_losses)
    cv_loss_df.to_csv(OUT_DIR + "/cv_losses.csv", index=False)
    pd.DataFrame(cv_outputs).to_csv(OUT_DIR + "/cv_outputs.csv", index=False)
    display(cv_loss_df)
    print(f"Mean validation loss over {N_FOLDS} folds: {cv_loss_df.final_val_loss.mean():.4f} "
          f"± {cv_loss_df.final_val_loss.std():.4f} (std)")
else:
    print("Cross-validation skipped (RUN_CV = False).")
""")

md("""
## Step 16: Settings table for the report
Everything needed for the "Training settings" table in the Methodology section, taken from this run.
Copy the numbers from the saved `training_settings.md` or `.csv`; don't retype them.
""")
code("""
import transformers, peft, unsloth
gpu = torch.cuda.get_device_properties(0)
settings = {
    "Base model": BASE_MODEL,
    "Fine-tuning method": "LoRA on a 16-bit base model (Unsloth + Hugging Face Trainer)",
    "LoRA rank r / alpha / dropout": f"{LORA_R} / {LORA_ALPHA} / {LORA_DROPOUT}",
    "LoRA target modules": ", ".join(TARGET_MODULES),
    "Trainable parameters": f"{trainable:,} of {total:,} ({100 * trainable / total:.2f}%)",
    "Epochs": EPOCHS,
    "Learning rate / scheduler / warmup": f"{LEARNING_RATE} / linear / {WARMUP_STEPS} steps",
    "Batch size x gradient accumulation": f"{BATCH_SIZE} x {GRAD_ACCUM} = {BATCH_SIZE * GRAD_ACCUM}",
    "Optimizer / weight decay": f"AdamW / {WEIGHT_DECAY}",
    "Max sequence length (longest example)": f"{MAX_SEQ_LENGTH} ({max(lengths)} tokens)",
    "Loss on": "assistant answer only (prompt tokens masked)",
    "Seed": SEED,
    "Rows: train / validation / test": f"{len(train_rows)} / {len(val_rows)} / {len(test_rows)}",
    "Training steps": train_result.global_step,
    "Training time (min)": round(train_minutes, 1),
    "Final training loss": round(history["loss"].dropna().iloc[-1], 4),
    "Best validation loss": round(best_val, 4),
    "GPU": f"{gpu.name} ({gpu.total_memory / 1e9:.0f} GB)",
    "Export": "GGUF Q4_K_M" + (f" ({os.path.getsize(gguf_path) / 1e6:.0f} MB)" if gguf_path else " (failed; merged 16-bit saved)"),
    "Library versions": f"unsloth {unsloth.__version__}, transformers {transformers.__version__}, "
                        f"peft {peft.__version__}, torch {torch.__version__}",
}
if cv_losses:
    settings["5-fold CV validation loss (mean ± std)"] = f"{cv_loss_df.final_val_loss.mean():.4f} ± {cv_loss_df.final_val_loss.std():.4f}"
    settings["5-fold CV total time (min)"] = round(cv_loss_df.minutes.sum(), 1)

table = pd.DataFrame(list(settings.items()), columns=["Setting", "Value"])
table.to_csv(OUT_DIR + "/training_settings.csv", index=False)
with open(OUT_DIR + "/training_settings.md", "w") as f:
    f.write("| Setting | Value |\\n|---|---|\\n" + "\\n".join(f"| {k} | {v} |" for k, v in settings.items()) + "\\n")
display(table)
""")

md("""
## Done: next steps on your laptop
1. Download `beginner-tutor-Q4_K_M.gguf` and `Modelfile` from `MyDrive/GEN_AI/training_outputs/` into one folder,
   for example `D:\\GEN AI\\model\\`.
2. Follow **TRAINING_GUIDE.md → "Run it on your laptop with Ollama"** in our project.
3. Also download the whole `training_outputs` folder. Its CSVs and PNGs are needed for the Methodology and Results sections.
""")

notebook = {"cells": cells, "metadata": {"accelerator": "GPU", "colab": {"gpuType": "T4", "provenance": []},
                                         "kernelspec": {"display_name": "Python 3", "name": "python3"},
                                         "language_info": {"name": "python"}},
            "nbformat": 4, "nbformat_minor": 0}
for c in cells:                                  # notebook JSON stores source as a list of lines
    c["source"] = c["source"].splitlines(keepends=True)
(HERE / "train_tutor.ipynb").write_text(json.dumps(notebook, indent=1, ensure_ascii=False), encoding="utf-8")
(HERE / "Modelfile").write_text(MODELFILE, encoding="utf-8")
print(f"Wrote train_tutor.ipynb ({len(cells)} cells) and Modelfile")
