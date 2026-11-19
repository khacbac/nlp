# Experiment pipeline

```
select_questions.py     ->  data/questions.jsonl        (500 questions, committed)
generate_answers.ipynb  ->  Drive: answers_qwen.jsonl, answers_gpt-oss.jsonl, answers_gemini.jsonl
 (runs generate_answers.py on Colab)
make_grading_sheet.py   ->  data/grading_sheets.xlsx (one tab per annotator; also grading_sheet_A..D.csv)
                            data/key.csv                 (keep private)
judge.ipynb             ->  Drive: judgments_vi.jsonl   (runs judge.py on a Colab T4)
analyze.py              ->  results/metrics_vi.json, summary_vi.md, figures/
```

Answer files, grading sheets and `key.csv` are git-ignored: the repo is public
and they reveal which model wrote each answer.

## 1. Questions

`data/questions.jsonl` is already generated (seed 42). To rebuild it:

```bash
pip install datasets
python select_questions.py
```

Questions come from the train split (no model is trained; the validation
split has only 469 why/how questions on 318 passages). The script takes
at most one question per passage and 15 per article; all 500 are
"why/how" questions, from 108 articles.

## 2. Answers (Google Colab)

Open the notebook straight from GitHub:
<https://colab.research.google.com/github/khacbac/nlp/blob/main/experiment/generate_answers.ipynb>

Edit the notebook and scripts locally and push; each run pulls the latest
`main`. Put the API keys in Colab *Secrets* (key icon on the left):
`GEMINI_API_KEY` (aistudio.google.com), `GROQ_API_KEY` (console.groq.com),
optionally `OPENROUTER_API_KEY`.

| Model | Runtime | Time |
|---|---|---|
| Gemini Flash-Lite | CPU | ~40 min, but ~500 requests/day: 1-2 days |
| gpt-oss-20b (Groq) | CPU | ~40 min |
| Qwen2.5-7B-Instruct (vLLM) | T4 GPU | ~10 min + ~5 min install |

Answers go to `MyDrive/nlp-answers/answers_<model>.jsonl`, one line per
answer, so they survive a Colab reset. **After any error (quota, rate
limit, disconnect), just run the notebook again from the top**: answered
questions are skipped, failed or empty ones are retried, a daily quota
stops the run at once, and a half-written last line is ignored. One file
per model means two models can run in parallel sessions.

If Groq's free quota runs out, set `PROVIDER = "openrouter"` in the gpt-oss
cell. Annotators should not open the answer files: they name the model of
each answer.

## 3. Grading sheets

Download the three `answers_*.jsonl` files from Drive into `data/`, then:

```bash
pip install openpyxl
python make_grading_sheet.py
```

Run it **once**: every run makes new answer ids and a new `key.csv`, which
no longer match sheets already handed out. To only rebuild the workbook
from the existing CSVs (same ids), run `python grading_xlsx.py`.

Each question goes to one of the 6 pairs of the 4 annotators (A+B, A+C,
..., C+D), and both rate all three of its answers, so every answer gets two
ratings and each annotator gets about 750 rows (~12-13 hours).

The sheets drop markdown `*` emphasis (only one model uses it, which would
reveal it); the answer files keep the raw text.

Upload `grading_sheets.xlsx` to Drive, open it with Google Sheets
(File > Save as Google Sheets) and share it with the four annotators. It has
a "Hướng dẫn" tab with the rubric in Vietnamese, then tabs A-D, one per
annotator, formatted for grading: wrapped text, frozen header, a 1-5
dropdown on `score`, and the input columns in yellow. The CSVs hold the same
rows, for the analysis scripts.

Google Sheets cannot hide a tab from one person, so annotators can see each
other's scores. The team agreed to grade only their own tab; say so in the
report, since it weakens the independence of the two ratings. Only
the person who ran the script keeps `key.csv`; it records which pair rated
each answer, for Cohen's kappa per pair and Krippendorff's alpha overall.

## Rubric (draft, agree on it before grading)

Score each answer against the passage and the gold answer:

| Score | Meaning |
|---|---|
| 5 | Has the main point, and everything it says is in the passage. |
| 4 | Has the main point, but misses a small detail or adds one inference not in the passage (not contradicting it). |
| 3 | Only part of the main point, or vague with no specific point, or the main point plus one statement that contradicts the passage. |
| 2 | Misses the main point; only side points that are true but do not answer the question. |
| 1 | Wrong, off-topic, made up, or the main point contradicts the passage. |

The main point is what directly answers the question, usually the gold
answer's idea. Grade in two steps: (1) is the main point there, (2) is the
rest true to the passage. Extra content found in the passage costs nothing,
however long; an inference not in the passage caps the score at 4; a
statement that contradicts the passage caps it at 3. When torn between two
scores, pick the lower one.

Some gold answers are wrong or unanswerable (e.g. the gold answers a
different question, or the passage never says). Grade
those against the passage and write `gold_sai` in `note`, so they can be
excluded; an answer that correctly says the passage does not cover it
gets 5.

Grade the content, not the length or style. An answer that switches to
another language part-way is graded on its content; mention it in `note`. Before the real grading, all
four annotators grade the same 20 answers, compare, and settle
disagreements.

## 4. Judge (Google Colab, T4 GPU)

Open <https://colab.research.google.com/github/khacbac/nlp/blob/main/experiment/judge.ipynb>
and run all cells. Qwen2.5-7B-Instruct (AWQ, greedy) judges each of the 1500
pairs twice, once in each order, with the MT-Bench pairwise prompt (tie
`[[C]]` allowed) and the passage added to the question. The judge sees the
raw answers, not the gold answer. For each run it saves the verdict and the
probabilities of `A`/`B`/`C` at the verdict token; `p_x`/`p_y` are A/B
renormalised and mapped back to the two answers. A rerun skips finished
judgments. Download `judgments_vi.jsonl` from Drive into `data/` (git-ignored).

## 5. Analysis

```bash
pip install numpy matplotlib            # sentence-transformers: optional cosine baseline
python analyze.py                       # human scores from data/grading_sheet_A..D.csv
python analyze.py --scores-dir data/ai_graded   # trial run on AI scores -> results/trial/
```

It writes every criterion with a 95% bootstrap interval (resampling
questions, since the 3 pairs of one question are not independent) to
`results/metrics_vi.json`, a readable `results/summary_vi.md`, and the charts
in `results/figures/`. Questions with `gold_sai` in an annotator note are left
out of the human-based criteria. `data/pairs_vi.jsonl` keeps one row per pair
for picking demo examples (git-ignored: it names the models).

`test_judge.py` guards the A/B -> X/Y mapping and verdict reading
(`pytest test_judge.py`).
