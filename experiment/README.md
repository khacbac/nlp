# Experiment pipeline

```
select_questions.py   ->  data/questions.jsonl     (300 questions, committed)
generate_answers.py   ->  data/answers.jsonl       (900 answers, 3 models)
make_grading_sheet.py ->  data/grading_sheet_A.csv, data/grading_sheet_B.csv
                          data/key.csv              (git-ignored, keep private)
```

## 1. Questions

`data/questions.jsonl` is already generated (seed 42). To rebuild it:

```bash
pip install datasets
python select_questions.py
```

The validation split has 2,653 answerable questions from only 19 articles
(557 passages), so the script takes at most one question per passage and
30 per article. 275 of the 300 are "why/how" questions.

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
!python generate_answers.py --model qwen               # ~5 min on a T4
!python generate_answers.py --model gpt-oss            # ~25 min (rate limit)
!python generate_answers.py --model gemini             # ~25 min (rate limit)
```

Download `data/answers.jsonl` before the Colab session ends. Rerunning a
command skips answers that already exist, so a cut-off run just continues.
If Groq's free quota runs out, use `--model gpt-oss --provider openrouter`
with `OPENROUTER_API_KEY`.

Annotators should not open `answers.jsonl`: it names the model of each answer.

## 3. Grading sheets

```bash
python make_grading_sheet.py
```

Import `grading_sheet_A.csv` and `grading_sheet_B.csv` into two separate
Google Sheets, one per annotator, and add a 1-5 dropdown on the `score`
column (Data > Data validation). The two annotators do not see each
other's sheet. Only the person who ran the script keeps `key.csv`.

## Rubric (draft, agree on it before grading)

Score each answer against the passage and the gold answer:

| Score | Meaning |
|---|---|
| 5 | Correct and complete: contains the gold answer's content, nothing wrong. |
| 4 | Correct, but with a small omission or some unneeded detail. |
| 3 | Partly correct: gets part of the gold answer, or is correct but vague. |
| 2 | Mostly wrong, with only a small correct element. |
| 1 | Wrong, off-topic, or contradicts the passage. |

Grade the content, not the length or style. Before the real grading, both
annotators grade the same 20 answers, compare, and settle disagreements.
