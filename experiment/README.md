# Experiment pipeline

```
select_questions.py     ->  data/questions.jsonl        (500 questions, committed)
generate_answers.ipynb  ->  Drive: answers_qwen.jsonl, answers_gpt-oss.jsonl, answers_gemini.jsonl
 (runs generate_answers.py on Colab)
make_grading_sheet.py   ->  data/grading_sheets.xlsx (one tab per annotator; also grading_sheet_A..D.csv)
                            data/key.csv                 (keep private)
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
| 5 | Correct and complete: contains the gold answer's content, nothing wrong. |
| 4 | Correct, but with a small omission or some unneeded detail. |
| 3 | Partly correct: gets part of the gold answer, or is correct but vague. |
| 2 | Mostly wrong, with only a small correct element. |
| 1 | Wrong, off-topic, or contradicts the passage. |

Grade the content, not the length or style. An answer that switches to
another language part-way is graded on its content; mention it in `note`. Before the real grading, all
four annotators grade the same 20 answers, compare, and settle
disagreements.
