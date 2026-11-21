"""Hộp thư thuế hộ kinh doanh: answers about household-business tax, grounded in the law.

For each question:

    scope rule ──► out of scope (companies, salaries…) ──► polite refusal, no model call
        │
    a fact the answer turns on is missing (clarify.py) ──► ask once, no model call; skippable
        │
    BM25 over the clauses in force (retrieve.py) ──► no clause scores high enough ──► "no legal basis found"
        │
    two models write a draft each, citing the clauses they were given
        │
    the judge compares the drafts in both orders (arbiter.py)
        │
    a rule-based check against rates.json and the cited clauses (factcheck.py)
        │
    pick survives the swap and passes the check ──► answer shown (or sent)
    otherwise ──► "chưa chắc chắn": the user sees the relevant clauses, not an unchecked draft

This is the position-bias experiment turned into a routing rule, with the
experiment's second lesson added: a consistent judge is not a correct one, so
the answer is also checked against the gold source, here the law itself.

Each browser gets its own inbox (a session cookie); one person's questions are
never shown to another. Inboxes are saved under data/state/ (gitignored).
"Chế độ trình bày" loads the trap questions from data/tickets.json for a demo.

Usage:
    python app/server.py            # then open http://localhost:8010
    python app/server.py --port 8080 --host 0.0.0.0
"""

import argparse
import json
import re
import secrets
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

APP = Path(__file__).resolve().parent
sys.path.insert(0, str(APP))

import arbiter  # noqa: E402
import clarify  # noqa: E402
import factcheck  # noqa: E402
import llm  # noqa: E402
import retrieve  # noqa: E402

DATA = APP / "data"
TAX = DATA / "tax"
STATES = DATA / "state"
SOURCES = {d["id"]: d for d in json.loads((TAX / "sources.json").read_text(encoding="utf-8"))}
CUTOFF = factcheck.RATES["cutoff"]
CUTOFF_VI = datetime.fromisoformat(CUTOFF).strftime("%d/%m/%Y")
INDEX = retrieve.Index.load()
RECORDS = {r["id"]: r for r in INDEX.records}

# Questions the corpus does not cover. A model would answer them from memory, which is exactly
# what this app exists to prevent, so they get a fixed reply without any model call.
OUT_OF_SCOPE = re.compile(
    r"\b(công ty|doanh nghiệp|tnhh|cổ phần|thuế tndn|thu nhập doanh nghiệp|lương tháng|lương hằng tháng|"
    r"quyết toán thuế tncn của người lao động|giảm trừ gia cảnh|người phụ thuộc|thuế đất|sổ đỏ|"
    r"chuyển nhượng bất động sản|bán nhà|bán đất|chứng khoán|thừa kế|trúng thưởng)\b", re.I)
OUT_OF_SCOPE_REPLY = (
    "Hộp thư này chỉ trả lời về thuế của hộ kinh doanh, cá nhân kinh doanh (ngưỡng doanh thu, thuế GTGT, "
    "thuế TNCN tính trên doanh thu, khai và nộp thuế, hóa đơn). Câu hỏi của anh/chị thuộc phạm vi khác "
    "(doanh nghiệp, tiền lương, bất động sản, đầu tư…), nên hộp thư không trả lời để tránh thông tin sai. "
    "Anh/chị vui lòng liên hệ cơ quan thuế quản lý hoặc tổng đài hỗ trợ của Cục Thuế.")
# Freelancers ("làm IT tự do", "nhận dự án") may be running a business or may be paid wages by
# a company under a contract; the two are taxed differently and the corpus only answers the first.
# The inbox asks which it is (clarify.py); a fixed note covers a skipped or "both" answer, a wage
# answer gets a fixed reply, and the two clauses that draw the line go to the writers.
FREELANCE_CLAUSES = ("vbhn-112-2026:d3:k1", "vbhn-112-2026:d3:k2")
FREELANCE_CAVEAT = (
    "Lưu ý cho người làm tự do: câu trả lời chỉ áp dụng khi anh/chị tự kinh doanh hàng hóa, dịch vụ "
    "(thu nhập từ kinh doanh, Luật Thuế thu nhập cá nhân Điều 3 khoản 1). Nếu anh/chị nhận tiền công, tiền thù lao "
    "từ công ty hay tổ chức theo hợp đồng, khoản đó là thu nhập từ tiền lương, tiền công (Điều 3 khoản 2), "
    "tính thuế theo cách khác và nằm ngoài phạm vi hộp thư. Trường hợp này anh/chị nên hỏi bên trả tiền "
    "hoặc cơ quan thuế quản lý.")
WAGE_REPLY = (
    "Tiền công, tiền thù lao anh/chị nhận từ công ty hay tổ chức theo hợp đồng là thu nhập từ tiền lương, tiền công "
    "(Luật Thuế thu nhập cá nhân Điều 3 khoản 2), không phải thu nhập của cá nhân kinh doanh. Hộp thư chỉ trả lời về "
    "thuế của hộ kinh doanh, cá nhân kinh doanh, nên không trả lời trường hợp này để tránh thông tin sai. "
    "Anh/chị vui lòng hỏi bên trả tiền hoặc cơ quan thuế quản lý.")
NO_BASIS_REPLY = (
    "Hộp thư chưa tìm thấy điều luật nào trong các văn bản đang có (hiệu lực đến {cutoff}) đủ khớp với câu hỏi, "
    "nên không trả lời để tránh đoán sai. Anh/chị có thể hỏi lại cụ thể hơn (loại hình kinh doanh, doanh thu năm, "
    "điều muốn biết) hoặc liên hệ cơ quan thuế quản lý.")

WRITER_SYSTEM = (
    "Bạn là chuyên viên tư vấn thuế cho hộ kinh doanh, cá nhân kinh doanh tại Việt Nam. "
    "Chỉ dựa trên các điều luật được cung cấp bên dưới (hiệu lực đến {cutoff}); không dùng hiểu biết riêng, "
    "không dùng con số không có trong các điều luật đó. Nếu các điều luật không đủ để trả lời, nói rõ là chưa đủ căn cứ "
    "và khuyên hỏi cơ quan thuế. Nếu hộ có doanh thu trên 03 tỷ đồng hoặc chọn tính thuế theo thu nhập (doanh thu trừ chi phí), "
    "giải thích nguyên tắc nhưng không tự tính số thuế, khuyên làm việc với cơ quan thuế hoặc kế toán. "
    "Khi tính tiền, ghi rõ từng bước và số tiền bằng đồng. Viết tiếng Việt, lịch sự, xưng \"em\", tối đa 170 từ, "
    "văn bản thuần, không dùng markdown. Dòng cuối cùng bắt buộc có dạng: "
    "\"Căn cứ: Điều X khoản Y <tên văn bản có số hiệu>; …\" chỉ gồm các điều luật được cung cấp."
)
WRITER_USER = "Các điều luật:\n{context}\n\nCâu hỏi của {customer}:\n{message}"
# What the judge reads as the "user question" of the MT-Bench prompt.
JUDGE_QUESTION = (
    "Bạn là chuyên viên tư vấn thuế cho hộ kinh doanh. Dựa trên các điều luật dưới đây (hiệu lực đến {cutoff}), "
    "hãy trả lời câu hỏi, có ghi căn cứ.\n\nCác điều luật:\n{context}\n\nCâu hỏi của {customer}:\n{message}"
)
JUDGE_QUESTION_NOLAW = (
    "Bạn là chuyên viên tư vấn thuế cho hộ kinh doanh tại Việt Nam. Hãy trả lời câu hỏi, có ghi căn cứ.\n\n"
    "Câu hỏi của {customer}:\n{message}")
DEFAULTS = {"writer1": "groq-gpt-oss-20b", "writer2": "gemini-3.5-flash-lite",
            "judge": "groq-gpt-oss-120b", "autopilot": True}
HOURLY_LIMIT = 30  # questions a session may process per hour; each costs 2–4 model calls

lock = threading.Lock()
sessions: dict[str, dict] = {}


class TooMany(Exception):
    """This session asked more than HOURLY_LIMIT questions in the last hour."""


def now() -> str:
    return datetime.now().strftime("%H:%M")


def stamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def demo_tickets() -> list:
    return json.loads((DATA / "tickets.json").read_text(encoding="utf-8"))


def blank(t: dict) -> dict:
    t.update(status="new", drafts=None, decision=None, sent=None, retrieved=None, reply=None)
    return t


def fresh_state(demo: bool = False) -> dict:
    tickets = [blank(t) for t in demo_tickets() if not t.get("reserve")] if demo else []
    return {"settings": dict(DEFAULTS), "tickets": tickets, "demo": demo, "usage": []}


def session(sid: str) -> dict:
    """The inbox of one browser, loaded from disk on first use."""
    if sid not in sessions:
        f = STATES / f"{sid}.json"
        sessions[sid] = json.loads(f.read_text(encoding="utf-8")) if f.exists() else fresh_state()
    return sessions[sid]


def save(sid: str) -> None:
    STATES.mkdir(exist_ok=True)
    (STATES / f"{sid}.json").write_text(json.dumps(sessions[sid], ensure_ascii=False, indent=1), encoding="utf-8")


def settings(st: dict) -> dict:
    """Current settings, with any model whose key went missing replaced by one that works."""
    models = list(llm.available())
    s = st["settings"]
    for role in ("writer1", "writer2", "judge"):
        if s.get(role) not in models and models:
            s[role] = DEFAULTS[role] if DEFAULTS[role] in models else models[0]
    return s


def short(text: str, limit: int = 56) -> str:
    """First words of a message, cut at a word boundary, for a ticket subject."""
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(",.;:") + "…"


def find(st: dict, tid: str) -> dict:
    for t in st["tickets"]:
        if t["id"] == tid:
            return t
    raise KeyError(tid)


def redact(text: str) -> str:
    """Mask what looks like a citizen ID (12 digits) or tax code (10 or 13 digits) before it leaves the server."""
    text = re.sub(r"\b\d{10}(?:-\d{3})?\b", "[mã số thuế]", text)
    return re.sub(r"\b\d{12}\b", "[số định danh]", text)


def label(r: dict) -> str:
    return f"{r['trich_dan']}, Điều {r['dieu']}" + (f" khoản {r['khoan']}" if r["khoan"] is not None else "")


def context(hits: list[dict]) -> str:
    """The clauses a model may use, each headed by the label it should cite."""
    return "\n\n".join(f"[{label(RECORDS[h['id']])} · {RECORDS[h['id']]['tieu_de']}]\n{RECORDS[h['id']]['text']}"
                       for h in hits)


def clause_view(h: dict) -> dict:
    """What the page shows for a retrieved clause: label, full text, link to the official file."""
    r = RECORDS[h["id"]]
    src = SOURCES[r["doc"]]
    return {"id": r["id"], "label": label(r), "title": r["tieu_de"], "text": r["text"],
            "amended_by": [SOURCES[d]["trich_dan"] for d in r.get("sua_doi_boi", [])],
            "url": src["url_trang"], "score": h["score"], "matched": h["matched"], "core": h.get("core", False)}


def question_text(t: dict) -> str:
    """The question as the models read it: the message, then the facts the person added when asked."""
    extra = clarify.summary(t.get("clarified") or {})
    return f"{t['message']}\n{extra}" if extra else t["message"]


def clarify_ticket(sid: str, tid: str, answers: dict, skip: bool) -> None:
    """Store the person's answers to the inbox's questions; the ticket is then processed as usual."""
    with lock:
        t = find(session(sid), tid)
        if t["status"] != "need_info":
            raise ValueError("Câu hỏi này không cần thêm thông tin.")
        got = {} if skip else clarify.accept(t.get("need") or [], answers)
        t.update(clarified=got, need=None)
        # The amount and group checks in factcheck.py read these, as they do for the demo questions.
        if "revenue" in got:
            t["revenue"] = got["revenue"]
        if got.get("group", "unknown") != "unknown":
            t["group"] = got["group"]
        save(sid)


def write_draft(model: str, t: dict, ctx: str) -> dict:
    msgs = [{"role": "system", "content": WRITER_SYSTEM.format(cutoff=CUTOFF_VI)},
            {"role": "user", "content": WRITER_USER.format(context=ctx, customer=t["customer"], message=redact(question_text(t)))}]
    text, _, _ = llm.chat(model, msgs, 700, temperature=0.7)
    return {"model": model, "text": text.strip()}


def within_limit(st: dict) -> bool:
    hour_ago = time.time() - 3600
    st["usage"] = [u for u in st.get("usage", []) if u > hour_ago]
    return len(st["usage"]) < HOURLY_LIMIT


def process(sid: str, tid: str, redraft: bool, autosend: bool) -> dict:
    """Route one question: scope rule, retrieval, two drafts, judge in both orders, fact check."""
    with lock:
        st = session(sid)
        t = find(st, tid)
        s = settings(st)
    if OUT_OF_SCOPE.search(t["message"]):
        with lock:
            t.update(status="out_of_scope", reply=OUT_OF_SCOPE_REPLY, decision=None, drafts=None, retrieved=None,
                     processed_at=stamp())
            save(sid)
        return public(t)
    # Ask once for the facts the answer turns on; demo questions carry theirs already.
    if not t.get("canned") and "clarified" not in t:
        need = clarify.questions(t["message"])
        if need:
            with lock:
                t.update(status="need_info", need=need, processed_at=stamp())
                save(sid)
            return public(t)
    answers = t.get("clarified") or {}
    if answers.get("income") == "wage":
        with lock:
            t.update(status="out_of_scope", reply=WAGE_REPLY, decision=None, drafts=None,
                     retrieved=[clause_view({"id": c, "score": None, "matched": []}) for c in FREELANCE_CLAUSES],
                     processed_at=stamp())
            save(sid)
        return public(t)
    freelance = clarify.has("freelance", t["message"])
    caveat = freelance and answers.get("income") != "business"
    with lock:
        t["caveat"] = FREELANCE_CAVEAT if caveat else None
    found = INDEX.search(question_text(t))
    if not found["enough"]:
        with lock:
            t.update(status="no_basis", reply=NO_BASIS_REPLY.format(cutoff=CUTOFF_VI), decision=None, drafts=None,
                     retrieved=[clause_view(h) for h in found["hits"]], processed_at=stamp())
            save(sid)
        return public(t)
    with lock:
        if not within_limit(st):
            raise TooMany(f"Đã đạt giới hạn {HOURLY_LIMIT} câu hỏi mỗi giờ. Vui lòng thử lại sau.")
        st["usage"].append(time.time())
    hits = found["hits"]
    if freelance:
        seen = {h["id"] for h in hits}
        hits += [{"id": c, "score": None, "matched": [], "core": False} for c in FREELANCE_CLAUSES if c not in seen]
    ctx = context(hits)
    if t.get("canned") and not t["drafts"] and not redraft:
        # Demo questions ship a fixed pair: equally fluent, one breaks one legal detail.
        drafts = [{"model": "Mẫu trả lời", "text": x} for x in t["canned"]]
    elif redraft or not t["drafts"]:
        with ThreadPoolExecutor(2) as pool:
            d1 = pool.submit(write_draft, s["writer1"], t, ctx)
            d2 = pool.submit(write_draft, s["writer2"], t, ctx)
            drafts = [d1.result(), d2.result()]
    else:
        drafts = t["drafts"]
    if st.get("demo") and s.get("judge_law") is False:
        # Presenter's switch: the judge reads no clauses and must rely on memory (bench.py --nolaw).
        question = JUDGE_QUESTION_NOLAW.format(customer=t["customer"], message=redact(question_text(t)))
    else:
        question = JUDGE_QUESTION.format(cutoff=CUTOFF_VI, context=ctx, customer=t["customer"], message=redact(question_text(t)))
    decision = arbiter.arbitrate(s["judge"], question, drafts[0]["text"], drafts[1]["text"])
    given = {h["id"] for h in hits}
    decision = factcheck.gate(decision, [factcheck.check(d["text"], t, given, RECORDS) for d in drafts])
    with lock:
        t.update(drafts=drafts, decision=decision, sent=None, reply=None, retrieved=[clause_view(h) for h in hits],
                 processed_at=stamp())
        if trusted(decision):
            t["status"] = "ready"
            # Outside the presenter's demo nobody else is there to press "send": a checked answer goes out.
            if autosend or not st.get("demo"):
                send(t, decision["winner"], drafts[decision["winner"] - 1]["text"], by="auto")
        else:
            t["status"] = "review"
        save(sid)
        return public(t)


# Demo-only fields: the answer key of a trap question must not reach the browser.
PRIVATE = ("canned", "answer", "trap", "fc_catches", "group", "revenue")


def public(t: dict) -> dict:
    return {k: v for k, v in t.items() if k not in PRIVATE}


def trusted(d: dict) -> bool:
    """The judge's pick survived the order swap and its draft passed the fact check."""
    return d.get("status") in arbiter.SAFE and not d.get("held")


def send(t: dict, draft: int, text: str, by: str) -> None:
    d = t["decision"] or {}
    t["sent"] = {"draft": draft, "text": text, "by": by, "at": now(),
                 "edited": bool(t["drafts"]) and text != t["drafts"][draft - 1]["text"],
                 "followed_ai": d.get("winner") == draft if trusted(d) else None}
    t["status"] = "sent"


def stats(st: dict) -> dict:
    done = [t for t in st["tickets"] if t["decision"]]
    # "held": a consistent pick stopped by the fact check; it is not counted under agree/tie.
    held = [t for t in done if t["decision"].get("held")]
    by = {k: sum(t["decision"]["status"] == k for t in done if t not in held) for k in ("agree", "tie", "partial", "flip", "invalid")}
    by["held"] = len(held)
    slot_a = sum(r["verdict"] == "A" for t in done for r in t["decision"]["runs"])
    picks = sum(r["verdict"] in ("A", "B") for t in done for r in t["decision"]["runs"])
    # Questions a single-pass judge would have answered although the swap shows the pick is not stable.
    saved = sum(t["decision"]["naive"] is not None and t["decision"]["status"] not in arbiter.SAFE for t in done)
    sent = [t for t in st["tickets"] if t["sent"]]
    return {"judged": len(done), **by, "slot_a": slot_a, "slot_picks": picks, "saved": saved,
            "out_of_scope": sum(t["status"] == "out_of_scope" for t in st["tickets"]),
            "no_basis": sum(t["status"] == "no_basis" for t in st["tickets"]),
            "auto_sent": sum(t["sent"]["by"] == "auto" for t in sent),
            "human_sent": sum(t["sent"]["by"] == "agent" for t in sent),
            "overridden": sum(t["sent"]["followed_ai"] is False for t in sent)}


def snapshot(st: dict) -> dict:
    models = llm.available()
    return {"settings": settings(st), "tickets": [public(t) for t in st["tickets"]], "stats": stats(st), "demo": st.get("demo", False),
            "cutoff": CUTOFF_VI, "pending_human_check": True,
            "clarify_options": {"income": clarify.INCOME_OPTIONS, "group": clarify.GROUP_OPTIONS},
            "sources": [{"id": d["id"], "label": d.get("trich_dan", d["so_hieu"]), "url": d["url_trang"]}
                        for d in SOURCES.values() if d.get("text_file")],
            "models": [{"id": k, "label": v[0], "provider": v[1]} for k, v in models.items()]}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("  " + (fmt % args) + "\n")

    def sid(self) -> str:
        """This browser's session id; a new one is issued (and set as a cookie) on first visit."""
        c = SimpleCookie(self.headers.get("Cookie", ""))
        v = c["sid"].value if "sid" in c else ""
        if re.fullmatch(r"[A-Za-z0-9_-]{22}", v):
            return v
        self._new_sid = secrets.token_urlsafe(16)
        return self._new_sid

    def send_body(self, data: bytes, ctype: str, code: int = 200) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        if getattr(self, "_new_sid", None):
            self.send_header("Set-Cookie", f"sid={self._new_sid}; Path=/; Max-Age=31536000; HttpOnly; SameSite=Lax")
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, obj, code: int = 200) -> None:
        self.send_body(json.dumps(obj, ensure_ascii=False).encode(), "application/json; charset=utf-8", code)

    def do_GET(self):
        path = self.path.split("?")[0]
        sid = self.sid()
        if path in ("/", "/index.html"):
            return self.send_body((APP / "index.html").read_bytes(), "text/html; charset=utf-8")
        if path == "/api/state":
            with lock:
                return self.send_json(snapshot(session(sid)))
        return self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        parts = self.path.strip("/").split("/")  # api, tickets, <id>, <action>
        sid = self.sid()
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            if parts == ["api", "settings"]:
                with lock:
                    st = session(sid)
                    allowed = llm.available()
                    for role in ("writer1", "writer2", "judge"):
                        if body.get(role) in allowed:
                            st["settings"][role] = body[role]
                    if "autopilot" in body:
                        st["settings"]["autopilot"] = bool(body["autopilot"])
                    if "judge_law" in body:
                        st["settings"]["judge_law"] = bool(body["judge_law"])
                    save(sid)
                    return self.send_json(snapshot(st))
            if parts == ["api", "reset"]:
                with lock:
                    keep = session(sid)["settings"]
                    sessions[sid] = fresh_state(demo=bool(body.get("demo"))) | {"settings": keep}
                    save(sid)
                    return self.send_json(snapshot(sessions[sid]))
            if parts == ["api", "release"]:
                with lock:
                    st = session(sid)
                    have = {t["id"] for t in st["tickets"]}
                    t = next((t for t in demo_tickets() if t.get("reserve") and t["id"] not in have), None)
                    if not st.get("demo") or not t:
                        return self.send_json({"error": "Không còn câu hỏi mới."}, 404)
                    del t["reserve"]
                    t["at"] = now()
                    st["tickets"].insert(0, blank(t))
                    save(sid)
                    return self.send_json(public(t))
            if parts == ["api", "tickets"]:
                name, msg = (body.get("customer") or "").strip() or "Bạn", (body.get("message") or "").strip()
                if not msg:
                    return self.send_json({"error": "Câu hỏi đang trống."}, 400)
                if len(msg) > 2000:
                    return self.send_json({"error": "Câu hỏi quá dài (tối đa 2000 ký tự)."}, 400)
                with lock:
                    st = session(sid)
                    n = 1 + max([int(x["id"][2:]) for x in st["tickets"] + demo_tickets()] or [1000])
                    t = blank({"id": f"Q-{n}", "customer": name[:60], "channel": "Web", "at": now(),
                               "subject": short(msg), "message": msg})
                    st["tickets"].insert(0, t)
                    save(sid)
                    return self.send_json(public(t))
            if len(parts) == 4 and parts[:2] == ["api", "tickets"]:
                tid, action = parts[2], parts[3]
                if action in ("process", "clarify"):
                    if not llm.available():
                        return self.send_json({"error": "Chưa có API key nào trong .env."}, 400)
                    if action == "clarify":
                        try:
                            clarify_ticket(sid, tid, body.get("answers") or {}, bool(body.get("skip")))
                        except ValueError as e:
                            return self.send_json({"error": str(e)}, 400)
                    return self.send_json(process(sid, tid, bool(body.get("redraft")), bool(body.get("autosend"))))
                if action == "send":
                    with lock:
                        t = find(session(sid), tid)
                        draft, text = int(body.get("draft", 1)), (body.get("text") or "").strip()
                        if draft not in (1, 2) or not text:
                            return self.send_json({"error": "Câu trả lời đang trống."}, 400)
                        send(t, draft, text, by="agent")
                        save(sid)
                        return self.send_json(public(t))
                if action == "feedback":
                    with lock:
                        t = find(session(sid), tid)
                        if body.get("vote") not in ("dung", "sai"):
                            return self.send_json({"error": "Phản hồi không hợp lệ."}, 400)
                        t["feedback"] = {"vote": body["vote"], "note": (body.get("note") or "").strip()[:1000], "at": now()}
                        save(sid)
                        return self.send_json(public(t))
            return self.send_json({"error": "not found"}, 404)
        except KeyError:
            return self.send_json({"error": "Không tìm thấy câu hỏi."}, 404)
        except TooMany as e:
            return self.send_json({"error": str(e)}, 429)
        except Exception as e:  # surface provider errors to the page instead of a dropped connection
            return self.send_json({"error": llm.error_message(e)}, 502 if isinstance(e, llm.ApiError) else 500)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=8010)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--max-wait", type=int, default=90,
                        help="seconds a question may wait for a provider rate limit to reset; one judgment with the "
                             "legal clauses is ~5,000 tokens and Groq's free tier allows 8,000 tokens per minute")
    args = parser.parse_args()
    llm.load_env()
    llm.MAX_WAIT = args.max_wait
    llm.check_models()
    models = llm.available()
    print(f"Corpus: {len(RECORDS)} clauses in force, cut-off {CUTOFF_VI}")
    print("Models: " + (", ".join(v[0] + f" ({v[1]})" for v in models.values()) or "none — add keys to .env"))
    print(f"Open http://{'localhost' if args.host == '127.0.0.1' else args.host}:{args.port}")
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
