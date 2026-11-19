"""Thin chat client for the providers the demo and the app use (stdlib only).

Keys are read from the environment or from a .env file at the repo root:

    GEMINI_API_KEY      Google AI Studio
    GROQ_API_KEY        Groq (gpt-oss, Qwen3)
    OPENROUTER_API_KEY  OpenRouter (Qwen2.5-7B, the experiment's judge)

Only models whose key is present, and that the provider lists for that key,
are offered (see check_models).
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiment"))

import generate_answers as gen  # noqa: E402
import judge as jdg  # noqa: E402

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
MAX_WAIT = 30  # seconds we are willing to wait for a rate limit to reset


class ApiError(Exception):
    def __init__(self, code: int, detail: str):
        super().__init__(f"HTTP {code}: {detail}")
        self.code = code


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


def _retry_after(e: urllib.error.HTTPError, body: str, attempt: int) -> float:
    """Seconds to wait before retrying: the provider's hint if it gives one."""
    hint = e.headers.get("retry-after") if e.headers else None
    m = re.search(r'"retryDelay":\s*"(\d+(?:\.\d+)?)s"', body) or re.search(r"try again in (\d+(?:\.\d+)?)s", body)
    try:
        wait = float(hint) if hint else float(m.group(1)) if m else 2 + 3 * attempt
    except ValueError:
        wait = 2 + 3 * attempt
    return wait + 0.5


def post(url: str, body: dict, headers: dict, retries: int = 4) -> dict:
    """POST JSON; wait and retry on overload (503) and rate limits (429)."""
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={
        "Content-Type": "application/json", "User-Agent": "position-bias-demo/1.0", **headers})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")
            wait = _retry_after(e, detail, attempt)
            if e.code not in (429, 503) or attempt == retries - 1 or wait > MAX_WAIT:
                raise ApiError(e.code, detail[:400]) from e
            time.sleep(wait)
    raise AssertionError("unreachable")


def chat(model_id: str, msgs: list[dict], max_tokens: int, want_logprobs: bool = False,
         temperature: float = 0) -> tuple[str, list, list]:
    """Return (text, tokens, top) where tokens/top are empty when logprobs are unavailable."""
    _, provider, model, kind = CATALOG[model_id]
    key = os.environ[KEY_ENV[provider]]
    want_logprobs = want_logprobs and model_id not in NO_LOGPROBS

    if provider == "gemini":
        cfg = {"temperature": temperature, "maxOutputTokens": max_tokens + 500}
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
                return chat(model_id, msgs, max_tokens, False, temperature)
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

    body = {"model": model, "messages": msgs, "temperature": temperature,
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
            return chat(model_id, msgs, max_tokens, False, temperature)
        raise
    choice = resp["choices"][0]
    text = choice["message"].get("content") or ""
    reasoning = (choice["message"].get("reasoning") or "").strip()
    if reasoning and len(jdg.VERDICT_RE.sub("", text).strip()) < 20:
        # gpt-oss sometimes keeps its explanation in the reasoning field and
        # answers with the bare verdict; show the explanation, keep the verdict last.
        text = reasoning + "\n\n" + text
    content =(choice.get("logprobs") or {}).get("content") or []
    if content:
        tokens = [c["token"] for c in content]
        top = [{t["token"]: t["logprob"] for t in c.get("top_logprobs", [])} | {c["token"]: c["logprob"]}
               for c in content]
        return text, tokens, top
    return text, [], []


def judge_once(model_id: str, question: str, a: str, b: str) -> dict:
    """One MT-Bench pair-v2 judgment with `a` shown as Assistant A and `b` as Assistant B."""
    user = jdg.USER_TEMPLATE.format(question=question, answer_a=a, answer_b=b)
    msgs = [{"role": "system", "content": jdg.SYSTEM_PROMPT}, {"role": "user", "content": user}]
    t0 = time.time()
    text, tokens, top = chat(model_id, msgs, jdg.MAX_TOKENS, want_logprobs=True)
    probs = {}
    if tokens:
        _, probs = jdg.read_verdict(tokens, top)
    found = jdg.VERDICT_RE.findall(text)
    return {"verdict": found[-1] if found else None, "probs": probs or None,
            "judgment": text.strip(), "ms": int((time.time() - t0) * 1000)}


def error_message(e: Exception) -> str:
    """A short Vietnamese message for the page."""
    if isinstance(e, ApiError) and e.code == 429:
        return "Hết hạn mức của nhà cung cấp, thử lại sau ít phút."
    return str(e)
