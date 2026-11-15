"""Build the blinded grading sheets for the two human annotators.

Each row is one answer (300 questions x 3 models = 900 rows). Annotators
see the passage, the question, the gold answer and the model answer, and
fill in a 1-5 score. They never see which model wrote the answer:

- every answer gets a random id, unrelated to the model or the question;
- rows are shuffled, and the three answers to one question are never
  placed next to each other;
- each annotator gets their own shuffle (grading_sheet_A.csv, _B.csv).

The mapping answer_id -> (qid, model) goes to data/key.csv, which is
git-ignored and must not be shared with the annotators.

Usage:
    python make_grading_sheet.py
Then import each CSV into its own Google Sheet (File > Import), and add a
1-5 dropdown on the "score" column (Data > Data validation).
"""

import argparse
import csv
import json
import random
import secrets
from pathlib import Path

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


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    # utf-8-sig so Excel also shows Vietnamese correctly; Google Sheets ignores the BOM.
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", type=Path, default=DATA / "questions.jsonl")
    parser.add_argument("--answers", type=Path, default=DATA / "answers.jsonl")
    parser.add_argument("--annotators", nargs="+", default=["A", "B"])
    args = parser.parse_args()

    questions = {q["qid"]: q for q in map(json.loads, args.questions.open(encoding="utf-8"))}
    answers = {}
    for a in map(json.loads, args.answers.open(encoding="utf-8")):
        answers[(a["qid"], a["model"])] = a  # a rerun's later line wins

    missing = [(qid, m) for qid in questions for m in MODELS if (qid, m) not in answers]
    if missing:
        raise SystemExit(f"{len(missing)} answers missing, e.g. {missing[:3]}; run generate_answers.py first.")
    empty = [k for k in answers if k[0] in questions and not answers[k]["answer"]]
    if empty:
        raise SystemExit(f"{len(empty)} empty answers, e.g. {empty[:3]}; delete those lines and regenerate.")

    # Not seeded on purpose: the ids must not be reproducible from the repo.
    rng = random.Random(secrets.randbits(64))
    ids = rng.sample(range(1000, 10000), len(questions) * len(MODELS))
    rows = []
    for qid, q in questions.items():
        for m in MODELS:
            a = answers[(qid, m)]
            rows.append({
                "answer_id": f"A{ids.pop()}",
                "qid": qid,
                "model": m,
                "context": q["context"],
                "question": q["question"],
                "gold_answer": " | ".join(dict.fromkeys(q["gold_answers"])),
                "answer": a["answer"],
                "num_words": a["num_words"],
                "score": "",
                "note": "",
            })

    write_csv(DATA / "key.csv", sorted(rows, key=lambda r: r["answer_id"]),
              ["answer_id", "qid", "model", "num_words"])
    for name in args.annotators:
        path = DATA / f"grading_sheet_{name}.csv"
        write_csv(path, shuffle_apart(list(rows), rng), COLUMNS)
        print(f"wrote {path} ({len(rows)} rows)")
    print(f"wrote {DATA / 'key.csv'} (keep private)")


if __name__ == "__main__":
    main()
