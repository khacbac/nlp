"""Generate answers to the selected questions with one of the three answer models.

Every model gets the same prompt (2-4 sentences, no formatting) and
temperature 0. Answers are appended to data/answers.jsonl one line at a
time; rerunning skips (qid, model) pairs that are already there, so a run
cut off by a rate limit or a Colab disconnect just continues.

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
"""

import argparse
import json
import os
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
GEMINI_MODEL = "gemini-2.5-flash-lite"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def messages(q: dict) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT.format(context=q["context"], question=q["question"])},
    ]


def post_json(url: str, body: dict, headers: dict, retries: int = 6) -> dict:
    """POST with exponential backoff on rate limits and server errors."""
    data = json.dumps(body).encode()
    for attempt in range(retries):
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **headers})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or attempt == retries - 1:
                raise RuntimeError(f"HTTP {e.code}: {e.read().decode(errors='replace')[:500]}") from e
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
        "generationConfig": {"temperature": 0, "maxOutputTokens": MAX_TOKENS},
    }
    resp = post_json(GEMINI_URL.format(model=GEMINI_MODEL), body, {"x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    cand = resp["candidates"][0]
    text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []))
    return text, cand.get("finishReason", ""), GEMINI_MODEL


def answer_qwen_batch(questions: list[dict]) -> list[tuple[str, str, str]]:
    from vllm import LLM, SamplingParams  # only needed on the GPU machine

    llm = LLM(QWEN_MODEL, quantization="awq", dtype="half", max_model_len=4096, gpu_memory_utilization=0.9)
    params = SamplingParams(temperature=0, max_tokens=MAX_TOKENS)
    outputs = llm.chat([messages(q) for q in questions], params)
    return [(o.outputs[0].text, o.outputs[0].finish_reason or "", QWEN_MODEL) for o in outputs]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=["qwen", "gpt-oss", "gemini"], required=True)
    parser.add_argument("--provider", choices=list(GPT_OSS), default="groq", help="gpt-oss only")
    parser.add_argument("--limit", type=int, help="only the first N questions (for a trial run)")
    parser.add_argument("--interval", type=float, default=4.5,
                        help="seconds between API calls (Gemini free tier allows ~15/minute)")
    parser.add_argument("--questions", type=Path, default=DATA / "questions.jsonl")
    parser.add_argument("--out", type=Path, default=DATA / "answers.jsonl")
    args = parser.parse_args()

    questions = [json.loads(line) for line in args.questions.open(encoding="utf-8")][: args.limit]
    done = set()
    if args.out.exists():
        done = {(r["qid"], r["model"]) for r in map(json.loads, args.out.open(encoding="utf-8"))}
    todo = [q for q in questions if (q["qid"], args.model) not in done]
    print(f"{args.model}: {len(todo)} to answer, {len(questions) - len(todo)} already done")

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

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("a", encoding="utf-8") as out:
        if args.model == "qwen":
            for q, result in zip(todo, answer_qwen_batch(todo)):
                write(out, q, *result)
            return
        for i, q in enumerate(todo, 1):
            if args.model == "gemini":
                result = answer_gemini(q)
            else:
                result = answer_gpt_oss(q, args.provider)
            write(out, q, *result)
            print(f"  [{i}/{len(todo)}] {q['qid']}")
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
