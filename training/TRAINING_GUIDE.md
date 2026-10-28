# Training guide: fine-tuning on Colab and running on your laptop

## Files in this folder
| File | What it is |
|---|---|
| `train_tutor.ipynb` | The Colab notebook, 16 steps. Each step has a plain-words explanation above its code. |
| `prompt_format.py` | The **one** definition of the tutor's system prompt, input layout and fixed answer format. Training and the app both use it. |
| `splits.py` | The balanced 80/20 split, validation split and 5 folds, with a fixed seed. |
| `build_notebook.py` | Rebuilds the notebook and `Modelfile` from the two files above. Run it after changing either one. |
| `Modelfile` | The Ollama "recipe" for the fine-tuned model. |
| `test_ollama.py` | Sends one dataset row to the model on your laptop and times the reply. |

## 1. Run the notebook on Colab
1. Go to https://colab.research.google.com → **File → Upload notebook** → choose `train_tutor.ipynb`.
2. **Runtime → Change runtime type → T4 GPU → Save.**
3. In Google Drive, create the folder `GEN_AI` and upload `dataset/beginner_bugs.csv` into it.
4. **Runtime → Run all.** Allow Google Drive access when asked.
5. When it finishes, download `MyDrive/GEN_AI/training_outputs/`. Keep everything: the CSVs and PNGs are your Methodology and Results material.

**The free GPU can disconnect if you're away too long.**
- Every output is saved to Drive as soon as its step finishes.
- After a disconnect, rerun from Step 1. Steps are quick apart from training, generating answers and exporting.
- To save about 30–60 minutes, set `RUN_CV = False` in Step 3. You can do the cross-validation in a later session.

## 2. Viva notes: what the notebook does, in one line per step
1. **Check the GPU:** confirm we have a T4.
2. **Install Unsloth:** makes LoRA training faster on small GPUs and can export GGUF.
3. **Settings:** all hyperparameters in one cell, with a table explaining each.
4. **Load the CSV** from Google Drive.
5. **Chat format:** turn each row into system + user + assistant messages.
   - The answer is always `Bug type / Hint 1 / Hint 2 / Explanation`.
   - *The `Bug type` line was added so Prompt 7 can measure bug-type accuracy.*
6. **Split:** stratified 80/20 (47 / 12 rows); 7 of the 47 are kept as validation (train 40). 5 folds for cross-validation. Seed 42.
7. **Load Qwen2.5-Coder-1.5B-Instruct** in 16-bit and check every example fits. The longest is 791 tokens; the limit is 1,024.
8. **Base model answers:** recorded before training, for the comparison.
9. **Add LoRA** (r = 8, alpha = 16): only the small adapter matrices train.
10. **Masking:** the loss is computed only on the answer tokens, not on the question.
11. **Train** for 3 epochs, measuring validation loss every 5 steps, and keep the best checkpoint.
12. **Loss curves**, and how to read overfitting (see below).
13. **Side-by-side CSV:** base vs fine-tuned answers on the 12 test rows.
14. **Save:** the LoRA adapter, plus the GGUF Q4_K_M export and `Modelfile` for Ollama.
15. **5-fold cross-validation** (optional): every row gets an answer from a model that never saw it.
16. **Settings table** for the report: model, LoRA settings, epochs, time, GPU and library versions.

**How to spot overfitting.** Training loss keeps falling while validation loss stops falling and rises; the gap between them grows. The best checkpoint is at the lowest validation loss. If validation rises early, lower the epochs or learning rate, or raise the dropout.

**Why the hyperparameters are small.** We have about 40 training rows and want to change the model's *style* (hints, format, no solutions), not its knowledge. A small rank and few epochs give it less capacity to memorise. The full table is in notebook Step 3.

## 3. Run it on your laptop with Ollama (Windows 11)
1. **Install Ollama.** Download it from https://ollama.com/download/windows and run `OllamaSetup.exe`. It then runs in the background (llama icon in the system tray).
2. **Check it works.** Open PowerShell and run:
   ```powershell
   ollama --version
   ```
3. **Put the model files together.** Create the folder `D:\GEN AI\model\` and place both files in it from `training_outputs`:
   - `beginner-tutor-Q4_K_M.gguf` (about 1 GB)
   - `Modelfile`

   The `Modelfile` in this `training/` folder is identical to the one in `training_outputs`.
4. **Create the model in Ollama:**
   ```powershell
   cd "D:\GEN AI\model"
   ollama create beginner-tutor -f Modelfile
   ollama list
   ```
   `ollama list` should now show `beginner-tutor`.
5. **Quick chat test:** run `ollama run beginner-tutor`, then type a question. Type `/bye` to leave.
6. **Proper test** with a real dataset row and the exact training prompt:
   ```powershell
   cd "D:\GEN AI\training"
   python test_ollama.py 37
   ```
   It prints the reply, the parsed hint parts and the seconds taken.
   - **Memory:** the model uses about 1.5–2 GB of your 16 GB RAM.
   - **Speed:** expect very roughly 10–30 seconds per reply on the CPU. Prompt 7 measures the real number.
7. **The app** (Prompt 6, M2) talks to the same address, `http://localhost:11434`, while Ollama is running.

**What the Modelfile does**
- `FROM`: which GGUF file to load.
- `TEMPLATE`: the Qwen chat format, the same one used in training.
- `SYSTEM`: the exact training system prompt.
- `PARAMETER stop`: where a reply ends.
- `temperature 0`: always the same answer for the same input.
- `num_ctx 2048`: how much text it can read at once.

## 4. If something goes wrong
| Problem | What to do |
|---|---|
| Step 2 install error | Runtime → Restart session, then run Step 2 again. |
| "CUDA out of memory" | Runtime → Restart session and run all again. If it repeats, set `BATCH_SIZE = 1` and `GRAD_ACCUM = 4` (the effective batch stays 4). |
| Step 14 GGUF export fails | The notebook automatically saves `merged_16bit/` (about 3 GB) instead. Download it into `D:\GEN AI\model\`, change the first line of `Modelfile` to `FROM ./merged_16bit`, then run `ollama create beginner-tutor -q q4_K_M -f Modelfile`, which makes Ollama do the 4-bit compression itself. If your Ollama version can't import that folder, rerun Step 14 in a new Colab session. The saved `lora_adapter/` means you don't have to retrain. |
| `test_ollama.py` can't connect | Make sure Ollama is running (tray icon, or run `ollama serve`) and that `ollama list` shows `beginner-tutor`. |
| Replies don't follow the format | Check that the `Modelfile` is the one from this project. The SYSTEM and TEMPLATE must match training. |

## 5. What to report honestly
- The loss values, times and settings come from **your** run. Copy them from `training_settings.md` and `cv_losses.csv`; don't retype or round differently.
- Generation times in the notebook are on the **GPU**. Laptop CPU times come from `test_ollama.py` and Prompt 7.
- **Small dataset:** with 40 training rows the model mainly learns the hint *style* and format, not new programming knowledge.
