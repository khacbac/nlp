"""Guards the routing rule: only a pick that survives the order swap, and whose draft the law does not
contradict, may be sent automatically."""
import pytest

from arbiter import SAFE, decide


@pytest.mark.parametrize("v1, v2, status, winner, naive", [
    ("A", "B", "agree", 1, 1),        # draft 1 wins in both slots
    ("B", "A", "agree", 2, 2),        # draft 2 wins in both slots
    ("C", "C", "tie", 1, None),       # consistent tie: send draft 1
    ("A", "A", "flip", None, 1),      # always slot A: first-position bias
    ("B", "B", "flip", None, 2),      # always slot B: second-position bias
    ("A", "C", "partial", None, 1),
    ("C", "B", "partial", None, None),
    (None, "A", "invalid", None, None),
])
def test_decide(v1, v2, status, winner, naive):
    d = decide(v1, v2)
    assert (d["status"], d["winner"], d["naive"]) == (status, winner, naive)
    # a winner exists exactly when the ticket may be sent without a person
    assert (d["status"] in SAFE) == (winner is not None)


# The fact check is the other half of the rule: a consistent pick is still held if its draft
# contradicts the law. The canned trap pairs in data/tickets.json are the ground truth here; each
# says whether the rule-based check is expected to catch its wrong draft (`fc_catches`).
import json  # noqa: E402
from pathlib import Path  # noqa: E402

import factcheck  # noqa: E402
import retrieve  # noqa: E402

INDEX = retrieve.Index.load()
RECORDS = {r["id"]: r for r in INDEX.records}
TRAPS = [t for t in json.loads((Path(__file__).parent / "data" / "tickets.json").read_text(encoding="utf-8")) if t.get("canned")]


def issues(t: dict) -> list[list[str]]:
    given = {h["id"] for h in INDEX.search(t["message"])["hits"]}  # what the server would give the writers
    return [factcheck.check(d, t, given, RECORDS) for d in t["canned"]]


@pytest.mark.parametrize("t", TRAPS, ids=lambda t: t["id"])
def test_factcheck_on_trap_pairs(t):
    res = issues(t)
    right = (1, 2) if t["answer"] == "any" else (t["answer"],)
    # A false flag on a correct draft sends a good answer to a person.
    assert all(res[n - 1] == [] for n in right)
    if t["answer"] != "any":
        assert bool(res[2 - t["answer"]]) is bool(t["fc_catches"])


@pytest.mark.parametrize("draft, flagged", [
    # "cũ" must match as a word, not inside "cũng" (a wrong draft once slipped through this way).
    ("Hộ có doanh thu trên 500 triệu đồng cũng phải nộp thuế.", True),
    # The part of this revenue above the threshold is not the old 500-million threshold.
    ("Thuế TNCN 1,5% trên phần vượt 500 triệu đồng là 7.500.000 đồng.", False),
])
def test_old_threshold_wording(draft, flagged):
    t = {"message": "Doanh thu 1,5 tỷ một năm thì nộp bao nhiêu?", "group": "san-xuat", "year": 2026}
    found = factcheck.check(draft + "\nCăn cứ: Điều 3 khoản 1 Nghị định 68/2026/NĐ-CP", t, {"nd-68-2026:d3:k1"}, RECORDS)
    assert any("500 triệu" in i for i in found) is flagged


@pytest.mark.parametrize("v1, v2, issues, held", [
    ("A", "B", [["x"], []], True),    # consistent pick of a draft with a wrong fact
    ("A", "B", [[], ["x"]], False),   # the other draft is wrong, the pick is fine
    ("A", "A", [["x"], []], False),   # already going to a person
])
def test_gate(v1, v2, issues, held):
    assert factcheck.gate(decide(v1, v2), issues)["held"] is held
