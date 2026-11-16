"""Build the blinded grading sheets for the four human annotators.

500 questions x 3 models = 1500 answers, and every answer is rated by two
annotators. Each question goes to one of the 6 pairs of annotators (A+B,
A+C, ..., C+D) in turn, so each annotator rates about 250 questions, i.e.
750 answers. Both annotators of a pair rate all three answers to the
question, so the score gap inside every answer pair comes from the same
two people.

Each row is one answer. Annotators see the passage, the question, the gold
answer and the model answer, and fill in a 1-5 score. They never see which
model wrote the answer:

- every answer gets a random id, unrelated to the model or the question;
- rows are shuffled, and the three answers to one question are never
  placed next to each other;
- each annotator gets their own sheet (grading_sheet_A.csv ... _D.csv).

The mapping answer_id -> (qid, model, annotators) goes to data/key.csv,
which is git-ignored and must not be shared with the annotators.

Usage:
    python make_grading_sheet.py
The sheets are also combined into one formatted workbook, grading_sheets.xlsx,
with one tab per annotator (see grading_xlsx.py); open it in Google Sheets.
"""

import argparse
import csv
import itertools
import json
import random
import re
import secrets
from pathlib import Path

from grading_xlsx import build_workbook  # pip install openpyxl

DATA = Path(__file__).parent / "data"
MODELS = ["qwen", "gpt-oss", "gemini"]
COLUMNS = ["answer_id", "context", "question", "gold_answer", "answer", "score", "note"]


def shuffle_apart(rows: list[dict], rng: random.Random) -> list[dict]:
    """Shuffle until no two neighbouring rows answer the same question."""
    for _ in range(10_000):
        rng.shuffle(rows)
        if all(a["qid"] != b["qid"] for a, b in zip(rows, rows[1:])):
            return rows
    raise RuntimeError("could not separate answers to the same question")


def strip_emphasis(text: str) -> str:
    """Drop markdown *italic* / **bold** asterisks.

    Only gpt-oss uses them, so annotators could tell its answers apart.
    The answer files keep the raw text, which is what the judge sees.
    """
    return re.sub(r"(\*{1,2})(\S(?:.*?\S)?)\1", r"\2", text)


def read_jsonl(path: Path) -> list[dict]:
    """Read a JSONL file, skipping a half-written line left by a killed run."""
    if not path.exists():
        return []
    rows = []
    for line in path.open(encoding="utf-8"):
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return rows


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    # utf-8-sig so Excel also shows Vietnamese correctly; Google Sheets ignores the BOM.
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", type=Path, default=DATA / "questions.jsonl")
    parser.add_argument("--answers-dir", type=Path, default=DATA,
                        help="folder with answers_qwen.jsonl, answers_gpt-oss.jsonl, answers_gemini.jsonl")
    parser.add_argument("--annotators", nargs="+", default=["A", "B", "C", "D"])
    args = parser.parse_args()

    questions = {q["qid"]: q for q in read_jsonl(args.questions)}
    answers = {}
    for m in MODELS:
        for a in read_jsonl(args.answers_dir / f"answers_{m}.jsonl"):
            if a.get("answer") or (a["qid"], m) not in answers:
                answers[(a["qid"], m)] = a  # a later non-empty answer wins

    missing = [(qid, m) for qid in questions for m in MODELS if (qid, m) not in answers]
    if missing:
        raise SystemExit(f"{len(missing)} answers missing, e.g. {missing[:3]}; run generate_answers.py first.")
    empty = [k for k in answers if k[0] in questions and not answers[k]["answer"]]
    if empty:
        raise SystemExit(f"{len(empty)} empty answers, e.g. {empty[:3]}; rerun generate_answers.py to retry them.")

    # Not seeded on purpose: the ids must not be reproducible from the repo.
    rng = random.Random(secrets.randbits(64))
    ids = rng.sample(range(10000, 100000), len(questions) * len(MODELS))
    pairs = list(itertools.combinations(args.annotators, 2))
    qids = list(questions)
    rng.shuffle(qids)
    rows = []
    for i, qid in enumerate(qids):
        q, pair = questions[qid], pairs[i % len(pairs)]
        for m in MODELS:
            a = answers[(qid, m)]
            rows.append({
                "answer_id": f"A{ids.pop()}",
                "qid": qid,
                "model": m,
                "context": q["context"],
                "question": q["question"],
                "gold_answer": " | ".join(dict.fromkeys(q["gold_answers"])),
                "answer": strip_emphasis(a["answer"]),
                "num_words": a["num_words"],
                "annotators": "+".join(pair),
                "score": "",
                "note": "",
            })

    write_csv(DATA / "key.csv", sorted(rows, key=lambda r: r["answer_id"]),
              ["answer_id", "qid", "model", "annotators", "num_words"])
    paths = []
    for name in args.annotators:
        mine = [r for r in rows if name in r["annotators"].split("+")]
        path = DATA / f"grading_sheet_{name}.csv"
        write_csv(path, shuffle_apart(mine, rng), COLUMNS)
        paths.append(path)
        print(f"wrote {path} ({len(mine)} rows)")
    print(f"wrote {build_workbook(paths, DATA / 'grading_sheets.xlsx')}")
    print(f"wrote {DATA / 'key.csv'} (keep private)")


if __name__ == "__main__":
    main()
