"""Guards the A/B -> X/Y mapping and verdict reading, which every metric depends on."""
import math

import pytest

from judge import read_verdict, to_xy


def lp(**probs):
    return {k: math.log(v) for k, v in probs.items()}


@pytest.mark.parametrize("tokens, top, verdict, pa", [
    # "[[" and "A" as separate tokens
    (["Both are fine. ", "[[", "A", "]]"], [{}, {}, lp(A=0.7, B=0.2, C=0.1), {}], "A", 0.7),
    # "[[A" merged into one token; alternatives are "[[B" / "[[C"
    (["Explanation ", "[[A", "]]"], [{}, {"[[A": math.log(0.6), "[[B": math.log(0.3)}, {}], "A", 0.6),
    # an earlier "[[B]]" quoted in the explanation is ignored; the last verdict counts
    (['"[[B]]" means B. ', "[[", "C", "]]"], [{}, {}, lp(C=0.5, A=0.3, B=0.2), {}], "C", 0.3),
])
def test_read_verdict(tokens, top, verdict, pa):
    got, probs = read_verdict(tokens, top)
    assert got == verdict
    assert probs["A"] == pytest.approx(pa)


def test_no_verdict_is_a_format_error():
    assert read_verdict(["no verdict here"], [{}]) == (None, {})


@pytest.mark.parametrize("order, verdict, winner, p_x", [
    ("xy", "A", "x", 0.75),   # X is shown as A
    ("yx", "A", "y", 0.25),   # Y is shown as A, so A's probability belongs to Y
    ("yx", "B", "x", 0.25),
    ("xy", "C", "tie", 0.75),
])
def test_to_xy(order, verdict, winner, p_x):
    got = to_xy(order, verdict, {"A": 0.6, "B": 0.2, "C": 0.2})
    assert got["winner"] == winner
    assert got["p_x"] == pytest.approx(p_x)
    assert got["p_x"] + got["p_y"] == pytest.approx(1)
