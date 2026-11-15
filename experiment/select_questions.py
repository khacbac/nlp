"""Select the 500 UIT-ViQuAD 2.0 questions used in the experiment.

Rules (see proposal.md, Approach step 1):
- train split, answerable questions only (is_impossible = false); no model
  is trained, and the validation split has only 469 why/how questions,
  on 318 passages;
- "why"/"how" questions first, because their answers are long enough to compare;
- at most one question per passage and --per-title per article, so no
  passage or topic dominates (138 articles, 4101 passages);
- a fixed seed, so every team member gets the same questions.

Usage:
    pip install datasets
    python select_questions.py            # writes data/questions.jsonl
"""

import argparse
import json
import random
import re
from collections import defaultdict
from pathlib import Path

from datasets import load_dataset

DATASET = "taidng/UIT-ViQuAD2.0"

# Vietnamese markers of "why" / "how" questions.
WHY_HOW = re.compile(
    r"tại sao|vì sao|vì lý do gì|lý do (gì|nào)|nguyên nhân|như thế nào|thế nào"
    r"|làm sao|bằng cách nào|ra sao|mục đích|ý nghĩa"
)


def is_why_how(question: str) -> bool:
    return bool(WHY_HOW.search(question.lower()))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=500)
    parser.add_argument("--per-title", type=int, default=15)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "data/questions.jsonl")
    args = parser.parse_args()

    rows = [r for r in load_dataset(DATASET, split="train") if not r["is_impossible"]]
    rng = random.Random(args.seed)
    rng.shuffle(rows)

    why_how = [r for r in rows if is_why_how(r["question"])]
    others = [r for r in rows if not is_why_how(r["question"])]

    picked, per_title, used_contexts = [], defaultdict(int), set()
    for r in why_how + others:  # why/how first, then fill up with the rest
        if len(picked) == args.n:
            break
        if r["context"] in used_contexts or per_title[r["title"]] >= args.per_title:
            continue
        used_contexts.add(r["context"])
        per_title[r["title"]] += 1
        picked.append(r)

    if len(picked) < args.n:
        raise SystemExit(f"Only {len(picked)} questions fit the rules; raise --per-title.")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for r in sorted(picked, key=lambda r: r["id"]):
            f.write(json.dumps({
                "qid": r["id"],
                "title": r["title"],
                "context": r["context"],
                "question": r["question"],
                "gold_answers": r["answers"]["text"],
                "why_how": is_why_how(r["question"]),
            }, ensure_ascii=False) + "\n")

    n_why_how = sum(is_why_how(r["question"]) for r in picked)
    print(f"answerable: {len(rows)}, why/how available: {len(why_how)}")
    print(f"wrote {len(picked)} questions ({n_why_how} why/how) "
          f"from {len(per_title)} articles to {args.out}")


if __name__ == "__main__":
    main()
