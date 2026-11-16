"""Generate answers to the selected questions with one of the three answer models.

Every model gets the same prompt (2-4 sentences, no formatting) and
temperature 0. Answers are appended to data/answers_<model>.jsonl one line
at a time (one file per model, so two models can run at the same time).

The script is safe to stop and rerun at any point:
- a rerun skips questions that already have a non-empty answer;
- a question that fails (blocked, bad response, network) is logged and
  skipped, and the next rerun tries it again;
- when a daily quota runs out, the script stops at once with a message,
  instead of retrying for minutes;
- a half-written last line (run killed while writing) is ignored;
- Qwen answers are written in chunks of 50, not only at the end.

Usage (one model per run):
    # Qwen2.5-7B-Instruct on a Colab / Kaggle T4 GPU (needs: pip install vllm)
    python generate_answers.py --model qwen

    # gpt-oss-20b through Groq's free API (env GROQ_API_KEY)
    python generate_answers.py --model gpt-oss
    # ...or through OpenRouter's free endpoint (env OPENROUTER_API_KEY)
    python generate_answers.py --model gpt-oss --provider openrouter

    # Gemini Flash-Lite through Google AI Studio's free tier (env GEMINI_API_KEY)
    python generate_answers.py --model gemini

    # try any model on 3 questions first
    python generate_answers.py --model gemini --limit 3

    # keep the answers somewhere that survives a Colab reset
    python generate_answers.py --model gemini --out-dir /content/drive/MyDrive/nlp-answers

Exit code 2 means a quota ran out (rerun later); 3 means 5 failures in a row
(check the key, model id or account).
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DATA = Path(__file__).parent / "data"

SYSTEM_PROMPT = (
    "Bạn là trợ lý trả lời câu hỏi đọc hiểu tiếng Việt. "
    "Chỉ dựa vào đoạn văn được cung cấp."
)
USER_PROMPT = """Đoạn văn:
{context}

Câu hỏi: {question}

Trả lời bằng tiếng Việt trong 2-4 câu, dựa vào đoạn văn. Viết thành một đoạn văn xuôi, không dùng gạch đầu dòng, tiêu đề hay chữ in đậm."""

MAX_TOKENS = 300

# API model ids. Check the provider's model list if one stops working.
QWEN_MODEL = "Qwen/Qwen2.5-7B-Instruct-AWQ"  # 4-bit, fits a 16 GB T4
GPT_OSS = {
    "groq": ("https://api.groq.com/openai/v1/chat/completions", "openai/gpt-oss-20b", "GROQ_API_KEY"),
    "openrouter": ("https://openrouter.ai/api/v1/chat/completions", "openai/gpt-oss-20b:free", "OPENROUTER_API_KEY"),
}
# gemini-2.5-flash-lite is closed to new projects; 3.5 Flash-Lite has a free tier.
GEMINI_MODEL = "gemini-3.5-flash-lite"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def messages(q: dict) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT.format(context=q["context"], question=q["question"])},
    ]


class QuotaExhausted(Exception):
    """Daily quota is used up, or rate limits persist; stop and rerun later."""


# Words providers use in a 429 body when the per-day quota, not the per-minute one, ran out.
DAILY_QUOTA_HINTS = ("per day", "perday", "daily", "tpd", "rpd")


def post_json(url: str, body: dict, headers: dict, retries: int = 6) -> dict:
    """POST with exponential backoff on rate limits and server errors."""
    data = json.dumps(body).encode()
    for attempt in range(retries):
        req = urllib.request.Request(url, data=data, headers={
            "Content-Type": "application/json",
            # Cloudflare (in front of Groq) rejects urllib's default User-Agent with "error code: 1010".
            "User-Agent": "answer-generator/1.0",
            **headers,
        })
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:500]
            if e.code == 429 and any(h in detail.lower() for h in DAILY_QUOTA_HINTS):
                raise QuotaExhausted(detail) from e
            if e.code == 429 and attempt == retries - 1:
                raise QuotaExhausted(detail) from e
            if e.code not in (429, 500, 502, 503, 504) or attempt == retries - 1:
                raise RuntimeError(f"HTTP {e.code}: {detail}") from e
        except (urllib.error.URLError, TimeoutError):
            if attempt == retries - 1:
                raise
        wait = 2 ** attempt * 5
        print(f"  retry in {wait}s")
        time.sleep(wait)
    raise AssertionError("unreachable")


def answer_gpt_oss(q: dict, provider: str) -> tuple[str, str, str]:
    url, model, key_env = GPT_OSS[provider]
    body = {"model": model, "messages": messages(q), "temperature": 0, "max_tokens": MAX_TOKENS + 1000}
    # Low reasoning effort; the reasoning text is returned separately from the answer.
    if provider == "groq":
        body["reasoning_effort"] = "low"
    else:
        body["reasoning"] = {"effort": "low", "exclude": True}
    resp = post_json(url, body, {"Authorization": f"Bearer {os.environ[key_env]}"})
    choice = resp["choices"][0]
    return choice["message"]["content"], choice.get("finish_reason", ""), model


def answer_gemini(q: dict) -> tuple[str, str, str]:
    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": messages(q)[1]["content"]}]}],
        # Gemini 3 always thinks a little and counts those tokens in maxOutputTokens,
        # so keep thinking minimal and leave room for it on top of the answer.
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": MAX_TOKENS + 500,
            "thinkingConfig": {"thinkingLevel": "minimal"},
        },
    }
    resp = post_json(GEMINI_URL.format(model=GEMINI_MODEL), body, {"x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    if not resp.get("candidates"):  # prompt blocked by a safety filter
        raise RuntimeError(f"no candidates: {json.dumps(resp.get('promptFeedback', resp))[:300]}")
    cand = resp["candidates"][0]
    parts = cand.get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
    return text, cand.get("finishReason", ""), GEMINI_MODEL


def answer_qwen_chunks(questions: list[dict], size: int = 50):
    """Yield (question, result) in chunks, so a disconnect loses at most one chunk."""
    from vllm import LLM, SamplingParams  # only needed on the GPU machine

    llm = LLM(QWEN_MODEL, quantization="awq", dtype="half", max_model_len=4096, gpu_memory_utilization=0.9)
    params = SamplingParams(temperature=0, max_tokens=MAX_TOKENS)
    for start in range(0, len(questions), size):
        chunk = questions[start:start + size]
        outputs = llm.chat([messages(q) for q in chunk], params, use_tqdm=False)
        for q, o in zip(chunk, outputs):
            yield q, (o.outputs[0].text, o.outputs[0].finish_reason or "", QWEN_MODEL)
        print(f"  [{start + len(chunk)}/{len(questions)}]")


def read_jsonl(path: Path) -> list[dict]:
    """Read a JSONL file, skipping a half-written line left by a killed run."""
    rows = []
    if path.exists():
        for line in path.open(encoding="utf-8"):
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"  skipping a broken line in {path.name}")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=["qwen", "gpt-oss", "gemini"], required=True)
    parser.add_argument("--provider", choices=list(GPT_OSS), default="groq", help="gpt-oss only")
    parser.add_argument("--limit", type=int, help="only the first N questions (for a trial run)")
    parser.add_argument("--interval", type=float, default=4.5,
                        help="seconds between API calls (Gemini free tier allows ~15/minute)")
    parser.add_argument("--questions", type=Path, default=DATA / "questions.jsonl")
    parser.add_argument("--out-dir", type=Path, default=DATA,
                        help="where answers_<model>.jsonl lives (e.g. a Google Drive folder)")
    args = parser.parse_args()
    out_path = args.out_dir / f"answers_{args.model}.jsonl"

    questions = read_jsonl(args.questions)[: args.limit]
    # Empty answers do not count as done, so a rerun tries them again.
    done = {(r["qid"], r["model"]) for r in read_jsonl(out_path) if r.get("answer")}
    todo = [q for q in questions if (q["qid"], args.model) not in done]
    print(f"{args.model}: {len(todo)} to answer, {len(questions) - len(todo)} already done -> {out_path}")
    if not todo:
        return

    def write(out, q, text, finish, model_id):
        text = text.strip()
        out.write(json.dumps({
            "qid": q["qid"],
            "model": args.model,
            "model_id": model_id,
            "answer": text,
            "num_words": len(text.split()),
            "finish_reason": str(finish),
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }, ensure_ascii=False) + "\n")
        out.flush()
        if not text or str(finish).lower() in ("length", "max_tokens"):
            print(f"  WARNING {q['qid']}: empty or cut-off answer ({finish})")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    failed = []
    streak = 0  # consecutive failures; many in a row means a bad key or model, not bad questions
    with out_path.open("a", encoding="utf-8") as out:
        # A killed run may leave a line without "\n"; start on a fresh line.
        if out.tell() > 0:
            with out_path.open("rb") as f:
                f.seek(-1, os.SEEK_END)
                if f.read(1) != b"\n":
                    out.write("\n")
        if args.model == "qwen":
            for q, result in answer_qwen_chunks(todo):
                write(out, q, *result)
        else:
            for i, q in enumerate(todo, 1):
                try:
                    if args.model == "gemini":
                        result = answer_gemini(q)
                    else:
                        result = answer_gpt_oss(q, args.provider)
                except QuotaExhausted as e:
                    print(f"\nQuota exhausted after {i - 1} answers this run: {e}")
                    print("Rerun later (e.g. tomorrow); finished answers are saved.")
                    sys.exit(2)
                except Exception as e:  # one bad question must not stop the run
                    print(f"  FAILED {q['qid']}: {e}")
                    failed.append(q["qid"])
                    streak += 1
                    if streak >= 5:
                        print("\n5 failures in a row: check the API key, model id and account, then rerun.")
                        sys.exit(3)
                else:
                    streak = 0
                    write(out, q, *result)
                    print(f"  [{i}/{len(todo)}] {q['qid']}")
                time.sleep(args.interval)

    answered = {r["qid"] for r in read_jsonl(out_path) if r.get("answer")}
    remaining = sum(q["qid"] not in answered for q in todo)
    print(f"done; {remaining} still without an answer" + (f" (failed: {failed[:10]})" if failed else ""))
    if remaining:
        print("Rerun the same command to retry them.")


if __name__ == "__main__":
    main()
