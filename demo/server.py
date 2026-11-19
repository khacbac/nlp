"""Local server for the live demo: pick a question, get two answers, judge them in both orders.

It serves ../demo.html and a small JSON API. API keys stay on this machine;
the browser only talks to localhost. Keys are read from the environment or
from a .env file at the repo root (see .env.example):

    GEMINI_API_KEY      Google AI Studio  -> Gemini judges and answers
    GROQ_API_KEY        Groq              -> gpt-oss, Llama, Qwen3 judges and answers
    OPENROUTER_API_KEY  OpenRouter        -> Qwen2.5-7B (the experiment's judge) and others

Only models whose key is present are offered.

Usage:
    python demo/server.py            # then open http://localhost:8000
    python demo/server.py --port 8080

The judge prompt, the verdict parser and the answer prompt are imported from
experiment/judge.py and experiment/generate_answers.py, so the live demo
judges exactly as the experiment did. Unlike the experiment, providers may
not return log-probabilities; then only the verdict is shown.
"""

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

import llm  # noqa: E402
from llm import gen, jdg  # noqa: E402

DATA = ROOT / "experiment" / "data"
EXPERIMENT_MODELS = ["qwen", "gpt-oss", "gemini"]


def judge_once(model_id: str, question: str, context: str, a: str, b: str) -> dict:
    return llm.judge_once(model_id, jdg.QUESTION_TEMPLATE.format(context=context, question=question), a, b)


def answer(model_id: str, question: str, context: str) -> dict:
    msgs = [{"role": "system", "content": gen.SYSTEM_PROMPT},
            {"role": "user", "content": gen.USER_PROMPT.format(context=context, question=question)}]
    text, _, _ = llm.chat(model_id, msgs, gen.MAX_TOKENS)
    return {"answer": text.strip()}


# ---------- recorded experiment data (local only; gitignored) ----------

def read_jsonl(path: Path) -> list[dict]:
    return jdg.read_jsonl(path)


QUESTIONS = {q["qid"]: q for q in read_jsonl(DATA / "questions.jsonl")}
ANSWERS = {(r["qid"], r["model"]): r["answer"] for m in EXPERIMENT_MODELS
           for r in read_jsonl(DATA / f"answers_{m}.jsonl")}
PAIRS = {(p["qid"], p["x"], p["y"]): p for p in read_jsonl(DATA / "pairs_vi.jsonl")}


def question_detail(qid: str) -> dict:
    q = QUESTIONS[qid]
    pairs = []
    for (pq, x, y), p in PAIRS.items():
        if pq == qid:
            pairs.append({k: p.get(k) for k in ("x", "y", "verdict_1", "verdict_2", "p1x", "p2x", "hx", "hy")})
    return {"qid": qid, "title": q.get("title", ""), "question": q["question"], "context": q["context"],
            "gold": (q.get("gold_answers") or [""])[0],
            "answers": {m: ANSWERS.get((qid, m)) for m in EXPERIMENT_MODELS if (qid, m) in ANSWERS},
            "pairs": pairs}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt, *args):
        if "/api/" in (args[0] if args else ""):
            sys.stderr.write("  " + (fmt % args) + "\n")

    def send_json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.path = "/demo.html"
        if self.path == "/api/models":
            return self.send_json({"models": [{"id": k, "label": v[0], "provider": v[1]} for k, v in llm.available().items()],
                                   "questions": len(QUESTIONS)})
        if self.path == "/api/questions":
            return self.send_json([{"qid": q["qid"], "title": q.get("title", ""), "question": q["question"]}
                                   for q in QUESTIONS.values()])
        if self.path.startswith("/api/question/"):
            qid = self.path.rsplit("/", 1)[1]
            return self.send_json(question_detail(qid)) if qid in QUESTIONS else self.send_json({"error": "not found"}, 404)
        if self.path.startswith("/api/"):
            return self.send_json({"error": "not found"}, 404)
        # Serve only the page itself; data files and keys stay private.
        if self.path.split("?")[0] != "/demo.html":
            return self.send_json({"error": "not found"}, 404)
        return super().do_GET()

    def do_POST(self):
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            model = body.get("model")
            if model not in llm.available():
                return self.send_json({"error": f"Chưa có API key cho mô hình {model}."}, 400)
            q, ctx = (body.get("question") or "").strip(), (body.get("context") or "").strip()
            if not q or not ctx:
                return self.send_json({"error": "Cần cả đoạn văn và câu hỏi."}, 400)
            if self.path == "/api/answer":
                return self.send_json(answer(model, q, ctx))
            if self.path == "/api/judge":
                x, y = (body.get("x") or "").strip(), (body.get("y") or "").strip()
                if not x or not y:
                    return self.send_json({"error": "Cần đủ hai câu trả lời."}, 400)
                # Both orders at once: run 1 shows X as A, run 2 shows Y as A.
                with ThreadPoolExecutor(2) as pool:
                    r1 = pool.submit(judge_once, model, q, ctx, x, y)
                    r2 = pool.submit(judge_once, model, q, ctx, y, x)
                    return self.send_json({"runs": [r1.result(), r2.result()]})
            return self.send_json({"error": "not found"}, 404)
        except Exception as e:  # surface provider errors to the page instead of a dropped connection
            return self.send_json({"error": llm.error_message(e)}, 502 if isinstance(e, llm.ApiError) else 500)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    llm.load_env()
    llm.check_models()
    models = llm.available()
    print(f"Loaded {len(QUESTIONS)} questions, {len(ANSWERS)} recorded answers, {len(PAIRS)} recorded pairs.")
    print("Models: " + (", ".join(v[0] + f" ({v[1]})" for v in models.values()) or "none — add keys to .env"))
    print(f"Open http://localhost:{args.port}")
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
