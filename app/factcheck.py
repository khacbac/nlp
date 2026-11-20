"""Check a reply draft against the shop's facts, without asking an LLM.

The experiment's strongest result is that a consistent judge is not a correct
judge: keeping only verdicts that survive the order swap lowered agreement with
humans (27.6%), while a plain comparison against the gold answer reached 68.9%.
In a support inbox the policy and the stock table are the gold answer, so the
facts they pin down (prices, percentages, stock, arrival dates) are checked by
rule here. A draft the judge picked consistently is still held for a person if
it states a fact the shop's data contradicts.

What this catches: wrong amounts, invented percentages, "in stock" for a sold
out product, promising an out-of-stock item arrives in time. What it cannot
catch: judgment calls (is a bicycle knock "impact damage"?), which stay with
the judge and the order swap.
"""

import re
from itertools import combinations

MONEY = re.compile(r"(\d{1,3}(?:\.\d{3})+)\s*(?:đ|đồng|vnđ)", re.I)
PERCENT = re.compile(r"(\d+(?:[.,]\d+)?)\s*%")
DATE = re.compile(r"\b(\d{1,2})/(\d{1,2})\b")
SHIPPING = 30000
REFUND_SHARE = 0.2  # policy 3(b): keep the item, get 20% back


def amounts(text: str) -> set[int]:
    return {int(m.replace(".", "")) for m in MONEY.findall(text)}


def percents(text: str) -> set[str]:
    return {p.replace(",", ".") for p in PERCENT.findall(text)}


def sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?;])\s+", text) if s]


def day_month(text: str) -> tuple[int, int] | None:
    m = DATE.search(text)
    return (int(m[2]), int(m[1])) if m else None


def allowed_amounts(policy: str, products: list, ticket: dict) -> set[int]:
    """Every amount a correct reply could state: policy figures, prices, 20% refunds, order totals."""
    ok = amounts(policy) | amounts(ticket["message"])
    prices = [p["price"] for p in products]
    ok |= set(prices) | {round(p * REFUND_SHARE) for p in prices}
    mine = [p["price"] for p in products if p["id"] in ticket.get("products", [])]
    for k in range(2, len(mine) + 1):
        ok |= {sum(c) for c in combinations(mine, k)}
    ok |= {x + SHIPPING for x in set(ok)}
    return ok


def check(draft: str, ticket: dict, products: list, policy: str) -> list[str]:
    """Facts in `draft` that the policy or stock table contradicts, as short Vietnamese notes."""
    issues = []
    ok_money = allowed_amounts(policy, products, ticket)
    for x in sorted(amounts(draft) - ok_money):
        issues.append(f"Số tiền {x:,}đ không có trong chính sách hay bảng giá".replace(",", "."))
    for p in sorted(percents(draft) - percents(policy) - percents(ticket["message"])):
        issues.append(f"Mức {p}% không có trong chính sách")

    sold_out = [p for p in products if p["stock"] <= 0]
    for s in sentences(draft):
        low = s.lower()
        for p in sold_out:
            named = any(a in low for a in p.get("aliases", [])) and not any(x in low for x in p.get("not", []))
            if named and "còn hàng" in low and "hết" not in low:
                issues.append(f"Nói còn hàng nhưng {p['name']} đang hết hàng")

    # A deadline in the customer's message that falls before an out-of-stock item's arrival date.
    need = day_month(ticket["message"])
    if need:
        for p in products:
            eta = p["stock"] <= 0 and p.get("eta") and day_month(p["eta"])
            if eta and p["id"] in ticket.get("products", []) and eta > need and re.search(r"(?<!không )kịp", draft.lower()):
                issues.append(f"Hứa kịp ngày {need[1]}/{need[0]}, nhưng hàng về {p['eta']}")
    return issues


def gate(decision: dict, issues: list[list[str]]) -> dict:
    """Hold a consistent pick for a person when the chosen draft breaks a checked fact."""
    w = decision["winner"]
    held = decision["status"] in ("agree", "tie") and bool(w and issues[w - 1])
    return decision | {"facts": issues, "held": held}
