"""Measure retrieval on hand-written questions: is each expected clause among the clauses given to the writers?

data/tax/retrieval_eval.jsonl has one question per line with the clause ids a correct answer needs.
A clause counts as found when it is in what the server would give the writers (top-k plus the core
clauses), so this measures exactly what matters: could the writer have cited the right clause?

    python app/eval_retrieval.py          # recall, misses listed
    python app/eval_retrieval.py --all    # also print every question's hits

Target before changing prompts or adding traps: recall >= 0.90 and every question "enough".
"""

import argparse
import json
from pathlib import Path

import retrieve

EVAL = Path(__file__).resolve().parent / "data" / "tax" / "retrieval_eval.jsonl"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    idx = retrieve.Index.load()
    rows = [json.loads(l) for l in EVAL.read_text(encoding="utf-8").splitlines() if l]
    found = total = weak = 0
    for r in rows:
        res = idx.search(r["q"])
        got = [h["id"] for h in res["hits"]]
        miss = [e for e in r["expect"] if e not in got]
        found += len(r["expect"]) - len(miss)
        total += len(r["expect"])
        weak += not res["enough"]
        if miss or not res["enough"] or args.all:
            print(f"{'MISS' if miss else 'ok  '} best={res['best']:<6} {r['q']}")
            for m in miss:
                print(f"       thiếu {m}")
            if args.all:
                print("       có: " + ", ".join(got))
    print(f"\nrecall {found}/{total} = {found / total:.2f}; câu bị coi là không đủ căn cứ: {weak}/{len(rows)}")


if __name__ == "__main__":
    main()
