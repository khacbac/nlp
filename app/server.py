"""ABNQ Store support inbox: an AI writes two reply drafts and an AI judge picks one.

The judge is checked against itself: it sees the two drafts in both orders
(see arbiter.py). Only a pick that survives the swap is sent automatically;
everything else lands in the "Cần bạn duyệt" queue for a person. This is the
position-bias experiment turned into a routing rule.

The shop, its policy (data/policy.md) and the customers (data/tickets.json)
are made up. Progress is kept in data/state.json (gitignored) so a restart
does not lose it; "Làm mới hộp thư" in the page clears it.

Usage:
    python app/server.py            # then open http://localhost:8010
    python app/server.py --port 8080
"""

import argparse
import html
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

APP = Path(__file__).resolve().parent
sys.path.insert(0, str(APP))

import arbiter  # noqa: E402
import llm  # noqa: E402

DATA = APP / "data"
STATE = DATA / "state.json"
IMAGES = APP / "static" / "products"
PRODUCTS = json.loads((DATA / "products.json").read_text())


def price(vnd: int) -> str:
    return f"{vnd:,}".replace(",", ".") + "đ"


def stock_line(p: dict) -> str:
    """One row of the stock table the AI reads; the page shows the same data as cards."""
    name = p["name"] + (f" ({p['defect']})" if p.get("defect") else "")
    if p["stock"] > 0:
        state = f"còn {p['stock']}"
    else:
        state = "HẾT HÀNG, " + (f"dự kiến về {p['eta']}" if p.get("eta") else "chưa có ngày về")
    return f"- {name}, {price(p['price'])}: {state}."


POLICY = (DATA / "policy.md").read_text().strip().replace("{stock}", "\n".join(map(stock_line, PRODUCTS)))

WRITER_SYSTEM = (
    "Bạn là nhân viên chăm sóc khách hàng của ABNQ Store. Hãy soạn câu trả lời gửi khách hàng, "
    "chỉ dựa trên chính sách được cung cấp. Nếu chính sách không đề cập, nói rõ sẽ chuyển bộ phận "
    "phụ trách và không tự hứa hẹn. Viết tiếng Việt, lịch sự, xưng \"ABNQ Store\" hoặc \"em\", "
    "tối đa 120 từ, văn bản thuần, không dùng markdown, không ký tên."
)
WRITER_USER = "Chính sách:\n{policy}\n\nTin nhắn của khách hàng {customer}:\n{message}"
# What the judge reads as the "user question" of the MT-Bench prompt.
JUDGE_QUESTION = (
    "Bạn là nhân viên chăm sóc khách hàng của ABNQ Store. Dựa trên chính sách dưới đây, "
    "hãy trả lời tin nhắn của khách hàng.\n\nChính sách:\n{policy}\n\nTin nhắn của khách hàng {customer}:\n{message}"
)
DEFAULTS = {"writer1": "groq-gpt-oss-20b", "writer2": "gemini-3.5-flash-lite",
            "judge": "groq-gpt-oss-120b", "autopilot": True}

lock = threading.Lock()


def now() -> str:
    return datetime.now().strftime("%H:%M")


def fresh_state() -> dict:
    tickets = json.loads((DATA / "tickets.json").read_text())
    for t in tickets:
        t.update(status="new", drafts=None, decision=None, sent=None)
    return {"settings": dict(DEFAULTS), "tickets": tickets}


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return fresh_state()


state = load_state()


def save() -> None:
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1))


def settings() -> dict:
    """Current settings, with any model whose key went missing replaced by one that works."""
    models = list(llm.available())
    s = state["settings"]
    for role in ("writer1", "writer2", "judge"):
        if s.get(role) not in models and models:
            s[role] = DEFAULTS[role] if DEFAULTS[role] in models else models[0]
    return s


def short(text: str, limit: int = 48) -> str:
    """First words of a message, cut at a word boundary, for a ticket subject."""
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(",.;:") + "…"


def find(tid: str) -> dict:
    for t in state["tickets"]:
        if t["id"] == tid:
            return t
    raise KeyError(tid)


def write_draft(model: str, t: dict) -> dict:
    msgs = [{"role": "system", "content": WRITER_SYSTEM},
            {"role": "user", "content": WRITER_USER.format(policy=POLICY, customer=t["customer"], message=t["message"])}]
    text, _, _ = llm.chat(model, msgs, 400, temperature=0.7)
    return {"model": model, "text": text.strip()}


def process(tid: str, redraft: bool, autosend: bool) -> dict:
    """Write two drafts (if needed), judge them in both orders, and route the ticket."""
    with lock:
        t = find(tid)
        s = settings()
    if t.get("canned") and not t["drafts"] and not redraft:
        # Demo tickets ship a fixed pair: equally fluent, one breaks a policy detail.
        drafts = [{"model": "Mẫu trả lời", "text": x} for x in t["canned"]]
    elif redraft or not t["drafts"]:
        with ThreadPoolExecutor(2) as pool:
            d1 = pool.submit(write_draft, s["writer1"], t)
            d2 = pool.submit(write_draft, s["writer2"], t)
            drafts = [d1.result(), d2.result()]
    else:
        drafts = t["drafts"]
    question = JUDGE_QUESTION.format(policy=POLICY, customer=t["customer"], message=t["message"])
    decision = arbiter.arbitrate(s["judge"], question, drafts[0]["text"], drafts[1]["text"])
    with lock:
        t.update(drafts=drafts, decision=decision, sent=None)
        if decision["status"] in arbiter.SAFE:
            t["status"] = "ready"
            if autosend:
                send(t, decision["winner"], drafts[decision["winner"] - 1]["text"], by="auto")
        else:
            t["status"] = "review"
        save()
        return t


def send(t: dict, draft: int, text: str, by: str) -> None:
    d = t["decision"] or {}
    t["sent"] = {"draft": draft, "text": text, "by": by, "at": now(),
                 "edited": bool(t["drafts"]) and text != t["drafts"][draft - 1]["text"],
                 "followed_ai": d.get("winner") == draft if d.get("status") in arbiter.SAFE else None}
    t["status"] = "sent"


def stats() -> dict:
    done = [t for t in state["tickets"] if t["decision"]]
    by = {k: sum(t["decision"]["status"] == k for t in done) for k in ("agree", "tie", "partial", "flip", "invalid")}
    slot_a = sum(r["verdict"] == "A" for t in done for r in t["decision"]["runs"])
    picks = sum(r["verdict"] in ("A", "B") for t in done for r in t["decision"]["runs"])
    # Tickets a single-pass judge would have sent although the swap shows the pick is not stable.
    saved = sum(t["decision"]["naive"] is not None and t["decision"]["status"] not in arbiter.SAFE for t in done)
    sent = [t for t in state["tickets"] if t["sent"]]
    return {"judged": len(done), **by, "slot_a": slot_a, "slot_picks": picks, "saved": saved,
            "auto_sent": sum(t["sent"]["by"] == "auto" for t in sent),
            "human_sent": sum(t["sent"]["by"] == "agent" for t in sent),
            "overridden": sum(t["sent"]["followed_ai"] is False for t in sent)}


def snapshot() -> dict:
    models = llm.available()
    return {"settings": settings(), "policy": POLICY, "products": PRODUCTS, "tickets": state["tickets"], "stats": stats(),
            "models": [{"id": k, "label": v[0], "provider": v[1]} for k, v in models.items()]}


def credits_page() -> str:
    """Where each product photo comes from, with its author and license."""
    rows = "".join(
        f'<li><img src="/img/{p["image"]}" alt=""><div><b>{html.escape(p["name"])}</b>'
        f'<a href="{html.escape(c["url"])}">{html.escape(c["title"])}</a>'
        f'<span>Tác giả: {html.escape(c["author"] or "không ghi")} · Giấy phép '
        f'<a href="{html.escape(c["license_url"])}">{html.escape(c["license"])}</a> · đã cắt vuông</span></div></li>'
        for p in PRODUCTS if (c := p.get("credit")))
    return f"""<!doctype html><html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Nguồn ảnh · ABNQ Store</title>
<style>:root{{color-scheme:light dark;--bg:#f6f7f9;--ink:#1b2430;--muted:#667085;--line:#e3e6eb;--card:#fff}}
@media (prefers-color-scheme:dark){{:root{{--bg:#12161c;--ink:#e8ecf1;--muted:#98a2b3;--line:#2a313b;--card:#1a1f27}}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,sans-serif}}
main{{max-width:760px;margin:0 auto;padding:32px 16px}}h1{{font-size:22px;margin:0 0 6px}}p{{color:var(--muted);margin:0 0 20px}}
ul{{list-style:none;padding:0;margin:0;display:grid;gap:10px}}li{{display:flex;gap:14px;align-items:center;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px}}
img{{width:64px;height:64px;border-radius:8px;object-fit:cover;flex:none}}li div{{display:grid;gap:2px;min-width:0}}
span{{color:var(--muted);font-size:13px}}a{{color:inherit;overflow-wrap:anywhere}}</style></head><body><main>
<h1>Nguồn ảnh sản phẩm</h1><p>ABNQ Store là cửa hàng giả lập cho bài demo môn NLP. Ảnh sản phẩm lấy từ Wikimedia Commons,
dùng theo giấy phép ghi bên dưới. Sản phẩm, giá và tồn kho là dữ liệu bịa.</p><ul>{rows}</ul>
<p style="margin-top:20px"><a href="/">← Về trang hỗ trợ khách hàng</a></p></main></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("  " + (fmt % args) + "\n")

    def send_body(self, data: bytes, ctype: str, code: int = 200) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, obj, code: int = 200) -> None:
        self.send_body(json.dumps(obj, ensure_ascii=False).encode(), "application/json; charset=utf-8", code)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            return self.send_body((APP / "index.html").read_bytes(), "text/html; charset=utf-8")
        if path.startswith("/img/"):
            img = IMAGES / path.removeprefix("/img/")
            if img.parent == IMAGES and img.suffix == ".jpg" and img.is_file():
                return self.send_body(img.read_bytes(), "image/jpeg")
        if path == "/nguon-anh":
            return self.send_body(credits_page().encode(), "text/html; charset=utf-8")
        if path == "/api/state":
            with lock:
                return self.send_json(snapshot())
        return self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        parts = self.path.strip("/").split("/")  # api, tickets, <id>, <action>
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            if parts == ["api", "settings"]:
                with lock:
                    allowed = llm.available()
                    for role in ("writer1", "writer2", "judge"):
                        if body.get(role) in allowed:
                            state["settings"][role] = body[role]
                    if "autopilot" in body:
                        state["settings"]["autopilot"] = bool(body["autopilot"])
                    save()
                    return self.send_json(snapshot())
            if parts == ["api", "reset"]:
                with lock:
                    keep = state["settings"]
                    state.clear()
                    state.update(fresh_state(), settings=keep)
                    save()
                    return self.send_json(snapshot())
            if parts == ["api", "tickets"]:
                name, msg = (body.get("customer") or "").strip(), (body.get("message") or "").strip()
                if not name or not msg:
                    return self.send_json({"error": "Cần tên khách và nội dung tin nhắn."}, 400)
                with lock:
                    n = 1000 + len(state["tickets"]) + 42
                    known = {p["id"] for p in PRODUCTS}
                    t = {"id": f"T-{n}", "customer": name, "channel": "Chat", "order": None, "at": now(),
                         "products": [i for i in body.get("products") or [] if i in known],
                         "subject": (body.get("subject") or "").strip() or short(msg), "message": msg,
                         "status": "new", "drafts": None, "decision": None, "sent": None}
                    state["tickets"].insert(0, t)
                    save()
                    return self.send_json(t)
            if len(parts) == 4 and parts[:2] == ["api", "tickets"]:
                tid, action = parts[2], parts[3]
                if action == "process":
                    if not llm.available():
                        return self.send_json({"error": "Chưa có API key nào trong .env."}, 400)
                    return self.send_json(process(tid, bool(body.get("redraft")), bool(body.get("autosend"))))
                if action == "send":
                    with lock:
                        t = find(tid)
                        draft, text = int(body.get("draft", 1)), (body.get("text") or "").strip()
                        if draft not in (1, 2) or not text:
                            return self.send_json({"error": "Câu trả lời đang trống."}, 400)
                        send(t, draft, text, by="agent")
                        save()
                        return self.send_json(t)
            return self.send_json({"error": "not found"}, 404)
        except KeyError:
            return self.send_json({"error": "Không tìm thấy tin nhắn."}, 404)
        except Exception as e:  # surface provider errors to the page instead of a dropped connection
            return self.send_json({"error": llm.error_message(e)}, 502 if isinstance(e, llm.ApiError) else 500)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=8010)
    args = parser.parse_args()
    llm.load_env()
    llm.check_models()
    models = llm.available()
    print("Models: " + (", ".join(v[0] + f" ({v[1]})" for v in models.values()) or "none — add keys to .env"))
    print(f"Open http://localhost:{args.port}")
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
