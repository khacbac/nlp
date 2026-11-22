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


# Citations are checked in the body too, down to the clause: a draft once cited an article it was
# never given in its body ("Điều 5 khoản 2") while its "Căn cứ:" line was clean.
@pytest.mark.parametrize("body, flagged", [
    ("Trên 03 tỷ phải tính theo thu nhập (Điều 5 khoản 2 Nghị định 68/2026/NĐ-CP).", True),   # article not given
    ("Theo Điều 4 khoản 2 Nghị định 68/2026/NĐ-CP, hộ phải khai thuế.", True),               # clause not given
    ("Theo khoản 5 Điều 4 Nghị định 68/2026/NĐ-CP, trên 03 tỷ tính theo thu nhập.", False),  # legal word order
])
def test_body_citations(body, flagged):
    t = {"message": "Làm IT tự do thì đóng thuế như thế nào?"}
    given = {"nd-68-2026:d4:k1", "nd-68-2026:d4:k5"}
    found = factcheck.check(body + "\nCăn cứ: Điều 4 khoản 1 Nghị định 68/2026/NĐ-CP", t, given, RECORDS)
    assert any(i.startswith("Trích") for i in found) is flagged


@pytest.mark.parametrize("draft, flagged", [
    # A live draft put the income method's 15% on revenue; for services the revenue rate is 2%.
    ("Thuế suất nhân doanh thu (doanh thu 01–03 tỷ đồng, thuế suất 15%).", True),
    ("Tính theo thu nhập tính thuế (doanh thu trừ chi phí) nhân thuế suất 15%.", False),
    ("Hàng hóa được giảm 20% mức tỷ lệ thuế GTGT trên doanh thu.", False),
])
def test_income_rate_on_revenue(draft, flagged):
    t = {"message": "Làm IT tự do thì đóng thuế như thế nào?"}
    found = factcheck.check(draft + "\nCăn cứ: Điều 4 khoản 5 Nghị định 68/2026/NĐ-CP", t, {"nd-68-2026:d4:k5"}, RECORDS)
    assert any("phương pháp thu nhập" in i for i in found) is flagged


# Follow-up questions: asked by rule, only for facts that change the answer, never for demo questions.
import clarify  # noqa: E402


@pytest.mark.parametrize("message, asked", [
    ("làm IT tự do thì đóng thuế như thế nào", ["income", "revenue", "group"]),  # IT fits several groups
    ("lam IT tu do thi dong thue nhu the nao", ["income", "revenue", "group"]),  # typed without marks
    ("Tôi làm job ngoài có phải đóng thuế không?", ["income", "revenue"]),
    ("Tôi kinh doanh thì đóng thuế bao nhiêu?", ["revenue", "group"]),        # no amount, no line of business
    ("Tôi bán hàng online thì phải đóng thuế bao nhiêu?", ["revenue"]),       # the writers place the business
    ("Tôi mới mở tiệm, mỗi tháng thu khoảng 50 triệu, có phải đóng thuế không?", []),  # an amount is given
    ("Hộ kinh doanh phải khai thuế theo tháng hay theo quý? Hạn nộp là khi nào?", []),  # answer does not depend on revenue
    ("Năm 2026 tôi có phải nộp lệ phí môn bài không?", []),
])
def test_clarify_questions(message, asked):
    assert [q["id"] for q in clarify.questions(message)] == asked


def test_demo_questions_are_never_asked_back():
    assert all(not clarify.questions(t["message"]) for t in TRAPS if t.get("revenue"))


@pytest.mark.parametrize("text, value", [("1,2 tỷ", 1_200_000_000), ("800 triệu", 800_000_000), ("1200", 1_200_000_000), ("", None)])
def test_parse_revenue(text, value):
    assert clarify.parse_revenue(text) == value


def test_clarify_rejects_unknown_answers():
    asked = clarify.questions("Tôi kinh doanh thì đóng thuế bao nhiêu?")
    with pytest.raises(ValueError):
        clarify.accept(asked, {"group": "khong-co"})
    with pytest.raises(ValueError):
        clarify.accept(asked, {"revenue": "nhiều lắm"})
    # an answer to a question that was not asked is ignored
    assert clarify.accept(asked, {"income": "wage", "revenue": "2 tỷ"}) == {"revenue": 2_000_000_000}


@pytest.mark.parametrize("draft, group, flagged", [
    # A live draft gave IT services the 1% GTGT rate of distribution.
    ("Tính thuế giá trị gia tăng theo phương pháp trực tiếp: thuế suất 1% trên doanh thu.", "dich-vu", True),
    ("Thuế GTGT 5% và thuế TNCN 2% trên doanh thu.", "dich-vu", False),
    ("Thuế GTGT 5% và thuế TNCN 1% trên doanh thu.", "dich-vu", True),       # each rate goes with its tax
    ("Hàng hóa được giảm 20% mức tỷ lệ GTGT, còn 4%.", "dich-vu", False),     # a reduction
    ("Thuế GTGT 5% trên tiền cho thuê.", "cho-thue-dai-ly", False),            # no GTGT rate in the law for this group
])
def test_group_rates(draft, group, flagged):
    t = {"message": "Doanh thu 1,5 tỷ thì đóng thuế bao nhiêu?", "group": group}
    found = factcheck.check(draft + "\nCăn cứ: Điều 4 khoản 5 Nghị định 68/2026/NĐ-CP", t, {"nd-68-2026:d4:k5"}, RECORDS)
    assert any("không phải tỷ lệ của nhóm" in i for i in found) is flagged


@pytest.mark.parametrize("draft, flagged", [
    # A live draft put GTGT on the part above 01 tỷ, which is the TNCN base.
    ("Về thuế giá trị gia tăng, anh/chị phải nộp thuế theo phương pháp trực tiếp trên phần doanh thu vượt trên mức 01 tỷ đồng.", True),
    ("Thuế GTGT tính trên phần vượt 1 tỷ đồng.", True),
    ("Thuế GTGT 5% tính trên toàn bộ doanh thu, còn thuế TNCN 2% tính trên phần vượt 01 tỷ đồng.", False),
    ("Thuế TNCN 2% tính trên phần doanh thu vượt 01 tỷ đồng.", False),
    ("Doanh thu trên 01 tỷ đồng thì phải nộp thuế GTGT.", False),            # the threshold, not the base
])
def test_gtgt_base(draft, flagged):
    t = {"message": "Doanh thu 1,2 tỷ thì đóng thuế thế nào?"}
    found = factcheck.check(draft + "\nCăn cứ: Điều 3 khoản 2 Nghị định 68/2026/NĐ-CP", t, {"nd-68-2026:d3:k2"}, RECORDS)
    assert any("toàn bộ doanh thu" in i for i in found) is flagged
