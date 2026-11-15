# Experiment pipeline

```
select_questions.py   ->  data/questions.jsonl     (500 questions, committed)
generate_answers.py   ->  data/answers.jsonl       (1500 answers, 3 models)
make_grading_sheet.py ->  data/grading_sheet_A.csv ... _D.csv (one per annotator)
                          data/key.csv              (git-ignored, keep private)
```

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

Open a Colab notebook with a **T4 GPU** runtime, put the API keys in
Colab *Secrets* (key icon on the left), then run:

```python
!git clone https://github.com/khacbac/nlp.git
%cd nlp/experiment
!pip install -q vllm

import os
from google.colab import userdata
os.environ["GROQ_API_KEY"] = userdata.get("GROQ_API_KEY")      # console.groq.com
os.environ["GEMINI_API_KEY"] = userdata.get("GEMINI_API_KEY")  # aistudio.google.com

!python generate_answers.py --model gemini --limit 3   # trial run, read the output
!python generate_answers.py --model qwen               # ~10 min on a T4
!python generate_answers.py --model gpt-oss            # ~40 min
!python generate_answers.py --model gemini             # ~40 min, ~500 requests/day: 1-2 days
```

Download `data/answers.jsonl` before the Colab session ends, and upload it
again in the next session. Rerunning a command skips answers that already
exist, so a run cut off by a daily quota just continues the next day.
If Groq's free quota runs out, use `--model gpt-oss --provider openrouter`
with `OPENROUTER_API_KEY`.

Annotators should not open `answers.jsonl`: it names the model of each answer.

## 3. Grading sheets

```bash
python make_grading_sheet.py
```

Each question goes to one of the 6 pairs of the 4 annotators (A+B, A+C,
..., C+D), and both rate all three of its answers, so every answer gets two
ratings and each annotator gets about 750 rows (~12-13 hours).

Import each `grading_sheet_X.csv` into its own Google Sheet and share it
with that annotator only; add a 1-5 dropdown on the `score` column
(Data > Data validation). Annotators do not see each other's sheets. Only
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

Grade the content, not the length or style. Before the real grading, all
four annotators grade the same 20 answers, compare, and settle
disagreements.
