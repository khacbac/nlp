"""Guards the routing rule: only a pick that survives the order swap may be sent automatically."""
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
# contradicts the policy or stock table. The canned trap pairs are the ground truth here.
import server  # noqa: E402
import factcheck  # noqa: E402

CANNED = {t["id"]: t for t in server.all_tickets() if t.get("canned")}


@pytest.mark.parametrize("tid, wrong", [("T-1042", 1), ("T-1044", 2), ("T-1055", 1)])
def test_factcheck_catches_wrong_fact(tid, wrong):
    t = CANNED[tid]
    issues = [factcheck.check(d, t, server.PRODUCTS, server.POLICY) for d in t["canned"]]
    assert issues[wrong - 1] and not issues[2 - wrong]


def test_factcheck_never_flags_correct_draft():
    # The correct draft of every trap pair (from DEMO.md); a false flag sends good replies to a person.
    correct = {"T-1042": 2, "T-1044": 1, "T-1045": 2, "T-1046": 1, "T-1047": 2, "T-1049": 1, "T-1054": 2,
               "T-1055": 2, "T-1057": 1, "T-1058": 2}
    for tid, n in correct.items():
        t = CANNED[tid]
        assert factcheck.check(t["canned"][n - 1], t, server.PRODUCTS, server.POLICY) == [], tid


@pytest.mark.parametrize("v1, v2, issues, held", [
    ("A", "B", [["x"], []], True),    # consistent pick of a draft with a wrong fact
    ("A", "B", [[], ["x"]], False),   # the other draft is wrong, the pick is fine
    ("A", "A", [["x"], []], False),   # already going to a person
])
def test_gate(v1, v2, issues, held):
    assert factcheck.gate(decide(v1, v2), issues)["held"] is held
