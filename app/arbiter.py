"""Pick the better of two reply drafts without trusting the judge's position.

This is the experiment's protocol turned into a routing rule. The judge
(MT-Bench pair-v2 prompt, as in experiment/judge.py) sees the two drafts
twice, with their slots swapped:

    run 1: draft 1 is Assistant A, draft 2 is Assistant B
    run 2: draft 2 is Assistant A, draft 1 is Assistant B

A pick is trusted only when both runs name the same draft (or both call a
tie). Anything else means the slot, not the content, drove the verdict at
least once, so the ticket goes to a person instead of being sent.

    agree    both runs pick the same draft            -> safe to send
    tie      both runs say [[C]]                      -> safe to send draft 1
    partial  one run picks a draft, the other a tie   -> person decides
    flip     the runs pick different drafts           -> person decides
    invalid  a run gave no [[A]]/[[B]]/[[C]] verdict  -> person decides
"""

from concurrent.futures import ThreadPoolExecutor

import llm

SAFE = {"agree", "tie"}


def to_draft(verdict: str | None, run: int) -> int | str | None:
    """Map a run's slot verdict to a draft number (1/2), "tie", or None."""
    if verdict == "C":
        return "tie"
    if verdict not in ("A", "B"):
        return None
    first = 1 if run == 1 else 2  # the draft shown as Assistant A
    return first if verdict == "A" else 3 - first


def decide(v1: str | None, v2: str | None) -> dict:
    """Combine the two runs' slot verdicts into a routing decision.

    `naive` is what a single-pass judge (run 1 only) would have done; it
    shows how many tickets the second run saves from a position-driven pick.
    """
    p1, p2 = to_draft(v1, 1), to_draft(v2, 2)
    if p1 is None or p2 is None:
        status, winner = "invalid", None
    elif p1 == p2:
        status, winner = ("tie", 1) if p1 == "tie" else ("agree", p1)
    elif "tie" in (p1, p2):
        status, winner = "partial", None
    else:
        status, winner = "flip", None
    return {"status": status, "winner": winner, "picks": [p1, p2],
            "naive": p1 if p1 in (1, 2) else None}


def arbitrate(judge_model: str, question: str, draft1: str, draft2: str) -> dict:
    """Judge both orders in parallel and return the decision plus both runs."""
    with ThreadPoolExecutor(2) as pool:
        r1 = pool.submit(llm.judge_once, judge_model, question, draft1, draft2)
        r2 = pool.submit(llm.judge_once, judge_model, question, draft2, draft1)
        runs = [r1.result(), r2.result()]
    return decide(runs[0]["verdict"], runs[1]["verdict"]) | {"runs": runs, "judge": judge_model}
