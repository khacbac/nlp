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
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiment"))

import generate_answers as gen  # noqa: E402
import judge as jdg  # noqa: E402

DATA = ROOT / "experiment" / "data"
EXPERIMENT_MODELS = ["qwen", "gpt-oss", "gemini"]

OPENAI_URLS = {
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
}
KEY_ENV = {"groq": "GROQ_API_KEY", "openrouter": "OPENROUTER_API_KEY", "gemini": "GEMINI_API_KEY"}

# id -> (label, provider, provider model id, kind). The kind picks how to
# switch reasoning off or down, which differs per model family:
#   plain   no reasoning settings
#   gpt-oss reasoning_effort "low" (Groq) / reasoning.effort "low" (OpenRouter)
#   qwen3   Groq Qwen3: reasoning_effort "none"
#   g3      Gemini 3.x: thinkingLevel "minimal"
# Not offered: Gemini 2.5 (closed to new keys), Gemini 3.8 Flash (no "minimal"
# thinking, timed out) and Gemma 4 (thinking cannot be switched off, ~30 s per call).
# Models a key cannot reach are dropped at startup (see check_models).
CATALOG = {
    "or-qwen2.5-7b": ("Qwen2.5-7B (judge của thí nghiệm)", "openrouter", "qwen/qwen-2.5-7b-instruct", "plain"),
    "or-gpt-oss-20b": ("gpt-oss-20b", "openrouter", "openai/gpt-oss-20b", "gpt-oss"),
    "groq-gpt-oss-20b": ("gpt-oss-20b", "groq", "openai/gpt-oss-20b", "gpt-oss"),
    "groq-gpt-oss-120b": ("gpt-oss-120b", "groq", "openai/gpt-oss-120b", "gpt-oss"),
    "groq-qwen3.8-27b": ("Qwen3.8 27B", "groq", "qwen/qwen3.8-27b", "qwen3"),
    "gemini-3.5-flash-lite": ("Gemini 3.5 Flash-Lite", "gemini", gen.GEMINI_MODEL, "g3"),
    "gemini-3.5-flash": ("Gemini 3.5 Flash", "gemini", "gemini-3.5-flash", "g3"),
}
# Providers that rejected logprobs once are not asked again (per model).
NO_LOGPROBS: set[str] = set()
# Filled by check_models(); None means "not checked yet, offer everything with a key".
REACHABLE: set[str] | None = None


def load_env() -> None:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def available() -> dict[str, tuple]:
    return {k: v for k, v in CATALOG.items()
            if os.environ.get(KEY_ENV[v[1]]) and (REACHABLE is None or k in REACHABLE)}


def check_models() -> None:
    """Keep only catalog models that each provider lists for this key."""
    global REACHABLE
    listed: dict[str, set[str]] = {}
    sources = {
        "groq": ("https://api.groq.com/openai/v1/models", "Authorization", "Bearer ", "data", "id"),
        "openrouter": ("https://openrouter.ai/api/v1/models", "Authorization", "Bearer ", "data", "id"),
        "gemini": ("https://generativelanguage.googleapis.com/v1beta/models?pageSize=1000",
                   "x-goog-api-key", "", "models", "name"),
    }
    for provider, (url, header, prefix, field, key_field) in sources.items():
        key = os.environ.get(KEY_ENV[provider])
        if not key:
            continue
        try:
            req = urllib.request.Request(url, headers={header: prefix + key, "User-Agent": "position-bias-demo/1.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                listed[provider] = {m[key_field].removeprefix("models/") for m in json.load(resp)[field]}
        except Exception as e:  # keep the provider's models if the list cannot be read
            print(f"  could not list {provider} models ({e}); offering all of them")
    REACHABLE = {k for k, (_, provider, model, _) in CATALOG.items()
                 if provider not in listed or model in listed[provider]}
    for k, (label, provider, model, _) in CATALOG.items():
        if os.environ.get(KEY_ENV[provider]) and k not in REACHABLE:
            print(f"  skipping {label} ({provider}): {model} is not available for this key")


def post(url: str, body: dict, headers: dict, retries: int = 3) -> dict:
    """POST JSON; retry briefly on overload (503) and rate limits (429)."""
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={
        "Content-Type": "application/json", "User-Agent": "position-bias-demo/1.0", **headers})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503) or attempt == retries - 1:
                raise ApiError(e.code, e.read().decode(errors="replace")[:400]) from e
        time.sleep(2 + 3 * attempt)
    raise AssertionError("unreachable")


class ApiError(Exception):
    def __init__(self, code: int, detail: str):
        super().__init__(f"HTTP {code}: {detail}")
        self.code = code


def chat(model_id: str, msgs: list[dict], max_tokens: int, want_logprobs: bool) -> tuple[str, list, list]:
    """Return (text, tokens, top) where tokens/top are empty when logprobs are unavailable."""
    _, provider, model, kind = CATALOG[model_id]
    key = os.environ[KEY_ENV[provider]]
    want_logprobs = want_logprobs and model_id not in NO_LOGPROBS

    if provider == "gemini":
        cfg = {"temperature": 0, "maxOutputTokens": max_tokens + 500}
        if kind == "g3":
            cfg["thinkingConfig"] = {"thinkingLevel": "minimal"}
        if want_logprobs:
            cfg.update(responseLogprobs=True, logprobs=jdg.TOP_LOGPROBS)
        body = {"systemInstruction": {"parts": [{"text": msgs[0]["content"]}]},
                "contents": [{"role": "user", "parts": [{"text": msgs[1]["content"]}]}],
                "generationConfig": cfg}
        try:
            resp = post(gen.GEMINI_URL.format(model=model), body, {"x-goog-api-key": key})
        except ApiError as e:
            if want_logprobs and e.code == 400:
                NO_LOGPROBS.add(model_id)
                return chat(model_id, msgs, max_tokens, False)
            raise
        if not resp.get("candidates"):
            raise RuntimeError("Gemini không trả lời (có thể bị bộ lọc an toàn chặn).")
        cand = resp["candidates"][0]
        text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []) if not p.get("thought"))
        lr = cand.get("logprobsResult") or {}
        chosen, tops = lr.get("chosenCandidates") or [], lr.get("topCandidates") or []
        if chosen and len(chosen) == len(tops):
            tokens = [c["token"] for c in chosen]
            top = [{c["token"]: c["logProbability"] for c in t.get("candidates", [])} for t in tops]
            return text, tokens, top
        return text, [], []

    body = {"model": model, "messages": msgs, "temperature": 0,
            "max_tokens": max_tokens + (1500 if kind in ("gpt-oss", "qwen3") else 0)}
    if kind == "gpt-oss" and provider == "groq":
        body["reasoning_effort"] = "low"
    elif kind == "gpt-oss":
        body["reasoning"] = {"effort": "low", "exclude": True}
    elif kind == "qwen3":
        body["reasoning_effort"] = "none"
    if want_logprobs:
        body.update(logprobs=True, top_logprobs=jdg.TOP_LOGPROBS)
    try:
        resp = post(OPENAI_URLS[provider], body, {"Authorization": f"Bearer {key}"})
    except ApiError as e:
        if want_logprobs and e.code == 400:
            NO_LOGPROBS.add(model_id)
            return chat(model_id, msgs, max_tokens, False)
        raise
    choice = resp["choices"][0]
    text = choice["message"].get("content") or ""
    content = (choice.get("logprobs") or {}).get("content") or []
    if content:
        tokens = [c["token"] for c in content]
        top = [{t["token"]: t["logprob"] for t in c.get("top_logprobs", [])} | {c["token"]: c["logprob"]}
               for c in content]
        return text, tokens, top
    return text, [], []


def judge_once(model_id: str, question: str, context: str, a: str, b: str) -> dict:
    user = jdg.USER_TEMPLATE.format(
        question=jdg.QUESTION_TEMPLATE.format(context=context, question=question), answer_a=a, answer_b=b)
    msgs = [{"role": "system", "content": jdg.SYSTEM_PROMPT}, {"role": "user", "content": user}]
    t0 = time.time()
    text, tokens, top = chat(model_id, msgs, jdg.MAX_TOKENS, want_logprobs=True)
    probs = {}
    if tokens:
        _, probs = jdg.read_verdict(tokens, top)
    found = jdg.VERDICT_RE.findall(text)
    return {"verdict": found[-1] if found else None, "probs": probs or None,
            "judgment": text.strip(), "ms": int((time.time() - t0) * 1000)}


def answer(model_id: str, question: str, context: str) -> dict:
    msgs = [{"role": "system", "content": gen.SYSTEM_PROMPT},
            {"role": "user", "content": gen.USER_PROMPT.format(context=context, question=question)}]
    text, _, _ = chat(model_id, msgs, gen.MAX_TOKENS, want_logprobs=False)
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
            return self.send_json({"models": [{"id": k, "label": v[0], "provider": v[1]} for k, v in available().items()],
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
            if model not in available():
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
        except ApiError as e:
            msg = "Hết hạn mức của nhà cung cấp, thử lại sau ít phút." if e.code == 429 else str(e)
            return self.send_json({"error": msg}, 502)
        except Exception as e:  # surface provider errors to the page instead of a dropped connection
            return self.send_json({"error": str(e)}, 500)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    load_env()
    check_models()
    models = available()
    print(f"Loaded {len(QUESTIONS)} questions, {len(ANSWERS)} recorded answers, {len(PAIRS)} recorded pairs.")
    print("Models: " + (", ".join(v[0] + f" ({v[1]})" for v in models.values()) or "none — add keys to .env"))
    print(f"Open http://localhost:{args.port}")
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
