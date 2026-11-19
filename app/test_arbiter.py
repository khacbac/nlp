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
