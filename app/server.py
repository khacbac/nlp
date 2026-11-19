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
POLICY = (DATA / "policy.md").read_text().strip()

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
    if redraft or not t["drafts"]:
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
    return {"settings": settings(), "policy": POLICY, "tickets": state["tickets"], "stats": stats(),
            "models": [{"id": k, "label": v[0], "provider": v[1]} for k, v in models.items()]}


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
                    t = {"id": f"T-{n}", "customer": name, "channel": "Chat", "order": None, "at": now(),
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
