"""Decide, by rule, whether a question lacks a fact that changes the answer, and ask for it once.

The tax a household owes turns on a few facts: whether the money is business income at all
(a freelancer may be paid wages under a contract), the yearly revenue (01 tỷ and 03 tỷ change
the rules), and, for an amount, the industry group (each has its own rate). A question that
asks what tax applies but gives none of these can only get a generic answer, so the inbox asks
first. The rule is fixed, not a model's call: the same question is always asked the same thing,
and no model quota is spent on it.

Questions about deadlines, filing, invoices or abolished regimes are answered directly: their
answer does not depend on revenue. The person can always skip and get the general answer.
"""

import re

import factcheck
from retrieve import strip_marks, unaccented

# Freelancers may be running a business or may be paid wages by a company under a contract.
FREELANCE = r"tự do|freelanc\w*|hợp đồng dịch vụ|hợp đồng khoán|cộng tác viên|ctv|thù lao|nhận dự án|nhận job|job ngoài|upwork|fiverr|làm remote|làm từ xa"
# The question asks whether, how, or how much tax applies.
ASKS_TAX = (r"(có |)phải (đóng|nộp)|(đóng|nộp|tính) thuế (như thế nào|thế nào|ra sao|sao|gì|những gì)|"
            r"(đóng|nộp|tính|mất|hết) (thuế |)(bao nhiêu|mấy)|thuế (là |)bao nhiêu|mức thuế|(chịu|mất|bị) thuế|"
            r"thuế (gì|nào)|tính thế nào|tính sao")
# Asks for an amount or how the tax is worked out: the answer then states the group's rates.
ASKS_AMOUNT = r"bao nhiêu|mấy|mức thuế|tính thuế|số thuế|tính thế nào|tính sao|như thế nào|thế nào|ra sao"
# Answers that do not depend on revenue.
DIRECT = (r"khoán|môn bài|hoàn|nộp thừa|nộp dư|nộp lố|hạn nộp|khi nào|ở đâu|hồ sơ|tờ khai|hóa đơn|hoá đơn|"
          r"máy tính tiền|thủ tục|mẫu số|đăng ký")
# Words that name a line of business whose group is plain; the writers place it, as before.
# Work like IT, design or "online" fits several groups (a live draft gave IT the 1% rate of
# distribution), so the person is asked which group it is instead.
INDUSTRY = (r"tạp hóa|tạp hoá|bán|cửa hàng|sửa|cắt tóc|tóc|nail|spa|tư vấn|xây dựng|cho thuê|quán|nhà hàng|"
            r"cà phê|cafe|may|vận tải|xe ôm|grab|chạy xe|sản xuất|xưởng|làm bánh|youtube|tiktok|quảng cáo|"
            r"dạy|gia sư|chụp ảnh|nhiếp ảnh|đại lý|homestay|khách sạn|nhà nghỉ|phòng trọ")


def _rx(pattern: str) -> tuple[re.Pattern, re.Pattern]:
    """The pattern as written, and its unaccented twin for questions typed without marks."""
    return (re.compile(rf"\b(?:{pattern})\b", re.I), re.compile(rf"\b(?:{strip_marks(pattern)})\b", re.I))


RX = {k: _rx(v) for k, v in
      {"freelance": FREELANCE, "asks_tax": ASKS_TAX, "asks_amount": ASKS_AMOUNT, "direct": DIRECT, "industry": INDUSTRY}.items()}


def has(kind: str, text: str) -> bool:
    accented, plain = RX[kind]
    return bool((plain if unaccented(text) else accented).search(text))


INCOME_OPTIONS = [
    ("business", "Tôi tự tìm khách, tự kinh doanh"),
    ("wage", "Công ty, tổ chức trả tiền theo hợp đồng (tiền công, thù lao)"),
    ("both", "Cả hai"),
]
GROUP_OPTIONS = [(g["id"], g["ten"] + (f" (ví dụ: {g['vi_du']})" if g.get("vi_du") else ""))
                 for g in factcheck.RATES["groups"]] + [("unknown", "Không rõ")]
QUESTIONS = {
    "income": {"id": "income", "kind": "choice", "text": "Anh/chị nhận tiền theo cách nào?", "options": INCOME_OPTIONS},
    "revenue": {"id": "revenue", "kind": "amount", "text": "Doanh thu một năm khoảng bao nhiêu?",
                "hint": "Ví dụ: 800 triệu, 1,2 tỷ. Mốc 01 tỷ và 03 tỷ đồng làm thay đổi cách tính thuế."},
    "group": {"id": "group", "kind": "choice", "text": "Anh/chị kinh doanh ngành gì?", "options": GROUP_OPTIONS},
}


def questions(message: str) -> list[dict]:
    """What to ask before answering `message`; empty when the question can be answered as it is."""
    out = []
    if has("freelance", message):
        out.append("income")
    if has("asks_tax", message) and not has("direct", message):
        if not factcheck.money(message):
            out.append("revenue")
        if has("asks_amount", message) and not has("industry", message):
            out.append("group")
    return [QUESTIONS[k] for k in out]


def parse_revenue(text: str) -> int | None:
    """'1,2 tỷ' -> 1_200_000_000; a bare number is read in triệu ('800' -> 800 triệu)."""
    text = (text or "").strip()
    if not text:
        return None
    found = factcheck.money(text)
    if found:
        v = found[0][0]
    elif re.fullmatch(r"\d+(?:[.,]\d+)?", text):
        v = round(factcheck._num(text) * factcheck.TRIEU)
    else:
        raise ValueError("Doanh thu chưa đúng dạng, ví dụ: 800 triệu hoặc 1,2 tỷ.")
    if not 0 < v <= 10**15:
        raise ValueError("Doanh thu chưa hợp lệ.")
    return v


def accept(asked: list[dict], answers: dict) -> dict:
    """Validated answers to the questions that were asked; a blank answer stays unknown."""
    ids = {q["id"] for q in asked}
    out = {}
    for key in ("income", "group"):
        v = answers.get(key)
        if key in ids and v:
            if v not in {o[0] for o in QUESTIONS[key]["options"]}:
                raise ValueError("Lựa chọn không hợp lệ.")
            out[key] = v
    if "revenue" in ids:
        v = parse_revenue(str(answers.get("revenue") or ""))
        if v:
            out["revenue"] = v
    return out


def summary(answers: dict) -> str:
    """The answers as one line the writers and the judge read after the question."""
    parts = []
    if "income" in answers:
        parts.append("cách nhận tiền: " + dict(INCOME_OPTIONS)[answers["income"]].lower())
    if "revenue" in answers:
        parts.append("doanh thu năm khoảng " + factcheck.fmt(answers["revenue"]))
    if answers.get("group", "unknown") != "unknown":
        parts.append("ngành: " + next(g["ten"] for g in factcheck.RATES["groups"] if g["id"] == answers["group"]))
    return ("Thông tin bổ sung: " + "; ".join(parts) + ".") if parts else ""
