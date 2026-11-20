"""Measure what each layer of the inbox's routing rule buys, on the trap tickets.

Every canned ticket has a known correct draft (`answer` in data/tickets.json).
Each (judge, ticket, repeat) is judged once in both orders, exactly as the inbox
does, and the same two judgments are scored under three routing modes:

    single   trust one judgment, as most products do. Each of the two runs is
             one single-pass trial, so the trials split by whether the wrong
             draft was shown first (slot A) or second. A tie sends the draft
             shown first; a run with no verdict goes to a person.
    swap     send only when both orders pick the same draft (arbiter.decide).
    swap+fc  as swap, but a pick whose draft breaks a checked fact is held
             (factcheck.gate).

Each outcome is "wrong" (a reply that breaks the policy went to the customer),
"right", or "human" (a person decides). Raw judgments are appended to a JSONL
file, so an interrupted run resumes where it stopped.

    python app/bench.py --judges groq-gpt-oss-20b,groq-gpt-oss-120b --repeats 3
    python app/bench.py --report-only          # rebuild the tables from the JSONL
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import arbiter
import factcheck
import llm
import server

OUT = Path(__file__).resolve().parent / "results"
MODES = ["single, wrong shown first", "single, right shown first", "single", "swap", "swap+fc"]
OUTCOME_VI = {"wrong": "Gửi sai", "right": "Gửi đúng", "human": "Chuyển người"}


def traps() -> list[dict]:
    return [t for t in server.all_tickets() if t.get("canned") and "answer" in t]


def judge_ticket(judge: str, t: dict) -> dict:
    question = server.JUDGE_QUESTION.format(policy=server.POLICY, customer=t["customer"], message=t["message"])
    d = arbiter.arbitrate(judge, question, t["canned"][0], t["canned"][1])
    issues = [factcheck.check(x, t, server.PRODUCTS, server.POLICY) for x in t["canned"]]
    d = factcheck.gate(d, issues)
    return {"verdicts": [r["verdict"] for r in d["runs"]], "status": d["status"], "held": d["held"],
            "judgments": [r["judgment"] for r in d["runs"]]}


def score(draft: int | None, answer) -> str:
    if draft is None:
        return "human"
    return "right" if answer == "any" or draft == answer else "wrong"


def outcomes(row: dict, answer) -> list[tuple[str, str]]:
    """(mode, outcome) pairs for one judged ticket."""
    out = []
    for run, v in enumerate(row["verdicts"], 1):
        first = 1 if run == 1 else 2  # the draft in slot A for this run
        pick = {"A": first, "C": first, "B": 3 - first}.get(v)
        o = score(pick, answer)
        out.append(("single", o))
        if answer != "any":
            out.append(("single, wrong shown first" if first != answer else "single, right shown first", o))
    d = arbiter.decide(*row["verdicts"])
    out.append(("swap", score(d["winner"], answer)))
    out.append(("swap+fc", "human" if row["held"] else score(d["winner"], answer)))
    return out


def report(rows: list[dict]) -> str:
    answers = {t["id"]: t["answer"] for t in traps()}
    rows = [r for r in rows if r["ticket"] in answers]
    judges = list(dict.fromkeys(r["judge"] for r in rows))
    label = {k: v[0] for k, v in llm.CATALOG.items()}
    lines = [f"# Hiệu quả từng lớp kiểm tra trên tin bẫy ({date.today():%d/%m/%Y})", "",
             f"{len({r['ticket'] for r in rows})} tin bẫy, mỗi tin chạy {max(r['rep'] for r in rows) + 1} lần cho mỗi giám khảo. "
             "\"Một lượt\" tính cả hai lượt chấm như hai lần thử độc lập.", ""]
    names = {"single, wrong shown first": "Một lượt, câu sai đứng trước",
             "single, right shown first": "Một lượt, câu đúng đứng trước",
             "single": "Một lượt (như phần lớn sản phẩm)",
             "swap": "+ Đảo thứ tự", "swap+fc": "+ Đảo thứ tự + Đối chiếu chính sách"}
    lines += ["| Giám khảo | Chế độ | Gửi sai | Gửi đúng | Chuyển người |", "|---|---|---|---|---|"]
    for j in judges:
        c = defaultdict(Counter)
        for r in rows:
            if r["judge"] == j:
                for mode, o in outcomes(r, answers[r["ticket"]]):
                    c[mode][o] += 1
        for mode in MODES:
            n = sum(c[mode].values())
            cells = [f"{c[mode][o]}/{n} ({c[mode][o] / n:.0%})" for o in ("wrong", "right", "human")]
            bold = "**" if mode == "swap+fc" else ""
            lines.append(f"| {label.get(j, j)} | {bold}{names[mode]}{bold} | " + " | ".join(cells) + " |")
    lines += ["", "## Từng tin", "", "Mỗi ô: kết quả sau cả hai lớp, theo từng lần chạy. "
              "✓ gửi đúng, ✗ gửi sai, ↻ đổi ý khi đảo thứ tự, ⊘ lớp đối chiếu giữ lại, ? phân vân hoặc không ra kết quả.", "",
              "| Tin | Đáp án | " + " | ".join(label.get(j, j) for j in judges) + " |",
              "|---|---|" + "---|" * len(judges)]
    for tid, ans in answers.items():
        cells = []
        for j in judges:
            marks = ""
            for r in sorted((r for r in rows if r["judge"] == j and r["ticket"] == tid), key=lambda r: r["rep"]):
                d = arbiter.decide(*r["verdicts"])
                if d["status"] == "flip":
                    marks += "↻"
                elif d["status"] not in arbiter.SAFE:
                    marks += "?"
                elif r["held"]:
                    marks += "⊘"
                else:
                    marks += "✓" if score(d["winner"], ans) == "right" else "✗"
            cells.append(marks or "–")
        lines.append(f"| {tid} | {'cả hai' if ans == 'any' else f'Gợi ý {ans}'} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--judges", default="groq-gpt-oss-20b,groq-gpt-oss-120b")
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--tickets", help="comma-separated ids; default: every trap ticket")
    ap.add_argument("--raw", type=Path, default=OUT / "bench.jsonl")
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()
    args.raw.parent.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(x) for x in args.raw.read_text().splitlines()] if args.raw.exists() else []

    if not args.report_only:
        llm.load_env()
        todo = [t for t in traps() if not args.tickets or t["id"] in args.tickets.split(",")]
        done = {(r["judge"], r["ticket"], r["rep"]) for r in rows}
        failures = 0
        for judge in args.judges.split(","):
            for rep in range(args.repeats):
                for t in todo:
                    if (judge, t["id"], rep) in done:
                        continue
                    try:
                        row = {"judge": judge, "ticket": t["id"], "rep": rep} | judge_ticket(judge, t)
                    except Exception as e:  # a rate limit or outage: skip, a rerun picks it up
                        failures += 1
                        print(f"  {judge} {t['id']} #{rep}: {llm.error_message(e)[:120]}", file=sys.stderr)
                        if failures >= 5:
                            sys.exit("Stopping after 5 failures; rerun later to resume.")
                        continue
                    rows.append(row)
                    with args.raw.open("a") as f:
                        f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    print(f"{judge} {t['id']} #{rep}: {row['status']}{' held' if row['held'] else ''} {row['verdicts']}")

    md = report(rows)
    args.raw.with_suffix(".md").write_text(md)
    print("\n" + md)


if __name__ == "__main__":
    main()
