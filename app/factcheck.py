"""Check a reply draft against the tax rules, by rule, without asking an LLM.

The experiment's strongest result is that a consistent judge is not a correct
judge: keeping only verdicts that survive the order swap lowered agreement with
humans (27.6%), while a plain comparison against the gold answer reached 68.9%.
Here the gold answer is the law: data/tax/rates.json holds the numbers (each
cited to a clause), and articles.jsonl holds the clauses the drafts may cite.
A draft the judge picked consistently is still held for a person when it
contradicts them.

What this catches:
- a threshold that is no longer in force ("từ 500 triệu đồng trở xuống");
- thuế khoán or lệ phí môn bài presented as still applying;
- a percentage that is not a rate in the law;
- an income-method rate (15%, 17%, 20% of taxable income) applied to revenue;
- GTGT worked out on the part of revenue above 01 tỷ (that base is TNCN's; GTGT is on all revenue);
- a GTGT or TNCN rate that is not the rate of the industry group, when the group is known
  (from the question, the person's answer, or a group the draft names);
- a tax amount that does not match the law for the revenue in the question;
- the revenue-percentage method used where revenue is above 03 tỷ;
- a missing "Căn cứ:" line, or a cited article or clause the draft was not given,
  in the "Căn cứ:" line or in the body ("theo Điều 5 khoản 2 Nghị định 68/2026/NĐ-CP").

What it cannot catch: judgment calls (which industry group a business is in,
whether a good is in the VAT-reduction list), which stay with the judge.
"""

import json
import re
from datetime import date
from pathlib import Path

TAX = Path(__file__).resolve().parent / "data" / "tax"
RATES = json.loads((TAX / "rates.json").read_text(encoding="utf-8"))

TY, TRIEU = 1_000_000_000, 1_000_000
MONEY = re.compile(
    r"(?P<ty>\d+(?:[.,]\d+)?)\s*(?:tỷ|tỉ)\s*(?P<trieu>\d+)\s*triệu"  # "1 tỷ 200 triệu"
    r"|(?P<num>\d+(?:[.,]\d+)*)\s*(?P<unit>tỷ|tỉ|triệu|nghìn|ngàn|đồng|vnđ|vnd|đ)(?![a-zà-ỹ])"
    r"|(?P<dotted>\d{1,3}(?:\.\d{3}){2,})",  # bare "15.000.000"
    re.I)
PERCENT = re.compile(r"(\d+(?:[.,]\d+)?)\s*%")
CITE_LINE = re.compile(r"căn cứ\s*:", re.I)
# "Điều 4 khoản 5" and the legal order "khoản 5 Điều 4" both name clause 5 of article 4.
CITE_DIEU = re.compile(r"(?:khoản\s+(\d+)\s+)?Điều\s+(\d+)(?:\s+khoản\s+(\d+))?", re.I)
SO_HIEU = re.compile(r"\b(\d{1,3}/\d{4}/[A-ZĐ][A-ZĐ0-9\-]*)", re.I)

# Whole-word matches only: "cũ" must not match inside "cũng".
NEGATION = re.compile(r"\b(không|bỏ|bãi bỏ|chấm dứt|hết|ngừng|trước đây|đã được thay|thay vì|cũ)\b")
# Words that mark an old threshold as history ("trước đây là 500 triệu"), not as the rule.
OLD_MARKERS = re.compile(r"\b(trước đây|trước kia|đã được thay|đã được nâng|thay vì|cũ|năm 2025|không còn)\b")
# Words that put a rate on taxable income (revenue minus costs), where 15/17/20% are the right rates.
INCOME_BASIS = re.compile(r"thu nhập tính thuế|thu nhập chịu thuế|trừ chi phí|trừ \(-\) chi phí|phương pháp thu nhập|theo thu nhập")
THRESHOLD_WORDS = ("trở xuống", "trở lên", "dưới", "không quá", "vượt", "ngưỡng", "mức doanh thu", "trên mức",
                   "doanh thu trên", "doanh thu năm trên", "doanh thu từ", "doanh thu năm từ")


def _num(s: str) -> float:
    if re.fullmatch(r"\d+,\d+", s):
        return float(s.replace(",", "."))
    if re.fullmatch(r"\d+\.\d{1,2}", s):  # "1.5 tỷ": decimal point
        return float(s)
    return float(s.replace(".", "").replace(",", ""))


def money(text: str) -> list[tuple[int, int, int]]:
    """Amounts in đồng with their (start, end) offsets: '1,5 tỷ', '7.500.000 đồng', '15 triệu'."""
    out = []
    for m in MONEY.finditer(text):
        if m["ty"]:
            v = _num(m["ty"]) * TY + int(m["trieu"]) * TRIEU
        elif m["dotted"]:
            v = _num(m["dotted"])
        else:
            unit = m["unit"].lower()
            scale = {"tỷ": TY, "tỉ": TY, "triệu": TRIEU, "nghìn": 1000, "ngàn": 1000}.get(unit, 1)
            v = _num(m["num"]) * scale
            if scale == 1 and v < 1000:
                continue  # "5 đ" is never a tax amount; likely a stray unit
        out.append((round(v), m.start(), m.end()))
    return out


def revenue_in(message: str) -> int | None:
    """The yearly revenue a customer states, if any: the first amount near 'doanh thu'."""
    for v, s, _ in money(message):
        if "doanh thu" in message[max(0, s - 40):s].lower() or "doanh thu" in message[s:s + 30].lower():
            return v
    return None


def sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?;])\s+|\n+", text) if s.strip()]


def fmt(v: float) -> str:
    return f"{round(v):,}".replace(",", ".") + " đồng"


def group_named(text: str) -> dict | None:
    """The industry group a draft says applies, if it names exactly one."""
    low = text.lower()
    named = [g for g in RATES["groups"] if g["ten"].split(",")[0].lower() in low]
    return named[0] if len(named) == 1 else None


def expected(revenue: int, group: dict, year: int) -> dict[str, set[int]]:
    """Every tax amount a correct draft could state for this revenue and group.

    Allows the reductions in force (TNCN −30% for 2026–2027 and revenue ≤ 10 tỷ;
    GTGT −20% for eligible goods until 31/12/2026), because the draft may or may
    not apply them depending on facts the question does not give, and quarterly
    shares (÷4) because households declare by quarter.
    """
    th = RATES["threshold"]["value"]
    if revenue <= th:
        return {"gtgt": {0}, "tncn": {0}}
    gtgt, tncn = set(), set()
    if group.get("gtgt") is not None:
        g = revenue * group["gtgt"]
        gtgt = {g, g * 0.8} if year <= 2026 else {g}
    if revenue <= RATES["tncn_revenue_method"]["max_revenue"]:
        t = (revenue - th) * group["tncn"]
        tncn = {t, t * 0.7} if year in (2026, 2027) and revenue <= 10 * TY else {t}
    both = {a + b for a in gtgt for b in tncn}
    quarterly = {x / 4 for x in gtgt | tncn | both}
    ok = {round(x) for x in gtgt | tncn | both | quarterly}
    return {"gtgt": {round(x) for x in gtgt}, "tncn": {round(x) for x in tncn}, "any": ok}


def close(a: int, b: int) -> bool:
    return abs(a - b) <= max(1000, 0.005 * max(a, b))


def check(draft: str, ticket: dict, retrieved: set[str], records: dict[str, dict]) -> list[str]:
    """Facts in `draft` the law contradicts, as short Vietnamese notes (empty list: nothing found)."""
    issues = []
    msg = ticket.get("message", "")
    asked = {v for v, _, _ in money(msg)}
    year = ticket.get("year") or date.today().year
    revenue = ticket.get("revenue") or revenue_in(msg)
    th = RATES["threshold"]["value"]
    # Amounts that describe the question, not the rule: the revenue and its part above the threshold.
    own = asked | ({revenue, revenue - th} if revenue else set())

    for s in sentences(draft):
        low = s.lower()
        # 1. A threshold that is no longer in force, stated as the rule.
        for old in RATES["outdated_thresholds"]:
            for v, a, b in money(s):
                if v == old["value"] and v not in asked:
                    before, after = low[max(0, a - 25):a], low[b:b + 25]
                    if revenue and v == revenue - th and "phần" in before and not after.lstrip().startswith(("trở", "đồng trở")):
                        continue  # "phần vượt 500 triệu": the part of this revenue above the threshold
                    if any(w in before + after for w in THRESHOLD_WORDS) and not OLD_MARKERS.search(low):
                        issues.append(f"Dùng ngưỡng {old['label']} đã hết hiệu lực; ngưỡng hiện hành là "
                                      f"{fmt(RATES['threshold']['value'])} (Nghị định 141/2026/NĐ-CP)")
        # 2. Abolished regimes presented as current.
        for ab, word in (("thue-khoan", "khoán"), ("mon-bai", "môn bài")):
            if word in low.replace("chứng khoán", "") and not NEGATION.search(low):
                what = next(x["what"] for x in RATES["abolished"] if x["id"] == ab)
                issues.append(f"Nói {what} vẫn áp dụng, nhưng đã bãi bỏ từ 01/01/2026 (Nghị quyết 198/2025/QH15 Điều 10)")

    # 3. Percentages that are not a rate, reduction or threshold share in the law.
    valid = {0.5, 1, 1.5, 2, 3, 5, 15, 17, 20, 30, 70, 80, 100}
    valid |= {float(p.replace(",", ".")) for p in PERCENT.findall(msg)}
    for p in {float(x.replace(",", ".")) for x in PERCENT.findall(draft)} - valid:
        issues.append(f"Mức {p:g}% không có trong luật thuế áp dụng cho hộ kinh doanh")

    # 3b. The income method's rates (15/17/20% of revenue minus costs) stated as a share of revenue.
    income_rates = {round(b["rate"] * 100) for b in RATES["tncn_income_method"]["brackets"]}
    for s in sentences(draft):
        low = s.lower()
        rates = {float(x.replace(",", ".")) for x in PERCENT.findall(s)} & income_rates
        if rates and "doanh thu" in low and not INCOME_BASIS.search(low) and "giảm" not in low:
            issues.append(f"Thuế suất {', '.join(f'{r:g}%' for r in sorted(rates))} là của phương pháp thu nhập "
                          "(doanh thu trừ chi phí), không áp lên doanh thu (Nghị định 68/2026/NĐ-CP Điều 4 khoản 5)")

    # 3b'. GTGT on the part above the threshold, a base that belongs to TNCN only.
    # The base belongs to the tax named last before it in the sentence ("GTGT 5% trên toàn bộ doanh thu,
    # TNCN 2% trên phần vượt" is right).
    for sent in sentences(draft):
        m = EXCESS_BASE.search(sent)
        named = list(TAX_NAME.finditer(sent[:m.start()])) if m else []
        if named and GTGT_NAME.fullmatch(named[-1][0]):
            issues.append("Thuế GTGT tính trên toàn bộ doanh thu, không phải trên phần vượt 01 tỷ đồng; chỉ thuế TNCN "
                          "theo tỷ lệ mới tính trên phần vượt (Nghị định 68/2026/NĐ-CP Điều 3 khoản 2, Điều 4 khoản 5)")
            break

    group = next((g for g in RATES["groups"] if g["id"] == ticket.get("group")), None) or group_named(draft)
    # 3c. Rates of the wrong group ("dịch vụ" is 5% GTGT and 2% TNCN, not distribution's 1%).
    if group:
        issues += group_rate_issues(draft, group)

    # 4–5. Amounts and method, when the revenue is known.
    if revenue:
        cap = RATES["tncn_revenue_method"]["max_revenue"]
        if revenue > cap and group and any(close(v, round((revenue - th) * group["tncn"] * f)) for v, _, _ in money(draft) for f in (1, 0.7)):
            issues.append(f"Doanh thu {fmt(revenue)} trên 03 tỷ phải tính thuế TNCN theo thu nhập tính thuế × thuế suất, "
                          "không được tính theo tỷ lệ trên doanh thu (Nghị định 68/2026/NĐ-CP Điều 4 khoản 5)")
        elif group and revenue <= cap:
            ok = expected(revenue, group, year)
            plain = own | {th, cap, 10 * TY}
            for v, a, _ in ((v, a, s) for s in sentences(draft) if "thuế" in s.lower() for v, a, _ in money(s)):
                if v in plain or v >= revenue:
                    continue
                if not any(close(v, x) for x in ok.get("any", ok["gtgt"] | ok["tncn"])):
                    gt = " hoặc ".join(fmt(x) for x in sorted(ok["gtgt"])) or "không có"
                    tn = " hoặc ".join(fmt(x) for x in sorted(ok["tncn"])) or "không có"
                    issues.append(f"Số thuế {fmt(v)} không khớp với luật cho doanh thu {fmt(revenue)}, nhóm "
                                  f"\"{group['ten']}\": GTGT {gt}; TNCN {tn}")

    # 6. Citations: a "Căn cứ:" line, and every article or clause cited anywhere was given to the draft.
    line = CITE_LINE.search(draft)
    if not line:
        issues.append("Thiếu dòng \"Căn cứ:\" nêu Điều luật")
    body = draft[:line.start()] if line else draft
    refs = cited(draft[line.start():]) if line else []
    refs += cited(body, sentences)  # in the body a document number only counts within its own sentence
    issues += citation_issues(refs, retrieved, records)
    return list(dict.fromkeys(issues))


def cited(text: str, split=lambda t: re.split(r"[;\n]", t)) -> list[tuple[int, int | None, str]]:
    """(article, clause or None, document number) for each "Điều N" in `text`.

    Each "Điều N" goes with the nearest document number, before or after it, within
    one part of `text` (items of a "Căn cứ:" line are usually separated by ";"),
    so both "Điều 4 Nghị định 68/2026/NĐ-CP" and "Nghị định 68/2026/NĐ-CP, Điều 4"
    read the same. An article with no document number in its part is skipped.
    """
    refs = []
    for part in split(text):
        docs = [(m.start(), m.end(), m[1].upper()) for m in SO_HIEU.finditer(part)]
        for m in CITE_DIEU.finditer(part):
            if docs:
                near = min(docs, key=lambda d: min(abs(m.start() - d[1]), abs(d[0] - m.end())))
                k = m[1] or m[3]
                refs.append((int(m[2]), int(k) if k else None, near[2]))
    return list(dict.fromkeys(refs))


def citation_issues(refs: list[tuple[int, int | None, str]], retrieved: set[str], records: dict[str, dict]) -> list[str]:
    """Notes for cited articles or clauses that are not in the corpus, or that the draft was not given."""
    def keys(rs):
        return {(r["dieu"], r["khoan"], a) for r in rs for a in r.get("aliases", [r["so_hieu"]])}
    given = keys(records[r] for r in retrieved if r in records)
    known = keys(records.values())
    issues = []
    for dieu, khoan, so in dict.fromkeys(refs):
        if not any(d == dieu and a == so for d, _, a in known):
            issues.append(f"Trích Điều {dieu} văn bản {so}, không có trong kho văn bản")
        elif not any(d == dieu and a == so for d, _, a in given):
            issues.append(f"Trích Điều {dieu} văn bản {so}, không nằm trong các Điều đã cung cấp")
        elif khoan is not None and (dieu, khoan, so) not in given:
            # An article given whole (no clauses) covers any clause of it.
            if (dieu, None, so) in given:
                continue
            where = "không nằm trong các khoản đã cung cấp" if (dieu, khoan, so) in known else "không có trong kho văn bản"
            issues.append(f"Trích khoản {khoan} Điều {dieu} văn bản {so}, {where}")
    return issues


# "phần doanh thu vượt trên mức 01 tỷ", "phần vượt 1 tỷ", "sau khi trừ 01 tỷ": the TNCN base.
EXCESS_BASE = re.compile(r"phần (?:doanh thu )?(?:vượt|trên|vượt quá|cao hơn|dôi ra)|(?:sau khi |)trừ (?:đi |)(?:mức |)0?1 tỷ", re.I)
GTGT_NAME = re.compile(r"gtgt|giá trị gia tăng", re.I)


TAX_NAME = re.compile(r"gtgt|giá trị gia tăng|tncn|thu nhập cá nhân", re.I)


def group_rate_issues(draft: str, group: dict) -> list[str]:
    """Percentages stated for GTGT or TNCN that are not this group's rate.

    Each percentage belongs to the tax named last before it in its sentence. Sentences about a
    reduction ("giảm 20%", "giảm 30%") are left alone, and so are the income method's rates.
    """
    allowed = {"gtgt": {group["gtgt"] * 100, group["gtgt"] * 80} if group.get("gtgt") is not None else None,
               "tncn": {group["tncn"] * 100} | {b["rate"] * 100 for b in RATES["tncn_income_method"]["brackets"]}}
    issues = []
    for s in sentences(draft):
        if "giảm" in s.lower():
            continue
        names = [(m.start(), "gtgt" if "gt" in m[0].lower() or "gia tăng" in m[0].lower() else "tncn") for m in TAX_NAME.finditer(s)]
        for m in PERCENT.finditer(s):
            tax = next((t for pos, t in reversed(names) if pos < m.start()), None)
            ok = allowed.get(tax) if tax else None
            p = float(m[1].replace(",", "."))
            if ok is not None and not any(abs(p - a) < 1e-6 for a in ok):
                label = "GTGT" if tax == "gtgt" else "TNCN"
                rate = f"{group[tax] * 100:g}%"
                issues.append(f"Tỷ lệ {label} {p:g}% không phải tỷ lệ của nhóm \"{group['ten']}\" ({rate} trên doanh thu)")
    return issues


def gate(decision: dict, issues: list[list[str]]) -> dict:
    """Hold a consistent pick for a person when the chosen draft breaks a checked fact."""
    w = decision["winner"]
    held = decision["status"] in ("agree", "tie") and bool(w and issues[w - 1])
    return decision | {"facts": issues, "held": held}
